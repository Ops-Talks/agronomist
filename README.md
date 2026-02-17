# agronomist
Ferramenta alternativa ao Gruntwork Patcher para detectar e atualizar refs de modulos Terragrunt.

## O que faz no MVP
- Varre arquivos .hcl e .tf e encontra `source` com `?ref=` apontando para GitHub.
- Consulta releases/tags para sugerir uma nova versao.
- Gera relatorio JSON e opcionalmente atualiza refs in-place.
- Pode ser usado via CLI local ou GitHub Action.

## Requisitos
- Python 3.10+
- Git instalado (para resolver tags via `git ls-remote`)
- Token do GitHub (PAT) recomendado para evitar rate limit quando usar `--resolver github`

## Uso rapido (CLI)
```
poetry install
poetry run agronomist report --root . --output report.json
poetry run agronomist update --root . --output report.json
```

## Resolver de versoes
- Padrao: `git` (usa `git ls-remote --tags`).
- Opcional: `github` (usa GitHub API).
`git` funciona com GitHub, GitLab e outros servidores Git compativeis.

Exemplos:
```
poetry run agronomist report --root . --resolver git --output report.json
poetry run agronomist report --root . --resolver github --output report.json
```

## Lint e testes
```
poetry run ruff check .
poetry run ruff format .
poetry run black .
poetry run pytest
```

## Pre-commit
```
poetry run pre-commit install
poetry run pre-commit run --all-files
```

## GitHub Action
Exemplo em [examples/workflows/agronomist.yml](examples/workflows/agronomist.yml).

## Categorias (config)
Crie um arquivo `.agronomist.yaml` (ou informe `--config`) para classificar dependencias:
```
categories:
	- name: aws
		repo_patterns:
			- "*/terraform-aws-*"
	- name: mysql
		repo_patterns:
			- "*/terraform-*-mysql-*"
	- name: postgres
		repo_patterns:
			- "*/terraform-*-postgres-*"
```
O campo `category` sera incluido no relatorio e exibido no stdout.

## Design
Veja o design do MVP em [docs/design.md](docs/design.md).
