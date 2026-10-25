"""Sem GCP: executa o SQL real (transpilado) sobre casos de borda pequenos."""

from datetime import UTC, date, datetime

import duckdb
import pandas as pd
import pytest
import sqlglot

from scripts.export_marts import gravar_parquet
from scripts.modelagem import PROJETO, ROOT


def modelar(segundo_turno_2026=False):
    con = duckdb.connect()
    for schema in ("raw", "staging", "marts"):
        con.execute(f"CREATE SCHEMA {schema}")
    municipios = [(1, "SP", 100, 80), (2, "SP", 900, 450), (3, "DF", 10, 8),
                  (4, "MT", 10, 8), (5, "AC", 0, 0), (6, "ZZ", 10, 1)]
    linhas, dimensao = [], []
    for codigo, uf, aptos, comp in municipios:
        if uf != "ZZ":
            dimensao.append(dict(cd_municipio_tse=codigo, cd_municipio_ibge=codigo + 100,
                                 sg_uf=uf, nm_municipio=f"M{codigo}", regiao="Teste"))
        for ano, turno in [(2022, 1), (2022, 2), (2026, 1)] + (
            [(2026, 2)] if segundo_turno_2026 else []
        ):
            if codigo == 4 and ano == 2022:
                continue
            linhas.append(dict(
                ano=ano, turno=turno, cd_eleicao=ano * 10 + turno, sg_uf=uf,
                cd_municipio_tse=codigo, nm_municipio_tse=f"M{codigo}", nr_zona=1,
                aptos=aptos, comparecimento=comp,
                abstencoes=aptos - comp - (1 if uf == "ZZ" else 0),
                validos=comp, brancos=0, nulos=0, anulados=0, apurados_em_separado=0,
                eleitores_secoes_nao_instaladas=1 if uf == "ZZ" else 0, secoes=1,
                dt_geracao=date(2026, 10, 25), dt_ultima_totalizacao=date(2026, 10, 25),
                ingerido_em=datetime(2026, 10, 25, tzinfo=UTC), arquivo_origem="fixture",
            ))
    con.register("zona", pd.DataFrame(linhas))
    con.register("dim", pd.DataFrame(dimensao))
    con.execute("CREATE TABLE raw.raw_tse_zona AS SELECT * FROM zona")
    con.execute("CREATE TABLE raw.raw_dim_municipio AS SELECT * FROM dim")
    for path in sorted((ROOT / "sql").glob("0[123]_*.sql")):
        sql = path.read_text(encoding="utf-8").replace(f"{PROJETO}.", "")
        con.execute(sqlglot.transpile(sql, read="bigquery", write="duckdb")[0])
    return con


@pytest.fixture
def db():
    con = modelar()
    yield con
    con.close()


def test_razao_das_somas_e_exterior(db):
    uf = db.execute("""SELECT comparecimento_pct FROM marts.mart_uf_brasil_indicadores
                       WHERE ano=2022 AND turno=1 AND localidade='SP'""").fetchone()
    assert uf[0] == pytest.approx(53)
    totais = dict(db.execute("""SELECT nivel, SUM(aptos)
        FROM marts.mart_uf_brasil_indicadores WHERE ano=2022 AND turno=1
        GROUP BY nivel""").fetchall())
    assert totais == {"UF": 1010, "BRASIL": 1020, "EXTERIOR": 10}
    br = db.execute("""SELECT abstencoes, abstencoes_pct,
        eleitores_secoes_nao_instaladas FROM marts.mart_uf_brasil_indicadores
        WHERE ano=2022 AND turno=1 AND nivel='BRASIL'""").fetchone()
    assert br == pytest.approx((480, 100 * 480 / 1020, 1))
    benchmark = db.execute("""SELECT DISTINCT abstencoes_pct_brasil
        FROM marts.mart_municipio_benchmark WHERE ano=2022 AND turno=1""").fetchall()
    assert len(benchmark) == 1
    assert benchmark[0][0] == pytest.approx(br[1])


def test_ausencia_nao_vira_zero(db):
    novo = db.execute("""SELECT status_comparacao, aptos_base, comparecimento_delta_pp
        FROM marts.mart_municipio_comparativo WHERE cd_municipio_tse=4
        AND tipo_comparacao='anos' AND turno_base=1""").fetchone()
    assert novo == ("sem_base", None, None)
    pendente = db.execute("""SELECT status_comparacao, aptos_comparacao, aptos_variacao_pct
        FROM marts.mart_municipio_comparativo WHERE cd_municipio_tse=1
        AND tipo_comparacao='turnos' AND ano_base=2026""").fetchone()
    assert pendente == ("sem_comparacao", None, None)
    zero = db.execute("""SELECT comparecimento_pct, validos_pct
        FROM marts.mart_municipio_indicadores WHERE cd_municipio_tse=5 LIMIT 1""").fetchone()
    assert zero == (None, None)


def test_benchmark_percentil_e_empates(db):
    linhas = db.execute("""SELECT cd_municipio_tse, comparecimento_percentil_uf,
        comparecimento_delta_uf_pp FROM marts.mart_municipio_benchmark
        WHERE ano=2022 AND turno=1 ORDER BY cd_municipio_tse""").fetchall()
    assert linhas == [(1, 100, 27), (2, 0, -3), (3, None, 0), (5, None, None)]
    ranks = dict(db.execute("""SELECT localidade, validos_posicao_uf
        FROM marts.mart_uf_brasil_indicadores WHERE ano=2022 AND turno=1""").fetchall())
    assert ranks == {"SP": 1, "DF": 1, "AC": None, "BR": None, "ZZ": None}


def test_segundo_turno_entra_sem_alterar_sql():
    con = modelar(segundo_turno_2026=True)
    try:
        linha = con.execute("""SELECT status_comparacao, aptos_variacao_pct
            FROM marts.mart_municipio_comparativo WHERE cd_municipio_tse=1
            AND tipo_comparacao='turnos' AND ano_base=2026""").fetchone()
        assert linha == ("disponivel", 0)
    finally:
        con.close()


def test_exportacao_preserva_nulos_e_rejeita_duplicadas(tmp_path):
    df = pd.DataFrame({"id": [2, 1], "taxa": [None, 80.0]})
    path = tmp_path / "mart.parquet"
    assert gravar_parquet(df, path, ["id"])["linhas"] == 2
    assert pd.read_parquet(path)["taxa"].isna().sum() == 1
    with pytest.raises(ValueError, match="duplicada"):
        gravar_parquet(pd.concat([df, df]), path, ["id"])
