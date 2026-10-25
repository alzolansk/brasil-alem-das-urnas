"""Fumaça do app com AppTest (sem GCP): cada tela abre, sem exceção, nos estados principais."""

import pytest
from streamlit.testing.v1 import AppTest

from app.lib import data, fmt, narrativa

SAO_PAULO, LAGOA_DO_PIAUI = 3550308, 2205508


def abrir(pagina="explore", municipio=SAO_PAULO):
    def roteiro(pagina, municipio):
        import sys
        from pathlib import Path

        import streamlit as st

        sys.path.insert(0, str(Path("app").resolve()))
        import navegacao

        st.session_state.setdefault("cd_ibge", municipio)
        navegacao.executar(pagina)

    return AppTest.from_function(
        roteiro, kwargs={"pagina": pagina, "municipio": municipio}, default_timeout=60
    ).run()


TELAS = ["explore", "comparativo", "mapa", "brasil", "metodologia", "dicionario", "dados",
         "acessibilidade", "termos", "contato"]


@pytest.mark.parametrize("pagina", TELAS)
def test_tela_abre_sem_excecao(pagina):
    at = abrir(pagina)
    assert not at.exception, [e.value for e in at.exception]


def test_municipio_inexistente_mostra_aviso():
    at = abrir("explore", municipio=1)
    assert not at.exception
    assert any("não encontrado" in w.value for w in at.warning)


def test_busca_sem_acento_e_sem_maiuscula():
    achados = data.buscar("SAO JOAO DEL")
    assert not achados.empty
    assert all("João" in r or "Joao" in r for r in achados["rotulo"].head(2))
    assert not data.buscar("sao paulo").empty


def test_busca_sem_resultado_sugere_parecidos():
    assert data.buscar("zzzzqq").empty
    assert data.parecidos("Sao Paulu")


def test_segundo_turno_2026_aguardando():
    at = abrir("explore")
    at.radio(key="explore_eleicao").set_value((2026, 2)).run()
    assert not at.exception
    assert any("Aguardando apuração" in m.value for m in at.markdown)


def test_mapa_municipios_e_lista():
    at = abrir("mapa")
    at.radio(key="mapa_nivel").set_value("Municípios").run()
    assert not at.exception
    at.radio(key="mapa_visao").set_value("Lista ordenada").run()
    assert not at.exception


def test_municipio_de_uma_zona_so_mostra_nota():
    base = data.carregar("mart_municipio_indicadores")
    uma = base[(base["n_zonas"] == 1) & ~base["exterior"].astype(bool) & (base["ano"] == 2026)]
    cd = int(uma.iloc[0]["cd_municipio_ibge"])
    at = abrir("explore", municipio=cd)
    assert not at.exception
    assert any("única zona eleitoral" in m.value for m in at.markdown)


def test_formatacao_brasileira():
    assert fmt.pct(79.44) == "79,4%"
    assert fmt.inteiro(863412) == "863.412"
    assert fmt.pp(0.94) == "+0,9 p.p."
    assert fmt.pp(-0.94) == "−0,9 p.p."
    assert fmt.milhoes(34_812_345) == "34,8 milhões"


@pytest.mark.parametrize(
    ("delta", "classe"), [(0.9, "alta"), (-1.2, "queda"), (0.49, "igual"), (-0.49, "igual"),
                          (0.5, "alta"), (None, "igual")]
)
def test_classificacao_com_limite_de_meio_ponto(delta, classe):
    assert narrativa.classificar(delta) == classe


def test_modelos_de_frase_cobrem_alta_queda_e_igual():
    assert narrativa.comparar("O comparecimento", 2.1, "uf") == (
        "O comparecimento está 2,1 p.p. acima da média do estado"
    )
    assert narrativa.comparar("O comparecimento", -2.1, "br") == (
        "O comparecimento está 2,1 p.p. abaixo da média do Brasil"
    )
    assert "praticamente igual à média do estado" in narrativa.comparar("X", 0.1, "uf")
    assert narrativa.evolucao("O comparecimento", 0.9) == "O comparecimento subiu 0,9 p.p. desde 2022"
    assert narrativa.evolucao("O comparecimento", -0.9) == "O comparecimento caiu 0,9 p.p. desde 2022"
    assert "praticamente igual" in narrativa.evolucao("O comparecimento", 0.2)
    assert narrativa.em_quatro_anos(0.9) == "Em quatro anos, o comparecimento subiu 0,9 p.p."
    assert narrativa.em_quatro_anos(0.0).endswith("praticamente igual.")


def test_leitura_rapida_tem_tres_itens_com_ou_sem_2022():
    assert len(narrativa.leitura_rapida(1.0, -1.0, 0.8, 4.0, 0.2)) == 3
    assert len(narrativa.leitura_rapida(1.0, -1.0, None, 4.0, 0.2)) == 3
