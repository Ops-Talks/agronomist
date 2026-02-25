# Getting Started

## Requirements

- Python 3.10 or newer
- Git installed (used for `git ls-remote`)
- GitHub token recommended to avoid rate limits when using `--resolver github` (`GITHUB_TOKEN` or `--github-token`)
- GitLab token recommended for private GitLab repositories when using `--resolver auto` (`GITLAB_TOKEN` or `--gitlab-token`)

## Install

### Using pipx (recommended)

#### From GitHub Releases (pre-built)

Download the latest version from [Releases](https://github.com/Ops-Talks/agronomist/releases):

```sh
pipx install agronomist-X.Y.Z-py3-none-any.whl
```

#### From Source (build locally)

##### With Make (simplest)

```sh
git clone https://github.com/Ops-Talks/agronomist.git
cd agronomist
make build-docker
pipx install dist/agronomist-*-py3-none-any.whl
```

##### With Poetry

```sh
git clone https://github.com/Ops-Talks/agronomist.git
cd agronomist
poetry build
pipx install dist/agronomist-*-py3-none-any.whl
```

### For local development

If you want to develop the project:

```sh
poetry install
```

## Run a report

### With pipx

```sh
agronomist report --root . --output report.json
```

### With poetry

```sh
poetry run agronomist report --root . --output report.json
```

## Apply updates

### With pipx

```sh
agronomist update --root . --output report.json
```

### With poetry

```sh
poetry run agronomist update --root . --output report.json
```

## Generate Markdown report

### With pipx

```sh
agronomist report --root . --markdown report.md --output report.json
```

### With poetry

```sh
poetry run agronomist report --root . --markdown report.md --output report.json
```

## Next steps

- Review [CLI](cli.md) options
- Configure categories in [Configuration](configuration.md)
- CI runs `poetry run task check` on pushes to `main` and on pull requests.
- Releases are created by pushing a SemVer tag (e.g. `v0.3.8`).
