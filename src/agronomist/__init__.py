"""Agronomist package."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

try:
    __version__: str = version("agronomist")
except PackageNotFoundError:
    __version__ = "0.0.0"

__all__: list[str] = [
    "cli",
    "config",
    "exceptions",
    "fileutil",
    "git",
    "github",
    "gitlab",
    "http",
    "markdown",
    "models",
    "report",
    "scanner",
    "updater",
]
