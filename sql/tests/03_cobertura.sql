-- Deve retornar zero linhas.
WITH observado AS (
    SELECT ano, turno, COUNT(*) AS municipios
    FROM `brasil-alem-das-urnas-2026.marts.mart_municipio_indicadores` WHERE NOT exterior
    GROUP BY ano, turno
), esperado AS (
    SELECT 2022 AS ano, 1 AS turno, 5570 AS municipios UNION ALL
    SELECT 2022, 2, 5570 UNION ALL SELECT 2026, 1, 5571
    UNION ALL SELECT 2026, 2, 5571 FROM UNNEST([1]) WHERE EXISTS (
        SELECT 1 FROM `brasil-alem-das-urnas-2026.raw.raw_tse_zona` WHERE ano = 2026 AND turno = 2
    )
)
SELECT COALESCE(e.ano, o.ano) AS ano, COALESCE(e.turno, o.turno) AS turno,
    e.municipios AS esperado, o.municipios AS observado
FROM esperado e FULL OUTER JOIN observado o USING (ano, turno)
WHERE e.municipios IS DISTINCT FROM o.municipios;
