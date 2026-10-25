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

Totais do Brasil + Exterior (linha `BRASIL` das marts), 1º turno de 2022: 156.454.011 aptos e 123.682.372 de comparecimento, coerentes com os números oficiais divulgados pelo TSE (conferência formal pendente em `docs/validacao.md`).

## Decisões tomadas
| Tema | Decisão | Data |
|---|---|---|
| Anulados / apurados em separado | São 0 para Presidente em 2022 e 2026; sem tratamento. O teste de consistência avisa se isso mudar no 2º turno de 2026 | 25/10/2026 |
| Nulos técnicos | Contam como nulos (usar `QT_TOTAL_VOTOS_NULOS`, como o TSE). Afeta só 2026: 5.246 votos no 1º turno | 25/10/2026 |
| Exterior (`SG_UF = ZZ`) | Fora do mapa e dos municípios, mas **dentro do total "Brasil"** (linha `BRASIL` de `mart_uf_brasil_indicadores`), que passa a bater com o total oficial do TSE. O app indica "Brasil + Exterior" onde mostra o total nacional. O exterior segue também à parte, na linha `EXTERIOR`. Substitui a decisão anterior (exterior fora da média "Brasil"), que deixava a abstenção de 2026 em 20,84% contra 21,08% do TSE | 25/10/2026 |
| Boa Esperança do Norte (MT, código TSE 73709) | Município instalado após 2022: mostra só 2026, com a nota "município instalado após 2022; não há dados de 2022 para comparar". Os municípios de origem recebem a nota de que perderam eleitores para o novo município | 25/10/2026 |
| Diferença para o painel do TSE | O pipeline usa `detalhe_votacao_munzona`; o painel de comparecimento/abstenção usa `perfil_comparecimento_abstencao`. Diferença no Brasil: menos de 0,03% (maior no exterior). Mantida a fonte de resultados; nota no app. Detalhes em `docs/validacao.md` | 25/10/2026 |
| "Praticamente igual" nos textos automáticos | Diferença absoluta menor que 0,5 p.p. entre duas taxas. Decidido em 25/10/2026 (valor proposto no rascunho, mantido) | 25/10/2026 |
| Municípios de origem de Boa Esperança do Norte | Sorriso e Nova Ubiratã (Lei estadual 7.264/2000, validada pelo STF em 2023). A nota de perda de eleitores vai nesses dois municípios | 25/10/2026 |
| Rezoneamento (32 municípios com zonas criadas ou extintas) | A comparação 2022 × 2026 é feita só no nível do município. A tabela "Zona por zona" mostra apenas o ano selecionado, sem variação entre anos | 25/10/2026 |

## Decisões pendentes 🧑
Nenhuma.

## Limitações
- A abstenção inclui eleitores que morreram ou mudaram de domicílio e ainda constam no cadastro, o que infla a taxa sobretudo onde o cadastro está desatualizado.
- O voto é facultativo para quem tem 16–17 anos, para quem tem 70 anos ou mais e para analfabetos (Constituição, art. 14, § 1º, II), o que afeta a comparação entre municípios com perfis de idade diferentes.
- Os resultados descrevem o comportamento agregado, não as razões individuais do voto ou da abstenção.

## Quem ficou em casa? (abstenção por perfil do eleitor)

### Fonte e cobertura
- Conjunto do TSE `perfil_comparecimento_abstencao` (o mesmo do painel oficial de comparecimento e abstenção), arquivo nacional `perfil_comparecimento_abstencao_<ano>_BRASIL.csv`. Usa-se o nacional porque o zip de 2022 não tem arquivos próprios para DF e exterior. Configuração em `ingestion/sources.yaml`.
- Disponível: **2022, 1º e 2º turnos** (arquivo gerado em 29/04/2025) e **2026, 1º turno** (gerado em 13/10/2026). O perfil do 2º turno de 2026 ainda não foi publicado; a tela avisa e não estima nada.
- Cada linha é uma combinação de zona × gênero × estado civil × faixa etária × escolaridade × cor/raça × demais campos do cadastro. **Não há linhas de total.** Somar as linhas de uma dimensão reproduz o total do município, sem dupla contagem; o pipeline confere isso para as três dimensões em todos os municípios.
- Municípios: 5.570 em 2022 e 5.571 em 2026, casados 100% com o IBGE pela tabela oficial do TSE. O exterior (`ZZ`) fica fora da tela, que é municipal.

### Colunas usadas
| Uso | Coluna do TSE |
|---|---|
| Eleitores aptos | `QT_APTOS` |
| Compareceram | `QT_COMPARECIMENTO` |
| Não compareceram | `QT_ABSTENCAO` |
| Gênero | `CD_GENERO` / `DS_GENERO` |
| Faixa etária | `CD_FAIXA_ETARIA` / `DS_FAIXA_ETARIA` |
| Escolaridade | `CD_GRAU_ESCOLARIDADE` (2022) ou `CD_GRAU_INSTRUCAO` (2026): mesmos códigos e descrições |

Em todas as linhas dos dois anos, `QT_APTOS = QT_COMPARECIMENTO + QT_ABSTENCAO` (aqui não há "seções não instaladas" à parte) e não há contagens negativas.

### Categorias (oficiais do TSE, sem reagrupamento)
- **Gênero:** Feminino, Masculino, além de "Não informado" (23.336 eleitores no total nacional com exterior, em 2026). É o campo "gênero" do cadastro. O campo de identidade de gênero ficou de fora: em 2022 está todo "não informado" e em 2026, em 79% dos eleitores.
- **Faixa etária:** 16, 17, 18, 19 e 20 anos isolados; depois 21 a 24, 25 a 29 … 95 a 99 anos e 100 anos ou mais (22 faixas), além de "Inválido" (1.212 eleitores no total nacional, em 2026). Voto facultativo marcado para 16, 17 e 70 anos ou mais (Constituição, art. 14, § 1º, II). **Exceção:** analfabetos também têm voto facultativo, em qualquer idade. Por isso, as faixas de 18 a 69 anos não reúnem só quem é obrigado a votar; a tela fala em "faixas de 18 a 69 anos", nunca em "voto obrigatório".
- **Escolaridade:** Analfabeto (marcado como voto facultativo), Lê e escreve, Ensino fundamental incompleto/completo, Ensino médio incompleto/completo, Superior incompleto/completo, além de "Não informado".
- **Filtros de voto facultativo:** nas seções de faixa etária, de escolaridade e da comparação, um interruptor mostra ou oculta os grupos de voto facultativo (16, 17 e 70 anos ou mais; analfabetos). Ocultar muda só o que aparece no gráfico e nos destaques "Maior/Menor taxa". A média do município continua com todos os eleitores, e a tela informa quantos eleitores estão ocultos.
- "Não informado" e "Inválido" ficam **fora dos gráficos e dos textos**, mas **dentro do total** do município. A tela diz quantos eleitores estão nessa situação.
- As categorias informadas são **idênticas em 2022 e 2026**, conferidas pelo pipeline. Por isso a comparação entre os anos é feita grupo a grupo, no mesmo turno.

### Cruzamentos
A estrutura do arquivo permitiria cruzar dimensões (por exemplo, idade × escolaridade), mas a mart guarda e a tela mostra **uma dimensão por vez**. Cruzamentos dividiriam municípios pequenos em grupos de poucas pessoas.

### Fórmulas e regras
| Indicador | Fórmula |
|---|---|
| Taxa de abstenção do grupo | `abstenções do grupo ÷ aptos do grupo × 100` |
| Média municipal | `abstenções do município ÷ aptos do município × 100`, na mesma base do perfil |
| Diferença para a média | taxa do grupo − média municipal, em p.p. |
| Variação 2022 → 2026 | taxa de 2026 − taxa de 2022 do mesmo grupo e turno, em p.p. |

- Números absolutos (aptos, compareceram, não compareceram) aparecem ao lado de cada taxa e na tabela "Ver como tabela".
- **Grupos pequenos:** com menos de **50 eleitores aptos** (em qualquer um dos anos, na comparação), o percentual aparece com `*` e fica fora dos destaques "Maior/Menor taxa" e das frases automáticas.
- As etiquetas "Maior taxa"/"Menor taxa" só aparecem quando as duas diferem em 0,5 p.p. ou mais, o mesmo limite de "praticamente igual" dos textos.
- Municípios sem 2022 (Boa Esperança do Norte/MT) não têm comparação. O 2º turno só é comparado quando houver o perfil do 2º turno de 2026.

### "O que os dados revelam?"
Frases montadas por regras fixas (`app/lib/narrativa.py`, função `revelam`), sem IA. No máximo **6 frases**: a tela mostra as **3 primeiras** e as outras em "Ver mais". A ordem de prioridade é:
1. Taxa e número de pessoas ausentes no município, com a taxa da outra eleição, quando houver.
2. Maior e menor taxa entre as faixas de 18 a 69 anos (os jovens adultos costumam aparecer aqui).
3. Com 2022 disponível: o grupo com a maior alta desde 2022.
4. Escolaridade com a maior taxa e sua distância da média municipal, além da menor taxa. Se a maior for a de analfabetos, a frase lembra que eles têm voto facultativo.
5. Feminino × masculino: diferença em p.p. ou "praticamente igual" (menos de 0,5 p.p.).
6. Com 2022 disponível: o grupo com a maior queda.
7. Maior taxa nas idades de voto facultativo, descrita como "registros de eleitores … no cadastro eleitoral", só quando supera a das faixas de 18 a 69 anos.
8. Aviso de comparação indisponível (2º turno de 2026 não publicado, ou município sem 2022).

As frases que não couberem nas 6 ficam de fora; os números continuam nos gráficos e nas tabelas.

Empates ficam com a primeira categoria na ordem oficial. As frases descrevem onde a ausência foi maior ou menor. Nunca atribuem motivos, e um teste barra palavras como "porque", "devido" e "motivo".

### Diferença para as outras telas
As outras telas usam `detalhe_votacao_munzona` (resultados por seção). Em cada município, as duas bases do TSE têm aptos ligeiramente diferentes, mas somam o mesmo total no Brasil: 156.454.011 em 2022 e 158.745.463 em 2026. A abstenção difere em 0,02 p.p. na mediana; no 99º percentil, até 0,4 p.p.; no máximo, 3,4 p.p. (Melgaço/PA, 2022, 2º turno). Por isso, a tela avisa: "As taxas podem diferir entre as bases; normalmente a diferença é pequena, mas há exceções." Grupos e média vêm sempre da mesma base. Detalhes em `docs/validacao.md` e `docs/validacao/perfil_execucao.json`.

### Limitações específicas
- Os indicadores descrevem **grupos agregados** de eleitores e não permitem identificar comportamentos individuais.
- As faixas mais altas reúnem muitos **registros no cadastro eleitoral**, com abstenção acima de 90%. São dados do CSV oficial do TSE, não erro de processamento: por exemplo, 48.821 registros de 100 anos ou mais em São Paulo e 4.361 em Campinas em 2026, com 99,8% de abstenção nos dois. O TSE não detalha a situação desses registros, então a tela não atribui o resultado a uma causa (como óbitos) e põe esse contexto junto do gráfico de idade.
- Dimensões diferentes se sobrepõem (idade e escolaridade, por exemplo). Uma diferença entre grupos não isola o efeito de uma característica.
