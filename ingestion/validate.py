"""Validações de consistência da ingestão; cada função devolve a lista de problemas."""

import pandas as pd

from ingestion.parse_tse import COLUNAS_CONTAGEM, ID_ZONA

# Número de municípios (sem exterior) por ano, conforme docs/metodologia.md
MUNICIPIOS_ESPERADOS = {2022: 5570, 2026: 5571}
# Total oficial (com exterior), 1º turno 2022 — conferência formal em docs/validacao.md
TOTAL_2022_T1 = {"aptos": 156_454_011, "comparecimento": 123_682_372}


def validar_zona(zona: pd.DataFrame) -> list[str]:
    erros = []
    if zona.duplicated(ID_ZONA).any():
        erros.append(
            f"chave ano/turno/uf/município/zona duplicada: {zona.duplicated(ID_ZONA).sum()}"
        )
    nulos = zona[COLUNAS_CONTAGEM].isna().sum()
    for col, n in nulos[nulos > 0].items():
        erros.append(f"{col}: {n} valores nulos")
    if (zona[COLUNAS_CONTAGEM] < 0).any().any():
        erros.append("contagem negativa")

    z = zona[COLUNAS_CONTAGEM].astype("int64")
    soma_comp = z.comparecimento + z.abstencoes + z.eleitores_secoes_nao_instaladas
    n = (z.aptos != soma_comp).sum()
    if n:
        erros.append(f"aptos != comparecimento + abstenções + seções não instaladas em {n} linhas")

    soma_votos = z.validos + z.brancos + z.nulos + z.anulados + z.apurados_em_separado
    n = (z.comparecimento != soma_votos).sum()
    if n:
        erros.append(f"comparecimento != válidos + brancos + nulos + anulados + apu. sep. em {n}")

    for col in ("anulados", "apurados_em_separado"):
        if (z[col] != 0).any():
            erros.append(f"{col} deixou de ser 0 para Presidente (revisar tratamento)")
    return erros


def validar_municipios(municipio: pd.DataFrame, nao_casados: pd.DataFrame) -> list[str]:
    erros = []
    for (ano, turno), g in municipio[municipio.sg_uf != "ZZ"].groupby(["ano", "turno"]):
        esperado = MUNICIPIOS_ESPERADOS.get(int(ano))
        if esperado and g.cd_municipio_tse.nunique() != esperado:
            erros.append(
                f"{ano} T{turno}: {g.cd_municipio_tse.nunique()} municípios, esperado {esperado}"
            )
    if len(nao_casados):
        nomes = nao_casados[
            ["ano", "turno", "cd_municipio_tse", "nm_municipio_tse"]
        ].drop_duplicates("cd_municipio_tse")
        erros.append(f"{len(nomes)} municípios sem código IBGE:\n{nomes.to_string(index=False)}")
    return erros


def validar_totais(zona: pd.DataFrame) -> list[str]:
    s = zona[(zona.ano == 2022) & (zona.turno == 1)][list(TOTAL_2022_T1)].astype("int64").sum()
    return [f"Brasil 2022 T1 {k}: {s[k]:,} != {v:,}" for k, v in TOTAL_2022_T1.items() if s[k] != v]
