-- Deve retornar zero linhas.
SELECT ano, turno, sg_uf, cd_municipio_tse
FROM `brasil-alem-das-urnas-2026.marts.mart_municipio_indicadores` WHERE NOT exterior
EXCEPT DISTINCT
SELECT ano, turno, sg_uf, cd_municipio_tse FROM `brasil-alem-das-urnas-2026.marts.mart_municipio_benchmark`;
