# Configuration

Agronomist reads category rules from a YAML or JSON file. By default, it looks for `.agronomist.yaml` in the root directory.

## Example

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
```

## Fields

- `categories` List of category rules.
- `name` Category name.
- `repo_patterns` Match repositories using glob patterns.
- `module_patterns` Match module names using glob patterns.

## Notes

- Pattern matching uses Python `fnmatch` rules.
- If no rule matches, updates are labeled `uncategorized`.
