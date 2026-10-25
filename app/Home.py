"""Brasil Além das Urnas: ponto de entrada. Rodar com `streamlit run app/Home.py`."""

import sys
from pathlib import Path

import streamlit as st

APP = Path(__file__).resolve().parent
sys.path.insert(0, str(APP))

from lib import loader  # noqa: E402 - leve, sem pandas: vem antes do resto do app

st.set_page_config(
    page_title="Brasil Além das Urnas",
    page_icon=str(APP / "assets" / "logo.svg"),
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Loader do 1º acesso da sessão: vai para a tela antes de importar as telas (pandas, Plotly) e de
# ler os dados. O CSS garante 1,5 s desde a montagem no navegador e espera o rodapé;
# um sleep em Python não mediria o tempo realmente visível. Os dois blocos existem em
# toda execução para não mudar a posição dos elementos entre uma execução e outra.
st.markdown(
    f"<style>{(APP / 'assets' / 'loader.css').read_text(encoding='utf-8')}</style>",
    unsafe_allow_html=True,
)
sobreposicao = st.empty()
if not st.session_state.get("_abriu"):
    st.session_state["_abriu"] = True
    contraste = st.session_state.get("alto_contraste", st.query_params.get("c") == "1")
    sobreposicao.markdown(loader.sobreposicao_html(contraste), unsafe_allow_html=True)

import navegacao  # noqa: E402

navegacao.executar()
