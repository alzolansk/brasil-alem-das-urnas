"""Reexecuta SQL nacional e benchmarks a partir da mart municipal versionada.

Não baixa fontes, não altera contagens municipais e não exige BigQuery.
Uso: python -m scripts.regenerar_nacional (dependências de desenvolvimento).
"""

import hashlib
import json
import shutil
import tempfile
from datetime import UTC, datetime
from pathlib import Path

import duckdb
import pandas as pd
import sqlglot

from scripts.export_marts import MARTS, gravar_parquet
from scripts.modelagem import PROJETO, ROOT
from scripts.validar_marts import validar_pacote


def regenerar():
    destino = ROOT / "data/marts"
    manifest = json.loads((destino / "manifest.json").read_text(encoding="utf-8"))
    con = duckdb.connect()
    fontes = {}
    try:
        con.execute("CREATE SCHEMA staging")
        con.execute("CREATE SCHEMA marts")
        mun = pd.read_parquet(destino / "mart_municipio_indicadores.parquet")
        con.register("municipios", mun)
        con.execute("CREATE TABLE staging.int_municipio AS SELECT * FROM municipios")
        con.execute("CREATE TABLE marts.mart_municipio_indicadores AS SELECT * FROM municipios")
        with tempfile.TemporaryDirectory(dir=destino) as temp:
            pasta = Path(temp)
            for arquivo in destino.glob("*.parquet"):
                shutil.copy2(arquivo, pasta / arquivo.name)
            for nome_sql, tabela in (
                ("03_mart_03_uf_brasil_indicadores.sql", "mart_uf_brasil_indicadores"),
                ("03_mart_05_municipio_benchmark.sql", "mart_municipio_benchmark"),
            ):
                arquivo = ROOT / "sql" / nome_sql
                fontes[nome_sql] = hashlib.sha256(arquivo.read_bytes()).hexdigest()
                sql = arquivo.read_text(encoding="utf-8").replace(f"{PROJETO}.", "")
                con.execute(sqlglot.transpile(sql, read="bigquery", write="duckdb")[0])
                df = con.execute(f"SELECT * FROM marts.{tabela}").df()
                nome = f"{tabela}.parquet"
                manifest["arquivos"][nome] = gravar_parquet(df, pasta / nome, MARTS[tabela])
            totais = validar_pacote(pasta, conferir_manifest=False)
            manifest["reconciliacao_nacional"] = {
                "executado_em": datetime.now(UTC).isoformat(),
                "motor": "DuckDB / SQLGlot (SQL do projeto)",
                "sql_sha256": fontes,
                "fonte_sha256": manifest["arquivos"][
                    "mart_municipio_indicadores.parquet"]["sha256"],
                "totais": totais,
            }
            (pasta / "manifest.json").write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            validar_pacote(pasta)
            for nome in ("mart_uf_brasil_indicadores.parquet", "mart_municipio_benchmark.parquet",
                         "manifest.json"):
                (pasta / nome).replace(destino / nome)
    finally:
        con.close()
    print(json.dumps(totais, indent=2))


if __name__ == "__main__":
    regenerar()
