# Testing

This guide covers the test suite for contributors to Agronomist. The project has two test layers: a **Python test suite** (primary) run with pytest, and a **shell test suite** (secondary) run with BATS that validates CI workflow scripts.

---

## Python test suite (pytest)

The pytest suite is the primary test layer. It covers scanner logic, resolver behavior, report generation, configuration loading, and updater correctness.

### Prerequisites

Install dependencies using Poetry:

```sh
poetry install
```

### Run all Python tests

```sh
poetry run task test
```

This runs pytest with coverage enabled. The shorthand task is defined in `pyproject.toml` under `[tool.taskipy.tasks]`.

### Run with coverage report

```sh
poetry run task test-coverage
```

This runs the full suite and enforces a coverage threshold. Use it before submitting a pull request.

### Run a specific test file or test

```sh
# Single file
poetry run pytest test/unit/python/test_scanner.py

# Single test function
poetry run pytest test/unit/python/test_scanner.py::test_parse_git_source
```

### Run with verbose output

```sh
poetry run pytest -v
```

### Understand the output

A passing run reports a summary line like:

```
<N> passed in <T>s
```

The exact count depends on the current test suite. Coverage output follows if you ran `task test-coverage`.

---

## Writing new Python tests

Test files live under `test/unit/python/`. Use `pytest` conventions:

- File names must match `test_*.py`.
- Test functions must start with `test_`.
- Use `pytest.fixture` for shared setup.
- Prefer small, focused tests over large integration-style test functions.

Example test:

```python
from agronomist.scanner import _parse_git_source

def test_parse_git_source_with_module():
    source = "git::https://github.com/org/repo.git//modules/vpc?ref=v1.2.3"
    ref = _parse_git_source(source)
    assert ref is not None
    assert ref.ref == "v1.2.3"
    assert ref.module == "modules/vpc"
```

---

## Full check (lint + security + tests)

Before opening a pull request, run:

```sh
poetry run task check
```

This runs, in order:

1. `lint` -- ruff check, ruff format, and mypy (linting, formatting, and static type checking)
2. `security` -- bandit and eradicate (security scanning and dead code detection)
3. `test` -- pytest with coverage (full test suite)

---

## Shell test suite (BATS)

The BATS suite validates shell logic used in the multi-PR CI workflow scripts. It is secondary to the Python suite and requires additional system tooling.

### Test structure

```
test/
├── unit/
│   ├── test_file_based_updates.bats   # File-based update logic
│   └── test_multi_pr.bats             # Multi-PR branch/PR creation logic
├── integration/
│   └── test_multi_pr_flow.sh          # End-to-end workflow simulation
└── fixtures/
    ├── report_empty.json
    ├── report_single_module.json
    └── report_multiple_modules.json
```

### Install BATS dependencies

```sh
make install-test-deps
```

Or manually:

```sh
# Ubuntu / Debian
sudo apt-get install -y bats jq shellcheck git

# macOS
brew install bats-core jq shellcheck
```

### Run BATS tests

```sh
# All BATS tests
bats test/unit/*.bats

# Single file
bats test/unit/test_multi_pr.bats

# Filter by name
bats test/unit/test_multi_pr.bats --filter "branch naming"
```

### Run integration tests

```sh
bash test/integration/test_multi_pr_flow.sh
```

This creates a temporary Git repository, applies fixture data, and validates branch creation behavior end-to-end.

---

## Fixtures

Located in `test/fixtures/`. Used by both BATS and integration tests to represent different report shapes.

| File | Description |
|------|-------------|
| `report_empty.json` | Report with no updates (`{"updates": []}`) |
| `report_single_module.json` | One module with one file |
| `report_multiple_modules.json` | Three modules across multiple files |

---

## Common issues

**pytest not found:**

```sh
poetry install
```

**Import errors in tests:**

Always run pytest through Poetry:

```sh
# Correct
poetry run pytest

# Wrong (uses system Python, missing dependencies)
python -m pytest
```

**BATS not found:**

```sh
make install-test-deps
```

**jq not found:**

```sh
sudo apt-get install jq
```

---

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
- [BATS documentation](https://bats-core.readthedocs.io/)
- [jq manual](https://jqlang.github.io/jq/manual/)

