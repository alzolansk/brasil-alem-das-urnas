# Validação contra números oficiais do TSE

## Reconferência nacional em 25/10/2026

O problema informado na publicação reproduz exatamente a agregação territorial antiga: em 2026 T1, 157.828.968 aptos e 32.894.899 abstenções / aptos = 20,842118%. A SQL antiga (`83296a4`) tinha `WHERE NOT exterior` no total nacional. O commit `c842bbb` removeu esse filtro **e atualizou as duas marts dependentes**, os benchmarks e a documentação. Na revisão atual, os seis hashes do manifest conferiam antes de qualquer alteração; Brasil e benchmarks já continham 21,083586%. Portanto, **a hipótese de documentação atualizada sem regeneração não se confirmou no checkout atual**.

Foi confirmada uma vulnerabilidade independente: `st.cache_data` usava apenas o nome da mart, sem versão/caminho do arquivo. Uma substituição do Parquet no mesmo processo podia devolver o conteúdo anterior. Agora a chave inclui caminho absoluto, modificação em nanossegundos e tamanho. A lista municipal derivada também é refeita a partir da leitura atualizada. Teste com cache aquecido reproduz a substituição e verifica a atualização sem limpeza manual.

**Limite da investigação em produção:** a URL fornecida foi tentada, mas a ferramenta web não conseguiu acessá-la e nenhum navegador conectado estava disponível. Não foi possível inspecionar o commit, o branch, o cache nem os números vivos do processo remoto. Uma versão anterior ou um cache antigo explicam os valores relatados, mas não foram distinguidos em produção. Não houve commit, push, reinício nem deploy nesta revisão.

### Antes (território) e depois (Brasil + Exterior)

| Eleição / turno | Aptos sem ZZ | Abstenção sem ZZ | Aptos com ZZ | Comparecimento com ZZ | Abstenções com ZZ | Taxa com ZZ |
|---|---:|---:|---:|---:|---:|---:|
| 2022 T1 | 155.758.656 | 20,788721% | 156.454.011 | 123.682.372 | 32.770.982 | 20,946080% |
| 2022 T2 | 155.758.433 | 20,426310% | 156.454.011 | 124.252.796 | 32.200.558 | 20,581484% |
| 2026 T1 | 157.828.968 | 20,842118% | 158.745.502 | 125.275.835 | 33.469.244 | 21,083586% |

“Antes” reconstrói a regra antiga, não uma medição remota nova. A regeneração local desta revisão reexecutou a SQL real de UF/Brasil e benchmark, partindo da mart municipal versionada. Preservou os totais já corrigidos; não inseriu valores de referência nem constantes corretivas. Motor, hashes e totais em `data/marts/manifest.json`, campo `reconciliacao_nacional`.

### Fontes oficiais e diferenças

- Downloads novos dos arquivos `detalhe_votacao_munzona` de [2022](https://dadosabertos.tse.jus.br/dataset/resultados-2022) e [2026](https://dadosabertos.tse.jus.br/dataset/resultados-2026): todos os campos de contagem nacionais coincidem com as marts. Evidência reproduzível: `python -m scripts.conferir_fontes_nacionais`; saída em `docs/validacao/conferencia_nacional_fontes.json`.
- 2022: a [totalização oficial do primeiro turno](https://www.tse.jus.br/comunicacao/noticias/2022/Outubro/100-das-secoes-totalizadas-confira-como-ficou-o-quadro-eleitoral-apos-o-1o-turno) confirma 156.454.011 aptos e 123.682.372 comparecimentos. A [totalização do segundo turno](https://www.tse.jus.br/comunicacao/noticias/2022/Outubro/100-das-secoes-totalizadas-confira-como-ficou-o-quadro-eleitoral-apos-o-2o-turno/) confirma 156.454.011 e 124.252.796. Percentuais de notícias não substituem a razão dos campos inteiros do CSV.
  No segundo turno, a notícia exibe 79,41% de comparecimento; a divisão dos próprios totais dá 79,418096%. Não se ajustou a razão para reproduzir a apresentação da notícia. A abstenção foi calculada diretamente de 32.200.558 / 156.454.011, preservando separadamente os 657 eleitores de seções não instaladas.
- 2026: o portal oficial documenta **39 registros de TTE ainda vinculados à origem**: resultados = 158.745.502 registros; eleitorado efetivo = 158.745.463. A diferença tem causa oficial e não deve ser corrigida subtraindo 39 arbitrariamente das localidades. Mantida a base de resultados, com a limitação explícita na metodologia.
- O [TRE-MT](https://www.tre-mt.jus.br/comunicacao/noticias/2026/Outubro/mato-grosso-registra-menor-indice-de-abstencao-dos-ultimos-quatro-pleitos-presidenciais) informa, para a base de comparecimento/perfil de 2026 T1, 158.745.463 aptos, 125.277.230 presentes e 33.468.233 ausentes. Os resultados têm +39 aptos, −1.395 presentes e +1.011 abstenções, com 423 eleitores de seções não instaladas separados. Não misturar numerador de perfil com denominador de resultados.
- O arquivo de 2026 baixado agora tem geração em 25/10/2026 e hash diferente do bruto anterior. As contagens por zona foram comparadas; os totais nacionais coincidem. Não houve troca silenciosa do arquivo bruto. O segundo turno de 2026 não está no download e continua indisponível.
- Leiame oficial distribuído nos ZIPs, cópia em `docs/fontes/tse/leiame_detalhe_votacao_munzona_2022.pdf`, pp. 1 e 5: `BR` é nacional e `ZZ` é exterior; eleitores de seções não instaladas possuem campo próprio. O parser ignora linhas agregadas `BR` e admite apenas as UFs e `ZZ` como folhas; siglas sem regra fazem a ingestão falhar.

### Verificações reproduzíveis

`python -m scripts.validar_marts` confere os Parquets efetivamente servidos: chaves, hashes, uma linha nacional, 27 UFs, um exterior, todas as contagens zona = município = UF + exterior = Brasil, todas as taxas pela razão das somas, benchmark e deltas nacionais, exclusão territorial e seções não instaladas. O export do BigQuery aplica a mesma validação **antes** de substituir as marts. `python -m scripts.regenerar_nacional` regenera as duas marts dependentes localmente com a SQL do projeto, sem acesso ao GCP.

Os testes de regressão também injetam exterior ausente/duplicado, média simples e benchmark antigo e exigem rejeição. Os testes AppTest cobrem as páginas e filtros existentes. AppTest não valida pixels/CSS nem comprova o estado do serviço publicado.

Resultado desta revisão: `python -m pytest -q` **127 passaram**, incluindo as três eleições/turnos disponíveis em Brasil em perspectiva e Mapa com filtro regional, além de Explore, Comparativo e demais telas. `python -m ruff check .`, `git diff --check` e `python -m scripts.validar_marts` passaram. Houve um aviso do ambiente sobre versões de dependências de `requests`; os downloads oficiais e testes concluíram. Não foi executada modelagem no BigQuery nem validação visual em navegador nesta revisão.

## Registro anterior de conferência com o painel de perfil

Os registros abaixo foram mantidos como histórico da comparação com outra base, não como metas de ajuste.

| Data | Eleição | Turno | Recorte | Indicador | Pipeline | TSE oficial | Diferença | OK? | Observação |
|---|---|---|---|---|---|---|---|---|---|
| 25/10/2026 | 2022 | 1º | Brasil (com exterior) | Eleitores aptos | 156.454.011 | 156.454.011 | 0 | OK | Linha BRASIL já contém EXTERIOR; nunca somar as duas |
| 25/10/2026 | 2022 | 1º | Brasil (com exterior) | Comparecimento | 123.682.372 | 123.714.335 | −31.963 (−0,026%) | ❌ | Idem |
| 25/10/2026 | 2022 | 1º | Brasil (com exterior) | Abstenção | 32.770.982 (20,95%) | 20,95% | 0,00 p.p. | ✅ | Linha `BRASIL` da mart (Brasil + Exterior). 32.771.639 = aptos − comparecimento, que inclui os 657 eleitores de seções não instaladas |
| 25/10/2026 | 2026 | 1º | Brasil (com exterior) | Abstenção | 33.469.244 (21,08%) | 33,4 milhões (21,08%) | 0,00 p.p. | ✅ | Antes da inclusão do exterior na linha `BRASIL`, a mart dava 32.894.899 (20,84%) |
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

## Perfil da abstenção ("Quem ficou em casa?", 25/10/2026)
Rodado por `python -m scripts.perfil_abstencao`, que grava a evidência em `docs/validacao/perfil_execucao.json`. A mart só é substituída se não houver nenhum problema.

| Verificação | Resultado |
|---|---|
| `QT_APTOS = QT_COMPARECIMENTO + QT_ABSTENCAO`, linha a linha (8.785.738 linhas em 2022, 11.060.908 em 2026) | 0 linhas diferentes, 0 negativas |
| Códigos e descrições de gênero, faixa etária e escolaridade iguais aos do leiame | OK nos dois anos |
| Soma das categorias de cada dimensão = total do município (sem dupla contagem) | OK em todos os municípios e turnos |
| Municípios casados com o IBGE | 5.570 (2022) e 5.571 (2026), 100% |
| Categorias informadas iguais em 2022 e 2026 | Sim |

Totais do Brasil com exterior contra o painel oficial de comparecimento e abstenção do TSE, que usa este mesmo dataset:

| Eleição | Indicador | Pipeline | TSE | Diferença |
|---|---|---|---|---|
| 2022, 1º turno | Aptos | 156.454.011 | 156.454.011 | 0 |
| 2022, 1º turno | Comparecimento | 123.714.335 | 123.714.335 | 0 |
| 2022, 2º turno | Aptos | 156.454.011 | 156.454.011 | 0 |
| 2022, 2º turno | Comparecimento | 124.267.614 | 124.267.614 | 0 |
| 2026, 1º turno | Aptos | 158.745.463 | 158.745.463 | 0 |
| 2026, 1º turno | Comparecimento | 125.277.230 | 125.277.230 | 0 |

Diferença de cobertura em relação a `detalhe_votacao_munzona` (base das outras telas), por município e sem o exterior:

| Eleição | Municípios com aptos diferentes | Abstenção: diferença mediana | 99º percentil | Máxima |
|---|---|---|---|---|
| 2022, 1º turno | 5.453 de 5.570 | 0,025 p.p. | 0,18 p.p. | 2,35 p.p. |
| 2022, 2º turno | 5.468 de 5.570 | 0,022 p.p. | 0,37 p.p. | 3,36 p.p. |
| 2026, 1º turno | 5.462 de 5.571 | 0,023 p.p. | 0,17 p.p. | 0,77 p.p. |

No perfil, os aptos de um município são os mesmos nos dois turnos de 2022 (Campinas: 878.715). No resultado por seção, eles mudam de um turno para o outro (Campinas: 881.377 e 881.208). Isso é compatível com o perfil contar o eleitor pelo cadastro e o resultado, pelo local onde votou (por exemplo, transferência temporária). O TSE não documenta o critério, então isto é inferência, como na seção acima. Decisão: a tela usa só o perfil, para grupos e média virem da mesma base, e avisa que "as taxas podem diferir entre as bases; normalmente a diferença é pequena, mas há exceções" (a maior: 3,36 p.p. em Melgaço/PA, 2º turno de 2022).
