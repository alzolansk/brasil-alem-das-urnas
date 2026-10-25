"""Valida o pacote realmente servido pelo app, sem GCP: python -m scripts.validar_marts."""

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from ingestion.parse_tse import COLUNAS_CONTAGEM

ROOT = Path(__file__).resolve().parents[1]
CHAVE = ["ano", "turno"]
TAXAS = {
    "comparecimento": ("comparecimento", "aptos"),
    "abstencoes": ("abstencoes", "aptos"),
    "validos": ("validos", "comparecimento"),
    "brancos": ("brancos", "comparecimento"),
    "nulos": ("nulos", "comparecimento"),
    "brancos_nulos": (None, "comparecimento"),
}


def validar_pacote(pasta: Path, conferir_manifest=True):
    tabelas = {nome: pd.read_parquet(pasta / f"mart_{nome}.parquet") for nome in (
        "zona_indicadores", "municipio_indicadores", "uf_brasil_indicadores",
        "municipio_benchmark",
    )}
    z, m, u, b = tabelas.values()
    for df, chave in ((z, CHAVE + ["sg_uf", "cd_municipio_tse", "nr_zona"]),
                      (m, CHAVE + ["sg_uf", "cd_municipio_tse"]),
                      (u, CHAVE + ["nivel", "localidade"]),
                      (b, CHAVE + ["sg_uf", "cd_municipio_tse"])):
        assert not df.empty and not df.duplicated(chave).any(), "chaves duplicadas/vazias"
        assert (df.aptos == df.comparecimento + df.abstencoes
                + df.eleitores_secoes_nao_instaladas).all(), "seções não instaladas"
        for indicador, (num, den) in TAXAS.items():
            numerador = df[num] if num else df.brancos + df.nulos
            esperado = 100 * numerador / df[den].replace(0, np.nan)
            assert np.allclose(df[f"{indicador}_pct"].astype(float),
                               esperado.astype(float), equal_nan=True), indicador
    assert m.exterior.eq(m.sg_uf.eq("ZZ")).all(), "flag exterior"
    assert not b.exterior.any() and not b.sg_uf.eq("ZZ").any(), "ranking municipal"
    assert u[u.nivel == "UF"].localidade.ne("ZZ").all(), "ranking UF"
    assert u[u.nivel == "EXTERIOR"].localidade.eq("ZZ").all(), "exterior"
    for indicador in TAXAS:
        assert u.loc[u.nivel != "UF", f"{indicador}_posicao_uf"].isna().all()
    totais = []
    for (ano, turno), mun in m.groupby(CHAVE):
        uf = u[(u.ano == ano) & (u.turno == turno)]
        nacional = uf[uf.nivel == "BRASIL"]
        assert len(nacional) == 1, "uma linha nacional por eleição/turno"
        assert (uf.nivel == "EXTERIOR").sum() == 1, "um exterior"
        assert (uf.nivel == "UF").sum() == 27, "27 UFs"
        br = nacional.iloc[0]
        zonas = z[(z.ano == ano) & (z.turno == turno)]
        for col in COLUNAS_CONTAGEM:
            assert br[col] == mun[col].sum() == zonas[col].sum(), f"total {col}"
            assert br[col] == uf.loc[uf.nivel.isin(["UF", "EXTERIOR"]), col].sum(), col
        bench = b[(b.ano == ano) & (b.turno == turno)]
        assert len(bench) == len(mun[~mun.exterior]), "cobertura benchmark"
        for indicador in TAXAS:
            taxa = br[f"{indicador}_pct"]
            assert np.allclose(bench[f"{indicador}_pct_brasil"], taxa), "benchmark Brasil"
            assert np.allclose(bench[f"{indicador}_delta_brasil_pp"],
                               bench[f"{indicador}_pct"] - taxa), "delta Brasil"
        totais.append({"ano": int(ano), "turno": int(turno),
                       **{c: int(br[c]) for c in COLUNAS_CONTAGEM},
                       "abstencoes_pct": float(br.abstencoes_pct)})
    assert set(map(tuple, u[CHAVE].values)) == set(map(tuple, m[CHAVE].values))
    if conferir_manifest:
        manifest = json.loads((pasta / "manifest.json").read_text(encoding="utf-8"))
        for nome, info in manifest["arquivos"].items():
            arquivo = pasta / nome
            assert hashlib.sha256(arquivo.read_bytes()).hexdigest() == info["sha256"], nome
            assert len(pd.read_parquet(arquivo)) == info["linhas"], nome
    return totais


if __name__ == "__main__":
    print(json.dumps(validar_pacote(ROOT / "data/marts"), indent=2))
