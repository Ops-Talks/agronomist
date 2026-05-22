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
| `--root` | Root directory to scan for Terragrunt (`.hcl`), OpenTofu, and Terraform (`.tf`) files. | `.` (current directory) |
| `--config` | Path to `.agronomist.yaml` or JSON configuration file. | `.agronomist.yaml` |
| `--version` | Show the version of Agronomist and exit. | Not set |

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
| `--bitbucket-token` | Authentication token for Bitbucket Cloud API. Can also be set via `BITBUCKET_TOKEN` environment variable. | Read from `BITBUCKET_TOKEN` env var |
| `--bitbucket-username` | Optional Bitbucket username for App Password Basic Auth. When omitted, `--bitbucket-token` is used as a Bearer token. | Not set |
| `--token` | Shared fallback token for GitHub, GitLab, and Bitbucket APIs when specific tokens are not provided. | Not set |
| `--github-base-url` | GitHub API base URL (useful for GitHub Enterprise). | `https://api.github.com` |
| `--gitlab-base-url` | GitLab API base URL (useful for self-hosted GitLab). | `https://gitlab.com` |
| `--bitbucket-base-url` | Bitbucket API base URL. | `https://api.bitbucket.org/2.0` |
| `--resolver` | Version resolution strategy. See [Resolution Strategies](#resolution-strategies). | `git` |
| `--validate-token` | Validate API token before processing (useful for CI/CD pipelines). Does not scan if invalid. | `false` |

### Output Options

| Option | Description | Default |
|--------|-------------|---------|
| `--json` | Path to write JSON report. | Not set |
| `--markdown` | Path to write human-readable Markdown report. | Not set |

## Reporting Behavior

By default, Agronomist runs the scan and prints a summary of discovered updates to the terminal. **No output files are generated unless explicitly requested.**

- To generate a JSON report, use the `--json <path>` flag.
- To generate a Markdown summary, use the `--markdown <path>` flag.
- Both flags can be used simultaneously to produce both formats.

If these flags are omitted, Agronomist will only output its findings to `stdout` and `stderr` (logs).

### Performance Options

| Option | Description | Default |
|--------|-------------|---------|
| `--timeout` | Request timeout in seconds for API calls and `git ls-remote` operations. | `20` |
| `--workers` | Number of parallel workers used to resolve versions concurrently. Higher values reduce wall-clock time when scanning many distinct upstream modules. | `10` |

### Logging Options

| Option | Description |
|--------|-------------|
| `--verbose`, `-v` | Enable `DEBUG`-level logging. Shows every HTTP request, git call, and resolution decision. |
| `--quiet` | Suppress `INFO` output. Only warnings and errors are printed. Mutually exclusive with `--verbose`. |

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

### `bitbucket`

- Uses Bitbucket Cloud API to fetch tags
- Only works with Bitbucket Cloud
- Supports Repository Access Tokens as Bearer tokens and App Passwords with `--bitbucket-username`
- Requires valid Bitbucket token for private repositories
- **Best for**: Bitbucket Cloud repositories or when Git protocol access is restricted

### `auto`

- Automatically selects the best resolver based on repository host
- Uses GitLab API for GitLab repositories
- Uses GitHub API for GitHub repositories
- Uses Bitbucket API for Bitbucket Cloud repositories
- Falls back to Git for other repositories
- Requires tokens if accessing private repositories
- **Best for**: Mixed environments with multiple Git hosting platforms

## Environment Variables

- `GITHUB_TOKEN` - Default authentication token for GitHub API. Used when `--github-token` is not specified.
- `GITLAB_TOKEN` - Default authentication token for GitLab API. Used when `--gitlab-token` is not specified.
- `BITBUCKET_TOKEN` - Default authentication token for Bitbucket Cloud API. Used when `--bitbucket-token` is not specified.

> **Security note:** Prefer environment variables (`GITHUB_TOKEN`, `GITLAB_TOKEN`, `BITBUCKET_TOKEN`) over the `--token`, `--github-token`, `--gitlab-token`, and `--bitbucket-token` CLI flags.  Arguments passed on the command line may be visible in shell history, process listings (`ps`), and CI/CD logs.  Environment variables avoid this exposure.

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
agronomist report --json ./reports/versions.json
```

### With Markdown Output

```sh
# Generate both JSON and Markdown reports
agronomist report --markdown report.md --json report.json

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

# Use BITBUCKET_TOKEN from environment (Bitbucket Cloud API)
export BITBUCKET_TOKEN="xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
agronomist report --root . --resolver bitbucket
```

### Using GitHub Enterprise

```sh
# Point to GitHub Enterprise API with token
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
agronomist report --github-base-url https://github.enterprise.com/api/v3 --resolver github

# Or pass token directly
agronomist report --github-base-url https://github.enterprise.com/api/v3 --resolver github --github-token $GITHUB_TOKEN
```

### Using Bitbucket Cloud

```sh
# Use a Repository Access Token as a Bearer token
export BITBUCKET_TOKEN="xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
agronomist report --bitbucket-base-url https://api.bitbucket.org/2.0 --resolver bitbucket

# Or use an App Password with Basic Auth
agronomist report --resolver bitbucket --bitbucket-username "$BITBUCKET_USERNAME" --bitbucket-token "$BITBUCKET_TOKEN"
```

### Using Self-Hosted GitLab

```sh
# Point to self-hosted GitLab with token
export GITLAB_TOKEN="glpat-xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
agronomist report --gitlab-base-url https://gitlab.company.com --resolver auto

# Or pass token directly
agronomist report --gitlab-base-url https://gitlab.company.com --resolver auto --gitlab-token $GITLAB_TOKEN
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

# Validate token in CI/CD before running expensive scan (Bitbucket)
agronomist report --bitbucket-token $BITBUCKET_TOKEN --validate-token

# If token is invalid, exit with code 1
```

### Updating Modules

```sh
# Update all modules and generate report
agronomist update --json report.json

# Update with Markdown report
agronomist update --markdown UPDATES.md --json report.json

# Update specific directory with token
agronomist update --root ./terraform --resolver github --github-token $GITHUB_TOKEN
```
