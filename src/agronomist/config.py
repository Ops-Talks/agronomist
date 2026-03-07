"""Configuration loader for Agronomist.

Reads category rules and blacklist settings from YAML or JSON
files. Provides sensible defaults when no configuration file
exists.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

import yaml


@dataclass(frozen=True)
class CategoryRule:
    """A rule that assigns a category name to matching updates.

    Attributes:
        name: Human-readable category label.
        repo_patterns: Glob patterns matched against repo paths.
        module_patterns: Glob patterns matched against modules.
    """

    name: str
    repo_patterns: list[str]
    module_patterns: list[str]


@dataclass(frozen=True)
class Blacklist:
    """Glob patterns used to exclude resources from scanning.

    Attributes:
        repos: Patterns to exclude repositories.
        modules: Patterns to exclude sub-modules.
        files: Patterns to exclude file paths.
    """

    repos: list[str]
    modules: list[str]
    files: list[str]


@dataclass(frozen=True)
class Config:
    """Top-level configuration container.

    Attributes:
        categories: Ordered list of category assignment rules.
        blacklist: Patterns for resources to ignore entirely.
    """

    categories: list[CategoryRule]
    blacklist: Blacklist


def _normalize_rules(data: dict[str, Any]) -> list[CategoryRule]:
    """Parse raw config data into a list of CategoryRule objects.

    Entries without a ``name`` field are silently skipped.

    Parameters:
        data: Top-level config dict (may contain ``categories``).

    Returns:
        A list of validated CategoryRule instances.
    """
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
    """Load and parse an Agronomist configuration file.

    Supports both YAML and JSON formats. Returns a default
    empty configuration when the file does not exist or the
    path is empty.

    Parameters:
        path: Relative or absolute path to the config file.
        root: Root directory used to resolve relative paths.

    Returns:
        A Config instance with categories and blacklist.
    """
    empty = Config(
        categories=[],
        blacklist=Blacklist(repos=[], modules=[], files=[]),
    )

    if not path:
        return empty

    full_path = path
    if not os.path.isabs(path):
        full_path = os.path.join(root, path)

    if not os.path.exists(full_path):
        return empty

    with open(full_path, encoding="utf-8") as handle:
        if full_path.endswith(".json"):
            data = json.load(handle)
        else:
            data = yaml.safe_load(handle) or {}

    if not isinstance(data, dict):
        return empty

    categories = _normalize_rules(data)
    blacklist_data = data.get("blacklist", {}) or {}
    blacklist = Blacklist(
        repos=blacklist_data.get("repos", []) or [],
        modules=blacklist_data.get("modules", []) or [],
        files=blacklist_data.get("files", []) or [],
    )

    return Config(categories=categories, blacklist=blacklist)
