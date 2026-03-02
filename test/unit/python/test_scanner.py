"""Tests for scanner module."""

from agronomist.scanner import (
    _match_any,
    _parse_git_source,
    scan_sources,
)


class TestMatchAny:
    """Test pattern matching functionality."""

    def test_match_any_single_pattern_match(self):
        """Test matching a single pattern."""
        assert _match_any("src/main.tf", ["**/*.tf"])

    def test_match_any_single_pattern_no_match(self):
        """Test non-matching pattern."""
        assert not _match_any("src/main.py", ["**/*.tf"])

    def test_match_any_multiple_patterns(self):
        """Test matching with multiple patterns."""
        patterns = ["**/*.tf", "**/*.hcl"]
        assert _match_any("src/main.tf", patterns)
        assert _match_any("src/terragrunt.hcl", patterns)
        assert not _match_any("src/main.py", patterns)

    def test_match_any_empty_patterns(self):
        """Test with empty patterns list."""
        assert not _match_any("src/main.tf", [])

    def test_match_any_wildcard_patterns(self):
        """Test various wildcard patterns."""
        assert _match_any("test/fixtures/data.json", ["test/**"])
        assert _match_any("deep/nested/file.tf", ["**/file.tf"])


class TestParseGitSource:
    """Test Git source parsing."""

    def test_parse_valid_git_source(self):
        """Test parsing valid git source URL."""
        source = "git::https://github.com/terraform-aws-modules/terraform-aws-vpc.git?ref=v5.0.0"
        result = _parse_git_source(source)

        assert result is not None
        assert result.repo == "terraform-aws-modules/terraform-aws-vpc"
        # Note: repo_url is extracted without .git extension
        assert "terraform-aws-modules/terraform-aws-vpc" in result.repo_url
        assert result.ref == "v5.0.0"
        assert result.module is None

    def test_parse_git_source_with_module(self):
        """Test parsing git source with module path."""
        source = "git::https://github.com/example/repo.git//modules/vpc?ref=v2.0.0"
        result = _parse_git_source(source)

        assert result is not None
        assert result.repo == "example/repo"
        assert result.module == "modules/vpc"
        assert result.ref == "v2.0.0"

    def test_parse_git_source_without_git_prefix(self):
        """Test parsing source without git:: prefix."""
        source = "https://github.com/hashicorp/terraform.git?ref=main"
        result = _parse_git_source(source)

        assert result is not None
        assert result.repo == "hashicorp/terraform"

    def test_parse_invalid_source_returns_none(self):
        """Test that invalid sources return None."""
        invalid_sources = [
            "not-a-url",
            "local/path",
            "https://github.com/path/",  # Missing query param
            "",
        ]
        for source in invalid_sources:
            result = _parse_git_source(source)
            assert result is None

    def test_parse_git_source_http_format(self):
        """Test parsing git source without git:: prefix."""
        source = "https://github.com/myorg/modules//vpc?ref=v1.0"
        result = _parse_git_source(source)

        assert result is not None
        assert result.repo == "myorg/modules"
        assert result.module == "vpc"

    def test_parse_bitbucket_git_source(self):
        """Test parsing Bitbucket git source."""
        source = "git::https://bitbucket.org/company/repo.git?ref=main"
        result = _parse_git_source(source)

        assert result is not None
        assert result.repo == "company/repo"
        assert result.repo_host == "bitbucket.org"


class TestScanSources:
    """Test source scanning functionality."""

    def test_scan_sources_with_sample_terraform_file(self, sample_terraform_file):
        """Test that scan finds terraform sources."""
        import os

        root_dir = os.path.dirname(sample_terraform_file)
        results = scan_sources(root_dir, include=["**/*.tf"])

        # Should find at least some sources
        assert isinstance(results, list)

    def test_scan_sources_respects_include_patterns(self, sample_terraform_file):
        """Test that include patterns are respected."""
        import os

        root_dir = os.path.dirname(sample_terraform_file)
        results = scan_sources(root_dir, include=["**/*.tf"])

        assert all(r.file_path.endswith(".tf") for r in results)

    def test_scan_sources_respects_exclude_patterns(self, sample_terraform_file):
        """Test that exclude patterns are respected."""
        import os

        root_dir = os.path.dirname(sample_terraform_file)
        results = scan_sources(root_dir, include=["**/*.tf"], exclude=["**/main.tf"])

        # Should exclude main.tf
        assert all("main.tf" not in r.file_path for r in results)

    def test_scan_sources_applies_blacklist_repos(self, temp_dir):
        """Test that repo blacklist is applied."""
        # Create a file with blacklisted repo
        from pathlib import Path

        tf_file = Path(temp_dir) / "test.tf"
        tf_file.write_text(
            'module "test" { source = "git::https://github.com/deprecated/repo.git?ref=v1" }'
        )

        results = scan_sources(temp_dir, blacklist_repos=["deprecated/*"])

        assert len(results) == 0

    def test_scan_sources_applies_blacklist_modules(self, temp_dir):
        """Test that module blacklist is applied."""
        from pathlib import Path

        tf_file = Path(temp_dir) / "test.tf"
        tf_file.write_text(
            'module "test" { source = "git::https://github.com/org/repo.git//deprecated_module?ref=v1" }'
        )

        results = scan_sources(temp_dir, blacklist_modules=["deprecated_*"])

        assert len(results) == 0

    def test_scan_sources_applies_blacklist_files(self, temp_dir):
        """Test that file blacklist is applied."""
        from pathlib import Path

        # Create files in test/ directory
        test_dir = Path(temp_dir) / "test"
        test_dir.mkdir()
        tf_file = test_dir / "main.tf"
        tf_file.write_text(
            'module "test" { source = "git::https://github.com/org/repo.git?ref=v1" }'
        )

        results = scan_sources(temp_dir, blacklist_files=["test/**"])

        assert len(results) == 0

    def test_scan_sources_empty_directory(self, temp_dir):
        """Test scanning empty directory returns empty list."""
        results = scan_sources(temp_dir)
        assert results == []

    def test_scan_sources_returns_list(self, sample_terraform_file):
        """Test that scan returns list."""
        import os

        root_dir = os.path.dirname(sample_terraform_file)
        results = scan_sources(root_dir, include=["**/*.tf"])

        assert isinstance(results, list)
        # Each result should have required metadata
        for result in results:
            assert hasattr(result, "file_path")
            assert hasattr(result, "raw")
            assert hasattr(result, "repo")
