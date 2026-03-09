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

## Minimal Example

The following workflow installs Agronomist from GitHub Releases and applies updates. It does not create pull requests -- use it as a starting point or for simple single-commit workflows:

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
          AGRONOMIST_VERSION="v1.2.3"
          WHEEL="agronomist-${AGRONOMIST_VERSION#v}-py3-none-any.whl"
          curl -L -o "$WHEEL" "https://github.com/Ops-Talks/agronomist/releases/download/${AGRONOMIST_VERSION}/${WHEEL}"
          pip install "$WHEEL"
      - name: Run Agronomist
        run: |
          agronomist update --root . --no-report
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## Full Multi-PR Example

For production use, the recommended workflow creates **one pull request per updated module**. Each branch is named with the module identifier and a short hash, so re-running the pipeline updates existing PRs rather than creating duplicates.

See [examples/workflows/agronomist-ci.yml](https://github.com/Ops-Talks/agronomist/blob/main/examples/workflows/agronomist-ci.yml) for the full workflow that:

- Runs `agronomist update` and generates `report.json`.
- Iterates over each module in the report using `jq`.
- Creates a dedicated branch and PR per module via `gh pr create`.
- Uses SHA-256 hashing to produce deterministic, unique branch names.

## Branch naming

When creating one PR per module, each branch is named:

```
agronomist/update-<base-module>-<hash8>
```

- **`<base-module>`** — the module name (path before `@`), with `/` and `@` replaced by `-`, truncated to 50 characters.
- **`<hash8>`** — first 8 characters of the SHA-256 hash of the full module ID (base module + file path). This ensures two files that reference the same upstream module produce distinct branch names.

The PR title and commit message use the same pattern: `[Agronomist] Update <base-module> to <latest-ref>`.

### Examples

| Module ID in `report.json` | Branch name | PR title |
|---|---|---|
| `hashicorp/terraform-provider-aws@infra/versions.tf` | `agronomist/update-hashicorp-terraform-provider-aws-ea7332eb` | `[Agronomist] Update hashicorp/terraform-provider-aws to 5.1.0` |
| `terraform-aws-modules/vpc/aws@infra/network.tf` | `agronomist/update-terraform-aws-modules-vpc-aws-3335a2ca` | `[Agronomist] Update terraform-aws-modules/vpc/aws to v5.2.0` |
| `terraform-aws-modules/rds/aws@infra/database.tf` | `agronomist/update-terraform-aws-modules-rds-aws-f7fab219` | `[Agronomist] Update terraform-aws-modules/rds/aws to v3.1.0` |
| `terraform-aws-modules/eks/aws@platform/eks/main.tf` | `agronomist/update-terraform-aws-modules-eks-aws-55583821` | `[Agronomist] Update terraform-aws-modules/eks/aws to v20.0.0` |
| `cloudwatch-log-group@providers/aws/contoso/dev/us-east-2/cloudwatch-log-group/terragrunt.hcl` | `agronomist/update-cloudwatch-log-group-8bfc52c9` | `[Agronomist] Update cloudwatch-log-group to v1.2.0` |
| `cloudwatch-log-group@providers/aws/contoso/prod/eu-west-1/cloudwatch-log-group/terragrunt.hcl` | `agronomist/update-cloudwatch-log-group-4e428acf` | `[Agronomist] Update cloudwatch-log-group to v1.2.0` |

The last two rows show the same upstream module (`cloudwatch-log-group`) referenced from two different files. Because the hash is derived from the full module ID (including the file path), each file gets a **unique** branch and PR — even though the base module name is identical.
