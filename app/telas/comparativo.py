"""Comparativo 2022 × 2026 e 1º × 2º turno (D4: comparação fixa 2022 → 2026)."""

import streamlit as st
from lib import data, fmt, narrativa, ui

LINHAS = ["comparecimento", "abstencoes", "validos", "brancos", "nulos", "brancos_nulos"]
TURNOS = ["comparecimento", "abstencoes", "brancos", "nulos"]


def _classe(delta) -> str:
    return "up" if delta > 0 else "down" if delta < 0 else "flat"


def tabela_evolucao(c) -> str:
    """Tabela com barra de diferença centrada no zero (aptos: variação em %, sem barra)."""
    deltas = [c[f"{i}_delta_pp"] for i in LINHAS if c[f"{i}_delta_pp"] == c[f"{i}_delta_pp"]]
    maximo = max([abs(d) for d in deltas] + [1.0])
    linhas = []
    for j, i in enumerate(LINHAS):
        delta = c[f"{i}_delta_pp"]
        linhas.append([
            (data.INDICADORES[i][0], "", True),
            (fmt.pct(c[f"{i}_pct_base"]), "num base", False),
            (fmt.pct(c[f"{i}_pct_comparacao"]), "num comp", False),
            (f'<span class="{_classe(delta)}">{fmt.seta(delta)} {fmt.pp(delta)}</span>', "num dif-txt", False),
            (ui.barra_diferenca(delta, maximo, j), "", False),
        ])
    variacao = c["aptos_variacao_pct"]
    linhas.append([
        ("Eleitores aptos (variação)", "", True),
        (fmt.inteiro(c["aptos_base"]), "num base", False),
        (fmt.inteiro(c["aptos_comparacao"]), "num comp", False),
        (f'<span class="{_classe(variacao)}">{fmt.seta(variacao)} {fmt.variacao_pct(variacao)}</span>',
         "num dif-txt", False),
        ("", "", False),
    ])
    cabecalho = [("Indicador", ""), ("2022", "num"), ("2026", "num"), ("Diferença", "num"),
                 ("", "col-barra")]
    return ui.tabela_html(cabecalho, linhas)


def cartao_turno(ano: int, c, anima: str, i: int) -> str:
    disponivel = c is not None and c["status_comparacao"] == "disponivel"
    if c is None:
        indicadores = []
    else:
        indicadores = [
            (data.INDICADORES[k][0], c[f"{k}_pct_base"], c[f"{k}_pct_comparacao"]) for k in TURNOS
        ]
    if disponivel:
        selo = ui.etiqueta("Apuração concluída", "ok")
        nota = narrativa.entre_turnos(ano, c["comparecimento_delta_pp"], c["brancos_nulos_delta_pp"])
    else:
        selo = ui.etiqueta(ui.segundo_turno_pendente(), "aviso")
        nota = (f"Os dados do 2º turno de {ano} aparecem aqui automaticamente após a "
                "totalização oficial.")
    return ui.html(
        f"""<article class="turno{anima}" style="--i:{i}"><div class="cab"><h3>Eleição {ano}</h3>
        {selo}</div>{ui.barras_pareadas(indicadores, pendente=not disponivel)}
        <p class="nota-turno">{nota}</p></article>"""
    )


def render():
    ui.cabecalho("comparativo")
    ui.abertura("comparativo")
    mun = ui.municipio_ou_parar()
    cd = int(mun["cd_municipio_ibge"])
    anima = ui.anima("comparativo")

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

    ui.mostrar(ui.contexto_livre(
        f"{mun['rotulo']} · 1º turno de 2022 comparado com o 1º turno de 2026"
    ))
    if anos is None or anos["status_comparacao"] != "disponivel":
        ui.nota(
            "Este município não tem dados em 2022 (por exemplo, foi criado depois), "
            "então não há como comparar."
        )
    else:
        ui.mostrar(ui.manchete(
            "Em quatro anos",
            narrativa.manchete_comparativo(
                mun["nm_municipio"], anos["aptos_base"], anos["aptos_comparacao"],
                anos["comparecimento_delta_pp"], anos["brancos_nulos_delta_pp"],
            ),
            anima, menor=True,
        ))
        ui.mostrar(ui.cartao_tabela(
            "Evolução dos indicadores · 1º turno",
            "Diferença em pontos percentuais (p.p.) de 2026 em relação a 2022",
            tabela_evolucao(anos), ui.legenda_aumento(), anima, 1,
        ))

    ui.mostrar(
        """<section class="secao-cab"><h2>1º turno × 2º turno</h2><span>Como o comportamento
        do eleitor mudou entre os turnos de cada eleição presidencial</span></section>"""
    )
    ui.mostrar(ui.legenda_turnos())
    ui.mostrar(
        '<div class="cartoes-turnos">'
        + cartao_turno(2022, t2022, anima, 2)
        + cartao_turno(2026, t2026, anima, 3)
        + "</div>"
    )
    ui.rodape()
