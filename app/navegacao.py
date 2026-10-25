"""Registro das páginas. Separado do Home.py para os testes escolherem a página inicial."""

import streamlit as st
from lib import ui
from telas import brasil, comparativo, explore, mapa, textos

TELAS = {
    "explore": ("Explore seu município", explore.render),
    "comparativo": ("Comparativo 2022 × 2026", comparativo.render),
    "mapa": ("Mapa eleitoral", mapa.render),
    "brasil": ("Brasil em perspectiva", brasil.render),
}


def executar(padrao: str = "explore") -> None:
    paginas = {
        chave: st.Page(funcao, title=titulo, url_path=chave, default=chave == padrao)
        for chave, (titulo, funcao) in TELAS.items()
    }
    for chave, titulo in ui.RODAPE:
        paginas[chave] = st.Page(
            textos.pagina(chave), title=titulo, url_path=chave, default=chave == padrao
        )
    ui.PAGINAS.update(paginas)
    st.navigation(list(paginas.values()), position="hidden").run()
