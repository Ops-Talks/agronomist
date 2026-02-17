from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class SourceRef:
    file_path: str
    raw: str
    repo: str
    repo_url: str
    repo_host: str
    ref: str
    module: Optional[str] = None
