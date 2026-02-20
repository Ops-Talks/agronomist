# Configuration

Agronomist reads category rules from a YAML or JSON file. By default, it looks for `.agronomist.yaml` in the root directory.

## Example

### YAML Format

```yaml
categories:
  - name: aws
    repo_patterns:
      - "*/terraform-aws-*"
      - "*/opentofu-aws-*"
      - "*/tofu-aws-*"
  - name: database
    repo_patterns:
      - "*/terraform-*-mysql-*"
      - "*/opentofu-*-mysql-*"
      - "*/tofu-*-mysql-*"
      - "*/terraform-*-mariadb-*"
      - "*/opentofu-*-mariadb-*"
      - "*/tofu-*-mariadb-*"
      - "*/terraform-*-postgres-*"
      - "*/opentofu-*-postgres-*"
      - "*/tofu-*-postgres-*"
  - name: security
    repo_patterns:
      - "*/terraform-*-security-*"
      - "*/opentofu-*-security-*"
      - "*/tofu-*-security-*"
  - name: monitoring
    repo_patterns:
      - "*/terraform-*-monitoring-*"
      - "*/opentofu-*-monitoring-*"
      - "*/tofu-*-monitoring-*"

blacklist:
  repos:
    - "*/terraform-legacy-*"
    - "*/deprecated-*"
  modules:
    - "old-modules/*"
  files:
    - "**/legacy/**"
    - "**/deprecated/**"
```

### JSON Format

```json
{
  "categories": [
    {
      "name": "aws",
      "repo_patterns": [
        "*/terraform-aws-*",
        "*/opentofu-aws-*"
      ]
    },
    {
      "name": "database",
      "repo_patterns": [
        "*/terraform-*-mysql-*",
        "*/terraform-*-postgres-*"
      ]
    }
  ],
  "blacklist": {
    "repos": [
      "*/terraform-legacy-*",
      "*/deprecated-*"
    ],
    "modules": [
      "old-modules/*"
    ],
    "files": [
      "**/legacy/**",
      "**/deprecated/**"
    ]
  }
}
```

## Fields

### Categories

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `categories` | list | Yes | List of category rules |
| `name` | string | Yes | Category name (assigned to matching updates) |
| `repo_patterns` | list[string] | No | Glob patterns to match repository names/URLs |
| `module_patterns` | list[string] | No | Glob patterns to match module names |

### Blacklist

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `blacklist` | object | No | Blacklist configuration to ignore specific resources |
| `repos` | list[string] | No | Glob patterns to ignore repositories |
| `modules` | list[string] | No | Glob patterns to ignore modules |
| `files` | list[string] | No | Glob patterns to ignore files |

## Behavior

- **Pattern matching**: Uses Python `fnmatch` rules (not regex). Supports `*`, `?`, `[abc]`, `[!abc]`
- **Matching logic**: 
  - If `repo_patterns` matches the repository, category is assigned
  - If `module_patterns` matches the module name, category is assigned
  - First matching rule wins
- **Uncategorized**: Updates that don't match any rule are labeled `uncategorized`
- **Optional patterns**: If `repo_patterns` or `module_patterns` are omitted or empty, they are skipped
- **Blacklist**: Resources matching blacklist patterns are completely ignored and won't appear in reports or updates
- **File formats**: Both YAML (`.yaml`, `.yml`) and JSON (`.json`) are supported
