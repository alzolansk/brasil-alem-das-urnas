"""Brasil Além das Urnas: ponto de entrada. Rodar com `streamlit run app/Home.py`."""

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))

import navegacao  # noqa: E402

st.set_page_config(
    page_title="Brasil Além das Urnas",
    page_icon=str(Path(__file__).resolve().parent / "assets" / "logo.svg"),
    layout="wide",
    initial_sidebar_state="collapsed",
)
navegacao.executar()
