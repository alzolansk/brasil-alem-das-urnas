"""Layout base e componentes HTML do protótipo (docs/design/especificacao-fidelidade-prototipo.md)."""

import base64
from html import escape
from pathlib import Path

import streamlit as st

from . import data, fmt

ASSETS = Path(__file__).resolve().parents[1] / "assets"
PAGINAS: dict = {}  # preenchido por navegacao.py: chave -> st.Page

ABAS = [
    ("explore", "Explore seu município"),
    ("comparativo", "Comparativo 2022 × 2026"),
    ("mapa", "Mapa eleitoral"),
    ("brasil", "Brasil em perspectiva"),
]
RODAPE = [
    ("metodologia", "Metodologia"),
    ("dicionario", "Dicionário de dados"),
    ("dados", "Sobre os dados"),
    ("acessibilidade", "Acessibilidade"),
    ("termos", "Termos de uso"),
    ("contato", "Contato"),
]
TITULOS = dict(ABAS) | dict(RODAPE)
ABERTURAS = {
    "explore": (
        "Explore seu município",
        "Quantas pessoas votaram na sua cidade, quantas ficaram em casa e como ficaram os "
        "votos. Tudo comparado com o estado e com o país.",
    ),
    "comparativo": (
        "Comparativo 2022 × 2026",
        "Veja como os indicadores do município evoluíram entre as duas últimas eleições "
        "presidenciais e o que mudou de um turno para o outro.",
    ),
    "mapa": (
        "Mapa eleitoral interativo",
        "Escolha um indicador e filtre por região para identificar padrões no território. "
        "Selecione um estado para ver o detalhe e descer até os municípios.",
    ),
    "brasil": (
        "Brasil em perspectiva",
        "Compare o município com o seu estado e com a média nacional para entender onde ele "
        "se destaca e para onde está caminhando.",
    ),
}
RELOGIO = (
    '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="2" stroke-linecap="round" aria-hidden="true" style="color:var(--blue)">'
    '<circle cx="12" cy="12" r="9"></circle><path d="M12 7v5l3 2"></path></svg>'
)


def html(texto: str) -> str:
    """Junta as linhas com espaço: recuo de 4 espaços viraria bloco de código no markdown."""
    return " ".join(linha.strip() for linha in texto.splitlines() if linha.strip())


def mostrar(texto: str) -> None:
    st.markdown(html(texto), unsafe_allow_html=True)


def _ler(nome: str) -> str:
    return (ASSETS / nome).read_text(encoding="utf-8")


def _css_aba_ativa(ativa: str) -> str:
    """O st.page_link não expõe aria-current; a aba ativa é marcada pela chave do contêiner."""
    alvo = f".st-key-aba_{ativa} [data-testid='stPageLink-NavLink']"
    return (
        f"{alvo} {{ border-bottom-color: var(--blue) !important; }}"
        f"{alvo} p {{ color: var(--blue) !important; font-weight: 700 !important; }}"
    )


def injetar_css(ativa: str) -> None:
    css = _ler("style.css") + _css_aba_ativa(ativa)
    if st.session_state.get("alto_contraste"):
        css += _ler("contraste.css")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def anima(pagina: str) -> str:
    """Devolve ' anima' só na primeira renderização desta tela para este município."""
    chave = f"_animou_{pagina}_{st.session_state.get('cd_ibge')}"
    if st.session_state.get(chave):
        return ""
    st.session_state[chave] = True
    return " anima"


# --- município selecionado e URL ----------------------------------------------------


def _inicializar_estado() -> None:
    if "cd_ibge" not in st.session_state:
        try:
            st.session_state["cd_ibge"] = int(st.query_params.get("m", data.IBGE_PADRAO))
        except (TypeError, ValueError):
            st.session_state["cd_ibge"] = data.IBGE_PADRAO
    if "alto_contraste" not in st.session_state:
        st.session_state["alto_contraste"] = st.query_params.get("c") == "1"


def url(pagina: str = "explore") -> str:
    """Link interno com o município (e o alto contraste). O Explore é servido na raiz."""
    caminho = "/" if pagina == "explore" else f"/{pagina}"
    consulta = f"?m={st.session_state.get('cd_ibge', data.IBGE_PADRAO)}"
    if st.session_state.get("alto_contraste"):
        consulta += "&c=1"
    return caminho + consulta


def seletor_municipio() -> None:
    _inicializar_estado()
    with st.container(key="busca"):
        texto = st.text_input(
            "Buscar município",
            key="busca_txt",
            placeholder="Buscar município ou estado",
            label_visibility="collapsed",
        )
        if texto.strip():
            achados = data.buscar(texto)
            if achados.empty:
                sugestoes = data.parecidos(texto)
                st.warning(
                    f"Nenhum município encontrado para “{texto}”."
                    + (f" Você quis dizer: {', '.join(sugestoes)}?" if sugestoes else "")
                )
            else:
                rotulo = st.selectbox(
                    "Resultados", achados["rotulo"].tolist(), label_visibility="collapsed"
                )
                par = (texto, rotulo)
                if st.session_state.get("busca_ultima") != par:
                    st.session_state["busca_ultima"] = par
                    linha = achados[achados["rotulo"] == rotulo].iloc[0]
                    st.session_state["cd_ibge"] = int(linha["cd_municipio_ibge"])
    st.query_params["m"] = str(st.session_state["cd_ibge"])
    if st.session_state.get("alto_contraste"):
        st.query_params["c"] = "1"
    elif "c" in st.query_params:
        del st.query_params["c"]


def municipio_atual():
    """Linha do município escolhido; None se o código não existir."""
    _inicializar_estado()
    return data.municipio(st.session_state["cd_ibge"])


# --- layout base -------------------------------------------------------------------


@st.cache_data(show_spinner=False)
def _logo() -> str:
    return base64.b64encode((ASSETS / "logo.svg").read_bytes()).decode()


def _selo() -> str:
    if data.tem_dados(2026, 2):
        return etiqueta("Apuração concluída: 1º e 2º turnos 2026", "ok")
    return etiqueta("1º turno 2026 apurado · 2º turno em 25/10", "aviso")


def cabecalho(ativa: str) -> None:
    _inicializar_estado()
    injetar_css(ativa)
    with st.container(key="topo", gap=None):
        with st.container(
            key="utilitaria", horizontal=True, horizontal_alignment="distribute",
            vertical_alignment="center",
        ):
            mostrar(
                '<span class="util-texto">Ferramenta independente de consulta a dados '
                "eleitorais públicos</span>"
            )
            with st.container(
                horizontal=True, gap="medium", vertical_alignment="center", width="content"
            ):
                st.page_link(PAGINAS["acessibilidade"], label="Acessibilidade")
                st.page_link(PAGINAS["dados"], label="Sobre os dados")
                st.toggle("Alto contraste", key="alto_contraste")
        mostrar('<div class="faixa" aria-hidden="true"><i></i><i></i><i></i></div>')
        with st.container(key="cabecalho"):
            marca, busca = st.columns([3, 2], vertical_alignment="center")
            with marca:
                mostrar(
                    f"""<a class="marca-site" href="{url()}" target="_self">
                    <img src="data:image/svg+xml;base64,{_logo()}" alt="">
                    <span><span class="nome">Brasil Além das Urnas</span>
                    <span class="sub">Dados do eleitorado e do comparecimento</span></span></a>"""
                )
            with busca:
                seletor_municipio()
            _navegacao()
    _trilha(ativa)


def _navegacao() -> None:
    with st.container(key="nav_desktop", horizontal=True, gap="large"):
        for chave, titulo in ABAS:
            with st.container(key=f"aba_{chave}", width="content"):
                st.page_link(PAGINAS[chave], label=titulo)
    with st.container(key="nav_mobile"), st.popover("☰ Menu", width="stretch"):
        for chave, titulo in ABAS:
            st.page_link(PAGINAS[chave], label=titulo)


def _trilha(ativa: str) -> None:
    itens = [f'<a href="{url()}" target="_self">Início</a>']
    mun = municipio_atual()
    if ativa in dict(ABAS) and mun is not None:
        itens += [
            '<span aria-hidden="true">›</span>',
            f"<span>{escape(TITULOS[ativa])}</span>",
            '<span aria-hidden="true">›</span>',
            f'<span aria-current="page">{escape(mun["rotulo"])}</span>',
        ]
    else:
        itens += [
            '<span aria-hidden="true">›</span>',
            f'<span aria-current="page">{escape(TITULOS.get(ativa, ""))}</span>',
        ]
    mostrar(
        f"""<div class="trilha-linha"><nav class="trilha" aria-label="Você está em">
        {"".join(itens)}</nav>{_selo()}</div>"""
    )


def abertura(pagina: str) -> None:
    titulo, texto = ABERTURAS[pagina]
    mostrar(f'<section class="abertura"><h1>{escape(titulo)}</h1><p>{escape(texto)}</p></section>')


def rodape() -> None:
    with st.container(key="rodape"):
        esquerda, direita = st.columns([1, 1], vertical_alignment="center")
        with esquerda:
            mostrar(
                f"""<strong>Brasil Além das Urnas</strong><div class="texto-rodape">
                Ferramenta independente, sem vínculo com órgãos públicos ou partidos. Fonte:
                Portal de Dados Abertos do TSE e IBGE · dados atualizados em
                {data.ultima_atualizacao()}.</div>"""
            )
        with direita, st.container(key="rodape_links", horizontal=True):
            for chave, titulo in RODAPE:
                st.page_link(PAGINAS[chave], label=titulo)


# --- componentes -------------------------------------------------------------------------


def _classe(delta) -> str:
    if delta is None or delta != delta or round(float(delta), 1) == 0:
        return "flat"
    return "up" if delta > 0 else "down"


def _delta_txt(delta) -> str:
    """Seta + valor no padrão D5. Sem base: 'sem base'."""
    if delta is None or delta != delta:
        return "sem base"
    return f"{fmt.seta(round(float(delta), 1))} {fmt.pp_sem_mais(delta)}"


def linha_contexto(municipio, uf, ano, turno, aptos) -> str:
    return html(
        f"""<div class="contexto">{escape(municipio)} ({escape(uf)}) · Eleição presidencial
        {ano} · {turno}º turno · {fmt.inteiro(aptos)} eleitores aptos</div>"""
    )


def contexto_livre(texto: str) -> str:
    return f'<div class="contexto">{escape(texto)}</div>'


def manchete(rotulo: str, partes: dict, anima: str = "", menor: bool = False, i: int = 0) -> str:
    classe = "achado" + (" menor" if menor else "") + anima
    return html(
        f"""<section class="{classe}" style="--i:{i}"><span class="rotulo">{escape(rotulo)}</span>
        <h2>{escape(partes["antes"])} <span class="marca">{escape(partes["destaque"])}</span>{escape(partes["depois"])}</h2>
        </section>"""
    )


def cartao_heroi(titulo, valor, frase, comparacoes, anima: str = "", i: int = 0) -> str:
    """comparacoes: [(rótulo, delta_pp)] na ordem vs. estado, vs. Brasil, vs. 2022."""
    itens = "".join(
        f'<div><dt>{escape(rotulo)}</dt><dd class="{_classe(delta)}">{escape(_delta_txt(delta))}</dd></div>'
        for rotulo, delta in comparacoes
    )
    return html(
        f"""<article class="heroi{anima}" style="--i:{i}"><h3>{escape(titulo)}</h3>
        <span class="numero">{escape(valor)}</span><span class="frase">{escape(frase)}</span>
        <dl class="comparacoes">{itens}</dl></article>"""
    )


def cartao_leitura(itens, link: tuple | None = None, anima: str = "", i: int = 0) -> str:
    """link: (texto, href) opcional no rodapé do cartão."""
    lista = "".join(
        f'<li><b aria-hidden="true">{n}</b><span>{escape(item)}</span></li>'
        for n, item in enumerate(itens, start=1)
    )
    rodape_link = (
        f'<a class="link-claro" href="{escape(link[1])}" target="_self">{escape(link[0])} '
        '<span aria-hidden="true">→</span></a>'
        if link
        else ""
    )
    return html(
        f"""<aside class="escuro{anima}" style="--i:{i}"><span class="rotulo">Leitura rápida</span>
        <ol>{lista}</ol>{rodape_link}</aside>"""
    )


def grade_herois(heroi1: str, heroi2: str, leitura: str) -> str:
    return f'<div class="grade-herois">{heroi1}{heroi2}{leitura}</div>'


def barra_empilhada(partes) -> str:
    """partes: [(nome, pct, cor_css)]. Sem texto dentro dos segmentos."""
    segmentos = "".join(
        f'<span style="width:{max(v, 0.3)}%;background:{cor};--j:{j}"></span>'
        for j, (_, v, cor) in enumerate(partes)
    )
    descricao = ", ".join(f"{n} {fmt.pct(v)}" for n, v, _ in partes) + " dos votos"
    return f'<div class="barra" role="img" aria-label="{escape(descricao)}">{segmentos}</div>'


def bloco_votos(
    validos, brancos, nulos, qtd_validos, qtd_brancos, qtd_nulos, texto, anima: str = "", i: int = 0
) -> str:
    partes = [
        ("Válidos", validos, "var(--green)", qtd_validos),
        ("Brancos", brancos, "var(--yellow)", qtd_brancos),
        ("Nulos", nulos, "var(--orange)", qtd_nulos),
    ]
    numeros = "".join(
        f"""<div><span class="nome"><i class="quadrado" style="background:{cor}"></i>{n}</span>
        <span class="pct">{fmt.pct(v)}</span><span class="qtd">{fmt.inteiro(q)} votos</span></div>"""
        for n, v, cor, q in partes
    )
    return html(
        f"""<section class="votos{anima}" style="--i:{i}"><div class="texto">
        <h3>E quem votou, votou em quê?</h3><p>{escape(texto)}</p></div>
        <div class="grafico">{barra_empilhada([(n, v, c) for n, v, c, _ in partes])}
        <div class="numeros">{numeros}</div></div></section>"""
    )


def tabela_html(cabecalho: list, linhas: list, alta: bool = False) -> str:
    """cabecalho: [(texto, classe)]; linhas: [[(texto, classe, é_cabeçalho_de_linha)]]."""
    ths = "".join(f'<th scope="col" class="{c}">{escape(t)}</th>' for t, c in cabecalho)
    corpo = "".join(
        "<tr>"
        + "".join(
            f'<th scope="row" class="{c}">{t}</th>' if eh_th else f'<td class="{c}">{t}</td>'
            for t, c, eh_th in linha
        )
        + "</tr>"
        for linha in linhas
    )
    classe = "tabela-rolagem" + (" alta" if alta else "")
    return html(
        f"""<div class="{classe}"><table class="tab"><thead><tr>{ths}</tr></thead>
        <tbody>{corpo}</tbody></table></div>"""
    )


def cartao_tabela(titulo, subtitulo, tabela, direita: str = "", anima: str = "", i: int = 0) -> str:
    return html(
        f"""<section class="cartao-tabela{anima}" style="--i:{i}"><div class="cab-cartao">
        <div><h2>{escape(titulo)}</h2><span>{escape(subtitulo)}</span></div>{direita}</div>
        {tabela}</section>"""
    )


def legenda_aumento() -> str:
    return html(
        """<div class="legenda-dir" title="A cor indica só a direção da mudança, não se ela é boa ou ruim.">
        <span><i class="quadrado" style="background:var(--blue)"></i>Aumentou</span>
        <span><i class="quadrado" style="background:var(--orange)"></i>Diminuiu</span></div>"""
    )


def barra_diferenca(delta_pp, maximo: float, j: int = 0) -> str:
    """Barra centrada no zero: azul para a direita (aumentou), laranja para a esquerda."""
    if delta_pp is None or delta_pp != delta_pp:
        return ""
    largura = min(abs(delta_pp) / maximo, 1) * 50 if maximo else 0
    classe = "up" if delta_pp > 0 else "down"
    return (
        f'<div class="dif" aria-hidden="true"><b class="{classe}" '
        f'style="width:{largura:.1f}%;--j:{j}"></b></div>'
    )


def etiqueta(texto: str, tipo: str) -> str:
    return f'<span class="etiqueta {tipo}">{escape(texto)}</span>'


def barras_pareadas(indicadores, pendente: bool) -> str:
    """indicadores: [(nome, pct_1t, pct_2t)]."""
    blocos = []
    for j, (nome, v1, v2) in enumerate(indicadores):
        if pendente:
            barra2 = '<div class="trilho"><i class="tracejado" style="width:100%;background:transparent"></i></div>'
            valor2 = '<span class="val flat">Aguardando</span>'
        else:
            barra2 = f'<div class="trilho"><i style="width:{v2}%;background:var(--blue-2t);--j:{j}"></i></div>'
            valor2 = f'<span class="val">{fmt.pct(v2)}</span>'
        blocos.append(
            f"""<div class="ind"><span>{escape(nome)}</span><div class="pares">
            <span class="rot">1º turno</span>
            <div class="trilho"><i style="width:{v1}%;background:var(--blue);--j:{j}"></i></div>
            <span class="val">{fmt.pct(v1)}</span><span class="rot">2º turno</span>{barra2}{valor2}
            </div></div>"""
        )
    return html("".join(blocos))


def legenda_turnos() -> str:
    return html(
        """<div class="legenda-linha">
        <span><i class="quadrado" style="background:var(--blue)"></i>1º turno</span>
        <span><i class="quadrado" style="background:var(--blue-2t)"></i>2º turno</span>
        <span><i class="quadrado tracejado"></i>Aguardando apuração</span></div>"""
    )


def cartao_escopo(tipo, nome, aptos, serie, anima: str = "", i: int = 0) -> str:
    aptos_txt = fmt.mil(aptos)
    return html(
        f"""<article class="escopo serie-{serie}{anima}" style="--i:{i}">
        <span class="rotulo-cinza">{escape(tipo)}</span><h2>{escape(nome)}</h2>
        <span>{escape(aptos_txt)} eleitores aptos</span></article>"""
    )


def bloco_indicador(nome, valores, escala, delta_uf, delta_br) -> str:
    """valores: [(rótulo, pct, serie)]; escala = valor que ocupa 100% da barra."""
    linhas = "".join(
        f"""<div class="linha-barra"><span class="rot">{escape(rot)}</span>
        <div class="barra-h"><i class="serie-{serie}-bg" style="width:{min(v / escala * 100, 100):.1f}%;--j:{j}"></i></div>
        <span class="val">{fmt.pct(v)}</span></div>"""
        for j, (rot, v, serie) in enumerate(valores)
    )
    return html(
        f"""<div class="bloco-ind"><div class="topo"><h3>{escape(nome)}</h3>
        <span class="deltas">vs. estado <strong class="{_classe(delta_uf)}">{fmt.pp(delta_uf)}</strong>
        · vs. Brasil <strong class="{_classe(delta_br)}">{fmt.pp(delta_br)}</strong></span></div>
        {linhas}</div>"""
    )


def legenda_mapa(titulo: str, cores: list, limites: list) -> str:
    faixas = "".join(
        f'<div><i style="background:{c}"></i><span>{fmt.pct(v).removesuffix("%")}</span></div>'
        for c, v in zip(cores, limites, strict=True)
    )
    return html(
        f"""<div class="legenda-mapa"><span>{escape(titulo)} (%)</span>
        <div class="faixas">{faixas}</div></div>"""
    )


def aguardando(titulo: str, texto: str) -> None:
    mostrar(
        f"""<div class="aguardando">{RELOGIO}<div>
        <span class="rotulo"><i class="ponto-aguardando" aria-hidden="true"></i>Aguardando apuração</span>
        <strong>{escape(titulo)}</strong><span class="texto">{escape(texto)}</span></div></div>"""
    )


def nota(texto: str) -> None:
    mostrar(f'<div class="nota">{escape(texto)}</div>')


def esqueleto(linhas: int = 2):
    """Placeholder de carregamento; chamar .empty() quando os dados chegarem."""
    espaco = st.empty()
    espaco.markdown(html('<div class="esqueleto"></div>' * linhas), unsafe_allow_html=True)
    return espaco


def erro_leitura(exc: Exception) -> None:
    st.error(
        "Não foi possível carregar os dados agora. Tente novamente em instantes. "
        "Se o problema continuar, veja a página Contato."
    )
    st.caption(f"Detalhe técnico: {type(exc).__name__}")


def municipio_ou_parar():
    """Município escolhido; mostra o estado 'não encontrado' e interrompe a página se faltar."""
    linha = municipio_atual()
    if linha is None:
        st.warning("Município não encontrado. Use a busca acima para escolher outro.")
        rodape()
        st.stop()
    return linha
