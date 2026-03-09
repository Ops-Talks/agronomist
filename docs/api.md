# API

Agronomist can be used as a Python library for custom automation.

## Basic usage

```python
from agronomist.scanner import scan_sources
from agronomist.config import load_config
from agronomist.github import GitHubClient
from agronomist.git import GitClient
from agronomist.gitlab import GitLabClient
from agronomist.report import build_report, write_report
from agronomist.markdown import write_markdown
from agronomist.updater import apply_updates
from agronomist.models import UpdateEntry, Replacement, SourceRef

# Load configuration (includes categories and blacklist)
config = load_config(".agronomist.yaml", root=".")

# Scan sources with optional blacklist filters
sources = scan_sources(
    root="./infra",
    include=["**/*.tf", "**/*.hcl"],
    exclude=["**/.terraform/**"],
    blacklist_repos=config.blacklist.repos,
    blacklist_modules=config.blacklist.modules,
    blacklist_files=config.blacklist.files,
)

github = GitHubClient(
    base_url="https://api.github.com",
    token="...",
)
gitlab = GitLabClient(
    base_url="https://gitlab.com",
    token="...",
)
resolver = GitClient()

# Resolve and build a report using custom logic with categories
updates = []  # Collect UpdateEntry objects using resolver
report = build_report(root=".", updates=[u.to_dict() for u in updates])
```

## Common functions and classes

### Data models (`models`)

- `SourceRef` -- immutable dataclass representing a scanned module reference (file path, repo, host, ref, module).
- `Replacement` -- immutable dataclass for a single source-string substitution pair. Provides `to_dict()`.
- `UpdateEntry` -- immutable dataclass for a version-update action. Contains repo metadata, current and latest refs, files, replacements, and optional category. Provides `to_dict()`.

### Scanner (`scanner`)

- `scan_sources(root, include, exclude, ...)` -- scan files and return discovered `SourceRef` objects. Supports optional blacklist filters for repos, modules, and files.

### Configuration (`config`)

- `load_config(path, root)` -- load configuration from YAML or JSON. Returns a `Config` object containing category rules and blacklist settings.

### Resolvers

- `GitClient(timeout)` -- resolve tags via `git ls-remote`.
- `GitHubClient(base_url, token, timeout, ...)` -- resolve latest release and tags via the GitHub REST API.
- `GitLabClient(base_url, token, timeout, ...)` -- resolve latest tags via the GitLab REST API.

### Report and output

- `build_report(root, updates)` -- build the JSON-serializable report dict.
- `write_report(path, report)` -- write JSON report to disk (atomic write).
- `write_markdown(path, report)` -- write Markdown report to disk (atomic write).

### Updater

- `apply_updates(root, updates)` -- apply `UpdateEntry` replacements to files on disk. Returns a list of modified file paths.

### HTTP utilities (`http`)

- `build_session(retries, backoff_factor)` -- return a `requests.Session` with automatic retry and exponential backoff.

Refer to the source in `src/agronomist` for implementation details.
