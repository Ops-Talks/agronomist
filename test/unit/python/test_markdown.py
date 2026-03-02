"""Tests for markdown module."""

import tempfile
from pathlib import Path

from agronomist.markdown import (
    _group_by_module,
    _group_by_repo,
    generate_markdown,
    write_markdown,
)


class TestGroupByRepo:
    """Test _group_by_repo function."""

    def test_group_by_repo_empty_list(self):
        """Test grouping empty update list."""
        result = _group_by_repo([])

        assert result == {}

    def test_group_by_repo_single_repo(self):
        """Test grouping updates from single repo."""
        updates = [
            {"repo": "repo1", "module": "mod1"},
            {"repo": "repo1", "module": "mod2"},
        ]
        result = _group_by_repo(updates)

        assert len(result) == 1
        assert "repo1" in result
        assert len(result["repo1"]) == 2

    def test_group_by_repo_multiple_repos(self):
        """Test grouping updates from multiple repos."""
        updates = [
            {"repo": "repo1", "module": "mod1"},
            {"repo": "repo2", "module": "mod2"},
            {"repo": "repo1", "module": "mod3"},
        ]
        result = _group_by_repo(updates)

        assert len(result) == 2
        assert len(result["repo1"]) == 2
        assert len(result["repo2"]) == 1

    def test_group_by_repo_missing_repo_defaults_to_unknown(self):
        """Test that missing repo defaults to 'unknown'."""
        updates = [{"module": "mod1"}]
        result = _group_by_repo(updates)

        assert "unknown" in result
        assert result["unknown"] == [{"module": "mod1"}]


class TestGroupByModule:
    """Test _group_by_module function."""

    def test_group_by_module_empty_list(self):
        """Test grouping empty update list."""
        result = _group_by_module([])

        assert result == {}

    def test_group_by_module_single_module(self):
        """Test grouping updates from single module."""
        updates = [
            {"module": "mod1", "current_ref": "1.0"},
            {"module": "mod1", "current_ref": "2.0"},
        ]
        result = _group_by_module(updates)

        assert len(result) == 1
        assert "mod1" in result
        assert len(result["mod1"]) == 2

    def test_group_by_module_multiple_modules(self):
        """Test grouping updates from multiple modules."""
        updates = [
            {"module": "mod1"},
            {"module": "mod2"},
            {"module": "mod1"},
        ]
        result = _group_by_module(updates)

        assert len(result) == 2
        assert len(result["mod1"]) == 2
        assert len(result["mod2"]) == 1

    def test_group_by_module_prefers_base_module(self):
        """Test that base_module is preferred over module."""
        updates = [{"module": "mod1", "base_module": "base_mod1"}]
        result = _group_by_module(updates)

        assert "base_mod1" in result
        assert "mod1" not in result

    def test_group_by_module_missing_defaults_to_root(self):
        """Test that missing module defaults to 'root'."""
        updates = [{"repo": "repo1"}]
        result = _group_by_module(updates)

        assert "root" in result


class TestGenerateMarkdown:
    """Test generate_markdown function."""

    def test_generate_markdown_empty_report(self):
        """Test markdown generation for empty report."""
        report = {"updates": []}
        markdown = generate_markdown(report)

        assert "No updates available" in markdown

    def test_generate_markdown_header(self):
        """Test that markdown includes main header."""
        report = {"updates": [{"repo": "repo1", "module": "mod1"}]}
        markdown = generate_markdown(report)

        assert "# Agronomist Report" in markdown

    def test_generate_markdown_generated_at(self):
        """Test that markdown includes generated_at."""
        timestamp = "2024-01-01T00:00:00+00:00"
        report = {
            "updates": [{"repo": "repo1", "module": "mod1"}],
            "generated_at": timestamp,
        }
        markdown = generate_markdown(report)

        assert timestamp in markdown

    def test_generate_markdown_root(self):
        """Test that markdown includes root path."""
        report = {
            "updates": [{"repo": "repo1", "module": "mod1"}],
            "root": "/test",
        }
        markdown = generate_markdown(report)

        assert "`/test`" in markdown

    def test_generate_markdown_summary_counts(self):
        """Test that markdown includes correct summary counts."""
        report = {
            "updates": [
                {"repo": "repo1", "module": "mod1"},
                {"repo": "repo1", "module": "mod1"},
                {"repo": "repo2", "module": "mod2"},
            ],
            "generated_at": "2024-01-01T00:00:00+00:00",
            "root": "/test",
        }
        markdown = generate_markdown(report)

        assert "- **Total updates:** 3" in markdown
        assert "- **Affected repositories:** 2" in markdown
        assert "- **Affected modules:** 2" in markdown

    def test_generate_markdown_includes_repos(self):
        """Test that markdown includes repository sections."""
        report = {
            "updates": [{"repo": "repo1", "module": "mod1", "repo_host": "github"}],
            "generated_at": "2024-01-01T00:00:00+00:00",
            "root": "/test",
        }
        markdown = generate_markdown(report)

        assert "### repo1 (github)" in markdown

    def test_generate_markdown_file_count(self):
        """Test that markdown includes file counts."""
        report = {
            "updates": [
                {
                    "repo": "repo1",
                    "module": "mod1",
                    "current_ref": "1.0",
                    "latest_ref": "2.0",
                    "files": ["file1.tf", "file2.tf"],
                }
            ],
            "generated_at": "2024-01-01T00:00:00+00:00",
            "root": "/test",
        }
        markdown = generate_markdown(report)

        assert "- Affected files: 2" in markdown


class TestWriteMarkdown:
    """Test write_markdown function."""

    def test_write_markdown_creates_file(self):
        """Test that write_markdown creates a file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            markdown_path = Path(tmpdir) / "report.md"
            report = {
                "updates": [{"repo": "repo1", "module": "mod1"}],
                "generated_at": "2024-01-01T00:00:00+00:00",
                "root": "/test",
            }

            write_markdown(str(markdown_path), report)

            assert markdown_path.exists()

    def test_write_markdown_file_content(self):
        """Test that written markdown file has expected content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            markdown_path = Path(tmpdir) / "report.md"
            report = {
                "updates": [{"repo": "repo1", "module": "mod1"}],
                "generated_at": "2024-01-01T00:00:00+00:00",
                "root": "/test",
            }

            write_markdown(str(markdown_path), report)

            content = markdown_path.read_text()
            assert "# Agronomist Report" in content
            assert "repo1" in content

    def test_write_markdown_overwrites_existing(self):
        """Test that write_markdown overwrites existing file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            markdown_path = Path(tmpdir) / "report.md"
            # Create initial file
            markdown_path.write_text("old content")

            report = {
                "updates": [],
                "generated_at": "2024-01-01T00:00:00+00:00",
                "root": "/test",
            }
            write_markdown(str(markdown_path), report)

            content = markdown_path.read_text()
            assert "old content" not in content
            assert "No updates available" in content
