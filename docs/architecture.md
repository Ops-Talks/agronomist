# Architecture

## Flow

1. Scan source files under the root directory.
2. Extract `source` references that contain `?ref=`.
3. Resolve the latest version based on the selected resolver.
4. Build a report of updates.
5. Optionally apply updates in place.

## Components

- `scanner` Walks the file tree and finds module sources. Supports blacklist filters for repos, modules, and files.
- `config` Loads category rules and blacklist settings for filtering and tagging updates.
- `git` Resolves tags using Git.
- `github` Resolves releases and tags using GitHub API.
- `gitlab` Resolves tags using GitLab API when detected.
- `report` Builds JSON report structures.
- `markdown` Generates Markdown summaries.
- `updater` Applies replacements to files.
