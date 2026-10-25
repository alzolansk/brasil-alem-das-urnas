"""Textos automáticos por regras e modelos de frase fixos (sem IA).

O limite de "praticamente igual" é o da metodologia (menos de 0,5 p.p.). O texto descreve a
direção, sem julgar se é bom ou ruim.
"""

from . import fmt

LIMITE_IGUAL_PP = 0.5

# referência -> (depois de "acima/abaixo", depois de "igual")
REFERENCIAS = {
    "uf": ("da média do estado", "à média do estado"),
    "br": ("da média do Brasil", "à média do Brasil"),
}


def classificar(delta_pp, limite: float = LIMITE_IGUAL_PP) -> str:
    """'alta', 'queda' ou 'igual' (também quando não há valor)."""
    if delta_pp is None or delta_pp != delta_pp or abs(delta_pp) < limite:
        return "igual"
    return "alta" if delta_pp > 0 else "queda"


def _modulo(delta_pp) -> str:
    return fmt.pp(abs(delta_pp)).lstrip("+")


def comparar(sujeito: str, delta_pp, referencia: str) -> str:
    """Compara com 'uf' ou 'br'. Ex.: 'O comparecimento está 2,1 p.p. abaixo da média do estado'."""
    depois_de, igual_a = REFERENCIAS[referencia]
    classe = classificar(delta_pp)
    if classe == "igual":
        return f"{sujeito} está praticamente igual {igual_a}"
    posicao = "acima" if classe == "alta" else "abaixo"
    return f"{sujeito} está {_modulo(delta_pp)} {posicao} {depois_de}"


def evolucao(sujeito: str, delta_pp, base: str = "2022") -> str:
    """Ex.: 'O comparecimento subiu 0,9 p.p. desde 2022'."""
    classe = classificar(delta_pp)
    if classe == "igual":
        return f"{sujeito} ficou praticamente igual ao de {base}"
    verbo = "subiu" if classe == "alta" else "caiu"
    return f"{sujeito} {verbo} {_modulo(delta_pp)} desde {base}"


def frase_resumo(nome, uf, ano, turno, aptos, comparecimento_pct, abstencoes_pct) -> str:
    return (
        f"Em {nome} ({uf}), no {turno}º turno de {ano}, {fmt.pct(comparecimento_pct)} dos "
        f"{fmt.inteiro(aptos)} eleitores aptos compareceram e {fmt.pct(abstencoes_pct)} "
        "não compareceram."
    )


def leitura_rapida(comp_delta_uf, comp_delta_br, comp_delta_base, bn_pct, bn_delta_br) -> list:
    """Três itens: × estado, × 2022 (ou × Brasil, se não houver 2022) e brancos+nulos."""
    segundo = (
        evolucao("O comparecimento", comp_delta_base)
        if comp_delta_base is not None and comp_delta_base == comp_delta_base
        else comparar("O comparecimento", comp_delta_br, "br")
    )
    return [
        comparar("O comparecimento", comp_delta_uf, "uf") + ".",
        segundo + ".",
        f"Brancos e nulos somam {fmt.pct(bn_pct)} dos votos; "
        + comparar("esse valor", bn_delta_br, "br")
        + ".",
    ]


def em_quatro_anos(delta_pp) -> str:
    classe = classificar(delta_pp)
    if classe == "igual":
        return "Em quatro anos, o comparecimento ficou praticamente igual."
    verbo = "subiu" if classe == "alta" else "caiu"
    return f"Em quatro anos, o comparecimento {verbo} {_modulo(delta_pp)}"


def posicao_uf(posicao, total: int = 27) -> str:
    if posicao is None or posicao != posicao:
        return "—"
    return f"{int(posicao)}º entre {total} UFs"
