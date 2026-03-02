"""Performance benchmarks for Agronomist modules."""

import tempfile
from pathlib import Path

from agronomist.markdown import generate_markdown, write_markdown
from agronomist.report import build_report, write_report
from agronomist.scanner import _match_any, _parse_git_source, scan_sources
from agronomist.updater import apply_updates


class TestScannerBenchmarks:
    """Benchmarks for scanner module."""

    def test_benchmark_match_any_single_pattern(self, benchmark):
        """Benchmark _match_any with single pattern."""
        result = benchmark(
            _match_any,
            "terraform/aws/ec2/main.tf",
            ["**/*.tf"],
        )
        assert result is True

    def test_benchmark_match_any_multiple_patterns(self, benchmark):
        """Benchmark _match_any with multiple patterns."""
        patterns = [
            "**/*.tf",
            "**/*.hcl",
            "**/test/**",
            "**/fixtures/**",
            "**/examples/**",
        ]
        result = benchmark(
            _match_any,
            "terraform/aws/vpc/outputs.tf",
            patterns,
        )
        assert result is True

    def test_benchmark_parse_git_source_https(self, benchmark):
        """Benchmark _parse_git_source with HTTPS URL."""
        source = "git::https://github.com/terraform-aws-modules/terraform-aws-vpc.git//modules/vpc?ref=v5.0.0"
        result = benchmark(_parse_git_source, source)
        assert result is not None

    def test_benchmark_parse_git_source_ssh(self, benchmark):
        """Benchmark _parse_git_source with SSH URL."""
        source = "git::ssh://git@github.com/terraform-aws-modules/terraform-aws-vpc.git//modules/vpc?ref=v5.0.0"
        result = benchmark(_parse_git_source, source)
        assert result is None

    def test_benchmark_scan_sources_small_repo(self, benchmark):
        """Benchmark scan_sources with small repository."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create sample terraform files
            for i in range(5):
                Path(tmpdir, f"module_{i}.tf").write_text(
                    'module "test" { source = "git::https://github.com/test/module.git" }'
                )

            result = benchmark(
                scan_sources,
                tmpdir,
                [],
                [],
                None,
            )
            assert isinstance(result, list)


class TestReportBenchmarks:
    """Benchmarks for report module."""

    def test_benchmark_build_report_no_updates(self, benchmark):
        """Benchmark build_report with no updates."""
        result = benchmark(build_report, "/root", [])
        assert "root" in result
        assert "updates" in result

    def test_benchmark_build_report_many_updates(self, benchmark):
        """Benchmark build_report with many updates."""
        updates = [
            {
                "repo": f"repo{i}",
                "module": f"module{i % 10}",
                "current_ref": "1.0.0",
                "latest_ref": "2.0.0",
                "files": [f"main_{j}.tf" for j in range(3)],
            }
            for i in range(100)
        ]
        result = benchmark(build_report, "/root", updates)
        assert len(result["updates"]) == 100

    def test_benchmark_write_report_json(self, benchmark):
        """Benchmark write_report JSON serialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "report.json"
            report = {
                "root": "/test",
                "updates": [
                    {
                        "repo": f"repo{i}",
                        "module": f"mod{i}",
                        "current_ref": "1.0.0",
                        "latest_ref": "2.0.0",
                    }
                    for i in range(50)
                ],
                "generated_at": "2024-01-01T00:00:00+00:00",
            }

            benchmark(write_report, str(report_path), report)
            assert report_path.exists()


class TestMarkdownBenchmarks:
    """Benchmarks for markdown module."""

    def test_benchmark_generate_markdown_empty(self, benchmark):
        """Benchmark generate_markdown with empty report."""
        report = {"updates": []}
        result = benchmark(generate_markdown, report)
        assert "No updates available" in result

    def test_benchmark_generate_markdown_many_repos(self, benchmark):
        """Benchmark generate_markdown with many repositories."""
        updates = [
            {
                "repo": f"repo{i // 10}",
                "module": f"module{i % 5}",
                "current_ref": "1.0.0",
                "latest_ref": "2.0.0",
                "files": [f"file_{j}.tf" for j in range(5)],
                "repo_host": "github",
            }
            for i in range(100)
        ]
        report = {
            "updates": updates,
            "generated_at": "2024-01-01T00:00:00+00:00",
            "root": "/test",
        }

        result = benchmark(generate_markdown, report)
        assert "# Agronomist Report" in result

    def test_benchmark_write_markdown_file(self, benchmark):
        """Benchmark write_markdown file I/O."""
        with tempfile.TemporaryDirectory() as tmpdir:
            markdown_path = Path(tmpdir) / "report.md"
            report = {
                "updates": [
                    {
                        "repo": f"repo{i}",
                        "module": f"module{i}",
                        "current_ref": "1.0.0",
                        "latest_ref": "2.0.0",
                        "files": ["main.tf", "outputs.tf"],
                    }
                    for i in range(50)
                ],
                "generated_at": "2024-01-01T00:00:00+00:00",
                "root": "/test",
            }

            benchmark(write_markdown, str(markdown_path), report)
            assert markdown_path.exists()


class TestUpdaterBenchmarks:
    """Benchmarks for updater module."""

    def test_benchmark_apply_updates_small(self, benchmark):
        """Benchmark apply_updates with small update list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test file
            test_file = Path(tmpdir) / "main.tf"
            test_file.write_text(
                'module "test" {\n  source = "git::https://github.com/test/module.git?ref=v1.0.0"\n}'
            )

            updates = [
                {
                    "files": ["main.tf"],
                    "replacements": [
                        {
                            "from": "v1.0.0",
                            "to": "v2.0.0",
                        }
                    ],
                }
            ]

            result = benchmark(apply_updates, tmpdir, updates)
            assert isinstance(result, list)

    def test_benchmark_apply_updates_many_files(self, benchmark):
        """Benchmark apply_updates with many files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create multiple test files
            updates = []
            for i in range(20):
                test_file = Path(tmpdir) / f"main_{i}.tf"
                test_file.write_text(
                    f'module "mod{i}" {{\n  source = "git::https://github.com/test/module.git?ref=v1.0.{i}"\n}}'
                )
                updates.append(
                    {
                        "files": [f"main_{i}.tf"],
                        "replacements": [
                            {
                                "from": f"v1.0.{i}",
                                "to": f"v2.0.{i}",
                            }
                        ],
                    }
                )

            result = benchmark(apply_updates, tmpdir, updates)
            assert isinstance(result, list)
