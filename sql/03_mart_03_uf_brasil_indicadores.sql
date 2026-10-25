-- GoogleSQL / BigQuery Sandbox. Executar na ordem descrita em sql/README.md.
CREATE OR REPLACE TABLE `brasil-alem-das-urnas-2026.marts.mart_uf_brasil_indicadores` AS
WITH agregados AS (
    SELECT ano, turno, IF(exterior, 'EXTERIOR', 'UF') AS nivel,
        sg_uf AS localidade, regiao,
        SUM(aptos) AS aptos, SUM(comparecimento) AS comparecimento, SUM(abstencoes) AS abstencoes, SUM(validos) AS validos, SUM(brancos) AS brancos, SUM(nulos) AS nulos, SUM(anulados) AS anulados, SUM(apurados_em_separado) AS apurados_em_separado, SUM(eleitores_secoes_nao_instaladas) AS eleitores_secoes_nao_instaladas, SUM(secoes) AS secoes,
        MAX(dt_geracao) AS dt_geracao, MAX(ingerido_em) AS ingerido_em
    FROM `brasil-alem-das-urnas-2026.staging.int_municipio`
    GROUP BY ano, turno, nivel, localidade, regiao
    UNION ALL
    SELECT ano, turno, 'BRASIL' AS nivel, 'BR' AS localidade, CAST(NULL AS STRING) AS regiao,
        SUM(aptos), SUM(comparecimento), SUM(abstencoes), SUM(validos), SUM(brancos), SUM(nulos), SUM(anulados), SUM(apurados_em_separado), SUM(eleitores_secoes_nao_instaladas), SUM(secoes),
        MAX(dt_geracao), MAX(ingerido_em)
    FROM `brasil-alem-das-urnas-2026.staging.int_municipio`
    WHERE NOT exterior
    GROUP BY ano, turno
), taxas AS (
    SELECT *, 100.0 * SAFE_DIVIDE(comparecimento, aptos) AS comparecimento_pct,
    100.0 * SAFE_DIVIDE(abstencoes, aptos) AS abstencoes_pct,
    100.0 * SAFE_DIVIDE(validos, comparecimento) AS validos_pct,
    100.0 * SAFE_DIVIDE(brancos, comparecimento) AS brancos_pct,
    100.0 * SAFE_DIVIDE(nulos, comparecimento) AS nulos_pct,
    100.0 * SAFE_DIVIDE(brancos + nulos, comparecimento) AS brancos_nulos_pct
    FROM agregados
), rankings AS (
    SELECT *,
        IF(nivel = 'UF' AND comparecimento_pct IS NOT NULL,
            RANK() OVER (PARTITION BY ano, turno, nivel ORDER BY comparecimento_pct DESC),
            NULL) AS comparecimento_posicao_uf,
        IF(nivel = 'UF' AND abstencoes_pct IS NOT NULL,
            RANK() OVER (PARTITION BY ano, turno, nivel ORDER BY abstencoes_pct DESC),
            NULL) AS abstencoes_posicao_uf,
        IF(nivel = 'UF' AND validos_pct IS NOT NULL,
            RANK() OVER (PARTITION BY ano, turno, nivel ORDER BY validos_pct DESC),
            NULL) AS validos_posicao_uf,
        IF(nivel = 'UF' AND brancos_pct IS NOT NULL,
            RANK() OVER (PARTITION BY ano, turno, nivel ORDER BY brancos_pct DESC),
            NULL) AS brancos_posicao_uf,
        IF(nivel = 'UF' AND nulos_pct IS NOT NULL,
            RANK() OVER (PARTITION BY ano, turno, nivel ORDER BY nulos_pct DESC),
            NULL) AS nulos_posicao_uf,
        IF(nivel = 'UF' AND brancos_nulos_pct IS NOT NULL,
            RANK() OVER (PARTITION BY ano, turno, nivel ORDER BY brancos_nulos_pct DESC),
            NULL) AS brancos_nulos_posicao_uf
    FROM taxas
)
SELECT *,
    comparecimento_posicao_uf <= 5 AS comparecimento_top5_uf,
    abstencoes_posicao_uf <= 5 AS abstencoes_top5_uf,
    validos_posicao_uf <= 5 AS validos_top5_uf,
    brancos_posicao_uf <= 5 AS brancos_top5_uf,
    nulos_posicao_uf <= 5 AS nulos_top5_uf,
    brancos_nulos_posicao_uf <= 5 AS brancos_nulos_top5_uf
FROM rankings;
