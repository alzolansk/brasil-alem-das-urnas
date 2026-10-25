-- GoogleSQL / BigQuery Sandbox. Executar na ordem descrita em sql/README.md.
CREATE OR REPLACE TABLE `brasil-alem-das-urnas-2026.staging.int_zona` AS
SELECT z.*, d.cd_municipio_ibge,
    COALESCE(d.nm_municipio, z.nm_municipio_tse) AS nm_municipio,
    d.regiao, z.sg_uf = 'ZZ' AS exterior
FROM `brasil-alem-das-urnas-2026.staging.stg_tse_zona` z
LEFT JOIN `brasil-alem-das-urnas-2026.staging.stg_dim_municipio` d
    ON z.cd_municipio_tse = d.cd_municipio_tse AND z.sg_uf = d.sg_uf;
