# NEXT_STEPS.md -- Agronomist Code Review

> **Review by:** Senior Software Engineer (Python)
> **Project:** Agronomist v1.1.3 -- CLI to detect and update Terraform module version refs
> **Baseline:** 187 tests passing, 89.26% coverage, Bandit clean, MyPy clean

---

## EPIC 1 -- Code Quality and PEP 8 Compliance

> **Goal:** Improve readability, maintainability, and compliance with PEP 8/PEP 257 across the project.

### Story 1.1 -- Add Missing Docstrings and Type Hints

> **Why?** PEP 257 requires docstrings on all public functions/classes. Several modules had
> functions without documentation, making onboarding and maintenance harder.

#### Task 1.1.1 -- Document `cli.py` module [DONE]

- **Sub-task 1.1.1.1:** [DONE] Added docstrings to `_parse_args`, `_match_any`, `_categorize`,
  `_collect_updates`, `_print_category_summary`, and `main`.
- **Sub-task 1.1.1.2:** [DONE] Added explicit return type hints to `_headers()` (`-> dict[str, str]`).
- **Sub-task 1.1.1.3:** [DONE] Documented parameters and return value of `_collect_updates`.

#### Task 1.1.2 -- Document `config.py` module [DONE]

- **Sub-task 1.1.2.1:** [DONE] Added docstrings to dataclasses `CategoryRule`, `Blacklist`, and `Config`.
- **Sub-task 1.1.2.2:** [DONE] Added docstrings to `_normalize_rules` and `load_config`.

#### Task 1.1.3 -- Document `git.py`, `github.py`, and `gitlab.py` modules [DONE]

- **Sub-task 1.1.3.1:** [DONE] Added docstrings to `GitClient` and `GitClient.latest_ref`.
- **Sub-task 1.1.3.2:** [DONE] Added docstrings to `GitHubClient._headers`,
  `GitHubClient.latest_release_tag`, `GitHubClient.latest_tag`, `GitHubClient.latest_ref`.
- **Sub-task 1.1.3.3:** [DONE] Added docstrings to `GitLabClient._headers`,
  `GitLabClient.detect_gitlab_host`, `GitLabClient.latest_tag`, `GitLabClient.latest_ref`.

#### Task 1.1.4 -- Document `scanner.py`, `updater.py`, `report.py`, `markdown.py`, and `models.py` [DONE]

- **Sub-task 1.1.4.1:** [DONE] Added docstrings to `_match_any`, `_parse_git_source`, and
  `scan_sources` in `scanner.py`.
- **Sub-task 1.1.4.2:** [DONE] Added docstrings to `apply_updates` and `_is_safe_path` in `updater.py`.
- **Sub-task 1.1.4.3:** [DONE] Added docstrings to `build_report` and `write_report` in `report.py`.
- **Sub-task 1.1.4.4:** [DONE] Added docstrings to `_group_by_repo`, `_group_by_module`,
  `generate_markdown`, and `write_markdown` in `markdown.py`.
- **Sub-task 1.1.4.5:** [DONE] Added docstring to the `SourceRef` dataclass in `models.py`.

---

### Story 1.2 -- Reduce Duplication and Complexity in CLI [DONE]

> **Why?** The argument parsing for `report` and `update` was nearly identical
> (lines 26-179 of `cli.py`), violating the DRY principle. The `main()` function had 100+ lines,
> making it difficult to read and test.

#### Task 1.2.1 -- Extract shared arguments into a helper function [DONE]

- **Sub-task 1.2.1.1:** [DONE] Created `_add_common_args(parser)` to add all shared arguments.
- **Sub-task 1.2.1.2:** [DONE] Refactored `report_parser` and `update_parser` to use `_add_common_args`.
- **Sub-task 1.2.1.3:** [DONE] Verified that both parsers maintain the same defaults and behavior.

#### Task 1.2.2 -- Eliminate duplicate print in `main()` [DONE]

- **Sub-task 1.2.2.1:** [DONE] Removed the redundant `if/else` block (formerly lines 367-370).

#### Task 1.2.3 -- Split `main()` into smaller functions [DONE]

- **Sub-task 1.2.3.1:** [DONE] Extracted client creation logic to `_create_clients(args)`.
- **Sub-task 1.2.3.2:** [DONE] Extracted token validation logic to `_validate_tokens(args, ...)`.

---

### Story 1.3 -- Eliminate `_build_session` Duplication [DONE]

> **Why?** The `_build_session` function was identically duplicated between `github.py` and
> `gitlab.py`. Direct violation of the DRY principle.

#### Task 1.3.1 -- Move `_build_session` to a shared module [DONE]

- **Sub-task 1.3.1.1:** [DONE] Created `src/agronomist/http.py` with the `build_session` function.
- **Sub-task 1.3.1.2:** [DONE] Updated imports in `github.py` and `gitlab.py`.
- **Sub-task 1.3.1.3:** [DONE] Added unit tests for `build_session` in `test_http.py`.

---

### Story 1.4 -- Use Typed Dataclasses Instead of `dict[str, object]`

> **Why?** `_collect_updates` returns `list[dict[str, object]]`, losing all type safety.
> The code uses manual `cast` in `updater.py` and accesses keys via `.get()` without validation,
> which is prone to `KeyError` at runtime.

#### Task 1.4.1 -- Create `UpdateEntry` dataclass

- **Sub-task 1.4.1.1:** Define `UpdateEntry` in `models.py` with typed fields.
- **Sub-task 1.4.1.2:** Refactor `_collect_updates` to return `list[UpdateEntry]`.
- **Sub-task 1.4.1.3:** Refactor `apply_updates` to accept `list[UpdateEntry]`, eliminating casts.
- **Sub-task 1.4.1.4:** Update `build_report`, `generate_markdown`, and corresponding tests.

---

## EPIC 2 -- Security

> **Goal:** Mitigate potential vulnerabilities and adopt secure practices.

### Story 2.1 -- Protect Tokens and Credentials [DONE]

> **Why?** Tokens passed via CLI flags (`--github-token`, `--gitlab-token`) are visible in
> `ps aux` and shell history. This poses a risk in shared and CI/CD environments.

#### Task 2.1.1 -- Add warning about token exposure via CLI [DONE]

- **Sub-task 2.1.1.1:** [DONE] Security note added to `docs/cli.md` recommending environment
  variables over CLI flags.

#### Task 2.1.2 -- Avoid logging tokens

- **Sub-task 2.1.2.1:** Audit all log messages to ensure no token is printed, even at DEBUG level.

---

### Story 2.2 -- Protect Against Path Traversal in Updater [DONE]

> **Why?** The updater built paths using `f"{root}/{file_path}"` without validation.
> A crafted `file_path` containing `../../etc/passwd` could write outside the root directory.

#### Task 2.2.1 -- Validate paths in the updater [DONE]

- **Sub-task 2.2.1.1:** [DONE] Used `os.path.join(root, file_path)` instead of f-string.
- **Sub-task 2.2.1.2:** [DONE] Added validation with `os.path.realpath()` via `_is_safe_path()`.
- **Sub-task 2.2.1.3:** [DONE] Added test for path traversal attempt.

---

### Story 2.3 -- Improve Dockerfile Security [DONE]

> **Why?** The `Dockerfile` used `pip install poetry` without a pinned version, potentially
> installing versions with vulnerabilities.

#### Task 2.3.1 -- Pin Poetry version in Dockerfile [DONE]

- **Sub-task 2.3.1.1:** [DONE] Changed to `pip install --no-cache-dir "poetry>=1.8,<2"`.
- **Sub-task 2.3.1.2:** [DONE] Added `--no-cache-dir` flag to pip install.

#### Task 2.3.2 -- Use base image with digest hash

- **Sub-task 2.3.2.1:** Replace `python:3.12-slim` with a digest-pinned version
  (e.g., `python:3.12-slim@sha256:...`).

---

## EPIC 3 -- Performance and Efficiency

> **Goal:** Optimize algorithms and resource usage for large repositories.

### Story 3.1 -- Optimize File Reading in Scanner

> **Why?** `scan_sources` reads entire files into memory. For very large Terraform/HCL files,
> this could consume excessive memory. Line-by-line reading would be more efficient.

#### Task 3.1.1 -- Evaluate incremental reading

- **Sub-task 3.1.1.1:** Benchmark `handle.read()` vs line-by-line for large files (>1MB).
- **Sub-task 3.1.1.2:** If needed, implement block-based or line-based reading with match accumulation.

> **Note:** For typical use (HCL files < 100KB), the current approach is acceptable.
> Prioritize only if performance complaints arise with very large repositories.

---

### Story 3.2 -- Atomic File Writes

> **Why?** In `updater.py` and `report.py`, files are written directly with `open(path, "w")`.
> If the process is interrupted during writing, the file may be corrupted. Atomic writes
> (temp file + rename) prevent this.

#### Task 3.2.1 -- Implement atomic writes

- **Sub-task 3.2.1.1:** Create helper `_atomic_write(path, content)` using temp file + `os.replace()`.
- **Sub-task 3.2.1.2:** Apply to `updater.py`, `report.py`, and `markdown.py`.
- **Sub-task 3.2.1.3:** Add tests for atomic write behavior.

---

### Story 3.3 -- HTTP Session Caching

> **Why?** `GitHubClient` and `GitLabClient` each create their own HTTP session. Sharing a
> session (or connection pool) could reuse connections to the same host, reducing TLS handshake
> overhead.

#### Task 3.3.1 -- Reuse HTTP sessions when possible

- **Sub-task 3.3.1.1:** Evaluate if the shared `build_session` (from EPIC 1, Story 1.3)
  can use a global connection pool.
- **Sub-task 3.3.1.2:** Benchmark latency with and without session reuse.

---

## EPIC 4 -- Tests and Coverage

> **Goal:** Increase test coverage to >95%, focusing on edge cases and failure scenarios.

### Story 4.1 -- Increase `cli.py` Coverage (was 90.40%)

> **Why?** Critical functions like `_latest_ref` (closure inside `main`) and error paths
> in `_collect_updates` were not tested.

#### Task 4.1.1 -- Test uncovered paths

- **Sub-task 4.1.1.1:** Test `_collect_updates` when `latest_ref_fn` raises an exception --
  should log warning and continue with `None`.
- **Sub-task 4.1.1.2:** Test resolver `"auto"` with GitLab host returning `None`,
  falling back to git.
- **Sub-task 4.1.1.3:** Test `--validate-token` with no token provided ("No token provided" message).
- **Sub-task 4.1.1.4:** Test `--timeout` and `--workers` with custom values.

---

### Story 4.2 -- Increase `git.py` Coverage (was 79.55%) [DONE]

> **Why?** Error paths for `CalledProcessError` without "not found" in stderr, and the
> skip of `^{}` lines were not covered.

#### Task 4.2.1 -- Test edge cases for `GitClient` [DONE]

- **Sub-task 4.2.1.1:** [DONE] Test for `CalledProcessError` with generic stderr (without "not found").
- **Sub-task 4.2.1.2:** [DONE] Test for output with `^{}` lines (dereferenced tags) -- must be skipped.
- **Sub-task 4.2.1.3:** [DONE] Test for empty output (no tags) -- must return `None`.
- **Sub-task 4.2.1.4:** [DONE] Test for malformed lines (without `\t` separator).

---

### Story 4.3 -- Increase `github.py` (was 87.72%) and `gitlab.py` (was 81.48%) Coverage [DONE]

#### Task 4.3.1 -- Test edge cases for HTTP clients [DONE]

- **Sub-task 4.3.1.1:** [DONE] Test for `validate_token` with status 403 (insufficient permissions).
- **Sub-task 4.3.1.2:** [DONE] Test for `validate_token` with `RequestException`.
- **Sub-task 4.3.1.3:** [DONE] Test for `latest_tag` with status 403 in GitLabClient.
- **Sub-task 4.3.1.4:** [DONE] Test for `latest_tag` with `RequestException` in GitLabClient.
- **Sub-task 4.3.1.5:** [DONE] Test for `latest_ref` in GitLabClient with invalid URL.
- **Sub-task 4.3.1.6:** [DONE] Test for `_headers()` without token (should return dict without
  Authorization/PRIVATE-TOKEN).
- **Sub-task 4.3.1.7:** [DONE] Test for `latest_release_tag` with status 403 in GitHubClient.

---

### Story 4.4 -- Increase `scanner.py` Coverage (was 85.71%)

#### Task 4.4.1 -- Test uncovered paths

- **Sub-task 4.4.1.1:** Test for `_parse_git_source` with URL without valid netloc.
- **Sub-task 4.4.1.2:** Test for `_parse_git_source` with URL ending in `.git`.
- **Sub-task 4.4.1.3:** Test for `scan_sources` with `include=[]` (explicit empty list)
  -- verify defaults are applied.
- **Sub-task 4.4.1.4:** Test for `scan_sources` with a file containing multiple
  references to the same repo but different refs.

---

### Story 4.5 -- Test `updater.py` Edge Cases (was 94.44%) [DONE]

#### Task 4.5.1 -- Test failure paths [DONE]

- **Sub-task 4.5.1.1:** [DONE] Test for `apply_updates` when file does not exist (OSError path).
- **Sub-task 4.5.1.2:** [DONE] Test for `apply_updates` with `file_path` containing path traversal.
- **Sub-task 4.5.1.3:** [DONE] Test for `apply_updates` with multiple updates mapping to the same file.

---

### Story 4.6 -- Add End-to-End Integration Tests

> **Why?** Current tests are unit tests with extensive mocking. There is no E2E test exercising
> the full `scan -> resolve -> report -> update` flow with real files.

#### Task 4.6.1 -- Create Python integration test suite

- **Sub-task 4.6.1.1:** Create fixture with temp directory containing `.tf` and `.hcl` files
  with real Git sources (HTTP-level mocked).
- **Sub-task 4.6.1.2:** E2E test for `report` command with real files and mocked resolver.
- **Sub-task 4.6.1.3:** E2E test for `update` command verifying files are modified correctly.
- **Sub-task 4.6.1.4:** Mark tests with `@pytest.mark.integration`.

---

## EPIC 5 -- Configuration and Tooling Improvements

> **Goal:** Harmonize tool configurations and improve developer experience.

### Story 5.1 -- Harmonize Line Length

> **Why?** The project uses `line-length = 100` (black/ruff), while PEP 8 recommends 79.
> This is a valid project decision, but `mypy` and `ruff` explicitly ignore `E501`.
> Recommendation: keep 100 if it is the team convention, but document the decision.

#### Task 5.1.1 -- Document line-length decision

- **Sub-task 5.1.1.1:** Add a section in `README.md` or `CONTRIBUTING.md` explaining
  the decision to use 100 characters.

---

### Story 5.2 -- Strengthen MyPy Configuration [DONE]

> **Why?** The `pyproject.toml` had `allow_untyped_defs = true` and
> `allow_untyped_calls = true`, which effectively disabled type checking for functions
> without annotations. This negated most of MyPy's benefit.

#### Task 5.2.1 -- Harden MyPy configuration incrementally [DONE]

- **Sub-task 5.2.1.1:** [DONE] Set `disallow_untyped_defs = true` and fixed resulting errors.
- **Sub-task 5.2.1.2:** [DONE] Set `disallow_incomplete_defs = true`.
- **Sub-task 5.2.1.3:** [DONE] Set `check_untyped_defs = true`.
- **Sub-task 5.2.1.4:** [DONE] Removed `allow_untyped_defs` and `allow_untyped_calls`,
  set `warn_return_any = true` and `implicit_optional = false`.

---

### Story 5.3 -- Black + Ruff Redundancy

> **Why?** The project uses both **Black** and **Ruff** for formatting simultaneously. Ruff
> already includes a Black-compatible formatter (`ruff format`). Keeping both adds overhead
> without additional benefit.

#### Task 5.3.1 -- Evaluate removing Black

- **Sub-task 5.3.1.1:** Compare output of `ruff format` vs `black` on the entire project.
- **Sub-task 5.3.1.2:** If output is identical, remove `black` from dependencies and tasks.
- **Sub-task 5.3.1.3:** Update `pre-commit-config.yaml`, `Makefile`, and taskipy scripts.

---

## Priority Summary

| Priority | Item | Impact | Status |
|:---:|:---|:---|:---:|
| HIGH | EPIC 2.2 -- Path Traversal in Updater | Security | DONE |
| HIGH | EPIC 1.2.2 -- Duplicate print in CLI | Bug/Code Smell | DONE |
| MEDIUM | EPIC 1.1 -- Missing docstrings | Maintainability | DONE |
| MEDIUM | EPIC 1.2 -- Refactor CLI (DRY args, split main) | Maintainability | DONE |
| MEDIUM | EPIC 1.3 -- `_build_session` duplication | DRY | DONE |
| MEDIUM | EPIC 2.1 -- Token exposure docs | Security | DONE |
| MEDIUM | EPIC 2.3 -- Dockerfile security | Security | DONE |
| MEDIUM | EPIC 4.2 -- `git.py` coverage (79%) | Quality | DONE |
| MEDIUM | EPIC 4.3 -- `gitlab.py` (81%) / `github.py` (87%) coverage | Quality | DONE |
| MEDIUM | EPIC 4.5 -- `updater.py` edge case tests | Quality | DONE |
| MEDIUM | EPIC 5.2 -- Strengthen MyPy | Type Safety | DONE |
| LOW | EPIC 1.4 -- Dataclass UpdateEntry | Type Safety | -- |
| LOW | EPIC 3 -- Performance | Efficiency | -- |
| LOW | EPIC 4.1 -- `cli.py` additional coverage | Quality | -- |
| LOW | EPIC 4.4 -- `scanner.py` additional coverage | Quality | -- |
| LOW | EPIC 4.6 -- Integration tests | Quality | -- |
| LOW | EPIC 5.1 -- Document line-length | Documentation | -- |
| LOW | EPIC 5.3 -- Remove Black | Simplification | -- |

---

> **Note:** All suggestions follow the principle of not breaking existing functionality.
> Incremental implementation is recommended, validating with `make check` on each PR.
