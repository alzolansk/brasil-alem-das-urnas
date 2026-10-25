-- GoogleSQL / BigQuery Sandbox. Executar na ordem descrita em sql/README.md.
CREATE OR REPLACE TABLE `brasil-alem-das-urnas-2026.marts.mart_municipio_benchmark` AS
SELECT m.*,
    u.comparecimento_pct AS comparecimento_pct_uf,
    b.comparecimento_pct AS comparecimento_pct_brasil,
    m.comparecimento_pct - u.comparecimento_pct AS comparecimento_delta_uf_pp,
    m.comparecimento_pct - b.comparecimento_pct AS comparecimento_delta_brasil_pp,
    IF(m.comparecimento_pct IS NULL, NULL,
        100.0 * SAFE_DIVIDE(
            RANK() OVER (PARTITION BY m.ano, m.turno, m.sg_uf
                         ORDER BY m.comparecimento_pct ASC NULLS LAST) - 1,
            NULLIF(COUNT(m.comparecimento_pct) OVER (
                PARTITION BY m.ano, m.turno, m.sg_uf) - 1, 0)
        )) AS comparecimento_percentil_uf,
    u.abstencoes_pct AS abstencoes_pct_uf,
    b.abstencoes_pct AS abstencoes_pct_brasil,
    m.abstencoes_pct - u.abstencoes_pct AS abstencoes_delta_uf_pp,
    m.abstencoes_pct - b.abstencoes_pct AS abstencoes_delta_brasil_pp,
    IF(m.abstencoes_pct IS NULL, NULL,
        100.0 * SAFE_DIVIDE(
            RANK() OVER (PARTITION BY m.ano, m.turno, m.sg_uf
                         ORDER BY m.abstencoes_pct ASC NULLS LAST) - 1,
            NULLIF(COUNT(m.abstencoes_pct) OVER (
                PARTITION BY m.ano, m.turno, m.sg_uf) - 1, 0)
        )) AS abstencoes_percentil_uf,
    u.validos_pct AS validos_pct_uf,
    b.validos_pct AS validos_pct_brasil,
    m.validos_pct - u.validos_pct AS validos_delta_uf_pp,
    m.validos_pct - b.validos_pct AS validos_delta_brasil_pp,
    IF(m.validos_pct IS NULL, NULL,
        100.0 * SAFE_DIVIDE(
            RANK() OVER (PARTITION BY m.ano, m.turno, m.sg_uf
                         ORDER BY m.validos_pct ASC NULLS LAST) - 1,
            NULLIF(COUNT(m.validos_pct) OVER (
                PARTITION BY m.ano, m.turno, m.sg_uf) - 1, 0)
        )) AS validos_percentil_uf,
    u.brancos_pct AS brancos_pct_uf,
    b.brancos_pct AS brancos_pct_brasil,
    m.brancos_pct - u.brancos_pct AS brancos_delta_uf_pp,
    m.brancos_pct - b.brancos_pct AS brancos_delta_brasil_pp,
    IF(m.brancos_pct IS NULL, NULL,
        100.0 * SAFE_DIVIDE(
            RANK() OVER (PARTITION BY m.ano, m.turno, m.sg_uf
                         ORDER BY m.brancos_pct ASC NULLS LAST) - 1,
            NULLIF(COUNT(m.brancos_pct) OVER (
                PARTITION BY m.ano, m.turno, m.sg_uf) - 1, 0)
        )) AS brancos_percentil_uf,
    u.nulos_pct AS nulos_pct_uf,
    b.nulos_pct AS nulos_pct_brasil,
    m.nulos_pct - u.nulos_pct AS nulos_delta_uf_pp,
    m.nulos_pct - b.nulos_pct AS nulos_delta_brasil_pp,
    IF(m.nulos_pct IS NULL, NULL,
        100.0 * SAFE_DIVIDE(
            RANK() OVER (PARTITION BY m.ano, m.turno, m.sg_uf
                         ORDER BY m.nulos_pct ASC NULLS LAST) - 1,
            NULLIF(COUNT(m.nulos_pct) OVER (
                PARTITION BY m.ano, m.turno, m.sg_uf) - 1, 0)
        )) AS nulos_percentil_uf,
    u.brancos_nulos_pct AS brancos_nulos_pct_uf,
    b.brancos_nulos_pct AS brancos_nulos_pct_brasil,
    m.brancos_nulos_pct - u.brancos_nulos_pct AS brancos_nulos_delta_uf_pp,
    m.brancos_nulos_pct - b.brancos_nulos_pct AS brancos_nulos_delta_brasil_pp,
    IF(m.brancos_nulos_pct IS NULL, NULL,
        100.0 * SAFE_DIVIDE(
            RANK() OVER (PARTITION BY m.ano, m.turno, m.sg_uf
                         ORDER BY m.brancos_nulos_pct ASC NULLS LAST) - 1,
            NULLIF(COUNT(m.brancos_nulos_pct) OVER (
                PARTITION BY m.ano, m.turno, m.sg_uf) - 1, 0)
        )) AS brancos_nulos_percentil_uf
FROM `brasil-alem-das-urnas-2026.marts.mart_municipio_indicadores` m
JOIN `brasil-alem-das-urnas-2026.marts.mart_uf_brasil_indicadores` u
    ON m.ano = u.ano AND m.turno = u.turno AND m.sg_uf = u.localidade AND u.nivel = 'UF'
JOIN `brasil-alem-das-urnas-2026.marts.mart_uf_brasil_indicadores` b
    ON m.ano = b.ano AND m.turno = b.turno AND b.nivel = 'BRASIL'
WHERE NOT m.exterior;
