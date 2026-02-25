from __future__ import annotations

import argparse
import fnmatch
import logging
import os
import sys
from collections.abc import Callable
from urllib.parse import urlparse

from .config import load_config
from .git import GitClient
from .github import GitHubClient
from .gitlab import GitLabClient
from .markdown import write_markdown
from .models import SourceRef
from .report import build_report, write_report
from .scanner import scan_sources
from .updater import apply_updates

logger = logging.getLogger(__name__)


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="agronomist",
        description="Detect and update Terraform module versions across repositories",
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
        "report", help="Generate a version report for all Terraform modules"
    )
    report_parser.add_argument("--root", default=".")
    report_parser.add_argument("--include", action="append", default=[])
    report_parser.add_argument("--exclude", action="append", default=[])
    report_parser.add_argument("--github-base-url", default="https://api.github.com")
    report_parser.add_argument(
        "--token",
        default=None,
        help="Shared fallback token for GitHub/GitLab when specific tokens are not provided",
    )
    report_parser.add_argument(
        "--github-token",
        default=None,
        help="GitHub API token (overrides GITHUB_TOKEN env var)",
    )
    report_parser.add_argument(
        "--gitlab-token",
        default=None,
        help="GitLab API token (overrides GITLAB_TOKEN env var)",
    )
    report_parser.add_argument("--config", default=".agronomist.yaml")
    report_parser.add_argument(
        "--resolver",
        default="git",
        choices=["git", "github", "auto"],
        help="How to resolve the latest version: git, github or auto",
    )
    report_parser.add_argument("--output", default="report.json")
    report_parser.add_argument(
        "--markdown",
        default=None,
        help="Generate Markdown report (e.g.: report.md)",
    )
    report_parser.add_argument(
        "--validate-token",
        action="store_true",
        help="Validate token before processing (useful for CI/CD)",
    )
    report_parser.add_argument(
        "--no-report",
        action="store_true",
        help="Skip generating report files (useful for CI/CD pipelines)",
    )

    update_parser = subparsers.add_parser(
        "update", help="Update Terraform modules to their latest versions and generate report"
    )
    update_parser.add_argument("--root", default=".")
    update_parser.add_argument("--include", action="append", default=[])
    update_parser.add_argument("--exclude", action="append", default=[])
    update_parser.add_argument("--github-base-url", default="https://api.github.com")
    update_parser.add_argument(
        "--token",
        default=None,
        help="Shared fallback token for GitHub/GitLab when specific tokens are not provided",
    )
    update_parser.add_argument(
        "--github-token",
        default=None,
        help="GitHub API token (overrides GITHUB_TOKEN env var)",
    )
    update_parser.add_argument(
        "--gitlab-token",
        default=None,
        help="GitLab API token (overrides GITLAB_TOKEN env var)",
    )
    update_parser.add_argument("--config", default=".agronomist.yaml")
    update_parser.add_argument(
        "--resolver",
        default="git",
        choices=["git", "github", "auto"],
        help="How to resolve the latest version: git, github or auto",
    )
    update_parser.add_argument("--output", default="report.json")
    update_parser.add_argument(
        "--markdown",
        default=None,
        help="Generate Markdown report (e.g.: report.md)",
    )
    update_parser.add_argument(
        "--validate-token",
        action="store_true",
        help="Validate token before processing (useful for CI/CD)",
    )
    update_parser.add_argument(
        "--no-report",
        action="store_true",
        help="Skip generating report files (useful for CI/CD pipelines)",
    )

    args = parser.parse_args(argv)

    if not argv or not args.command:
        parser.print_help()
        sys.exit(0)

    return args


def _match_any(value: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(value, pattern) for pattern in patterns)


def _categorize(rules: list, repo: str, module: str | None) -> str | None:
    for rule in rules:
        if rule.repo_patterns and _match_any(repo, rule.repo_patterns):
            return rule.name
        if module and rule.module_patterns and _match_any(module, rule.module_patterns):
            return rule.name
    return "uncategorized" if rules else None


def _collect_updates(
    latest_ref_fn: Callable[[SourceRef], str | None],
    sources: list[SourceRef],
    category_rules: list,
) -> list[dict[str, object]]:
    by_repo: dict[str, str | None] = {}
    updates: list[dict[str, object]] = []

    for source in sources:
        if source.repo not in by_repo:
            by_repo[source.repo] = latest_ref_fn(source)

        latest_ref = by_repo[source.repo]
        if not latest_ref or latest_ref == source.ref:
            continue

        new_source = source.raw.replace(f"ref={source.ref}", f"ref={latest_ref}")

        # Create unique module identifier by combining module with file path
        # This ensures each file gets its own update entry and PR
        module_id = source.module if source.module else "root"
        # Use file path to create unique identifier per file
        unique_module = f"{module_id}@{source.file_path}"

        update = {
            "repo": source.repo,
            "repo_host": source.repo_host,
            "repo_url": source.repo_url,
            "module": unique_module,
            "base_module": source.module,  # Keep original module for reference
            "file": source.file_path,  # Primary file for this update
            "current_ref": source.ref,
            "latest_ref": latest_ref,
            "strategy": "latest",
            "files": [source.file_path],
            "replacements": [{"from": source.raw, "to": new_source}],
        }

        category = _categorize(category_rules, source.repo, source.module)
        if category:
            update["category"] = category

        updates.append(update)

    return updates


def _print_category_summary(updates: list[dict[str, object]]) -> None:
    if not updates:
        return

    counts: dict[str, int] = {}
    for update in updates:
        category = update.get("category", "uncategorized")
        counts[category] = counts.get(category, 0) + 1

    summary = ", ".join(f"{name}: {count}" for name, count in sorted(counts.items()))
    print(f"Updates by category: {summary}")


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv or sys.argv[1:])

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    config = load_config(args.config, args.root)
    sources = scan_sources(
        args.root,
        include=args.include,
        exclude=args.exclude,
        blacklist_repos=config.blacklist.repos,
        blacklist_modules=config.blacklist.modules,
        blacklist_files=config.blacklist.files,
    )

    github_token = args.github_token or os.environ.get("GITHUB_TOKEN") or args.token
    gitlab_token = args.gitlab_token or os.environ.get("GITLAB_TOKEN") or args.token
    github_client = GitHubClient(base_url=args.github_base_url, token=github_token)
    gitlab_client = GitLabClient(base_url="https://gitlab.com", token=gitlab_token)
    git_client = GitClient()

    if args.validate_token:
        validated_any = False
        if github_token:
            validated_any = True
            if not github_client.validate_token():
                logger.error("GitHub token validation failed")
                return 1
        if gitlab_token:
            validated_any = True
            if not gitlab_client.validate_token():
                logger.error("GitLab token validation failed")
                return 1
        if validated_any:
            print("Tokens validated successfully.")
        else:
            print("No token provided. Token validation skipped.")

    base_host = urlparse(args.github_base_url).netloc
    github_hosts = {"github.com"}
    if base_host:
        github_hosts.add(base_host)

    def _latest_ref(source: SourceRef) -> str | None:
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

    updates = _collect_updates(_latest_ref, sources, config.categories)

    if updates:
        if not args.no_report:
            report = build_report(args.root, updates)
            write_report(args.output, report)

            if args.markdown:
                write_markdown(args.markdown, report)
                print(f"Markdown report written to {args.markdown}.")

            if args.command == "update":
                print(f"Report written to {args.output}.")
            else:
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
