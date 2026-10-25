"""Execute manualmente: python -m scripts.modelagem [--somente-testes]."""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from google.cloud import bigquery

ROOT = Path(__file__).resolve().parents[1]
PROJETO = "brasil-alem-das-urnas-2026"


def conectar():
    client = bigquery.Client(project=PROJETO)
    locais = {
        client.get_dataset(f"{PROJETO}.{ds}", timeout=30).location
        for ds in ("raw", "staging", "marts")
    }
    if len(locais) != 1:
        raise ValueError(f"Datasets em regiões diferentes: {locais}")
    return client, locais.pop()


def consultar(client, local, sql):
    return client.query(
        sql, location=local,
        job_config=bigquery.QueryJobConfig(maximum_bytes_billed=1_000_000_000),
        timeout=30,
    ).result(timeout=300)


def validar(client, local):
    resultados = []
    for path in sorted((ROOT / "sql/tests").glob("*.sql")):
        linhas = list(consultar(client, local, path.read_text(encoding="utf-8")))
        resultados.append({"teste": path.name, "falhas": len(linhas)})
        print(f"{path.name}: {len(linhas)} falhas", flush=True)
        if linhas:
            raise ValueError(f"{path.name}: {len(linhas)} falhas; amostra: {dict(linhas[0])}")
    if not resultados:
        raise ValueError("Nenhum teste SQL encontrado")
    return resultados


def executar(somente_testes=False):
    client, local = conectar()
    execucoes = []
    if not somente_testes:
        for path in sorted((ROOT / "sql").glob("0[123]_*.sql")):
            result = consultar(client, local, path.read_text(encoding="utf-8"))
            execucoes.append({"arquivo": path.name, "job_id": result.job_id})
            print(f"Executado: {path.name}", flush=True)
    testes = validar(client, local)
    evidencia = ROOT / "docs/validacao/fase2_execucao.json"
    evidencia.parent.mkdir(parents=True, exist_ok=True)
    evidencia.write_text(json.dumps({
        "executado_em": datetime.now(UTC).isoformat(), "projeto": PROJETO,
        "local": local, "execucoes": execucoes, "testes": testes,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--somente-testes", action="store_true")
    executar(parser.parse_args().somente_testes)
