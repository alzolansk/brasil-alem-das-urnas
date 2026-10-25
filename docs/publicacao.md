# Publicação e 2º turno de 2026 (Fase 4)

## 1. Quando o TSE publicar o 2º turno (4.1 e 4.2)
```bash
python -m scripts.segundo_turno            # 0 = publicado e completo; 1 = ainda não
python -m scripts.segundo_turno --ativar   # troca o zip local de 2026 e liga o turno 2 em sources.yaml
python -m scripts.rebuild                  # ingestão → raw → SQL + testes → data/marts/*.parquet
pytest -q && ruff check .
git add data/marts ingestion/sources.yaml docs/validacao && git commit -m "Dados: 2º turno 2026"
git push                                   # o Streamlit Cloud republica sozinho
```
- O verificador baixa o zip de 2026 (≈2,5 MB) numa pasta temporária e só aceita o 2º turno se tiver os 5.571 municípios e passar nas validações de consistência. Enquanto o TSE estiver totalizando, o arquivo pode não mudar por alguns dias.
- O app não precisa de alteração: os selos, o bloco "1º × 2º turno" do Comparativo, a tela Explore, o Mapa e o Brasil em perspectiva passam a mostrar o 2º turno quando ele existir nas marts (coberto por `tests/test_app.py` com dados simulados).
- `rebuild` precisa de `gcloud auth application-default login`. Se as tabelas do Sandbox tiverem expirado (60 dias), ele as recria.
- Depois: refazer a conferência com o painel do TSE (4.3) e registrar em `docs/validacao.md`.

## 2. Deploy no Streamlit Community Cloud (4.4)
1. Entrar em https://share.streamlit.io com a conta do GitHub dona do repositório.
2. **Create app** → repositório `alzolansk/brasil-alem-das-urnas`, branch `main`, arquivo principal `app/Home.py`.
3. Em **Advanced settings**, escolher Python 3.12. Não há segredos: o app lê só `data/marts/*.parquet` e `data/geo/`.
4. As dependências vêm de `requirements.txt` (só as do app) e o tema de `.streamlit/config.toml`.
5. Conferir a URL publicada no celular e no computador e anotar o endereço no `README.md`.

## 3. Integração contínua (4.5)
`.github/workflows/ci.yml` roda `ruff check .` e `pytest -q` a cada push e pull request. Os testes de ingestão dependem dos zips do TSE em `data/raw/` (fora do git) e são pulados no CI.
