"""End-to-end integration tests for report and update commands.

These tests exercise the full CLI pipeline with real files
on disk and mocked API resolvers, verifying that scanning,
resolution, updating, and report generation work together.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from agronomist.cli import main
from agronomist.config import Blacklist, Config


def _config() -> Config:
    """Return a minimal Config with no filters."""
    return Config(
        categories=[],
        blacklist=Blacklist(repos=[], modules=[], files=[]),
    )


@pytest.mark.integration
class TestIntegrationReportCommand:
    """Integration tests for the ``report`` sub-command."""

    @patch("agronomist.cli.GitClient")
    @patch("agronomist.cli.GitLabClient")
    @patch("agronomist.cli.GitHubClient")
    @patch("agronomist.cli.load_config")
    def test_report_generates_json_file(
        self,
        mock_load_config,
        mock_gh_cls,
        mock_gl_cls,
        mock_git_cls,
        tmp_path,
    ):
        """Test that report command writes a valid JSON report."""
        mock_load_config.return_value = _config()

        # Create real Terraform file in a subdirectory
        infra = tmp_path / "infra"
        infra.mkdir()
        tf = infra / "main.tf"
        tf.write_text(
            'module "vpc" {\n  source = "git::https://github.com/org/vpc.git?ref=v1.0.0"\n}\n'
        )

        git_client = MagicMock()
        git_client.latest_ref.return_value = "v2.0.0"
        mock_git_cls.return_value = git_client
        mock_gh_cls.return_value = MagicMock()
        mock_gl_cls.return_value = MagicMock()
        mock_gl_cls.detect_gitlab_host.return_value = None

        output_path = str(tmp_path / "report.json")

        result = main(
            [
                "report",
                "--root",
                str(tmp_path),
                "--resolver",
                "git",
                "--json",
                output_path,
            ]
        )

        assert result == 0
        report = json.loads(Path(output_path).read_text())
        assert "updates" in report
        assert len(report["updates"]) == 1
        assert report["updates"][0]["current_ref"] == "v1.0.0"
        assert report["updates"][0]["latest_ref"] == "v2.0.0"

    @patch("agronomist.cli.GitClient")
    @patch("agronomist.cli.GitLabClient")
    @patch("agronomist.cli.GitHubClient")
    @patch("agronomist.cli.load_config")
    def test_report_generates_markdown_file(
        self,
        mock_load_config,
        mock_gh_cls,
        mock_gl_cls,
        mock_git_cls,
        tmp_path,
    ):
        """Test that --markdown flag generates a Markdown report."""
        mock_load_config.return_value = _config()

        infra = tmp_path / "infra"
        infra.mkdir()
        tf = infra / "main.tf"
        tf.write_text(
            'module "vpc" {\n  source = "git::https://github.com/org/vpc.git?ref=v1.0.0"\n}\n'
        )

        git_client = MagicMock()
        git_client.latest_ref.return_value = "v3.0.0"
        mock_git_cls.return_value = git_client
        mock_gh_cls.return_value = MagicMock()
        mock_gl_cls.return_value = MagicMock()
        mock_gl_cls.detect_gitlab_host.return_value = None

        md_path = str(tmp_path / "report.md")
        json_path = str(tmp_path / "report.json")

        result = main(
            [
                "report",
                "--root",
                str(tmp_path),
                "--resolver",
                "git",
                "--json",
                json_path,
                "--markdown",
                md_path,
            ]
        )

        assert result == 0
        md_content = Path(md_path).read_text()
        assert "# Agronomist Report" in md_content
        assert "org/vpc" in md_content
        assert "v1.0.0" in md_content
        assert "v3.0.0" in md_content


@pytest.mark.integration
class TestIntegrationUpdateCommand:
    """Integration tests for the ``update`` sub-command."""

    @patch("agronomist.cli.GitClient")
    @patch("agronomist.cli.GitLabClient")
    @patch("agronomist.cli.GitHubClient")
    @patch("agronomist.cli.load_config")
    def test_update_modifies_terraform_file(
        self,
        mock_load_config,
        mock_gh_cls,
        mock_gl_cls,
        mock_git_cls,
        tmp_path,
    ):
        """Test that update command modifies source refs in-place."""
        mock_load_config.return_value = _config()

        infra = tmp_path / "infra"
        infra.mkdir()
        tf = infra / "main.tf"
        tf.write_text(
            'module "vpc" {\n  source = "git::https://github.com/org/vpc.git?ref=v1.0.0"\n}\n'
        )

        git_client = MagicMock()
        git_client.latest_ref.return_value = "v2.0.0"
        mock_git_cls.return_value = git_client
        mock_gh_cls.return_value = MagicMock()
        mock_gl_cls.return_value = MagicMock()
        mock_gl_cls.detect_gitlab_host.return_value = None

        result = main(
            [
                "update",
                "--root",
                str(tmp_path),
                "--resolver",
                "git",
                "--json",
                str(tmp_path / "report.json"),
            ]
        )

        assert result == 0
        content = tf.read_text()
        assert "ref=v2.0.0" in content
        assert "ref=v1.0.0" not in content

    @patch("agronomist.cli.GitClient")
    @patch("agronomist.cli.GitLabClient")
    @patch("agronomist.cli.GitHubClient")
    @patch("agronomist.cli.load_config")
    def test_update_no_outputs_requested_skips_files(
        self,
        mock_load_config,
        mock_gh_cls,
        mock_gl_cls,
        mock_git_cls,
        tmp_path,
    ):
        """Test that no JSON/Markdown is generated when no flags are given."""
        mock_load_config.return_value = _config()

        infra = tmp_path / "infra"
        infra.mkdir()
        tf = infra / "main.tf"
        tf.write_text(
            'module "vpc" {\n  source = "git::https://github.com/org/vpc.git?ref=v1.0.0"\n}\n'
        )

        git_client = MagicMock()
        git_client.latest_ref.return_value = "v2.0.0"
        mock_git_cls.return_value = git_client
        mock_gh_cls.return_value = MagicMock()
        mock_gl_cls.return_value = MagicMock()
        mock_gl_cls.detect_gitlab_host.return_value = None

        json_path = tmp_path / "report.json"

        result = main(
            [
                "update",
                "--root",
                str(tmp_path),
                "--resolver",
                "git",
            ]
        )

        assert result == 0
        # File should be updated
        assert "ref=v2.0.0" in tf.read_text()
        # No JSON report generated by default
        assert not json_path.exists()
