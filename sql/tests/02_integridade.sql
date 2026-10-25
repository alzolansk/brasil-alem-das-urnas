-- Deve retornar zero linhas.
SELECT 'zona' AS nivel, ano, turno, sg_uf, cd_municipio_tse
FROM `brasil-alem-das-urnas-2026.marts.mart_zona_indicadores`
WHERE ano NOT IN (2022, 2026) OR ano IS NULL OR turno NOT IN (1, 2) OR turno IS NULL
    OR sg_uf IS NULL OR cd_municipio_tse IS NULL
    OR nr_zona IS NULL
    OR (NOT exterior AND (cd_municipio_ibge IS NULL OR regiao IS NULL))
    OR aptos IS NULL OR aptos < 0
    OR comparecimento IS NULL OR comparecimento < 0
    OR abstencoes IS NULL OR abstencoes < 0
    OR validos IS NULL OR validos < 0
    OR brancos IS NULL OR brancos < 0
    OR nulos IS NULL OR nulos < 0
    OR anulados IS NULL OR anulados < 0
    OR apurados_em_separado IS NULL OR apurados_em_separado < 0
    OR eleitores_secoes_nao_instaladas IS NULL OR eleitores_secoes_nao_instaladas < 0
    OR secoes IS NULL OR secoes < 0
    OR aptos != comparecimento + abstencoes + eleitores_secoes_nao_instaladas
    OR comparecimento != validos + brancos + nulos
    OR anulados != 0 OR apurados_em_separado != 0
    OR (comparecimento_pct < 0 OR comparecimento_pct > 100)
    OR (abstencoes_pct < 0 OR abstencoes_pct > 100)
    OR (validos_pct < 0 OR validos_pct > 100)
    OR (brancos_pct < 0 OR brancos_pct > 100)
    OR (nulos_pct < 0 OR nulos_pct > 100)
    OR (brancos_nulos_pct < 0 OR brancos_nulos_pct > 100)
UNION ALL
SELECT 'municipio' AS nivel, ano, turno, sg_uf, cd_municipio_tse
FROM `brasil-alem-das-urnas-2026.marts.mart_municipio_indicadores`
WHERE ano NOT IN (2022, 2026) OR ano IS NULL OR turno NOT IN (1, 2) OR turno IS NULL
    OR sg_uf IS NULL OR cd_municipio_tse IS NULL
    
    OR (NOT exterior AND (cd_municipio_ibge IS NULL OR regiao IS NULL))
    OR aptos IS NULL OR aptos < 0
    OR comparecimento IS NULL OR comparecimento < 0
    OR abstencoes IS NULL OR abstencoes < 0
    OR validos IS NULL OR validos < 0
    OR brancos IS NULL OR brancos < 0
    OR nulos IS NULL OR nulos < 0
    OR anulados IS NULL OR anulados < 0
    OR apurados_em_separado IS NULL OR apurados_em_separado < 0
    OR eleitores_secoes_nao_instaladas IS NULL OR eleitores_secoes_nao_instaladas < 0
    OR secoes IS NULL OR secoes < 0
    OR aptos != comparecimento + abstencoes + eleitores_secoes_nao_instaladas
    OR comparecimento != validos + brancos + nulos
    OR anulados != 0 OR apurados_em_separado != 0
    OR (comparecimento_pct < 0 OR comparecimento_pct > 100)
    OR (abstencoes_pct < 0 OR abstencoes_pct > 100)
    OR (validos_pct < 0 OR validos_pct > 100)
    OR (brancos_pct < 0 OR brancos_pct > 100)
    OR (nulos_pct < 0 OR nulos_pct > 100)
    OR (brancos_nulos_pct < 0 OR brancos_nulos_pct > 100);
