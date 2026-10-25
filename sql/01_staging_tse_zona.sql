-- GoogleSQL / BigQuery Sandbox. Executar na ordem descrita em sql/README.md.
CREATE OR REPLACE TABLE `brasil-alem-das-urnas-2026.staging.stg_tse_zona` AS
SELECT ano, turno, cd_eleicao, sg_uf, cd_municipio_tse, nm_municipio_tse, nr_zona,
    aptos, comparecimento, abstencoes, validos, brancos, nulos, anulados, apurados_em_separado, eleitores_secoes_nao_instaladas, secoes,
    dt_geracao, dt_ultima_totalizacao, ingerido_em, arquivo_origem
FROM `brasil-alem-das-urnas-2026.raw.raw_tse_zona`;
