# Architecture

This document describes the internal design of Agronomist for contributors and developers. See [Development](development.md) for setup instructions.

## Overview

Agronomist is a command-line tool that inspects Terraform and OpenTofu source files, resolves the latest version for each external module, produces a structured report, and optionally applies updates in place.

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

### `cli`

The command-line entry point. Defines the `report` and `update` sub-commands, registers all shared arguments via `_add_common_args()`, and orchestrates the full pipeline: scan, resolve (with parallel workers), categorize, report, and optionally update. The `main()` function delegates to smaller helpers such as `_create_clients()`, `_validate_tokens()`, `_collect_updates()`, and `_print_category_summary()`.

### `scanner`

Entry point for file discovery. Implements `scan_sources()`, which walks a root directory recursively, parses every file for `source = "..."` lines, and extracts structured `SourceRef` objects for any source that contains a `?ref=` segment.

Filtering is applied during the walk:

- Files matching `blacklist_files` patterns are skipped.
- Repos matching `blacklist_repos` are excluded from the output.
- Modules matching `blacklist_modules` are excluded from the output.

The `_parse_git_source()` helper uses a compiled regex to decompose sources of the form `git::https://host/org/repo.git//module/path?ref=vX.Y.Z` into structured fields (`repo_host`, `repo`, `module`, `ref`).

### `models`

Defines the core dataclasses:

- `SourceRef` -- a single scanned module reference (file path, raw source string, repo, repo_url, repo_host, ref, module). Frozen and immutable.
- `Replacement` -- a single source-string substitution pair (`old` and `new`). Provides `to_dict()` returning `{"from": ..., "to": ...}` for JSON serialization.
- `UpdateEntry` -- a standalone frozen dataclass representing a version-update action. Contains repo metadata, current and latest refs, affected files, replacement pairs, and an optional category. Provides `to_dict()` for JSON serialization.

### `git`

Implements the `git` resolver. Calls `git ls-remote --tags --sort=-v:refname <url>`, parses the output for tag refs, skips `^{}` dereference lines, and returns the first matching tag name.

### `github`

Implements the `github` resolver. Uses two GitHub REST API endpoints:

- `GET /repos/{owner}/{repo}/releases/latest` -- fetches the latest published release tag.
- `GET /repos/{owner}/{repo}/tags` -- falls back to the most recent tag when no release exists.

Supports optional Bearer token authentication (`GITHUB_TOKEN` / `--github-token`) and custom base URL for GitHub Enterprise (`--github-base-url`).

### `gitlab`

Implements the `auto`-path for GitLab hosts. Uses `GET /api/v4/projects/{encoded_path}/repository/tags` via the GitLab API. Supports:

- Optional Private-Token authentication (`GITLAB_TOKEN` / `--gitlab-token`).
- Self-hosted GitLab via host detection from the source URL.

### `config`

Loads `.agronomist.yaml` (or the path specified by `--config`). Parses:

- `categories` -- maps label names to lists of repo and module glob patterns used to tag updates.
- `blacklist` -- repo, module, and file glob lists passed to the scanner for filtering.

Returns a `Config` dataclass consumed by the CLI.

### `http`

Shared HTTP utilities. Provides `build_session()`, which returns a `requests.Session` configured with automatic retry and exponential backoff for transient HTTP errors (429, 500, 502, 503, 504). Used by both `GitHubClient` and `GitLabClient`.

### `report`

Builds a JSON-serializable report dict containing a UTC timestamp, the scan root, and the list of update dicts. Writes the result to a JSON file using atomic writes.

### `markdown`

Generates a Markdown-formatted update summary grouped by repository and module. Output is intended for use in PR descriptions and CI step summaries. Writes the result using atomic writes.

### `updater`

Accepts a list of `UpdateEntry` objects and applies string replacements to the affected files on disk. Groups replacements by file, reads each file once, applies all substitutions, and writes back only when content actually changed. Includes path traversal protection via `_is_safe_path()`. All writes use the shared `atomic_write()` helper.

### `fileutil`

Shared file-writing utilities. Provides `atomic_write(path, content, newline=None)`, which writes to a temporary file in the same directory and then atomically renames it to the target path. Prevents file corruption if the process is interrupted mid-write.

### `exceptions`

Defines the custom exception hierarchy:

- `AgronomistError` -- base exception for all Agronomist errors.
- `NetworkError` -- raised when an HTTP request fails after retries.
- `AuthenticationError` -- raised when an API token is invalid or lacks permissions.
- `ResolverError` -- raised when a version resolver cannot determine the latest ref.
- `ConfigError` -- raised when configuration is missing or malformed.

---

## Key design decisions

**Regex-based source parsing.** Terraform sources are not evaluated -- the scanner uses a regular expression against raw file content. This avoids a runtime Terraform dependency and works regardless of HCL formatting.

**Stateless runs.** Each invocation is independent. There is no database or local state cache. Report files written to disk are the only persistence.

**Resolver is pluggable by flag.** The `--resolver` flag selects which resolution strategy is invoked. The `auto` mode delegates per source URL to the appropriate resolver.

**Report and update share a pipeline.** Both the `report` and `update` commands run the same scan-resolve-categorize pipeline. The `report` command writes a JSON file (and optional Markdown). The `update` command additionally applies file modifications. This allows reviewing changes with `report` before applying them with `update`, and enables CI/CD pipelines that separate the two steps into different jobs.
