# CLI

Agronomist exposes two subcommands: `report` and `update`.

## Commands

### Report

```sh
agronomist report [options]
```

Scans Terraform/OpenTofu files and generates a JSON report with available module version updates. Does not modify any files.

### Update

```sh
agronomist update [options]
```

Scans Terraform/OpenTofu files, identifies available module version updates, and applies them directly to the source files. Also generates a JSON report.

## Options

### Required/Common Options

| Option | Description | Default |
|--------|-------------|---------|
| `--root` | Root directory to scan for `.tf` and `.hcl` files. | `.` (current directory) |
| `--config` | Path to `.agronomist.yaml` or JSON configuration file. | `.agronomist.yaml` |

### Filtering Options

| Option | Description |
|--------|-------------|
| `--include` | Glob patterns to include in scan. Can be specified multiple times. |
| `--exclude` | Glob patterns to exclude from scan. Can be specified multiple times. |

**Note**: Additional filtering via **blacklist** can be configured in `.agronomist.yaml` to permanently ignore specific repositories, modules, or files. See [Configuration](configuration.md) for details.

### API & Authentication

| Option | Description | Default |
|--------|-------------|---------|
| `--github-token` | Authentication token for GitHub API (PAT - Personal Access Token). Can also be set via `GITHUB_TOKEN` environment variable. | Read from `GITHUB_TOKEN` env var |
| `--gitlab-token` | Authentication token for GitLab API (PAT - Personal Access Token). Can also be set via `GITLAB_TOKEN` environment variable. | Read from `GITLAB_TOKEN` env var |
| `--token` | Shared fallback token for GitHub and GitLab APIs when specific tokens are not provided. | Not set |
| `--github-base-url` | GitHub API base URL (useful for GitHub Enterprise). | `https://api.github.com` |
| `--resolver` | Version resolution strategy. See [Resolution Strategies](#resolution-strategies). | `git` |
| `--validate-token` | Validate API token before processing (useful for CI/CD pipelines). Does not scan if invalid. | `false` |

### Output Options

| Option | Description | Default |
|--------|-------------|---------|
| `--output` | Path to write JSON report. | `report.json` |
| `--markdown` | Path to write human-readable Markdown report. If omitted, no Markdown is generated. | Not set || `--no-report` | Skip generating report files (useful for CI/CD pipelines). | `false` |
## Resolution Strategies

The `--resolver` option determines how Agronomist queries for the latest module version:

### `git` (default)

- Uses `git ls-remote --tags` to fetch the latest release from Git repositories
- Works with GitHub, GitLab, Gitea, and other Git-compatible servers
- Does not require authentication
- **Best for**: Most use cases, especially private repositories without API access

### `github`

- Uses GitHub API to fetch releases and tags
- Only works with GitHub.com (or GitHub Enterprise with `--github-base-url`)
- Requires valid GitHub token for better rate limits
- **Best for**: Public repositories or when you need GitHub-specific features

### `auto`

- Automatically selects the best resolver based on repository host
- Uses GitLab API for GitLab repositories
- Uses GitHub API for GitHub repositories
- Falls back to Git for other repositories
- Requires tokens if accessing private repositories
- **Best for**: Mixed environments with multiple Git hosting platforms

## Environment Variables

- `GITHUB_TOKEN` - Default authentication token for GitHub API. Used when `--github-token` is not specified.
- `GITLAB_TOKEN` - Default authentication token for GitLab API. Used when `--gitlab-token` is not specified.

## Exit Codes

- `0` - Success
- `1` - Error (invalid token, scan failure, etc.)

## Examples

### Basic Report Generation

```sh
# Generate report for current directory
agronomist report

# Generate report for specific directory
agronomist report --root ./infrastructure

# Generate report and save to custom location
agronomist report --output ./reports/versions.json
```

### With Markdown Output

```sh
# Generate both JSON and Markdown reports
agronomist report --markdown report.md --output report.json

# Generate Markdown report for documentation
agronomist report --root ./terraform --markdown UPDATES.md
```

### Using Environment Variables

```sh
# Use GITHUB_TOKEN from environment (GitHub API)
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
agronomist report --root . --resolver github

# Or pass token inline
GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxx" agronomist report --root . --resolver github

# Use GITLAB_TOKEN from environment (GitLab API)
export GITLAB_TOKEN="glpat_xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
agronomist report --root . --resolver auto
```

### Using GitHub Enterprise

```sh
# Point to GitHub Enterprise API with token
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
agronomist report --github-base-url https://github.enterprise.com/api/v3 --resolver github

# Or pass token directly
agronomist report --github-base-url https://github.enterprise.com/api/v3 --resolver github --github-token $GITHUB_TOKEN
```

### Filtering Files

```sh
# Include only specific patterns
agronomist report --include "**/*.tf" --include "**/*.hcl"

# Exclude specific patterns
agronomist report --exclude "**/test/**" --exclude "**/*_test.tf"

# Combine include and exclude
agronomist report --include "**/*.tf" --exclude "**/examples/**"
```

### Validating Token Before Processing

```sh
# Validate token in CI/CD before running expensive scan (GitHub)
agronomist report --github-token $GITHUB_TOKEN --validate-token

# Validate token in CI/CD before running expensive scan (GitLab)
agronomist report --gitlab-token $GITLAB_TOKEN --validate-token

# If token is invalid, exit with code 1
```

### Updating Modules

```sh
# Update all modules and generate report
agronomist update --output report.json

# Update with Markdown report
agronomist update --markdown UPDATES.md --output report.json

# Update specific directory with token
agronomist update --root ./terraform --resolver github --github-token $GITHUB_TOKEN

# Update without generating report files (useful for CI/CD)
agronomist update --no-report
```
