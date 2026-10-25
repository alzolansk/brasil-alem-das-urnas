"""Gráficos Plotly com o tema do protótipo. Série fixa: município azul · estado verde · Brasil cinza."""

import plotly.graph_objects as go

from . import data, fmt

AZUL, VERDE, CINZA, LARANJA, NAVY = "#1550A8", "#1B7A3A", "#6B7280", "#C8401A", "#0B1F45"
COR_SERIE = {"Município": AZUL, "Estado": VERDE, "Brasil": CINZA}
PRINCIPAIS = ["comparecimento", "abstencoes", "brancos", "nulos"]
FONTE = dict(family="Inter, sans-serif", color=NAVY)


def _base(fig, altura):
    fig.update_layout(
        height=altura,
        margin=dict(l=0, r=10, t=10, b=0),
        font=FONTE,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", y=-0.15),
    )
    return fig


def barras_agrupadas(valores: dict):
    """valores: {serie: {indicador: pct}}."""
    fig = go.Figure()
    rotulos = [data.INDICADORES[i][0] for i in PRINCIPAIS]
    for serie, dados in valores.items():
        y = [dados[i] for i in PRINCIPAIS]
        fig.add_bar(
            name=serie,
            y=rotulos,
            x=y,
            orientation="h",
            marker_color=COR_SERIE[serie],
            text=[fmt.pct(v) for v in y],
            textposition="outside",
            cliponaxis=False,
            hovertemplate="%{y}: %{text}<extra>" + serie + "</extra>",
        )
    fig.update_layout(barmode="group", yaxis=dict(autorange="reversed"), xaxis=dict(visible=False))
    return _base(fig, 420)


def inclinacao(series: dict):
    """series: {serie: (valor_2022, valor_2026)}."""
    fig = go.Figure()
    for nome, (a, b) in series.items():
        fig.add_scatter(
            x=["2022", "2026"],
            y=[a, b],
            mode="lines+markers+text",
            name=nome,
            line=dict(color=COR_SERIE[nome], width=3),
            marker=dict(size=10),
            text=[fmt.pct(a), fmt.pct(b)],
            textposition=["middle left", "middle right"],
            hovertemplate="%{x}: %{text}<extra>" + nome + "</extra>",
        )
    fig.update_layout(
        yaxis=dict(title="Comparecimento (%)", gridcolor="#E3E7EE"), xaxis=dict(fixedrange=True)
    )
    return _base(fig, 360)


# Grade de UFs (linha, coluna), aproximando a posição geográfica.
GRADE_UF = {
    "RR": (0, 3), "AP": (0, 5),
    "AM": (1, 2), "PA": (1, 4), "MA": (1, 5), "CE": (1, 6), "RN": (1, 7),
    "AC": (2, 1), "RO": (2, 2), "TO": (2, 4), "PI": (2, 5), "PE": (2, 6), "PB": (2, 7),
    "MT": (3, 3), "GO": (3, 4), "BA": (3, 5), "SE": (3, 6), "AL": (3, 7),
    "MS": (4, 3), "DF": (4, 4), "MG": (4, 5), "ES": (4, 6),
    "SP": (5, 4), "RJ": (5, 5), "PR": (6, 4), "SC": (7, 4), "RS": (8, 4),
}


def grade_ufs(valores: dict, titulo: str, selecionada: str | None):
    """Grade de quadrados por estado, colorida pelo indicador. valores: {sigla: valor}."""
    siglas = [s for s in GRADE_UF if s in valores]
    fig = go.Figure(
        go.Scatter(
            x=[GRADE_UF[s][1] for s in siglas],
            y=[GRADE_UF[s][0] for s in siglas],
            mode="markers+text",
            text=siglas,
            customdata=siglas,
            marker=dict(
                symbol="square",
                size=44,
                color=[valores[s] for s in siglas],
                colorscale=[[0, "#8FB2E6"], [1, "#0B2F6B"]],
                showscale=True,
                colorbar=dict(title=titulo, thickness=12, len=0.8),
                line=dict(
                    width=[4 if s == selecionada else 0 for s in siglas], color="#F2C200"
                ),
            ),
            textfont=dict(color="white", size=12, family="Inter"),
            hovertext=[f"{s}: {fmt.pct(valores[s])}" for s in siglas],
            hoverinfo="text",
            selected=dict(marker=dict(opacity=1)),
            unselected=dict(marker=dict(opacity=1)),
        )
    )
    fig.update_layout(
        xaxis=dict(visible=False, range=[0.3, 7.7], fixedrange=True),
        yaxis=dict(visible=False, autorange="reversed", fixedrange=True, scaleanchor="x"),
        dragmode="select",
        clickmode="event+select",
    )
    return _base(fig, 520)


def coropletico(sigla: str, df, coluna: str, titulo: str):
    """Mapa dos municípios da UF. df precisa de cd_municipio_ibge, nm_municipio e `coluna`."""
    fig = go.Figure(
        go.Choropleth(
            geojson=data.malha(sigla),
            featureidkey="properties.cd_municipio_ibge",
            locations=df["cd_municipio_ibge"],
            z=df[coluna],
            zmin=df[coluna].min(),
            zmax=df[coluna].max(),
            colorscale=[[0, "#8FB2E6"], [1, "#0B2F6B"]],
            colorbar=dict(title=titulo, thickness=12),
            text=df["nm_municipio"] + ": " + df[coluna].map(fmt.pct),
            hoverinfo="text",
            marker_line_width=0.3,
            marker_line_color="white",
        )
    )
    fig.update_geos(fitbounds="locations", visible=False)
    return _base(fig, 520)
