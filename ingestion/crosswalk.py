"""Crosswalk código TSE ↔ IBGE (tabela oficial do TSE) e tabela de municípios/UF/região."""

import zipfile
from pathlib import Path

import pandas as pd
import requests

from ingestion.config import carregar_sources

REGIAO_POR_UF = {
    **dict.fromkeys(["AC", "AM", "AP", "PA", "RO", "RR", "TO"], "Norte"),
    **dict.fromkeys(["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"], "Nordeste"),
    **dict.fromkeys(["DF", "GO", "MS", "MT"], "Centro-Oeste"),
    **dict.fromkeys(["ES", "MG", "RJ", "SP"], "Sudeste"),
    **dict.fromkeys(["PR", "RS", "SC"], "Sul"),
}


def ler_crosswalk(zip_path: Path) -> pd.DataFrame:
    with zipfile.ZipFile(zip_path) as z, z.open("municipio_tse_ibge.csv") as f:
        d = pd.read_csv(f, sep=";", encoding="latin-1", dtype=str)
    return pd.DataFrame(
        {
            "cd_municipio_tse": d["CD_MUNICIPIO_TSE"].astype("int32"),
            "cd_municipio_ibge": d["CD_MUNICIPIO_IBGE"].astype("int32"),
            "sg_uf": d["SG_UF"],
            "nm_municipio": d["NM_MUNICIPIO_IBGE"],
            "nm_municipio_tse": d["NM_MUNICIPIO_TSE"],
        }
    )


def baixar_municipios_ibge() -> pd.DataFrame:
    """Município, UF e região direto da API de localidades do IBGE."""
    url = carregar_sources()["ibge"]["municipios"]["url"]
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    linhas = []
    for m in r.json():
        micro = m.get("microrregiao")
        if micro:
            uf = micro["mesorregiao"]["UF"]
        else:
            uf = m["regiao-imediata"]["regiao-intermediaria"]["UF"]
        linhas.append(
            {
                "cd_municipio_ibge": m["id"],
                "nm_municipio": m["nome"],
                "sg_uf": uf["sigla"],
                "regiao": uf["regiao"]["nome"],
            }
        )
    return pd.DataFrame(linhas).astype({"cd_municipio_ibge": "int32"})


def montar_dim_municipio(crosswalk: pd.DataFrame, ibge: pd.DataFrame | None = None) -> pd.DataFrame:
    """Dimensão município: código TSE + IBGE, nome, UF, região. Junta sempre por código."""
    dim = crosswalk.copy()
    dim["regiao"] = dim["sg_uf"].map(REGIAO_POR_UF)
    if ibge is not None:
        # a região do IBGE prevalece quando disponível; serve também de conferência
        r = ibge.set_index("cd_municipio_ibge")["regiao"]
        dim["regiao"] = dim["cd_municipio_ibge"].map(r).fillna(dim["regiao"])
    return dim.sort_values("cd_municipio_ibge").reset_index(drop=True)


def casar(zona_ou_mun: pd.DataFrame, dim: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Anexa o código IBGE. Retorna (casados, nao_casados); o exterior (ZZ) fica de fora."""
    base = zona_ou_mun[zona_ou_mun["sg_uf"] != "ZZ"]
    m = base.merge(
        dim[["cd_municipio_tse", "cd_municipio_ibge", "nm_municipio", "regiao"]],
        on="cd_municipio_tse",
        how="left",
    )
    sem = m["cd_municipio_ibge"].isna()
    return m[~sem], m[sem]
