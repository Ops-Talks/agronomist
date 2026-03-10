# Changelog

All notable changes to this project are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.2.9] -- 2026-03-10

### Added

- **`--json` alias**: Added `--json` as a more intuitive alias for the `--output` flag in both `report` and `update` commands.
- **`--version` flag**: Added `--version` flag to display the current version of Agronomist and exit.

### Changed

- **Opt-in Reporting**: JSON and Markdown reports are now strictly opt-in. They are only generated if the `--json` (or `--output`) or `--markdown` flags are explicitly provided.
- **Documentation**: All documentation files (README, CLI guide, Reports, Getting Started, GitHub Action, and GitLab CI) have been updated to reflect the new opt-in reporting behavior and the `--json` alias.
- **Tasks and Examples**: Updated `pyproject.toml` tasks and CI workflow examples to use the new `--json` flag.

### Removed

- **`--no-report` flag**: Removed the `--no-report` flag as it is no longer needed with the new opt-in reporting model.

---

## [1.2.3] -- 2026-03-09

### Changed

- `poetry.lock`: updated.

---

## [1.2.2] -- 2026-03-07

### Fixed

- Documentation corrections across `docs/api.md`, `docs/architecture.md`, `docs/development.md`, `docs/github-action.md`, `docs/gitlab-ci.md`, `docs/reports.md`, `docs/resolvers.md`, and `docs/testing.md`.

### Changed

- `Makefile`: minor target adjustments.

---

## [1.2.1] -- 2026-03-07

### Added

- **`src/agronomist/fileutil.py`**: extracted shared `atomic_write()` helper into a standalone module. Used by `report.py`, `markdown.py`, and `updater.py` for crash-safe file writes.
- **New tests**: `test_benchmarks.py`, `test_cli_main.py`, `test_fileutil.py`, `test_integration.py`, `test_models.py`, `test_scanner_edge.py` -- Python test suite expanded to 235 tests.

### Changed

- **`src/agronomist/models.py`**: `UpdateEntry` refactored to a frozen dataclass with `base_module`, `file`, and `to_dict()` method for JSON serialization.
- **`src/agronomist/updater.py`**: now accepts `list[UpdateEntry]` instead of raw dicts; groups replacements by file and writes only changed files.
- **`src/agronomist/cli.py`**: adapted to use refactored `UpdateEntry` dataclass.
- **`src/agronomist/markdown.py`**: uses `base_module` field for grouping.
- **`Dockerfile`**: minor build optimizations.
- `poetry.lock`: updated.

### Removed

- `NEXT_STEPS.md`: planning document removed from repository.

---

## [1.2.0] -- 2026-03-04

### Added

- **GNU GPL v3 license** (`LICENSE`).
- **Comprehensive docstrings** on all modules (`cli.py`, `scanner.py`, `config.py`, `git.py`, `github.py`, `gitlab.py`, `http.py`, `markdown.py`, `models.py`, `report.py`, `updater.py`).
- **`src/agronomist/http.py`**: new shared HTTP session builder with retry and exponential backoff, used by `GitHubClient` and `GitLabClient`.
- **New tests**: `test_http.py`, additional cases in `test_git.py`, `test_github.py`, `test_gitlab.py`, `test_updater.py`.
- `.github/agents/` and `.github/copilot-instructions.md` for contributor tooling.

### Changed

- **`src/agronomist/cli.py`**: major refactor -- extracted `_create_clients()`, `_validate_tokens()`, `_collect_updates()`, and `_print_category_summary()` as standalone helper functions.
- **`src/agronomist/config.py`**: expanded with type-safe `CategoryRule`, `Blacklist`, and `Config` frozen dataclasses.
- **`src/agronomist/github.py`**: refactored to use `build_session()` from `http.py`; added `retries` and `backoff_factor` parameters.
- **`src/agronomist/gitlab.py`**: same session refactor; added `retries` and `backoff_factor` parameters.
- **`src/agronomist/git.py`**: expanded error handling (timeout, not-found, file-not-found).
- **`Dockerfile`**: switched base image argument for flexibility.
- `docs/cli.md`: added `--timeout` and `--workers` options.
- `pyproject.toml`: version bump to 1.2.0; dependency adjustments.

---

## [1.1.3] -- 2026-03-02

### Changed

- `pyproject.toml`: version bump to 1.1.3.

---

## [1.1.2] -- 2026-03-02

### Added

- **`src/agronomist/exceptions.py`**: new module with custom exception hierarchy -- `AgronomistError` (base), `NetworkError`, `AuthenticationError`, `ResolverError`, `ConfigError`.
- **`--validate-token` flag**: validates API tokens before processing. Exits with code 1 if invalid.
- **`--timeout` flag** (default: 20 s) on `report` and `update` subcommands.
- **`--workers` flag** (default: 10) on `report` and `update` subcommands.
- **`--verbose` / `-v` flag**: sets log level to `DEBUG`.
- **`--quiet` flag**: suppresses `INFO` output (log level `WARNING`). Mutually exclusive with `--verbose`.
- **Parallel version resolution** in `_collect_updates()` via `ThreadPoolExecutor`.
- **`test/unit/python/test_exceptions.py`**: tests for the exception hierarchy.
- Codecov integration in `.github/workflows/quality.yml`.

### Changed

- **`src/agronomist/cli.py`**: added `--timeout`, `--workers`, `--verbose`, `--quiet`, `--validate-token` arguments; refactored token resolution and validation.
- **`src/agronomist/github.py`**: added `validate_token()` method.
- **`src/agronomist/gitlab.py`**: added `validate_token()` method.
- `docs/cli.md`: documented new flags.
- `.gitignore`: updated.

---

## [1.1.1] -- 2026-03-02

### Changed

- `README.md`: updated badges and project description.
- `pyproject.toml`: version bump to 1.1.1.

---

## [1.1.0] -- 2026-03-02

### Added

- **Python test suite** (`test/unit/python/`): 171 pytest tests covering all core modules -- scanner, git, github, gitlab, markdown, report, updater, config, and CLI. Includes benchmark tests via `pytest-benchmark`.
- **Static analysis pipeline**: mypy, bandit, and eradicate integrated into the `check` task and pre-commit hooks.
- **Coverage reporting**: `pytest-cov` configured with branch coverage, HTML report output to `htmlcov/`, and per-module missing-line reporting.
- **`[tool.mypy]` configuration** in `pyproject.toml`: lenient baseline (`allow_untyped_defs`, `allow_untyped_calls`) with targeted strictness (`warn_return_any = false`, `warn_no_return = true`, `warn_unused_ignores = true`).
- **`[tool.bandit]` configuration** in `pyproject.toml`: excludes test directories, integrated into CI pipeline.
- **`[tool.eradicate]` configuration** in `pyproject.toml`: dead-code detection, hooked into lint task.
- **`[tool.pytest.ini_options]`** in `pyproject.toml`: testpaths, markers (`unit`, `integration`, `slow`), strict marker enforcement, short tracebacks.
- **`[tool.coverage.run]` and `[tool.coverage.report]`** in `pyproject.toml`: branch coverage, standard exclusion patterns, precision-2 output.
- **`docs/stylesheets/extra.css`**: custom CSS overrides for the Zensical theme, restoring the deep-orange/blue-grey colour palette that Material for MkDocs 9.x no longer applies via JavaScript at runtime.
- **`types-PyYAML`** and **`types-requests`** added as dev dependencies for mypy type stubs.
- **`zensical ^0.0.24`** added as a dev dependency, replacing `mkdocs` + `mkdocs-material` for documentation site generation.
- **Pre-commit hooks** expanded in `.pre-commit-config.yaml`: mypy, bandit, eradicate, and pytest now run as pre-commit stages alongside the existing ruff and black hooks.
- **Retry with exponential backoff** in `GitHubClient` and `GitLabClient`: requests are now routed through a `requests.Session` with a `urllib3.util.retry.Retry` adapter (3 retries, 0.5 s backoff factor, retries on HTTP 429/500/502/503/504).

### Changed

- **`pyproject.toml` version**: `1.0.5` to `1.1.0`.
- **`[tool.taskipy.tasks]`**: `lint` task extended to include `mypy src/`; `format` task extended to include `eradicate --recursive --in-place .`.
- **`src/agronomist/cli.py`**: `_print_category_summary()` now explicitly calls `str()` on the category value before dictionary operations, fixing a latent type narrowing issue surfaced by mypy.
- **`src/agronomist/git.py`**: `subprocess` import and `subprocess.run()` call annotated with `# nosec B404/B603` to suppress intentional bandit warnings for controlled subprocess usage.
- **`src/agronomist/gitlab.py`**: bare `except Exception` block annotated with `# nosec B110`; `requests.get()` `params` argument annotated with `# type: ignore[arg-type]` for mypy dict-type compatibility.
- **`src/agronomist/updater.py`**: `cast(list[str], ...)` and `cast(list[Any], ...)` added for `update["files"]` and `update["replacements"]` iteration to satisfy mypy without runtime overhead.
- **`mkdocs.yml`** navigation restructured: flat page list replaced with two top-level sections -- **User Guide** and **Contributing**.
- **`docs/index.md`** rewritten: now targets both end-user and contributor audiences, with dedicated "For SREs and infrastructure teams" and "For contributors and developers" sections.
- **`docs/getting-started.md`** rewritten: end-user focused, removed local development instructions (moved to `development.md`), added `!!! warning` admonition before the `update` command.
- **`docs/resolvers.md`** expanded from 15 lines to a full reference: comparison table, per-resolver guidance (when to use, authentication, limitations), GitHub Enterprise and self-hosted GitLab coverage.
- **`docs/architecture.md`** expanded from 18 lines to a full contributor guide: data flow diagram, per-module descriptions, key design decisions (regex-based parsing, stateless runs, pluggable resolver, separated report/update flow).
- **`docs/development.md`**: added contributor-focused introduction; removed duplicated troubleshooting section (already covered in `docs/troubleshooting.md`).
- **`docs/testing.md`** rewritten: leads with the pytest suite as the primary test layer, covers running, filtering, and writing new tests; BATS shell tests documented as secondary; fixtures table added.
- **`docs/cli.md`**: minor wording fixes.
- **`Makefile`**: new targets and updated task orchestration to match the extended check pipeline.
- **`README.md`**: minor badge/link update.
- **`poetry.lock`**: updated to reflect all new and changed dev dependencies.

### Removed

- **`mkdocs`** and **`mkdocs-material`** removed as direct dev dependencies (replaced by `zensical`).
- **`docs/assets` symlink** removed; assets are now resolved correctly without a symlink.

---

## [1.0.5] — 2026-02-27

### Fixed

- Patched documentation assets path resolution in the Zensical site configuration.

### Changed

- `mkdocs.yml`: updated site paths for asset references.
- `docs/index.md`: minor corrections.
- `poetry.lock`: updated.

---

## [1.0.4] — 2026-02-27

### Changed

- `docs/index.md`: updated home page content.
- `mkdocs.yml`: adjusted navigation and configuration.
- `pyproject.toml`: updated doc-related dependencies.
- `README.md`: updated badges and project description.
- `assets/agronomist-logo.png` and `assets/agronomist-logo.svg`: added/updated project logo files.

---

## [1.0.3] — 2026-02-26

### Changed

- `.github/workflows/release.yml`: release workflow refinements.
- `pyproject.toml`: version bump to 1.0.3.

---

## [1.0.2] — 2026-02-26

### Added

- `workflow_dispatch` trigger added to the release workflow, allowing manual release runs from the GitHub Actions UI (PR #2).

### Changed

- `.github/workflows/release.yml`: added `workflow_dispatch` event trigger.
- `pyproject.toml`: version bump to 1.0.2.

---

## [1.0.1] — 2026-02-26

_Initial public release. Bumped from pre-release version 0.6.2._

### Added

- `agronomist report` — scans a directory tree for Terraform `source =` references containing `?ref=`, resolves the latest version for each, and produces a structured JSON report and Markdown summary.
- `agronomist update` — reads a report produced by `agronomist report` and applies in-place `?ref=` replacements across source files.
- Three resolver strategies: `git` (default, uses `git ls-remote`), `github` (GitHub REST API), `auto` (selects resolver per source URL host).
- GitHub Enterprise support via `--github-base-url`.
- GitLab self-hosted support with host detection from source URLs.
- Category tagging via `agronomist.yml` configuration file (glob-based repo-to-category mapping).
- Blacklist filtering for repos, modules, and files in configuration.
- Docker image support (`Dockerfile`, `make build-docker`).
- GitHub Actions workflow for automated releases on tag push.
- MkDocs-based documentation site.

[1.2.3]: https://github.com/Ops-Talks/agronomist/compare/v1.2.2...v1.2.3
[1.2.2]: https://github.com/Ops-Talks/agronomist/compare/v1.2.1...v1.2.2
[1.2.1]: https://github.com/Ops-Talks/agronomist/compare/v1.2.0...v1.2.1
[1.2.0]: https://github.com/Ops-Talks/agronomist/compare/v1.1.3...v1.2.0
[1.1.3]: https://github.com/Ops-Talks/agronomist/compare/v1.1.2...v1.1.3
[1.1.2]: https://github.com/Ops-Talks/agronomist/compare/v1.1.1...v1.1.2
[1.1.1]: https://github.com/Ops-Talks/agronomist/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/Ops-Talks/agronomist/compare/v1.0.5...v1.1.0
[1.0.5]: https://github.com/Ops-Talks/agronomist/compare/v1.0.4...v1.0.5
[1.0.4]: https://github.com/Ops-Talks/agronomist/compare/v1.0.3...v1.0.4
[1.0.3]: https://github.com/Ops-Talks/agronomist/compare/v1.0.2...v1.0.3
[1.0.2]: https://github.com/Ops-Talks/agronomist/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/Ops-Talks/agronomist/releases/tag/v1.0.0
