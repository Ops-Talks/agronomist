from __future__ import annotations

from typing import Any


def _group_by_repo(updates: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    by_repo: dict[str, list[dict[str, Any]]] = {}
    for update in updates:
        repo = update.get("repo", "unknown")
        if repo not in by_repo:
            by_repo[repo] = []
        by_repo[repo].append(update)
    return by_repo


def _group_by_module(updates: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    by_module: dict[str, list[dict[str, Any]]] = {}
    for update in updates:
        # Use base_module for display grouping, fall back to module for backward compatibility
        module = update.get("base_module") or update.get("module", "root")
        if module not in by_module:
            by_module[module] = []
        by_module[module].append(update)
    return by_module


def generate_markdown(report: dict[str, Any]) -> str:
    updates = report.get("updates", [])
    if not updates:
        return "# Agronomist Report\n\nNo updates available.\n"

    lines = [
        "# Agronomist Report",
        "",
        f"**Generated at:** {report.get('generated_at', 'N/A')}",
        f"**Root:** `{report.get('root', '.')}`",
        "",
    ]

    by_repo = _group_by_repo(updates)
    total_updates = len(updates)
    unique_repos = len(by_repo)
    unique_modules = len(set(u.get("module") for u in updates))

    lines.extend(
        [
            "## Summary",
            "",
            f"- **Total updates:** {total_updates}",
            f"- **Affected repositories:** {unique_repos}",
            f"- **Affected modules:** {unique_modules}",
            "",
        ]
    )

    lines.extend(
        [
            "## Updates by Repository",
            "",
        ]
    )

    for repo in sorted(by_repo.keys()):
        repo_updates = by_repo[repo]
        repo_host = repo_updates[0].get("repo_host", "unknown")
        lines.append(f"### {repo} ({repo_host})")
        lines.append("")

        by_module = _group_by_module(repo_updates)
        for module in sorted(by_module.keys()):
            module_updates = by_module[module]
            if module and module != "root":
                lines.append(f"#### Module: `{module}`")
            else:
                lines.append("#### Root")
            lines.append("")

            for update in module_updates:
                current = update.get("current_ref", "?")
                latest = update.get("latest_ref", "?")
                files = update.get("files", [])
                category = update.get("category", "")

                lines.append(f"**{current} → {latest}**")
                if category:
                    lines.append(f"- Category: `{category}`")
                lines.append(f"- Affected files: {len(files)}")
                if len(files) <= 3:
                    for file in files:
                        lines.append(f"  - `{file}`")
                else:
                    for file in files[:3]:
                        lines.append(f"  - `{file}`")
                    lines.append(f"  - ... and {len(files) - 3} more")
                lines.append("")

    return "\n".join(lines)


def write_markdown(path: str, report: dict[str, Any]) -> None:
    markdown = generate_markdown(report)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(markdown)
