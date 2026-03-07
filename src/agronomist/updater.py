"""Module for applying version updates to Terraform/HCL files."""

from __future__ import annotations

import logging
import os

from .fileutil import atomic_write
from .models import UpdateEntry

logger = logging.getLogger(__name__)


def _is_safe_path(root: str, file_path: str) -> bool:
    """Check that file_path resolves to a location inside root.

    Prevents path traversal attacks where a crafted file_path
    such as ``../../etc/passwd`` could write outside the
    intended directory.

    Parameters:
        root: The root directory that all paths must stay
            within.
        file_path: The relative file path to validate.

    Returns:
        True if the resolved path is inside *root*,
        False otherwise.
    """
    full_path = os.path.join(root, file_path)
    resolved = os.path.realpath(full_path)
    root_resolved = os.path.realpath(root)
    return resolved.startswith(root_resolved + os.sep) or resolved == root_resolved


def apply_updates(
    root: str,
    updates: list[UpdateEntry],
) -> list[str]:
    """Apply version-ref replacements to files on disk.

    Groups all pending replacements by file, reads each file
    once, applies every substitution, and writes the result
    back only when the content actually changed.

    Parameters:
        root: The root directory containing target files.
        updates: A list of UpdateEntry instances containing
            file paths and replacement pairs.

    Returns:
        A list of relative file paths that were modified.
    """
    touched: list[str] = []

    updates_by_file: dict[str, list[UpdateEntry]] = {}
    for update in updates:
        for file_path in update.files:
            updates_by_file.setdefault(file_path, []).append(update)

    for file_path, file_updates in updates_by_file.items():
        if not _is_safe_path(root, file_path):
            logger.warning(
                "Path traversal detected, skipping: %s",
                file_path,
            )
            continue

        full_path = os.path.join(root, file_path)
        try:
            with open(full_path, encoding="utf-8", newline="") as handle:
                content = handle.read()
        except OSError:
            continue

        new_content = content
        for update in file_updates:
            for replacement in update.replacements:
                new_content = new_content.replace(replacement.old, replacement.new, 1)

        if new_content != content:
            atomic_write(full_path, new_content, newline="")
            touched.append(file_path)

    return touched
