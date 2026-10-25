"""Baixa os resultados oficiais para conferência, sem substituir os brutos ou as marts."""

import hashlib
import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import requests

from ingestion.config import RAIZ, carregar_sources
from ingestion.parse_tse import COLUNAS_CONTAGEM, ID_ZONA, parse_zona


def conferir():
    cfg = carregar_sources()["tse"]["detalhe_votacao_munzona"]
    mart = pd.read_parquet(RAIZ / "data/marts/mart_uf_brasil_indicadores.parquet")
    evidencia = {"conferido_em": datetime.now(UTC).isoformat(), "fontes": []}
    with tempfile.TemporaryDirectory() as temp:
        for ano in (2022, 2026):
            resposta = requests.get(cfg[ano]["url"], timeout=120)
            resposta.raise_for_status()
            arquivo = Path(temp) / f"{ano}.zip"
            arquivo.write_bytes(resposta.content)
            zona = parse_zona(arquivo, ano)
            totais = []
            for turno, df in zona.groupby("turno"):
                br = mart[(mart.ano == ano) & (mart.turno == turno) & (mart.nivel == "BRASIL")]
                soma = {c: int(df[c].sum()) for c in COLUNAS_CONTAGEM}
                igual = len(br) == 1 and all(int(br.iloc[0][c]) == v for c, v in soma.items())
                totais.append({"turno": int(turno), "linhas_zona": len(df), **soma,
                               "abstencoes_pct": 100 * soma["abstencoes"] / soma["aptos"],
                               "igual_mart": igual})
                if turno in cfg[ano]["turnos"] and not igual:
                    raise ValueError(f"Fonte oficial difere da mart: {ano} T{turno}: {soma}")
            local = RAIZ / cfg[ano]["arquivo_local"]
            zona_local = parse_zona(local, ano)
            colunas = ID_ZONA + COLUNAS_CONTAGEM
            evidencia["fontes"].append({
                "ano": ano, "url": cfg[ano]["url"],
                "sha256_download": hashlib.sha256(resposta.content).hexdigest(),
                "sha256_bruto_local": hashlib.sha256(local.read_bytes()).hexdigest(),
                "dt_geracao": sorted(str(d) for d in zona.dt_geracao.unique()),
                "dt_geracao_bruto_local": sorted(str(d) for d in zona_local.dt_geracao.unique()),
                "contagens_por_zona_iguais_bruto_local": zona[colunas].equals(zona_local[colunas]),
                "ufs": sorted(zona.sg_uf.unique().tolist()), "totais": totais,
            })
    alvo = RAIZ / "docs/validacao/conferencia_nacional_fontes.json"
    alvo.write_text(json.dumps(evidencia, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(alvo)


if __name__ == "__main__":
    conferir()
