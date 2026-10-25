-- Deve retornar zero linhas.
WITH zonas AS (
    SELECT ano, turno, sg_uf, cd_municipio_tse,
        SUM(aptos) AS aptos, SUM(comparecimento) AS comparecimento, SUM(abstencoes) AS abstencoes, SUM(validos) AS validos, SUM(brancos) AS brancos, SUM(nulos) AS nulos, SUM(anulados) AS anulados, SUM(apurados_em_separado) AS apurados_em_separado, SUM(eleitores_secoes_nao_instaladas) AS eleitores_secoes_nao_instaladas, SUM(secoes) AS secoes, COUNT(*) AS n_zonas
    FROM `brasil-alem-das-urnas-2026.marts.mart_zona_indicadores`
    GROUP BY ano, turno, sg_uf, cd_municipio_tse
)
SELECT COALESCE(m.ano,z.ano) AS ano, COALESCE(m.turno,z.turno) AS turno,
    COALESCE(m.sg_uf,z.sg_uf) AS sg_uf,
    COALESCE(m.cd_municipio_tse,z.cd_municipio_tse) AS cd_municipio_tse
FROM zonas z FULL OUTER JOIN `brasil-alem-das-urnas-2026.marts.mart_municipio_indicadores` m
    USING (ano, turno, sg_uf, cd_municipio_tse)
WHERE m.aptos IS DISTINCT FROM z.aptos
    OR m.comparecimento IS DISTINCT FROM z.comparecimento
    OR m.abstencoes IS DISTINCT FROM z.abstencoes
    OR m.validos IS DISTINCT FROM z.validos
    OR m.brancos IS DISTINCT FROM z.brancos
    OR m.nulos IS DISTINCT FROM z.nulos
    OR m.anulados IS DISTINCT FROM z.anulados
    OR m.apurados_em_separado IS DISTINCT FROM z.apurados_em_separado
    OR m.eleitores_secoes_nao_instaladas IS DISTINCT FROM z.eleitores_secoes_nao_instaladas
    OR m.secoes IS DISTINCT FROM z.secoes
    OR m.n_zonas IS DISTINCT FROM z.n_zonas;
