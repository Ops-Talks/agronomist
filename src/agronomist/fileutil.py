"""Shared file-writing utilities for Agronomist.

Provides an atomic write helper that prevents file corruption
when the process is interrupted mid-write.
"""

from __future__ import annotations

import os
import tempfile


def atomic_write(
    path: str,
    content: str,
    newline: str | None = None,
) -> None:
    """Write content to a file atomically.

    Creates a temporary file in the same directory, writes
    the content, then atomically replaces the target path.
    If any error occurs after the temp file is created, it
    is removed before the exception propagates.

    Parameters:
        path: Destination file path.
        content: String content to write.
        newline: Newline translation mode passed to
            ``os.fdopen``.  Use ``""`` to preserve
            original line endings (e.g. when round-
            tripping file content).  Defaults to the
            platform default when ``None``.

    Raises:
        OSError: If the temporary file cannot be created
            or the rename fails.
    """
    dir_name = os.path.dirname(path) or "."
    fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline=newline) as handle:
            handle.write(content)
        os.replace(tmp_path, path)
    except BaseException:
        os.unlink(tmp_path)
        raise
