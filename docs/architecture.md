# Architecture

This document describes the internal design of Agronomist for contributors and developers. See [Development](development.md) for setup instructions.

## Overview

Agronomist is a command-line tool that inspects Terraform source files, resolves the latest version for each external module, produces a structured report, and optionally applies updates in place.

The data flow is linear and stateless between runs:

```
Project files on disk
       |
       v
   [Scanner]          -- walks the file tree, extracts module source= references
       |
       v
   [Resolver]         -- looks up the latest tag or release for each repo
       |
       v
   [Report builder]   -- structures the diff as a JSON report + Markdown summary
       |
       v (optional)
   [Updater]          -- rewrites source= lines in place with the new ref
```

---

## Modules

### `scanner`

Entry point for file discovery. Implements `scan_sources()`, which walks a root directory recursively, parses every file for `source = "..."` lines, and extracts structured `SourceRef` objects for any source that contains a `?ref=` segment.

Filtering is applied during the walk:

- Files matching `file_blacklist` patterns are skipped.
- Repos matching `repo_blacklist` are excluded from the output.
- Modules matching `module_blacklist` are excluded from the output.

The `_parse_git_source()` helper uses a compiled regex to decompose sources of the form `git::https://host/org/repo.git//module/path?ref=vX.Y.Z` into structured fields (`repo_host`, `repo`, `module`, `ref`).

### `models`

Defines the core dataclasses:

- `SourceRef` — a single scanned module reference (file path, raw source string, repo, host, current ref, module path).
- `UpdateEntry` — extends `SourceRef` with the resolved latest ref.
- `Report` — the aggregate result (`schema_version`, `scan_root`, timestamp, list of `UpdateEntry` objects).

### `git`

Implements the `git` resolver. Calls `git ls-remote --tags <url>`, parses the output for tag refs, strips `^{}` derefs, filters out non-semver tags, and returns the latest by version sort.

### `github`

Implements the `github` resolver. Uses `GET /repos/{owner}/{repo}/git/refs/tags` via the GitHub REST API. Supports:

- Optional Bearer token (`GITHUB_TOKEN` / `--github-token`).
- Custom base URL for GitHub Enterprise (`--github-base-url`).

Returns the latest tag by semver sort.

### `gitlab`

Implements the `auto`-path for GitLab hosts. Uses `GET /api/v4/projects/{encoded_path}/repository/tags` via the GitLab API. Supports:

- Optional Private-Token auth (`GITLAB_TOKEN` / `--gitlab-token`).
- Self-hosted GitLab via host detection from the source URL.

### `config`

Loads `agronomist.yml` (or the path specified by `--config`). Parses:

- `categories` — maps label names to lists of repo glob patterns used to tag `UpdateEntry` rows.
- `blacklists` — repo, module, and file glob lists passed to the scanner.

Returns a `Config` dataclass consumed by the CLI.

### `report`

Builds the `Report` object and serializes it to JSON. Also writes a human-readable Markdown summary via the `markdown` module.

### `markdown`

Generates a Markdown-formatted update summary grouped by repository. Output is intended for use in PR descriptions and CI step summaries.

### `updater`

Reads each source file referenced in the report and performs in-place string replacement of `?ref=<old>` → `?ref=<new>` using the raw source string as the anchor. Writes the updated content back to disk.

---

## Key design decisions

**Regex-based source parsing.** Terraform sources are not evaluated — the scanner uses a regular expression against raw file content. This avoids a runtime Terraform dependency and works regardless of HCL formatting.

**Stateless runs.** Each invocation is independent. There is no database or local state cache. Report files written to disk are the only persistence.

**Resolver is pluggable by flag.** The `--resolver` flag selects which resolution strategy is invoked. The `auto` mode delegates per source URL to the appropriate resolver.

**Separation of report and update.** The `report` command only reads and writes a JSON file. The `update` command reads that report and modifies source files. This allows reviewing changes before applying them and enables automation pipelines where report and update happen in separate steps or separate jobs.
