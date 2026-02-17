from __future__ import annotations

import argparse
import fnmatch
import logging
import os
import sys
from typing import Callable, Dict, List, Optional
from urllib.parse import urlparse

from .config import CategoryRule, load_config
from .git import GitClient
from .github import GitHubClient
from .gitlab import GitLabClient
from .markdown import write_markdown
from .models import SourceRef
from .report import build_report, write_report
from .scanner import scan_sources
from .updater import apply_updates

logger = logging.getLogger(__name__)


def _parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="agronomist")

    subparsers = parser.add_subparsers(dest="command", required=True)

    report_parser = subparsers.add_parser("report")
    report_parser.add_argument("--root", default=".")
    report_parser.add_argument("--include", action="append", default=[])
    report_parser.add_argument("--exclude", action="append", default=[])
    report_parser.add_argument("--github-base-url", default="https://api.github.com")
    report_parser.add_argument("--token", default=None)
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

    update_parser = subparsers.add_parser("update")
    update_parser.add_argument("--root", default=".")
    update_parser.add_argument("--include", action="append", default=[])
    update_parser.add_argument("--exclude", action="append", default=[])
    update_parser.add_argument("--github-base-url", default="https://api.github.com")
    update_parser.add_argument("--token", default=None)
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

    return parser.parse_args(argv)


def _match_any(value: str, patterns: List[str]) -> bool:
    return any(fnmatch.fnmatch(value, pattern) for pattern in patterns)


def _categorize(rules: List[CategoryRule], repo: str, module: Optional[str]) -> Optional[str]:
    for rule in rules:
        if rule.repo_patterns and _match_any(repo, rule.repo_patterns):
            return rule.name
        if module and rule.module_patterns and _match_any(module, rule.module_patterns):
            return rule.name
    return "uncategorized" if rules else None


def _collect_updates(
    latest_ref_fn: Callable[[SourceRef], Optional[str]],
    sources: List[SourceRef],
    category_rules: List[CategoryRule],
) -> List[Dict[str, object]]:
    by_repo: Dict[str, Optional[str]] = {}
    updates: List[Dict[str, object]] = []

    for source in sources:
        if source.repo not in by_repo:
            by_repo[source.repo] = latest_ref_fn(source)

        latest_ref = by_repo[source.repo]
        if not latest_ref or latest_ref == source.ref:
            continue

        new_source = source.raw.replace(f"ref={source.ref}", f"ref={latest_ref}")
        update = {
            "repo": source.repo,
            "repo_host": source.repo_host,
            "repo_url": source.repo_url,
            "module": source.module,
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


def _print_category_summary(updates: List[Dict[str, object]]) -> None:
    if not updates:
        return

    counts: Dict[str, int] = {}
    for update in updates:
        category = update.get("category", "uncategorized")
        counts[category] = counts.get(category, 0) + 1

    summary = ", ".join(f"{name}: {count}" for name, count in sorted(counts.items()))
    print(f"Updates by category: {summary}")


def main(argv: List[str] | None = None) -> int:
    args = _parse_args(argv or sys.argv[1:])

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    category_rules = load_config(args.config, args.root)
    sources = scan_sources(args.root, include=args.include, exclude=args.exclude)

    token = args.token or os.environ.get("GITHUB_TOKEN")
    github_client = GitHubClient(base_url=args.github_base_url, token=token)
    gitlab_client = GitLabClient(base_url="https://gitlab.com", token=token)
    git_client = GitClient()

    if args.validate_token:
        if token:
            if not github_client.validate_token():
                logger.error("GitHub token validation failed")
                return 1
            if not gitlab_client.validate_token():
                logger.error("GitLab token validation failed")
                return 1
            print("Tokens validated successfully.")
        else:
            print("No token provided. Token validation skipped.")

    base_host = urlparse(args.github_base_url).netloc
    github_hosts = {"github.com"}
    if base_host:
        github_hosts.add(base_host)

    def _latest_ref(source: SourceRef) -> Optional[str]:
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

    updates = _collect_updates(_latest_ref, sources, category_rules)

    report = build_report(args.root, updates)
    write_report(args.output, report)

    if args.markdown:
        write_markdown(args.markdown, report)
        print(f"Markdown report written to {args.markdown}.")

    if args.command == "update":
        touched = apply_updates(args.root, updates)
        if touched:
            print(f"Updated {len(touched)} file(s).")
        else:
            print("No updates applied.")
    else:
        print(f"Report written to {args.output}.")

    _print_category_summary(updates)

    return 0

