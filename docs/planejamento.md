# Planejamento

Arquivo criado em 25/10/2026: o repositório não tinha um documento de planejamento, só as referências "tarefa 0.5", "2.4", "2.5" e "4.3" em `docs/`.

## Status das fases

| Fase | Status |
|---|---|
| 0 e 1: estrutura e ingestão TSE/IBGE | Concluídas (commit `c590ce2`) |
| 2: modelagem SQL e exportação das marts | **Concluída em 25/10/2026** |
| 3 em diante | Não iniciadas |

## Fase 2: o que está pronto
- Staging (2 tabelas), intermediate (2) e marts (5) em `sql/`, executados no BigQuery Sandbox por `python -m scripts.modelagem`.
- 11 testes SQL em `sql/tests/`: todos com 0 falhas em 25/10/2026. Evidência em `docs/validacao/fase2_execucao.json`.
- Exportação para `data/marts/*.parquet` + `manifest.json` (com hash) por `python -m scripts.export_marts`. Linhas: zona 18.858, município 17.259, UF/Brasil 87, comparativo 22.282, benchmark 16.711.
- Testes locais (`tests/test_modelagem.py`, DuckDB, sem GCP): 12 passam com os de ingestão.

## Problemas encontrados e resolvidos
1. `sql/tests/06_totais_brasil.sql` usava HAVING sem GROUP BY e falhava no BigQuery. Reescrito com subconsulta.
2. Os Parquets saíam com a metadata de tipo `dbdate` (db_dtypes) e não abriam com pandas/pyarrow sem essa lib, o que quebraria o app Streamlit. `export_marts.py` agora converte as datas para `datetime64`.

## Conferência com o TSE (2.4 e 2.5)
- Feita em 25/10/2026 contra o painel oficial (Brasil, 3 recortes). Divergência de comparecimento menor que 0,03%, causa confirmada: o painel usa outro dataset do TSE (`perfil_comparecimento_abstencao`), que reproduzimos exatamente. Ver `docs/validacao.md`.
- Decisões de metodologia fechadas: "praticamente igual" = menos de 0,5 p.p.; origem de Boa Esperança do Norte = Sorriso e Nova Ubiratã; fonte de resultados mantida.
- Ainda não conferidos: uma UF e um município contra o painel (linhas em branco de `docs/validacao.md`); recomendado antes de publicar o app.
- Aviso: as tabelas do Sandbox expiram em 60 dias (por volta de 24/12/2026); o app depende só dos Parquets versionados.
