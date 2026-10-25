"""Roda a ingestão: baixa → parse → crosswalk → valida → grava Parquet em data/interim/.

Uso: python -m ingestion.pipeline [--sem-ibge] [--malha]
"""

import argparse
import sys

import pandas as pd

from ingestion import crosswalk, download, ibge_malha, parse_tse, validate
from ingestion.config import INTERIM, carregar_sources


def executar(usar_ibge_api: bool = True, malha: bool = False) -> int:
    cfg = carregar_sources()["tse"]["detalhe_votacao_munzona"]
    zonas, erros = [], []
    for ano in (2022, 2026):
        zip_path = download.arquivo_detalhe_votacao(ano)
        z = parse_tse.parse_zona(zip_path, ano)
        no_arquivo, pedidos = set(z.turno.unique()), set(cfg[ano]["turnos"])
        for t in sorted(pedidos - no_arquivo):
            erros.append(f"{ano}: turno {t} está em sources.yaml mas não no arquivo do TSE")
        for t in sorted(no_arquivo - pedidos):
            print(f"AVISO: {ano} turno {t} já está no arquivo do TSE; ative em sources.yaml")
        z = z[z.turno.isin(pedidos)]
        print(f"{ano}: {len(z)} linhas de zona (turnos {sorted(z.turno.unique())})")
        zonas.append(z)
    zona = pd.concat(zonas, ignore_index=True)

    cw = crosswalk.ler_crosswalk(download.arquivo_crosswalk())
    ibge = crosswalk.baixar_municipios_ibge() if usar_ibge_api else None
    dim = crosswalk.montar_dim_municipio(cw, ibge)
    municipio = parse_tse.agregar_municipio(zona)
    _, nao_casados = crosswalk.casar(municipio, dim)

    erros += (
        validate.validar_zona(zona)
        + validate.validar_municipios(municipio, nao_casados)
        + validate.validar_totais(zona)
    )

    INTERIM.mkdir(parents=True, exist_ok=True)
    zona.to_parquet(INTERIM / "zona.parquet", index=False)
    municipio.to_parquet(INTERIM / "municipio.parquet", index=False)
    dim.to_parquet(INTERIM / "dim_municipio.parquet", index=False)
    print(f"gravado em {INTERIM}")

    if malha:
        falhas = ibge_malha.baixar_malhas()
        if falhas:
            erros.append(f"malha municipal: falha em {falhas}")

    for e in erros:
        print("PROBLEMA:", e)
    print("OK" if not erros else f"{len(erros)} problema(s)")
    return 1 if erros else 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sem-ibge", action="store_true", help="não consulta a API do IBGE")
    p.add_argument("--malha", action="store_true", help="baixa também a malha municipal")
    a = p.parse_args()
    sys.exit(executar(not a.sem_ibge, a.malha))
