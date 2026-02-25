from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

import yaml


@dataclass(frozen=True)
class CategoryRule:
    name: str
    repo_patterns: list[str]
    module_patterns: list[str]


@dataclass(frozen=True)
class Blacklist:
    repos: list[str]
    modules: list[str]
    files: list[str]


@dataclass(frozen=True)
class Config:
    categories: list[CategoryRule]
    blacklist: Blacklist


def _normalize_rules(data: dict[str, Any]) -> list[CategoryRule]:
    rules: list[CategoryRule] = []
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


def load_config(path: str, root: str) -> Config:
    if not path:
        return Config(categories=[], blacklist=Blacklist(repos=[], modules=[], files=[]))

    full_path = path
    if not os.path.isabs(path):
        full_path = os.path.join(root, path)

    if not os.path.exists(full_path):
        return Config(categories=[], blacklist=Blacklist(repos=[], modules=[], files=[]))

    with open(full_path, encoding="utf-8") as handle:
        if full_path.endswith(".json"):
            data = json.load(handle)
        else:
            data = yaml.safe_load(handle) or {}

    if not isinstance(data, dict):
        return Config(categories=[], blacklist=Blacklist(repos=[], modules=[], files=[]))

    categories = _normalize_rules(data)
    blacklist_data = data.get("blacklist", {}) or {}
    blacklist = Blacklist(
        repos=blacklist_data.get("repos", []) or [],
        modules=blacklist_data.get("modules", []) or [],
        files=blacklist_data.get("files", []) or [],
    )

    return Config(categories=categories, blacklist=blacklist)
