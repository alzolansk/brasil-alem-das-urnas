"""Gráficos Plotly com o tema do protótipo. Série fixa: município azul · estado verde · Brasil cinza."""

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
    """series: {serie: (valor_2022, valor_2026)}; curtos: {serie: nome curto do rótulo}."""
    fig = go.Figure()
    for nome, (a, b) in series.items():
        fig.add_scatter(
            x=["2022", "2026"],
            y=[a, b],
            mode="lines+markers",
            name=nome,
            line=dict(color=COR_SERIE[nome], width=3, dash="dash" if nome == "Brasil" else None),
            marker=dict(size=10, color=COR_SERIE[nome]),
            hovertemplate="%{x}: %{customdata}<extra>" + curtos[nome] + "</extra>",
            customdata=[fmt.pct(a), fmt.pct(b)],
        )
    for indice, lado in ((0, "2022"), (1, "2026")):
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
                x=lado, y=valor, text=texto, showarrow=False,
                xanchor="right" if indice == 0 else "left", xshift=-12 if indice == 0 else 12,
                yshift=deslocamento,
                font=dict(size=13, color=COR_TEXTO_SERIE[nome], family="Inter, sans-serif"),
            )
    fig.update_layout(
        xaxis=dict(
            type="category", categoryorder="array", categoryarray=["2022", "2026"],
            showgrid=False, showline=False, zeroline=False, fixedrange=True,
            tickfont=dict(size=13, color=CINZA_TEXTO),
        ),
        yaxis=dict(visible=False, fixedrange=True),
    )
    return _base(fig, 300, dict(l=60, r=130, t=10, b=30))


# Grade de UFs (linha, coluna), com base zero, aproximando a posição geográfica.
GRADE_UF = {
    "RR": (0, 1), "AP": (0, 3),
    "AM": (1, 1), "PA": (1, 2), "MA": (1, 3), "CE": (1, 4), "RN": (1, 5),
    "AC": (2, 0), "RO": (2, 1), "MT": (2, 2), "TO": (2, 3), "PI": (2, 4), "PE": (2, 5), "PB": (2, 6),
    "MS": (3, 2), "GO": (3, 3), "DF": (3, 4), "BA": (3, 5), "AL": (3, 6),
    "SP": (4, 3), "MG": (4, 4), "ES": (4, 5), "SE": (4, 6),
    "PR": (5, 3), "RJ": (5, 4),
    "SC": (6, 3),
    "RS": (7, 3),
}
MEIO_LADO = 0.44  # quadrado de 0,88 unidade: sobra o espaço entre vizinhos


def grade_ufs(valores: dict, selecionada: str | None, realce: set):
    """Grade com os 27 estados, sempre. Fora de `realce` (região filtrada) ficam a 25%.

    As cores usam 5 faixas fixas calculadas sobre os 27 estados, então não mudam com o filtro.
    Os quadrados são formas em coordenadas do gráfico, para encolher junto com a tela.
    """
    siglas = list(GRADE_UF)
    _, faixa = faixas([valores[s] for s in siglas])
    fig = go.Figure()
    for s in siglas:
        linha, coluna = GRADE_UF[s]
        fig.add_shape(
            type="rect",
            x0=coluna - MEIO_LADO, x1=coluna + MEIO_LADO,
            y0=linha - MEIO_LADO, y1=linha + MEIO_LADO,
            fillcolor=FAIXAS[faixa(valores[s])],
            opacity=1 if s in realce else 0.25,
            line=dict(width=4 if s == selecionada else 0, color="#F5C400"),
            layer="below",
        )
    fig.add_trace(
        go.Scatter(
            x=[GRADE_UF[s][1] for s in siglas],
            y=[GRADE_UF[s][0] for s in siglas],
            mode="markers+text",
            customdata=siglas,
            text=[f"<b>{s}</b><br><span style='font-size:11px'>{fmt.pct(valores[s])}</span>" for s in siglas],
            textfont=dict(
                size=13,
                color=[
                    ("rgba(7,29,65," if faixa(valores[s]) < 3 else "rgba(255,255,255,")
                    + ("1)" if s in realce else "0.35)")
                    for s in siglas
                ],
            ),
            marker=dict(
                symbol="square", size=40, color="rgba(0,0,0,0)",
                opacity=[1 if s in realce else 0.25 for s in siglas],
            ),
            hovertext=[f"{data.NOME_UF[s]}: {fmt.pct(valores[s])}" for s in siglas],
            hoverinfo="text",
        )
    )
    fig.update_layout(
        xaxis=dict(visible=False, range=[-0.6, 6.6], fixedrange=True),
        yaxis=dict(visible=False, range=[7.6, -0.6], fixedrange=True, scaleanchor="x"),
        dragmode=False,
        clickmode="event+select",
    )
    return _base(fig, 560)


def coropletico(sigla: str, df, coluna: str):
    """Mapa dos municípios da UF, nas mesmas 5 faixas (calculadas sobre os municípios da UF)."""
    limites, _ = faixas(df[coluna])
    minimo, maximo = float(df[coluna].min()), float(df[coluna].max())
    escala = []
    for i, cor in enumerate(FAIXAS):
        escala += [[i / 5, cor], [(i + 1) / 5, cor]]
    fig = go.Figure(
        go.Choropleth(
            geojson=data.malha(sigla),
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
