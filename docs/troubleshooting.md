# Troubleshooting

## Git is not installed

Agronomist uses `git ls-remote`. Install Git and ensure it is on your PATH.

## GitHub/GitLab token errors

- `401` means the token is invalid or expired.
- `403` means the token lacks permissions or rate limit was hit.
- For GitHub, ensure the token has `public_repo` or `repo` scope.
- For GitLab, ensure the token has `read_api` scope.

**Tip**: Use `--validate-token` to check token validity before processing.

## No updates found

- Ensure your sources use `?ref=` in the `source` string.
- Confirm the repository has tags.
- Check if the repository is blacklisted in `.agronomist.yaml`.

## Pre-commit Python version errors

If pre-commit cannot find `python3.10`, install it or set:

```yaml
default_language_version:
  python: python3
```

## GitHub API base URL issues

For GitHub Enterprise, set `--github-base-url` to your API endpoint (e.g., `https://github.company.com/api/v3`).

## GitLab API issues

For self-hosted GitLab instances, use `--gitlab-token` and ensure the base URL is correct (default: `https://gitlab.com`).

## Resolver issues

- **git resolver**: Requires Git installed and network access to repositories.
- **github/gitlab resolvers**: Require valid tokens and API access.
- **auto resolver**: Falls back to git if API resolvers fail. Check logs for details.