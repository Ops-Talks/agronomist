"""Tests for CLI module."""

import pytest

from agronomist.cli import _parse_args


class TestParseArgsReportCommand:
    """Test CLI argument parsing for report command."""

    def test_parse_args_report_command(self):
        """Test parsing report command."""
        args = _parse_args(["report"])

        assert args.command == "report"

    def test_parse_args_report_with_root(self):
        """Test parsing report with custom root."""
        args = _parse_args(["report", "--root", "/custom/path"])

        assert args.root == "/custom/path"

    def test_parse_args_default_root(self):
        """Test that default root is current directory."""
        args = _parse_args(["report"])

        assert args.root == "."

    def test_parse_args_include_patterns(self):
        """Test include patterns."""
        args = _parse_args(["report", "--include", "**/*.tf", "--include", "**/*.hcl"])

        assert "**/*.tf" in args.include
        assert "**/*.hcl" in args.include

    def test_parse_args_exclude_patterns(self):
        """Test exclude patterns."""
        args = _parse_args(["report", "--exclude", "**/test/**"])

        assert "**/test/**" in args.exclude

    def test_parse_args_github_token(self):
        """Test GitHub token argument."""
        args = _parse_args(["report", "--github-token", "gh-token"])

        assert args.github_token == "gh-token"

    def test_parse_args_gitlab_token(self):
        """Test GitLab token argument."""
        args = _parse_args(["report", "--gitlab-token", "gl-token"])

        assert args.gitlab_token == "gl-token"

    def test_parse_args_shared_token(self):
        """Test shared token argument."""
        args = _parse_args(["report", "--token", "shared-token"])

        assert args.token == "shared-token"

    def test_parse_args_config_file(self):
        """Test config file argument."""
        args = _parse_args(["report", "--config", ".custom.yaml"])

        assert args.config == ".custom.yaml"

    def test_parse_args_resolver_git(self):
        """Test git resolver."""
        args = _parse_args(["report", "--resolver", "git"])

        assert args.resolver == "git"

    def test_parse_args_resolver_github(self):
        """Test github resolver."""
        args = _parse_args(["report", "--resolver", "github"])

        assert args.resolver == "github"

    def test_parse_args_resolver_auto(self):
        """Test auto resolver."""
        args = _parse_args(["report", "--resolver", "auto"])

        assert args.resolver == "auto"

    def test_parse_args_json_flag(self):
        """Test --json flag for JSON report output."""
        args = _parse_args(["report", "--json", "custom-report.json"])

        assert args.json == "custom-report.json"

    def test_parse_args_markdown_output(self):
        """Test markdown output argument."""
        args = _parse_args(["report", "--markdown", "report.md"])

        assert args.markdown == "report.md"

    def test_parse_args_validate_token_flag(self):
        """Test validate-token flag."""
        args = _parse_args(["report", "--validate-token"])

        assert args.validate_token is True

    def test_parse_args_github_base_url(self):
        """Test github-base-url argument."""
        args = _parse_args(["report", "--github-base-url", "https://github.enterprise.com/api/v3"])

        assert args.github_base_url == "https://github.enterprise.com/api/v3"

    def test_parse_args_gitlab_base_url(self):
        """Test gitlab-base-url argument."""
        args = _parse_args(
            [
                "report",
                "--gitlab-base-url",
                "https://gitlab.corp.example.com",
            ]
        )

        assert args.gitlab_base_url == "https://gitlab.corp.example.com"

    def test_parse_args_default_gitlab_base_url(self):
        """Test default gitlab-base-url value."""
        args = _parse_args(["report"])

        assert args.gitlab_base_url == "https://gitlab.com"


class TestParseArgsUpdateCommand:
    """Test CLI argument parsing for update command."""

    def test_parse_args_update_command(self):
        """Test parsing update command."""
        args = _parse_args(["update"])

        assert args.command == "update"

    def test_parse_args_update_with_include(self):
        """Test update command with include patterns."""
        args = _parse_args(["update", "--include", "**/*.tf"])

        assert "**/*.tf" in args.include

    def test_parse_args_update_with_resolver(self):
        """Test update command with resolver."""
        args = _parse_args(["update", "--resolver", "github"])

        assert args.resolver == "github"

    def test_parse_args_update_with_json(self):
        """Test update command with --json flag."""
        args = _parse_args(["update", "--json", "update-report.json"])

        assert args.json == "update-report.json"


class TestParseArgsValidation:
    """Test argument validation."""

    def test_parse_args_unknown_command(self):
        """Test that unknown command raises SystemExit."""
        with pytest.raises(SystemExit):
            _parse_args(["unknown"])

    def test_parse_args_unknown_flag(self):
        """Test that unknown flag raises SystemExit."""
        with pytest.raises(SystemExit):
            _parse_args(["report", "--unknown-flag"])

    def test_parse_args_no_command_shows_help(self):
        """Test that no command shows help and exits."""
        with pytest.raises(SystemExit):
            _parse_args([])

    def test_parse_args_version_flag(self):
        """Test that --version flag exits."""
        with pytest.raises(SystemExit):
            _parse_args(["--version"])


class TestParseArgsDefaults:
    """Test default argument values."""

    def test_parse_args_default_root_report(self):
        """Test default root value."""
        args = _parse_args(["report"])
        assert args.root == "."

    def test_parse_args_default_resolver_report(self):
        """Test default resolver value."""
        args = _parse_args(["report"])
        assert args.resolver == "git"

    def test_parse_args_default_json_report(self):
        """Test default --json value."""
        args = _parse_args(["report"])
        assert args.json is None

    def test_parse_args_default_config_report(self):
        """Test default config file."""
        args = _parse_args(["report"])
        assert args.config == ".agronomist.yaml"

    def test_parse_args_default_github_base_url(self):
        """Test default GitHub base URL."""
        args = _parse_args(["report"])
        assert args.github_base_url == "https://api.github.com"
