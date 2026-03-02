"""Tests for report module."""

import json
import tempfile
from datetime import datetime
from pathlib import Path

from agronomist.report import build_report, write_report


class TestBuildReport:
    """Test report building functionality."""

    def test_build_report_empty_updates(self):
        """Test building a report with no updates."""
        report = build_report("/root", [])

        assert report["root"] == "/root"
        assert report["updates"] == []
        assert "generated_at" in report

    def test_build_report_with_updates(self):
        """Test building a report with updates."""
        updates = [
            {"repo": "repo1", "module": "mod1"},
            {"repo": "repo2", "module": "mod2"},
        ]
        report = build_report("/root", updates)

        assert report["root"] == "/root"
        assert len(report["updates"]) == 2
        assert report["updates"] == updates

    def test_build_report_timestamp_format(self):
        """Test that timestamp is in ISO format."""
        report = build_report("/root", [])

        # Should parse without error if it's valid ISO format
        parsed = datetime.fromisoformat(report["generated_at"])
        assert parsed is not None

    def test_build_report_timestamp_includes_timezone(self):
        """Test that timestamp includes timezone."""
        report = build_report("/root", [])

        # ISO format with timezone should have + or Z
        assert "+" in report["generated_at"] or report["generated_at"].endswith("Z")

    def test_build_report_root_path_preserved(self):
        """Test that root path is preserved exactly."""
        root_path = "/home/user/terraform"
        report = build_report(root_path, [])

        assert report["root"] == root_path

    def test_build_report_updates_reference_not_copied(self):
        """Test that updates list is referenced, not copied."""
        updates = [{"repo": "repo1"}]
        report = build_report("/root", updates)

        # Modify original list
        updates.append({"repo": "repo2"})
        # Report should reference the same list
        assert len(report["updates"]) == 2


class TestWriteReport:
    """Test report file writing functionality."""

    def test_write_report_creates_file(self):
        """Test that write_report creates a file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "report.json"
            report = {"root": "/test", "updates": [], "generated_at": "2024-01-01T00:00:00+00:00"}

            write_report(str(report_path), report)

            assert report_path.exists()

    def test_write_report_valid_json(self):
        """Test that written file contains valid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "report.json"
            report = {"root": "/test", "updates": [], "generated_at": "2024-01-01T00:00:00+00:00"}

            write_report(str(report_path), report)

            with open(report_path) as f:
                loaded = json.load(f)
            assert loaded == report

    def test_write_report_sorted_keys(self):
        """Test that keys are sorted in output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "report.json"
            report = {"zebra": 1, "apple": 2, "root": "/test"}

            write_report(str(report_path), report)

            with open(report_path) as f:
                content = f.read()
            # Check that "apple" comes before "zebra" in the file
            assert content.index("apple") < content.index("zebra")

    def test_write_report_indented(self):
        """Test that output is indented with 2 spaces."""
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "report.json"
            report = {"root": "/test", "updates": [{"item": 1}]}

            write_report(str(report_path), report)

            with open(report_path) as f:
                content = f.read()
            # Should have indentation (2 spaces)
            assert "  " in content

    def test_write_report_ends_with_newline(self):
        """Test that file ends with newline."""
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "report.json"
            report = {"root": "/test"}

            write_report(str(report_path), report)

            with open(report_path) as f:
                content = f.read()
            assert content.endswith("\n")

    def test_write_report_overwrites_existing(self):
        """Test that write_report overwrites existing file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "report.json"
            # Create initial file
            report_path.write_text('{"old": "data"}')

            new_report = {"root": "/test"}
            write_report(str(report_path), new_report)

            with open(report_path) as f:
                loaded = json.load(f)
            assert loaded == new_report
