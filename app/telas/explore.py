"""Explore seu município."""

import streamlit as st
from lib import data, fmt, narrativa, ui

COLUNAS_ZONAS = [
    ("aptos", "Eleitores aptos", fmt.inteiro),
    ("comparecimento_pct", "Comparecimento", fmt.pct),
    ("abstencoes_pct", "Abstenção", fmt.pct),
    ("brancos_nulos_pct", "Brancos + nulos", fmt.pct),
]


def tabela_zonas(zonas):
    """Tabela exibida no cartão "Zona por zona"; o CSV baixa exatamente estas linhas e colunas
    (Zona, Eleitores aptos, Comparecimento, Abstenção, Brancos + nulos), já formatadas."""
    saida = zonas[["nr_zona"]].rename(columns={"nr_zona": "Zona"})
    saida["Zona"] = saida["Zona"].map(lambda nr: f"{int(nr):03d}ª Zona")
    for coluna, titulo, formato in COLUNAS_ZONAS:
        saida[titulo] = zonas[coluna].map(formato)
    return saida.reset_index(drop=True)


def _tabela_html(tabela) -> str:
    cabecalho = [("Zona", "")] + [(t, "num") for _, t, _ in COLUNAS_ZONAS]
    linhas = [
        [(linha["Zona"], "", True)] + [(linha[t], "num", False) for _, t, _ in COLUNAS_ZONAS]
        for _, linha in tabela.iterrows()
    ]
    return ui.tabela_html(cabecalho, linhas, alta=len(tabela) > 12)


def render():
    ui.cabecalho("explore")
    ui.abertura("explore")
    mun = ui.municipio_ou_parar()
    cd = int(mun["cd_municipio_ibge"])
    anima = ui.anima("explore")

    with st.container(key="filtros"):
        ano, turno = st.radio(
            "Eleição",
            data.ELEICOES,
            format_func=lambda e: f"{e[0]} · {e[1]}º turno",
            horizontal=True,
            key="explore_eleicao",
        )

    carregando = ui.esqueleto(3)
    try:
        ind = data.indicadores(cd, ano, turno)
        base = data.comparativo(cd, "anos", 2022, 1) if (ano, turno) == (2026, 1) else None
        ind_2022 = data.indicadores(cd, 2022, 1) if (ano, turno) == (2026, 1) else None
        zonas = data.zonas(cd, ano, turno)
    except Exception as exc:  # noqa: BLE001 - qualquer falha de leitura vira mensagem amigável
        carregando.empty()
        ui.erro_leitura(exc)
        ui.rodape()
        st.stop()
    carregando.empty()

    if ind is None:
        ui.mostrar(ui.contexto_livre(
            f"{mun['rotulo']} · Eleição presidencial {ano} · {turno}º turno"
        ))
        ui.aguardando(
            f"O {turno}º turno de {ano} ainda está sendo apurado",
            f"Assim que a totalização oficial for liberada, os números de {mun['nm_municipio']} "
            "aparecem aqui. Enquanto isso, veja o 1º turno ou o 2º turno de 2022.",
        )
        ui.rodape()
        st.stop()

    ui.mostrar(ui.linha_contexto(mun["nm_municipio"], mun["sg_uf"], ano, turno, ind["aptos"]))
    ui.mostrar(ui.manchete(
        "O que os números dizem",
        narrativa.manchete_explore(
            mun["nm_municipio"], ind["comparecimento_pct"],
            ind["comparecimento_delta_brasil_pp"], ind["abstencoes_delta_uf_pp"],
        ),
        anima,
    ))

    delta_2022 = {}
    if base is not None and base["status_comparacao"] == "disponivel":
        delta_2022 = {"comparecimento": base["comparecimento_delta_pp"],
                      "abstencoes": base["abstencoes_delta_pp"]}
    nome_uf = data.NOME_UF.get(mun["sg_uf"], mun["sg_uf"])

    def comparacoes(indicador):
        itens = [
            (f"vs. {nome_uf}", ind[f"{indicador}_delta_uf_pp"]),
            ("vs. Brasil", ind[f"{indicador}_delta_brasil_pp"]),
        ]
        if indicador in delta_2022:
            itens.append(("vs. 2022", delta_2022[indicador]))
        return itens

    heroi_comp = ui.cartao_heroi(
        "Comparecimento", fmt.pct(ind["comparecimento_pct"]),
        f"{fmt.inteiro(ind['comparecimento'])} eleitores foram votar",
        comparacoes("comparecimento"), anima, 1,
    )
    heroi_abst = ui.cartao_heroi(
        "Abstenção", fmt.pct(ind["abstencoes_pct"]),
        f"{fmt.inteiro(ind['abstencoes'])} eleitores não foram votar",
        comparacoes("abstencoes"), anima, 2,
    )
    leitura = ui.cartao_leitura(
        narrativa.leitura_rapida(
            ind["comparecimento_delta_uf_pp"],
            ind["comparecimento_delta_brasil_pp"],
            delta_2022.get("comparecimento"),
            ind["brancos_nulos_pct"],
            ind["brancos_nulos_delta_brasil_pp"],
            comp_delta_br_2022=(
                ind_2022["comparecimento_delta_brasil_pp"] if ind_2022 is not None else None
            ),
            nome=mun["nm_municipio"],
        ),
        link=(f"Ver {mun['nm_municipio']} em perspectiva", ui.url("brasil")),
        anima=anima, i=3,
    )
    ui.mostrar(ui.grade_herois(heroi_comp, heroi_abst, leitura))
    ui.mostrar(
        '<div class="legenda-pp">“p.p.” = ponto percentual, a diferença simples entre duas '
        "porcentagens. ▲ azul = aumentou · ▼ laranja = diminuiu.</div>"
    )

    ui.mostrar(ui.bloco_votos(
        ind["validos_pct"], ind["brancos_pct"], ind["nulos_pct"],
        ind["validos"], ind["brancos"], ind["nulos"],
        narrativa.votos(ind["comparecimento"], ind["brancos_nulos_delta_brasil_pp"]),
        anima, 4,
    ))

    with st.container(key="zonas"):
        cabeca, botao = st.columns([4, 1], vertical_alignment="center")
        with cabeca:
            ui.mostrar(
                '<div class="sub-cartao-wrap"><h3>Zona por zona</h3>'
                '<span class="sub-cartao">A participação muda dentro da própria cidade</span></div>'
            )
        if len(zonas) <= 1:
            ui.nota("O município tem uma única zona eleitoral; os números acima já são os dela.")
        else:
            tabela = tabela_zonas(zonas)
            with botao:
                st.download_button(
                    "Baixar CSV",
                    tabela.to_csv(index=False, sep=";").encode("utf-8-sig"),
                    file_name=f"zonas_{cd}_{ano}_t{turno}.csv",
                    mime="text/csv",
                    icon=":material/download:",
                )
            ui.mostrar(_tabela_html(tabela))
    ui.rodape()
