# CLI

Agronomist exposes two subcommands: `report` and `update`.

## Report

```sh
agronomist report [options]
```

## Update

```sh
agronomist update [options]
```

## Common options

- `--root` Root directory to scan. Default: `.`
- `--include` Glob patterns to include. May be specified multiple times.
- `--exclude` Glob patterns to exclude. May be specified multiple times.
- `--github-base-url` GitHub API base URL. Default: `https://api.github.com`
- `--token` Token for GitHub and GitLab APIs. Default: from `GITHUB_TOKEN`.
- `--config` Path to `.agronomist.yaml` or JSON config. Default: `.agronomist.yaml`
- `--resolver` Version resolver strategy: `git`, `github`, or `auto`.
- `--output` Report output file. Default: `report.json`
- `--markdown` Path for Markdown report output.
- `--validate-token` Validate API token before processing.

## Examples

```sh
poetry run agronomist report --root . --output report.json
poetry run agronomist report --root . --resolver github --token $GITHUB_TOKEN
poetry run agronomist report --root . --markdown report.md --output report.json
poetry run agronomist update --root . --output report.json
```
