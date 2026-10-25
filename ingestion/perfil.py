"""Leitura do perfil_comparecimento_abstencao do TSE e agregação por município × perfil.

Cada linha do CSV é uma combinação de zona × gênero × estado civil × faixa etária × escolaridade ×
cor/raça × demais campos do cadastro. Não há linhas de total: a soma das linhas de uma dimensão
reproduz o total do município. Guardamos só as marginais (uma dimensão por vez), nunca cruzamentos.
"""

import zipfile
from pathlib import Path

import pandas as pd

from ingestion.config import carregar_sources

QT = {"QT_APTOS": "aptos", "QT_COMPARECIMENTO": "comparecimento", "QT_ABSTENCAO": "abstencoes"}
CONTAGENS = list(QT.values())

# Categorias oficiais (leiame do TSE). código -> (rótulo, informado). O rótulo, sem diferenciar
# maiúsculas, tem de ser igual à descrição do TSE (DS_*); "informado" = entra nos gráficos.
GENERO = {0: ("Não informado", False), 2: ("Masculino", True), 4: ("Feminino", True)}
ESCOLARIDADE = {
    0: ("Não informado", False),
    1: ("Analfabeto", True),
    2: ("Lê e escreve", True),
    3: ("Ensino fundamental incompleto", True),
    4: ("Ensino fundamental completo", True),
    5: ("Ensino médio incompleto", True),
    6: ("Ensino médio completo", True),
    7: ("Superior incompleto", True),
    8: ("Superior completo", True),
}
FAIXA_ETARIA = {
    -3: ("Inválido", False),
    1600: ("16 anos", True), 1700: ("17 anos", True), 1800: ("18 anos", True),
    1900: ("19 anos", True), 2000: ("20 anos", True), 2124: ("21 a 24 anos", True),
    2529: ("25 a 29 anos", True), 3034: ("30 a 34 anos", True), 3539: ("35 a 39 anos", True),
    4044: ("40 a 44 anos", True), 4549: ("45 a 49 anos", True), 5054: ("50 a 54 anos", True),
    5559: ("55 a 59 anos", True), 6064: ("60 a 64 anos", True), 6569: ("65 a 69 anos", True),
    7074: ("70 a 74 anos", True), 7579: ("75 a 79 anos", True), 8084: ("80 a 84 anos", True),
    8589: ("85 a 89 anos", True), 9094: ("90 a 94 anos", True), 9599: ("95 a 99 anos", True),
    9999: ("100 anos ou mais", True),
}  # fmt: skip
# Voto facultativo (Constituição, art. 14, § 1º, II): analfabetos, maiores de 70 anos e quem tem
# 16 ou 17 anos. Por isso as faixas de 18 a 69 anos também incluem quem não é obrigado a votar.
FACULTATIVO = {
    "faixa_etaria": {1600, 1700, 7074, 7579, 8084, 8589, 9094, 9599, 9999},
    "escolaridade": {1},  # Analfabeto
}

# dimensão -> (sufixo da coluna no CSV por ano, categorias)
DIMENSOES = {
    "genero": ({2022: "GENERO", 2026: "GENERO"}, GENERO),
    "faixa_etaria": ({2022: "FAIXA_ETARIA", 2026: "FAIXA_ETARIA"}, FAIXA_ETARIA),
    "escolaridade": ({2022: "GRAU_ESCOLARIDADE", 2026: "GRAU_INSTRUCAO"}, ESCOLARIDADE),
}
CHAVE = ["turno", "sg_uf", "cd_municipio_tse"]


def _sufixo(dimensao: str, ano: int) -> str:
    colunas = DIMENSOES[dimensao][0]
    return colunas.get(ano, colunas[max(colunas)])  # ano novo: assume o leiaute mais recente


def ler(zip_path: Path, ano: int, tamanho_bloco: int = 2_000_000) -> tuple[pd.DataFrame, dict]:
    """Marginais por turno × município × (dimensão, código), exterior incluso.

    Devolve (marginais, verificações). `marginais` tem a dimensão "total" (código 0) e uma linha
    por categoria presente; `verificações` traz o que só se vê linha a linha no arquivo bruto.
    """
    cfg = carregar_sources()["tse"]["perfil_comparecimento_abstencao"]
    cods = {d: f"CD_{_sufixo(d, ano)}" for d in DIMENSOES}
    descs = {d: f"DS_{_sufixo(d, ano)}" for d in DIMENSOES}
    tipos = {"ANO_ELEICAO": "int16", "NR_TURNO": "int8", "SG_UF": "category",
             "CD_MUNICIPIO": "int32", "DT_GERACAO": "category",
             **dict.fromkeys(cods.values(), "int16"), **dict.fromkeys(descs.values(), "category"),
             **dict.fromkeys(QT, "int64")}  # fmt: skip
    partes = {d: [] for d in ["total", *DIMENSOES]}
    pares = {d: set() for d in DIMENSOES}
    v = {"linhas": 0, "aptos_diferente_da_soma": 0, "contagem_negativa": 0,
         "anos": set(), "dt_geracao": set()}  # fmt: skip
    nome = cfg["arquivo_csv"].format(ano=ano)
    with zipfile.ZipFile(zip_path) as z, z.open(nome) as f:
        blocos = pd.read_csv(f, sep=cfg["separador"], encoding=cfg["encoding"], usecols=list(tipos),
                             dtype=tipos, chunksize=tamanho_bloco)  # fmt: skip
        for b in blocos:
            b = b.rename(columns={"NR_TURNO": "turno", "SG_UF": "sg_uf",
                                  "CD_MUNICIPIO": "cd_municipio_tse", **QT})  # fmt: skip
            v["linhas"] += len(b)
            v["aptos_diferente_da_soma"] += int((b.aptos != b.comparecimento + b.abstencoes).sum())
            v["contagem_negativa"] += int((b[CONTAGENS] < 0).any(axis=1).sum())
            v["anos"].update(b.ANO_ELEICAO.unique().tolist())
            v["dt_geracao"].update(b.DT_GERACAO.unique().tolist())
            partes["total"].append(
                b.groupby(CHAVE, observed=True)[CONTAGENS].sum().assign(cd_categoria=0)
            )
            for d in DIMENSOES:
                unicos = b[[cods[d], descs[d]]].drop_duplicates().values.tolist()
                pares[d].update(map(tuple, unicos))
                g = b.groupby([*CHAVE, cods[d]], observed=True)[CONTAGENS].sum()
                partes[d].append(g.rename_axis([*CHAVE, "cd_categoria"]))
    marginais = []
    for d, lista in partes.items():
        g = pd.concat(lista).reset_index()
        # categórica: o groupby criaria pares UF × município inexistentes
        g["sg_uf"] = g["sg_uf"].astype(str)
        g = g.groupby([*CHAVE, "cd_categoria"], as_index=False)[CONTAGENS].sum()
        marginais.append(g.assign(dimensao=d))
    v["pares_codigo_descricao"] = {d: sorted(p) for d, p in pares.items()}
    v["anos"], v["dt_geracao"] = sorted(v["anos"]), sorted(v["dt_geracao"])
    df = pd.concat(marginais, ignore_index=True).assign(ano=ano)
    df["dt_geracao"] = pd.to_datetime(v["dt_geracao"][-1], format="%d/%m/%Y")
    return df, v


def validar_arquivo(ano: int, v: dict, turnos_pedidos: list[int], turnos: set) -> list[str]:
    """Problemas encontrados na leitura linha a linha."""
    erros = []
    if v["anos"] != [ano]:
        erros.append(f"{ano}: ANO_ELEICAO no arquivo = {v['anos']}")
    if len(v["dt_geracao"]) != 1:
        erros.append(f"{ano}: mais de uma data de geração no arquivo: {v['dt_geracao']}")
    for chave in ("aptos_diferente_da_soma", "contagem_negativa"):
        if v[chave]:
            erros.append(f"{ano}: {v[chave]} linhas com {chave.replace('_', ' ')}")
    for t in sorted(set(turnos_pedidos) - turnos):
        erros.append(f"{ano}: turno {t} está em sources.yaml mas não no perfil do TSE")
    for d, pares in v["pares_codigo_descricao"].items():
        oficiais = DIMENSOES[d][1]
        for cd, ds in pares:
            if cd not in oficiais:
                erros.append(f"{ano} {d}: código {cd} ({ds!r}) fora das categorias oficiais")
            elif oficiais[cd][0].casefold() != str(ds).casefold():
                erros.append(f"{ano} {d}: código {cd} descrito como {ds!r}, "
                             f"esperado {oficiais[cd][0]!r}")
    return erros


def montar_mart(marginais: pd.DataFrame, dim: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Camada analítica: uma linha por ano × turno × município × dimensão × categoria.

    Sem o exterior (fora do seletor de municípios, como no resto do app). Devolve (mart, erros).
    """
    erros = []
    base = marginais[marginais["sg_uf"] != "ZZ"]
    m = base.merge(dim[["cd_municipio_tse", "cd_municipio_ibge", "nm_municipio"]],
                   on="cd_municipio_tse", how="left")  # fmt: skip
    sem = m[m["cd_municipio_ibge"].isna()]["cd_municipio_tse"].unique()
    if len(sem):
        erros.append(f"{len(sem)} municípios do perfil sem código IBGE: {sorted(sem)[:10]}")
    m = m.dropna(subset=["cd_municipio_ibge"])

    categorias = {("total", 0): ("Todos os eleitores", True, 0)}
    for d, (_, cats) in DIMENSOES.items():
        informados = [cd for cd, (_, informado) in cats.items() if informado]
        for cd, (rotulo, informado) in cats.items():
            # ordem oficial do TSE; "Não informado"/"Inválido" ficam por último
            categorias[(d, cd)] = (rotulo, informado, informados.index(cd) + 1 if informado else 99)
    info = pd.DataFrame(
        [(d, cd, *valores) for (d, cd), valores in categorias.items()],
        columns=["dimensao", "cd_categoria", "categoria", "informado", "ordem"],
    )
    m = m.merge(info, on=["dimensao", "cd_categoria"], how="left")
    m["voto_facultativo"] = [cd in FACULTATIVO.get(d, ()) for d, cd in
                             zip(m["dimensao"], m["cd_categoria"], strict=True)]
    m["abstencao_pct"] = (100 * m["abstencoes"] / m["aptos"]).where(m["aptos"] > 0)
    colunas = ["ano", "turno", "sg_uf", "cd_municipio_tse", "cd_municipio_ibge", "nm_municipio",
               "dimensao", "cd_categoria", "categoria", "ordem", "informado", "voto_facultativo",
               *CONTAGENS, "abstencao_pct", "dt_geracao"]  # fmt: skip
    tipos = {"ano": "int16", "turno": "int8", "cd_municipio_tse": "int32",
             "cd_municipio_ibge": "int32", "cd_categoria": "int16", "ordem": "int8"}
    m = m[colunas].astype(tipos)
    chave = ["ano", "turno", "cd_municipio_ibge", "dimensao", "cd_categoria"]
    return m.sort_values(chave).reset_index(drop=True), erros


def validar_mart(mart: pd.DataFrame, municipios_esperados: dict) -> list[str]:
    """Regras de qualidade da camada analítica (também conferidas pelos testes sobre o Parquet)."""
    erros = []
    chave = ["ano", "turno", "cd_municipio_ibge", "dimensao", "cd_categoria"]
    if mart.duplicated(chave).any():
        erros.append(f"chave duplicada em {mart.duplicated(chave).sum()} linhas")
    if mart["categoria"].isna().any():
        erros.append("categoria sem rótulo")
    if (mart["aptos"] != mart["comparecimento"] + mart["abstencoes"]).any():
        erros.append("aptos != comparecimento + abstenções")
    # sem dupla contagem: cada dimensão soma exatamente o total do município
    mun = ["ano", "turno", "cd_municipio_ibge"]
    total = mart[mart["dimensao"] == "total"].set_index(mun)[CONTAGENS]
    for d in DIMENSOES:
        soma = mart[mart["dimensao"] == d].groupby(mun)[CONTAGENS].sum()
        soma = soma.reindex(total.index, fill_value=0)
        n = int((soma != total).any(axis=1).sum())
        if n:
            erros.append(f"{d}: soma das categorias != total em {n} municípios")
    for (ano, turno), g in mart.groupby(["ano", "turno"]):
        esperado = municipios_esperados.get(int(ano))
        if esperado and g["cd_municipio_ibge"].nunique() != esperado:
            n = g["cd_municipio_ibge"].nunique()
            erros.append(f"{ano} T{turno}: {n} municípios, esperado {esperado}")
    return erros


def conferir_totais(marginais: pd.DataFrame, oficiais: dict) -> tuple[list[dict], list[str]]:
    """Brasil com exterior × painel de comparecimento/abstenção do TSE (que usa este dataset)."""
    linhas, erros = [], []
    tot = marginais[marginais["dimensao"] == "total"].groupby(["ano", "turno"])[CONTAGENS].sum()
    for (ano, turno), esperado in oficiais.items():
        if (ano, turno) not in tot.index:
            continue
        for k, valor in esperado.items():
            calculado = int(tot.loc[(ano, turno), k])
            linhas.append({"ano": ano, "turno": turno, "indicador": k, "pipeline": calculado,
                           "tse": valor, "diferenca": calculado - valor})
            if calculado != valor:
                erros.append(f"Brasil {ano} T{turno} {k}: {calculado:,} != {valor:,} "
                             "(painel do TSE)")
    return linhas, erros


def comparar_com_resultados(mart: pd.DataFrame, municipio: pd.DataFrame) -> list[dict]:
    """Diferença, por município, entre a abstenção do perfil e a do detalhe_votacao_munzona
    (base do resto do app). Informativo: as duas bases não coincidem por município."""
    total = mart[mart["dimensao"] == "total"]
    j = total.merge(municipio, on=["ano", "turno", "cd_municipio_ibge"], suffixes=("", "_res"))
    saida = []
    for (ano, turno), g in j.groupby(["ano", "turno"]):
        dif = (g["abstencao_pct"] - 100 * g["abstencoes_res"] / g["aptos_res"]).abs()
        saida.append({
            "ano": int(ano), "turno": int(turno), "municipios": len(g),
            "aptos_perfil": int(g["aptos"].sum()), "aptos_resultados": int(g["aptos_res"].sum()),
            "municipios_com_aptos_diferentes": int((g["aptos"] != g["aptos_res"]).sum()),
            "dif_taxa_pp_mediana": round(float(dif.median()), 3),
            "dif_taxa_pp_p99": round(float(dif.quantile(0.99)), 3),
            "dif_taxa_pp_max": round(float(dif.max()), 3),
        })
    return saida
