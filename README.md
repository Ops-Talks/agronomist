# Agronomist

**Automate dependency version management for your Terraform/OpenTofu infrastructure.** 

Agronomist continuously monitors and reports on module updates, ensuring your IaC stays current, secure, and maintainable with minimal effort.

<div align="center">
  <img src="assets/agronomist-logo.png" width="400" alt="Agronomist Logo">
</div>

## What it does in MVP
- Scans .hcl and .tf files and finds `source` with `?ref=` pointing to GitHub.
- Queries releases/tags to suggest a new version.
- Generates JSON report and optionally updates refs in-place.
- Generate humam readable reports with updates using Markdown.
- Can be used via local CLI or GitHub Action.

## Requirements
- Python 3.10+
- Git installed (to resolve tags via `git ls-remote`)
- GitHub token (PAT) recommended to avoid rate limit when using `--resolver github`

## Quick start (CLI)
```
poetry install
poetry run agronomist report --root . --output report.json
poetry run agronomist report --root . --markdown report.md --output report.json
poetry run agronomist update --root . --output report.json
```

## Version resolver
- Default: `git` (uses `git ls-remote --tags`).
- Optional: `github` (uses GitHub API).

`git` works with GitHub, GitLab and other compatible Git servers.

Examples:
```
poetry run agronomist report --root . --resolver git --output report.json
poetry run agronomist report --root . --resolver github --output report.json
```

## Lint and tests
### Using task runner (taskipy)
```
poetry run task lint          # Run ruff and black
poetry run task format        # Format code
poetry run task test          # Run tests
poetry run task check         # Run linters + tests
poetry run task pre-commit    # Install and run pre-commit hooks
```

Or with `poe` alias (shorter):
```
poe lint          # Run ruff and black
poe format        # Format code
poe test          # Run tests
poe check         # Run linters + tests
poe pre-commit    # Install and run pre-commit hooks
```

### Using poetry directly
```
poetry run ruff check .
poetry run ruff format .
poetry run black .
poetry run pytest
```

## Pre-commit
Using task runner:
```
poetry run task pre-commit-install  # Install hooks
poetry run task pre-commit-run      # Run on all files
poetry run task pre-commit          # Install + run hooks
```

Or with `poe` alias:
```
poe pre-commit-install  # Install hooks
poe pre-commit-run      # Run on all files
poe pre-commit          # Install + run hooks
```

Using poetry directly:
```
poetry run pre-commit install
poetry run pre-commit run --all-files
```

## GitHub Action
See example in [examples/workflows/agronomist.yml](examples/workflows/agronomist.yml).

## Categories (config)
Create a `.agronomist.yaml` file (or specify `--config`) to classify dependencies:
```
categories:
  - name: aws
    repo_patterns:
      - "*/terraform-aws-*"
  - name: mysql
    repo_patterns:
      - "*/terraform-*-mysql-*"
  - name: postgres
    repo_patterns:
      - "*/terraform-*-postgres-*"
```
The `category` field will be included in the report and displayed in stdout.

## Design
See MVP design in [docs/design.md](docs/design.md).
