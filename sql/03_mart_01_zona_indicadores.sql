-- GoogleSQL / BigQuery Sandbox. Executar na ordem descrita em sql/README.md.
CREATE OR REPLACE TABLE `brasil-alem-das-urnas-2026.marts.mart_zona_indicadores` AS
SELECT *,
    100.0 * SAFE_DIVIDE(comparecimento, aptos) AS comparecimento_pct,
    100.0 * SAFE_DIVIDE(abstencoes, aptos) AS abstencoes_pct,
    100.0 * SAFE_DIVIDE(validos, comparecimento) AS validos_pct,
    100.0 * SAFE_DIVIDE(brancos, comparecimento) AS brancos_pct,
    100.0 * SAFE_DIVIDE(nulos, comparecimento) AS nulos_pct,
    100.0 * SAFE_DIVIDE(brancos + nulos, comparecimento) AS brancos_nulos_pct
FROM `brasil-alem-das-urnas-2026.staging.int_zona`;
