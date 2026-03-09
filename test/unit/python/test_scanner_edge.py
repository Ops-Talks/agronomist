"""Additional edge-case tests for scanner module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from agronomist.scanner import _parse_git_source, scan_sources


class TestScannerEdgeCases:
    def test_parse_git_source_invalid_url_parts_returns_none(self):
        # Valid regex shape but invalid parsed URL (missing host/path)
        source = "git::https://?ref=v1.0.0"
        assert _parse_git_source(source) is None

    def test_parse_git_source_strips_dot_git_suffix(self):
        """Test that .git suffix is stripped from repo path."""
        source = "git::https://github.com/org/repo.git?ref=v1.0.0"
        result = _parse_git_source(source)
        assert result is not None
        assert result.repo == "org/repo"
        assert not result.repo.endswith(".git")

    def test_parse_git_source_without_dot_git_suffix(self):
        """Test parsing URL without .git suffix."""
        source = "https://github.com/org/repo//modules/vpc?ref=v2.0.0"
        result = _parse_git_source(source)
        assert result is not None
        assert result.repo == "org/repo"
        assert result.module == "modules/vpc"

    def test_scan_sources_uses_default_include_patterns(self, temp_dir):
        infra_dir = Path(temp_dir) / "infra"
        infra_dir.mkdir()
        tf_file = infra_dir / "main.tf"
        hcl_file = infra_dir / "terragrunt.hcl"
        tf_file.write_text(
            'module "x" { source = "git::https://github.com/org/repo.git?ref=v1.0.0" }'
        )
        hcl_file.write_text(
            'terraform { source = "git::https://github.com/org/repo2.git?ref=v2.0.0" }'
        )

        results = scan_sources(temp_dir)

        repos = {item.repo for item in results}
        assert "org/repo" in repos
        assert "org/repo2" in repos

    def test_scan_sources_skips_unreadable_files(self, temp_dir):
        tf_file = Path(temp_dir) / "main.tf"
        tf_file.write_text(
            'module "x" { source = "git::https://github.com/org/repo.git?ref=v1.0.0" }'
        )

        real_open = open

        def fake_open(path, *args, **kwargs):
            if str(path).endswith("main.tf"):
                raise OSError("permission denied")
            return real_open(path, *args, **kwargs)

        with patch("builtins.open", side_effect=fake_open):
            results = scan_sources(temp_dir)

        assert results == []

    def test_scan_sources_skips_non_git_source_entries(self, temp_dir):
        infra_dir = Path(temp_dir) / "infra"
        infra_dir.mkdir()
        tf_file = infra_dir / "main.tf"
        tf_file.write_text(
            'module "x" { source = "./local-module" }\n'
            'module "y" { source = "../relative" }\n'
            'module "z" { source = "git::https://github.com/org/repo.git?ref=v1.0.0" }\n'
        )

        results = scan_sources(temp_dir)

        assert len(results) == 1
        assert results[0].repo == "org/repo"

    def test_scan_sources_with_explicit_empty_include(self, temp_dir):
        """Test that empty include list uses defaults."""
        infra_dir = Path(temp_dir) / "infra"
        infra_dir.mkdir()
        tf_file = infra_dir / "main.tf"
        tf_file.write_text(
            'module "x" { source = "git::https://github.com/org/repo.git?ref=v1.0.0" }'
        )

        results = scan_sources(temp_dir, include=[])
        assert len(results) == 1

    def test_scan_sources_multiple_refs_same_repo(self, temp_dir):
        """Test scanning file with multiple refs to same repo."""
        infra_dir = Path(temp_dir) / "infra"
        infra_dir.mkdir()
        tf_file = infra_dir / "main.tf"
        tf_file.write_text(
            'module "a" { source = "git::https://github.com/org/repo.git?ref=v1.0.0" }\n'
            'module "b" { source = "git::https://github.com/org/repo.git?ref=v2.0.0" }\n'
        )

        results = scan_sources(temp_dir)
        assert len(results) == 2
        refs = {r.ref for r in results}
        assert refs == {"v1.0.0", "v2.0.0"}

    def test_scan_sources_blacklist_repos_pattern(self, temp_dir):
        """Test that blacklist_repos filters by glob pattern."""
        infra_dir = Path(temp_dir) / "infra"
        infra_dir.mkdir()
        tf_file = infra_dir / "main.tf"
        tf_file.write_text(
            'module "a" { source = "git::https://github.com/internal/infra.git?ref=v1.0.0" }\n'
            'module "b" { source = "git::https://github.com/public/vpc.git?ref=v1.0.0" }\n'
        )

        results = scan_sources(temp_dir, blacklist_repos=["internal/*"])
        assert len(results) == 1
        assert results[0].repo == "public/vpc"

    def test_scan_sources_blacklist_modules_pattern(self, temp_dir):
        """Test that blacklist_modules filters matching modules."""
        infra_dir = Path(temp_dir) / "infra"
        infra_dir.mkdir()
        tf_file = infra_dir / "main.tf"
        tf_file.write_text(
            'module "a" { source = "git::https://github.com/org/repo.git//modules/old?ref=v1.0.0" }\n'
            'module "b" { source = "git::https://github.com/org/repo.git//modules/new?ref=v1.0.0" }\n'
        )

        results = scan_sources(temp_dir, blacklist_modules=["modules/old"])
        assert len(results) == 1
        assert results[0].module == "modules/new"

    def test_scan_sources_discovers_ssh_scp_sources(
        self,
        temp_dir,
    ):
        """Test that SCP-style SSH sources are discovered."""
        infra_dir = Path(temp_dir) / "infra"
        infra_dir.mkdir()
        hcl = infra_dir / "terragrunt.hcl"
        hcl.write_text(
            'terraform {\n  source = "git::git@github.com:org/modules.git//vpc?ref=v1.0.0"\n}\n'
        )

        results = scan_sources(temp_dir)
        assert len(results) == 1
        assert results[0].repo == "org/modules"
        assert results[0].repo_host == "github.com"
        assert results[0].module == "vpc"
        assert results[0].ref == "v1.0.0"

    def test_scan_sources_mixed_https_and_ssh(
        self,
        temp_dir,
    ):
        """Test scanning files with both HTTPS and SSH sources."""
        infra_dir = Path(temp_dir) / "infra"
        infra_dir.mkdir()
        tf_file = infra_dir / "main.tf"
        tf_file.write_text(
            'module "a" {\n'
            '  source = "git::https://github.com/org/'
            'repo-a.git?ref=v1.0.0"\n'
            "}\n"
            'module "b" {\n'
            '  source = "git::git@github.com:org/'
            'repo-b.git?ref=v2.0.0"\n'
            "}\n"
        )

        results = scan_sources(temp_dir)
        assert len(results) == 2
        repos = {r.repo for r in results}
        assert repos == {"org/repo-a", "org/repo-b"}
