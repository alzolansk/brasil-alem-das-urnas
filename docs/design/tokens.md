# Tokens visuais

Extraídos de [prototipo-2.pdf](prototipo-2.pdf), que é a referência visual. O [prototipo-1.pdf](prototipo-1.pdf) é histórico.

## Cores
| Token | Valor | Uso |
|---|---|---|
| `--navy` | `#0B1F45` | Títulos, rodapé, cartão "Leitura rápida" |
| `--blue` | `#1550A8` | Ações, aba ativa, série **Município**, aumento ▲ |
| `--green` | `#1B7A3A` | Série **Estado**, votos válidos |
| `--yellow` | `#F2C200` | Destaques de texto, numeração da leitura rápida |
| `--orange` | `#C8401A` | Votos nulos, queda ▼ |
| `--gray` | `#6B7280` | Série **Brasil** |
| `--bg-soft` | `#F5F7FA` | Painéis de filtro, faixas |
| `--border` | `#E3E7EE` | Bordas de cartões |

Faixa no topo: verde · amarelo · azul.

Valores aproximados, tirados do PDF. Conferir o contraste (mínimo de 4,5:1 para texto) no spike (tarefa 3.0).

## Séries fixas
**Município = azul · Estado = verde · Brasil = cinza**, iguais em todas as telas.

## Variações (decisão D5, pendente)
Proposta neutra: azul ▲ aumentou, laranja ▼ diminuiu, sempre com seta e sinal. A cor indica só a direção, sem julgar se a mudança é boa ou ruim.

## Tipografia
- Títulos: Raleway (600–700)
- Texto: Inter (400–600)
- Número de destaque: 48px ou mais, peso 700

## Formatação de números
`79,4%` · `863.412` · `+0,9 p.p.` · `−0,9 p.p.` (sinal de menos tipográfico) · `34,8 milhões`

## Componentes
Cartão de indicador · Cartão "Leitura rápida" · Barra empilhada válidos/brancos/nulos · Tabela com barra de diferença · Barras horizontais agrupadas · Gráfico de inclinação 2022→2026 · Grade de UFs · Botões segmentados · Selo de status · Selo "Dados ilustrativos"
