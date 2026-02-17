# Development

## Setup

```sh
poetry install
```

## Task runner (taskipy)

```sh
poetry run task lint
poetry run task format
poetry run task test
poetry run task check
poetry run task pre-commit
```

## Pre-commit

```sh
poetry run task pre-commit-install
poetry run task pre-commit-run
```

## Tests

```sh
poetry run pytest
```

## Linting and formatting

```sh
poetry run ruff check .
poetry run ruff format .
poetry run black .
```

## Building

### Using Make (recommended)

```sh
make build-docker
```

Generates `dist/agronomist-*.whl` and `dist/agronomist-*.tar.gz` using Docker.

### Using Poetry

```sh
poetry build
```

Generates `dist/agronomist-*.whl` and `dist/agronomist-*.tar.gz`

## Release

1. Update version in `pyproject.toml`:
   ```toml
   version = "X.Y.Z"
   ```

2. Commit and push:
   ```sh
   git add pyproject.toml
   git commit -m "Bump version to X.Y.Z"
   git push
   ```

3. Create and push tag (following SemVer):
   ```sh
   git tag vX.Y.Z
   git push origin vX.Y.Z
   ```

The GitHub Actions workflow (`release.yml`) will automatically:
- Build the package
- Create a GitHub Release
- Upload built artifacts (`.whl` and `.tar.gz`) to the release

Users can then download and install via pipx:
```sh
pipx install agronomist-X.Y.Z-py3-none-any.whl
```
