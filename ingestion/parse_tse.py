"""Leitura do detalhe_votacao_munzona do TSE: Presidente, nível zona, agregação por município."""

import zipfile
from pathlib import Path

import pandas as pd

from ingestion.config import carregar_sources

NULOS = ["#NULO#", "#NE#", "-1", "-3", ""]

CONTAGENS = {
    "QT_APTOS": "aptos",
    "QT_COMPARECIMENTO": "comparecimento",
    "QT_ABSTENCOES": "abstencoes",
    "QT_TOTAL_VOTOS_VALIDOS": "validos",
    "QT_VOTOS_BRANCOS": "brancos",
    "QT_TOTAL_VOTOS_NULOS": "nulos",
    "QT_TOTAL_VOTOS_ANULADOS": "anulados",
    "QT_VOTOS_ANULADOS_APU_SEP": "apurados_em_separado",
    "QT_ELEITORES_SECOES_NAO_INSTALADAS": "eleitores_secoes_nao_instaladas",
    "QT_TOTAL_SECOES": "secoes",
}
COLUNAS_CONTAGEM = list(CONTAGENS.values())

ID_ZONA = ["ano", "turno", "sg_uf", "cd_municipio_tse", "nr_zona"]


def _ler_csv(zip_path: Path, ano: int) -> pd.DataFrame:
    cfg = carregar_sources()["tse"]["detalhe_votacao_munzona"]
    nome = cfg["arquivo_csv"].format(ano=ano)
    with zipfile.ZipFile(zip_path) as z, z.open(nome) as f:
        return pd.read_csv(
            f,
            sep=cfg["separador"],
            encoding=cfg["encoding"],
            dtype=str,
            na_values=NULOS,
            keep_default_na=False,
        )


def parse_zona(zip_path: Path, ano: int, cargo: str | None = None) -> pd.DataFrame:
    """Uma linha por ano × turno × município × zona, só do cargo (Presidente), exterior incluso."""
    cargo = cargo or carregar_sources()["filtros"]["cargo"]
    bruto = _ler_csv(zip_path, ano)
    bruto = bruto[bruto["DS_CARGO"] == cargo]
    if bruto.empty:
        raise ValueError(f"Nenhuma linha de {cargo!r} em {zip_path}")

    df = pd.DataFrame(
        {
            "ano": bruto["ANO_ELEICAO"].astype("int16"),
            "turno": bruto["NR_TURNO"].astype("int8"),
            "cd_eleicao": bruto["CD_ELEICAO"].astype("int32"),
            "sg_uf": bruto["SG_UF"],
            "cd_municipio_tse": bruto["CD_MUNICIPIO"].astype("int32"),
            "nm_municipio_tse": bruto["NM_MUNICIPIO"],
            "nr_zona": bruto["NR_ZONA"].astype("int16"),
        }
    )
    for col_tse, col in CONTAGENS.items():
        df[col] = pd.to_numeric(bruto[col_tse], errors="coerce").astype("Int64")
    df["dt_geracao"] = pd.to_datetime(bruto["DT_GERACAO"], format="%d/%m/%Y").dt.date
    df["dt_ultima_totalizacao"] = pd.to_datetime(
        bruto["DT_ULTIMA_TOTALIZACAO"], format="%d/%m/%Y", errors="coerce"
    ).dt.date
    return df.sort_values(ID_ZONA).reset_index(drop=True)


def agregar_municipio(zona: pd.DataFrame) -> pd.DataFrame:
    """Soma as zonas de cada município (inclui `n_zonas`)."""
    chaves = ["ano", "turno", "sg_uf", "cd_municipio_tse"]
    agg = {c: "sum" for c in COLUNAS_CONTAGEM}
    agg.update(nm_municipio_tse="first", nr_zona="nunique")
    return zona.groupby(chaves, as_index=False).agg(agg).rename(columns={"nr_zona": "n_zonas"})
