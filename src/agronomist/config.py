from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import yaml


@dataclass(frozen=True)
class CategoryRule:
    name: str
    repo_patterns: List[str]
    module_patterns: List[str]


def _normalize_rules(data: Dict[str, Any]) -> List[CategoryRule]:
    rules: List[CategoryRule] = []
    for item in data.get("categories", []) or []:
        name = item.get("name")
        if not name:
            continue
        rules.append(
            CategoryRule(
                name=name,
                repo_patterns=item.get("repo_patterns", []) or [],
                module_patterns=item.get("module_patterns", []) or [],
            )
        )
    return rules


def load_config(path: str, root: str) -> List[CategoryRule]:
    if not path:
        return []

    full_path = path
    if not os.path.isabs(path):
        full_path = os.path.join(root, path)

    if not os.path.exists(full_path):
        return []

    with open(full_path, "r", encoding="utf-8") as handle:
        if full_path.endswith(".json"):
            data = json.load(handle)
        else:
            data = yaml.safe_load(handle) or {}

    if not isinstance(data, dict):
        return []

    return _normalize_rules(data)
