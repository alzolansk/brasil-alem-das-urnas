"""Leitura das marts em Parquet (o app nunca consulta o BigQuery)."""

import json
import math
from pathlib import Path

import pandas as pd
import streamlit as st
from unidecode import unidecode

RAIZ = Path(__file__).resolve().parents[2]
MARTS = RAIZ / "data" / "marts"
GEO = RAIZ / "data" / "geo"

IBGE_PADRAO = 3550308  # São Paulo

INDICADORES = {
    "comparecimento": ("Comparecimento", "Parte dos eleitores aptos que foi votar."),
    "abstencoes": ("Abstenção", "Parte dos eleitores aptos que não compareceu."),
    "validos": ("Votos válidos", "Votos em candidatos, em % de quem compareceu."),
    "brancos": ("Votos brancos", "Quem foi votar mas não escolheu ninguém, em % de quem compareceu."),
    "nulos": ("Votos nulos", "Votos anulados, em % de quem compareceu."),
    "brancos_nulos": ("Brancos + nulos", "Soma de brancos e nulos, em % de quem compareceu."),
}

ELEICOES = [(2026, 1), (2026, 2), (2022, 1), (2022, 2)]

NOME_UF = {
    "AC": "Acre", "AL": "Alagoas", "AM": "Amazonas", "AP": "Amapá", "BA": "Bahia",
    "CE": "Ceará", "DF": "Distrito Federal", "ES": "Espírito Santo", "GO": "Goiás",
    "MA": "Maranhão", "MG": "Minas Gerais", "MS": "Mato Grosso do Sul", "MT": "Mato Grosso",
    "PA": "Pará", "PB": "Paraíba", "PE": "Pernambuco", "PI": "Piauí", "PR": "Paraná",
    "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte", "RO": "Rondônia", "RR": "Roraima",
    "RS": "Rio Grande do Sul", "SC": "Santa Catarina", "SE": "Sergipe", "SP": "São Paulo",
    "TO": "Tocantins",
}


def normalizar(texto: str) -> str:
    return unidecode(str(texto)).casefold().strip()


def carregar(nome: str) -> pd.DataFrame:
    caminho = (MARTS / f"{nome}.parquet").resolve()
    stat = caminho.stat()
    return _carregar(str(caminho), stat.st_mtime_ns, stat.st_size)


@st.cache_data(show_spinner=False)
def _carregar(caminho: str, modificado_ns: int, tamanho: int) -> pd.DataFrame:
    """A revisão do arquivo faz parte da chave, inclusive com cache já aquecido."""
    return pd.read_parquet(caminho)


def municipios() -> pd.DataFrame:
    """Um registro por município (sem exterior), com chave de busca sem acento."""
    df = carregar("mart_municipio_indicadores")
    df = df[~df["exterior"].astype(bool)]
    df = df.sort_values(["ano", "turno"]).drop_duplicates("cd_municipio_ibge", keep="last")
    df = df[["cd_municipio_ibge", "nm_municipio", "sg_uf", "regiao"]].copy()
    df["chave"] = df["nm_municipio"].map(normalizar)
    df["rotulo"] = df["nm_municipio"] + " (" + df["sg_uf"] + ")"
    return df.sort_values("nm_municipio").reset_index(drop=True)


def buscar(texto: str, limite: int = 30) -> pd.DataFrame:
    """Busca sem acento e sem diferenciar maiúsculas: começa-com, depois contém e, por fim,
    os municípios do estado cujo nome ou sigla foi digitado."""
    base = municipios()
    chave = normalizar(texto)
    if not chave:
        return base.head(0)
    comeca = base[base["chave"].str.startswith(chave)]
    contem = base[base["chave"].str.contains(chave, regex=False) & ~base.index.isin(comeca.index)]
    siglas = [s for s, nome in NOME_UF.items() if chave in (s.casefold(), normalizar(nome))]
    do_estado = base[base["sg_uf"].isin(siglas) & ~base.index.isin(comeca.index.union(contem.index))]
    return pd.concat([comeca, contem, do_estado]).head(limite)


def parecidos(texto: str, n: int = 5) -> list:
    import difflib

    base = municipios()
    achados = difflib.get_close_matches(normalizar(texto), base["chave"].tolist(), n=n, cutoff=0.6)
    return base[base["chave"].isin(achados)]["rotulo"].tolist()


def municipio(cd_ibge: int) -> pd.Series | None:
    base = municipios()
    linha = base[base["cd_municipio_ibge"] == cd_ibge]
    return None if linha.empty else linha.iloc[0]


def indicadores(cd_ibge: int, ano: int, turno: int) -> pd.Series | None:
    df = carregar("mart_municipio_benchmark")
    linha = df[(df["cd_municipio_ibge"] == cd_ibge) & (df["ano"] == ano) & (df["turno"] == turno)]
    return None if linha.empty else linha.iloc[0]


def comparativo(cd_ibge: int, tipo: str, ano_base: int, turno_base: int) -> pd.Series | None:
    df = carregar("mart_municipio_comparativo")
    linha = df[
        (df["cd_municipio_ibge"] == cd_ibge)
        & (df["tipo_comparacao"] == tipo)
        & (df["ano_base"] == ano_base)
        & (df["turno_base"] == turno_base)
    ]
    return None if linha.empty else linha.iloc[0]


def zonas(cd_ibge: int, ano: int, turno: int) -> pd.DataFrame:
    df = carregar("mart_zona_indicadores")
    return df[
        (df["cd_municipio_ibge"] == cd_ibge) & (df["ano"] == ano) & (df["turno"] == turno)
    ].sort_values("nr_zona")


def uf_brasil(ano: int, turno: int) -> pd.DataFrame:
    df = carregar("mart_uf_brasil_indicadores")
    return df[(df["ano"] == ano) & (df["turno"] == turno)]


def brasil(ano: int, turno: int) -> pd.Series | None:
    df = uf_brasil(ano, turno)
    df = df[df["nivel"] == "BRASIL"]
    return None if df.empty else df.iloc[0]


def uf(sigla: str, ano: int, turno: int) -> pd.Series | None:
    df = uf_brasil(ano, turno)
    df = df[(df["nivel"] == "UF") & (df["localidade"] == sigla)]
    return None if df.empty else df.iloc[0]


def tem_dados(ano: int, turno: int) -> bool:
    return not uf_brasil(ano, turno).empty


def municipios_da_uf(sigla: str, ano: int, turno: int) -> pd.DataFrame:
    df = carregar("mart_municipio_indicadores")
    return df[
        (df["sg_uf"] == sigla) & (df["ano"] == ano) & (df["turno"] == turno) & ~df["exterior"].astype(bool)
    ]


def perfil(cd_ibge: int, ano: int, turno: int) -> pd.DataFrame:
    """Abstenção por gênero, faixa etária e escolaridade (mart_perfil_abstencao); vazio se não houver."""
    df = carregar("mart_perfil_abstencao")
    return df[(df["cd_municipio_ibge"] == cd_ibge) & (df["ano"] == ano) & (df["turno"] == turno)]


def tem_perfil(ano: int, turno: int) -> bool:
    df = carregar("mart_perfil_abstencao")
    return bool(((df["ano"] == ano) & (df["turno"] == turno)).any())


@st.cache_data(show_spinner=False)
def malha(sigla: str) -> dict | None:
    caminho = GEO / f"malha_{sigla}.geojson"
    return json.loads(caminho.read_text(encoding="utf-8")) if caminho.exists() else None


def ultima_atualizacao() -> str:
    df = carregar("mart_uf_brasil_indicadores")
    return pd.to_datetime(df["dt_geracao"]).max().strftime("%d/%m/%Y")


def pontos_100(contagens: list[int], total: int) -> list[int]:
    """Distribui 100 pontos pelos grupos pelo método dos maiores restos (empate: menor índice)."""
    if not total:
        return [0] * len(contagens)
    bruto = [c / total * 100 for c in contagens]
    pontos = [math.floor(b) for b in bruto]
    ordem = sorted(range(len(bruto)), key=lambda i: (-(bruto[i] - pontos[i]), i))
    for i in ordem[: 100 - sum(pontos)]:
        pontos[i] += 1
    return pontos


def contagens_100(ind) -> list[int]:
    """Válidos, brancos, nulos e quem não compareceu (aptos − comparecimento): somam os aptos."""
    return [int(ind["validos"]), int(ind["brancos"]), int(ind["nulos"]),
            int(ind["aptos"]) - int(ind["comparecimento"])]
