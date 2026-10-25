-- Deve retornar zero linhas.
SELECT tipo_comparacao, ano_base, turno_base, cd_municipio_tse
FROM `brasil-alem-das-urnas-2026.marts.mart_municipio_comparativo`
WHERE (status_comparacao = 'disponivel' AND (aptos_base IS NULL OR aptos_comparacao IS NULL))
    OR (status_comparacao = 'sem_base' AND aptos_base IS NOT NULL)
    OR (status_comparacao = 'sem_comparacao' AND aptos_comparacao IS NOT NULL)
    OR comparecimento_delta_pp IS DISTINCT FROM (comparecimento_pct_comparacao - comparecimento_pct_base)
    OR abstencoes_delta_pp IS DISTINCT FROM (abstencoes_pct_comparacao - abstencoes_pct_base)
    OR validos_delta_pp IS DISTINCT FROM (validos_pct_comparacao - validos_pct_base)
    OR brancos_delta_pp IS DISTINCT FROM (brancos_pct_comparacao - brancos_pct_base)
    OR nulos_delta_pp IS DISTINCT FROM (nulos_pct_comparacao - nulos_pct_base)
    OR brancos_nulos_delta_pp IS DISTINCT FROM (brancos_nulos_pct_comparacao - brancos_nulos_pct_base)
    OR aptos_variacao_pct IS DISTINCT FROM
        (100.0 * SAFE_DIVIDE(aptos_comparacao - aptos_base, aptos_base));
