"""Brasil em perspectiva: município × estado × Brasil."""

import streamlit as st
from lib import charts, data, fmt, narrativa, ui

ANO, TURNO = 2026, 1
SEM_BARRA = {"displayModeBar": False}


def _cartao(titulo, serie, aptos, nome):
    return ui.html(
        f"""<div class="cartao"><h3><span class="chip"><span class="pt serie-{serie}"></span>
        {titulo}</span></h3><div class="destaque alt">{fmt.milhoes(aptos)}</div>
        <div class="frase">eleitores aptos em {nome}</div></div>"""
    )


def render():
    ui.cabecalho("brasil")
    mun = ui.municipio_ou_parar()
    cd = int(mun["cd_municipio_ibge"])
    sigla = mun["sg_uf"]
    st.markdown(f"## {mun['nm_municipio']} em perspectiva")
    st.caption("1º turno de 2026. Cores fixas: município azul, estado verde, Brasil cinza.")

    carregando = ui.esqueleto(3)
    try:
        ind = data.indicadores(cd, ANO, TURNO)
        uf = data.uf(sigla, ANO, TURNO)
        br = data.brasil(ANO, TURNO)
        antes = {
            "Município": data.indicadores(cd, 2022, 1),
            "Estado": data.uf(sigla, 2022, 1),
            "Brasil": data.brasil(2022, 1),
        }
        comparativo = data.comparativo(cd, "anos", 2022, 1)
    except Exception as exc:  # noqa: BLE001
        carregando.empty()
        ui.erro_leitura(exc)
        ui.rodape()
        st.stop()
    carregando.empty()
    if ind is None or uf is None or br is None:
        ui.aguardando("Os dados deste recorte ainda não estão disponíveis.")
        ui.rodape()
        st.stop()

    ui.mostrar(
        '<div class="grade">'
        + _cartao("Município", "mun", ind["aptos"], mun["nm_municipio"])
        + _cartao("Estado", "uf", uf["aptos"], sigla)
        + _cartao("Brasil", "br", br["aptos"], "todo o país")
        + "</div>"
    )

    atual = {"Município": ind, "Estado": uf, "Brasil": br}
    valores = {
        nome: {i: linha[f"{i}_pct"] for i in charts.PRINCIPAIS} for nome, linha in atual.items()
    }
    st.markdown("### Os quatro indicadores lado a lado")
    st.plotly_chart(charts.barras_agrupadas(valores), width="stretch", config=SEM_BARRA)
    with st.expander("Ver como tabela, com as diferenças"):
        linhas = "".join(
            f"""<tr><td>{data.INDICADORES[i][0]}</td>
            <td class="num">{fmt.pct(valores['Município'][i])}</td>
            <td class="num">{fmt.pct(valores['Estado'][i])}</td>
            <td class="num">{fmt.pct(valores['Brasil'][i])}</td>
            <td class="num">{fmt.pp(ind[f'{i}_delta_uf_pp'])}</td>
            <td class="num">{fmt.pp(ind[f'{i}_delta_brasil_pp'])}</td></tr>"""
            for i in charts.PRINCIPAIS
        )
        ui.mostrar(
            f"""<div class="tabela-rolagem"><table class="tab"><thead><tr><th>Indicador</th>
            <th>Município</th><th>Estado</th><th>Brasil</th><th>Mun. − estado</th>
            <th>Mun. − Brasil</th></tr></thead><tbody>{linhas}</tbody></table></div>"""
        )

    st.markdown("### Comparecimento: 2022 → 2026")
    if all(v is not None for v in antes.values()):
        serie = {
            nome: (antes[nome]["comparecimento_pct"], atual[nome]["comparecimento_pct"])
            for nome in atual
        }
        st.plotly_chart(charts.inclinacao(serie), width="stretch", config=SEM_BARRA)
        with st.expander("Ver como tabela"):
            linhas = "".join(
                f"""<tr><td>{n}</td><td class="num">{fmt.pct(a)}</td>
                <td class="num">{fmt.pct(b)}</td><td class="num">{fmt.pp(b - a)}</td></tr>"""
                for n, (a, b) in serie.items()
            )
            ui.mostrar(
                f"""<div class="tabela-rolagem"><table class="tab"><thead><tr><th>Série</th>
                <th>2022</th><th>2026</th><th>Variação</th></tr></thead>
                <tbody>{linhas}</tbody></table></div>"""
            )
    else:
        ui.nota("Sem dados de 2022 para este município, então não há tendência a mostrar.")

    delta_base = None
    if comparativo is not None and comparativo["status_comparacao"] == "disponivel":
        delta_base = comparativo["comparecimento_delta_pp"]
    ui.mostrar(
        ui.cartao_leitura(
            narrativa.leitura_rapida(
                ind["comparecimento_delta_uf_pp"],
                ind["comparecimento_delta_brasil_pp"],
                delta_base,
                ind["brancos_nulos_pct"],
                ind["brancos_nulos_delta_brasil_pp"],
            )
        )
    )
    ui.rodape()
