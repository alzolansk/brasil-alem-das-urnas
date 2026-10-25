"""Carrega os Parquet de data/interim/ no dataset `raw` do BigQuery Sandbox (WRITE_TRUNCATE).

Requer `gcloud auth application-default login`. Sandbox: sem DML, então só load jobs.
Uso: python -m ingestion.load_bq [--projeto brasil-alem-das-urnas-2026] [--dataset raw]
"""

import argparse
from datetime import UTC, datetime

import pandas as pd

from ingestion.config import INTERIM

PROJETO = "brasil-alem-das-urnas-2026"
LOCAL = "southamerica-east1"
TABELAS = {
    "raw_tse_zona": "zona.parquet",
    "raw_tse_municipio": "municipio.parquet",
    "raw_dim_municipio": "dim_municipio.parquet",
}


def carregar(projeto: str = PROJETO, dataset: str = "raw") -> None:
    from google.api_core.exceptions import NotFound
    from google.cloud import bigquery  # import tardio: o resto do pipeline não exige GCP

    client = bigquery.Client(project=projeto)
    ingerido_em = datetime.now(UTC)
    try:  # usa a região do dataset existente (load jobs precisam rodar na mesma região)
        local = client.get_dataset(f"{projeto}.{dataset}").location
    except NotFound:
        ds = bigquery.Dataset(f"{projeto}.{dataset}")
        ds.location = LOCAL
        client.create_dataset(ds)
        local = LOCAL
    cfg = bigquery.LoadJobConfig(write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE)
    for tabela, arquivo in TABELAS.items():
        df = pd.read_parquet(INTERIM / arquivo)
        df["ingerido_em"] = ingerido_em
        df["arquivo_origem"] = arquivo
        destino = f"{projeto}.{dataset}.{tabela}"
        client.load_table_from_dataframe(df, destino, job_config=cfg, location=local).result()
        print(f"{destino}: {len(df)} linhas")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--projeto", default=PROJETO)
    p.add_argument("--dataset", default="raw")
    a = p.parse_args()
    carregar(a.projeto, a.dataset)
