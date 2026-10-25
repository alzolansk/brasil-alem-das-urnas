# Handoff: loader e transição entre páginas (25/10/2026)

## Pedido posterior: abertura mínima de 1,5 s

O usuário pediu que toda abertura mostre a animação por 1,5 s, mesmo com dados carregados. Isso substitui a regra antiga da seção 11.3 e a decisão da primeira retomada de ocultar a camada com cache quente. O temporizador agora fica no CSS, começa na montagem no navegador e espera também o conteúdo; não há espera artificial no Python. Nova abertura/recarregamento repete a camada, navegação interna não. O ciclo visual de 3,6 s da referência continua igual. Alto contraste restaura o desenho completo e a primeira frase, além de desligar as animações. A spec e o planejamento do repositório registram a nova regra; o plano externo do Claude foi consultado como referência.

Sondagem reproduzível: `python tests/browser/verificar_loader.py --saida <pasta>` com o Streamlit em `http://localhost:8599`, Playwright e Chrome instalados no ambiente de verificação. Mede exibição real, cache aquecido, recarregamento em rota interna, movimento reduzido, alto contraste e conteúdo que demora mais do que 1,5 s. Evidências atuais ficam no checklist `docs/design/aceite/README.md`. As seções abaixo são histórico das etapas anteriores.

## Retomada por Codex (25/10/2026)

O estado experimental descrito abaixo foi resolvido: `Home.py` voltou a usar `st.markdown(..., unsafe_allow_html=True)` para CSS e camada. A camada agora se oculta imediatamente quando o rodapé chega, sem fade; a visibilidade espera 150 ms antes de aparecer para não piscar no quadro entre a retirada do rodapé antigo e a retirada da camada na primeira navegação. O teste no Chrome reproduziu esse piscar antes do ajuste e não o reproduziu depois.

Verificação atual: 85 testes passam, Ruff limpo; Chrome/Playwright confirmou transições direita/esquerda, topo a 0 px, camada inicial ausente nas trocas e compacto de Municípios até o SVG do Plotly. Servidor reiniciado: camada visível ~1,8–2,9 s. Servidor aquecido com página pronta: camada permaneceu oculta. `docs/planejamento.md` e o checklist 11.4 foram atualizados. Nenhum commit feito.

Limitação preservada e registrada: o loader só existe após o Streamlit montar HTML/CSS; não cobre o intervalo inicial de widgets sem estilo. Os demais itens da revisão listados abaixo não foram alterados. O restante deste arquivo registra o diagnóstico e o estado anterior à retomada.

## Pedido do usuário
1. Corrigir o loader, que não aparecia em lugar nenhum: nem no 1º acesso, nem na troca de páginas.
2. Nas abas, **não** pôr loader. Em vez disso, uma **animação de transição esquerda/direita** entre as páginas, conforme a direção (para onde a pessoa vai e de onde vem).

A tarefa foi **interrompida a pedido do usuário** no meio de um experimento (ver "Estado atual"). Nada foi commitado.

## Diagnóstico (confirmado no Chrome com Playwright)
- O loader antigo (`ui.carregando()` nas 4 telas) envolvia só leituras de Parquet de 20 a 30 ms. Era colocado e retirado na mesma fração de segundo: aparecia por cerca de 120 ms no 1º acesso e nunca nas trocas de aba.
- O que demora fica fora dele: o `import navegacao` (cerca de 0,6 s, com pandas e Plotly), o cabeçalho (lê dados antes do loader) e o desenho do Plotly no navegador.
- No Mapa, `espera.empty()` rodava **antes** do `st.plotly_chart`.
- O teste `test_loader_some_depois_de_carregar` só conferia a ausência do loader no fim; nunca que ele aparecia.
- **Descoberta nova, que muda a abordagem:** no 1º acesso, o conteúdo de **todo `st.markdown`** (CSS e HTML) só aparece cerca de 1,2 s depois dos primeiros blocos. O Streamlit carrega sob demanda o código que desenha markdown com HTML. Nesse intervalo, os widgets aparecem **sem estilo** (texto, rádio, selectbox crus). Uma camada feita com `st.markdown` não consegue cobrir esse intervalo. Linha do tempo medida (servidor aquecido): blocos de 266 a 1.430 ms; markdown, CSS e camada só em 1.552 ms, junto com o rodapé.

## O que foi feito (arquivos alterados, sem commit)
| Arquivo | Mudança |
|---|---|
| `app/lib/loader.py` (novo) | Loader extraído do `ui.py`, **sem pandas** (teste garante). Novas funções `sobreposicao_html(contraste)`, para a tela cheia do 1º acesso, e `loader_grafico(titulo, texto)`, para a área do Mapa. Cada uma tem um id de gradiente próprio. |
| `app/assets/loader.css` (novo) | Seção do loader retirada do `style.css`, mais as regras novas:<br>• `.bau-sobre` fixa em tela cheia; some sozinha (com fade) quando `.st-key-rodape` existe, sem depender do Python, então funciona também com `st.stop()`.<br>• Variante `.contraste`.<br>• `[data-stale="true"] .bau-sobre` escondida, o que evitou a camada voltar por um quadro na 1ª troca de aba.<br>• Loader do gráfico: fica sobre a área do mapa e some quando existe `[data-stale="false"] .js-plotly-plot .main-svg`; atraso de 150 ms para não piscar. |
| `app/assets/style.css` | Sem a seção do loader; ganhou os keyframes `entrar-direita` e `entrar-esquerda`. |
| `app/lib/ui.py` | Sem o código do loader (importa `loader_html` de `loader.py`). Novos: `ORDEM` (abas, depois o rodapé), `direcao(anterior, atual)` e `_css_transicao(sentido)`. `cabecalho()` guarda `st.session_state["_pagina"]` e injeta a transição só quando a página muda e o alto contraste está desligado. A animação vale para os blocos não stale abaixo do cabeçalho, exceto o rodapé; os contêineres com chave ficam dentro de `stLayoutWrapper`, por isso os seletores usam `:has(> .st-key-…)`. |
| `app/telas/mapa.py` | Os dois mapas (Estados e Municípios) ficam em `st.container(key="mapa_grafico")`, com `loader.loader_grafico(...)` antes do `plotly_chart`. Saiu o `espera`/`st.empty()`. O loader não aparece na Lista ordenada nem quando a UF não tem dados. |
| `app/Home.py` | Depois do `set_page_config` e **antes** do `import navegacao`: injeta `loader.css`, cria o espaço `sobreposicao = st.empty()` (em toda execução, para não deslocar os elementos) e o preenche só na 1ª execução da sessão (`_abriu`). |
| `tests/test_app.py` | `abrir(..., estado=)` para pré-definir o `session_state`. Testes novos: loader sem pandas, ids únicos, Home com camada só no 1º acesso, variante de contraste, loader do gráfico nos Municípios, `direcao` (6 casos), lado da transição por página, sem transição no 1º acesso e no alto contraste. |

## Verificado no navegador (antes do experimento com st.html)
- **Transição: funciona.** Explore → Mapa e Comparativo → Brasil entram pela direita (`translateX(56px)` → 0); Mapa → Comparativo entra pela esquerda. Dura 420 ms e respeita `prefers-reduced-motion`.
- **Loader do gráfico: funciona.** Mapa → Municípios: visível por cerca de 0,8 s até o Plotly desenhar. Na 1ª abertura do Mapa, visível por cerca de 1 s, enquanto o navegador baixa o código do Plotly.
- **Camada do 1º acesso: funciona só em parte.** Com o servidor frio, cobriu de 1,0 s a 2,4 s e sumiu com fade. Com o servidor aquecido, aparece junto com a página pronta e só faz o fade, um **piscar branco** sobre a página. Isso vem da espera do markdown descrita no diagnóstico.
- Os blocos invisíveis não empurram o layout: o topo continua a 0 px do início do bloco em todas as telas.
- `ruff` limpo e **85 testes passando**, mas **antes** da última mudança no `Home.py` (abaixo).

## Estado atual: experimento pela metade, decidir antes de seguir
O `Home.py` foi trocado de `st.markdown(...)` para **`st.html(...)`** (linhas 23 e 28), para testar se o `st.html` escapa da espera do markdown. Resultado do único teste:
- A camada apareceu em 2.329 ms, ou seja, **também esperou**.
- O CSS **não foi aplicado**: `display: block` e nenhum `<style>` com `bau-sobre` no DOM. O `st.html` com só `<style>` provavelmente vai para outro lugar ou é sanitizado.

**O experimento piorou e deve ser revertido.** Os testes **não foram rodados** depois dessa troca, e `test_home_mostra_loader_so_no_primeiro_acesso` deve falhar, porque procura os valores em `at.markdown`.

## Próximos passos sugeridos
1. Reverter as linhas 23 e 28 do `Home.py` para `st.markdown(..., unsafe_allow_html=True)` e rodar `ruff check .` e `pytest -q`.
2. Resolver o piscar e os widgets sem estilo do 1º acesso. Opções a avaliar:
   - Pular a camada quando a página já chega pronta. O CSS só conhece a presença do rodapé, então talvez tirar o fade de saída (`display: none` direto quando o rodapé existe), aceitando que a camada só aparece quando o carregamento é lento de fato (servidor frio).
   - Esconder a página inteira até o CSS chegar. Não dá por CSS, que é justamente o que atrasa. Um caminho seria um componente (`st.components.v1.html`, iframe) ou o tema do `.streamlit/config.toml` para disfarçar os widgets crus. Avaliar o custo.
   - Aceitar a limitação: o tempo antes do 1º bloco é o carregamento do próprio Streamlit e nenhum código Python o cobre.
3. Conferir de novo com o script de sondagem (abaixo), em servidor frio e aquecido.
4. Atualizar `docs/planejamento.md`, na seção Loader, e o checklist 11.4 de `docs/design/aceite/README.md`. Talvez refazer as capturas do loader.
5. Itens da revisão anterior ainda abertos (não tocados):
   - "Sobre os dados" diz que o exterior entra no total do Brasil (errado; ver `docs/metodologia.md:51`).
   - Faltam no app a nota de diferença com o painel do TSE e o exterior à parte.
   - O Explore no 2º turno de 2026 fica sem "vs. 2022".
   - Faltam setas no `bloco_indicador`.
   - Bug de reselecionar a mesma linha na Lista ordenada do Mapa.
   - `--malha` não baixa a `malha_UF`.
   - Código morto: `em_quatro_anos` e `posicao_uf`.

## Como verificar no navegador
- Subir: `python -m streamlit run app/Home.py --server.port 8599 --server.headless true --server.runOnSave false`.
- **Atenção no Windows:** parar a tarefa do shell **não mata** o processo do Streamlit. Antes de subir de novo, conferir com `Get-NetTCPConnection -LocalPort 8599 -State Listen` e encerrar com `Stop-Process`. Dois servidores na mesma porta fazem o navegador usar o código antigo, e isso já confundiu uma rodada de verificação.
- Scripts de sondagem (Playwright com o Chrome instalado) na pasta de rascunho da sessão `C:\Users\joaov\AppData\Local\Temp\claude\c--xampp-htdocs-brasil-alem-das-urnas\b3eebbf5-cfa3-41f7-88ef-cdb76d5f60db\scratchpad\`:
  - `verifica.py`: camada, transição e loader do gráfico, quadro a quadro.
  - `quadros.py`: estado da `.bau-sobre` e dos estilos no 1º acesso.
  - `dom.py`: estrutura do bloco principal.

  A pasta é temporária; copie os scripts se for usá-los depois.
