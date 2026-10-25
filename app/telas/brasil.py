"""Brasil em perspectiva: município × estado × Brasil."""

import math

import streamlit as st
from lib import charts, data, fmt, narrativa, ui

INDICADORES = ["comparecimento", "abstencoes", "validos", "brancos_nulos"]
ESCALA_FIXA = {"comparecimento": 100, "validos": 100}


def escala(indicador: str, valores) -> float:
    """100 para taxas altas; senão o múltiplo de 5 acima de 1,5 × o maior valor."""
    if indicador in ESCALA_FIXA:
        return ESCALA_FIXA[indicador]
    return max(5, math.ceil(1.5 * max(valores) / 5) * 5)


def render():
    ui.cabecalho("brasil")
    ui.abertura("brasil")
    mun = ui.municipio_ou_parar()
    cd = int(mun["cd_municipio_ibge"])
    sigla = mun["sg_uf"]
    nome_uf = data.NOME_UF.get(sigla, sigla)
    anima = ui.anima("brasil")

    with st.container(key="filtros"):
        ano, turno = st.selectbox(
            "Eleição",
            data.ELEICOES,
            format_func=lambda e: f"{e[0]} · {e[1]}º turno",
            key="brasil_eleicao",
        )

    carregando = ui.esqueleto(3)
    try:
        ind = data.indicadores(cd, ano, turno)
        uf = data.uf(sigla, ano, turno)
        br = data.brasil(ano, turno)
        antes = {
            "Município": data.indicadores(cd, 2022, 1),
            "Estado": data.uf(sigla, 2022, 1),
            "Brasil": data.brasil(2022, 1),
        }
        agora = {
            "Município": data.indicadores(cd, 2026, 1),
            "Estado": data.uf(sigla, 2026, 1),
            "Brasil": data.brasil(2026, 1),
        }
        comparativo = data.comparativo(cd, "anos", 2022, 1)
    except Exception as exc:  # noqa: BLE001
        carregando.empty()
        ui.erro_leitura(exc)
        ui.rodape()
        st.stop()
    carregando.empty()

    if ind is None or uf is None or br is None:
        ui.mostrar(ui.contexto_livre(f"{mun['rotulo']} · Eleição presidencial {ano} · {turno}º turno"))
        ui.aguardando(
            f"O {turno}º turno de {ano} ainda está sendo apurado",
            f"Assim que a totalização oficial for liberada, os números de {mun['nm_municipio']} "
            "aparecem aqui. Enquanto isso, veja o 1º turno ou o 2º turno de 2022.",
        )
        ui.rodape()
        st.stop()

    ui.mostrar(ui.linha_contexto(mun["nm_municipio"], sigla, ano, turno, ind["aptos"]))
    ui.mostrar(
        '<section class="escopos">'
        + ui.cartao_escopo("Município", mun["nm_municipio"], ind["aptos"], "mun", anima, 0)
        + ui.cartao_escopo("Estado", nome_uf, uf["aptos"], "uf", anima, 1)
        + ui.cartao_escopo("País", "Brasil", br["aptos"], "br", anima, 2)
        + "</section>"
    )

    series = [(mun["nm_municipio"], ind, "mun"), (nome_uf, uf, "uf"), ("Brasil", br, "br")]
    blocos = "".join(
        ui.bloco_indicador(
            data.INDICADORES[i][0],
            [(rot, linha[f"{i}_pct"], serie) for rot, linha, serie in series],
            escala(i, [linha[f"{i}_pct"] for _, linha, _ in series]),
            ind[f"{i}_delta_uf_pp"],
            ind[f"{i}_delta_brasil_pp"],
        )
        for i in INDICADORES
    )
    legenda = "".join(
        f'<span><i class="quadrado serie-{serie}-bg"></i>{rot}</span>' for rot, _, serie in series
    )
    esquerda, direita = st.columns([3, 2], gap="large")
    with esquerda:
        ui.mostrar(
            f"""<section class="cartao{anima}" style="--i:3"><div class="cab"><div>
            <h2>Indicador a indicador</h2><span class="sub-cartao">{ano} · {turno}º turno</span></div>
            <div class="legenda-linha">{legenda}</div></div>{blocos}</section>"""
        )
    with direita:
        with st.container(key="tendencia"):
            ui.mostrar(
                """<div class="sub-cartao-wrap"><h2 style="margin:0;font-size:22px">Tendência do
                comparecimento</h2><span class="sub-cartao">1º turno, 2022 → 2026</span></div>"""
            )
            if all(v is not None for v in (*antes.values(), *agora.values())):
                serie = {
                    nome: (antes[nome]["comparecimento_pct"], agora[nome]["comparecimento_pct"])
                    for nome in agora
                }
                curtos = {"Município": mun["nm_municipio"], "Estado": sigla, "Brasil": "Brasil"}
                st.plotly_chart(charts.inclinacao(serie, curtos), config=charts.SEM_BARRA)
                with st.expander("Ver como tabela"):
                    linhas = [
                        [(curtos[n], "", True), (fmt.pct(a), "num", False),
                         (fmt.pct(b), "num", False), (fmt.pp(b - a), "num", False)]
                        for n, (a, b) in serie.items()
                    ]
                    ui.mostrar(ui.tabela_html(
                        [("Série", ""), ("2022", "num"), ("2026", "num"), ("Variação", "num")],
                        linhas,
                    ))
            else:
                ui.nota("Sem dados de 2022 para este município, então não há tendência a mostrar.")

        delta_base = None
        if (ano, turno) == (2026, 1) and comparativo is not None and (
            comparativo["status_comparacao"] == "disponivel"
        ):
            delta_base = comparativo["comparecimento_delta_pp"]
        ui.mostrar(ui.cartao_leitura(
            narrativa.leitura_rapida(
                ind["comparecimento_delta_uf_pp"],
                ind["comparecimento_delta_brasil_pp"],
                delta_base,
                ind["brancos_nulos_pct"],
                ind["brancos_nulos_delta_brasil_pp"],
                comp_delta_br_2022=(
                    antes["Município"]["comparecimento_delta_brasil_pp"]
                    if delta_base is not None and antes["Município"] is not None
                    else None
                ),
                nome=mun["nm_municipio"],
            ),
            anima=anima, i=4,
        ))
    ui.rodape()
