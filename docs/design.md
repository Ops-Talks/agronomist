# Agronomist: design do MVP

## Objetivo
Desenvolver uma ferramenta que detecta e atualiza referencias de modulos Terragrunt, mantendo o IaC em dia, usando:
- CLI local para reportar e atualizar referencias de modulos GitHub.
- GitHub Action para rodar o CLI e permitir abertura de PR via workflow.
- Detecao de breaking changes somente por aviso (sem patches).

## Escopo do MVP
- Scan de arquivos .hcl e .tf em um diretorio raiz.
- Descoberta de dependencias Git em `source` com `?ref=`.
- Resolucao de nova versao via Git:
  - Usa `git ls-remote --tags` como fonte principal.
  - Opcionalmente usa GitHub API quando configurado.
- Gera relatorio JSON com dependencias e sugestoes de update.
- Opcionalmente aplica updates in-place (substitui `ref=`).

## Nao inclui no MVP
- Patches para breaking changes.
- Validacao de planos ou aplicacao de Terraform/Tofu.
- Registry do Terraform.
- Suporte amplo a VCS alem de Git.

## Componentes
1) Scanner
- Percorre arquivos, aplica include/exclude via glob.
- Extrai `source` com regex simples.
- Normaliza repositorios GitHub e ref atual.

1b) Categorizer
- Carrega regras de categorias via YAML/JSON.
- Classifica dependencias por padroes de repo ou modulo.

2) Resolver
- Consulta GitHub API usando token.
- Determina ultima versao disponivel (release/tag).
- Compara versoes e marca candidato.

3) Updater
- Substitui o `source` antigo pelo novo dentro do arquivo.
- Mantem o restante do arquivo intacto.

4) Reporter
- Exporta JSON com dependencias, versoes e sugestoes.
- Inclui lista de arquivos afetados.
- Adiciona `category` quando configurado.

## Formato do relatorio (JSON)
```
{
  "generated_at": "2026-02-17T12:34:56Z",
  "root": ".",
  "updates": [
    {
      "repo": "gruntwork-io/terraform-aws-vpc",
      "repo_host": "github.com",
      "repo_url": "https://github.com/gruntwork-io/terraform-aws-vpc",
      "module": "modules/vpc",
      "current_ref": "v1.2.0",
      "latest_ref": "v1.4.1",
      "strategy": "latest",
      "category": "aws",
      "files": ["infrastructure-live/prod/vpc/terragrunt.hcl"]
    }
  ]
}
```

## CLI
- `agronomist report --root . --output report.json`
- `agronomist update --root . --output report.json`

Flags:
- `--include`, `--exclude` (glob)
- `--github-base-url` (default: https://api.github.com)
- `--token` (PAT ou via env GITHUB_TOKEN)

## GitHub Action
- Composite action que instala o pacote e roda o CLI.
- Abertura de PR fica no workflow, usando `peter-evans/create-pull-request`.

## Riscos e limitacoes
- Regex pode perder formatos HCL mais complexos.
- Comparacao de versoes usa string simples (sem semver avancado).
- Sem detecao automatica de breaking changes.

## Proximos passos
- Parser HCL real (python-hcl2) para maior robustez.
  - Substituir regex por parser HCL e mapear `source` em estruturas reais.
  - Garantir suporte a `locals`, `include`, `dependency` e multi-line strings.
  - Adicionar testes com fixtures HCL variados.
- Suporte a Terraform Registry.
  - Resolver versoes via API do Registry e mapear namespace/modulo/provider.
  - Permitir configurar prioridades: Registry vs GitHub.
  - Cache local para reduzir chamadas de rede.
- Regras de agrupamento por dependencia para PRs.
  - Agrupar por repo/modulo/categoria e gerar um PR por grupo.
  - Adicionar regras de tamanho (ex.: max N updates por PR).
  - Ajustar o workflow para criar branches distintas.
- Estrategias `next-safe` com changelogs gerados.
  - Implementar comparacao semver real e salto de versoes com zero changes.
  - Gerar changelog consolidado no relatorio/PR.
  - Permitir filtros (seguranca/bugfix/feature).
