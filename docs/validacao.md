# Validação contra números oficiais do TSE

Preenchimento manual (tarefas 2.4 e 4.3). Compare o valor calculado pelo pipeline com o painel oficial de resultados do TSE.

| Data | Eleição | Turno | Recorte | Indicador | Pipeline | TSE oficial | Diferença | OK? | Observação |
|---|---|---|---|---|---|---|---|---|---|
| 25/10/2026 | 2022 | 1º | Brasil (com exterior) | Eleitores aptos | 156.454.011 | 156.454.0xx (cortado na captura) | a confirmar | ? | Soma BRASIL + EXTERIOR; teste 06 já confere este valor |
| 25/10/2026 | 2022 | 1º | Brasil (com exterior) | Comparecimento | 123.682.372 | 123.714.335 | −31.963 (−0,026%) | ❌ | Idem |
| 25/10/2026 | 2022 | 1º | Brasil (com exterior) | Abstenção | 32.771.639 | pendente | | | Inclui 657 eleitores de seções não instaladas |
| 25/10/2026 | 2022 | 2º | Brasil (com exterior) | Comparecimento | 124.252.796 | 124.267.614 | −14.818 (−0,012%) | ❌ | |
| 25/10/2026 | 2026 | 1º | Brasil (com exterior) | Comparecimento | 125.275.835 | 125.277.230 | −1.395 (−0,001%) | ❌ | |
| | | | UF: | | | | | | |
| | | | Município: | | | | | | |

## Divergências encontradas
<!-- Descrever a causa e a decisão tomada (tarefa 2.5). -->
**Comparecimento do Brasil, 3 recortes (25/10/2026).** O pipeline fica sempre abaixo do painel de comparecimento/abstenção do TSE: 2022 1º turno −31.963; 2022 2º turno −14.818; 2026 1º turno −1.395.
- **Causa confirmada: são duas bases diferentes do TSE.** O pipeline usa `detalhe_votacao_munzona` (resultados): comparecimento 123.682.372 = válidos 118.229.719 + brancos 1.964.779 + nulos 3.487.874. O painel usa `perfil_comparecimento_abstencao`. Somando esse dataset, as mesmas 18.858 zonas (nenhuma a mais ou a menos) reproduzem o painel exatamente: 123.714.335, 124.267.614 e 125.277.230 de comparecimento; 156.454.011 aptos em 2022 e 158.745.463 em 2026.
- Onde está a diferença (comparecimento, pipeline − perfil): 2022 1º turno concentrada no exterior (−32.874; DF +3.860); 2022 2º turno exterior −2.678 e DF +3.595; 2026 exterior −2.895 e DF +5.052. No resto do país, as diferenças são pequenas e dispersas (mediana de 12 eleitores a menos por zona em 2026). Os aptos também diferem zona a zona, nos dois sentidos, e quase se anulam no total (2026: +39). O dataset de perfil parece alocar eleitores às zonas por critério diferente do boletim de urna (por exemplo, voto fora do domicílio eleitoral); o TSE não documenta o critério, então isto é inferência.
- Os números anunciados do resultado (123.682.372 em 2022) coincidem com o pipeline; os do painel, com o perfil. Ambos são oficiais.
- **Decisão:** manter `detalhe_votacao_munzona`. Só ele traz válidos, brancos e nulos, que somam exatamente o comparecimento. A diferença para o painel é inferior a 0,03% no Brasil e vira nota de rodapé do app ("os números podem diferir ligeiramente do painel de comparecimento do TSE, que usa outra base"). Para zonas do exterior e do DF a diferença relativa é maior (exterior 2022 1º turno: ~10%); o app deve mostrar essa nota junto do exterior.
- Os totais do painel serão reconferidos se o app passar a exibir comparecimento por perfil.

## Abstenção × aptos (bloco "Sua cidade em 100 eleitores", 25/10/2026)
Em `mart_municipio_benchmark`, `comparecimento = válidos + brancos + nulos` nas 16.711 linhas, mas `abstenções + comparecimento ≠ aptos` em 2 linhas:

| Eleição | Município | Aptos | Comparecimento | Abstenções | Seções não instaladas |
|---|---|---|---|---|---|
| 2022, 1º turno | Manaus (AM) | 1.418.757 | 1.202.632 | 216.041 | 84 |
| 2022, 2º turno | Manaus (AM) | 1.418.871 | 1.190.953 | 227.834 | 84 |

A diferença é exatamente a dos eleitores de seções não instaladas, que o TSE não conta como abstenção (`aptos = comparecimento + abstenções + seções não instaladas`, como na metodologia). No bloco de 100 eleitores, "Não compareceram" usa `aptos − comparecimento` para os quatro grupos somarem 100%, e por isso inclui esses 84 eleitores. Os cartões de abstenção continuam com o número do TSE.
