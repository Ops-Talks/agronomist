# GitHub Action

## Available CLI Options

When running Agronomist in GitHub Actions, you can use these CLI options:

- `--github-token` GitHub token for API calls (or use `GITHUB_TOKEN` env var).
- `--root` Root directory to scan. Default: `.`
- `--include` Glob patterns to include. Can be specified multiple times.
- `--exclude` Glob patterns to exclude. Can be specified multiple times.
- `--output` Report file name. Default: `report.json`
- `--markdown` Markdown report file (optional).
- `--github-base-url` GitHub API base URL (for GitHub Enterprise).
- `--resolver` Version resolver strategy: `git`, `github`, or `auto`. Default: `git`
- `--config` Path to configuration file. Default: `.agronomist.yaml`
- `--no-report` Skip generating report files (useful for CI/CD pipelines).
- `--validate-token` Validate API token before processing.

## Example Workflow

Install Agronomist from GitHub Releases and run the CLI directly in your workflow:

```yaml
name: Agronomist Updates
on:
  schedule:
    - cron: "0 7 * * 1"
  workflow_dispatch: {}

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install Agronomist
        run: |
          AGRONOMIST_VERSION="v0.5.3"
          WHEEL="agronomist-${AGRONOMIST_VERSION#v}-py3-none-any.whl"
          curl -L -o "$WHEEL" "https://github.com/Ops-Talks/agronomist/releases/download/${AGRONOMIST_VERSION}/${WHEEL}"
          pip install "$WHEEL"
      - name: Run Agronomist
        run: |
          agronomist update --root . --no-report
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

See [examples/workflows/agronomist-ci.yml](https://github.com/Ops-Talks/agronomist/blob/main/examples/workflows/agronomist-ci.yml) for a full example.
