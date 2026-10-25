"""Layout base e componentes HTML do protótipo (docs/design/especificacao-fidelidade-prototipo.md)."""

import base64
from datetime import date
from html import escape
from pathlib import Path

import streamlit as st

from . import data, fmt, perfil
from .loader import loader_html

ASSETS = Path(__file__).resolve().parents[1] / "assets"
PAGINAS: dict = {}  # preenchido por navegacao.py: chave -> st.Page

ABAS = [
    ("explore", "Explore seu município"),
    ("comparativo", "Comparativo 2022 × 2026"),
    ("abstencao", "Quem ficou em casa?"),
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
    "abstencao": (
        "Quem ficou em casa?",
        "Descubra como a abstenção eleitoral se distribuiu entre diferentes grupos de eleitores "
        "da sua cidade.",
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


ORDEM = [chave for chave, _ in ABAS + RODAPE]


def direcao(anterior: str | None, atual: str) -> int:
    """Lado de entrada da página nova, pela ordem das abas (rodapé depois delas):
    1 = entra pela direita (ela fica à direita da anterior), -1 = pela esquerda, 0 = sem transição."""
    if anterior not in ORDEM or atual not in ORDEM or anterior == atual:
        return 0
    return 1 if ORDEM.index(atual) > ORDEM.index(anterior) else -1


def _css_transicao(sentido: int) -> str:
    """Tudo abaixo do cabeçalho (menos o rodapé) desliza para dentro, vindo do lado `sentido`.

    Só os blocos já desta execução (`data-stale` diferente de "true") recebem a animação: cada
    um começa a deslizar quando o conteúdo novo chega, e a página antiga, ainda na tela até ser
    substituída, fica parada. Os contêineres com chave ficam dentro de um stLayoutWrapper."""
    if not sentido:
        return ""
    topo = '[data-testid="stLayoutWrapper"]:has(> .st-key-topo)'
    novo = '[data-testid="stElementContainer"]:not([data-stale="true"])'
    alvos = (f"{topo} ~ {novo}, "
             f'{topo} ~ [data-testid="stLayoutWrapper"]:not(:has(> .st-key-rodape)) {novo}')
    nome = "entrar-direita" if sentido > 0 else "entrar-esquerda"
    return ("@media (prefers-reduced-motion: no-preference) { "
            f"{alvos} {{ animation: {nome} 420ms cubic-bezier(.2,.7,.2,1) both; }} }}")


def injetar_css(ativa: str, sentido: int = 0) -> None:
    css = _ler("style.css") + _css_aba_ativa(ativa)
    if st.session_state.get("alto_contraste"):
        css += _ler("contraste.css")
    else:  # no alto contraste as animações ficam desligadas
        css += _css_transicao(sentido)
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


def indice_eleicao() -> int:
    """Posição em data.ELEICOES da última eleição escolhida em qualquer tela (filtro compartilhado).

    O Streamlit apaga o estado dos widgets de outra página; esta chave comum o leva de uma tela à outra."""
    escolhida = st.session_state.get("_eleicao")
    return data.ELEICOES.index(escolhida) if escolhida in data.ELEICOES else 0


def lembrar_eleicao(ano: int, turno: int) -> None:
    st.session_state["_eleicao"] = (ano, turno)


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


DATA_2T_2026 = date(2026, 10, 25)


def segundo_turno_pendente() -> str:
    """Texto do selo enquanto o 2º turno de 2026 não está nas marts."""
    if date.today() <= DATA_2T_2026:
        return "2º turno em 25/10"
    return "2º turno em totalização"


def _selo() -> str:
    if data.tem_dados(2026, 2):
        return etiqueta("Apuração concluída: 1º e 2º turnos 2026", "ok")
    return etiqueta(f"1º turno 2026 apurado · {segundo_turno_pendente()}", "aviso")


def cabecalho(ativa: str) -> None:
    _inicializar_estado()
    anterior = st.session_state.get("_pagina")
    st.session_state["_pagina"] = ativa
    injetar_css(ativa, direcao(anterior, ativa))
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
                key="util_links", horizontal=True, gap="medium", vertical_alignment="center",
                width="content",
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


def cartao_leitura(itens, link: tuple | None = None, anima: str = "", i: int = 0,
                   rotulo: str = "Leitura rápida", visiveis: int | None = None) -> str:
    """link: (texto, href) opcional no rodapé do cartão. Com `visiveis`, os itens seguintes ficam
    num <details> "Ver mais" (numeração contínua, abre pelo teclado sem JavaScript)."""

    def _itens(trecho, inicio):
        return "".join(
            f'<li><b aria-hidden="true">{n}</b><span>{escape(item)}</span></li>'
            for n, item in enumerate(trecho, start=inicio)
        )

    corte = len(itens) if visiveis is None else visiveis
    corpo = f"<ol>{_itens(itens[:corte], 1)}</ol>"
    if len(itens) > corte:
        corpo += (f'<details class="mais"><summary><span class="ver-mais">Ver mais '
                  f'({len(itens) - corte})</span><span class="ver-menos">Ver menos</span></summary>'
                  f'<ol start="{corte + 1}">{_itens(itens[corte:], corte + 1)}</ol></details>')
    rodape_link = (
        f'<a class="link-claro" href="{escape(link[1])}" target="_self">{escape(link[0])} '
        '<span aria-hidden="true">→</span></a>'
        if link
        else ""
    )
    return html(
        f"""<aside class="escuro{anima}" style="--i:{i}"><span class="rotulo">{escape(rotulo)}</span>
        {corpo}{rodape_link}</aside>"""
    )


def grade_herois(heroi1: str, heroi2: str, leitura: str) -> str:
    return f'<div class="grade-herois">{heroi1}{heroi2}{leitura}</div>'


# Sua cidade em 100 eleitores (seção 12): classe CSS e descrição de cada grupo
GRUPOS_100 = [("val", "Votaram em um candidato"), ("bra", "Votaram em branco"),
              ("nul", "Votaram nulo"), ("abs", "Não compareceram")]
TEXTO_2T_PENDENTE = ("O 2º turno de 2026 ainda está em apuração. Os pontos aparecem aqui assim que a "
                     "totalização oficial for publicada. Enquanto isso, veja 2022.")


def cabecalho_100() -> str:
    return ('<div class="e100-cab"><span class="e100-rotulo">Participação</span>'
            "<h3>Sua cidade em 100 eleitores</h3></div>")


def exibindo_100(ano: int, turno: int) -> str:
    return f'<p class="e100-exibindo">Exibindo <b>{ano} · {turno}º turno</b></p>'


def _grade_100(pontos) -> str:
    if pontos is None:
        return '<i class="e100-pt"></i>' * 100
    classes = [g for (g, _), n in zip(GRUPOS_100, pontos, strict=True) for _ in range(n)]
    return "".join(f'<i class="e100-pt e100-{g}" style="--i:{i}"></i>' for i, g in enumerate(classes))


def bloco_100(ind, pontos, ano: int, turno: int, resumo: str) -> str:
    """Grade de 100 pontos (aria-hidden) e corpo com texto, legenda, nota e detalhe.
    `ind` None = estado indisponível (sem estimar nada)."""
    sr = f'<p class="e100-sr" aria-live="polite">{escape(resumo)}</p>'
    if ind is None:
        texto = (TEXTO_2T_PENDENTE if (ano, turno) == (2026, 2)
                 else "Não há dados desta eleição para o município.")
        return html(
            f"""<div class="e100">{sr}<div class="e100-grade sem" aria-hidden="true">{_grade_100(None)}
            <span class="e100-sem">Sem dados para {ano}</span></div>
            <div class="e100-corpo"><div class="e100-indisp" role="status">
            <strong>Dados de {ano}, {turno}º turno, indisponíveis</strong><span>{texto}</span></div>
            </div></div>"""
        )
    aptos, comparecimento = int(ind["aptos"]), int(ind["comparecimento"])
    contagens = data.contagens_100(ind)
    legenda = "".join(
        f"""<li><i class="e100-bola e100-{g}"></i><span>{nome}</span>
        <span class="n">{n} de 100</span><b>{fmt.pct(100 * c / aptos)}</b></li>"""
        for (g, nome), n, c in zip(GRUPOS_100, pontos, contagens, strict=True)
    )
    votos = [("Em um candidato (válidos)", contagens[0]), ("Em branco", contagens[1]),
             ("Nulo", contagens[2])]
    linhas = "".join(
        f'<tr><th scope="row">{v}</th><td>{fmt.inteiro(c)}</td>'
        f"<td>{fmt.pct(100 * c / comparecimento if comparecimento else None)}</td></tr>"
        for v, c in votos
    )
    return html(
        f"""<div class="e100">{sr}<div class="e100-grade" aria-hidden="true">{_grade_100(pontos)}</div>
        <div class="e100-corpo"><p class="e100-intro">Se o eleitorado da sua cidade fosse um grupo
        de 100 pessoas, a participação seria assim.</p><ul class="e100-legenda">{legenda}</ul>
        <p class="e100-nota">Percentuais sobre os {fmt.inteiro(aptos)} eleitores aptos. Pontos
        arredondados para somar 100; percentuais exibidos com uma casa decimal.</p>
        <details class="e100-det"><summary>Ver distribuição entre quem votou</summary>
        <p>Base: {fmt.inteiro(comparecimento)} eleitores que compareceram em {ano}, {turno}º turno.
        A abstenção fica de fora desta conta.</p>
        <table><thead><tr><th scope="col">Voto</th><th scope="col">Eleitores</th>
        <th scope="col">% de quem votou</th></tr></thead><tbody>{linhas}</tbody>
        <tfoot><tr><th scope="row">Total de quem votou</th><td>{fmt.inteiro(comparecimento)}</td>
        <td>100,0%</td></tr></tfoot></table></details></div></div>"""
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


# O total "Brasil" das marts soma o exterior, como o total oficial do TSE.
BRASIL_EXTERIOR = "Brasil + Exterior"


def barras_grupos(linhas, media: float, maior=None, menor=None, anima: str = "") -> str:
    """Barras horizontais de abstenção por grupo, na escala de 0 a 100%.

    linhas: DataFrame de perfil.grupos(); maior/menor: códigos de categoria destacados.
    A linha tracejada em cada trilho marca a média do município (`media`, em %)."""
    itens = []
    for j, (_, g) in enumerate(linhas.iterrows()):
        cd = int(g["cd_categoria"])
        classes = "grupo" + (" facultativo" if g["voto_facultativo"] else "") + (
            " pequena" if g["base_pequena"] else "")
        marca = "Maior taxa" if cd == maior else "Menor taxa" if cd == menor else ""
        tag = f'<span class="tag-grupo">{marca}</span>' if marca else ""
        itens.append(
            f"""<li class="{classes}"><div class="rot"><span class="nome">{escape(g["categoria"])}{tag}</span>
            <span class="n">{fmt.inteiro(g["abstencoes"])} de {fmt.inteiro(g["aptos"])} eleitores</span></div>
            <div class="barra-g" aria-hidden="true"><i style="width:{g["abstencao_pct"]:.1f}%;--j:{j}"></i></div>
            <span class="val">{fmt.pct(g["abstencao_pct"])}{"*" if g["base_pequena"] else ""}</span></li>"""
        )
    return html(f'<ul class="grupos{anima}" style="--media:{media:.2f}%">{"".join(itens)}</ul>')


def legenda_grupos(media: float, cores: tuple[str, str] | None = None, pequena: bool = False) -> str:
    """cores: (rótulo da barra escura, rótulo da barra clara = grupos com voto facultativo)."""
    itens = []
    if cores:
        itens += [f'<span><i class="quadrado" style="background:var(--blue)"></i>{escape(cores[0])}</span>',
                  f'<span><i class="quadrado" style="background:var(--blue-2t)"></i>{escape(cores[1])}</span>']
    itens.append(f'<span><i class="traco-media"></i>Média do município, todos os eleitores ({fmt.pct(media)})</span>')
    if pequena:
        itens.append(f"<span>* menos de {perfil.BASE_MINIMA} eleitores aptos: percentual instável</span>")
    return f'<div class="legenda-linha legenda-grupos">{"".join(itens)}</div>'



def tabela_grupos(linhas, total) -> str:
    """Alternativa em tabela (dentro de <details>) com os números absolutos de cada grupo."""
    corpo = "".join(
        f'<tr><th scope="row">{escape(g["categoria"])}</th><td>{fmt.inteiro(g["aptos"])}</td>'
        f'<td>{fmt.inteiro(g["comparecimento"])}</td><td>{fmt.inteiro(g["abstencoes"])}</td>'
        f'<td>{fmt.pct(g["abstencao_pct"])}</td></tr>'
        for _, g in linhas.iterrows()
    )
    return html(
        f"""<details class="e100-det"><summary>Ver como tabela</summary><table><thead><tr>
        <th scope="col">Grupo</th><th scope="col">Aptos</th><th scope="col">Compareceram</th>
        <th scope="col">Não compareceram</th><th scope="col">Abstenção</th></tr></thead>
        <tbody>{corpo}</tbody><tfoot><tr><th scope="row">Todos os eleitores</th>
        <td>{fmt.inteiro(total["aptos"])}</td><td>{fmt.inteiro(total["comparecimento"])}</td>
        <td>{fmt.inteiro(total["abstencoes"])}</td><td>{fmt.pct(total["abstencao_pct"])}</td></tr>
        </tfoot></table></details>"""
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


def cartao_escopo(tipo, nome, aptos, serie, anima: str = "", i: int = 0, info: str = "") -> str:
    aptos_txt = fmt.mil(aptos)
    selo = etiqueta(info, "neutra") if info else ""
    return html(
        f"""<article class="escopo serie-{serie}{anima}" style="--i:{i}">
        <span class="rotulo-cinza">{escape(tipo)}</span><h2>{escape(nome)}</h2>{selo}
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


def carregando():
    """Loader de tela cheia; chamar .empty() quando os dados chegarem."""
    espaco = st.empty()
    espaco.markdown(loader_html(), unsafe_allow_html=True)
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
