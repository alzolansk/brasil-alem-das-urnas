# Aceite visual (25/10/2026)

Capturas feitas com Playwright no Chrome instalado (a extensão Claude in Chrome não respondeu), app rodando localmente, movimento reduzido ligado para as imagens ficarem estáveis. Larguras de 1280px e 390px; municípios Campinas (3509502) e Lagoa do Piauí (2205508, zona única). Em todas as capturas: **sem rolagem horizontal** e **nenhum `p` em Source Sans** (conferido no DOM).

| Arquivo | O que mostra |
|---|---|
| `{explore,comparativo,mapa,brasil}_{campinas,zona-unica}_{1280,390}.png` | As 4 telas |
| `mapa-lista_*` | Mapa na visão "Lista ordenada" |
| `explore_campinas_*_alto-contraste.png` | Alto contraste |
| `e100-detalhe_campinas_*` | Bloco de 100 eleitores com o detalhe aberto |
| `e100-indisponivel_boa-esperanca_*` | Estado indisponível (Boa Esperança do Norte/MT em 2022) |
| `loader_parado*.png` / `loader_animado.png` | Loader de tela cheia e compactos, sem e com movimento |

## Seção 9.2
- [x] Logo nova no cabeçalho (favicon: não verificável em captura headless)
- [x] Inter no texto e Raleway nos títulos e números; nenhum `p` em Source Sans
- [x] Barra utilitária, faixa 3 : 1 : 3, busca em pílula e abas sublinhadas
- [x] H1, abertura e linha de contexto em todas as telas
- [x] Filtros em painel (Explore, Mapa, Brasil)
- [x] Manchete com grifo no Explore e no Comparativo
- [x] Dois heróis e a Leitura rápida na mesma linha (1280px)
- [x] Bloco "Sua cidade em 100 eleitores" no lugar da barra de votos
- [x] Tabela de zonas em cartão com "Baixar CSV"; zona única mostra a nota
- [x] Turnos com barras pareadas e etiquetas de status
- [x] Mapa em 3 colunas, 5 faixas, região esmaecendo (mapa por estados com a malha do IBGE, não mais quadrados)
- [x] Ranking "Maiores valores"
- [x] Cartões de escopo e "Indicador a indicador" em HTML
- [x] Inclinação só com 2022 e 2026
- [x] Rodapé azul-marinho único
- [ ] Animações só no 1º carregamento: coberto pela flag `ui.anima`, não conferido em vídeo

## Seção 11.4 (loader)
- [x] `pathLength` preservado pelo `st.markdown` do Streamlit 1.58 (conferido no DOM); `role="status"`
- [x] Com movimento reduzido fica parado (`animation-name: none`); sem ele, `bau-tracar` roda
- [x] Some quando os dados chegam (teste `test_loader_some_depois_de_carregar` nas 4 telas)
- [ ] Aparecer com cache frio e o compacto ao trocar para "Municípios": é transitório, conferir a olho reiniciando o app

## Seção 12.9 (100 eleitores)
- [x] Entre a grade de cartões e "Zona por zona"; barra empilhada removida
- [x] 100 pontos na ordem válidos, brancos, nulos e abstenção; legenda soma 100; percentuais sobre os aptos
- [x] Trocar 2022 / 2026 muda só o bloco (`@st.fragment`) e o texto "Exibindo"
- [x] Detalhe com o denominador e os percentuais entre quem votou
- [x] Indisponível em Boa Esperança do Norte em 2022; em 2026 2º turno a página mostra o aviso de apuração (testes)
- [x] Em 390px: título e seletor, grade, texto e legenda, sem rolagem horizontal
- [x] Frase-resumo em parágrafo escondido com `aria-live`; grade com `aria-hidden`
- [x] Com movimento reduzido a troca é instantânea (transição só dentro de `prefers-reduced-motion: no-preference`)

## Observações
- O segmentado "Nível" do Mapa quebra em duas linhas na coluna estreita de filtros a 1280px (anterior a esta etapa).
- A transição de cor dos pontos (A3) depende de o Streamlit reaproveitar o HTML; não foi conferida em vídeo.
