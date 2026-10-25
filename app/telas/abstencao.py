"""Quem ficou em casa? Abstenção por faixa etária, gênero e escolaridade (perfil do eleitorado, TSE)."""

from html import escape

import streamlit as st
from lib import data, fmt, narrativa, perfil, ui

ORDENS = ["Por idade", "Maior taxa primeiro"]
SUBTITULOS = {
    "faixa_etaria": "Faixas etárias como o TSE as publica: anos isolados de 16 a 20, depois de 5 em 5 anos",
    "genero": "Categorias do campo “gênero” do cadastro eleitoral do TSE",
    "escolaridade": "Grau de instrução declarado no cadastro eleitoral, nas 8 categorias do TSE",
}
FORA_DO_GRAFICO = {
    "faixa_etaria": "sem faixa etária válida no cadastro (“Inválido”)",
    "genero": "sem gênero informado no cadastro",
    "escolaridade": "sem escolaridade informada no cadastro",
}
# dimensão -> (rótulo do filtro, legenda das barras escura/clara, aviso quando ocultos)
FACULTATIVO = {
    "faixa_etaria": ("Mostrar idades de voto facultativo (16, 17 e 70 anos ou mais)",
                     ("18 a 69 anos", "Voto facultativo: 16, 17 e 70 anos ou mais"),
                     "Idades de voto facultativo ocultas pelo filtro"),
    "escolaridade": ("Mostrar analfabetos (voto facultativo)",
                     ("Demais níveis", "Voto facultativo: analfabetos"),
                     "Analfabetos ocultos pelo filtro"),
}
DIFERENCA_BASES = ("As outras telas usam os resultados por seção eleitoral, outra base do TSE. As taxas "
                   "podem diferir entre as bases; normalmente a diferença é pequena, mas há exceções.")


def _historico(cd: int, ano: int, turno: int):
    """(situação, dados) para narrativa.revelam e para o cartão de comparação."""
    if not data.tem_perfil(2026, turno):
        return "pendente", None
    base, comp = data.perfil(cd, 2022, turno), data.perfil(cd, 2026, turno)
    if base.empty or comp.empty:
        return "sem_base", None
    c = perfil.comparacao(base, comp)
    alta, queda = perfil.maiores_variacoes(c)
    return "disponivel", (perfil.total(base), perfil.total(comp), alta, queda, c)


def _filtro_facultativo(dimensao: str) -> bool:
    """Interruptor da seção: True = mostra os grupos com voto facultativo."""
    return st.toggle(FACULTATIVO[dimensao][0], value=True, key=f"abstencao_fac_{dimensao}")


def _contexto_idade_alta(df, nome: str) -> str:
    """Contexto junto do gráfico para as faixas mais altas, sem atribuir causa."""
    centenarios = df[(df["dimensao"] == "faixa_etaria") & (df["cd_categoria"] == 9999)]
    if centenarios.empty or int(centenarios.iloc[0]["aptos"]) == 0:
        return ""
    c = centenarios.iloc[0]
    return (f'<p class="fora-grafico">As faixas de 70 anos ou mais reúnem registros do cadastro '
            f"eleitoral com voto facultativo. Em {escape(nome)}, há {fmt.inteiro(c['aptos'])} registros "
            f"de 100 anos ou mais, com {fmt.pct(c['abstencao_pct'])} de abstenção. Os dados mostram a "
            "ausência desses registros, não o motivo.</p>")


def _rodape_grupo(df, dimensao: str, g, mostra_facultativo: bool = True) -> str:
    """Legenda, avisos (não informados, grupos ocultos) e tabela de um cartão de grupo."""
    tot = perfil.total(df)
    cores = FACULTATIVO[dimensao][1] if dimensao in FACULTATIVO and mostra_facultativo else None
    partes = [ui.legenda_grupos(tot["abstencao_pct"], cores, bool(g["base_pequena"].any()))]
    if not mostra_facultativo:
        ocultos = perfil.grupos(df, dimensao)
        ocultos = ocultos[ocultos["voto_facultativo"]]
        partes.append(f'<p class="fora-grafico">{FACULTATIVO[dimensao][2]}: '
                      f"{fmt.inteiro(ocultos['aptos'].sum())} eleitores. Eles continuam na média do "
                      "município.</p>")
    fora = perfil.nao_informados(df, dimensao)
    if fora:
        quem = "eleitor" if fora == 1 else "eleitores"
        verbo = "não aparece" if fora == 1 else "não aparecem"
        partes.append(f'<p class="fora-grafico">{fmt.inteiro(fora)} {quem} {FORA_DO_GRAFICO[dimensao]} '
                      f"{verbo} no gráfico, mas {'está' if fora == 1 else 'estão'} na média do município.</p>")
    partes.append(ui.tabela_grupos(g, tot))
    return "".join(partes)


def _cabecalho_cartao(titulo: str, dimensao: str) -> str:
    return (f'<div class="sub-cartao-wrap"><h2>{escape(titulo)}</h2>'
            f'<span class="sub-cartao">{escape(SUBTITULOS[dimensao])}</span></div>')


def _barras(df, g, anima: str = "") -> str:
    return ui.barras_grupos(g, perfil.total(df)["abstencao_pct"], *perfil.destaques(g), anima)


def _genero(df, anima: str) -> str:
    g = perfil.grupos(df, "genero")
    return ui.html(
        f"""<section class="cartao cartao-grupos{anima}" style="--i:3">{_cabecalho_cartao("Por gênero", "genero")}
        {_barras(df, g)}{_rodape_grupo(df, "genero", g)}</section>"""
    )


def _escolaridade(df) -> None:
    with st.container(key="abstencao_escolaridade"):
        ui.mostrar(_cabecalho_cartao("Por escolaridade", "escolaridade"))
        mostra = _filtro_facultativo("escolaridade")
        g = perfil.grupos(df, "escolaridade")
        if not mostra:
            g = g[~g["voto_facultativo"]]
        ui.mostrar(_barras(df, g) + _rodape_grupo(df, "escolaridade", g, mostra))


def _idade(df, nome: str, anima: str) -> None:
    with st.container(key="abstencao_idade"):
        cab, ordem_col = st.columns([3, 2], vertical_alignment="top")
        with cab:
            ui.mostrar(_cabecalho_cartao("Por faixa etária", "faixa_etaria"))
        with ordem_col:
            ordem = st.radio("Ordenar", ORDENS, horizontal=True, key="abstencao_ordem",
                             label_visibility="collapsed")
        mostra = _filtro_facultativo("faixa_etaria")
        g = perfil.grupos(df, "faixa_etaria")
        if not mostra:
            g = g[~g["voto_facultativo"]]
        destaques = perfil.destaques(g)
        if ordem == ORDENS[1]:
            g = g.sort_values(["abstencao_pct", "ordem"], ascending=[False, True])
        ui.mostrar(ui.barras_grupos(g, perfil.total(df)["abstencao_pct"], *destaques, anima))
        avisos = ('<p class="fora-grafico">Analfabetos têm voto facultativo em qualquer idade; por '
                  "isso, as faixas de 18 a 69 anos não reúnem só quem é obrigado a votar.</p>")
        if mostra:
            avisos += _contexto_idade_alta(df, nome)
        ui.mostrar(avisos + _rodape_grupo(df, "faixa_etaria", g, mostra))


def _tabela_historico(c, dimensao: str) -> str:
    linhas_df = c[c["dimensao"].isin(["total", dimensao])]
    deltas = linhas_df.loc[linhas_df["comparavel"], "delta_pp"].abs()
    maximo = max([*deltas.tolist(), 1.0])
    linhas = []
    for j, (_, r) in enumerate(linhas_df.iterrows()):
        delta = r["delta_pp"]
        classe = "up" if round(delta, 1) > 0 else "down" if round(delta, 1) < 0 else "flat"
        aviso = "" if r["comparavel"] else "*"
        nome = "Todos os eleitores" if r["dimensao"] == "total" else r["categoria"]
        linhas.append([
            (escape(nome), "total" if r["dimensao"] == "total" else "", True),
            (fmt.pct(r["abstencao_pct_base"]), "num base", False),
            (fmt.pct(r["abstencao_pct_comp"]), "num comp", False),
            (f'<span class="{classe}">{fmt.seta(round(delta, 1))} {fmt.pp(delta)}{aviso}</span>',
             "num dif-txt", False),
            (ui.barra_diferenca(delta, maximo, j) if r["comparavel"] else "", "", False),
            (fmt.inteiro(r["aptos_comp"]), "num base", False),
        ])
    cabecalho = [("Grupo", ""), ("2022", "num"), ("2026", "num"), ("Diferença", "num"),
                 ("", "col-barra"), ("Aptos em 2026", "num")]
    return ui.tabela_html(cabecalho, linhas)


def _comparacao(mun, turno: int, historico) -> None:
    situacao, dados = historico
    with st.container(key="abstencao_historico"):
        cab, seletor = st.columns([3, 2], vertical_alignment="top")
        with cab:
            ui.mostrar(
                f"""<div class="sub-cartao-wrap"><h2>Comparação 2022 × 2026</h2><span class="sub-cartao">
                Abstenção de cada grupo no {turno}º turno, em pontos percentuais (p.p.)</span></div>"""
            )
        if situacao == "pendente":
            ui.aguardando(
                f"Perfil do {turno}º turno de 2026 ainda não publicado",
                f"O TSE ainda não divulgou o perfil de quem votou e de quem se absteve no {turno}º "
                "turno de 2026. A comparação aparece aqui quando ele sair; nada é estimado antes disso.",
            )
            return
        if situacao == "sem_base":
            ui.nota(f"{mun['nm_municipio']} não tem dados de 2022 (município instalado depois), "
                    "então não há comparação entre as eleições.")
            return
        with seletor:
            dimensao = st.radio("Grupo", list(perfil.DIMENSOES), horizontal=True,
                                format_func=perfil.DIMENSOES.get, key="abstencao_hist_dim",
                                label_visibility="collapsed")
        c = dados[-1]
        if dimensao in FACULTATIVO and not st.toggle(
            "Mostrar grupos de voto facultativo", value=True, key="abstencao_fac_historico"
        ):
            c = c[~c["voto_facultativo"] | (c["dimensao"] == "total")]
        ui.mostrar(ui.legenda_aumento())
        ui.mostrar(_tabela_historico(c, dimensao))
        pequena = not c[c["dimensao"].isin(["total", dimensao])]["comparavel"].all()
        ui.mostrar(
            '<p class="fora-grafico">Mesmas categorias do TSE nos dois anos. '
            + ("* Grupo com menos de 50 eleitores aptos em um dos anos: variação instável, fora dos "
               "destaques. " if pequena else "")
            + "A cor indica só a direção da mudança, não se ela é boa ou ruim.</p>"
        )


def _nota_metodologica(df) -> str:
    gerado = df["dt_geracao"].max().strftime("%d/%m/%Y")
    itens = [
        "<b>Como a taxa é calculada:</b> eleitores do grupo que não compareceram ÷ eleitores aptos "
        "do grupo × 100. Ao lado de cada taxa aparece quantas pessoas formam o grupo.",
        "<b>Grupos, não pessoas:</b> os números descrevem grupos agregados de eleitores. Eles não "
        "identificam o comportamento de ninguém e não explicam por que alguém deixou de votar.",
        "<b>Uma característica por vez:</b> cada gráfico olha só a idade, o gênero ou a "
        "escolaridade. Diferenças entre grupos podem se sobrepor (por exemplo, idade e escolaridade).",
        "<b>Voto facultativo</b> para analfabetos, para quem tem 16 ou 17 anos e para quem tem 70 anos "
        "ou mais (Constituição, art. 14, § 1º, II). Os filtros de cada seção mostram ou ocultam "
        "esses grupos.",
        "<b>Registros do cadastro:</b> os grupos são formados pelos registros do cadastro eleitoral. "
        "Nas faixas de idade mais altas, a abstenção passa de 90%; o TSE não detalha a situação "
        "desses registros, e esta tela não atribui o resultado a uma causa.",
        f"<b>Grupos pequenos:</b> com menos de {perfil.BASE_MINIMA} eleitores aptos, o percentual "
        "aparece com * e fica fora dos destaques e das frases automáticas.",
        "<b>Fonte:</b> TSE, perfil do eleitorado que compareceu e que se absteve "
        f"(perfil_comparecimento_abstencao), arquivo gerado em {gerado}, a base do painel oficial de "
        f"comparecimento do TSE. {DIFERENCA_BASES}",
    ]
    lista = "".join(f"<li>{item}</li>" for item in itens)
    return ui.html(
        f"""<section class="cartao nota-metodo"><div class="sub-cartao-wrap"><h2>Como ler estes
        números</h2></div><ul>{lista}</ul><a href="{ui.url("metodologia")}" target="_self">
        Ver a metodologia completa <span aria-hidden="true">→</span></a></section>"""
    )


def render():
    ui.cabecalho("abstencao")
    ui.abertura("abstencao")
    mun = ui.municipio_ou_parar()
    cd = int(mun["cd_municipio_ibge"])
    anima = ui.anima("abstencao")

    with st.container(key="filtros"):
        ano, turno = st.radio(
            "Eleição",
            data.ELEICOES,
            format_func=lambda e: f"{e[0]} · {e[1]}º turno",
            horizontal=True,
            index=ui.indice_eleicao(),
            key="abstencao_eleicao",
        )
    ui.lembrar_eleicao(ano, turno)

    carregando = ui.carregando()
    try:
        df = data.perfil(cd, ano, turno)
        historico = _historico(cd, ano, turno)
    except Exception as exc:  # noqa: BLE001 - qualquer falha de leitura vira mensagem amigável
        carregando.empty()
        ui.erro_leitura(exc)
        ui.rodape()
        st.stop()
    carregando.empty()

    tot = perfil.total(df)
    if tot is None:
        ui.mostrar(ui.contexto_livre(f"{mun['rotulo']} · Eleição presidencial {ano} · {turno}º turno"))
        if not data.tem_perfil(ano, turno):
            ui.aguardando(
                f"O perfil do {turno}º turno de {ano} ainda não foi publicado",
                "O TSE divulga o perfil de quem compareceu e de quem se absteve depois da "
                "totalização. Enquanto isso, veja o 1º turno de 2026 ou as eleições de 2022.",
            )
        else:
            ui.nota(f"Não há dados desta eleição para {mun['nm_municipio']} (município instalado "
                    "depois). Escolha outra eleição.")
        ui.rodape()
        st.stop()

    ui.mostrar(ui.linha_contexto(mun["nm_municipio"], mun["sg_uf"], ano, turno, tot["aptos"]))
    ui.mostrar(ui.manchete(
        "Quem ficou em casa",
        narrativa.manchete_abstencao(mun["nm_municipio"], tot["abstencao_pct"], ano, turno),
        anima,
    ))

    situacao, dados = historico
    delta = None
    if situacao == "disponivel":
        delta = dados[1]["abstencao_pct"] - dados[0]["abstencao_pct"]
    heroi = ui.cartao_heroi(
        "Abstenção no município", fmt.pct(tot["abstencao_pct"]),
        f"{fmt.inteiro(tot['abstencoes'])} de {fmt.inteiro(tot['aptos'])} eleitores não foram votar",
        [(f"{turno}º turno, 2022 → 2026", delta)], anima, 1,
    )
    historico_txt = (situacao, dados[:4] if dados else None)
    leitura = ui.cartao_leitura(
        narrativa.revelam(
            mun["nm_municipio"], ano, turno, tot, perfil.grupos(df, "faixa_etaria"),
            perfil.grupos(df, "genero"), perfil.grupos(df, "escolaridade"), historico_txt,
        ),
        anima=anima, i=2, rotulo="O que os dados revelam?", visiveis=3,
    )
    ui.mostrar(f'<div class="grade-abstencao">{heroi}{leitura}</div>')
    ui.mostrar(
        '<div class="legenda-pp">Frases geradas por regras fixas a partir dos números (sem IA). '
        "Mostram onde a ausência foi maior ou menor, não por que as pessoas deixaram de votar.</div>"
    )

    _idade(df, mun["nm_municipio"], anima)
    genero, escolaridade = st.columns([2, 3], gap="large")
    with genero:
        ui.mostrar(_genero(df, anima))
    with escolaridade:
        _escolaridade(df)
    _comparacao(mun, turno, historico)
    ui.mostrar(_nota_metodologica(df))
    ui.rodape()
