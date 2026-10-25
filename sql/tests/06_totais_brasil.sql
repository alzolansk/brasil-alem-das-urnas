-- Deve retornar zero linhas.
WITH totais AS (
    SELECT ano, turno, SUM(aptos) AS aptos, SUM(comparecimento) AS comparecimento, SUM(abstencoes) AS abstencoes, SUM(validos) AS validos, SUM(brancos) AS brancos, SUM(nulos) AS nulos, SUM(anulados) AS anulados, SUM(apurados_em_separado) AS apurados_em_separado, SUM(eleitores_secoes_nao_instaladas) AS eleitores_secoes_nao_instaladas, SUM(secoes) AS secoes
    FROM `brasil-alem-das-urnas-2026.marts.mart_municipio_indicadores` WHERE NOT exterior GROUP BY ano, turno
)
SELECT t.ano, t.turno, 'soma_territorio' AS teste
FROM totais t FULL OUTER JOIN (
    SELECT * FROM `brasil-alem-das-urnas-2026.marts.mart_uf_brasil_indicadores` WHERE nivel = 'BRASIL'
) b USING (ano, turno)
WHERE t.aptos IS DISTINCT FROM b.aptos OR t.comparecimento IS DISTINCT FROM b.comparecimento OR t.abstencoes IS DISTINCT FROM b.abstencoes OR t.validos IS DISTINCT FROM b.validos OR t.brancos IS DISTINCT FROM b.brancos OR t.nulos IS DISTINCT FROM b.nulos OR t.anulados IS DISTINCT FROM b.anulados OR t.apurados_em_separado IS DISTINCT FROM b.apurados_em_separado OR t.eleitores_secoes_nao_instaladas IS DISTINCT FROM b.eleitores_secoes_nao_instaladas OR t.secoes IS DISTINCT FROM b.secoes
UNION ALL
SELECT 2022, 1, 'total_oficial_com_exterior'
FROM (
    SELECT SUM(aptos) AS aptos, SUM(comparecimento) AS comparecimento, COUNT(*) AS n
    FROM `brasil-alem-das-urnas-2026.marts.mart_uf_brasil_indicadores`
    WHERE ano = 2022 AND turno = 1 AND nivel IN ('BRASIL', 'EXTERIOR')
)
WHERE aptos IS DISTINCT FROM 156454011 OR comparecimento IS DISTINCT FROM 123682372 OR n != 2;
