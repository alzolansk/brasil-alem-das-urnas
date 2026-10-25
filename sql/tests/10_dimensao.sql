-- Deve retornar zero linhas.
SELECT sg_uf, cd_municipio_tse, COUNT(*) AS n
FROM `brasil-alem-das-urnas-2026.staging.stg_dim_municipio`
GROUP BY sg_uf, cd_municipio_tse
HAVING COUNT(*) != 1 OR sg_uf IS NULL OR cd_municipio_tse IS NULL
UNION ALL
SELECT sg_uf, cd_municipio_ibge, COUNT(*)
FROM `brasil-alem-das-urnas-2026.staging.stg_dim_municipio`
GROUP BY sg_uf, cd_municipio_ibge
HAVING COUNT(*) != 1 OR cd_municipio_ibge IS NULL;
