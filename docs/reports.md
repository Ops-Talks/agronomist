# Reports

Agronomist can produce JSON and Markdown reports.

## JSON report

The JSON report is always produced and written to `--output`.

Example structure:

```json
{
  "generated_at": "2026-02-17T12:34:56Z",
  "root": ".",
  "updates": [
    {
      "repo": "owner/repo",
      "repo_host": "github.com",
      "repo_url": "https://github.com/owner/repo",
      "module": "modules/vpc",
      "current_ref": "v1.2.0",
      "latest_ref": "v1.4.1",
      "strategy": "latest",
      "category": "aws",
      "files": ["infra/prod/vpc/terragrunt.hcl"],
      "replacements": [
        {"from": "source = ...", "to": "source = ..."}
      ]
    }
  ]
}
```

## Markdown report

Use `--markdown` to generate a human readable summary.

Example:

```sh
poetry run agronomist report --root . --markdown report.md --output report.json
```

Example output:

```markdown
# Agronomist Report

**Generated at:** 2026-02-17T12:34:56Z
**Root:** `.`

## Summary

- **Total updates:** 2
- **Affected repositories:** 2
- **Affected modules:** 2

## Updates by Repository

### terraform-aws/vpc (github.com)

#### Module: `vpc`

**v1.2.0 -> v1.4.1**
- Category: `aws`
- Affected files: 1
  - `infra/prod/vpc/terragrunt.hcl`

### terraform-aws/rds (github.com)

#### Module: `rds`

**v3.0.0 -> v3.1.0**
- Category: `database`
- Affected files: 1
  - `infra/prod/db/terragrunt.hcl`
```
