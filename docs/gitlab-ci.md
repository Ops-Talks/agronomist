# GitLab CI

This project includes a GitLab pipeline to run Agronomist using GitLab Runners.

## Requirements
- GitLab Runner with Docker or shell executor.
- A GitHub or GitLab token stored in GitLab CI variables.

## Variables
- `GITHUB_TOKEN` Token used by Agronomist for GitHub or GitLab API calls.
- `AGRONOMIST_ROOT` Root directory to scan. Default: `.`
- `AGRONOMIST_RESOLVER` Resolver strategy: `git`, `github`, or `auto`.
- `AGRONOMIST_CONFIG` Path to configuration file. Default: `.agronomist.yaml`.

## Pipeline overview
- `report` stage generates `report.json` and `report.md` as artifacts.
- `update` stage runs in manual mode and updates files in the job workspace.

## Example pipeline

```yaml
stages:
  - report
  - update

variables:
  AGRONOMIST_ROOT: "."
  AGRONOMIST_RESOLVER: "git"
  AGRONOMIST_CONFIG: ".agronomist.yaml"

report:
  stage: report
  image: python:3.12
  script:
    - apt-get update && apt-get install -y git
    - pip install .
    - agronomist report --root "$AGRONOMIST_ROOT" --config "$AGRONOMIST_CONFIG" \
        --resolver "$AGRONOMIST_RESOLVER" --output report.json --markdown report.md
  artifacts:
    paths:
      - report.json
      - report.md

update:
  stage: update
  image: python:3.12
  when: manual
  script:
    - apt-get update && apt-get install -y git
    - pip install .
    - agronomist update --root "$AGRONOMIST_ROOT" --config "$AGRONOMIST_CONFIG" \
        --resolver "$AGRONOMIST_RESOLVER" --output report.json
  artifacts:
    paths:
      - report.json
```

For a full pipeline, see [.gitlab-ci.yml](../.gitlab-ci.yml).
