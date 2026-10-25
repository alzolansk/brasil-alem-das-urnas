"""Seção "Quem ficou em casa?": perfil do TSE → data/marts/mart_perfil_abstencao.parquet.

Uso: python -m scripts.perfil_abstencao
Sem BigQuery: lê os zips de data/raw/ (ou baixa), valida, agrega por município × perfil e só
substitui o Parquet publicado se todas as verificações passarem (≈3 min; os CSV somam 5,5 GB).
Evidência em docs/validacao/perfil_execucao.json; hash e linhas em data/marts/manifest.json.
"""

import json
import sys
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from ingestion import crosswalk, download, perfil, validate
from ingestion.config import RAIZ, carregar_sources
from scripts.export_marts import gravar_parquet

NOME = "mart_perfil_abstencao"
CHAVE = ["ano", "turno", "cd_municipio_ibge", "dimensao", "cd_categoria"]
MARTS = RAIZ / "data" / "marts"
EVIDENCIA = RAIZ / "docs" / "validacao" / "perfil_execucao.json"
# Painel de comparecimento/abstenção do TSE, Brasil com exterior (docs/validacao.md)
PAINEL_TSE = {
    (2022, 1): {"aptos": 156_454_011, "comparecimento": 123_714_335},
    (2022, 2): {"aptos": 156_454_011, "comparecimento": 124_267_614},
    (2026, 1): {"aptos": 158_745_463, "comparecimento": 125_277_230},
}


def _resultados() -> pd.DataFrame:
    """Aptos e abstenções do detalhe_votacao_munzona, já publicados no app."""
    m = pd.read_parquet(MARTS / "mart_municipio_indicadores.parquet")
    m = m[~m["exterior"].astype(bool)]
    return m[["ano", "turno", "cd_municipio_ibge", "aptos", "abstencoes"]].astype("int64")


def _gravar_json(caminho: Path, conteudo: dict) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    texto = json.dumps(conteudo, ensure_ascii=False, indent=2) + "\n"
    caminho.write_text(texto, encoding="utf-8")


def executar() -> int:
    cfg = carregar_sources()["tse"]["perfil_comparecimento_abstencao"]
    marginais, erros, fontes = [], [], {}
    for ano in (2022, 2026):
        inicio = time.time()
        zip_path = download.arquivo_perfil(ano)
        df, v = perfil.ler(zip_path, ano)
        no_arquivo, pedidos = set(df["turno"].unique().tolist()), cfg[ano]["turnos"]
        erros += perfil.validar_arquivo(ano, v, pedidos, no_arquivo)
        for t in sorted(no_arquivo - set(pedidos)):
            print(f"AVISO: {ano} turno {t} já está no perfil do TSE; ative em sources.yaml")
        marginais.append(df[df["turno"].isin(pedidos)])
        fontes[ano] = {"arquivo": zip_path.relative_to(RAIZ).as_posix(), "linhas": v["linhas"],
                       "dt_geracao": v["dt_geracao"], "turnos": pedidos}
        print(f"{ano}: {v['linhas']:,} linhas lidas em {time.time() - inicio:.0f} s", flush=True)
    marginais = pd.concat(marginais, ignore_index=True)

    dim = crosswalk.montar_dim_municipio(crosswalk.ler_crosswalk(download.arquivo_crosswalk()))
    mart, problemas = perfil.montar_mart(marginais, dim)
    erros += problemas + perfil.validar_mart(mart, validate.MUNICIPIOS_ESPERADOS)
    totais, problemas = perfil.conferir_totais(marginais, PAINEL_TSE)
    erros += problemas
    categorias = {
        ano: sorted(map(list, g.loc[g["informado"], ["dimensao", "cd_categoria"]]
                        .drop_duplicates().itertuples(index=False)))
        for ano, g in mart.groupby("ano")
    }  # fmt: skip

    for e in erros:
        print("PROBLEMA:", e)
    if erros:
        print(f"{len(erros)} problema(s): {NOME}.parquet não foi substituído")
        return 1

    with tempfile.TemporaryDirectory(dir=MARTS) as temp:
        info = gravar_parquet(mart, Path(temp) / f"{NOME}.parquet", CHAVE)
        (Path(temp) / f"{NOME}.parquet").replace(MARTS / f"{NOME}.parquet")
    manifest_path = MARTS / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["arquivos"][f"{NOME}.parquet"] = info
    _gravar_json(manifest_path, manifest)

    _gravar_json(EVIDENCIA, {
        "executado_em": datetime.now(UTC).isoformat(),
        "fontes": fontes,
        "mart": {"arquivo": f"data/marts/{NOME}.parquet", **info},
        "problemas": erros,
        "totais_brasil_com_exterior_vs_painel_tse": totais,
        "categorias_informadas_iguais_entre_anos": len({json.dumps(c) for c in categorias.values()})
        == 1,
        "perfil_vs_detalhe_votacao_por_municipio": perfil.comparar_com_resultados(
            mart, _resultados()
        ),
    })
    print(f"{NOME}.parquet: {info['linhas']:,} linhas. Evidência em {EVIDENCIA.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    sys.exit(executar())
