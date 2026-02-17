# Getting Started

## Requirements
- Python 3.10 or newer
- Git installed (used for `git ls-remote`)
- GitHub token recommended to avoid rate limits when using `--resolver github`

## Install

For local development from this repository:

```sh
poetry install
```

## Run a report

```sh
poetry run agronomist report --root . --output report.json
```

## Apply updates

```sh
poetry run agronomist update --root . --output report.json
```

## Generate Markdown report

```sh
poetry run agronomist report --root . --markdown report.md --output report.json
```

## Next steps

- Review [CLI](cli.md) options
- Configure categories in [Configuration](configuration.md)
