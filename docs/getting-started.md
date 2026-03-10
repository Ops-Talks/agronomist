# Getting Started

This guide covers installing Agronomist and running your first scan against an infrastructure repository.

If you want to contribute to or develop Agronomist itself, see [Development](development.md) instead.

## Requirements

- Python 3.10 or newer
- Git installed and available on your `PATH` (used by the default `git` resolver)
- A GitHub token is recommended when using `--resolver github` to avoid API rate limits (`GITHUB_TOKEN` environment variable or `--github-token` flag)
- A GitLab token is required for private GitLab repositories when using `--resolver auto` (`GITLAB_TOKEN` environment variable or `--gitlab-token` flag)

## Install

### Using pipx (recommended)

`pipx` installs Agronomist in an isolated environment and makes the `agronomist` command globally available.

#### From a release wheel

Download the latest `.whl` from the [Releases page](https://github.com/Ops-Talks/agronomist/releases) and install it:

```sh
pipx install agronomist-X.Y.Z-py3-none-any.whl
```

#### Build from source with Docker

The Docker build produces a wheel without requiring a specific local Python version:

```sh
git clone https://github.com/Ops-Talks/agronomist.git
cd agronomist
make build-docker
pipx install dist/agronomist-*-py3-none-any.whl
```

#### Build from source with Poetry

```sh
git clone https://github.com/Ops-Talks/agronomist.git
cd agronomist
poetry build
pipx install dist/agronomist-*-py3-none-any.whl
```

### Verify the installation

```sh
agronomist --help
```

## Run a report

The `report` command scans your infrastructure files and produces a JSON report of available module updates. No files are modified.

```sh
# Scan the current directory
agronomist report

# Scan a specific directory
agronomist report --root ./infrastructure

# Write the JSON report to a custom path
agronomist report --root ./infrastructure --json updates.json

# Also generate a human-readable Markdown summary
agronomist report --root ./infrastructure --json updates.json --markdown updates.md
```

## Apply updates

The `update` command applies the identified version changes directly to your source files and also produces a JSON report.

```sh
# Apply updates in the current directory
agronomist update

# Apply updates in a specific directory
agronomist update --root ./infrastructure --json updates.json
```

!!! warning
    Review the generated report before applying updates to production infrastructure. The `report` command is always safe — it never modifies files.

## Set up a configuration file

Place a `.agronomist.yaml` file in your repository root to configure category rules and blacklists. Agronomist loads it automatically.

See [Configuration](configuration.md) for the full file format and options.

## Authenticate with GitHub or GitLab

Export your tokens as environment variables before running Agronomist:

```sh
export GITHUB_TOKEN="ghp_..."
export GITLAB_TOKEN="glpat-..."
```

Alternatively, pass them as flags:

```sh
agronomist report --github-token ghp_... --root ./infrastructure
```

## Next steps

- [CLI Reference](cli.md) — complete list of options and flags.
- [Configuration](configuration.md) — configure category tagging and blacklists.
- [Resolvers](resolvers.md) — choose between Git, GitHub API, and GitLab API resolvers.
- [Reports](reports.md) — understand the report output format.
- [GitHub Action](github-action.md) — run Agronomist automatically in GitHub Actions.
- [GitLab CI](gitlab-ci.md) — run Agronomist and create merge requests in GitLab CI.

