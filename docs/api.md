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

# Load configuration (includes categories and blacklist)
config = load_config(".agronomist.yaml", root=".")

# Scan sources with optional blacklist filters
sources = scan_sources(
    root="./infra",
    include=[".tf"],
    exclude=[".terraform/"],
    blacklist_repos=config.blacklist.repos,
    blacklist_modules=config.blacklist.modules,
    blacklist_files=config.blacklist.files,
)

github = GitHubClient(token="...")
gitlab = GitLabClient(base_url="https://gitlab.com", token="...")
resolver = GitClient()

# Resolve and build a report using custom logic with categories
updates = []  # Collect updates using resolver
report = build_report(root=".", updates=updates)
```

## Common functions and classes

- `scan_sources` Scan files and return discovered sources. Supports optional blacklist filters for repos, modules, and files.
- `load_config` Load configuration from YAML or JSON. Returns a `Config` object containing category rules and blacklist settings.
- `GitHubClient` Resolve latest release and tags.
- `GitClient` Resolve tags via `git ls-remote`.
- `build_report` Build the report structure.
- `write_report` Write JSON report to disk.
- `write_markdown` Write Markdown report to disk.
- `apply_updates` Apply updates to files.

Refer to the source in `src/agronomist` for implementation details.
