"""Mapa eleitoral: grade de UFs e mapa dos municípios de uma UF."""

import streamlit as st
from lib import charts, data, fmt, ui

REGIOES = ["Todas", "Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]
NIVEIS = ["Estados", "Municípios"]
VISOES = ["Mapa", "Lista ordenada"]
SEM_BARRA = {"displayModeBar": False}


def _ver_municipios():
    st.session_state["mapa_nivel"] = "Municípios"


def _painel_estado(sigla, linha, brasil, indicador, nome):
    coluna = f"{indicador}_pct"
    valor, media = linha[coluna], brasil[coluna]
    posicao = linha[f"{indicador}_posicao_uf"]
    ui.mostrar(
        f"""<div class="cartao"><h3>Estado selecionado: {sigla}</h3>
        <div class="info">{nome} · região {linha['regiao']}</div>
        <div class="destaque">{fmt.pct(valor)}</div>
        <div class="chips">{ui.chip('uf', 'vs. média nacional', valor - media)}</div>
        <p class="frase">Média nacional: {fmt.pct(media)}.<br>
        Posição: {int(posicao)}º entre as 27 UFs (1º = maior valor).</p></div>"""
    )
    st.button(f"Ver municípios de {sigla}", on_click=_ver_municipios, width="stretch")


def render():
    ui.cabecalho("mapa")
    mun = ui.municipio_ou_parar()

    with st.expander("Filtros", expanded=True):
        c1, c2, c3 = st.columns(3)
        indicador = c1.selectbox(
            "Indicador",
            list(data.INDICADORES),
            format_func=lambda i: data.INDICADORES[i][0],
            key="mapa_indicador",
        )
        ano, turno = c2.selectbox(
            "Eleição",
            data.ELEICOES,
            format_func=lambda e: f"{e[1]}º turno de {e[0]}",
            key="mapa_eleicao",
        )
        regiao = c3.selectbox("Região", REGIOES, key="mapa_regiao")
        c4, c5 = st.columns(2)
        nivel = c4.radio("Nível", NIVEIS, horizontal=True, key="mapa_nivel")
        visao = c5.radio("Visualização", VISOES, horizontal=True, key="mapa_visao")
        st.caption(data.INDICADORES[indicador][1])

    nome = data.INDICADORES[indicador][0]
    coluna = f"{indicador}_pct"
    carregando = ui.esqueleto(3)
    try:
        ufs = data.uf_brasil(ano, turno)
    except Exception as exc:  # noqa: BLE001
        carregando.empty()
        ui.erro_leitura(exc)
        ui.rodape()
        st.stop()
    carregando.empty()

    st.markdown(f"## {nome} por {'estado' if nivel == 'Estados' else 'município'}, "
                f"{turno}º turno de {ano}")
    if ufs.empty:
        ui.aguardando(f"O {turno}º turno de {ano} ainda não foi publicado pelo TSE.")
        ui.rodape()
        st.stop()

    brasil = ufs[ufs["nivel"] == "BRASIL"].iloc[0]
    estados = ufs[ufs["nivel"] == "UF"]
    if regiao != "Todas":
        estados = estados[estados["regiao"] == regiao]
    por_sigla = estados.set_index("localidade")

    siglas = sorted(por_sigla.index)
    if st.session_state.get("mapa_uf") not in siglas:
        padrao = mun["sg_uf"] if mun["sg_uf"] in siglas else siglas[0]
        st.session_state["mapa_uf"] = padrao

    esquerda, direita = st.columns([3, 2])
    with esquerda:
        if nivel == "Estados" and visao == "Mapa":
            valores = {s: por_sigla.loc[s, coluna] for s in siglas}
            fig = charts.grade_ufs(valores, nome, st.session_state["mapa_uf"])
            evento = st.plotly_chart(
                fig, on_select="rerun", selection_mode="points", key="mapa_grade",
                config=SEM_BARRA,
            )
            pontos = evento.selection.points if evento and evento.selection else []
            clicado = (
                [s for s in charts.GRADE_UF if s in valores][pontos[0]["point_index"]]
                if pontos
                else None
            )
            if clicado and clicado != st.session_state.get("mapa_ultimo_clique"):
                st.session_state["mapa_ultimo_clique"] = clicado
                st.session_state["mapa_uf"] = clicado
                st.rerun()
            st.caption("Clique num quadrado para ver o estado, ou use a lista ao lado.")
        elif nivel == "Estados":
            tabela = estados.sort_values(coluna, ascending=False)[
                ["localidade", "regiao", "aptos", coluna]
            ].reset_index(drop=True)
            tabela.insert(0, "Posição", tabela.index + 1)
            tabela["aptos"] = tabela["aptos"].map(fmt.inteiro)
            tabela[coluna] = tabela[coluna].map(fmt.pct)
            tabela.columns = ["Posição", "UF", "Região", "Eleitores aptos", nome]
            st.dataframe(tabela, hide_index=True, width="stretch")
        else:
            sigla = st.session_state["mapa_uf"]
            df = data.municipios_da_uf(sigla, ano, turno)
            if df.empty:
                ui.aguardando("Sem municípios apurados para esta UF neste turno.")
            elif visao == "Mapa":
                fig = charts.coropletico(sigla, df, coluna, nome)
                st.plotly_chart(fig, width="stretch", config=SEM_BARRA)
                geo = data.malha(sigla)
                ids = {f["properties"]["cd_municipio_ibge"] for f in geo["features"]}
                faltam = df[~df["cd_municipio_ibge"].isin(ids)]["nm_municipio"].tolist()
                if faltam:
                    ui.nota(
                        f"Sem polígono na malha do IBGE: {', '.join(faltam)}. "
                        "Aparece só na Lista ordenada."
                    )
            else:
                tabela = df.sort_values(coluna, ascending=False)[
                    ["nm_municipio", "aptos", coluna]
                ].reset_index(drop=True)
                tabela.insert(0, "Posição", tabela.index + 1)
                tabela["aptos"] = tabela["aptos"].map(fmt.inteiro)
                tabela[coluna] = tabela[coluna].map(fmt.pct)
                tabela.columns = ["Posição", "Município", "Eleitores aptos", nome]
                st.dataframe(tabela, hide_index=True, width="stretch")

    with direita:
        sigla = st.selectbox("Estado", siglas, key="mapa_uf")
        _painel_estado(sigla, por_sigla.loc[sigla], brasil, indicador, nome)

    if nivel == "Estados" and visao == "Mapa":
        with st.expander("Ver os mesmos dados em lista"):
            tabela = estados.sort_values(coluna, ascending=False)[["localidade", coluna]]
            tabela[coluna] = tabela[coluna].map(fmt.pct)
            tabela.columns = ["UF", nome]
            st.dataframe(tabela, hide_index=True, width="stretch")
    ui.rodape()
