"""Malha municipal simplificada do IBGE (GeoJSON por UF) → data/geo/malha_{UF}.geojson."""

import json
import time

import requests

from ingestion.config import GEO, carregar_sources

UF_CODIGO = {
    "RO": 11, "AC": 12, "AM": 13, "RR": 14, "PA": 15, "AP": 16, "TO": 17, "MA": 21, "PI": 22,
    "CE": 23, "RN": 24, "PB": 25, "PE": 26, "AL": 27, "SE": 28, "BA": 29, "MG": 31, "ES": 32,
    "RJ": 33, "SP": 35, "PR": 41, "SC": 42, "RS": 43, "MS": 50, "MT": 51, "GO": 52, "DF": 53,
}  # fmt: skip


def _baixar_uf(url: str, tentativas: int = 3) -> dict | None:
    for i in range(tentativas):
        try:
            r = requests.get(url, timeout=(15, 120))
            if r.status_code == 200:
                return r.json()
        except requests.RequestException:
            pass
        time.sleep(2 * (i + 1))
    return None


def baixar_malhas(forcar: bool = False) -> list[str]:
    """Baixa a malha de cada UF; devolve as siglas que falharam."""
    url = carregar_sources()["ibge"]["malha_municipal"]["url"]
    GEO.mkdir(parents=True, exist_ok=True)
    falhas = []
    for sigla, cod in UF_CODIGO.items():
        destino = GEO / f"malha_{sigla}.geojson"
        if destino.exists() and not forcar:
            continue
        dados = _baixar_uf(url.format(uf=cod))
        if dados is None:
            falhas.append(sigla)
            continue
        for feat in dados.get("features", []):
            feat["properties"] = {"cd_municipio_ibge": int(feat["properties"]["codarea"])}
        destino.write_text(json.dumps(dados, separators=(",", ":")), encoding="utf-8")
    return falhas


if __name__ == "__main__":
    print("falhas:", baixar_malhas())
