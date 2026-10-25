"""Downloader idempotente: usa o arquivo local se existir, senão baixa da URL."""

import argparse
from pathlib import Path

import requests

from ingestion.config import RAIZ, carregar_sources


def baixar(url: str, destino: Path, forcar: bool = False) -> Path:
    if destino.exists() and destino.stat().st_size > 0 and not forcar:
        return destino
    destino.parent.mkdir(parents=True, exist_ok=True)
    tmp = destino.with_suffix(destino.suffix + ".part")
    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        with tmp.open("wb") as f:
            for bloco in r.iter_content(1 << 20):
                f.write(bloco)
    tmp.replace(destino)
    return destino


def arquivo_detalhe_votacao(ano: int, forcar: bool = False) -> Path:
    cfg = carregar_sources()["tse"]["detalhe_votacao_munzona"][ano]
    return baixar(cfg["url"], RAIZ / cfg["arquivo_local"], forcar)


def arquivo_perfil(ano: int, forcar: bool = False) -> Path:
    cfg = carregar_sources()["tse"]["perfil_comparecimento_abstencao"][ano]
    return baixar(cfg["url"], RAIZ / cfg["arquivo_local"], forcar)


def arquivo_crosswalk(forcar: bool = False) -> Path:
    cfg = carregar_sources()["tse"]["municipio_tse_ibge"]
    return baixar(
        cfg["url"], RAIZ / "data/raw/tse/municipio_tse_ibge/municipio_tse_ibge.zip", forcar
    )


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--forcar", action="store_true", help="baixa de novo mesmo se já existir")
    args = p.parse_args()
    for ano in (2022, 2026):
        print(arquivo_detalhe_votacao(ano, args.forcar))
    print(arquivo_crosswalk(args.forcar))


if __name__ == "__main__":
    main()
