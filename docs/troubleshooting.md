# Troubleshooting

## Git is not installed

Agronomist uses `git ls-remote`. Install Git and ensure it is on your PATH.

## GitHub token errors

- `401` means the token is invalid or expired.
- `403` means the token lacks permissions or rate limit was hit.

## No updates found

- Ensure your sources use `?ref=` in the `source` string.
- Confirm the repository has tags.

## Pre-commit Python version errors

If pre-commit cannot find `python3.10`, install it or set:

```yaml
default_language_version:
  python: python3
```

## GitHub API base URL issues

For GitHub Enterprise, set `--github-base-url` to your API endpoint.
