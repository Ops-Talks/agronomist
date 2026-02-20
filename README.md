# Agronomist

**Automate dependency version management for your Terraform/OpenTofu infrastructure.** 

Agronomist continuously monitors and reports on module updates, ensuring your IaC stays current, secure, and maintainable with minimal effort.

<div align="center">
  <img src="assets/agronomist-logo.png" width="400" alt="Agronomist Logo">
</div>

## What it does?
- Scans `.hcl` and `.tf` files and finds `source` with `?ref=` pointing to GitHub.
- Queries releases/tags to suggest a new version.
- Generates JSON report and optionally updates refs in-place.
- Generate humam readable reports with updates using Markdown.
- Can be used via local CLI or GitHub Action.

## Requirements
- Python 3.10+
- Git installed (to resolve tags via `git ls-remote`)
- GitHub token (PAT) recommended to avoid rate limit when using `--resolver github` (`GITHUB_TOKEN` or `--github-token`)
- GitLab token (PAT) recommended for private GitLab repositories when using `--resolver auto` (`GITLAB_TOKEN` or `--gitlab-token`)

## Quick start (CLI)

### Install from Latest Release (recommended)
```bash
# Download the latest wheel from releases
# https://github.com/Ops-Talks/agronomist/releases/latest

# Install globally with pipx
pipx install agronomist-X.Y.Z-py3-none-any.whl
```

### Build from Source

#### Using Make (recommended)
```bash
make build-docker
# Artifacts in dist/
pipx install dist/agronomist-*-py3-none-any.whl
```

#### Using Poetry
```bash
poetry build
pipx install dist/agronomist-*-py3-none-any.whl
```

### Usage (after installing with pipx)
```bash
agronomist report --root . --output report.json
agronomist report --root . --markdown report.md --output report.json
agronomist update --root . --output report.json
```

### Alternative: Using poetry directly
```bash
poetry install
poetry run agronomist report --root . --output report.json
poetry run agronomist report --root . --markdown report.md --output report.json
poetry run agronomist update --root . --output report.json
```

## Documentation
- Getting started: [docs/getting-started.md](docs/getting-started.md)
- CLI reference: [docs/cli.md](docs/cli.md)
- Configuration: [docs/configuration.md](docs/configuration.md)
- Resolvers: [docs/resolvers.md](docs/resolvers.md)
- Reports: [docs/reports.md](docs/reports.md)
- GitHub Action: [docs/github-action.md](docs/github-action.md)
- GitLab CI: [docs/gitlab-ci.md](docs/gitlab-ci.md)
