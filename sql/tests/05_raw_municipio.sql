-- Deve retornar zero linhas.
SELECT COALESCE(r.ano,m.ano) AS ano, COALESCE(r.turno,m.turno) AS turno,
    COALESCE(r.sg_uf,m.sg_uf) AS sg_uf,
    COALESCE(r.cd_municipio_tse,m.cd_municipio_tse) AS cd_municipio_tse
FROM `brasil-alem-das-urnas-2026.raw.raw_tse_municipio` r
FULL OUTER JOIN `brasil-alem-das-urnas-2026.marts.mart_municipio_indicadores` m
    USING (ano, turno, sg_uf, cd_municipio_tse)
WHERE r.aptos IS DISTINCT FROM m.aptos
    OR r.comparecimento IS DISTINCT FROM m.comparecimento
    OR r.abstencoes IS DISTINCT FROM m.abstencoes
    OR r.validos IS DISTINCT FROM m.validos
    OR r.brancos IS DISTINCT FROM m.brancos
    OR r.nulos IS DISTINCT FROM m.nulos
    OR r.anulados IS DISTINCT FROM m.anulados
    OR r.apurados_em_separado IS DISTINCT FROM m.apurados_em_separado
    OR r.eleitores_secoes_nao_instaladas IS DISTINCT FROM m.eleitores_secoes_nao_instaladas
    OR r.secoes IS DISTINCT FROM m.secoes
    OR r.n_zonas IS DISTINCT FROM m.n_zonas;
