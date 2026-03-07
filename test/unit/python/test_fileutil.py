"""Unit tests for the shared fileutil module."""

from __future__ import annotations

import os

import pytest

from agronomist.fileutil import atomic_write


class TestAtomicWrite:
    """Tests for the ``atomic_write`` helper."""

    def test_writes_content(self, tmp_path: object) -> None:
        """Verify that content is written correctly."""
        path = str(tmp_path) + "/output.txt"  # type: ignore[operator]
        atomic_write(path, "hello world")
        with open(path, encoding="utf-8") as fh:
            assert fh.read() == "hello world"

    def test_overwrites_existing_file(self, tmp_path: object) -> None:
        """Verify that an existing file is replaced."""
        path = str(tmp_path) + "/output.txt"  # type: ignore[operator]
        atomic_write(path, "old")
        atomic_write(path, "new")
        with open(path, encoding="utf-8") as fh:
            assert fh.read() == "new"

    def test_preserves_newlines_when_requested(self, tmp_path: object) -> None:
        """Verify that newline='' preserves raw line endings."""
        path = str(tmp_path) + "/output.txt"  # type: ignore[operator]
        content = "line1\r\nline2\n"
        atomic_write(path, content, newline="")
        with open(path, "rb") as fh:
            raw = fh.read()
        assert b"\r\n" in raw

    def test_no_temp_file_left_on_error(
        self, tmp_path: object, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verify that temp files are cleaned up on error."""
        path = str(tmp_path) + "/output.txt"  # type: ignore[operator]
        original_replace = os.replace

        def failing_replace(src: str, dst: str) -> None:
            raise OSError("simulated failure")

        monkeypatch.setattr(os, "replace", failing_replace)
        with pytest.raises(OSError, match="simulated"):
            atomic_write(path, "content")

        remaining = os.listdir(str(tmp_path))
        assert not any(f.endswith(".tmp") for f in remaining)
        monkeypatch.setattr(os, "replace", original_replace)
