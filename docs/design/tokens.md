# Tokens visuais

Referência visual: canvas de Design "Brasil Além das Urnas" (4 artboards), que substitui o [prototipo-2.pdf](prototipo-2.pdf). Especificação completa em [especificacao-fidelidade-prototipo.md](especificacao-fidelidade-prototipo.md). O [prototipo-1.pdf](prototipo-1.pdf) é histórico.

## Cores
| Token | Valor | Uso |
|---|---|---|
| `--navy` | `#071D41` | Títulos, números de destaque, rodapé, cartão "Leitura rápida" |
| `--blue` | `#0B4EA2` | Ações, links, aba ativa, série **Município**, aumento ▲ |
| `--blue-hover` | `#073A7A` | Hover de links e botões |
| `--blue-soft` | `#EEF4FC` | Item selecionado, fundo de aviso |
| `--blue-2t` | `#7FA6D8` | Barra do 2º turno |
| `--green` | `#12753E` | Série **Estado**, votos válidos, rótulos de seção |
| `--green-text` | `#0E5C31` | Texto verde sobre fundo claro |
| `--green-soft` | `#E3F2E8` | Fundo da etiqueta "Apuração concluída" |
| `--yellow` | `#F5C400` | Faixa, votos brancos, numeração da Leitura rápida, foco e seleção |
| `--yellow-soft` | `#FCE79A` | Grifo da manchete |
| `--yellow-tag` | `#FFF4CC` · texto `#6B4E00` · borda `#E8C84A` | Etiqueta "2º turno em 25/10" |
| `--orange` | `#C2410C` | Votos nulos, queda ▼ |
| `--gray` | `#6B7280` | Série **Brasil** (texto do Brasil em `#4A4F57`) |
| `--text` | `#1B1B1B` | Texto corrido |
| `--muted` / `--caption` | `#3A3F47` / `#4A4F57` | Texto secundário / legendas |
| `--border` / `--divider` | `#DCDFE4` / `#E6E8EC` | Bordas de cartão / divisórias internas |
| `--input-border` | `#888F99` | Borda de campos |
| `--bg-soft` | `#F5F7FA` | Barra utilitária, filtros, bloco de votos |
| `--track` | `#F1F3F6` | Fundo das barras |
| `--on-dark-muted` | `#C9D3E3` | Texto secundário no rodapé |

Faixa no topo: 4px, verde · amarelo · azul na proporção 3 : 1 : 3.

Escala do mapa (5 faixas, menor → maior): `#DCE7F5` `#A9C4E8` `#6F9BD6` `#2F6BBE` `#0B3F86`. Texto azul-marinho nas faixas 1–3, branco nas 4–5.

`--yellow` nunca é cor de texto sobre branco; texto sobre amarelo é sempre `--navy`.

## Séries fixas
**Município = azul · Estado = verde · Brasil = cinza**, iguais em todas as telas. Na tendência, o Brasil é tracejado.

## Variações (D5)
Azul ▲ aumentou, laranja ▼ diminuiu, sempre com seta e sinal. A cor indica só a direção.

## Tipografia
- Títulos e números: Raleway (600–800). H1 36px, manchete 34px (32px no Comparativo), número principal 64px/800.
- Texto: Inter (400–700), 15px/1.5. Legendas 13–14px.
- Números com `font-variant-numeric: tabular-nums`.

## Espaço e forma
Largura máxima de 1200px; 32px entre blocos. Raios: campos 6px, cartões 12px, destaques 16px, pílulas 999px. Cartões com borda e sem sombra; a única sombra é a do cabeçalho.

## Formatação de números
`79,4%` · `863.412` · `+0,9 p.p.` · `−0,9 p.p.` · `873 mil` · `7,8 mil` · `34,8 milhões`
