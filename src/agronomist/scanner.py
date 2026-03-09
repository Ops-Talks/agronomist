"""File scanner that discovers Git-sourced Terraform modules.

Walks a directory tree, matches Terraform/HCL files, and
extracts ``source = "git::..."`` references along with their
version refs.
"""

from __future__ import annotations

import fnmatch
import os
import re
from collections.abc import Iterable
from urllib.parse import urlparse

from .models import SourceRef

_SOURCE_RE = re.compile(r"source\s*=\s*(['\"])(?P<source>[^'\"]+)\1")

# Matches HTTPS and ssh:// scheme URLs
_GIT_SOURCE_RE = re.compile(
    r"(?:git::)?(?P<url>(?:https?|ssh)://[^?]+?)"
    r"(?:\.git)?(?P<module>//[^?]+)?"
    r"\?ref=(?P<ref>[^&]+)"
)

# Matches SCP-style SSH URLs (git@host:owner/repo)
_SSH_SCP_RE = re.compile(
    r"(?:git::)?git@(?P<host>[^:]+):"
    r"(?P<path>[^?]+?)"
    r"(?:\.git)?(?P<module>//[^?]+)?"
    r"\?ref=(?P<ref>[^&]+)"
)


def _match_any(path: str, patterns: Iterable[str]) -> bool:
    """Return True if *path* matches any of the glob *patterns*.

    Parameters:
        path: The file path string to test.
        patterns: An iterable of ``fnmatch``-style patterns.

    Returns:
        True when at least one pattern matches.
    """
    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)


def _parse_git_source(source: str) -> SourceRef | None:
    """Parse a Git module source string into a SourceRef.

    Handles HTTPS, ``ssh://``, and SCP-style SSH URLs, with
    or without the ``git::`` prefix and optional ``//module``
    sub-paths.

    Parameters:
        source: Raw source value from a Terraform file.

    Returns:
        A SourceRef with an empty ``file_path`` (to be filled
        by the caller), or None if the string is not a valid
        Git source.
    """
    # Try HTTPS / ssh:// scheme first
    match = _GIT_SOURCE_RE.search(source)
    if match:
        return _build_ref_from_url(source, match)

    # Try SCP-style SSH (git@host:path)
    match = _SSH_SCP_RE.search(source)
    if match:
        return _build_ref_from_scp(source, match)

    return None


def _build_ref_from_url(
    source: str,
    match: re.Match,
) -> SourceRef | None:
    """Build a SourceRef from an HTTPS or ssh:// regex match.

    Parameters:
        source: Original raw source string.
        match: A regex match with ``url``, ``module``, and
            ``ref`` named groups.

    Returns:
        A SourceRef or None when the URL cannot be parsed.
    """
    url = match.group("url")
    module = match.group("module")
    ref = match.group("ref")

    parsed = urlparse(url)
    if not parsed.netloc or not parsed.path:
        return None

    # hostname strips user@ (e.g. git@gitlab.com -> gitlab.com)
    repo_host = parsed.hostname or parsed.netloc
    repo_path = parsed.path.lstrip("/")
    if repo_path.endswith(".git"):
        repo_path = repo_path[:-4]

    # Normalize SSH-scheme URLs to HTTPS for API compatibility
    if parsed.scheme == "ssh":
        repo_url = f"https://{repo_host}/{repo_path}"
    else:
        repo_url = url

    module_clean = module[2:] if module else None
    return SourceRef(
        file_path="",
        raw=source,
        repo=repo_path,
        repo_url=repo_url,
        repo_host=repo_host,
        ref=ref,
        module=module_clean,
    )


def _build_ref_from_scp(
    source: str,
    match: re.Match,
) -> SourceRef:
    """Build a SourceRef from an SCP-style SSH regex match.

    Converts ``git@host:owner/repo`` to an HTTPS ``repo_url``
    for downstream API compatibility.

    Parameters:
        source: Original raw source string.
        match: A regex match with ``host``, ``path``,
            ``module``, and ``ref`` named groups.

    Returns:
        A SourceRef with HTTPS-normalized ``repo_url``.
    """
    host = match.group("host")
    path = match.group("path")
    module = match.group("module")
    ref = match.group("ref")

    if path.endswith(".git"):
        path = path[:-4]

    repo_url = f"https://{host}/{path}"
    module_clean = module[2:] if module else None
    return SourceRef(
        file_path="",
        raw=source,
        repo=path,
        repo_url=repo_url,
        repo_host=host,
        ref=ref,
        module=module_clean,
    )


def scan_sources(
    root: str,
    include: list[str] | None = None,
    exclude: list[str] | None = None,
    blacklist_repos: list[str] | None = None,
    blacklist_modules: list[str] | None = None,
    blacklist_files: list[str] | None = None,
) -> list[SourceRef]:
    """Walk *root* and collect all Git module source refs.

    Parameters:
        root: Directory to scan recursively.
        include: Glob patterns for files to include
            (defaults to ``["**/*.hcl", "**/*.tf"]``).
        exclude: Glob patterns for files to skip.
        blacklist_repos: Repo patterns to ignore.
        blacklist_modules: Module patterns to ignore.
        blacklist_files: File-path patterns to ignore.

    Returns:
        A list of SourceRef objects found in matching files.
    """
    include = include or ["**/*.hcl", "**/*.tf"]
    exclude = exclude or []
    blacklist_repos = blacklist_repos or []
    blacklist_modules = blacklist_modules or []
    blacklist_files = blacklist_files or []

    results: list[SourceRef] = []
    for dirpath, _, filenames in os.walk(root):
        for filename in filenames:
            rel_path = os.path.relpath(os.path.join(dirpath, filename), root)
            if include and not _match_any(rel_path, include):
                continue
            if exclude and _match_any(rel_path, exclude):
                continue
            if blacklist_files and _match_any(rel_path, blacklist_files):
                continue

            full_path = os.path.join(root, rel_path)
            try:
                with open(full_path, encoding="utf-8", newline="") as handle:
                    content = handle.read()
            except OSError:
                continue

            for match in _SOURCE_RE.finditer(content):
                source = match.group("source")
                parsed = _parse_git_source(source)
                if not parsed:
                    continue

                # Apply blacklist filters
                if blacklist_repos and _match_any(parsed.repo, blacklist_repos):
                    continue
                if (
                    parsed.module
                    and blacklist_modules
                    and _match_any(parsed.module, blacklist_modules)
                ):
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
