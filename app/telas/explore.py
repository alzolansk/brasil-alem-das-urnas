"""Explore seu município."""

import streamlit as st
from lib import data, fmt, narrativa, ui


def tabela_zonas(zonas):
    """Tabela exibida na tela; o CSV baixa exatamente estas linhas e colunas."""
    saida = zonas[["nr_zona"]].rename(columns={"nr_zona": "Zona"}).astype(str)
    saida["Eleitores aptos"] = zonas["aptos"].map(fmt.inteiro)
    for coluna, titulo in [
        ("comparecimento_pct", "Comparecimento"),
        ("abstencoes_pct", "Abstenção"),
        ("validos_pct", "Válidos"),
        ("brancos_pct", "Brancos"),
        ("nulos_pct", "Nulos"),
    ]:
        saida[titulo] = zonas[coluna].map(fmt.pct)
    return saida.reset_index(drop=True)


def render():
    ui.cabecalho("explore")
    mun = ui.municipio_ou_parar()
    cd = int(mun["cd_municipio_ibge"])

    with st.expander("Filtros", expanded=False):
        ano, turno = st.radio(
            "Eleição",
            data.ELEICOES,
            format_func=lambda e: f"{e[1]}º turno de {e[0]}",
            horizontal=True,
            key="explore_eleicao",
        )

    carregando = ui.esqueleto(3)
    try:
        ind = data.indicadores(cd, ano, turno)
        base = data.comparativo(cd, "anos", 2022, 1) if (ano, turno) == (2026, 1) else None
        zonas = data.zonas(cd, ano, turno)
    except Exception as exc:  # noqa: BLE001 - qualquer falha de leitura vira mensagem amigável
        carregando.empty()
        ui.erro_leitura(exc)
        ui.rodape()
        st.stop()
    carregando.empty()

    st.markdown(f"## {mun['nm_municipio']} ({mun['sg_uf']})")
    if ind is None:
        ui.aguardando(f"O {turno}º turno de {ano} ainda não foi publicado pelo TSE.")
        ui.rodape()
        st.stop()

    ui.mostrar(
        f'<p class="resumo">{narrativa.frase_resumo(mun["nm_municipio"], mun["sg_uf"], ano, turno, ind["aptos"], ind["comparecimento_pct"], ind["abstencoes_pct"])}</p>'
    )

    delta_2022 = {}
    if base is not None and base["status_comparacao"] == "disponivel":
        delta_2022 = {"comparecimento": base["comparecimento_delta_pp"],
                      "abstencoes": base["abstencoes_delta_pp"]}

    def chips(indicador):
        itens = [
            ui.chip("uf", "Estado", ind[f"{indicador}_delta_uf_pp"]),
            ui.chip("br", "Brasil", ind[f"{indicador}_delta_brasil_pp"]),
        ]
        if indicador in delta_2022:
            itens.append(ui.chip("mun", "vs. 2022", delta_2022[indicador]))
        return itens

    cartoes = ui.cartao_indicador(
        "Comparecimento",
        data.INDICADORES["comparecimento"][1],
        fmt.pct(ind["comparecimento_pct"]),
        f"{fmt.inteiro(ind['comparecimento'])} de {fmt.inteiro(ind['aptos'])} eleitores aptos.",
        chips("comparecimento"),
    ) + ui.cartao_indicador(
        "Abstenção",
        data.INDICADORES["abstencoes"][1],
        fmt.pct(ind["abstencoes_pct"]),
        f"{fmt.inteiro(ind['abstencoes'])} eleitores não compareceram.",
        chips("abstencoes"),
    )
    ui.mostrar(f'<div class="grade">{cartoes}</div>')
    st.caption("“p.p.” = ponto percentual, a diferença simples entre duas porcentagens.")

    leitura = narrativa.leitura_rapida(
        ind["comparecimento_delta_uf_pp"],
        ind["comparecimento_delta_brasil_pp"],
        delta_2022.get("comparecimento"),
        ind["brancos_nulos_pct"],
        ind["brancos_nulos_delta_brasil_pp"],
    )
    ui.mostrar(ui.cartao_leitura(leitura))

    st.markdown("### Como foram os votos")
    st.caption("Percentuais sobre quem compareceu.")
    ui.mostrar(ui.barra_empilhada(ind["validos_pct"], ind["brancos_pct"], ind["nulos_pct"]))

    st.markdown("### Zona por zona")
    if len(zonas) <= 1:
        ui.nota("O município tem uma única zona eleitoral; os números acima já são os dela.")
    else:
        tabela = tabela_zonas(zonas)
        st.dataframe(tabela, hide_index=True, width="stretch")
        st.download_button(
            "Baixar CSV",
            tabela.to_csv(index=False, sep=";").encode("utf-8-sig"),
            file_name=f"zonas_{cd}_{ano}_t{turno}.csv",
            mime="text/csv",
        )
    ui.rodape()
