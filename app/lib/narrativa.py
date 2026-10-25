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


def _ponto(texto: str) -> str:
    """Fecha a frase sem duplicar o ponto de 'p.p.'."""
    return texto if texto.endswith(".") else texto + "."


def _tem(valor) -> bool:
    return valor is not None and valor == valor


def leitura_rapida(
    comp_delta_uf, comp_delta_br, comp_delta_base, bn_pct, bn_delta_br,
    comp_delta_br_2022=None, nome=None,
) -> list:
    """Três itens: × estado, × 2022 (ou × Brasil, se não houver 2022) e brancos+nulos.

    Com `comp_delta_br_2022` e `nome`, se o município mudou de lado em relação à média do
    Brasil entre 2022 e 2026, o item de 2022 conta essa virada.
    """
    antes, agora = classificar(comp_delta_br_2022), classificar(comp_delta_br)
    if nome and _tem(comp_delta_br_2022) and {antes, agora} == {"alta", "queda"}:
        segundo = (
            f"Em 2022, {nome} votava {'mais' if antes == 'alta' else 'menos'} que a média "
            f"do país. Em 2026, {'passou à frente' if agora == 'alta' else 'ficou para trás'}"
        )
    elif _tem(comp_delta_base):
        segundo = evolucao("O comparecimento", comp_delta_base)
    else:
        segundo = comparar("O comparecimento", comp_delta_br, "br")
    return [
        comparar("O comparecimento", comp_delta_uf, "uf") + ".",
        segundo + ".",
        f"Brancos e nulos somam {fmt.pct(bn_pct)} dos votos; "
        + comparar("esse valor", bn_delta_br, "br")
        + ".",
    ]


def manchete_explore(nome, comp_pct, comp_delta_br, abst_delta_uf) -> dict:
    """Ex.: 'Campinas foi menos às urnas do que o Brasil: [8 em cada 10 eleitores votaram],
    e a abstenção ficou acima da média do estado.'"""
    antes = {
        "alta": f"{nome} foi mais às urnas do que o Brasil:",
        "queda": f"{nome} foi menos às urnas do que o Brasil:",
        "igual": f"{nome} votou na mesma proporção que o Brasil:",
    }[classificar(comp_delta_br)]
    depois = {
        "queda": ", e a abstenção ficou abaixo da média do estado.",
        "alta": ", e a abstenção ficou acima da média do estado.",
        "igual": ", e a abstenção ficou na média do estado.",
    }[classificar(abst_delta_uf)]
    return {
        "antes": antes,
        "destaque": f"{round(comp_pct / 10)} em cada 10 eleitores votaram",
        "depois": depois,
    }


def _comparecimento_mudou(delta_pp) -> str:
    classe = classificar(delta_pp)
    if classe == "igual":
        return "ficou praticamente igual"
    return f"{'subiu' if classe == 'alta' else 'caiu'} {_modulo(delta_pp)}"


def _brancos_nulos_mudaram(delta_pp, alta="subiram", queda="caíram") -> str:
    classe = classificar(delta_pp)
    if classe == "igual":
        return "ficaram praticamente iguais"
    return f"{alta if classe == 'alta' else queda} {_modulo(delta_pp)}"


def manchete_comparativo(nome, aptos_base, aptos_comp, comp_delta, bn_delta) -> dict:
    """Ex.: 'Campinas perdeu 7,8 mil eleitores e [ficou menos participativa]: ...'."""
    dif = int(aptos_comp) - int(aptos_base)
    if dif == 0:
        antes = f"{nome} manteve o número de eleitores e"
    else:
        verbo = "ganhou" if dif > 0 else "perdeu"
        antes = f"{nome} {verbo} {fmt.milhar_curto(abs(dif))} eleitores e"
    destaque = {
        "alta": "ficou mais participativa",
        "queda": "ficou menos participativa",
        "igual": "manteve o nível de participação",
    }[classificar(comp_delta)]
    depois = (
        f": o comparecimento {_comparecimento_mudou(comp_delta)} e brancos e nulos "
        f"{_brancos_nulos_mudaram(bn_delta)}"
    )
    return {"antes": antes, "destaque": destaque, "depois": _ponto(depois)}


def entre_turnos(ano, comp_delta, bn_delta) -> str:
    """Síntese do 1º para o 2º turno de uma eleição."""
    return _ponto(
        f"Em {ano}, o comparecimento {_comparecimento_mudou(comp_delta)} do 1º para o 2º turno, "
        f"e brancos e nulos {_brancos_nulos_mudaram(bn_delta, 'aumentaram', 'recuaram')}"
    )


# grupo -> (plural, singular, zero), na ordem de data.contagens_100
GRUPOS_100 = [
    ("votaram em um candidato", "votou em um candidato", "nenhum votou em um candidato"),
    ("votaram em branco", "votou em branco", "nenhum votou em branco"),
    ("votaram nulo", "votou nulo", "nenhum votou nulo"),
    ("não compareceram", "não compareceu", "todos compareceram"),
]


def resumo_100(nome, ano, turno, pontos) -> str:
    """Frase lida pelo leitor de tela no lugar da grade de 100 pontos."""
    inicio = f"Exibindo {ano}, {turno}º turno."
    if pontos is None:
        return f"{inicio} Não há dados desta eleição para {nome}."
    partes = [
        zero if n == 0 else f"1 {singular}" if n == 1 else f"{n} {plural}"
        for n, (plural, singular, zero) in zip(pontos, GRUPOS_100, strict=True)
    ]
    return (f"{inicio} De cada 100 eleitores aptos de {nome}, "
            f"{', '.join(partes[:-1])} e {partes[-1]}.")


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
