# Resolvers

Agronomist supports three resolver strategies controlled by `--resolver`.

## git (default)
Uses `git ls-remote --tags` to list tags and select the latest tag.

## github
Uses the GitHub API to resolve the latest release or tag. Provide a token with `--token` or `GITHUB_TOKEN`.

## auto
Chooses the resolver based on repository host:
- GitLab URLs use the GitLab API.
- GitHub URLs use the GitHub API.
- Other URLs fall back to Git.

## GitHub base URL
Use `--github-base-url` for GitHub Enterprise or custom API endpoints.
