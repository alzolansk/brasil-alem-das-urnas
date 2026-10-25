"""Recria tudo em um comando: ingestão → carga no raw → SQL + testes → export das marts.

Uso: python -m scripts.rebuild [--sem-bq]
Requer `gcloud auth application-default login` (menos com --sem-bq, que para após a ingestão).
Para em qualquer falha, antes de substituir os Parquets publicados em data/marts/.
"""

import argparse
import sys

from ingestion import load_bq, pipeline
from scripts import export_marts, modelagem


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--sem-bq", action="store_true", help="só a ingestão local (data/interim/)")
    a = p.parse_args()
    print("== 1/4 ingestão", flush=True)
    if pipeline.executar() != 0:
        print("Ingestão com problemas: nada foi carregado no BigQuery.")
        return 1
    if a.sem_bq:
        return 0
    print("== 2/4 carga no dataset raw", flush=True)
    load_bq.carregar()
    print("== 3/4 SQL (staging, intermediate, marts) e testes", flush=True)
    modelagem.executar()
    print("== 4/4 exportação das marts", flush=True)
    export_marts.exportar()
    print("Pronto: confira `git diff --stat data/marts`, rode o pytest e faça o commit.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
