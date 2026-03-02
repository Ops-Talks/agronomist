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
