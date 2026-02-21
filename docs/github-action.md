# GitHub Action

Agronomist ships a composite action in `action.yml` that installs the package and runs the CLI.

## Inputs

- `github_token` GitHub token for API calls.
- `root` Root directory to scan.
- `include` Comma separated list of glob patterns.
- `exclude` Comma separated list of glob patterns.
- `mode` `report` or `update`.
- `output` Report file name.
- `github_base_url` GitHub API base URL.
- `resolver` Version resolver strategy: `git`, `github`, or `auto`.
- `config` Path to configuration file (supports category rules and blacklist filters).
- `no_report` Skip generating report files (useful for CI/CD pipelines). Default: `false`.

## Example workflow

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
      - name: Run Agronomist
        uses: ./.
        with:
          mode: "update"
          output: "report.json"
          github_token: ${{ secrets.GITHUB_TOKEN }}
```

## Workflow using GitHub Releases

If you prefer not to use the composite action, install Agronomist from GitHub Releases and run the CLI directly:

```yaml
name: Agronomist Updates (Releases)
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
          AGRONOMIST_VERSION="v0.5.0"
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
