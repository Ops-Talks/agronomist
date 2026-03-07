"""Data models used across Agronomist modules."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class SourceRef:
    """Immutable reference to a Terraform/HCL module source.

    Attributes:
        file_path: Path of the file relative to the scan root.
        raw: The original ``source = "..."`` value as written.
        repo: Repository path (e.g. ``owner/name``).
        repo_url: Full HTTPS URL of the repository.
        repo_host: Hostname of the repository (e.g. ``github.com``).
        ref: Current version ref (tag or branch).
        module: Optional sub-module path inside the repository.
    """

    file_path: str
    raw: str
    repo: str
    repo_url: str
    repo_host: str
    ref: str
    module: str | None = None


@dataclass(frozen=True)
class Replacement:
    """A single source-string substitution.

    Attributes:
        old: The original source string to find.
        new: The replacement source string.
    """

    old: str
    new: str

    def to_dict(self) -> dict[str, str]:
        """Serialize to a JSON-compatible dict.

        Returns:
            A dict with ``from`` and ``to`` keys.
        """
        return {"from": self.old, "to": self.new}


@dataclass(frozen=True)
class UpdateEntry:
    """A single version-update action for one source reference.

    Attributes:
        repo: Repository path (e.g. ``owner/name``).
        repo_host: Hostname of the repository host.
        repo_url: Full HTTPS URL of the repository.
        module: Unique module identifier (``module@file``).
        base_module: Original module path (may be None).
        file: Primary file path for this update.
        current_ref: The version ref currently in the file.
        latest_ref: The resolved latest version ref.
        strategy: Resolution strategy used (e.g. ``latest``).
        files: List of file paths affected by this update.
        replacements: List of string substitutions to apply.
        category: Optional category assigned by config rules.
    """

    repo: str
    repo_host: str
    repo_url: str
    module: str
    base_module: str | None
    file: str
    current_ref: str
    latest_ref: str
    strategy: str
    files: list[str] = field(default_factory=list)
    replacements: list[Replacement] = field(default_factory=list)
    category: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dict.

        Returns:
            A dict suitable for JSON report serialization.
        """
        result: dict[str, Any] = {
            "repo": self.repo,
            "repo_host": self.repo_host,
            "repo_url": self.repo_url,
            "module": self.module,
            "base_module": self.base_module,
            "file": self.file,
            "current_ref": self.current_ref,
            "latest_ref": self.latest_ref,
            "strategy": self.strategy,
            "files": self.files,
            "replacements": [r.to_dict() for r in self.replacements],
        }
        if self.category is not None:
            result["category"] = self.category
        return result
