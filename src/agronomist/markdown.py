from __future__ import annotations

import json
from typing import Any, Dict, List


def _group_by_repo(updates: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    by_repo: Dict[str, List[Dict[str, Any]]] = {}
    for update in updates:
        repo = update.get("repo", "unknown")
        if repo not in by_repo:
            by_repo[repo] = []
        by_repo[repo].append(update)
    return by_repo


def _group_by_module(updates: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    by_module: Dict[str, List[Dict[str, Any]]] = {}
    for update in updates:
        module = update.get("module", "root")
        if module not in by_module:
            by_module[module] = []
        by_module[module].append(update)
    return by_module


def generate_markdown(report: Dict[str, Any]) -> str:
    updates = report.get("updates", [])
    if not updates:
        return "# Agronomist Report\n\nNenhuma atualização disponível.\n"

    lines = [
        "# Agronomist Report",
        "",
        f"**Gerado em:** {report.get('generated_at', 'N/A')}",
        f"**Raiz:** `{report.get('root', '.')}`",
        "",
    ]

    by_repo = _group_by_repo(updates)
    total_updates = len(updates)
    unique_repos = len(by_repo)
    unique_modules = len(set(u.get("module") for u in updates))

    lines.extend(
        [
            "## Resumo",
            "",
            f"- **Total de atualizações:** {total_updates}",
            f"- **Repositórios afetados:** {unique_repos}",
            f"- **Módulos afetados:** {unique_modules}",
            "",
        ]
    )

    lines.extend(
        [
            "## Atualizações por Repositório",
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
                lines.append(f"#### Módulo: `{module}`")
            else:
                lines.append("#### Raiz")
            lines.append("")

            for update in module_updates:
                current = update.get("current_ref", "?")
                latest = update.get("latest_ref", "?")
                files = update.get("files", [])
                category = update.get("category", "")

                lines.append(f"**{current} → {latest}**")
                if category:
                    lines.append(f"- Categoria: `{category}`")
                lines.append(f"- Arquivos afetados: {len(files)}")
                if len(files) <= 3:
                    for file in files:
                        lines.append(f"  - `{file}`")
                else:
                    for file in files[:3]:
                        lines.append(f"  - `{file}`")
                    lines.append(f"  - ... e mais {len(files) - 3}")
                lines.append("")

    return "\n".join(lines)


def write_markdown(path: str, report: Dict[str, Any]) -> None:
    markdown = generate_markdown(report)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(markdown)
