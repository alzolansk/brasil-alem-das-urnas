"""Tarefa 4.1: o TSE já publicou o 2º turno de 2026 (Presidente) no detalhe_votacao_munzona?

Uso: python -m scripts.segundo_turno [--ativar]

Baixa o zip de 2026 numa pasta temporária (≈2,5 MB) e procura linhas de Presidente do 2º turno.
Com --ativar, se o 2º turno estiver completo (5.571 municípios), substitui o zip local de 2026 e
acrescenta o turno 2 em sources.yaml; depois é só rodar `python -m scripts.rebuild`.
Saída: 0 = publicado e completo; 1 = ainda não (ou incompleto).
"""

import argparse
import re
import shutil
import sys
import tempfile
from pathlib import Path

import requests

from ingestion import download, parse_tse, validate
from ingestion.config import RAIZ, SOURCES, carregar_sources

ANO = 2026


def verificar(pasta: Path) -> tuple[bool, Path, str]:
    cfg = carregar_sources()["tse"]["detalhe_votacao_munzona"][ANO]
    cab = requests.head(cfg["url"], timeout=30).headers
    print(f"TSE: Last-Modified {cab.get('Last-Modified')}, {cab.get('Content-Length')} bytes")
    zip_path = download.baixar(cfg["url"], pasta / "detalhe_votacao_munzona_2026.zip", forcar=True)
    zona = parse_tse.parse_zona(zip_path, ANO)
    t2 = zona[(zona.turno == 2) & (zona.sg_uf != "ZZ")]
    if t2.empty:
        return False, zip_path, "2º turno ainda não está no arquivo do TSE"
    n = t2.cd_municipio_tse.nunique()
    esperado = validate.MUNICIPIOS_ESPERADOS[ANO]
    resumo = (f"2º turno no arquivo: {len(t2)} zonas, {n} municípios (esperado {esperado}), "
              f"gerado em {t2.dt_geracao.max():%d/%m/%Y}, "
              f"última totalização {t2.dt_ultima_totalizacao.max():%d/%m/%Y}")
    erros = validate.validar_zona(zona[zona.turno == 2])
    return n == esperado and not erros, zip_path, "\n".join([resumo, *erros])


def ativar(zip_path: Path) -> None:
    cfg = carregar_sources()["tse"]["detalhe_votacao_munzona"][ANO]
    destino = RAIZ / cfg["arquivo_local"]
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(zip_path, destino)
    texto = SOURCES.read_text(encoding="utf-8")
    bloco = re.compile(r"(  2026:\n(?:    .*\n)*?      turnos: )\[1\][^\n]*")
    novo, n = bloco.subn(r"\g<1>[1, 2]", texto)
    if n:
        SOURCES.write_text(novo, encoding="utf-8")
    print(f"zip local substituído ({destino.relative_to(RAIZ)}); turnos de 2026: [1, 2]")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--ativar", action="store_true", help="usa o arquivo novo se estiver completo")
    a = p.parse_args()
    with tempfile.TemporaryDirectory() as temp:
        pronto, zip_path, resumo = verificar(Path(temp))
        print(resumo)
        if pronto and a.ativar:
            ativar(zip_path)
    print("PUBLICADO" if pronto else "AINDA NÃO")
    return 0 if pronto else 1


if __name__ == "__main__":
    sys.exit(main())
