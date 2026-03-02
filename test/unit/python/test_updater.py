"""Tests for updater module."""

import tempfile
from pathlib import Path

from agronomist.updater import apply_updates


class TestApplyUpdates:
    """Test applying updates to files."""

    def test_apply_single_replacement(self):
        """Test applying a single replacement."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "main.tf"
            test_file.write_text('source = "git::https://github.com/org/repo.git?ref=v1.0.0"')

            updates = [
                {
                    "files": ["main.tf"],
                    "replacements": [
                        {
                            "from": "git::https://github.com/org/repo.git?ref=v1.0.0",
                            "to": "git::https://github.com/org/repo.git?ref=v1.1.0",
                        }
                    ],
                    "category": "example",
                }
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
                {
                    "files": ["main.tf"],
                    "replacements": [
                        {"from": "ref=v1", "to": "ref=v1.1"},
                        {"from": "ref=v2", "to": "ref=v2.1"},
                    ],
                    "category": "example",
                }
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
                {
                    "files": ["main.tf", "vpc.tf"],
                    "replacements": [{"from": "v1.0.0", "to": "v2.0.0"}],
                    "category": "example",
                }
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
                {
                    "files": ["main.tf"],
                    "replacements": [{"from": "v1.0.0", "to": "v2.0.0"}],
                    "category": "example",
                }
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
                {
                    "files": ["main.tf"],
                    "replacements": [{"from": "nonexistent", "to": "v2.0.0"}],
                    "category": "example",
                }
            ]

            result_files = apply_updates(temp_dir, updates)

            # No changes made
            assert result_files == []
