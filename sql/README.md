# SQL — execução manual no BigQuery Sandbox

Projeto: `brasil-alem-das-urnas-2026` · Datasets: `raw`, `staging`, `marts` (região `US`; ver docs/planejamento.md)

## Regras
- O Sandbox não aceita DML (INSERT/UPDATE/DELETE/MERGE). Todo arquivo usa `CREATE OR REPLACE TABLE ... AS SELECT`.
- As tabelas expiram em 60 dias. Para recriar: carregar o `raw` com o Python e rodar os arquivos de novo, na ordem.
- Um arquivo = uma tabela, com o nome da tabela no arquivo.

## Ordem de execução
1. `01_staging_*.sql`
2. `02_int_*.sql`
3. `03_mart_*.sql`
4. `tests/*.sql`: **cada consulta deve retornar 0 linhas**. Se retornar alguma, anote em `docs/validacao.md` e investigue antes de exportar.
5. `python -m scripts.export_marts` → `data/marts/*.parquet` → commit

Atalho: `python -m scripts.rebuild` faz a carga, os SQLs, os testes e a exportação em sequência.
