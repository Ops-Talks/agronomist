from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceRef:
    file_path: str
    raw: str
    repo: str
    repo_url: str
    repo_host: str
    ref: str
    module: str | None = None
