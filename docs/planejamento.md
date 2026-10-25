# Planejamento

Arquivo criado em 25/10/2026: o repositório não tinha um documento de planejamento, só as referências "tarefa 0.5", "2.4", "2.5" e "4.3" em `docs/`.

## Status das fases

| Fase | Status |
|---|---|
| 0 e 1: estrutura e ingestão TSE/IBGE | Concluídas (commit `c590ce2`) |
| 2: modelagem SQL e exportação das marts | **Concluída em 25/10/2026** |
| 3: app Streamlit | **Implementada em 25/10/2026; aprovação visual (3.0), textos (3.7/3.8) e testes com pessoas (3.9) pendentes** |
| 4 em diante | Não iniciadas |

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

## Fase 3: app Streamlit (25/10/2026)
| # | Status |
|---|---|
| 3.0 | Feito com dados reais (sem selo "Dados ilustrativos"). **Aprovação visual pendente**: não consegui abrir o app no navegador nesta sessão (extensão do Chrome indisponível), então não há prints em `docs/design/aceite/` e a fidelidade ao protótipo 2 e o layout a 375px não foram vistos. Rodar `python -m streamlit run app/Home.py` e conferir. |
| 3.1 | Feito: faixa, cabeçalho com logo e busca, abas (menu "☰" abaixo de 768px), breadcrumb, rodapé, alto contraste. |
| 3.2–3.5 | Feitas: Explore, Comparativo, Mapa (grade de UFs clicável, municípios por UF, lista ordenada), Brasil em perspectiva. Estados de carregamento (esqueleto), sem dado ("Aguardando apuração"), município não encontrado (com sugestões) e erro de leitura. Município mantido entre telas e na URL (`?m=`). |
| 3.6 | Feito: `app/lib/narrativa.py`, modelos fixos, testados. Limite de 0,5 p.p. |
| 3.7 | Pendente (humano): aprovar os modelos de frase. |
| 3.8 | Rascunho: Metodologia (lê `docs/metodologia.md`), Dicionário, Sobre os dados, Acessibilidade, Termos, Contato. Texto final e canal de contato pendentes. |
| 3.9 | Pendente (humano). |

Decisões aplicadas: D4 (comparativo fixo 2022→2026), D5 (azul ▲ / laranja ▼), D7 (alto contraste), D8 (sem botões Consultar/Atualizar).

Testes: `tests/test_app.py` (AppTest, sem GCP) abre as 10 telas, cobre município inexistente, busca sem acento, 2º turno 2026 aguardando, município de uma zona, mapa e narrativa. Total: 37 passam; ruff limpo.

### Problemas e pontos de atenção
1. Streamlit 1.58: `use_container_width` está obsoleto; usei `width="stretch"` e subi o mínimo para `streamlit>=1.50`. `unidecode` não estava instalado localmente.
2. As páginas ficam em `app/telas/` (não `pages/`) porque o app usa `st.navigation`; o registro está em `app/navegacao.py`.
3. Boa Esperança do Norte/MT não tem polígono: o mapa avisa e o município aparece só na lista ordenada.
4. Troca de página por `st.page_link` mantém o município pela sessão; o link compartilhável usa `?m=` (código IBGE). Abrir uma URL com `?m=` numa sessão nova funciona; não testado no navegador.
5. Ainda sem testar no celular e sem checar o contraste 4,5:1 nos dois temas.
6. Não avancei para a Fase 4.
