from __future__ import annotations

import fnmatch
import os
import re
from collections.abc import Iterable
from urllib.parse import urlparse

from .models import SourceRef

_SOURCE_RE = re.compile(r"source\s*=\s*(['\"])(?P<source>[^'\"]+)\1")
_GIT_SOURCE_RE = re.compile(
    r"(?:git::)?(?P<url>https?://[^?]+?)(?:\.git)?(?P<module>//[^?]+)?\?ref=(?P<ref>[^&]+)"
)


def _match_any(path: str, patterns: Iterable[str]) -> bool:
    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)


def _parse_git_source(source: str) -> SourceRef | None:
    match = _GIT_SOURCE_RE.search(source)
    if not match:
        return None

    url = match.group("url")
    module = match.group("module")
    ref = match.group("ref")

    parsed = urlparse(url)
    if not parsed.netloc or not parsed.path:
        return None
    repo_host = parsed.netloc
    repo_path = parsed.path.lstrip("/")
    if repo_path.endswith(".git"):
        repo_path = repo_path[:-4]

    module_clean = module[2:] if module else None
    return SourceRef(
        file_path="",
        raw=source,
        repo=repo_path,
        repo_url=url,
        repo_host=repo_host,
        ref=ref,
        module=module_clean,
    )


def scan_sources(
    root: str, include: list[str] | None = None, exclude: list[str] | None = None
) -> list[SourceRef]:
    include = include or ["**/*.hcl", "**/*.tf"]
    exclude = exclude or []

    results: list[SourceRef] = []
    for dirpath, _, filenames in os.walk(root):
        for filename in filenames:
            rel_path = os.path.relpath(os.path.join(dirpath, filename), root)
            if include and not _match_any(rel_path, include):
                continue
            if exclude and _match_any(rel_path, exclude):
                continue

            full_path = os.path.join(root, rel_path)
            try:
                with open(full_path, encoding="utf-8") as handle:
                    content = handle.read()
            except OSError:
                continue

            for match in _SOURCE_RE.finditer(content):
                source = match.group("source")
                parsed = _parse_git_source(source)
                if not parsed:
                    continue
                results.append(
                    SourceRef(
                        file_path=rel_path,
                        raw=parsed.raw,
                        repo=parsed.repo,
                        repo_url=parsed.repo_url,
                        repo_host=parsed.repo_host,
                        ref=parsed.ref,
                        module=parsed.module,
                    )
                )

    return results
