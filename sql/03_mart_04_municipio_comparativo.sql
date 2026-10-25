-- GoogleSQL / BigQuery Sandbox. Executar na ordem descrita em sql/README.md.
CREATE OR REPLACE TABLE `brasil-alem-das-urnas-2026.marts.mart_municipio_comparativo` AS
WITH pares AS (
    SELECT 'anos' AS tipo_comparacao, 2022 AS ano_base, turno AS turno_base,
        2026 AS ano_comparacao, turno AS turno_comparacao
    FROM UNNEST([1, 2]) turno
    UNION ALL
    SELECT 'turnos', ano, 1, ano, 2 FROM UNNEST([2022, 2026]) ano
), municipios AS (
    SELECT DISTINCT sg_uf, cd_municipio_tse, cd_municipio_ibge, nm_municipio, regiao
    FROM `brasil-alem-das-urnas-2026.marts.mart_municipio_indicadores` WHERE NOT exterior
)
SELECT m.*, p.*,
    CASE WHEN b.ano IS NULL THEN 'sem_base'
         WHEN c.ano IS NULL THEN 'sem_comparacao'
         ELSE 'disponivel' END AS status_comparacao,
    b.aptos AS aptos_base, c.aptos AS aptos_comparacao,
    100.0 * SAFE_DIVIDE(c.aptos - b.aptos, b.aptos) AS aptos_variacao_pct,
    b.comparecimento_pct AS comparecimento_pct_base,
    c.comparecimento_pct AS comparecimento_pct_comparacao,
    c.comparecimento_pct - b.comparecimento_pct AS comparecimento_delta_pp,
    b.abstencoes_pct AS abstencoes_pct_base,
    c.abstencoes_pct AS abstencoes_pct_comparacao,
    c.abstencoes_pct - b.abstencoes_pct AS abstencoes_delta_pp,
    b.validos_pct AS validos_pct_base,
    c.validos_pct AS validos_pct_comparacao,
    c.validos_pct - b.validos_pct AS validos_delta_pp,
    b.brancos_pct AS brancos_pct_base,
    c.brancos_pct AS brancos_pct_comparacao,
    c.brancos_pct - b.brancos_pct AS brancos_delta_pp,
    b.nulos_pct AS nulos_pct_base,
    c.nulos_pct AS nulos_pct_comparacao,
    c.nulos_pct - b.nulos_pct AS nulos_delta_pp,
    b.brancos_nulos_pct AS brancos_nulos_pct_base,
    c.brancos_nulos_pct AS brancos_nulos_pct_comparacao,
    c.brancos_nulos_pct - b.brancos_nulos_pct AS brancos_nulos_delta_pp
FROM municipios m CROSS JOIN pares p
LEFT JOIN `brasil-alem-das-urnas-2026.marts.mart_municipio_indicadores` b
    ON m.sg_uf = b.sg_uf AND m.cd_municipio_tse = b.cd_municipio_tse
    AND p.ano_base = b.ano AND p.turno_base = b.turno
LEFT JOIN `brasil-alem-das-urnas-2026.marts.mart_municipio_indicadores` c
    ON m.sg_uf = c.sg_uf AND m.cd_municipio_tse = c.cd_municipio_tse
    AND p.ano_comparacao = c.ano AND p.turno_comparacao = c.turno
WHERE b.ano IS NOT NULL OR c.ano IS NOT NULL;
