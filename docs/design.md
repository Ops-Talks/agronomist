# Agronomist: MVP Design

## Objective
Develop a tool that detects and updates references of Terragrunt modules, keeping IaC up to date, using:
- Local CLI to report and update references of GitHub modules.
- GitHub Action to run the CLI and allow opening PR via workflow.
- Detection of breaking changes only by warning (without patches).

## Scope of MVP
- Scan of .hcl and .tf files in a root directory.
- Discovery of Git dependencies in `source` with `?ref=`.
- Resolution of new version via Git:
  - Uses `git ls-remote --tags` as primary source.
  - Optionally uses GitHub API when configured.
- Generates JSON report with dependencies and update suggestions.
- Optionally applies updates in-place (replaces `ref=`).

## Not included in MVP
- Patches for breaking changes.
- Validation of plans or application of Terraform/Tofu.
- Terraform Registry.
- Wide support for VCS beyond Git.

## Components
1) Scanner
- Traverses files, applies include/exclude via glob.
- Extracts `source` with simple regex.
- Normalizes GitHub repositories and current ref.

1b) Categorizer
- Loads category rules via YAML/JSON.
- Classifies dependencies by repository or module patterns.

2) Resolver
- Consults GitHub API using token.
- Determines latest available version (release/tag).
- Compares versions and marks candidate.

3) Updater
- Replaces old `source` with new one within the file.
- Keeps the rest of the file intact.

4) Reporter
- Exports JSON with dependencies, versions and suggestions.
- Includes list of affected files.
- Adds `category` when configured.

## Report format (JSON)
```
{
  "generated_at": "2026-02-17T12:34:56Z",
  "root": ".",
  "updates": [
    {
      "repo": "gruntwork-io/terraform-aws-vpc",
      "repo_host": "github.com",
      "repo_url": "https://github.com/gruntwork-io/terraform-aws-vpc",
      "module": "modules/vpc",
      "current_ref": "v1.2.0",
      "latest_ref": "v1.4.1",
      "strategy": "latest",
      "category": "aws",
      "files": ["infrastructure-live/prod/vpc/terragrunt.hcl"]
    }
  ]
}
```

## CLI
- `agronomist report --root . --output report.json`
- `agronomist update --root . --output report.json`

Flags:
- `--include`, `--exclude` (glob)
- `--github-base-url` (default: https://api.github.com)
- `--token` (PAT or via env GITHUB_TOKEN)

## GitHub Action
- Composite action that installs the package and runs the CLI.
- Opening PR is left to the workflow, using `peter-evans/create-pull-request`.

## Risks and limitations
- Regex may miss more complex HCL formats.
- Version comparison uses simple string (without advanced semver).
- No automatic detection of breaking changes.

## Next steps
- Real HCL parser (python-hcl2) for greater robustness.
  - Replace regex with HCL parser and map `source` to real structures.
  - Ensure support for `locals`, `include`, `dependency` and multi-line strings.
  - Add tests with varied HCL fixtures.
- Terraform Registry support.
  - Resolve versions via Registry API and map namespace/module/provider.
  - Allow configuring priorities: Registry vs GitHub.
  - Local cache to reduce network calls.
- Grouping rules by dependency for PRs.
  - Group by repo/module/category and generate one PR per group.
  - Add size rules (e.g.: max N updates per PR).
  - Adjust workflow to create distinct branches.
- `next-safe` strategies with generated changelogs.
  - Implement real semver comparison and version jumping with zero changes.
  - Generate consolidated changelog in report/PR.
  - Allow filters (security/bugfix/feature).
