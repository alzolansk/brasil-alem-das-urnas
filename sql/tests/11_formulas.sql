-- Deve retornar zero linhas: denominadores por indicador em todos os níveis.
SELECT 'zona' AS nivel, ano, turno
FROM `brasil-alem-das-urnas-2026.marts.mart_zona_indicadores`
WHERE comparecimento_pct IS DISTINCT FROM (100.0 * SAFE_DIVIDE(comparecimento, aptos))
    OR abstencoes_pct IS DISTINCT FROM (100.0 * SAFE_DIVIDE(abstencoes, aptos))
    OR validos_pct IS DISTINCT FROM (100.0 * SAFE_DIVIDE(validos, comparecimento))
    OR brancos_pct IS DISTINCT FROM (100.0 * SAFE_DIVIDE(brancos, comparecimento))
    OR nulos_pct IS DISTINCT FROM (100.0 * SAFE_DIVIDE(nulos, comparecimento))
    OR brancos_nulos_pct IS DISTINCT FROM (100.0 * SAFE_DIVIDE(brancos + nulos, comparecimento))
UNION ALL
SELECT 'municipio' AS nivel, ano, turno
FROM `brasil-alem-das-urnas-2026.marts.mart_municipio_indicadores`
WHERE comparecimento_pct IS DISTINCT FROM (100.0 * SAFE_DIVIDE(comparecimento, aptos))
    OR abstencoes_pct IS DISTINCT FROM (100.0 * SAFE_DIVIDE(abstencoes, aptos))
    OR validos_pct IS DISTINCT FROM (100.0 * SAFE_DIVIDE(validos, comparecimento))
    OR brancos_pct IS DISTINCT FROM (100.0 * SAFE_DIVIDE(brancos, comparecimento))
    OR nulos_pct IS DISTINCT FROM (100.0 * SAFE_DIVIDE(nulos, comparecimento))
    OR brancos_nulos_pct IS DISTINCT FROM (100.0 * SAFE_DIVIDE(brancos + nulos, comparecimento))
UNION ALL
SELECT 'uf_brasil' AS nivel, ano, turno
FROM `brasil-alem-das-urnas-2026.marts.mart_uf_brasil_indicadores`
WHERE comparecimento_pct IS DISTINCT FROM (100.0 * SAFE_DIVIDE(comparecimento, aptos))
    OR abstencoes_pct IS DISTINCT FROM (100.0 * SAFE_DIVIDE(abstencoes, aptos))
    OR validos_pct IS DISTINCT FROM (100.0 * SAFE_DIVIDE(validos, comparecimento))
    OR brancos_pct IS DISTINCT FROM (100.0 * SAFE_DIVIDE(brancos, comparecimento))
    OR nulos_pct IS DISTINCT FROM (100.0 * SAFE_DIVIDE(nulos, comparecimento))
    OR brancos_nulos_pct IS DISTINCT FROM (100.0 * SAFE_DIVIDE(brancos + nulos, comparecimento));
