# Brasil Além das Urnas

Ferramenta independente para qualquer cidadão entender como o seu município participou das eleições presidenciais de 2022 e 2026: comparecimento, abstenção e votos válidos, brancos e nulos, comparados com o estado e com o Brasil.

Fonte dos dados: Portal de Dados Abertos do TSE e IBGE. Sem vínculo com órgãos públicos.

## Funcionalidades (MVP)
1. **Explore seu município**: indicadores do município, por zona eleitoral
2. **Comparativo 2022 × 2026**: evolução em pontos percentuais e comparação entre os turnos
3. **Mapa eleitoral**: estados e municípios, com filtros por indicador e região
4. **Brasil em perspectiva**: município × estado × Brasil

## Arquitetura
```
VS Code → GitHub → (execução manual das consultas) → BigQuery Sandbox
```
| Etapa | Onde |
|---|---|
| Ingestão e validação (Python) | `ingestion/` |
| Modelagem (SQL, executado manualmente no BigQuery) | `sql/` |
| Exportação das marts para Parquet | `scripts/` → `data/marts/` |
| App Streamlit (lê só Parquet, sem credencial GCP) | `app/` |
| Metodologia, validação e design | `docs/` |

O BigQuery Sandbox apaga as tabelas após 60 dias. Por isso o app lê os arquivos Parquet versionados, e o BigQuery só precisa ser recriado quando houver dado novo.

## Como rodar
```bash
python -m venv .venv
.venv\Scripts\activate            # Windows
pip install -r requirements-dev.txt

# App
streamlit run app/Home.py

# Pipeline (requer gcloud auth application-default login)
# ver sql/README.md para a ordem de execução
```

## Status
Fases 0-2 concluídas; Fase 3 (app) implementada, com aprovação visual e testes com pessoas pendentes. Ver [docs/planejamento.md](docs/planejamento.md). Plano e decisões pendentes em [docs/metodologia.md](docs/metodologia.md).
