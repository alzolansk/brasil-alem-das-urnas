"""Exporta as cinco marts após os testes SQL: python -m scripts.export_marts."""

import hashlib
import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from scripts.modelagem import PROJETO, ROOT, conectar, consultar, validar
from scripts.validar_marts import validar_pacote

MARTS = {
    "mart_zona_indicadores": ["ano", "turno", "sg_uf", "cd_municipio_tse", "nr_zona"],
    "mart_municipio_indicadores": ["ano", "turno", "sg_uf", "cd_municipio_tse"],
    "mart_uf_brasil_indicadores": ["ano", "turno", "nivel", "localidade"],
    "mart_municipio_comparativo": [
        "tipo_comparacao", "ano_base", "turno_base", "ano_comparacao", "turno_comparacao",
        "sg_uf", "cd_municipio_tse",
    ],
    "mart_municipio_benchmark": ["ano", "turno", "sg_uf", "cd_municipio_tse"],
}


def normalizar_datas(df):
    """dbdate (db_dtypes) quebra a leitura sem a lib; o app lê só Parquet puro."""
    for col in df.columns:
        if str(df[col].dtype) == "dbdate":
            df[col] = pd.to_datetime(df[col])
    return df


def gravar_parquet(df, path, chaves):
    df = normalizar_datas(df)
    if df.empty or df[chaves].isna().any().any() or df.duplicated(chaves).any():
        raise ValueError(f"{path.name}: tabela vazia ou chave inválida/duplicada")
    df = df.sort_values(chaves).reset_index(drop=True)
    df.to_parquet(path, index=False, compression="snappy")
    pd.testing.assert_frame_equal(df, pd.read_parquet(path))
    return {"linhas": len(df), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def exportar():
    client, local = conectar()
    testes = validar(client, local)
    destino = ROOT / "data/marts"
    destino.mkdir(parents=True, exist_ok=True)
    manifest = {
        "exportado_em": datetime.now(UTC).isoformat(), "projeto": PROJETO,
        "local": local, "testes": testes, "arquivos": {},
    }
    # Todas as leituras e verificações terminam antes de substituir os arquivos publicados.
    with tempfile.TemporaryDirectory(dir=destino) as temp:
        for tabela, chaves in MARTS.items():
            rows = consultar(client, local, f"SELECT * FROM `{PROJETO}.marts.{tabela}`")
            df = rows.to_dataframe(create_bqstorage_client=False)
            nome = f"{tabela}.parquet"
            manifest["arquivos"][nome] = gravar_parquet(df, Path(temp) / nome, chaves)
            print(f"{nome}: {len(df)} linhas", flush=True)
        validar_pacote(Path(temp), conferir_manifest=False)
        for nome in manifest["arquivos"]:
            (Path(temp) / nome).replace(destino / nome)
    # Parquets gerados fora do BigQuery (scripts.perfil_abstencao) mantêm a sua entrada.
    anterior = destino / "manifest.json"
    if anterior.exists():
        for nome, info in json.loads(anterior.read_text(encoding="utf-8"))["arquivos"].items():
            manifest["arquivos"].setdefault(nome, info)
    (destino / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    exportar()
