"""Loader (seção 11 da especificação; referência em docs/design/loader/). Mesmo contorno da logo.

Não importa pandas nem os dados: o Home.py usa este módulo antes de carregar o resto do app.
"""

from html import escape

CONTORNO_BR = (
    "M33.9 0.3 L45.9 8.7 L57.1 2.3 L61.2 13.6 L65 16.7 L75.8 20 L90.6 23.1 L99 28.5 L99.7 34.1 "
    "L90.6 46.9 L89.3 51.5 L88.8 59 L86 65.6 L81.6 72.6 L70.7 75.1 L65 84.1 L55.9 95.9 L52.6 100 "
    "L47.2 93.1 L41.8 91 L51.5 83.3 L49.5 79.2 L46.2 70.8 L40.6 65.1 L39.8 55.4 L35.5 48.2 "
    "L22.2 41.5 L11.2 41.8 L1.3 37.7 L2.6 32.3 L10.2 24.4 L11.7 16.2 L10.7 9.2 L17.9 10.5 L25.5 3.3 Z"
)
CAPITAIS = [(36.8, 23.6), (63.9, 19.6), (86.1, 25.9), (92.6, 35.2), (46.0, 53.3), (65.4, 53.8),
            (68.4, 72.0), (57.6, 87.5)]
MENSAGENS_LOADER = ["Contando eleitores de todos os municípios…", "Comparando 2022 com 2026…",
                    "Pintando o mapa do Brasil…"]


def _juntar(texto: str) -> str:
    """Como ui.html: recuo de 4 espaços viraria bloco de código no markdown."""
    return " ".join(linha.strip() for linha in texto.splitlines() if linha.strip())


def _mapa_loader(tam: int, gid: str, contorno: str, capitais: bool) -> str:
    """Brasil em verde, amarelo e azul que se pinta na diagonal, com o contorno por cima."""
    grad = (f'<defs><linearGradient id="{gid}" x1="0" y1="0" x2="1" y2="1">'
            '<stop offset="0" stop-color="#12753E"/><stop offset=".47" stop-color="#12753E"/>'
            '<stop offset=".47" stop-color="#F5C400"/><stop offset=".59" stop-color="#F5C400"/>'
            '<stop offset=".59" stop-color="#0B4EA2"/><stop offset="1" stop-color="#0B4EA2"/>'
            "</linearGradient></defs>")
    cheio = (f'<div class="bau-cheio"><svg viewBox="-4 -4 108 108" aria-hidden="true">{grad}'
             f'<path d="{CONTORNO_BR}" fill="url(#{gid})" stroke="url(#{gid})" stroke-width="3" '
             'stroke-linejoin="round"/></svg></div>')
    linha = (f'<svg viewBox="-4 -4 108 108" aria-hidden="true"><path{contorno} d="{CONTORNO_BR}" '
             'fill="none" stroke-linejoin="round"/></svg>')
    pontos = "".join(
        f'<span class="bau-ponto" style="left:{x}%;top:{y}%;--d:{d}"></span>'
        for d, (x, y) in enumerate(CAPITAIS)
    ) if capitais else ""
    return f'<div class="bau-mapa" style="--tam:{tam}px">{cheio}{linha}{pontos}</div>'


def loader_html(gid: str = "bau-ld") -> str:
    mapa = _mapa_loader(240, gid, ' class="bau-contorno" pathLength="1" stroke="#071D41" '
                        'stroke-width="1.6"', capitais=True)
    msgs = "".join(f"<span>{m}</span>" for m in MENSAGENS_LOADER)
    return _juntar(
        f"""<div class="bau-loader" role="status" aria-live="polite">
        <span class="bau-sr">Carregando dados eleitorais</span>
        <div class="bau-corpo"><div class="bau-flutua">{mapa}</div>
        <div class="bau-sombra" aria-hidden="true"></div></div>
        <span class="bau-nome">Brasil Além das Urnas</span>
        <div class="bau-msgs" aria-hidden="true">{msgs}</div>
        <div class="bau-trilho" aria-hidden="true"><i></i></div></div>"""
    )


def loader_compacto_html(titulo: str, texto: str, escuro: bool = False,
                         gid: str = "bau-ld-mini") -> str:
    mapa = _mapa_loader(48, gid, ' stroke="#C9D3E3" stroke-width="4"', capitais=False)
    classe = "bau-compacto escuro" if escuro else "bau-compacto"
    return _juntar(
        f"""<div class="{classe}" role="status" aria-live="polite">{mapa}
        <div><strong>{escape(titulo)}</strong><span>{escape(texto)}</span></div></div>"""
    )


def sobreposicao_html(contraste: bool = False) -> str:
    """Loader do 1º acesso: visível por no mínimo 1,5 s desde a montagem no navegador.

    O CSS só o oculta após esse mínimo e a chegada do rodapé (ou de um erro).
    Navegação interna não o recria; uma nova abertura/recarregamento reinicia o ciclo.
    """
    classe = "bau-sobre contraste" if contraste else "bau-sobre"
    return f'<div class="{classe}">{loader_html("bau-ld-sobre")}</div>'


def loader_grafico(titulo: str, texto: str) -> str:
    """Loader por cima da área de um gráfico Plotly; o CSS o esconde quando o gráfico desta
    execução já foi desenhado no navegador (o desenho acontece depois que o Python termina)."""
    return f'<div class="bau-grafico">{loader_compacto_html(titulo, texto, gid="bau-ld-graf")}</div>'
