# Development

## Setup

```sh
poetry install
```

## Task runner (taskipy)

```sh
poetry run task lint
poetry run task format
poetry run task test
poetry run task check
poetry run task pre-commit
```

## Pre-commit

```sh
poetry run task pre-commit-install
poetry run task pre-commit-run
```

## Tests

```sh
poetry run pytest
```

## Linting and formatting

```sh
poetry run ruff check .
poetry run ruff format .
poetry run black .
```
