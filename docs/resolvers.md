# Resolvers

A resolver is the strategy Agronomist uses to determine the latest available version for a module source. Select one with the `--resolver` flag.

## Comparison

| Resolver | Works with | Authentication | Internet required |
|----------|-----------|----------------|------------------|
| `git` (default) | Any Git host | None | Yes, via Git protocol |
| `github` | GitHub only | Optional, recommended | Yes |
| `auto` | GitHub, GitLab, other | Optional per host | Yes |

---

## git (default)

Runs `git ls-remote --tags` against the module's remote URL and selects the latest tag based on semantic versioning sort order.

**When to use it:**

- Your modules are hosted on GitHub, GitLab, Gitea, Bitbucket, or any other Git-compatible server.
- You do not have or do not want to configure API tokens.
- You are working in an environment where Git is installed and can reach the remote hosts.

**Limitations:**

- Requires Git installed and available on `PATH`.
- Can be slower than API-based resolvers for large repositories with many tags.
- Does not use the GitHub or GitLab "latest release" concept — it always selects the most recent tag by version sort.

**Example:**

```sh
agronomist report --root ./infrastructure --resolver git
```

---

## github

Uses the GitHub REST API to fetch tags and releases for the module repository.

**When to use it:**

- All your module sources are hosted on GitHub.com.
- You want to resolve against published GitHub Releases rather than raw tags.
- You hit `git ls-remote` rate limits or firewall restrictions.

**Authentication:**

Provide a GitHub Personal Access Token (PAT) with `public_repo` scope (or `repo` for private repositories):

```sh
export GITHUB_TOKEN="ghp_..."
agronomist report --root ./infrastructure --resolver github
```

Or pass it directly:

```sh
agronomist report --root ./infrastructure --resolver github --github-token ghp_...
```

**GitHub Enterprise:**

For GitHub Enterprise Server, override the API base URL:

```sh
agronomist report \
  --resolver github \
  --github-base-url https://github.company.com/api/v3
```

**Limitations:**

- Only works with GitHub.com and GitHub Enterprise. GitLab, Gitea, and other hosts are not supported.
- Without a token, GitHub's unauthenticated API rate limit (60 requests/hour) is quickly reached.

---

## auto

Automatically selects the most appropriate resolver based on the hostname in each module's source URL.

- GitLab hostnames use the GitLab API.
- GitHub hostnames use the GitHub API.
- All other hostnames fall back to the `git` resolver.

**When to use it:**

- Your infrastructure uses modules from a mix of GitHub and GitLab repositories.
- You want optimal resolution per host without manual `--resolver` switching.

**Authentication:**

Configure tokens for each platform as needed:

```sh
export GITHUB_TOKEN="ghp_..."
export GITLAB_TOKEN="glpat-..."
agronomist report --root ./infrastructure --resolver auto
```

**Self-hosted GitLab:**

The GitLab resolver detects GitLab hosts by inspecting the hostname in each module's `source` URL. For self-hosted GitLab instances, set `--gitlab-base-url` to your instance URL (e.g., `https://gitlab.company.com`). The resolver also auto-detects the host from each module's source URL. Tokens are passed via `--gitlab-token` or the `GITLAB_TOKEN` environment variable.

**Limitations:**

- Requires tokens for private repositories on each platform.
- Falls back to the `git` resolver if API access fails for a host.

---

## Choosing a resolver

Use `git` as the default in most environments. Switch to `github` or `auto` when you need release-aware resolution or are scanning repositories across multiple Git hosting platforms where API tokens are already available.

See [CLI Reference](cli.md#resolution-strategies) for the full flag reference.

