"""Comparativo 2022 × 2026 e 1º × 2º turno."""

import streamlit as st
from lib import data, fmt, narrativa, ui

LINHAS = ["comparecimento", "abstencoes", "validos", "brancos", "nulos", "brancos_nulos"]


def tabela_evolucao(c, rotulo_base: str, rotulo_comp: str) -> str:
    """Tabela HTML com barra de diferença centrada no zero (aptos: variação em %)."""
    deltas = [c[f"{i}_delta_pp"] for i in LINHAS if c[f"{i}_delta_pp"] == c[f"{i}_delta_pp"]]
    maximo = max([abs(d) for d in deltas] + [1.0])
    linhas = [
        f"""<tr><td>Eleitores aptos</td><td class="num">{fmt.inteiro(c['aptos_base'])}</td>
        <td class="num">{fmt.inteiro(c['aptos_comparacao'])}</td>
        <td class="num">{fmt.seta(c['aptos_variacao_pct'])} {fmt.variacao_pct(c['aptos_variacao_pct'])}</td>
        <td></td></tr>"""
    ]
    for i in LINHAS:
        delta = c[f"{i}_delta_pp"]
        linhas.append(
            f"""<tr><td>{data.INDICADORES[i][0]}</td>
            <td class="num">{fmt.pct(c[f'{i}_pct_base'])}</td>
            <td class="num">{fmt.pct(c[f'{i}_pct_comparacao'])}</td>
            <td class="num">{fmt.seta(delta)} {fmt.pp(delta)}</td>
            <td>{ui.barra_diferenca(delta, maximo)}</td></tr>"""
        )
    return ui.html(
        f"""<div class="tabela-rolagem"><table class="tab"><thead><tr><th>Indicador</th>
        <th>{rotulo_base}</th><th>{rotulo_comp}</th><th>Variação</th><th>Diferença</th></tr></thead>
        <tbody>{"".join(linhas)}</tbody></table></div>"""
    )


def render():
    ui.cabecalho("comparativo")
    mun = ui.municipio_ou_parar()
    cd = int(mun["cd_municipio_ibge"])
    st.markdown(f"## {mun['nm_municipio']} ({mun['sg_uf']}): 2022 × 2026")

    carregando = ui.esqueleto(3)
    try:
        anos = data.comparativo(cd, "anos", 2022, 1)
        t2022 = data.comparativo(cd, "turnos", 2022, 1)
        t2026 = data.comparativo(cd, "turnos", 2026, 1)
    except Exception as exc:  # noqa: BLE001
        carregando.empty()
        ui.erro_leitura(exc)
        ui.rodape()
        st.stop()
    carregando.empty()

    st.caption("Comparação do 1º turno de 2022 com o 1º turno de 2026.")
    if anos is None or anos["status_comparacao"] != "disponivel":
        ui.nota(
            "Este município não tem dados em 2022 (por exemplo, foi criado depois), "
            "então não há como comparar."
        )
    else:
        ui.mostrar(
            f'<p class="resumo">{narrativa.em_quatro_anos(anos["comparecimento_delta_pp"])}</p>'
        )
        ui.mostrar(tabela_evolucao(anos, "2022", "2026"))
        st.caption(
            "A variação dos eleitores aptos é relativa (%); as demais são em pontos percentuais "
            "(p.p.). Azul ▲ = aumentou · laranja ▼ = diminuiu (a cor não indica se é bom ou ruim)."
        )

    st.markdown("### 1º turno × 2º turno")
    colunas = st.columns(2)
    for coluna, ano, c in [(colunas[0], 2022, t2022), (colunas[1], 2026, t2026)]:
        with coluna:
            st.markdown(f"**{ano}**")
            if c is None or c["status_comparacao"] != "disponivel":
                ui.aguardando(f"O 2º turno de {ano} ainda não foi publicado pelo TSE.")
            else:
                ui.mostrar(tabela_evolucao(c, "1º turno", "2º turno"))
    ui.rodape()
