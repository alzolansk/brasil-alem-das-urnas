-- GoogleSQL / BigQuery Sandbox. Executar na ordem descrita em sql/README.md.
CREATE OR REPLACE TABLE `brasil-alem-das-urnas-2026.staging.int_municipio` AS
SELECT ano, turno, sg_uf, cd_municipio_tse, cd_municipio_ibge,
    nm_municipio, regiao, exterior,
    SUM(aptos) AS aptos,
    SUM(comparecimento) AS comparecimento,
    SUM(abstencoes) AS abstencoes,
    SUM(validos) AS validos,
    SUM(brancos) AS brancos,
    SUM(nulos) AS nulos,
    SUM(anulados) AS anulados,
    SUM(apurados_em_separado) AS apurados_em_separado,
    SUM(eleitores_secoes_nao_instaladas) AS eleitores_secoes_nao_instaladas,
    SUM(secoes) AS secoes,
    COUNT(*) AS n_zonas, MAX(dt_geracao) AS dt_geracao,
    MAX(dt_ultima_totalizacao) AS dt_ultima_totalizacao, MAX(ingerido_em) AS ingerido_em
FROM `brasil-alem-das-urnas-2026.staging.int_zona`
GROUP BY ano, turno, sg_uf, cd_municipio_tse, cd_municipio_ibge,
    nm_municipio, regiao, exterior;
