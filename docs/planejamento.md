# Planejamento

Arquivo criado em 25/10/2026: o repositório não tinha um documento de planejamento, só as referências "tarefa 0.5", "2.4", "2.5" e "4.3" em `docs/`.

## Status das fases

| Fase | Status |
|---|---|
| 0 e 1: estrutura e ingestão TSE/IBGE | Concluídas (commit `c590ce2`) |
| 2: modelagem SQL e exportação das marts | **Concluída em 25/10/2026** |
| 3: app Streamlit | **Implementada; redesenho de fidelidade ao protótipo feito em 25/10/2026. Pendentes: prints e aprovação visual (3.0), textos (3.7/3.8) e testes com pessoas (3.9)** |
| 4: 2º turno 2026 e publicação | **Preparada em 25/10/2026**: 2º turno entra com 2 comandos, CI ativo. Pendentes (humano): dados do TSE, conferência, deploy e revisão final |

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
| 3.0 | 1ª versão reprovada pelo usuário (distante do protótipo). Refeita segundo `docs/design/especificacao-fidelidade-prototipo.md` e conferida contra os 4 artboards do canvas de Design. Prints feitos em 25/10/2026 em `docs/design/aceite/` (ver o README da pasta, com os checklists 9.2, 11.4 e 12.9). **Pendente (humano):** aprovação final. |
| 3.1 | Feito: faixa, cabeçalho com logo e busca, abas (menu "☰" abaixo de 768px), breadcrumb, rodapé, alto contraste. |
| 3.2–3.5 | Feitas: Explore, Comparativo, Mapa (grade de UFs clicável, municípios por UF, lista ordenada), Brasil em perspectiva. Estados de carregamento (esqueleto), sem dado ("Aguardando apuração"), município não encontrado (com sugestões) e erro de leitura. Município mantido entre telas e na URL (`?m=`). |
| 3.6 | Feito: `app/lib/narrativa.py`, modelos fixos, testados. Limite de 0,5 p.p. |
| 3.7 | Pendente (humano): aprovar os modelos de frase. |
| 3.8 | Rascunho: Metodologia (lê `docs/metodologia.md`), Dicionário, Sobre os dados, Acessibilidade, Termos, Contato. Texto final e canal de contato pendentes. |
| 3.9 | Pendente (humano). |

Decisões aplicadas: D4 (comparativo fixo 2022→2026), D5 (azul ▲ / laranja ▼), D7 (alto contraste), D8 (sem botões Consultar/Atualizar).

Testes: `tests/test_app.py` (AppTest, sem GCP) abre as 10 telas, cobre município inexistente, busca sem acento, 2º turno 2026 aguardando (Explore e Brasil), município de uma zona, mapa, app aberto sem caminho, grade de UFs (27 estados, esmaecimento por região), eixo de categorias da tendência, `fmt.mil`/`milhar_curto` e as frases novas (alta, queda e igual). Total: 56 passam; ruff limpo.

### Redesenho de fidelidade (25/10/2026)
Implementado conforme a especificação: tokens novos, Inter/Raleway pelo tema, logo e favicon novos, barra utilitária, faixa 3:1:3, busca em pílula, abas sublinhadas, trilha com o município, H1 + abertura + linha de contexto, filtros em painel, manchetes com grifo, heróis com Leitura rápida ao lado, bloco de votos (brancos em amarelo), tabela de zonas em cartão com CSV, barras pareadas por turno, mapa em 3 colunas com 5 faixas e região esmaecendo, ranking, cartões de escopo, "Indicador a indicador" em HTML, tendência corrigida (eixo de categorias), rodapé único, animações A1–A10 só no 1º carregamento e desligadas por `prefers-reduced-motion` e no alto contraste. A tela Brasil ganhou o filtro de eleição.

Contraste conferido por cálculo (WCAG): todos os pares da seção 8 passam (menor: branco sobre `#2F6BBE`, 5,3:1; borda de campo `#888F99`, 3,3:1).

### Problemas e pontos de atenção
1. Streamlit 1.58: `use_container_width` está obsoleto; usei `width="stretch"` e subi o mínimo para `streamlit>=1.50`. `unidecode` não estava instalado localmente.
2. As páginas ficam em `app/telas/` (não `pages/`) porque o app usa `st.navigation`; o registro está em `app/navegacao.py`.
3. Boa Esperança do Norte/MT não tem polígono: o mapa avisa e o município aparece só na lista ordenada.
4. Troca de página por `st.page_link` mantém o município pela sessão; o link compartilhável usa `?m=` (código IBGE). Abrir uma URL com `?m=` numa sessão nova funciona; não testado no navegador.
5. Ainda sem teste visual no navegador (a extensão do Chrome não respondeu; os prints ficaram com o usuário). Os seletores CSS de Streamlit 1.58 foram conferidos no código do front (`data-stale`, `stPageLink-NavLink`, estrutura do rádio), não no DOM renderizado.
6. O `st.page_link` não expõe `aria-current`: a aba ativa é marcada por CSS gerado com a chave do contêiner (`.st-key-aba_<tela>`).
7. Quadrados dos estados: em vez de marcadores de 54px (e `size=40` no celular), uso retângulos em coordenadas do gráfico, que encolhem com a largura da tela; o Python não sabe a largura do aparelho.
8. Links HTML ("Início", logo, "Ver … em perspectiva") recarregam a página; o município e o alto contraste seguem pela URL (`?m=`, `&c=1`). As abas e o rodapé usam `st.page_link` e mantêm a sessão.
9. A busca também aceita nome ou sigla de estado (lista os municípios dele), já que o placeholder do protótipo é "Buscar município ou estado".
10. A fonte do Google Fonts carregada é o subconjunto latino; símbolos como ▲ ▼ − › usam a fonte de reserva do sistema.
11. Fase 4: ver abaixo.

## Fase 4: 2º turno 2026 e publicação

Status em 25/10/2026: preparada, aguardando o TSE e o deploy.
| # | Status | Entrega |
|---|---|---|
| 4.1 | 🤖 automatizado / 🧑 rodar | `python -m scripts.segundo_turno` baixa o zip de 2026 numa pasta temporária e diz se o 2º turno de Presidente já está lá (exige 5.571 municípios e consistência). Com `--ativar`, troca o zip local e liga o turno 2 em `sources.yaml`. **Checado em 25/10/2026 ~15h: ainda não publicado** (arquivo do TSE de 24/10). |
| 4.2 | 🤖 pronto / 🧑 executar | `python -m scripts.rebuild` = ingestão → `raw` → SQL + 11 testes → Parquet (para em qualquer falha antes de trocar os arquivos). O pipeline agora acusa erro se `sources.yaml` pede um turno que o arquivo não tem e avisa se o arquivo já tem um turno não ativado. SQL e app já tratavam o 2º turno sem mudança: comprovado por testes com 2º turno simulado (DuckDB e AppTest em Explore, Comparativo, Mapa e Brasil). |
| 4.3 | 🧑 pendente | Repetir a conferência com o painel do TSE após a carga (e preencher a UF e o município em branco de `docs/validacao.md`). |
| 4.4 | 🧑 pendente | Passo a passo em `docs/publicacao.md` (Streamlit Community Cloud, `app/Home.py`, Python 3.12, sem segredos). |
| 4.5 | ✅ | `.github/workflows/ci.yml`: ruff + pytest em push/PR. Testes de ingestão são pulados quando `data/raw/` não existe (CI). |
| 4.6 | 🟡 parcial | Capturas headless (Playwright + Chrome) a 1280 e 390 px: sem rolagem lateral. Revisão com pessoas (3.9) segue pendente. |
| 4.7 | 🟡 parcial | O selo "Dados ilustrativos" já não existe no app. Textos que diziam "2º turno em 25/10" e "1º turno de 2026" agora dependem dos dados (e da data: a partir de 26/10 o selo diz "2º turno em totalização"). Revisão de neutralidade, licença e texto final das páginas do rodapé: humana. |

### Intervenções humanas necessárias
1. Rodar `python -m scripts.segundo_turno` nos próximos dias; quando der "PUBLICADO", `--ativar` + `python -m scripts.rebuild` (requer `gcloud auth application-default login`) + commit/push.
2. Conferir o 2º turno contra o painel do TSE (4.3) e registrar em `docs/validacao.md`.
3. Criar o app no Streamlit Community Cloud (4.4) e anotar a URL no README.
4. Revisão final de conteúdo e design (4.6/4.7), aprovação dos modelos de frase (3.7) e testes com pessoas (3.9).

### Problemas encontrados
- O 2º turno de 2026 ainda não está no portal (esperado: eleição hoje). Nada foi carregado; as marts continuam só com o 1º turno de 2026.
- A extensão Claude in Chrome não respondeu ("No group with id"); as capturas foram feitas com Playwright usando o Chrome instalado.
- O CI não tem os zips do TSE (fora do git), então os 7 testes de ingestão só rodam localmente.
- Saída dos scripts no terminal Git Bash do Windows mostra acentos trocados (codificação do console); o PowerShell e o CI não têm o problema.
- Havia alterações não commitadas da Fase 3 (mapa de UFs pela malha do IBGE, `data/geo/malha_UF.geojson`): testes passam e foram commitadas à parte.

## Loader e "Sua cidade em 100 eleitores" (25/10/2026)
Seções 11 e 12 da especificação.
- **Loader (retomada do handoff):** componente leve em `app/lib/loader.py` e CSS em `app/assets/loader.css`, injetados pelo Home antes de importar pandas/Plotly. Tela cheia somente no primeiro acesso da sessão; oculta imediatamente quando o rodapé chega, sem fade sobre uma página já pronta. A exibição espera 150 ms para evitar reaparecer por um quadro na primeira navegação. No Mapa, o compacto cobre a área do gráfico até o SVG do Plotly desta execução existir, tanto em Estados como em Municípios. Lista ordenada e UF sem dados não mostram esse loader.
- **Troca de abas:** sem loader de tela cheia; conteúdo novo entra pela direita ou esquerda conforme a ordem das abas, em 420 ms. Reexecuções na mesma tela não recebem a transição; alto contraste e movimento reduzido a desativam.
- **Verificação desta retomada:** 85 testes passam e Ruff limpo. Chrome local com Playwright confirmou entrada nos dois sentidos, topo sem deslocamento, loader de Municípios até o desenho do gráfico e ausência da camada inicial nas trocas. Com servidor reiniciado, camada visível de ~1,8 a ~2,9 s; com servidor aquecido e página pronta, camada oculta sem fade. As capturas antigas do loader são referências do componente, não prova desse ciclo de carregamento.
- **Limitação do primeiro acesso:** antes de o Streamlit montar HTML/CSS, o loader Python ainda não existe no navegador; nesse intervalo podem aparecer widgets sem o estilo personalizado. O experimento com `st.html` foi revertido porque também esperava a montagem e não aplicava o CSS no ensaio. Não foi alterado o frontend do Streamlit para cobrir esse intervalo.
- **100 eleitores:** `data.pontos_100` (maiores restos), `data.contagens_100`, `narrativa.resumo_100`, `ui.bloco_100`; bloco em `@st.fragment` com seletor de ano próprio (`e100_ano`), estado indisponível, detalhe com a distribuição entre quem votou. Saíram `ui.bloco_votos`, `ui.barra_empilhada` e `narrativa.votos` (e o teste dela).
- Verificação anterior do bloco de 100 eleitores: incluía pontos em lote nas 16.711 linhas, exemplo, empate, frases, indisponível, volta do ano e soma dos percentuais visíveis; incluída na suíte atual de 85 testes.
- Manaus 2022 (84 eleitores de seções não instaladas) registrada em `docs/validacao.md`.
