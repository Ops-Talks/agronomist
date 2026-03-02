# Development

This guide is for contributors working on Agronomist itself. It covers environment setup, available tasks, code style, testing, and the contribution workflow.

If you are looking for usage instructions as an end user, see [Getting Started](getting-started.md). For internal design decisions and module descriptions, see [Architecture](architecture.md).

## Prerequisites

Before setting up the development environment, ensure you have:

- **Python 3.10+** - Required by project (`pyproject.toml`)
- **Poetry** - Dependency and environment manager (https://python-poetry.org/)
- **Git** - Version control and required for git resolver testing
- **Docker** (optional) - For containerized builds using `make build-docker`

### Install Poetry

```sh
curl -sSL https://install.python-poetry.org | python3 -
```

Then add Poetry to your PATH:
```sh
export PATH="$HOME/.local/bin:$PATH"
```

## Development Setup

### 1. Clone and Install Dependencies

```sh
git clone https://github.com/Ops-Talks/agronomist.git
cd agronomist
poetry install
```

This installs:

- **Core dependencies**: `requests`, `pyyaml`
- **Dev dependencies**: `ruff`, `black`, `mypy`, `bandit`, `eradicate`, `pytest`, `pytest-cov`, `pytest-benchmark`, `pre-commit`, `taskipy`, `zensical`

### 2. Verify Installation

```sh
poetry run agronomist --help
```

## Task Runner (taskipy)

Agronomist uses **taskipy** for convenient task management. All tasks are defined in `pyproject.toml`.

### Available Tasks

| Task | Command | Description |
|------|---------|-------------|
| `lint` | `poetry run task lint` | Run ruff check, ruff format, black, and mypy |
| `format` | `poetry run task format` | Auto-format code and remove dead code (ruff + black + eradicate) |
| `test` | `poetry run task test` | Run pytest test suite with coverage |
| `test-coverage` | `poetry run task test-coverage` | Run pytest with strict coverage (no --exitfirst) |
| `security` | `poetry run task security` | Run security checks (bandit + eradicate) |
| `check` | `poetry run task check` | Run linters + security + tests (recommended before commit) |
| `bandit` | `poetry run task bandit` | Run bandit security scanner |
| `mypy` | `poetry run task mypy` | Run mypy static type checker |
| `pre-commit-install` | `poetry run task pre-commit-install` | Install pre-commit hooks |
| `pre-commit-run` | `poetry run task pre-commit-run` | Run pre-commit on all files |
| `pre-commit` | `poetry run task pre-commit` | Install and run pre-commit hooks |
| `report` | `poetry run task report` | Run agronomist on itself (example) |
| `update` | `poetry run task update` | Update agronomist's own dependencies (example) |

### Quick Start

```sh
# Run lint + security + tests
poetry run task check

# Install pre-commit hooks
poetry run task pre-commit-install

# Run tests only
poetry run task test

# Run tests with coverage report
poetry run task test-coverage
```

## Linting and Formatting

### Tools

- **ruff** - Fast Python linter (checks style, imports, bugs)
- **black** - Code formatter (enforces consistent style)
- **mypy** - Static type checker (enforces type annotations)
- **bandit** - Security scanner (detects common vulnerabilities)
- **eradicate** - Dead code detector

### Configuration

Both tools are configured in `pyproject.toml`:

```toml
[tool.ruff]
line-length = 100
target-version = "py310"

[tool.black]
line-length = 100
target-version = ["py310"]
```

### Manual Commands

```sh
# Check code style
poetry run ruff check .

# Auto-format with ruff
poetry run ruff format .

# Auto-format with black
poetry run black .

# Combined check and format (via task)
poetry run task check
```

## Testing

### Run All Tests

```sh
poetry run pytest
```

### Run Specific Test

```sh
poetry run pytest tests/test_cli.py
```

### Run Tests with Coverage

```sh
make coverage
# or
poetry run pytest --cov=src/agronomist --cov-report=html
```

### Test Configuration

Tests use **pytest**. Configuration is managed in `pyproject.toml` (if present) or pytest defaults.

## Pre-commit Hooks

Pre-commit hooks automatically run linters and formatters before each commit.

### Install Hooks

```sh
poetry run task pre-commit-install
```

This installs Git hooks defined in `.pre-commit-config.yaml`.

### Run Hooks Manually

```sh
poetry run task pre-commit-run
```

### Bypass Hooks (not recommended)

```sh
git commit --no-verify
```

## CI/CD (Quality Checks)

The GitHub Actions workflow automatically runs quality checks:

- **Trigger**: On every push to `main` and pull requests
- **Command**: `poetry run task check` (linters + tests)

**Local equivalent**:
```sh
poetry run task check
```

Always run this locally before pushing to ensure CI will pass.

## Building

### Using Make (Recommended)

```sh
make build-docker
```

**Advantages**:

- Isolated Docker environment (no local Python version conflicts)
- Consistent build across machines
- Cleans up automatically

**Output**: `dist/agronomist-*.whl` and `dist/agronomist-*.tar.gz`

### Using Poetry Directly

```sh
poetry build
```

**Advantages**:

- No Docker required
- Faster build

**Output**: Same as above

### Build Artifacts

Both methods generate:

- `.whl` - Wheel distribution (for `pipx install`)
- `.tar.gz` - Source distribution

## Documentation

### Build Docs Locally

```sh
poetry run zensical serve
```

Starts a local server at `http://localhost:8000` with live reloading.

### Using Make

```sh
make docs-serve
```

### Features

- Built with **Zensical** + **Material Theme**
- Source files: `docs/`
- Auto-generated navigation from directory structure

## Release Process

### Prerequisites

- All tests must pass (`poetry run task check`)
- Changes committed and merged to `main`
- Version number decided (follow [Semantic Versioning](https://semver.org/))

### Steps

#### 1. Update Version

Edit `pyproject.toml`:

```toml
[tool.poetry]
version = "X.Y.Z"
```

#### 2. Commit Version Bump

```sh
git add pyproject.toml
git commit -m "Bump version to X.Y.Z"
git push
```

#### 3. Create Release Tag

```sh
git tag vX.Y.Z
git push origin vX.Y.Z
```

Or using Make:
```sh
make release TAG=vX.Y.Z
```

### GitHub Actions Release Workflow

Once the tag is pushed, `.github/workflows/release.yml` automatically:

1. Runs `poetry build`
2. Creates a GitHub Release
3. Uploads artifacts (`.whl` and `.tar.gz`)

**Result**: Users can install the release:

```sh
# Download from https://github.com/Ops-Talks/agronomist/releases/latest
pipx install agronomist-X.Y.Z-py3-none-any.whl
```

## Makefile Targets

Agronomist provides a Makefile with convenience targets:

```sh
make help              # Show all available targets
make build             # Build locally with Poetry
make build-docker      # Build in Docker (recommended)
make clean             # Remove build artifacts
make lint              # Run linters (ruff, black, mypy)
make format            # Format code and remove dead code
make test              # Run tests
make coverage          # Run tests with coverage report
make test-coverage     # Alias for coverage
make run-tests         # Alias for test
make security          # Run security checks (bandit, eradicate)
make check             # Run linters + security + tests
make docs-serve        # Serve documentation locally
make pre-commit        # Run pre-commit hooks
make release TAG=vX.Y.Z # Create release tag
```

## Project Structure

```
agronomist/
├── src/
│   └── agronomist/
│       ├── __init__.py
│       ├── cli.py              # CLI entry point
│       ├── config.py           # Configuration loader (categories & blacklist)
│       ├── models.py           # Data models (SourceRef, etc.)
│       ├── scanner.py          # File scanner
│       ├── git.py              # Git resolver
│       ├── github.py           # GitHub API resolver
│       ├── gitlab.py           # GitLab API resolver
│       ├── report.py           # JSON report generation
│       ├── markdown.py         # Markdown report generation
│       └── updater.py          # In-place file update application
├── test/
│   ├── fixtures/               # Test fixtures (report.json samples)
│   ├── integration/            # Shell integration tests
│   └── unit/
│       ├── python/             # Python test suite (pytest, 171 tests)
│       └── test_multi_pr.bats  # BATS shell tests
├── docs/                       # Documentation (MkDocs)
├── pyproject.toml              # Project metadata and dependencies
├── Makefile                    # Build and development targets
├── Dockerfile                  # Docker build configuration
├── .github/workflows/          # GitHub Actions workflows
└── README.md
```

## Code Style Guidelines

- **Line length**: 100 characters
- **Imports**: Organized via ruff (auto-formatted)
- **Python version**: 3.10+
- **Type hints**: Encouraged (Python 3.10+ supports modern syntax)

## Contributing

1. Create a branch from `main`
2. Make changes and test: `poetry run task check`
3. Push and open a pull request
4. GitHub Actions CI will run automatically
5. Once approved and green, merge to `main`

Release tags are created manually after merging to trigger the release workflow.
