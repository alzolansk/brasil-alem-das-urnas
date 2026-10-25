-- GoogleSQL / BigQuery Sandbox. Executar na ordem descrita em sql/README.md.
CREATE OR REPLACE TABLE `brasil-alem-das-urnas-2026.staging.stg_dim_municipio` AS
SELECT cd_municipio_tse, cd_municipio_ibge, sg_uf, nm_municipio, regiao
FROM `brasil-alem-das-urnas-2026.raw.raw_dim_municipio`;
