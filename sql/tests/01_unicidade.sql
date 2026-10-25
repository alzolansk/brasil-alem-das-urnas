-- Deve retornar zero linhas.
SELECT 'mart_zona_indicadores' AS tabela, TO_JSON_STRING(STRUCT(ano, turno, sg_uf, cd_municipio_tse, nr_zona)) AS chave, COUNT(*) AS n
FROM `brasil-alem-das-urnas-2026.marts.mart_zona_indicadores` GROUP BY ano, turno, sg_uf, cd_municipio_tse, nr_zona HAVING COUNT(*) != 1
UNION ALL
SELECT 'mart_municipio_indicadores' AS tabela, TO_JSON_STRING(STRUCT(ano, turno, sg_uf, cd_municipio_tse)) AS chave, COUNT(*) AS n
FROM `brasil-alem-das-urnas-2026.marts.mart_municipio_indicadores` GROUP BY ano, turno, sg_uf, cd_municipio_tse HAVING COUNT(*) != 1
UNION ALL
SELECT 'mart_uf_brasil_indicadores' AS tabela, TO_JSON_STRING(STRUCT(ano, turno, nivel, localidade)) AS chave, COUNT(*) AS n
FROM `brasil-alem-das-urnas-2026.marts.mart_uf_brasil_indicadores` GROUP BY ano, turno, nivel, localidade HAVING COUNT(*) != 1
UNION ALL
SELECT 'mart_municipio_comparativo' AS tabela, TO_JSON_STRING(STRUCT(tipo_comparacao, ano_base, turno_base, ano_comparacao, turno_comparacao, sg_uf, cd_municipio_tse)) AS chave, COUNT(*) AS n
FROM `brasil-alem-das-urnas-2026.marts.mart_municipio_comparativo` GROUP BY tipo_comparacao, ano_base, turno_base, ano_comparacao, turno_comparacao, sg_uf, cd_municipio_tse HAVING COUNT(*) != 1
UNION ALL
SELECT 'mart_municipio_benchmark' AS tabela, TO_JSON_STRING(STRUCT(ano, turno, sg_uf, cd_municipio_tse)) AS chave, COUNT(*) AS n
FROM `brasil-alem-das-urnas-2026.marts.mart_municipio_benchmark` GROUP BY ano, turno, sg_uf, cd_municipio_tse HAVING COUNT(*) != 1;
