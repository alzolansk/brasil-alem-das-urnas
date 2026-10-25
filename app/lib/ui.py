"""Layout base e componentes HTML (cartões, chips, barras, estados)."""

import base64
from html import escape
from pathlib import Path

import streamlit as st

from . import data, fmt

ASSETS = Path(__file__).resolve().parents[1] / "assets"
PAGINAS: dict = {}  # preenchido por Home.py: chave -> st.Page

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


def html(texto: str) -> str:
    """Junta as linhas: recuo de 4 espaços viraria bloco de código no markdown."""
    return "".join(linha.strip() for linha in texto.splitlines())


def mostrar(texto: str) -> None:
    st.markdown(html(texto), unsafe_allow_html=True)


def _ler(nome: str) -> str:
    return (ASSETS / nome).read_text(encoding="utf-8")


def injetar_css() -> None:
    css = _ler("style.css")
    if st.session_state.get("alto_contraste"):
        css += _ler("contraste.css")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


# --- município selecionado -------------------------------------------------------------


def _inicializar_municipio() -> None:
    if "cd_ibge" in st.session_state:
        return
    try:
        st.session_state["cd_ibge"] = int(st.query_params.get("m", data.IBGE_PADRAO))
    except (TypeError, ValueError):
        st.session_state["cd_ibge"] = data.IBGE_PADRAO


def seletor_municipio() -> None:
    _inicializar_municipio()
    with st.container(key="busca"):
        coluna_texto, coluna_lista = st.columns([3, 2])
        texto = coluna_texto.text_input(
            "Buscar município",
            key="busca_txt",
            placeholder="Digite o nome do município (com ou sem acento)",
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
                rotulo = coluna_lista.selectbox("Resultados", achados["rotulo"].tolist())
                par = (texto, rotulo)
                if st.session_state.get("busca_ultima") != par:
                    st.session_state["busca_ultima"] = par
                    linha = achados[achados["rotulo"] == rotulo].iloc[0]
                    st.session_state["cd_ibge"] = int(linha["cd_municipio_ibge"])
    st.query_params["m"] = str(st.session_state["cd_ibge"])


def municipio_atual():
    """Linha do município escolhido; None se o código não existir."""
    _inicializar_municipio()
    return data.municipio(st.session_state["cd_ibge"])


# --- layout base -------------------------------------------------------------------


@st.cache_data(show_spinner=False)
def _logo() -> str:
    return base64.b64encode((ASSETS / "logo.svg").read_bytes()).decode()


def cabecalho(ativa: str) -> None:
    injetar_css()
    mostrar('<div class="faixa"></div>')
    topo, contraste = st.columns([5, 1])
    with topo:
        if data.tem_dados(2026, 2):
            selo = '<span class="selo">Apuração concluída: 1º e 2º turnos 2026</span>'
        else:
            selo = '<span class="selo aviso">1º turno 2026 apurado · 2º turno em 25/10</span>'
        mostrar(
            f"""<div class="marca"><img src="data:image/svg+xml;base64,{_logo()}" alt="">
            <div><div class="titulo nome">Brasil Além das Urnas</div>
            <div class="sub">Participação eleitoral nos municípios · Presidente 2022 × 2026</div></div></div>
            {selo}"""
        )
    with contraste:
        st.toggle("Alto contraste", key="alto_contraste")
    seletor_municipio()
    _navegacao()
    mostrar(f'<div class="crumb">Início › {escape(TITULOS.get(ativa, ""))}</div>')


def _navegacao() -> None:
    with st.container(key="nav_desktop"):
        colunas = st.columns(len(ABAS))
        for coluna, (chave, titulo) in zip(colunas, ABAS, strict=True):
            coluna.page_link(PAGINAS[chave], label=titulo)
    with st.container(key="nav_mobile"), st.popover("☰ Menu", width="stretch"):
        for chave, titulo in ABAS:
            st.page_link(PAGINAS[chave], label=titulo)


def rodape() -> None:
    st.divider()
    colunas = st.columns(len(RODAPE))
    for coluna, (chave, titulo) in zip(colunas, RODAPE, strict=True):
        coluna.page_link(PAGINAS[chave], label=titulo)
    mostrar(
        f"""<div class="rodape"><b>Fonte:</b> Portal de Dados Abertos do TSE e IBGE ·
        dados atualizados em {data.ultima_atualizacao()}.<br>
        Ferramenta independente, sem vínculo com órgãos públicos ou partidos.</div>"""
    )


# --- componentes -------------------------------------------------------------------------


def chip(serie: str, rotulo: str, delta_pp) -> str:
    """Chip com a cor da série (mun/uf/br) e a variação com seta e sinal."""
    if delta_pp is None or delta_pp != delta_pp:
        classe, seta, texto = "flat", "", "sem base"
    else:
        classe = "up" if delta_pp > 0 else "down" if delta_pp < 0 else "flat"
        seta, texto = fmt.seta(delta_pp), fmt.pp(delta_pp)
    return (
        f'<span class="chip"><span class="pt serie-{serie}"></span>{escape(rotulo)} '
        f'<span class="{classe}">{seta} {escape(texto)}</span></span>'
    )


def cartao_indicador(titulo, info, valor, frase, chips) -> str:
    return html(
        f"""<div class="cartao"><h3>{escape(titulo)}</h3><div class="info">{escape(info)}</div>
        <div class="destaque">{escape(valor)}</div><div class="frase">{escape(frase)}</div>
        <div class="chips">{"".join(chips)}</div></div>"""
    )


def cartao_leitura(itens) -> str:
    lista = "".join(f"<li><span>{escape(i)}</span></li>" for i in itens)
    return html(f'<div class="escuro"><h3>Leitura rápida</h3><ol>{lista}</ol></div>')


def barra_empilhada(validos, brancos, nulos) -> str:
    partes = [
        ("Válidos", validos, "var(--green)"),
        ("Brancos", brancos, "var(--gray)"),
        ("Nulos", nulos, "var(--orange)"),
    ]
    segmentos = "".join(
        f'<span style="width:{max(v, 0.3)}%;background:{cor}" title="{n}: {fmt.pct(v)}">'
        f'{fmt.pct(v) if v >= 6 else ""}</span>'
        for n, v, cor in partes
    )
    legenda = "".join(
        f'<span><i style="background:{cor}"></i>{n}: {fmt.pct(v)}</span>' for n, v, cor in partes
    )
    return html(
        f"""<div class="barra" role="img" aria-label="Válidos {fmt.pct(validos)}, brancos
        {fmt.pct(brancos)}, nulos {fmt.pct(nulos)}">{segmentos}</div>
        <div class="legenda">{legenda}</div>"""
    )


def barra_diferenca(delta_pp, maximo: float) -> str:
    """Barra centrada no zero: azul para a direita (aumentou), laranja para a esquerda."""
    if delta_pp is None or delta_pp != delta_pp:
        return ""
    largura = min(abs(delta_pp) / maximo, 1) * 50 if maximo else 0
    classe = "up" if delta_pp > 0 else "down"
    return f'<div class="dif"><b class="{classe}" style="width:{largura:.1f}%"></b></div>'


def aguardando(mensagem: str = "O resultado ainda não foi publicado pelo TSE.") -> None:
    mostrar(f'<div class="aguardando"><b>Aguardando apuração</b>{escape(mensagem)}</div>')


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
