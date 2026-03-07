"""Data models used across Agronomist modules."""

from __future__ import annotations

from dataclasses import dataclass


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
