"""Grupos de eleitores da tela "Quem ficou em casa?" (funções puras sobre mart_perfil_abstencao).

Taxa de abstenção do grupo = abstenções ÷ eleitores aptos do grupo × 100 (calculada no pipeline).
Cada dimensão é lida sozinha: a mart não tem cruzamentos (idade × escolaridade etc.).
"""

import pandas as pd

DIMENSOES = {"faixa_etaria": "Faixa etária", "genero": "Gênero", "escolaridade": "Escolaridade"}
# Abaixo disto o percentual oscila muito com poucas pessoas: aparece com aviso e fica fora dos
# destaques e dos textos automáticos.
BASE_MINIMA = 50


def total(df: pd.DataFrame) -> pd.Series | None:
    linha = df[df["dimensao"] == "total"]
    return None if linha.empty else linha.iloc[0]


def grupos(df: pd.DataFrame, dimensao: str) -> pd.DataFrame:
    """Categorias informadas da dimensão, na ordem oficial, com `base_pequena`."""
    g = df[(df["dimensao"] == dimensao) & df["informado"] & (df["aptos"] > 0)]
    g = g.sort_values("ordem").reset_index(drop=True)
    return g.assign(base_pequena=g["aptos"] < BASE_MINIMA)


def nao_informados(df: pd.DataFrame, dimensao: str) -> int:
    """Eleitores sem a característica no cadastro ("Não informado"/"Inválido"): ficam no total."""
    return int(df[(df["dimensao"] == dimensao) & ~df["informado"]]["aptos"].sum())


def extremos(g: pd.DataFrame) -> tuple[pd.Series | None, pd.Series | None]:
    """(maior, menor) taxa entre os grupos com base suficiente. Empate: o primeiro na ordem oficial."""
    ok = g[~g["base_pequena"]]
    if ok.empty:
        return None, None
    maior = ok.sort_values(["abstencao_pct", "ordem"], ascending=[False, True]).iloc[0]
    menor = ok.sort_values(["abstencao_pct", "ordem"], ascending=[True, True]).iloc[0]
    return maior, menor


def destaques(g: pd.DataFrame, limite: float = 0.5) -> tuple[int | None, int | None]:
    """Códigos da maior e da menor taxa para marcar no gráfico. Sem marca quando a distância
    entre elas fica abaixo de `limite` p.p. (o "praticamente igual" dos textos automáticos)."""
    maior, menor = extremos(g)
    if maior is None or maior["abstencao_pct"] - menor["abstencao_pct"] < limite:
        return None, None
    return int(maior["cd_categoria"]), int(menor["cd_categoria"])


def comparacao(base: pd.DataFrame, atual: pd.DataFrame) -> pd.DataFrame:
    """Mesmos grupos em duas eleições (total + categorias informadas), com a variação em p.p.

    `comparavel` = os dois lados têm pelo menos BASE_MINIMA eleitores aptos. As categorias do TSE
    são as mesmas em 2022 e 2026 (conferido no pipeline); grupo ausente em um ano fica de fora.
    """
    colunas = ["dimensao", "cd_categoria", "categoria", "ordem", "voto_facultativo"]
    a = base[base["informado"]][[*colunas, "aptos", "abstencao_pct"]]
    b = atual[atual["informado"]][["dimensao", "cd_categoria", "aptos", "abstencao_pct"]]
    j = a.merge(b, on=["dimensao", "cd_categoria"], suffixes=("_base", "_comp"))
    j["delta_pp"] = j["abstencao_pct_comp"] - j["abstencao_pct_base"]
    j["comparavel"] = (j["aptos_base"] >= BASE_MINIMA) & (j["aptos_comp"] >= BASE_MINIMA)
    j["_total"] = j["dimensao"] != "total"  # o total vem antes dos grupos
    return j.sort_values(["_total", "dimensao", "ordem"]).drop(columns="_total").reset_index(drop=True)


def maiores_variacoes(c: pd.DataFrame) -> tuple[pd.Series | None, pd.Series | None]:
    """(maior alta, maior queda) entre os grupos comparáveis das três dimensões."""
    ok = c[c["comparavel"] & (c["dimensao"] != "total")].copy()
    if ok.empty:
        return None, None
    ok["_dim"] = ok["dimensao"].map(list(DIMENSOES).index)
    alta = ok.sort_values(["delta_pp", "_dim", "ordem"], ascending=[False, True, True]).iloc[0]
    queda = ok.sort_values(["delta_pp", "_dim", "ordem"], ascending=[True, True, True]).iloc[0]
    return alta, queda
