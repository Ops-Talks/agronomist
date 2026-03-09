"""Command-line interface for Agronomist.

Provides ``report`` and ``update`` sub-commands for scanning
Terraform/HCL files, resolving latest module versions, and
optionally applying in-place updates.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import logging
import os
import sys
from collections.abc import Callable
from urllib.parse import urlparse

from .config import load_config
from .exceptions import AuthenticationError, ConfigError
from .git import GitClient
from .github import GitHubClient
from .gitlab import GitLabClient
from .markdown import write_markdown
from .models import Replacement, SourceRef, UpdateEntry
from .report import build_report, write_report
from .scanner import _match_any, scan_sources
from .updater import apply_updates

logger = logging.getLogger(__name__)


def _add_common_args(parser: argparse.ArgumentParser) -> None:
    """Register CLI arguments shared by report and update.

    Parameters:
        parser: The sub-parser to augment.
    """
    parser.add_argument("--root", default=".")
    parser.add_argument("--include", action="append", default=[])
    parser.add_argument("--exclude", action="append", default=[])
    parser.add_argument(
        "--github-base-url",
        default="https://api.github.com",
    )
    parser.add_argument(
        "--gitlab-base-url",
        default="https://gitlab.com",
        help=(
            "GitLab API base URL "
            "(default: https://gitlab.com)"
        ),
    )
    parser.add_argument(
        "--token",
        default=None,
        help=("Shared fallback token for GitHub/GitLab when specific tokens are not provided"),
    )
    parser.add_argument(
        "--github-token",
        default=None,
        help="GitHub API token (overrides GITHUB_TOKEN env var)",
    )
    parser.add_argument(
        "--gitlab-token",
        default=None,
        help="GitLab API token (overrides GITLAB_TOKEN env var)",
    )
    parser.add_argument("--config", default=".agronomist.yaml")
    parser.add_argument(
        "--resolver",
        default="git",
        choices=["git", "github", "auto"],
        help="How to resolve the latest version: git, github or auto",
    )
    parser.add_argument("--output", default="report.json")
    parser.add_argument(
        "--markdown",
        default=None,
        help="Generate Markdown report (e.g.: report.md)",
    )
    parser.add_argument(
        "--validate-token",
        action="store_true",
        help="Validate token before processing (useful for CI/CD)",
    )
    parser.add_argument(
        "--no-report",
        action="store_true",
        help="Skip generating report files (useful for CI/CD pipelines)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=20,
        help=("Request timeout in seconds for API and git operations (default: 20)"),
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=10,
        help=("Number of parallel workers for version resolution (default: 10)"),
    )
    verbose_group = parser.add_mutually_exclusive_group()
    verbose_group.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose (DEBUG) logging",
    )
    verbose_group.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress informational output (WARNING level only)",
    )


def _parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse CLI arguments and return a Namespace.

    Exits with usage help when no sub-command is provided.

    Parameters:
        argv: Raw argument list (typically ``sys.argv[1:]``).

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        prog="agronomist",
        description=("Detect and update Terraform module versions across repositories"),
        epilog="""
examples:
  %(prog)s report                           # Generate version report
  %(prog)s report --resolver github         # Use GitHub API resolver
  %(prog)s update --include '**/*.tf'       # Update matching Terraform files
  %(prog)s report --markdown report.md      # Export as Markdown
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command")

    report_parser = subparsers.add_parser(
        "report",
        help="Generate a version report for all Terraform modules",
    )
    _add_common_args(report_parser)

    update_parser = subparsers.add_parser(
        "update",
        help=("Update Terraform modules to their latest versions and generate report"),
    )
    _add_common_args(update_parser)

    args = parser.parse_args(argv)

    if not argv or not args.command:
        parser.print_help()
        sys.exit(0)

    return args


def _categorize(rules: list, repo: str, module: str | None) -> str | None:
    """Assign a category name to a repo/module pair.

    Parameters:
        rules: List of CategoryRule objects.
        repo: Repository path string.
        module: Optional module path string.

    Returns:
        The matching category name, ``"uncategorized"`` when
        rules exist but none match, or None when no rules
        are configured.
    """
    for rule in rules:
        if rule.repo_patterns and _match_any(repo, rule.repo_patterns):
            return str(rule.name)
        if module and rule.module_patterns and _match_any(module, rule.module_patterns):
            return str(rule.name)
    return "uncategorized" if rules else None


def _collect_updates(
    latest_ref_fn: Callable[[SourceRef], str | None],
    sources: list[SourceRef],
    category_rules: list,
    max_workers: int = 10,
) -> list[UpdateEntry]:
    """Resolve latest refs and build the list of updates.

    Resolves each unique repository in parallel, then compares
    the current ref with the latest to produce update entries.

    Parameters:
        latest_ref_fn: Callable that returns the latest ref
            for a given SourceRef.
        sources: Discovered source references.
        category_rules: Category rules from config.
        max_workers: Thread pool size.

    Returns:
        A list of UpdateEntry instances ready for reporting
        or applying.
    """
    unique_repos: dict[str, SourceRef] = {}
    for source in sources:
        if source.repo not in unique_repos:
            unique_repos[source.repo] = source

    by_repo: dict[str, str | None] = {}
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=max_workers,
    ) as executor:
        future_to_repo = {
            executor.submit(latest_ref_fn, src): repo for repo, src in unique_repos.items()
        }
        for future in concurrent.futures.as_completed(
            future_to_repo,
        ):
            repo = future_to_repo[future]
            try:
                by_repo[repo] = future.result()
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Failed to resolve latest ref for %s: %s",
                    repo,
                    exc,
                )
                by_repo[repo] = None

    updates: list[UpdateEntry] = []
    for source in sources:
        latest_ref = by_repo.get(source.repo)
        if not latest_ref or latest_ref == source.ref:
            continue

        new_source = source.raw.replace(f"ref={source.ref}", f"ref={latest_ref}")

        module_id = source.module if source.module else "root"
        unique_module = f"{module_id}@{source.file_path}"

        category = _categorize(category_rules, source.repo, source.module)

        entry = UpdateEntry(
            repo=source.repo,
            repo_host=source.repo_host,
            repo_url=source.repo_url,
            module=unique_module,
            base_module=source.module,
            file=source.file_path,
            current_ref=source.ref,
            latest_ref=latest_ref,
            strategy="latest",
            files=[source.file_path],
            replacements=[Replacement(old=source.raw, new=new_source)],
            category=category,
        )

        updates.append(entry)

    return updates


def _print_category_summary(
    updates: list[UpdateEntry],
) -> None:
    """Print a one-line summary of update counts per category."""
    if not updates:
        return

    counts: dict[str, int] = {}
    for update in updates:
        category = update.category or "uncategorized"
        counts[category] = counts.get(category, 0) + 1

    summary = ", ".join(f"{name}: {count}" for name, count in sorted(counts.items()))
    print(f"Updates by category: {summary}")


def _create_clients(
    args: argparse.Namespace,
) -> tuple[GitHubClient, GitLabClient, GitClient, str | None, str | None]:
    """Instantiate API clients and resolve tokens.

    Token resolution priority: CLI flag > environment
    variable > shared ``--token`` flag.

    Parameters:
        args: Parsed CLI arguments.

    Returns:
        A tuple of (github_client, gitlab_client, git_client,
        github_token, gitlab_token).
    """
    github_token = args.github_token or os.environ.get("GITHUB_TOKEN") or args.token
    gitlab_token = args.gitlab_token or os.environ.get("GITLAB_TOKEN") or args.token
    github_client = GitHubClient(
        base_url=args.github_base_url,
        token=github_token,
        timeout=args.timeout,
    )
    gitlab_client = GitLabClient(
        base_url=args.gitlab_base_url,
        token=gitlab_token,
        timeout=args.timeout,
    )
    git_client = GitClient(timeout=args.timeout)
    return (
        github_client,
        gitlab_client,
        git_client,
        github_token,
        gitlab_token,
    )


def _validate_tokens(
    args: argparse.Namespace,
    github_client: GitHubClient,
    gitlab_client: GitLabClient,
    github_token: str | None,
    gitlab_token: str | None,
) -> bool:
    """Validate configured API tokens when requested.

    Parameters:
        args: Parsed CLI arguments.
        github_client: GitHub API client.
        gitlab_client: GitLab API client.
        github_token: Resolved GitHub token (may be None).
        gitlab_token: Resolved GitLab token (may be None).

    Returns:
        True if validation passed or was skipped,
        False if a token failed validation.
    """
    if not args.validate_token:
        return True

    validated_any = False
    if github_token:
        validated_any = True
        try:
            github_client.validate_token()
        except AuthenticationError:
            logger.error("GitHub token validation failed")
            return False
    if gitlab_token:
        validated_any = True
        try:
            gitlab_client.validate_token()
        except AuthenticationError:
            logger.error("GitLab token validation failed")
            return False
    if validated_any:
        print("Tokens validated successfully.")
    else:
        print("No token provided. Token validation skipped.")
    return True


def main(argv: list[str] | None = None) -> int:
    """Entry point for the Agronomist CLI.

    Orchestrates scanning, version resolution, optional
    in-place updates, and report generation.

    Parameters:
        argv: Argument list; defaults to ``sys.argv[1:]``.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    args = _parse_args(argv or sys.argv[1:])

    log_level = logging.DEBUG if args.verbose else (logging.WARNING if args.quiet else logging.INFO)
    logging.basicConfig(
        level=log_level,
        format="%(levelname)s: %(message)s",
    )

    try:
        config = load_config(args.config, args.root)
    except ConfigError as exc:
        logger.error("Configuration error: %s", exc)
        return 1

    sources = scan_sources(
        args.root,
        include=args.include,
        exclude=args.exclude,
        blacklist_repos=config.blacklist.repos,
        blacklist_modules=config.blacklist.modules,
        blacklist_files=config.blacklist.files,
    )

    (
        github_client,
        gitlab_client,
        git_client,
        github_token,
        gitlab_token,
    ) = _create_clients(args)

    if not _validate_tokens(
        args,
        github_client,
        gitlab_client,
        github_token,
        gitlab_token,
    ):
        return 1

    base_host = urlparse(args.github_base_url).netloc
    github_hosts = {"github.com"}
    if base_host:
        github_hosts.add(base_host)

    def _latest_ref(source: SourceRef) -> str | None:
        """Resolve latest ref using the configured strategy."""
        gitlab_host = GitLabClient.detect_gitlab_host(source.repo_url)

        if args.resolver == "github":
            if source.repo_host in github_hosts:
                ref = github_client.latest_ref(source.repo)
                if ref:
                    return ref
            return git_client.latest_ref(source.repo_url)

        if args.resolver == "git":
            return git_client.latest_ref(source.repo_url)

        if args.resolver == "auto":
            if gitlab_host:
                ref = gitlab_client.latest_ref(source.repo_url)
                if ref:
                    return ref
            elif source.repo_host in github_hosts:
                ref = github_client.latest_ref(source.repo)
                if ref:
                    return ref
            return git_client.latest_ref(source.repo_url)

        return None

    updates = _collect_updates(
        _latest_ref,
        sources,
        config.categories,
        max_workers=args.workers,
    )

    if updates:
        if not args.no_report:
            update_dicts = [u.to_dict() for u in updates]
            report = build_report(args.root, update_dicts)
            write_report(args.output, report)

            if args.markdown:
                write_markdown(args.markdown, report)
                print(f"Markdown report written to {args.markdown}.")

            print(f"Report written to {args.output}.")

        if args.command == "update":
            touched = apply_updates(args.root, updates)
            if touched:
                print(f"Updated {len(touched)} file(s).")
            else:
                print("No updates applied.")

        _print_category_summary(updates)
    else:
        print("No updates found.")

    return 0
