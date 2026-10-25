# Especificação técnica: deixar o app fiel ao protótipo

**Projeto:** Brasil Além das Urnas (app Streamlit em `app/`)
**Data:** 25/10/2026
**Para:** Claude Code
**Referência visual:** canvas de Design "Brasil Além das Urnas", com 4 artboards: `1 · Explore seu município`, `2 · Comparativo 2022 × 2026`, `3 · Mapa eleitoral interativo` e `4 · Brasil em perspectiva`. Esta versão do protótipo **substitui o `docs/design/prototipo-2.pdf`** como referência.

---

## 0. Como usar este documento

### 0.1 Escopo
Pode alterar:

- `app/assets/` (`style.css`, `contraste.css`, `logo.svg`)
- `app/lib/` (`ui.py`, `charts.py`, `fmt.py`, `narrativa.py`)
- `app/telas/` (`explore.py`, `comparativo.py`, `mapa.py`, `brasil.py`)
- `app/Home.py`, `app/navegacao.py`, `.streamlit/config.toml`
- `tests/test_app.py` (só onde esta especificação mandar)
- `docs/design/tokens.md` e `docs/planejamento.md`

**Não** altere `ingestion/`, `sql/`, `scripts/` nem `data/`. Todas as colunas de que esta especificação precisa já existem nas marts (conferido em 25/10/2026).

### 0.2 Restrições
1. Use só Streamlit, Plotly e CSS, sem dependências novas e sem componentes JavaScript customizados.
2. Mantenha as decisões já registradas:
   - **D4:** comparativo fixo 2022 → 2026.
   - **D5:** azul ▲ indica aumento e laranja ▼ indica queda, e a cor não diz se a mudança é boa ou ruim.
   - **D7:** alto contraste.
   - **D8:** sem botões "Consultar" ou "Atualizar".

   Onde o protótipo contradiz uma dessas decisões, **vale a decisão** (detalhes na seção 10).
3. O app usa dados reais. **Não** implemente o selo amarelo "Dados ilustrativos do protótipo".
4. Os números de exemplo do protótipo (Campinas, 79,4% etc.) são ilustrativos. Todo número na tela vem das marts.
5. Ao final, `pytest` e `ruff` precisam passar.

### 0.3 Ordem sugerida (um commit por etapa)
1. Fundamentos: tokens, tipografia, logo e favicon (seção 2)
2. Layout global: cabeçalho, navegação, rodapé e painel de filtros (seção 3)
3. Componentes novos em `ui.py` e funções novas em `narrativa.py` e `fmt.py` (seções 4 e 6)
4. Telas, na ordem Explore → Comparativo → Brasil → Mapa (seção 5)
5. Animações (seção 7)
6. Acessibilidade, responsivo e aceite (seções 8 e 9)

---

## 1. Diagnóstico das telas atuais

O app foi rodado localmente com os Parquets reais, Campinas (SP), em 1280px e 390px.

| # | Onde | Como está hoje | Como está no protótipo | Prioridade |
|---|---|---|---|---|
| 1 | Logo | Urna amarela num quadrado azul-marinho (`app/assets/logo.svg`) | Mapa do Brasil com diagonais verde, amarela e azul (`docs/design/brasil-alem-das-urnas-simbolo.svg`) | Alta |
| 2 | Favicon | Emoji 🗳️ | O próprio símbolo da logo | Média |
| 3 | Fonte do texto | Os parágrafos estão em **Source Sans**, a fonte padrão do Streamlit (conferido no DOM: `getComputedStyle(p).fontFamily = "Source Sans"`). O Inter só pega em parte dos elementos | Inter em todo o texto; Raleway nos títulos e números | Alta |
| 4 | Cores | Tokens do protótipo 2 (`#1550A8`, `#0B1F45`, `#1B7A3A`, `#F2C200`, `#C8401A`) | Tokens novos (seção 2.1) | Média |
| 5 | Faixa do topo | 6px em três terços iguais | 4px na proporção 3 : 1 : 3 (verde, amarelo, azul) | Baixa |
| 6 | Barra utilitária | Não existe | Faixa cinza-clara acima da faixa colorida, com o texto "Ferramenta independente…" e os links Acessibilidade, Sobre os dados e Alto contraste | Média |
| 7 | Busca | Campo largo com rótulo visível, abaixo da marca | Campo arredondado (pill) com ícone de lupa, à direita da marca, na mesma linha | Alta |
| 8 | Navegação | 4 colunas de largura igual espalhadas pela página; a aba ativa tem fundo cinza | Links alinhados à esquerda, 28px de espaço entre eles, aba ativa sublinhada em azul (3px) e sem fundo | Alta |
| 9 | Trilha de navegação (breadcrumb) | "Início › Tela" | "Início › Tela › **Município**", com "Início" clicável | Baixa |
| 10 | Título da página | O H1 é o nome do município | O H1 é o nome da tela, seguido de um parágrafo de abertura; o município aparece na linha de contexto | Alta |
| 11 | Filtros | Escondidos num `st.expander` | Painel sempre visível, com fundo `#F5F7FA` e cantos arredondados | Alta |
| 12 | Explore: frase de abertura | Frase descritiva ("Em Campinas (SP), no 1º turno…") | Manchete editorial em H2 de 34px, com trecho grifado em amarelo (seção 6) | Alta |
| 13 | Explore: cartões principais | Número azul de 52px; comparações em chips | Número azul-marinho de 64px em Raleway 800; comparações numa grade de 3 colunas com linha divisória acima | Alta |
| 14 | Explore: Leitura rápida | Faixa larga abaixo dos cartões | Cartão escuro **ao lado** dos dois cartões principais, com o link "Ver … em perspectiva →" | Alta |
| 15 | Explore: votos | Título solto e barra sem contexto; brancos em **cinza** | Bloco com fundo claro: título "E quem votou, votou em quê?", texto, barra de 28px e três números com quantidades. Brancos em **amarelo** | Média |
| 16 | Explore: zonas | `st.dataframe` com 7 colunas, sem cartão | Tabela HTML dentro de um cartão com título, subtítulo e "Baixar CSV" no cabeçalho | Média |
| 17 | Comparativo: abertura | "Em quatro anos, o comparecimento caiu…", em texto de 17px | Rótulo "EM QUATRO ANOS" com manchete em H2 de 32px e grifo | Alta |
| 18 | Comparativo: tabela | Tabela sem cartão; legenda em nota de rodapé | Tabela dentro de um cartão, com a legenda Aumentou/Diminuiu no cabeçalho e a diferença colorida e em negrito | Média |
| 19 | Comparativo: turnos | Duas tabelas completas de evolução | Dois cartões com barras pareadas (1º e 2º turno), uma etiqueta de status e uma frase de síntese | Alta |
| 20 | Mapa: estrutura | Filtros num expander no topo; mapa e painel em 2 colunas | 3 colunas: filtros à esquerda, mapa no centro, estado selecionado e ranking à direita | Alta |
| 21 | Mapa: quadrados dos estados | Escala de cor contínua com barra de cor; posições diferentes das do protótipo; o filtro de região **remove** os estados de fora | 5 faixas de cor, valor escrito dentro de cada quadrado, legenda horizontal; o filtro de região **esmaece** os estados de fora (opacidade de 25%) | Alta |
| 22 | Mapa: Mapa ou lista | Rádio dentro do expander de filtros | Controle segmentado no cabeçalho do cartão do mapa; a lista tem barras e responde a clique | Média |
| 23 | Mapa: ranking | Não existe | Cartão "Maiores valores · Brasil/Região X" com os 5 maiores estados | Média |
| 24 | Brasil: cartões | Número de eleitores aptos enorme (vira duas linhas: "157,8 / milhões") | O nome do lugar em destaque (24px); os aptos em texto menor; borda superior de 4px na cor da série | Alta |
| 25 | Brasil: indicadores | Gráfico Plotly de barras agrupadas | Lista HTML "Indicador a indicador": cabeçalho com "vs. estado / vs. Brasil" e três barras finas por indicador | Alta |
| 26 | Brasil: tendência | O eixo X mostra "2.022,5", "2.023" etc., porque o Plotly trata 2022 e 2026 como números; tem eixo Y, grade e legenda | Gráfico de inclinação limpo: só 2022 e 2026, rótulos nas pontas e Brasil tracejado | Alta (bug) |
| 27 | Brasil: estrutura | Uma coluna | Duas colunas: indicadores à esquerda (3fr); tendência e Leitura rápida à direita (2fr) | Média |
| 28 | Rodapé | Links soltos numa linha cinza, com o bloco azul-marinho embaixo | Um bloco azul-marinho só: nome e texto à esquerda, links brancos à direita | Média |
| 29 | Rota `/explore` | Abrir `/explore` mostra o aviso "Page not found", porque a página padrão do `st.navigation` fica na raiz e ignora o `url_path` | Links e compartilhamento funcionando | Média (bug) |

---

## 2. Fundamentos

### 2.1 Tokens de cor
Substitua o bloco `:root` de `style.css`. Atualize também `charts.py` (constantes), `.streamlit/config.toml` e `docs/design/tokens.md`.

| Token | Antes | **Agora** | Uso |
|---|---|---|---|
| `--navy` | `#0B1F45` | `#071D41` | Títulos, números de destaque, rodapé, cartão Leitura rápida |
| `--blue` | `#1550A8` | `#0B4EA2` | Ações, links, aba ativa, série Município, ▲ |
| `--blue-hover` | (não existe) | `#073A7A` | Hover de links e botões |
| `--blue-soft` | (não existe) | `#EEF4FC` | Item selecionado, fundo de aviso |
| `--blue-2t` | (não existe) | `#7FA6D8` | Barra do 2º turno |
| `--green` | `#1B7A3A` | `#12753E` | Série Estado, votos válidos, rótulos de seção ("O QUE OS NÚMEROS DIZEM") |
| `--green-text` | (não existe) | `#0E5C31` | Texto verde sobre fundo claro (etiqueta "Apuração concluída") |
| `--green-soft` | (não existe) | `#E3F2E8` | Fundo da etiqueta "Apuração concluída" |
| `--yellow` | `#F2C200` | `#F5C400` | Faixa, votos brancos, numeração da Leitura rápida, contorno de foco e de seleção |
| `--yellow-soft` | (não existe) | `#FCE79A` | Grifo da manchete |
| `--yellow-tag` | (não existe) | `#FFF4CC` com texto `#6B4E00` e borda `#E8C84A` | Etiqueta "2º turno em 25/10" |
| `--orange` | `#C8401A` | `#C2410C` | Votos nulos, ▼ |
| `--gray` | `#6B7280` | `#6B7280` (mantém) | Série Brasil |
| `--text` | `#0B1F45` | `#1B1B1B` | Texto corrido |
| `--muted` | `#4B5563` | `#3A3F47` para texto secundário e `#4A4F57` para legendas | Texto de apoio |
| `--border` | `#E3E7EE` | `#DCDFE4` para bordas de cartão e `#E6E8EC` para divisórias internas | |
| `--input-border` | (não existe) | `#888F99` | Borda de campos (contraste de 3:1 contra o branco) |
| `--bg-soft` | `#F5F7FA` | `#F5F7FA` (mantém) | Barra utilitária, painéis de filtro, bloco de votos |
| `--track` | (não existe) | `#F1F3F6` | Fundo das barras |
| `--on-dark-muted` | (não existe) | `#C9D3E3` | Texto secundário no rodapé |

**Escala do mapa (5 faixas, do menor para o maior valor):** `#DCE7F5`, `#A9C4E8`, `#6F9BD6`, `#2F6BBE`, `#0B3F86`. O texto fica azul-marinho nas faixas 1 a 3 e branco nas faixas 4 e 5.

**Séries fixas:** Município `--blue`, Estado `--green`, Brasil `--gray`. Na tendência, a linha do Brasil é tracejada (`6 4`).

**Regra de contraste:** `--yellow` **nunca** é usado como cor de texto sobre fundo branco. Texto sobre amarelo é sempre `--navy`.

`.streamlit/config.toml`:
```toml
[theme]
base = "light"
primaryColor = "#0B4EA2"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F5F7FA"
textColor = "#1B1B1B"
font = "Inter"
headingFont = "Raleway"
borderColor = "#DCDFE4"
baseRadius = "8px"

[[theme.fontFaces]]
family = "Inter"
url = "https://fonts.gstatic.com/s/inter/v18/UcC73FwrK3iLTeHuS_nVMrMxCp50SjIa1ZL7.woff2"
weight = "400 700"

[[theme.fontFaces]]
family = "Raleway"
url = "https://fonts.gstatic.com/s/raleway/v34/1Ptug8zYS_SKggPNyC0ITw.woff2"
weight = "500 800"
```
> A versão instalada é a 1.58. As chaves `font`, `headingFont` e `[[theme.fontFaces]]` existem desde a 1.45 e `borderColor`/`baseRadius` desde a 1.46. Confira os nomes exatos na documentação da versão instalada e as URLs atuais dos arquivos `.woff2` (abra a CSS do Google Fonts e copie as URLs de lá). Se preferir não depender de CDN, sirva os `.woff2` por `app/static/` com `server.enableStaticServing = true`.

### 2.2 Tipografia
Com o tema configurado, remova o `@import` do Google Fonts de `style.css`. Como garantia, acrescente:
```css
.stApp, .stApp p, .stApp li, .stApp label, .stApp input, .stApp button,
.stApp [data-testid="stMarkdownContainer"] { font-family: "Inter", system-ui, sans-serif; }
h1, h2, h3, .titulo, .numero { font-family: "Raleway", "Inter", sans-serif !important; }
```

| Papel | Fonte | Tamanho / altura de linha | Peso | Cor |
|---|---|---|---|---|
| H1 da tela | Raleway | 36px / 1.2 | 700 | `--navy` |
| Parágrafo de abertura | Inter | 17px / 1.55, largura máxima de 760px | 400 | `#3A3F47` |
| Manchete (achado) | Raleway | 34px / 1.25 (32px no Comparativo), largura máxima de 900px | 700 | `--navy` |
| Rótulo de seção | Inter | 13px, maiúsculas, espaçamento entre letras de 0.6px | 700 | `--green`; `--yellow` sobre fundo escuro |
| H2 de seção | Raleway | 26px | 700 | `--navy` |
| Título de cartão | Raleway | 20 a 22px | 700 | `--navy` |
| Número principal | Raleway | 64px / 1, algarismos tabulares | 800 | `--navy` |
| Número secundário | Raleway | 26px (votos), 40px (estado no mapa) | 700 | `--navy` / `--blue` |
| Texto corrido | Inter | 15px / 1.5 | 400 | `--text` |
| Legenda e meta | Inter | 13 a 14px | 400 a 600 | `#4A4F57` |

Todo número fica com `font-variant-numeric: tabular-nums`.

### 2.3 Espaçamento, raios e sombras
- Conteúdo com largura máxima de **1200px** e margem lateral de 24px (16px abaixo de 768px). Substitua o `max-width: 1180px` de `.block-container`.
- Espaço vertical entre blocos da página: 32px. Dentro de cartões: 16 a 24px.
- Raios: campos 6px; cartões de tabela e de filtro 12px; cartões de destaque 16px; botões e etiquetas 999px.
- Cartão: `border: 1px solid #DCDFE4`, sem sombra. A **única sombra** do site fica no cabeçalho: `0 1px 3px rgba(7,29,65,.06)`.
- Área mínima de toque: 44px.

### 2.4 Logo e favicon
1. Copie `docs/design/brasil-alem-das-urnas-simbolo.svg` para `app/assets/logo.svg`. Antes, **remova o bloco `<metadata>…</metadata>`**: são cerca de 8 KB de manifesto C2PA, e o arquivo é embutido em base64 em toda página. Mantenha `<title>`, `<defs>` e `<path>`.
2. Em `ui.cabecalho`, o `<img>` passa a ter 48 × 48px, com `alt=""` (o nome ao lado já identifica a marca).
3. Em `Home.py`, troque o emoji por `page_icon=str(Path(__file__).parent / "assets" / "logo.svg")`. Se a versão não aceitar SVG, gere um `favicon.png` de 64px.
4. Alto contraste: a logo continua colorida (sem filtro).

---

## 3. Layout global (`ui.py` + `style.css`)

### 3.1 Estrutura do topo, de cima para baixo
```
[barra utilitária]  fundo #F5F7FA, borda inferior #DCDFE4, 13px, cor #4A4F57
[faixa 4px]         verde 3fr · amarelo 1fr · azul 3fr
[cabeçalho]         borda inferior #DCDFE4 + sombra
   linha 1: [logo 48 + "Brasil Além das Urnas" 22px/800 + subtítulo 12px]   [busca pill, até 380px]
   linha 2: navegação (links)
[conteúdo]
   trilha (breadcrumb) | selo de status (à direita)
   H1 + parágrafo de abertura
   painel de filtros
   …
[rodapé azul-marinho]
```

**Barra utilitária.** À esquerda, o texto "Ferramenta independente de consulta a dados eleitorais públicos". À direita, os links "Acessibilidade" (`/acessibilidade`) e "Sobre os dados" (`/dados`) e o `st.toggle("Alto contraste", key="alto_contraste")`. Implemente com um `st.container(key="utilitaria", horizontal=True)` ocupando a largura toda (margens negativas, como já faz a `.faixa`). Abaixo de 768px, o texto da esquerda some e só ficam os links e o toggle.

**Cabeçalho, linha 1.** Use `st.columns([3, 2], vertical_alignment="center")`.
- Esquerda: logo e nome em HTML. O nome é um link para a tela inicial.
- Direita: o `text_input` atual com `label_visibility="collapsed"` e o placeholder "Buscar município ou estado". Mantenha a lógica de busca, o `selectbox` de resultados e as sugestões.
- CSS do campo de busca (`.st-key-busca input`): `height: 44px; border: 1px solid #888F99; border-radius: 999px; padding: 0 48px 0 18px;` e lupa à direita via `background-image` com SVG em data URI (traço `#0B4EA2`, 20px).
- Abaixo de 768px, a busca vai para uma linha própria e continua *sticky*, como hoje.

**Cabeçalho, linha 2 (navegação).** Troque as `st.columns(len(ABAS))` por `st.container(key="nav_desktop", horizontal=True, gap="large")` com os `page_link`. CSS:
```css
.st-key-nav_desktop [data-testid="stPageLink-NavLink"] { background: transparent !important; border-radius: 0;
  border-bottom: 3px solid transparent; padding: 14px 4px; min-height: 44px; transition: color .15s, border-color .15s; }
.st-key-nav_desktop [data-testid="stPageLink-NavLink"] p { font: 600 15px "Inter"; color: #1B1B1B; }
.st-key-nav_desktop [data-testid="stPageLink-NavLink"]:hover p { color: var(--blue); }
.st-key-nav_desktop [data-testid="stPageLink-NavLink"][aria-current="page"] { border-bottom-color: var(--blue); }
.st-key-nav_desktop [data-testid="stPageLink-NavLink"][aria-current="page"] p { color: var(--blue); font-weight: 700; }
```
O menu "☰" do celular continua como está.

**Trilha e selo.** Fica numa linha com `justify-content: space-between`.
- Trilha: "Início › {Tela} › **{Município} ({UF})**". "Início" é um `<a href="/">`. O último item fica em `#1B1B1B`, peso 600, com `aria-current="page"`. Use `<nav aria-label="Você está em">`.
- O selo de status (hoje dentro da marca) vai para a direita dessa linha, com as cores de `--green-soft` / `--yellow-tag`.

**Abertura da tela.** Crie um helper `ui.abertura(titulo, texto)`. Os textos ficam assim:

| Tela | H1 | Parágrafo |
|---|---|---|
| Explore | Explore seu município | Quantas pessoas votaram na sua cidade, quantas ficaram em casa e como ficaram os votos. Tudo comparado com o estado e com o país. |
| Comparativo | Comparativo 2022 × 2026 | Veja como os indicadores do município evoluíram entre as duas últimas eleições presidenciais e o que mudou de um turno para o outro. |
| Mapa | Mapa eleitoral interativo | Escolha um indicador e filtre por região para identificar padrões no território. Selecione um estado para ver o detalhe e descer até os municípios. |
| Brasil | Brasil em perspectiva | Compare o município com o seu estado e com a média nacional para entender onde ele se destaca e para onde está caminhando. |

O nome do município sai do H1 e vai para a **linha de contexto** (seção 4.1).

**Painel de filtros.** Troque o `st.expander("Filtros")` por um `st.container(key="filtros")` com:
```css
.st-key-filtros { background: var(--bg-soft); border: 1px solid #DCDFE4; border-radius: 12px; padding: 24px; }
```
Campos: rótulo em 13px/600 `#333`, altura de 44px, borda `#888F99`, raio de 6px.

### 3.2 Controles segmentados (rádios horizontais)
Aplique a classe visual de "segmentado" (pílulas) aos rádios horizontais que já existem, **sem trocar o widget** (os testes dependem de `at.radio(key=…)`):
```css
.seg [role="radiogroup"] { display: inline-flex; gap: 0; border: 1px solid var(--blue); border-radius: 999px; padding: 2px; }
.seg [role="radiogroup"] label { margin: 0; padding: 0 18px; min-height: 40px; border-radius: 999px; display: flex; align-items: center; cursor: pointer; transition: background .15s, color .15s; }
.seg [role="radiogroup"] label > div:first-child { display: none; }   /* esconde a bolinha */
.seg [role="radiogroup"] label p { color: var(--blue); font-weight: 600; font-size: 14px; }
.seg [role="radiogroup"] label:has(input:checked) { background: var(--blue); }
.seg [role="radiogroup"] label:has(input:checked) p { color: #fff; }
```
Aplique pelas chaves: `.st-key-explore_eleicao`, `.st-key-mapa_nivel`, `.st-key-mapa_visao` e `.st-key-brasil_eleicao`. Os seletores internos (`label > div:first-child`) variam entre versões do Streamlit: confira no DOM da 1.58 antes de fechar. O foco pelo teclado precisa continuar visível (`:focus-within` com contorno amarelo).

### 3.3 Rodapé
Junte os links e o texto num único bloco: `st.container(key="rodape")` com margens negativas, para ocupar a largura toda.
```css
.st-key-rodape { background: var(--navy); color: #fff; margin: 48px -1.25rem -2rem; padding: 40px 24px; }
.st-key-rodape [data-testid="stPageLink-NavLink"] p { color: #fff; text-decoration: underline; font-size: 14px; }
```
Use duas colunas:
- Esquerda: "Brasil Além das Urnas" (Raleway 18px/700) e, em `#C9D3E3`, o texto "Ferramenta independente, sem vínculo com órgãos públicos ou partidos. Fonte: Portal de Dados Abertos do TSE e IBGE · dados atualizados em {data}."
- Direita: os 6 `page_link` em linha, com quebra quando faltar espaço.

Remova o `st.divider()` e a linha de links cinza de cima.

### 3.4 Bug da rota `/explore`
A página padrão do `st.navigation` é servida na raiz (`/`). Faça assim:
- Os links internos para o Explore apontam para `/`, nunca para `/explore`.
- No link de compartilhamento, use `/?m=…`.
- Acrescente um teste que abre o app sem caminho e confere que o Explore renderiza.

---

## 4. Componentes (`ui.py`)

Todo componente devolve HTML com `ui.html()` e escapa os textos com `escape()`, como já é feito hoje.

### 4.1 `linha_contexto(municipio, uf, ano, turno, aptos)`
```html
<div class="contexto">Campinas (SP) · Eleição presidencial 2026 · 1º turno · 873.613 eleitores aptos</div>
```
Estilo: 14px, peso 600, `#3A3F47`.

### 4.2 `manchete(rotulo, partes)`
`partes` é o dicionário `{"antes", "destaque", "depois"}` que sai de `narrativa` (seção 6).
```html
<section class="achado">
  <span class="rotulo">O que os números dizem</span>
  <h2>{antes} <span class="marca">{destaque}</span>{depois}</h2>
</section>
```
```css
.achado { display: flex; flex-direction: column; gap: 10px; max-width: 900px; }
.achado .rotulo { font: 700 13px "Inter"; letter-spacing: .6px; text-transform: uppercase; color: var(--green); }
.achado h2 { margin: 0; font-size: 34px; line-height: 1.25; }
.marca { background: linear-gradient(var(--yellow-soft), var(--yellow-soft)) no-repeat 0 88% / 100% 38%; padding: 0 2px; }
```
No alto contraste, `.marca` usa sublinhado amarelo de 3px e fundo transparente.

### 4.3 `cartao_heroi(titulo, valor, frase, comparacoes)`
`comparacoes` é uma lista de `(rotulo, delta_pp)` na ordem **vs. estado, vs. Brasil, vs. 2022**. O item de 2022 só aparece quando existe base.
```html
<article class="heroi">
  <h3>Comparecimento</h3>
  <span class="numero">76,4%</span>
  <span class="frase">667.699 eleitores foram votar</span>
  <dl class="comparacoes">
    <div><dt>vs. São Paulo</dt><dd class="down">▼ 1,0 p.p.</dd></div>
    …
  </dl>
</article>
```
```css
.heroi { border: 1px solid #DCDFE4; border-radius: 16px; padding: 28px; display: flex; flex-direction: column; gap: 14px; }
.heroi h3 { font: 700 16px "Inter"; color: #3A3F47; margin: 0; }
.heroi .numero { font: 800 64px/1 "Raleway"; color: var(--navy); font-variant-numeric: tabular-nums; }
.heroi .comparacoes { display: grid; grid-template-columns: repeat(3, minmax(0,1fr)); gap: 12px; margin: 6px 0 0; padding-top: 16px; border-top: 1px solid #E6E8EC; }
.heroi dt { font-size: 12px; color: #4A4F57; } .heroi dd { margin: 0; font: 700 16px "Inter"; }
.heroi dd.up { color: var(--blue); } .heroi dd.down { color: var(--orange); } .heroi dd.flat { color: var(--gray); }
```
- O rótulo "vs. {estado}" usa o **nome por extenso** da UF. Crie em `data.py` um dicionário `NOME_UF` com as 27 siglas.
- O sinal segue a D5: ▲ azul e ▼ laranja. Mantenha também o sinal no texto, com `fmt.pp` sem o "+", porque a seta já indica a direção.
- Texto da frase: Comparecimento → "{n} eleitores foram votar"; Abstenção → "{n} eleitores não foram votar".

### 4.4 `cartao_leitura(itens, link=None)`
Mantenha a estrutura atual e acrescente:
- Rótulo "LEITURA RÁPIDA" no padrão `.rotulo`, na cor `--yellow`.
- Itens em 15px/1.5 com 16px de espaço entre eles.
- Raio de 16px e padding de 28px.
- Link opcional no rodapé do cartão (`margin-top: auto`): "Ver {Município} em perspectiva →", branco, peso 600, apontando para a página `brasil`. Use `st.page_link` fora do HTML ou `<a href="/brasil?m={cd}">`.

### 4.5 `grade_herois(heroi1, heroi2, leitura)`
```css
.grade-herois { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 24px; }
@media (max-width: 1024px) { .grade-herois { grid-template-columns: 1fr 1fr; } .grade-herois > .escuro { grid-column: 1 / -1; } }
@media (max-width: 640px)  { .grade-herois { grid-template-columns: 1fr; } }
```

### 4.6 `bloco_votos(validos, brancos, nulos, qtd_validos, qtd_brancos, qtd_nulos, comparecimento, delta_bn_br)`
É um cartão com fundo `--bg-soft`, raio de 16px e padding de 28px, dividido em duas áreas com `flex-wrap`:
- **Esquerda (1fr):** o H3 "E quem votou, votou em quê?" e um texto gerado por `narrativa.votos(...)` (seção 6).
- **Direita (2fr):** a barra empilhada de 28px, com 2px entre os segmentos e raio de 6px. Válidos em `--green`, brancos em `--yellow`, nulos em `--orange`. Abaixo, uma grade de 3 colunas com, em cada uma: quadradinho de cor e nome (14px), percentual (Raleway 26px/700) e "{n} votos" (13px, `#4A4F57`).

A barra **não** mostra texto dentro dos segmentos (hoje mostra "94,8%"): os números ficam embaixo. Mantenha o `aria-label`.

### 4.7 `cartao_tabela(titulo, subtitulo, tabela_html)` e tabela de zonas
Cartão com raio de 16px e `overflow: hidden`. O cabeçalho tem padding de 20px 24px, borda inferior, título à esquerda e uma área para o botão à direita.
- O botão "Baixar CSV" é widget, então o cabeçalho é montado com `st.columns([4,1], vertical_alignment="center")` dentro de `st.container(key="zonas")`. O estilo do cartão vai na chave.
- O botão "Baixar CSV" vira um link-botão discreto: azul, 14px/600, ícone de download, sem borda.

Tabela (substitui o `st.dataframe` das zonas):

| Coluna | Formato |
|---|---|
| Zona | `"{nr:03d}ª Zona"`, como `<th scope="row">`, peso 600 |
| Eleitores aptos | `fmt.inteiro`, alinhado à direita |
| Comparecimento | `fmt.pct` |
| Abstenção | `fmt.pct` |
| Brancos + nulos | `fmt.pct(brancos_nulos_pct)` |

- O CSV continua sendo exatamente o que a tabela mostra. Atualize `tabela_zonas()` e a docstring.
- `thead` com fundo `--bg-soft`; linhas com `border-top: 1px solid #E6E8EC`; padding das células de 14px 16px (24px nas pontas).
- Município com mais de 12 zonas (São Paulo tem 58): o corpo da tabela rola dentro de `max-height: 560px`, com `thead` fixo (`position: sticky; top: 0`).
- Envolva tudo em `.tabela-rolagem` (rolagem horizontal no celular).

### 4.8 `etiqueta(texto, tipo)`
`tipo` é `"ok"` (fundo `--green-soft`, texto `--green-text`) ou `"aviso"` (fundo `#FFF4CC`, texto `#6B4E00`). Estilo: 13px/600, padding de 4px 10px, raio de 999px.

### 4.9 `barras_pareadas(indicadores, pendente)`
Para cada indicador, um bloco com o nome (14px/600) e uma grade de duas linhas, `grid-template-columns: 56px minmax(0,1fr) 64px`:
- **1º turno:** barra de 12px em `--blue`, largura igual ao valor em %.
- **2º turno:** barra em `--blue-2t`. Se estiver pendente, a barra ocupa 100% com `border: 1.5px dashed #888F99`, fundo transparente, e o valor mostra "Aguardando" em `#4A4F57`.
- O trilho fica em `--track`, com raio de 3px.

Os indicadores são comparecimento, abstenção, brancos e nulos. A legenda fica acima dos dois cartões: 1º turno, 2º turno e "Aguardando apuração" (quadrado tracejado).

### 4.10 `cartao_escopo(tipo, nome, aptos, serie)`
```html
<article class="escopo serie-mun"><span class="rotulo-cinza">MUNICÍPIO</span><h2>Campinas</h2><span>873 mil eleitores aptos</span></article>
```
- Estilo: `border-top: 4px solid <cor da série>`, raio de 12px e padding de 20px.
- O nome fica em Raleway 24px/700; a linha dos aptos em 14px `#3A3F47`.
- Aptos: `fmt.mil()` abaixo de 1 milhão e `fmt.milhoes()` a partir de 1 milhão (seção 6.3).

### 4.11 `bloco_indicador(nome, valores, escala, delta_uf, delta_br)`
Usado no "Indicador a indicador" do Brasil.
- Cabeçalho com o nome à esquerda (16px/700) e, à direita, "vs. estado **{±x p.p.}** · vs. Brasil **{±y p.p.}**", com as cores da D5.
- Em seguida, três linhas com `grid-template-columns: 96px minmax(0,1fr) 56px`: rótulo, barra de 14px na cor da série e valor em negrito.
- Uma borda inferior separa um bloco do outro.

---

## 5. Telas

### 5.1 Explore seu município (`telas/explore.py`)
Ordem dos blocos:
1. `ui.cabecalho("explore")`
2. `ui.abertura(...)`
3. Painel de filtros com o rádio `explore_eleicao` horizontal, no estilo segmentado. **Mantenha a chave e os valores**, porque o teste usa `(2026, 2)`.
4. `linha_contexto`
5. Se não houver dados: `ui.aguardando(...)`, no estilo da seção 5.1.1.
6. `manchete("O que os números dizem", narrativa.manchete_explore(...))`
7. `grade_herois` com o herói de comparecimento, o herói de abstenção e a Leitura rápida com link.
8. A nota "p.p. = ponto percentual…" vira uma legenda pequena **abaixo da grade** (13px).
9. `bloco_votos(...)`
10. Cartão "Zona por zona", com o subtítulo "A participação muda dentro da própria cidade" e a tabela da seção 4.7. Município com uma zona só: mantenha a nota atual (o teste procura "única zona eleitoral").
11. `ui.rodape()`

Remova o `frase_resumo` da tela, porque a manchete e a linha de contexto cobrem o que ele dizia. Mantenha a função em `narrativa.py`, porque os testes a usam.

#### 5.1.1 Estado "Aguardando apuração"
Siga o protótipo: cartão com fundo `--blue-soft`, borda `#B9CCE8`, raio de 12px e padding de 24px. À esquerda, um ícone de relógio (SVG com traço, 28px, `--blue`); à direita, o título 17px/700 "O 2º turno de 2026 ainda está sendo apurado" e o texto 15px "Assim que a totalização oficial for liberada, os números de {Município} aparecem aqui. Enquanto isso, veja o 1º turno ou o 2º turno de 2022."
**Mantenha** a expressão "Aguardando apuração" em algum lugar do HTML, porque o teste procura por ela. Ela pode ficar como rótulo de seção acima do título.

### 5.2 Comparativo 2022 × 2026 (`telas/comparativo.py`)
1. Cabeçalho, abertura e linha de contexto: "{Município} ({UF}) · 1º turno de 2022 comparado com o 1º turno de 2026". Pela D4, **não** há painel de filtros nesta tela.
2. `manchete("Em quatro anos", narrativa.manchete_comparativo(anos))`. Use 32px.
3. Cartão "Evolução dos indicadores · 1º turno":
   - O cabeçalho tem o subtítulo "Diferença em pontos percentuais (p.p.) de 2026 em relação a 2022" e, à direita, a legenda ■ Aumentou (`--blue`) e ■ Diminuiu (`--orange`).
   - Colunas: Indicador (`<th scope="row">`), 2022 (em `#4A4F57`), 2026 (peso 600), Diferença (700, colorida, com seta) e a barra de diferença (280px).
   - A linha de eleitores aptos continua em % relativo, com a coluna da barra vazia.
   - A barra de diferença cresce a partir do centro: 14px de altura, trilho `--track`, linha central de 1px em `#888F99`, preenchimento de 10px com raio de 2px.
   - A legenda de rodapé atual sai, porque passou para o cabeçalho. A frase "a cor não indica se é bom ou ruim" vira o `title`/tooltip da legenda e entra também na página de Acessibilidade.
4. Seção "1º turno × 2º turno":
   - H2 de 26px e o subtítulo "Como o comportamento do eleitor mudou entre os turnos de cada eleição presidencial".
   - A legenda de barras pareadas.
   - Dois cartões (`flex: 1 1 460px`), cada um com o título "Eleição {ano}" (Raleway 22px), uma etiqueta de status e `barras_pareadas`.
   - Etiqueta: "Apuração concluída" (`ok`) quando `status_comparacao == "disponivel"`; senão "2º turno em 25/10" (`aviso`).
   - No rodapé de cada cartão, depois de uma divisória, a frase `narrativa.entre_turnos(ano, c)`, ou o texto de pendência "Os dados do 2º turno de {ano} aparecem aqui automaticamente após a totalização oficial."
5. `ui.rodape()`

### 5.3 Mapa eleitoral (`telas/mapa.py`)
**Estrutura:** `st.columns([1.1, 2.4, 1.5], gap="large")`. O Streamlit empilha as colunas abaixo de 640px, na ordem filtros → mapa → painel.

**Coluna 1: filtros** (`st.container(key="mapa_filtros")`, no mesmo estilo de `.st-key-filtros`)

| Grupo | Widget | Observação |
|---|---|---|
| Indicador | `st.radio(..., key="mapa_indicador")`, vertical | Troca o `selectbox` atual. Cada opção é uma linha de 40px, raio de 8px e borda transparente; a selecionada fica com fundo `--blue-soft`, borda `--blue` e texto azul 600. Mantenha os **6 indicadores** que já existem. |
| Eleição | `st.selectbox(..., key="mapa_eleicao")` | Continua como está. |
| Região | `st.pills(REGIOES, default="Todas", key="mapa_regiao")` | Pílulas de 36px; a selecionada fica `--navy` com texto branco. Se o usuário desmarcar (`None`), trate como "Todas". |
| Nível | `st.radio(..., key="mapa_nivel")`, horizontal, segmentado | **Mantenha a chave** (teste). |

A descrição do indicador (`INDICADORES[i][1]`) entra abaixo do grupo Indicador, em 13px.

**Coluna 2: cartão do mapa** (`st.container(key="mapa_cartao")`, com borda, raio de 12px e padding de 24px)
- O cabeçalho tem o título "{Indicador} por {estado|município} · {turno}º turno de {ano}" (Raleway 22px) e a descrição (14px). À direita fica o rádio `mapa_visao` ("Mapa" / "Lista ordenada"), horizontal, segmentado. Ele sai dos filtros e vem para cá, **mantendo a chave** (teste).
- Descrição para "Mapa": "Cada quadrado é um estado, posicionado aproximadamente como no mapa. Clique para ver o detalhe."
- Descrição para "Lista": "Estados do maior para o menor valor. Clique em uma linha para ver o detalhe."

**Quadrados dos estados (`charts.grade_ufs`).** Reescreva a função assim:
1. Novas posições (linha, coluna), com base zero:
   ```python
   GRADE_UF = {
       "RR": (0, 1), "AP": (0, 3),
       "AM": (1, 1), "PA": (1, 2), "MA": (1, 3), "CE": (1, 4), "RN": (1, 5),
       "AC": (2, 0), "RO": (2, 1), "MT": (2, 2), "TO": (2, 3), "PI": (2, 4), "PE": (2, 5), "PB": (2, 6),
       "MS": (3, 2), "GO": (3, 3), "DF": (3, 4), "BA": (3, 5), "AL": (3, 6),
       "SP": (4, 3), "MG": (4, 4), "ES": (4, 5), "SE": (4, 6),
       "PR": (5, 3), "RJ": (5, 4),
       "SC": (6, 3),
       "RS": (7, 3),
   }
   ```
2. **Sempre mostre os 27 estados.** A função recebe `valores` de todos e um conjunto `realce` com as siglas da região filtrada. Os estados de fora ficam com `marker.opacity = 0.25`.
3. **Faixas fixas:** 5 intervalos iguais entre o mínimo e o máximo **dos 27 estados**, para as cores não mudarem quando o filtro de região muda. Mande a cor de cada ponto já calculada (`marker.color = [cor_hex, ...]`) e remova `colorscale` e `colorbar`.
4. Formato do marcador: `symbol="square"`, `size=54`. Teste a grade em 520px de altura; o objetivo é ter 6px de espaço entre os quadrados. Contorno de 4px em `--yellow` no estado selecionado e 0 nos outros.
5. Texto: `"<b>{UF}</b><br><span style='font-size:11px'>{fmt.pct(v)}</span>"`, com `textfont.color` por ponto (azul-marinho nas faixas 1 a 3, branco nas 4 e 5) e tamanho 13.
6. Eixos: `xaxis.range = [-0.6, 6.6]`, `yaxis.range = [7.6, -0.6]`, `scaleanchor="x"`, sem eixos visíveis, `height=560`.
7. Mantenha `on_select="rerun"` e o mapeamento de clique. Use `customdata` em vez do índice, porque agora a lista de pontos é sempre a dos 27.
8. **Legenda HTML** abaixo do gráfico, com até 420px de largura: 5 blocos de 12px de altura com 2px entre eles. Abaixo de cada bloco, o limite inferior da faixa (`fmt` com 1 casa decimal e vírgula). Título da legenda: "{Indicador} (%)".

**Lista ordenada.** Use `st.dataframe(..., on_select="rerun", selection_mode="single-row", key="mapa_lista", hide_index=True)` com estas colunas:
- `Posição` (`"{n}º"`)
- `UF`
- `Estado` (nome por extenso)
- uma `ProgressColumn` sem texto (`min_value=0`, `max_value=` o maior valor da lista)
- o valor já formatado com `fmt.pct`, como texto. Não use o `format` da `ProgressColumn`, porque ele mostra ponto decimal.

A seleção de uma linha atualiza `st.session_state["mapa_uf"]`. Na lista, o filtro de região **filtra** as linhas (no mapa, só esmaece). Remova o `expander` "Ver os mesmos dados em lista", porque a lista passa a ser uma visão de primeira classe.

**Municípios (choropleth).** Use as mesmas 5 faixas, calculadas sobre os municípios da UF, com `colorscale` discreta montada com pares de pontos repetidos. A legenda HTML é a mesma. Mantenha o aviso dos municípios sem polígono.

**Coluna 3: painel**
1. `st.selectbox("Estado", siglas, key="mapa_uf")`. Mantenha, porque é a alternativa de teclado ao clique nos quadrados. Mostre as opções como "SP · São Paulo".
2. Cartão "Estado selecionado":
   - Rótulo verde "ESTADO SELECIONADO".
   - Nome por extenso (Raleway 24px).
   - Valor (Raleway 40px/700, `--blue`) e "{Indicador} no {turno}º turno de {ano}" (14px).
   - Um `<dl>` em grade de 2 colunas, com divisória acima, contendo: Média nacional, Diferença (cor D5), Posição entre as UFs ("{n}º de 27") e Região.
   - Botão "Ver municípios de {UF}": contorno azul, raio de 999px, 44px, largura total. Ele continua chamando `_ver_municipios`.
3. Cartão "Maiores valores · {Brasil | Região X}": os 5 estados com maior valor dentro da região filtrada. Cada linha tem `grid-template-columns: 24px minmax(0,1fr) 56px`, com posição, nome e uma barra de 6px por baixo (largura relativa ao 1º colocado) e o valor em negrito.

### 5.4 Brasil em perspectiva (`telas/brasil.py`)
1. Cabeçalho e abertura.
2. Painel de filtros com `st.selectbox("Eleição", data.ELEICOES, key="brasil_eleicao")`, padrão `(2026, 1)`. **Isto é novo:** hoje a tela é fixa em 2026, 1º turno. Se o recorte escolhido não tiver dados, use `ui.aguardando`.
3. Linha de contexto.
4. Três `cartao_escopo`: Município, Estado (nome por extenso) e Brasil.
5. Duas colunas, `st.columns([3, 2], gap="large")`:
   - **Esquerda:** cartão "Indicador a indicador" com o subtítulo "{ano} · {turno}º turno", a legenda das séries à direita e 4 `bloco_indicador`:

     | Indicador | Escala (100% da barra) |
     |---|---|
     | Comparecimento | 100 |
     | Abstenção | o múltiplo de 5 acima de `1,5 × máximo` das três séries |
     | Votos válidos | 100 |
     | Brancos + nulos | o múltiplo de 5 acima de `1,5 × máximo` das três séries |

     As barras começam sempre do zero. Os deltas vêm de `{i}_delta_uf_pp` e `{i}_delta_brasil_pp`.
   - **Direita:**
     1. Cartão "Tendência do comparecimento", com o subtítulo "1º turno, 2022 → 2026" e o gráfico de inclinação (abaixo).
     2. `cartao_leitura(narrativa.leitura_rapida(...))`.
6. Remova o `expander` "Ver como tabela, com as diferenças", porque o próprio bloco já mostra os números e as diferenças. **Mantenha** a tabela da tendência num `expander` ("Ver como tabela"), porque o gráfico do Plotly não é acessível sozinho.

**Gráfico de inclinação (`charts.inclinacao`).** Corrija e simplifique:
- `xaxis=dict(type="category", categoryorder="array", categoryarray=["2022","2026"], showgrid=False, showline=False, tickfont=dict(size=13, color="#4A4F57"))`. **Isto resolve o bug do "2.022,5".**
- `yaxis=dict(visible=False)` e `showlegend=False`.
- Rótulo à esquerda (2022) só com o valor; rótulo à direita (2026) com `"{valor} {nome curto}"` ("76,4% Campinas", "77,5% SP", "79,2% Brasil"). Use `textposition` por ponto. Se dois rótulos ficarem a menos de 0,25 p.p. um do outro, desloque o de baixo com uma `annotation`, para não sobrepor.
- Linha de 3px, marcadores de 10px, Brasil com `dash="dash"`, `height=300` e margens `l=60, r=130, t=10, b=30`.
- Cor do texto de cada rótulo = cor da série. Para o Brasil, use `#4A4F57`, porque `#6B7280` fica abaixo de 4,5:1 em 13px.

---

## 6. Textos automáticos e formatação

### 6.1 `narrativa.py` (funções novas)
Todas usam `classificar()` com o limite de 0,5 p.p. que já existe. Elas devolvem texto simples; a interface cuida do HTML.

**`manchete_explore(nome, comp_pct, comp_delta_br, abst_delta_uf) -> dict`**
- `destaque` = `f"{round(comp_pct / 10)} em cada 10 eleitores votaram"`
- `antes`, conforme `classificar(comp_delta_br)`:
  - alta: `f"{nome} foi mais às urnas do que o Brasil:"`
  - queda: `f"{nome} foi menos às urnas do que o Brasil:"`
  - igual: `f"{nome} votou na mesma proporção que o Brasil:"`
- `depois`, conforme `classificar(abst_delta_uf)`:
  - queda: `", e a abstenção ficou abaixo da média do estado."`
  - alta: `", e a abstenção ficou acima da média do estado."`
  - igual: `", e a abstenção ficou na média do estado."`

Exemplo com os dados reais de Campinas, 1º turno de 2026: "Campinas foi menos às urnas do que o Brasil: **8 em cada 10 eleitores votaram**, e a abstenção ficou acima da média do estado."

**`manchete_comparativo(nome, aptos_base, aptos_comp, comp_delta, bn_delta) -> dict`**
- `antes`: `f"{nome} {ganhou|perdeu} {fmt.milhar_curto(abs(dif))} eleitores e"`. Com `dif == 0`: `f"{nome} manteve o número de eleitores e"`.
- `destaque`, conforme `classificar(comp_delta)`: "ficou mais participativa" / "ficou menos participativa" / "manteve o nível de participação".
- `depois`: `f": o comparecimento {narrativa de evolução sem o 'desde 2022'} e brancos e nulos {subiram X p.p. | caíram X p.p. | ficaram praticamente iguais}."`

Exemplo real: "Campinas perdeu 7,8 mil eleitores e **ficou menos participativa**: o comparecimento caiu 1,7 p.p. e brancos e nulos ficaram praticamente iguais."

**`entre_turnos(ano, comp_delta, bn_delta) -> str`**
"Em {ano}, o comparecimento {caiu|subiu} X p.p. do 1º para o 2º turno, e brancos e nulos {recuaram|aumentaram} Y p.p." Quando um dos dois for "igual", use "ficou praticamente igual" / "ficaram praticamente iguais".

**`votos(comparecimento, bn_delta_br) -> str`**
"Dos {comparecimento} votos registrados, a grande maioria foi para um candidato. Os brancos e nulos ficaram {X p.p. acima | X p.p. abaixo | praticamente iguais} {à média | da média} nacional." Os 2 casos não "igual" usam "da média nacional"; o caso "igual" usa "à média nacional".

Testes para cada função, cobrindo alta, queda e igual. Siga o padrão de `test_modelos_de_frase_cobrem_alta_queda_e_igual`.

**Linguagem.** Frases curtas, voz ativa, verbos concretos ("foram votar", "ficaram em casa"). Nada de adjetivo que julgue o resultado (bom, ruim, preocupante), em linha com a D5. Os textos continuam sujeitos à aprovação da tarefa 3.7.

### 6.2 `leitura_rapida`
Continua com 3 itens. Ajuste a redação para o tom das manchetes:
- "O comparecimento está 1,0 p.p. abaixo da média do estado." (mantém)
- Item de 2022: se mudou de lado em relação ao Brasil entre 2022 e 2026, prefira "Em 2022, {nome} votava {mais|menos} que a média do país. Em 2026, {passou à frente|ficou para trás}." Para isso, acrescente o parâmetro opcional `comp_delta_br_2022`. Sem ele, mantenha a frase atual.
- O item de brancos e nulos continua.

### 6.3 `fmt.py`
- `mil(valor)`: abaixo de 1.000, `inteiro`; de 1.000 a 999.999, `f"{round(v/1000)} mil"` ("873 mil"); a partir de 1 milhão, `milhoes()`.
- `milhar_curto(valor, casas=1)`: `"7,8 mil"`, `"31,6 mil"`; abaixo de 1.000, `inteiro`.
- Testes para os dois, em `test_formatacao_brasileira`.

---

## 7. Animações

**Princípio:** pouco movimento, sempre a serviço da leitura (mostrar a ordem dos blocos, o tamanho das barras e o achado principal). Nada em loop, exceto o indicador de "aguardando".

### 7.1 Regra 1: só no primeiro carregamento
O Streamlit refaz a página a cada interação. Animação de entrada que se repete a cada clique cansa. Use uma flag por tela e por município:
```python
def anima(pagina: str) -> str:
    """Devolve ' anima' só na primeira renderização desta tela para este município."""
    chave = f"_animou_{pagina}_{st.session_state.get('cd_ibge')}"
    if st.session_state.get(chave):
        return ""
    st.session_state[chave] = True
    return " anima"
```
Os componentes recebem a classe no contêiner externo, por exemplo `<section class="achado{anima}">`. Quando o município muda, a chave muda e a animação roda de novo, o que faz sentido porque os números são novos.

### 7.2 Regra 2: respeitar quem prefere menos movimento
Todo `@keyframes` e toda `animation` ficam dentro de `@media (prefers-reduced-motion: no-preference)`. O alto contraste também desliga as animações (`contraste.css`: `.anima, .anima * { animation: none !important; }`).

### 7.3 Catálogo

| # | Elemento | Efeito | Duração / atraso | Curva |
|---|---|---|---|---|
| A1 | Blocos da página (manchete, heróis, Leitura rápida, votos, tabelas e cartões do mapa) | Surgir: opacidade 0 → 1 e `translateY(8px)` → 0 | 320ms; atraso `var(--i) × 70ms`, com `--i` de 0 a 5 na ordem do HTML | `cubic-bezier(.2,.7,.2,1)` |
| A2 | Grifo da manchete (`.marca`) | O fundo amarelo "pinta" da esquerda para a direita: `background-size` de `0% 38%` para `100% 38%` | 700ms; atraso de 350ms (depois de a manchete aparecer) | `ease-out` |
| A3 | Barra empilhada de votos | Cada segmento cresce com `scaleX(0)` → 1 e `transform-origin: left`, um depois do outro | 600ms; atrasos de 200, 280 e 360ms | mesma de A1 |
| A4 | Barras de diferença (Comparativo) | Crescem **a partir da linha central**: `transform-origin: left` em `.up` e `right` em `.down` | 500ms; atraso por linha de `--i × 50ms` | mesma de A1 |
| A5 | Barras pareadas e barras do "Indicador a indicador" | `scaleX` de 0 → 1, da esquerda | 600ms; atraso por linha de 40ms | mesma de A1 |
| A6 | Barras do ranking "Maiores valores" | Como A5 | 500ms | mesma de A1 |
| A7 | Ponto de "aguardando" (novo: um círculo de 8px `--blue` antes do texto "Aguardando apuração") | Pulso de opacidade 1 → 0,35 → 1 | 1,6s, infinito | `ease-in-out` |
| A8 | Abas, links, pílulas, segmentados, linhas da lista | Transição de `color`, `background` e `border-color` | 150ms | `ease` |
| A9 | Botão "Ver municípios", "Baixar CSV" | Hover: fundo `--blue-soft`; ao pressionar, `transform: translateY(1px)` | 150ms | `ease` |
| A10 | Esqueleto de carregamento (já existe) | Mantém o brilho, mas envolto na regra de 7.2 | 1,2s | linear |

CSS de referência:
```css
@media (prefers-reduced-motion: no-preference) {
  .anima { animation: surgir 320ms cubic-bezier(.2,.7,.2,1) both; animation-delay: calc(var(--i, 0) * 70ms); }
  @keyframes surgir { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: none; } }

  .anima .marca { background-size: 0% 38%; animation: grifar 700ms 350ms ease-out forwards; }
  @keyframes grifar { to { background-size: 100% 38%; } }

  .anima .barra span, .anima .barra-h > i { transform-origin: left; animation: crescer 600ms cubic-bezier(.2,.7,.2,1) both;
    animation-delay: calc(200ms + var(--j, 0) * 80ms); }
  .anima .dif b.up   { transform-origin: left;  animation: crescer 500ms cubic-bezier(.2,.7,.2,1) both; animation-delay: calc(var(--j,0) * 50ms); }
  .anima .dif b.down { transform-origin: right; animation: crescer 500ms cubic-bezier(.2,.7,.2,1) both; animation-delay: calc(var(--j,0) * 50ms); }
  @keyframes crescer { from { transform: scaleX(0); } to { transform: scaleX(1); } }

  .ponto-aguardando { animation: pulsar 1.6s ease-in-out infinite; }
  @keyframes pulsar { 50% { opacity: .35; } }
}
```
`--i` e `--j` são definidos inline (`style="--i:2"`) ao gerar o HTML. Em `.dif b.down`, o preenchimento precisa estar ancorado em `right: 50%` (já está), senão o `transform-origin: right` cresce do lado errado.

### 7.4 O que **não** fazer
- **Contagem animada dos números grandes (count-up).** Leitores de tela leriam valores intermediários e o efeito se repetiria em cada rerun. O número aparece pronto, só com o A1.
- **Transições do Plotly** (`layout.transition`). O Streamlit recria o gráfico a cada rerun e o efeito não acontece de forma confiável. A troca de indicador no mapa é instantânea.
- **Animação de rolagem (parallax ou aparecer ao rolar).** Exigiria JavaScript.
- **Esmaecimento padrão do Streamlit durante o rerun:** suavize para não "piscar" a página toda. Use `[data-stale="true"] { opacity: .75 !important; transition: opacity .2s; }`, depois de conferir no DOM da 1.58 o atributo que o Streamlit usa.

---

## 8. Acessibilidade e responsivo

1. Contraste mínimo de 4,5:1 para texto e 3:1 para bordas de campos e elementos gráficos que carregam informação. Pares a conferir:
   - `#4A4F57` sobre `#F5F7FA`
   - `#6B4E00` sobre `#FFF4CC`
   - `#0E5C31` sobre `#E3F2E8`
   - branco sobre `#2F6BBE`
   - azul-marinho sobre `#6F9BD6`
   - `#C9D3E3` sobre `#071D41`
2. Ordem dos títulos: um H1 por tela; manchete e títulos de seção em H2; títulos de cartão em H3.
3. Toda variação traz seta **e** sinal. Toda barra ou gráfico tem texto equivalente (`aria-label`, tabela ou o número ao lado).
4. Foco visível amarelo (já existe) em todos os controles novos, inclusive pílulas e linhas da lista.
5. Cores que precisam ser diferenciadas também diferem em luminosidade: 1º turno `#0B4EA2` × 2º turno `#7FA6D8`, e as 5 faixas do mapa.
6. Responsivo:

   | Largura | Comportamento |
   |---|---|
   | ≥ 1024px | Layouts como descritos |
   | 641 a 1023px | Heróis em 2 colunas com a Leitura rápida embaixo; mapa em 2 colunas (filtros em cima) |
   | ≤ 640px | Tudo em 1 coluna. Manchete 26px, H1 28px, número principal 48px. Grade de comparações dos heróis continua com 3 colunas, em 12px. Quadrados do mapa com `size=40` e altura de 440. Tabelas com rolagem horizontal |

7. Alto contraste: atualize `contraste.css` com os novos seletores (`.heroi`, `.achado`, `.marca`, `.escopo`, `.st-key-filtros`, `.st-key-rodape`, `.st-key-utilitaria`, pílulas e segmentados).

---

## 9. Testes e critérios de aceite

### 9.1 Testes automatizados
- Todos os testes atuais continuam passando, com as chaves `explore_eleicao`, `mapa_nivel` e `mapa_visao` mantidas. O texto "Aguardando apuração" continua presente, assim como "única zona eleitoral" e "não encontrado".
- Acrescente:
  1. Frases de `manchete_explore`, `manchete_comparativo`, `entre_turnos` e `votos`, nos 3 casos cada.
  2. `fmt.mil` e `fmt.milhar_curto`.
  3. `charts.grade_ufs` devolve 27 pontos com qualquer filtro de região, e só os da região com opacidade 1.
  4. `charts.inclinacao` usa eixo X do tipo `category`.
  5. A tela `brasil` com `brasil_eleicao = (2026, 2)` mostra o estado de aguardando, sem exceção.
  6. Abrir o app sem caminho renderiza o Explore.
- `ruff` limpo.

### 9.2 Aceite visual (tarefa 3.0)
Rode `python -m streamlit run app/Home.py` e salve capturas de tela em `docs/design/aceite/`:

- Telas: `explore`, `comparativo`, `mapa` (visão mapa e visão lista) e `brasil`.
- Larguras: **1280px** e **390px**.
- Municípios: **Campinas (3509502)** e **um município de zona única**.
- Uma versão com **alto contraste**.

Confira item por item contra o protótipo:
- [ ] Logo nova no cabeçalho e no favicon
- [ ] Inter no texto corrido e Raleway nos títulos e números (conferir no DOM: nenhum `p` em Source Sans)
- [ ] Barra utilitária, faixa 3 : 1 : 3, busca em pill e abas sublinhadas
- [ ] H1 da tela, parágrafo de abertura e linha de contexto em todas as telas
- [ ] Filtros visíveis em painel (Explore, Mapa, Brasil)
- [ ] Manchete com grifo no Explore e no Comparativo
- [ ] Dois heróis e a Leitura rápida na mesma linha (desktop)
- [ ] Bloco de votos com brancos em amarelo
- [ ] Tabela de zonas em cartão, com "Baixar CSV" no cabeçalho
- [ ] Turnos com barras pareadas e etiquetas de status
- [ ] Mapa em 3 colunas, 5 faixas, valores nos quadrados e região esmaecendo
- [ ] Ranking "Maiores valores"
- [ ] Cartões de escopo com borda colorida; "Indicador a indicador" em HTML
- [ ] Gráfico de inclinação só com 2022 e 2026, sem "2.022,5"
- [ ] Rodapé num bloco azul-marinho único
- [ ] Animações só no primeiro carregamento e desligadas com `prefers-reduced-motion`

Atualize `docs/planejamento.md` (tarefa 3.0) e `docs/design/tokens.md` (seção 2.1).

---

## 10. Divergências conhecidas (o que vale)

| Tema | Protótipo | O que fazer |
|---|---|---|
| Cor das comparações nos heróis | Verde para tudo que é "melhor" | **D5:** azul ▲ / laranja ▼ |
| Botões "Consultar", "Comparar" e "Atualizar" | Aparecem | **D8:** não implementar; os filtros aplicam na hora |
| Selects de ano no Comparativo | Ano base e comparação editáveis | **D4:** fixo; mostrar só na linha de contexto |
| Selo "Dados ilustrativos" | Aparece | Não implementar (dados reais) |
| Indicadores no mapa | 3 | Manter os 6 do app |
| Nível "Municípios" | Só desenhado | Manter o choropleth que já funciona |
| Seletor "Estado" no painel do mapa | Não existe | Manter (alternativa de teclado) |
| Zonas descritas como bairros | Não se aplica | Nunca chamar zona eleitoral de bairro |

Fim da especificação.
