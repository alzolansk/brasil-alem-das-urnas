# Metodologia

> **Rascunho.** As fórmulas abaixo são uma proposta e precisam de aprovação (tarefa 0.5).

## Escopo
- Cargo: Presidente da República.
- Eleições: 2022 e 2026, 1º e 2º turnos.
- Granularidade: zona eleitoral, agregada para município, UF e Brasil.
- Fonte: Portal de Dados Abertos do TSE (resultados e comparecimento/abstenção); IBGE (municípios e malhas).

## Indicadores

| Indicador | Fórmula | Base |
|---|---|---|
| Comparecimento % | comparecimento ÷ eleitores aptos | aptos |
| Abstenção % | abstenções ÷ eleitores aptos | aptos |
| Votos válidos % | votos nominais ÷ comparecimento | comparecimento |
| Votos brancos % | brancos ÷ comparecimento | comparecimento |
| Votos nulos % | nulos ÷ comparecimento | comparecimento |
| Brancos + nulos % | (brancos + nulos) ÷ comparecimento | comparecimento |

- Na eleição presidencial não há voto de legenda, então válidos = votos nominais.
- **Variação de taxas** (2022 → 2026, 1º → 2º turno, município − UF): em **pontos percentuais (p.p.)**, que são a diferença simples entre duas porcentagens. Exemplo: de 78,5% para 79,4% = +0,9 p.p.
- **Variação de contagens** (eleitores aptos): em % relativa.
- **UF e Brasil**: razão das somas (ponderada pelos eleitores aptos), não média simples dos municípios.

## Colunas do TSE usadas (`detalhe_votacao_munzona`)
| Indicador | Coluna |
|---|---|
| Eleitores aptos | `QT_APTOS` |
| Comparecimento | `QT_COMPARECIMENTO` |
| Abstenção | `QT_ABSTENCOES` |
| Válidos | `QT_TOTAL_VOTOS_VALIDOS` |
| Brancos | `QT_VOTOS_BRANCOS` |
| Nulos | `QT_TOTAL_VOTOS_NULOS` (= `QT_VOTOS_NULOS` + `QT_VOTOS_NULOS_TECNICOS`) |

## Verificações de consistência
Conferidas nos arquivos de 2022 (1º e 2º turnos) e 2026 (1º turno), nas linhas de Presidente:
- aptos = comparecimento + abstenções + `QT_ELEITORES_SECOES_NAO_INSTALADAS`
  - Seções não instaladas quase só no exterior: 657 eleitores em 2022 e 423 em 2026. Fora delas, aptos = comparecimento + abstenções vale em todas as linhas.
- comparecimento = válidos + brancos + nulos + anulados + apurados em separado (vale em 100% das linhas; anulados e apurados em separado são 0 para Presidente)
- soma das zonas = total do município

Totais do Brasil (com exterior), 1º turno de 2022: 156.454.011 aptos e 123.682.372 de comparecimento, coerentes com os números oficiais divulgados pelo TSE (conferência formal pendente em `docs/validacao.md`).

## Decisões tomadas
| Tema | Decisão | Data |
|---|---|---|
| Anulados / apurados em separado | São 0 para Presidente em 2022 e 2026; sem tratamento. O teste de consistência avisa se isso mudar no 2º turno de 2026 | 25/10/2026 |
| Nulos técnicos | Contam como nulos (usar `QT_TOTAL_VOTOS_NULOS`, como o TSE). Afeta só 2026: 5.246 votos no 1º turno | 25/10/2026 |
| Exterior (`SG_UF = ZZ`) | Fora do mapa e fora da média "Brasil" usada nas comparações com municípios e UFs, porque o município se compara com o território nacional. Aparece à parte, como "Eleitores no exterior". A validação contra o TSE soma o exterior, porque o total oficial o inclui | 25/10/2026 |
| Boa Esperança do Norte (MT, código TSE 73709) | Município instalado após 2022: mostra só 2026, com a nota "município instalado após 2022; não há dados de 2022 para comparar". Os municípios de origem recebem a nota de que perderam eleitores para o novo município | 25/10/2026 |
| Diferença para o painel do TSE | O pipeline usa `detalhe_votacao_munzona`; o painel de comparecimento/abstenção usa `perfil_comparecimento_abstencao`. Diferença no Brasil: menos de 0,03% (maior no exterior). Mantida a fonte de resultados; nota no app. Detalhes em `docs/validacao.md` | 25/10/2026 |
| "Praticamente igual" nos textos automáticos | Diferença absoluta menor que 0,5 p.p. entre duas taxas. Decidido em 25/10/2026 (valor proposto no rascunho, mantido) | 25/10/2026 |
| Municípios de origem de Boa Esperança do Norte | Sorriso e Nova Ubiratã (Lei estadual 7.264/2000, validada pelo STF em 2023). A nota de perda de eleitores vai nesses dois municípios | 25/10/2026 |
| Rezoneamento (32 municípios com zonas criadas ou extintas) | A comparação 2022 × 2026 é feita só no nível do município. A tabela "Zona por zona" mostra apenas o ano selecionado, sem variação entre anos | 25/10/2026 |

## Decisões pendentes 🧑
Nenhuma.

## Limitações
- A abstenção inclui eleitores que morreram ou mudaram de domicílio e ainda constam no cadastro, o que infla a taxa sobretudo onde o cadastro está desatualizado.
- O voto é facultativo para quem tem 16–17 anos ou mais de 70, o que afeta a comparação entre municípios com perfis de idade diferentes.
- Os resultados descrevem o comportamento agregado, não as razões individuais do voto ou da abstenção.
