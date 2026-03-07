"""Tests for updater module."""

import tempfile
from pathlib import Path

from agronomist.models import Replacement, UpdateEntry
from agronomist.updater import apply_updates


def _mk_update(
    *,
    files: list[str],
    replacements: list[tuple[str, str]],
    category: str | None = None,
) -> UpdateEntry:
    """Build a minimal UpdateEntry for testing."""
    return UpdateEntry(
        repo="org/repo",
        repo_host="github.com",
        repo_url="https://github.com/org/repo.git",
        module="root@main.tf",
        base_module=None,
        file=files[0],
        current_ref="v1.0.0",
        latest_ref="v2.0.0",
        strategy="latest",
        files=files,
        replacements=[Replacement(old=r[0], new=r[1]) for r in replacements],
        category=category,
    )


class TestApplyUpdates:
    """Test applying updates to files."""

    def test_apply_single_replacement(self):
        """Test applying a single replacement."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "main.tf"
            test_file.write_text('source = "git::https://github.com/org/repo.git?ref=v1.0.0"')

            updates = [
                _mk_update(
                    files=["main.tf"],
                    replacements=[
                        (
                            "git::https://github.com/org/repo.git?ref=v1.0.0",
                            "git::https://github.com/org/repo.git?ref=v1.1.0",
                        )
                    ],
                    category="example",
                )
            ]

            result_files = apply_updates(temp_dir, updates)

            assert "main.tf" in result_files
            result = test_file.read_text()
            assert "v1.1.0" in result
            assert "v1.0.0" not in result

    def test_apply_multiple_replacements(self):
        """Test applying multiple replacements in same file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "main.tf"
            test_file.write_text(
                'source1 = "git::https://github.com/org/repo.git?ref=v1"\n'
                'source2 = "git::https://github.com/org/repo.git?ref=v2"'
            )

            updates = [
                _mk_update(
                    files=["main.tf"],
                    replacements=[("ref=v1", "ref=v1.1"), ("ref=v2", "ref=v2.1")],
                    category="example",
                )
            ]

            result_files = apply_updates(temp_dir, updates)
            assert "main.tf" in result_files

            result = test_file.read_text()
            assert "ref=v1.1" in result
            assert "ref=v2.1" in result

    def test_apply_updates_to_multiple_files(self):
        """Test applying updates to multiple files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file1 = Path(temp_dir) / "main.tf"
            file2 = Path(temp_dir) / "vpc.tf"
            file1.write_text('source = "v1.0.0"')
            file2.write_text('source = "v1.0.0"')

            updates = [
                _mk_update(
                    files=["main.tf", "vpc.tf"],
                    replacements=[("v1.0.0", "v2.0.0")],
                    category="example",
                )
            ]

            result_files = apply_updates(temp_dir, updates)
            assert "main.tf" in result_files
            assert "vpc.tf" in result_files

            assert "v2.0.0" in file1.read_text()
            assert "v2.0.0" in file2.read_text()

    def test_apply_updates_returns_touched_files(self):
        """Test that apply_updates returns list of modified files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "main.tf"
            test_file.write_text('source = "v1.0.0"')

            updates = [
                _mk_update(
                    files=["main.tf"],
                    replacements=[("v1.0.0", "v2.0.0")],
                    category="example",
                )
            ]

            result_files = apply_updates(temp_dir, updates)

            assert isinstance(result_files, list)
            assert "main.tf" in result_files

    def test_apply_updates_with_empty_list(self):
        """Test applying empty updates list."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "main.tf"
            original = 'source = "v1.0.0"'
            test_file.write_text(original)

            result_files = apply_updates(temp_dir, [])

            # File should be unchanged
            assert test_file.read_text() == original
            assert result_files == []

    def test_apply_updates_no_match_returns_empty(self):
        """Test that no changes returns empty list."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "main.tf"
            test_file.write_text('source = "v1.0.0"')

            updates = [
                _mk_update(
                    files=["main.tf"],
                    replacements=[("nonexistent", "v2.0.0")],
                    category="example",
                )
            ]

            result_files = apply_updates(temp_dir, updates)

            # No changes made
            assert result_files == []

    def test_apply_updates_file_not_found(self):
        """Test that missing files are skipped without error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            updates = [
                _mk_update(
                    files=["nonexistent.tf"],
                    replacements=[("v1.0.0", "v2.0.0")],
                    category="example",
                )
            ]

            result_files = apply_updates(temp_dir, updates)
            assert result_files == []

    def test_apply_updates_path_traversal_blocked(self):
        """Test that path traversal attempts are blocked."""
        with tempfile.TemporaryDirectory() as temp_dir:
            updates = [
                _mk_update(
                    files=["../../etc/passwd"],
                    replacements=[("root", "hacked")],
                    category="malicious",
                )
            ]

            result_files = apply_updates(temp_dir, updates)
            assert result_files == []

    def test_apply_updates_multiple_updates_same_file(self):
        """Test multiple update entries targeting the same file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "main.tf"
            test_file.write_text(
                'source1 = "git::https://github.com/org/a.git?ref=v1.0.0"\n'
                'source2 = "git::https://github.com/org/b.git?ref=v2.0.0"'
            )

            updates = [
                _mk_update(
                    files=["main.tf"],
                    replacements=[("ref=v1.0.0", "ref=v1.1.0")],
                ),
                _mk_update(
                    files=["main.tf"],
                    replacements=[("ref=v2.0.0", "ref=v2.1.0")],
                ),
            ]

            result_files = apply_updates(temp_dir, updates)
            assert "main.tf" in result_files

            content = test_file.read_text()
            assert "ref=v1.1.0" in content
            assert "ref=v2.1.0" in content
