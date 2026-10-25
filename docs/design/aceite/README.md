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
| `loader-1500ms/*.png` / `loader-1500ms/tempos.json` | Abertura real com mínimo de 1,5 s: servidor frio/aquecido, movimento reduzido e alto contraste; tempos medidos no Chrome |

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
- [x] Camada inicial espera **1,5 s no navegador e conteúdo pronto**; o pedido atual substitui a regra antiga de sumir imediatamente. AppTest verifica presença só na primeira execução, sem provar duração no navegador
- [x] Servidor reiniciado: 1.510 ms de exibição; aquecido: 1.516 ms; recarregamento de rota interna: 1.518 ms. Sondagem por mutações do DOM e quadros, com tolerância de um quadro a 60 Hz
- [x] Conteúdo já pronto em cenário isolado: ~1,5 s (1.492 ms amostrados); conteúdo atrasado além do mínimo: camada permanece até a chegada dele (~2.160 ms no ensaio)
- [x] Compacto visível ao trocar para "Municípios", oculto após desenhar o SVG do Plotly da execução atual (~220 ms visível no ensaio aquecido)
- [x] Troca de abas sem camada inicial, inclusive a primeira; entrada pela direita (Explore → Mapa, Comparativo → Brasil) e esquerda (Mapa → Comparativo), 420 ms; topo sem deslocamento
- [x] Chrome com movimento reduzido: contorno sem animação e navegação sem `entrar-*`; largura 390 px com alto contraste: camada preta, oculta ao concluir, sem rolagem horizontal (também conferido em 1280 px)
- [x] Abertura parada em 390 px: 1.557 ms com movimento reduzido e 1.561 ms com alto contraste; mapa completo, oito capitais e primeira frase visíveis. Sem movimento, o temporizador continua contando
- [ ] Cobrir o intervalo anterior à montagem do HTML/CSS: limitação ainda presente do Streamlit; podem aparecer widgets sem estilo personalizado

Regra de 1,5 s verificada em 25/10/2026 com Chrome local via Playwright; 85 testes e Ruff passam. Capturas atuais em `loader-1500ms/`, feitas aproximadamente um segundo após a camada aparecer (o ciclo visual de 3,6 s ainda está em andamento nas versões animadas). As imagens `loader_*.png` anteriores mostram o componente isolado.

Reproduzir: iniciar `python -m streamlit run app/Home.py --server.port 8599 --server.headless true --server.runOnSave false`, depois `python tests/browser/verificar_loader.py --saida <pasta>`. A sondagem usa Playwright e o Chrome instalados no ambiente de aceite; eles não são dependências do app nem da suíte pytest. Para o primeiro cenário representar cache frio, reiniciar o processo do Streamlit antes de executar. O teste também confere que a camada não reaparece ao navegar para Mapa e Comparativo.

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
