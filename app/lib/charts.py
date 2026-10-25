"""Gráficos Plotly com o tema do protótipo. Série fixa: município azul · estado verde · Brasil cinza."""

import copy
from functools import lru_cache

import plotly.graph_objects as go

from . import data, fmt

AZUL, VERDE, CINZA, LARANJA, NAVY = "#0B4EA2", "#12753E", "#6B7280", "#C2410C", "#071D41"
CINZA_TEXTO = "#4A4F57"  # #6B7280 fica abaixo de 4,5:1 em 13px
COR_SERIE = {"Município": AZUL, "Estado": VERDE, "Brasil": CINZA}
COR_TEXTO_SERIE = {"Município": AZUL, "Estado": VERDE, "Brasil": CINZA_TEXTO}
FAIXAS = ["#DCE7F5", "#A9C4E8", "#6F9BD6", "#2F6BBE", "#0B3F86"]
FONTE = dict(family="Inter, sans-serif", color=NAVY)
SEM_BARRA = {"displayModeBar": False}


def _base(fig, altura, margem=None):
    fig.update_layout(
        height=altura,
        margin=margem or dict(l=0, r=0, t=0, b=0),
        font=FONTE,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )
    return fig


def _area(anel) -> float:
    """Área com sinal (fórmula do laço): positiva = sentido anti-horário em lon/lat."""
    return sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(anel, anel[1:] + anel[:1], strict=True)) / 2


def _orientar(poligono: list) -> list:
    """Convenção do d3-geo (usado pelo Plotly): contorno externo horário, furos anti-horários.
    Com o sentido invertido, o Plotly pinta o "lado de fora" e o mapa vira um retângulo."""
    return [
        anel[::-1] if (_area(anel) > 0) == (i == 0) else anel for i, anel in enumerate(poligono)
    ]


@lru_cache(maxsize=32)
def malha_orientada(sigla: str) -> dict | None:
    geo = data.malha(sigla)
    if geo is None:
        return None
    geo = copy.deepcopy(geo)
    for feat in geo["features"]:
        g = feat["geometry"]
        if g["type"] == "Polygon":
            g["coordinates"] = _orientar(g["coordinates"])
        elif g["type"] == "MultiPolygon":
            g["coordinates"] = [_orientar(p) for p in g["coordinates"]]
    return geo


def faixas(valores) -> tuple[list, callable]:
    """5 intervalos iguais entre o mínimo e o máximo. Devolve (limites inferiores, faixa(v))."""
    valores = [float(v) for v in valores]
    minimo, maximo = min(valores), max(valores)
    passo = (maximo - minimo) / 5 or 1
    limites = [minimo + passo * i for i in range(5)]

    def faixa(v) -> int:
        return min(4, max(0, int((float(v) - minimo) // passo)))

    return limites, faixa


def inclinacao(series: dict, curtos: dict):
    """series: {serie: (valor_2022, valor_2026)}; curtos: {serie: nome curto do rótulo}.

    Eixo X numérico (0 = 2022, 1 = 2026) com rótulos fixos: o tipo "category" do Plotly
    juntava os dois anos num ponto só, e o linear puro mostrava "2.022,5".
    """
    fig = go.Figure()
    for nome, (a, b) in series.items():
        fig.add_scatter(
            x=[0, 1],
            y=[a, b],
            mode="lines+markers",
            name=nome,
            line=dict(color=COR_SERIE[nome], width=3, dash="dash" if nome == "Brasil" else None),
            marker=dict(size=10, color=COR_SERIE[nome]),
            hovertemplate="%{customdata}<extra>" + curtos[nome] + "</extra>",
            customdata=[f"2022: {fmt.pct(a)}", f"2026: {fmt.pct(b)}"],
        )
    valores = [v for par in series.values() for v in par]
    folga = max((max(valores) - min(valores)) * 0.15, 0.3)
    for indice in (0, 1):
        anteriores = []
        for nome in sorted(series, key=lambda n: -series[n][indice]):
            valor = series[nome][indice]
            deslocamento = 0
            for outro in anteriores:  # evita sobreposição de rótulos próximos (< 0,25 p.p.)
                if abs(outro - valor) < 0.25:
                    deslocamento -= 16
            anteriores.append(valor)
            texto = fmt.pct(valor) if indice == 0 else f"{fmt.pct(valor)} {curtos[nome]}"
            fig.add_annotation(
                x=indice, y=valor, text=texto, showarrow=False,
                xanchor="right" if indice == 0 else "left", xshift=-12 if indice == 0 else 12,
                yshift=deslocamento,
                font=dict(size=13, color=COR_TEXTO_SERIE[nome], family="Inter, sans-serif"),
            )
    fig.update_layout(
        xaxis=dict(
            tickmode="array", tickvals=[0, 1], ticktext=["2022", "2026"], range=[-0.55, 1.85],
            showgrid=False, showline=False, zeroline=False, fixedrange=True,
            tickfont=dict(size=13, color=CINZA_TEXTO),
        ),
        yaxis=dict(visible=False, fixedrange=True, range=[min(valores) - folga, max(valores) + folga]),
    )
    return _base(fig, 300, dict(l=0, r=0, t=10, b=30))


def _centro(geometria) -> tuple[float, float]:
    """Centroide (lon, lat) do maior anel do polígono, para posicionar a sigla."""
    aneis = (
        [geometria["coordinates"][0]]
        if geometria["type"] == "Polygon"
        else [poligono[0] for poligono in geometria["coordinates"]]
    )

    def area_centro(anel):
        a = cx = cy = 0.0
        for (x0, y0), (x1, y1) in zip(anel, anel[1:] + anel[:1], strict=True):
            cruz = x0 * y1 - x1 * y0
            a += cruz
            cx += (x0 + x1) * cruz
            cy += (y0 + y1) * cruz
        return abs(a / 2), (cx / (3 * a), cy / (3 * a)) if a else anel[0]

    return max((area_centro(anel) for anel in aneis), key=lambda t: t[0])[1]


# Ajuste fino da posição da sigla nas UFs pequenas do litoral (lon, lat somados ao centro).
AJUSTE_SIGLA = {"DF": (0, 0.6), "SE": (0.9, 0), "AL": (1.1, 0.2), "PB": (1.6, 0), "RN": (1.2, 0.3),
                "PE": (0.6, -0.4), "ES": (0.9, 0), "RJ": (0.8, -0.5)}  # fmt: skip


def mapa_ufs(valores: dict, selecionada: str | None, realce: set):
    """Mapa dos 27 estados com o contorno real (malha do IBGE).

    Fora de `realce` (região filtrada) os estados ficam a 25%. As 5 faixas de cor são
    calculadas sobre os 27 estados, então não mudam com o filtro de região.
    """
    geo = malha_orientada("UF")
    siglas = [f["properties"]["sg_uf"] for f in geo["features"]]
    _, faixa = faixas([valores[s] for s in siglas])
    escala = []
    for i, cor in enumerate(FAIXAS):
        escala += [[i / 5, cor], [(i + 1) / 5, cor]]
    fig = go.Figure(
        go.Choropleth(
            geojson=geo,
            featureidkey="properties.sg_uf",
            locations=siglas,
            z=[faixa(valores[s]) + 0.5 for s in siglas],
            zmin=0,
            zmax=5,
            colorscale=escala,
            showscale=False,
            customdata=siglas,
            marker=dict(
                opacity=[1 if s in realce else 0.25 for s in siglas],
                line=dict(color="#FFFFFF", width=1),
            ),
            text=[f"{data.NOME_UF[s]}: {fmt.pct(valores[s])}" for s in siglas],
            hoverinfo="text",
        )
    )
    if selecionada:
        fig.add_trace(
            go.Choropleth(
                geojson=geo, featureidkey="properties.sg_uf", locations=[selecionada], z=[0],
                colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]], showscale=False,
                marker=dict(line=dict(color="#F5C400", width=3.5)), hoverinfo="skip",
            )
        )
    centros = {f["properties"]["sg_uf"]: _centro(f["geometry"]) for f in geo["features"]}
    fig.add_trace(
        go.Scattergeo(
            lon=[centros[s][0] + AJUSTE_SIGLA.get(s, (0, 0))[0] for s in siglas],
            lat=[centros[s][1] + AJUSTE_SIGLA.get(s, (0, 0))[1] for s in siglas],
            mode="text",
            text=[f"<b>{s}</b>" for s in siglas],
            customdata=siglas,
            textfont=dict(
                size=11,
                family="Inter, sans-serif",
                color=[
                    ("rgba(7,29,65," if faixa(valores[s]) < 3 else "rgba(255,255,255,")
                    + ("1)" if s in realce else "0.35)")
                    for s in siglas
                ],
            ),
            hoverinfo="skip",
        )
    )
    fig.update_geos(
        fitbounds="locations", visible=False, bgcolor="rgba(0,0,0,0)",
        projection_type="mercator",
    )
    fig.update_layout(dragmode=False, clickmode="event+select")
    return _base(fig, 520)


def coropletico(sigla: str, df, coluna: str):
    """Mapa dos municípios da UF, nas mesmas 5 faixas (calculadas sobre os municípios da UF)."""
    limites, _ = faixas(df[coluna])
    minimo, maximo = float(df[coluna].min()), float(df[coluna].max())
    escala = []
    for i, cor in enumerate(FAIXAS):
        escala += [[i / 5, cor], [(i + 1) / 5, cor]]
    fig = go.Figure(
        go.Choropleth(
            geojson=malha_orientada(sigla),
            featureidkey="properties.cd_municipio_ibge",
            locations=df["cd_municipio_ibge"],
            z=df[coluna],
            zmin=minimo,
            zmax=maximo if maximo > minimo else minimo + 1,
            colorscale=escala,
            showscale=False,
            text=df["nm_municipio"] + ": " + df[coluna].map(fmt.pct),
            hoverinfo="text",
            marker_line_width=0.3,
            marker_line_color="white",
        )
    )
    fig.update_geos(fitbounds="locations", visible=False, bgcolor="rgba(0,0,0,0)")
    return _base(fig, 520), limites
