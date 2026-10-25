"""Formatação no padrão brasileiro: 79,4% · 863.412 · +0,9 p.p. · 34,8 milhões."""

MENOS = "−"


def _decimal(valor: float, casas: int) -> str:
    return f"{valor:,.{casas}f}".replace(",", "_").replace(".", ",").replace("_", ".")


def inteiro(valor) -> str:
    return "—" if valor is None or valor != valor else _decimal(round(float(valor)), 0)


def pct(valor, casas: int = 1) -> str:
    return "—" if valor is None or valor != valor else f"{_decimal(float(valor), casas)}%"


def pp(valor, casas: int = 1) -> str:
    """Variação em pontos percentuais, sempre com sinal."""
    if valor is None or valor != valor:
        return "—"
    arredondado = round(float(valor), casas)
    if arredondado == 0:
        return f"0,{'0' * casas} p.p." if casas else "0 p.p."
    sinal = "+" if arredondado > 0 else MENOS
    return f"{sinal}{_decimal(abs(arredondado), casas)} p.p."


def variacao_pct(valor, casas: int = 1) -> str:
    """Variação relativa (%), sempre com sinal."""
    if valor is None or valor != valor:
        return "—"
    arredondado = round(float(valor), casas)
    if arredondado == 0:
        return f"0,{'0' * casas}%"
    sinal = "+" if arredondado > 0 else MENOS
    return f"{sinal}{_decimal(abs(arredondado), casas)}%"


def seta(valor, limite: float = 0.0) -> str:
    if valor is None or valor != valor or abs(valor) <= limite:
        return "■"
    return "▲" if valor > 0 else "▼"


def milhoes(valor) -> str:
    if valor is None or valor != valor:
        return "—"
    if abs(valor) >= 1_000_000:
        return f"{_decimal(valor / 1_000_000, 1)} milhões"
    return inteiro(valor)


def mil(valor) -> str:
    """'873 mil' entre mil e um milhão; acima, milhoes(); abaixo, inteiro()."""
    if valor is None or valor != valor:
        return "—"
    if abs(valor) >= 1_000_000:
        return milhoes(valor)
    if abs(valor) >= 1_000:
        return f"{round(valor / 1000)} mil"
    return inteiro(valor)


def milhar_curto(valor, casas: int = 1) -> str:
    """'7,8 mil', '31,6 mil'; abaixo de mil, inteiro()."""
    if valor is None or valor != valor:
        return "—"
    if abs(valor) >= 1_000_000:
        return milhoes(valor)
    if abs(valor) >= 1_000:
        return f"{_decimal(valor / 1000, casas)} mil"
    return inteiro(valor)


def pp_sem_mais(valor, casas: int = 1) -> str:
    """Como pp(), sem o '+' (a seta ao lado já indica o aumento)."""
    return pp(valor, casas).lstrip("+")
