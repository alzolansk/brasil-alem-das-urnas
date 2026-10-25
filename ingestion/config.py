"""Caminhos e leitura do sources.yaml."""

from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parent.parent
SOURCES = RAIZ / "ingestion" / "sources.yaml"
RAW = RAIZ / "data" / "raw"
INTERIM = RAIZ / "data" / "interim"
GEO = RAIZ / "data" / "geo"


def carregar_sources() -> dict:
    with SOURCES.open(encoding="utf-8") as f:
        return yaml.safe_load(f)
