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
- `config` Path to configuration file.

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

See [examples/workflows/agronomist.yml](https://github.com/Ops-Talks/agronomist/blob/main/examples/workflows/agronomist.yml) for a full example.
