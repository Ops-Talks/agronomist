# Getting Started

## Requirements
- Python 3.10 or newer
- Git installed (used for `git ls-remote`)
- GitHub token recommended to avoid rate limits when using `--resolver github`

## Install

### Using pipx (recommended)

Build and install globally:

```sh
poetry build
pipx install dist/agronomist-0.1.0-py3-none-any.whl
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
