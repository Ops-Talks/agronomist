"""Tests for CLI main execution flows and helper functions."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from agronomist.cli import _categorize, _collect_updates, _print_category_summary, main
from agronomist.config import Blacklist, CategoryRule, Config
from agronomist.models import SourceRef


def _mk_source(
    *,
    repo: str,
    repo_url: str,
    repo_host: str,
    ref: str,
    file_path: str = "main.tf",
    module: str | None = None,
) -> SourceRef:
    raw = f"git::{repo_url}?ref={ref}"
    return SourceRef(
        file_path=file_path,
        raw=raw,
        repo=repo,
        repo_url=repo_url,
        repo_host=repo_host,
        ref=ref,
        module=module,
    )


class TestCliHelpers:
    def test_categorize_by_repo(self):
        rules = [
            CategoryRule(
                name="aws",
                repo_patterns=["terraform-aws-modules/*"],
                module_patterns=[],
            )
        ]
        result = _categorize(rules, "terraform-aws-modules/vpc", None)
        assert result == "aws"

    def test_categorize_by_module(self):
        rules = [
            CategoryRule(
                name="network",
                repo_patterns=[],
                module_patterns=["modules/vpc*"],
            )
        ]
        result = _categorize(rules, "org/repo", "modules/vpc")
        assert result == "network"

    def test_categorize_uncategorized_when_rules_exist(self):
        rules = [CategoryRule(name="x", repo_patterns=["no-match/*"], module_patterns=[])]
        result = _categorize(rules, "org/repo", "module")
        assert result == "uncategorized"

    def test_collect_updates_skips_when_latest_equal(self):
        source = _mk_source(
            repo="org/repo",
            repo_url="https://github.com/org/repo.git",
            repo_host="github.com",
            ref="v1.0.0",
        )

        updates = _collect_updates(lambda _s: "v1.0.0", [source], [])
        assert updates == []

    def test_collect_updates_deduplicates_latest_lookup_by_repo(self):
        source1 = _mk_source(
            repo="org/repo",
            repo_url="https://github.com/org/repo.git",
            repo_host="github.com",
            ref="v1.0.0",
            file_path="a.tf",
        )
        source2 = _mk_source(
            repo="org/repo",
            repo_url="https://github.com/org/repo.git",
            repo_host="github.com",
            ref="v1.1.0",
            file_path="b.tf",
        )

        calls: list[str] = []

        def latest_ref_fn(_s: SourceRef) -> str | None:
            calls.append("called")
            return "v2.0.0"

        updates = _collect_updates(latest_ref_fn, [source1, source2], [])
        assert len(calls) == 1
        assert len(updates) == 2
        assert updates[0]["module"] == "root@a.tf"
        assert updates[1]["module"] == "root@b.tf"

    def test_collect_updates_applies_category(self):
        source = _mk_source(
            repo="terraform-aws-modules/vpc",
            repo_url="https://github.com/terraform-aws-modules/vpc.git",
            repo_host="github.com",
            ref="v1.0.0",
            module="modules/vpc",
        )
        rules = [
            CategoryRule(name="aws", repo_patterns=["terraform-aws-modules/*"], module_patterns=[])
        ]

        updates = _collect_updates(lambda _s: "v2.0.0", [source], rules)
        assert updates[0]["category"] == "aws"

    def test_print_category_summary_with_updates(self, capsys):
        _print_category_summary(
            [
                {"category": "network"},
                {"category": "network"},
                {"category": "security"},
            ]
        )
        out = capsys.readouterr().out
        assert "Updates by category:" in out
        assert "network: 2" in out
        assert "security: 1" in out

    def test_print_category_summary_no_updates(self, capsys):
        _print_category_summary([])
        out = capsys.readouterr().out
        assert out == ""


class TestCliMain:
    def _config(self) -> Config:
        return Config(categories=[], blacklist=Blacklist(repos=[], modules=[], files=[]))

    @patch("agronomist.cli.apply_updates")
    @patch("agronomist.cli.write_markdown")
    @patch("agronomist.cli.write_report")
    @patch("agronomist.cli.build_report")
    @patch("agronomist.cli.GitClient")
    @patch("agronomist.cli.GitLabClient")
    @patch("agronomist.cli.GitHubClient")
    @patch("agronomist.cli.scan_sources")
    @patch("agronomist.cli.load_config")
    def test_main_report_no_updates(
        self,
        mock_load_config,
        mock_scan_sources,
        _mock_gh_cls,
        _mock_gl_cls,
        _mock_git_cls,
        mock_build_report,
        mock_write_report,
        mock_write_markdown,
        mock_apply_updates,
        capsys,
    ):
        mock_load_config.return_value = self._config()
        mock_scan_sources.return_value = []

        result = main(["report"])

        assert result == 0
        assert "No updates found." in capsys.readouterr().out
        mock_build_report.assert_not_called()
        mock_write_report.assert_not_called()
        mock_write_markdown.assert_not_called()
        mock_apply_updates.assert_not_called()

    @patch("agronomist.cli.GitClient")
    @patch("agronomist.cli.GitLabClient")
    @patch("agronomist.cli.GitHubClient")
    @patch("agronomist.cli.scan_sources")
    @patch("agronomist.cli.load_config")
    def test_main_validate_token_github_fail(
        self,
        mock_load_config,
        mock_scan_sources,
        mock_gh_cls,
        _mock_gl_cls,
        _mock_git_cls,
    ):
        mock_load_config.return_value = self._config()
        mock_scan_sources.return_value = []

        gh_client = MagicMock()
        gh_client.validate_token.return_value = False
        mock_gh_cls.return_value = gh_client

        result = main(["report", "--validate-token", "--github-token", "bad"])

        assert result == 1
        gh_client.validate_token.assert_called_once()

    @patch("agronomist.cli.GitClient")
    @patch("agronomist.cli.GitLabClient")
    @patch("agronomist.cli.GitHubClient")
    @patch("agronomist.cli.scan_sources")
    @patch("agronomist.cli.load_config")
    def test_main_validate_token_gitlab_fail(
        self,
        mock_load_config,
        mock_scan_sources,
        mock_gh_cls,
        mock_gl_cls,
        _mock_git_cls,
    ):
        mock_load_config.return_value = self._config()
        mock_scan_sources.return_value = []

        gh_client = MagicMock()
        gh_client.validate_token.return_value = True
        gl_client = MagicMock()
        gl_client.validate_token.return_value = False
        mock_gh_cls.return_value = gh_client
        mock_gl_cls.return_value = gl_client

        result = main(
            [
                "report",
                "--validate-token",
                "--github-token",
                "ok",
                "--gitlab-token",
                "bad",
            ]
        )

        assert result == 1
        gh_client.validate_token.assert_called_once()
        gl_client.validate_token.assert_called_once()

    @patch("agronomist.cli.apply_updates")
    @patch("agronomist.cli.write_markdown")
    @patch("agronomist.cli.write_report")
    @patch("agronomist.cli.build_report")
    @patch("agronomist.cli.GitClient")
    @patch("agronomist.cli.GitLabClient")
    @patch("agronomist.cli.GitHubClient")
    @patch("agronomist.cli.scan_sources")
    @patch("agronomist.cli.load_config")
    def test_main_update_with_markdown_and_touched_files(
        self,
        mock_load_config,
        mock_scan_sources,
        mock_gh_cls,
        mock_gl_cls,
        mock_git_cls,
        mock_build_report,
        mock_write_report,
        mock_write_markdown,
        mock_apply_updates,
        capsys,
    ):
        mock_load_config.return_value = self._config()
        source = _mk_source(
            repo="org/repo",
            repo_url="https://github.com/org/repo.git",
            repo_host="github.com",
            ref="v1.0.0",
            file_path="main.tf",
        )
        mock_scan_sources.return_value = [source]

        gh_client = MagicMock()
        gh_client.latest_ref.return_value = "v2.0.0"
        mock_gh_cls.return_value = gh_client

        gl_client = MagicMock()
        mock_gl_cls.return_value = gl_client
        mock_gl_cls.detect_gitlab_host.return_value = None

        git_client = MagicMock()
        mock_git_cls.return_value = git_client

        mock_build_report.return_value = {"updates": ["x"]}
        mock_apply_updates.return_value = ["main.tf"]

        result = main(["update", "--resolver", "github", "--markdown", "report.md"])

        assert result == 0
        mock_build_report.assert_called_once()
        mock_write_report.assert_called_once()
        mock_write_markdown.assert_called_once()
        mock_apply_updates.assert_called_once()
        out = capsys.readouterr().out
        assert "Markdown report written to report.md." in out
        assert "Updated 1 file(s)." in out

    @patch("agronomist.cli.apply_updates")
    @patch("agronomist.cli.write_report")
    @patch("agronomist.cli.build_report")
    @patch("agronomist.cli.GitClient")
    @patch("agronomist.cli.GitLabClient")
    @patch("agronomist.cli.GitHubClient")
    @patch("agronomist.cli.scan_sources")
    @patch("agronomist.cli.load_config")
    def test_main_update_no_report_and_no_updates_applied(
        self,
        mock_load_config,
        mock_scan_sources,
        mock_gh_cls,
        mock_gl_cls,
        mock_git_cls,
        mock_build_report,
        mock_write_report,
        mock_apply_updates,
        capsys,
    ):
        mock_load_config.return_value = self._config()
        source = _mk_source(
            repo="org/repo",
            repo_url="https://gitlab.com/org/repo.git",
            repo_host="gitlab.com",
            ref="v1.0.0",
            file_path="main.tf",
        )
        mock_scan_sources.return_value = [source]

        gh_client = MagicMock()
        mock_gh_cls.return_value = gh_client

        gl_client = MagicMock()
        gl_client.latest_ref.return_value = "v2.0.0"
        mock_gl_cls.return_value = gl_client
        mock_gl_cls.detect_gitlab_host.return_value = "gitlab.com"

        git_client = MagicMock()
        mock_git_cls.return_value = git_client

        mock_apply_updates.return_value = []

        result = main(["update", "--resolver", "auto", "--no-report"])

        assert result == 0
        mock_build_report.assert_not_called()
        mock_write_report.assert_not_called()
        mock_apply_updates.assert_called_once()
        out = capsys.readouterr().out
        assert "No updates applied." in out

    @patch("agronomist.cli.GitClient")
    @patch("agronomist.cli.GitLabClient")
    @patch("agronomist.cli.GitHubClient")
    @patch("agronomist.cli.scan_sources")
    @patch("agronomist.cli.load_config")
    def test_main_resolver_github_falls_back_to_git_for_non_github_host(
        self,
        mock_load_config,
        mock_scan_sources,
        mock_gh_cls,
        mock_gl_cls,
        mock_git_cls,
    ):
        mock_load_config.return_value = self._config()
        source = _mk_source(
            repo="org/repo",
            repo_url="https://gitlab.example.com/org/repo.git",
            repo_host="gitlab.example.com",
            ref="v1.0.0",
        )
        mock_scan_sources.return_value = [source]

        gh_client = MagicMock()
        gh_client.latest_ref.return_value = None
        mock_gh_cls.return_value = gh_client

        gl_client = MagicMock()
        mock_gl_cls.return_value = gl_client
        mock_gl_cls.detect_gitlab_host.return_value = "gitlab.example.com"

        git_client = MagicMock()
        git_client.latest_ref.return_value = "v2.0.0"
        mock_git_cls.return_value = git_client

        result = main(["report", "--resolver", "github", "--no-report"])

        assert result == 0
        git_client.latest_ref.assert_called_once()

    @patch("agronomist.cli.GitClient")
    @patch("agronomist.cli.GitLabClient")
    @patch("agronomist.cli.GitHubClient")
    @patch("agronomist.cli.scan_sources")
    @patch("agronomist.cli.load_config")
    def test_main_resolver_auto_falls_back_to_git_when_no_api_ref(
        self,
        mock_load_config,
        mock_scan_sources,
        mock_gh_cls,
        mock_gl_cls,
        mock_git_cls,
    ):
        mock_load_config.return_value = self._config()
        source = _mk_source(
            repo="org/repo",
            repo_url="https://github.com/org/repo.git",
            repo_host="github.com",
            ref="v1.0.0",
        )
        mock_scan_sources.return_value = [source]

        gh_client = MagicMock()
        gh_client.latest_ref.return_value = None
        mock_gh_cls.return_value = gh_client

        gl_client = MagicMock()
        mock_gl_cls.return_value = gl_client
        mock_gl_cls.detect_gitlab_host.return_value = None

        git_client = MagicMock()
        git_client.latest_ref.return_value = "v2.0.0"
        mock_git_cls.return_value = git_client

        result = main(["report", "--resolver", "auto", "--no-report"])

        assert result == 0
        gh_client.latest_ref.assert_called_once()
        git_client.latest_ref.assert_called_once()
