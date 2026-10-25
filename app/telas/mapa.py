"""Mapa eleitoral: mapa dos estados, lista ordenada e mapa dos municípios de uma UF."""

from html import escape

import streamlit as st
from lib import charts, data, fmt, loader, ui

REGIOES = ["Todas", "Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]
NIVEIS = ["Estados", "Municípios"]
VISOES = ["Mapa", "Lista ordenada"]
DESCRICAO = {
    ("Estados", "Mapa"): "Cada área é um estado, colorido pelo valor do indicador. "
    "Clique para ver o detalhe.",
    ("Estados", "Lista ordenada"): "Estados do maior para o menor valor. Clique em uma linha "
    "para ver o detalhe.",
    ("Municípios", "Mapa"): "Cada área é um município do estado selecionado.",
    ("Municípios", "Lista ordenada"): "Municípios do estado selecionado, do maior para o menor valor.",
}


def _ver_municipios():
    st.session_state["mapa_nivel"] = "Municípios"


def _lista(df, coluna_nome, rotulo_nome, coluna_valor, rotulo_valor, chave, extra=None):
    """Lista ordenada com barra; devolve a linha selecionada (ou None)."""
    ordenado = df.sort_values(coluna_valor, ascending=False).reset_index(drop=True)
    tabela = ordenado[[coluna_nome]].rename(columns={coluna_nome: rotulo_nome})
    tabela.insert(0, "Posição", [f"{n}º" for n in range(1, len(ordenado) + 1)])
    if extra:
        for nome, serie in extra(ordenado).items():
            tabela[nome] = serie
    tabela["barra"] = ordenado[coluna_valor].astype(float)
    tabela[rotulo_valor] = ordenado[coluna_valor].map(fmt.pct)
    evento = st.dataframe(
        tabela,
        hide_index=True,
        key=chave,
        on_select="rerun",
        selection_mode="single-row",
        column_config={
            "Posição": st.column_config.TextColumn(width=60),
            "UF": st.column_config.TextColumn(width=50),
            "barra": st.column_config.ProgressColumn(
                " ", min_value=0, max_value=float(tabela["barra"].max()), format=" ", width=110,
            ),
            rotulo_valor: st.column_config.TextColumn(width=110),
        },
    )
    linhas = evento.selection.rows if evento and evento.selection else []
    return ordenado.iloc[linhas[0]] if linhas else None


def _painel_estado(sigla, linha, brasil, coluna, nome, ano, turno):
    valor, media = linha[coluna], brasil[coluna]
    diferenca = valor - media
    classe = "up" if diferenca > 0 else "down" if diferenca < 0 else "flat"
    posicao = linha[coluna.replace("_pct", "_posicao_uf")]
    ui.mostrar(
        f"""<section class="estado-sel"><span class="rotulo">Estado selecionado</span>
        <h3>{escape(data.NOME_UF[sigla])}</h3><span class="valor">{fmt.pct(valor)}</span>
        <span class="info">{escape(nome)} no {turno}º turno de {ano}</span>
        <dl><dt>Média nacional</dt><dd>{fmt.pct(media)}</dd>
        <dt>Diferença</dt><dd class="{classe}">{fmt.seta(diferenca)} {fmt.pp(diferenca)}</dd>
        <dt>Posição entre as UFs</dt><dd>{int(posicao)}º de 27</dd>
        <dt>Região</dt><dd>{escape(linha['regiao'])}</dd></dl></section>"""
    )
    with st.container(key="ver_municipios"):
        st.button(f"Ver municípios de {sigla}", on_click=_ver_municipios, width="stretch")


def _ranking(estados, coluna, regiao, anima):
    top = estados.sort_values(coluna, ascending=False).head(5)
    maior = float(top[coluna].max()) if not top.empty else 1
    itens = "".join(
        f"""<li><span>{n}</span><div><span>{escape(data.NOME_UF[s])}</span>
        <div class="barra-h"><i style="width:{float(v) / maior * 100:.1f}%;--j:{n}"></i></div></div>
        <span class="val">{fmt.pct(v)}</span></li>"""
        for n, (s, v) in enumerate(zip(top["localidade"], top[coluna], strict=True), start=1)
    )
    titulo = "Brasil" if regiao == "Todas" else f"Região {regiao}"
    ui.mostrar(
        f"""<section class="ranking{anima}" style="--i:3"><h3>Maiores valores · {titulo}</h3>
        <ol>{itens}</ol></section>"""
    )


def render():
    ui.cabecalho("mapa")
    ui.abertura("mapa")
    mun = ui.municipio_ou_parar()
    anima = ui.anima("mapa")

    filtros, centro, painel = st.columns([1.1, 2.4, 1.5], gap="large")
    with filtros, st.container(key="mapa_filtros"):
        indicador = st.radio(
            "Indicador",
            list(data.INDICADORES),
            format_func=lambda i: data.INDICADORES[i][0],
            key="mapa_indicador",
        )
        ui.mostrar(f'<div class="desc-indicador">{escape(data.INDICADORES[indicador][1])}</div>')
        ano, turno = st.selectbox(
            "Eleição",
            data.ELEICOES,
            format_func=lambda e: f"{e[0]} · {e[1]}º turno",
            key="mapa_eleicao",
        )
        regiao = st.pills("Região", REGIOES, default="Todas", key="mapa_regiao") or "Todas"
        nivel = st.radio("Nível", NIVEIS, horizontal=True, key="mapa_nivel")

    nome = data.INDICADORES[indicador][0]
    coluna = f"{indicador}_pct"
    with centro:
        carregando = ui.carregando()
    try:
        ufs = data.uf_brasil(ano, turno)
    except Exception as exc:  # noqa: BLE001
        carregando.empty()
        with centro:
            ui.erro_leitura(exc)
        ui.rodape()
        st.stop()
    carregando.empty()

    if ufs.empty:
        with centro:
            ui.aguardando(
                f"O {turno}º turno de {ano} ainda está sendo apurado",
                "Assim que a totalização oficial for liberada, o mapa aparece aqui. Enquanto "
                "isso, veja o 1º turno ou o 2º turno de 2022.",
            )
        ui.rodape()
        st.stop()

    brasil = ufs[ufs["nivel"] == "BRASIL"].iloc[0]
    todos = ufs[ufs["nivel"] == "UF"]
    estados = todos if regiao == "Todas" else todos[todos["regiao"] == regiao]
    por_sigla = todos.set_index("localidade")
    siglas = sorted(estados["localidade"])
    if st.session_state.get("mapa_uf") not in siglas:
        st.session_state["mapa_uf"] = mun["sg_uf"] if mun["sg_uf"] in siglas else siglas[0]

    with centro, st.container(key="mapa_cartao"):
        titulo = st.empty()
        visao = st.radio(
            "Visualização", VISOES, horizontal=True, key="mapa_visao",
            label_visibility="collapsed",
        )
        sigla_atual = st.session_state["mapa_uf"]
        recorte = "estado" if nivel == "Estados" else f"município · {sigla_atual}"
        titulo.markdown(
            ui.html(
                f"""<div class="sub-cartao-wrap"><h2>{escape(nome)} por {recorte} · {turno}º turno
                de {ano}</h2><span class="desc-mapa">{DESCRICAO[(nivel, visao)]}</span></div>"""
            ),
            unsafe_allow_html=True,
        )

        if nivel == "Estados" and visao == "Mapa":
            valores = {s: float(por_sigla.loc[s, coluna]) for s in por_sigla.index}
            n = st.session_state.setdefault("mapa_cliques", 0)
            with st.container(key="mapa_grafico"):
                ui.mostrar(loader.loader_grafico("Carregando o mapa", "Desenhando os estados…"))
                fig = charts.mapa_ufs(valores, sigla_atual, set(estados["localidade"]))
                evento = st.plotly_chart(
                    fig, on_select="rerun", selection_mode="points", key=f"mapa_ufs_{n}",
                    config=charts.SEM_BARRA,
                )
            pontos = evento.selection.points if evento and evento.selection else []
            if pontos:
                clicado = pontos[0].get("customdata") or pontos[0].get("location")
                st.session_state["mapa_cliques"] = n + 1  # novo gráfico, sem seleção pendurada
                if clicado in siglas:
                    st.session_state["mapa_uf"] = clicado
                st.rerun()
            limites, _ = charts.faixas(valores.values())
            ui.mostrar(ui.legenda_mapa(nome, charts.FAIXAS, limites))
        elif nivel == "Estados":
            escolhida = _lista(
                estados, "localidade", "UF", coluna, nome, "mapa_lista",
                extra=lambda o: {"Estado": o["localidade"].map(data.NOME_UF)},
            )
            if escolhida is not None and escolhida["localidade"] != st.session_state.get(
                "mapa_lista_ultima"
            ):
                st.session_state["mapa_lista_ultima"] = escolhida["localidade"]
                st.session_state["mapa_uf"] = escolhida["localidade"]
        else:
            df = data.municipios_da_uf(sigla_atual, ano, turno)
            if df.empty:
                ui.nota("Sem municípios apurados para esta UF neste turno.")
            elif visao == "Mapa":
                with st.container(key="mapa_grafico"):
                    ui.mostrar(loader.loader_grafico(
                        f"Carregando {sigla_atual}", "Desenhando os municípios do estado…"
                    ))
                    fig, limites = charts.coropletico(sigla_atual, df, coluna)
                    st.plotly_chart(fig, config=charts.SEM_BARRA)
                ui.mostrar(ui.legenda_mapa(nome, charts.FAIXAS, limites))
                ids = {f["properties"]["cd_municipio_ibge"] for f in data.malha(sigla_atual)["features"]}
                faltam = df[~df["cd_municipio_ibge"].isin(ids)]["nm_municipio"].tolist()
                if faltam:
                    ui.nota(
                        f"Sem polígono na malha do IBGE: {', '.join(faltam)}. "
                        "Aparece só na Lista ordenada."
                    )
            else:
                _lista(df, "nm_municipio", "Município", coluna, nome, "mapa_lista_mun")

    with painel, st.container(key="mapa_painel"):
        sigla = st.selectbox(
            "Estado", siglas, key="mapa_uf",
            format_func=lambda s: f"{s} · {data.NOME_UF[s]}",
        )
        _painel_estado(sigla, por_sigla.loc[sigla], brasil, coluna, nome, ano, turno)
        _ranking(estados, coluna, regiao, anima)
    ui.rodape()
