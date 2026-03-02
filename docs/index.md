# Agronomist

<div align="center">
  <img src="assets/agronomist-logo.svg" width="400" alt="Agronomist Logo">
</div>

Agronomist continuously monitors and reports on module version updates across Terraform and OpenTofu codebases. It identifies outdated `?ref=` pins in `.tf` and `.hcl` files, resolves the latest available versions, and can apply updates automatically — keeping your Infrastructure as Code current, secure, and maintainable with minimal manual effort.

## How it works

1. Scan `.tf` and `.hcl` files for `source` references that contain `?ref=`.
2. Resolve the latest available version using Git tags, the GitHub API, or the GitLab API.
3. Generate a structured JSON report and an optional human-readable Markdown summary.
4. Optionally apply updates in place across all affected files.

## Core features

- Multi-resolver support: Git, GitHub API, GitLab API, or automatic detection.
- Category tagging for grouping updates by team or domain (e.g., `aws`, `database`).
- Blacklist filtering to permanently ignore specific repositories, modules, or files.
- CI/CD integration for GitHub Actions and GitLab CI, including automated pull and merge request creation.
- Python library API for custom automation workflows.

---

## For SREs and infrastructure teams

If you want to install Agronomist and run it against your infrastructure repositories, start here:

- [Getting Started](getting-started.md) — install, configure, and run your first report in minutes.
- [CLI Reference](cli.md) — full command and option reference.
- [Configuration](configuration.md) — define categories and blacklists with `.agronomist.yaml`.
- [Resolvers](resolvers.md) — choose the right version resolution strategy for your environment.
- [Reports](reports.md) — understand the JSON and Markdown report formats.
- [GitHub Action](github-action.md) — automate updates via GitHub Actions workflows.
- [GitLab CI](gitlab-ci.md) — automate updates via GitLab CI pipelines with automatic MR creation.
- [Troubleshooting](troubleshooting.md) — common issues and solutions.

## For contributors and developers

If you want to contribute to Agronomist or integrate it as a Python library:

- [Architecture](architecture.md) — internal design, components, and data flow.
- [Development](development.md) — environment setup, tooling, build process, and release workflow.
- [Testing](testing.md) — test suite structure, how to run tests, and how to add new ones.
- [API Reference](api.md) — use Agronomist as a Python library in your own tooling.

