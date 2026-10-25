"""Regressões sobre os Parquets servidos, não apenas sobre fixtures do SQL."""

import os
import shutil

import pandas as pd
import pytest

from app.lib import data
from ingestion import parse_tse
from scripts.validar_marts import ROOT, validar_pacote


def test_pacote_publicado_inclui_exterior_uma_vez_e_taxas_ponderadas():
    assert validar_pacote(ROOT / "data/marts")


@pytest.mark.parametrize("erro", ["sem_exterior", "exterior_duplo", "media_simples",
                                  "benchmark_antigo"])
def test_rejeita_regressoes_nacionais(tmp_path, erro):
    for arquivo in (ROOT / "data/marts").glob("*.parquet"):
        if "perfil" not in arquivo.name:
            shutil.copy2(arquivo, tmp_path / arquivo.name)
    nome = "mart_uf_brasil_indicadores.parquet"
    df = pd.read_parquet(tmp_path / nome)
    if erro == "benchmark_antigo":
        nome = "mart_municipio_benchmark.parquet"
        df = pd.read_parquet(tmp_path / nome)
        df["abstencoes_pct_brasil"] -= 0.24
    else:
        for _, grupo in df.groupby(["ano", "turno"]):
            idx = grupo[grupo.nivel == "BRASIL"].index[0]
            if erro == "media_simples":
                df.loc[idx, "abstencoes_pct"] = grupo.loc[
                    grupo.nivel == "UF", "abstencoes_pct"].mean()
            else:
                sinal = -1 if erro == "sem_exterior" else 1
                df.loc[idx, "aptos"] += sinal * grupo.loc[
                    grupo.nivel == "EXTERIOR", "aptos"].sum()
    df.to_parquet(tmp_path / nome, index=False)
    with pytest.raises(AssertionError):
        validar_pacote(tmp_path, conferir_manifest=False)


def test_cache_aquecido_rele_arquivo_e_lista_municipal(tmp_path, monkeypatch):
    monkeypatch.setattr(data, "MARTS", tmp_path)
    nome = "mart_municipio_indicadores"
    df = pd.read_parquet(ROOT / "data/marts" / f"{nome}.parquet")
    caminho = tmp_path / f"{nome}.parquet"
    df.to_parquet(caminho)
    antigo = caminho.stat().st_mtime_ns
    antes = data.carregar(nome)
    municipios = data.municipios()
    df["aptos"] += 1
    df["nm_municipio"] = "Nome atualizado"
    df.to_parquet(caminho)
    os.utime(caminho, ns=(antigo + 1_000_000, antigo + 1_000_000))
    depois = data.carregar(nome)
    assert (depois.aptos == antes.aptos + 1).all()
    assert not municipios.nm_municipio.eq("Nome atualizado").any()
    assert data.municipios().nm_municipio.eq("Nome atualizado").all()


def test_parser_nao_soma_linha_agregada_brasil(monkeypatch):
    linhas = []
    for uf in ("SP", "ZZ", "BR"):
        linhas.append({
            "DS_CARGO": "Presidente", "SG_UF": uf, "ANO_ELEICAO": "2026",
            "NR_TURNO": "1", "CD_ELEICAO": "1", "CD_MUNICIPIO": "1",
            "NM_MUNICIPIO": "Teste", "NR_ZONA": "1", "DT_GERACAO": "25/10/2026",
            "DT_ULTIMA_TOTALIZACAO": "25/10/2026",
            **{c: "10" for c in parse_tse.CONTAGENS},
        })
    monkeypatch.setattr(parse_tse, "_ler_csv", lambda *args: pd.DataFrame(linhas))
    zona = parse_tse.parse_zona(None, 2026)
    assert zona.sg_uf.tolist() == ["SP", "ZZ"]
    assert zona.aptos.sum() == 20
