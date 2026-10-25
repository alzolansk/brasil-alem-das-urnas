-- Deve retornar zero linhas.
SELECT ano, turno, sg_uf, cd_municipio_tse
FROM `brasil-alem-das-urnas-2026.marts.mart_municipio_benchmark`
WHERE exterior
    OR comparecimento_pct_uf IS NULL OR comparecimento_pct_brasil IS NULL
    OR comparecimento_delta_uf_pp IS DISTINCT FROM (comparecimento_pct - comparecimento_pct_uf)
    OR comparecimento_delta_brasil_pp IS DISTINCT FROM (comparecimento_pct - comparecimento_pct_brasil)
    OR comparecimento_percentil_uf < 0 OR comparecimento_percentil_uf > 100
    OR abstencoes_pct_uf IS NULL OR abstencoes_pct_brasil IS NULL
    OR abstencoes_delta_uf_pp IS DISTINCT FROM (abstencoes_pct - abstencoes_pct_uf)
    OR abstencoes_delta_brasil_pp IS DISTINCT FROM (abstencoes_pct - abstencoes_pct_brasil)
    OR abstencoes_percentil_uf < 0 OR abstencoes_percentil_uf > 100
    OR validos_pct_uf IS NULL OR validos_pct_brasil IS NULL
    OR validos_delta_uf_pp IS DISTINCT FROM (validos_pct - validos_pct_uf)
    OR validos_delta_brasil_pp IS DISTINCT FROM (validos_pct - validos_pct_brasil)
    OR validos_percentil_uf < 0 OR validos_percentil_uf > 100
    OR brancos_pct_uf IS NULL OR brancos_pct_brasil IS NULL
    OR brancos_delta_uf_pp IS DISTINCT FROM (brancos_pct - brancos_pct_uf)
    OR brancos_delta_brasil_pp IS DISTINCT FROM (brancos_pct - brancos_pct_brasil)
    OR brancos_percentil_uf < 0 OR brancos_percentil_uf > 100
    OR nulos_pct_uf IS NULL OR nulos_pct_brasil IS NULL
    OR nulos_delta_uf_pp IS DISTINCT FROM (nulos_pct - nulos_pct_uf)
    OR nulos_delta_brasil_pp IS DISTINCT FROM (nulos_pct - nulos_pct_brasil)
    OR nulos_percentil_uf < 0 OR nulos_percentil_uf > 100
    OR brancos_nulos_pct_uf IS NULL OR brancos_nulos_pct_brasil IS NULL
    OR brancos_nulos_delta_uf_pp IS DISTINCT FROM (brancos_nulos_pct - brancos_nulos_pct_uf)
    OR brancos_nulos_delta_brasil_pp IS DISTINCT FROM (brancos_nulos_pct - brancos_nulos_pct_brasil)
    OR brancos_nulos_percentil_uf < 0 OR brancos_nulos_percentil_uf > 100;
