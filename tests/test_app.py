"""Fumaça do app com AppTest (sem GCP): cada tela abre, sem exceção, nos estados principais."""

from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from app.lib import charts, data, fmt, narrativa

SAO_PAULO, LAGOA_DO_PIAUI = 3550308, 2205508


def abrir(pagina="explore", municipio=SAO_PAULO, marts=None, estado=None):
    def roteiro(pagina, municipio, marts, estado):
        import sys
        from pathlib import Path

        import streamlit as st

        sys.path.insert(0, str(Path("app").resolve()))
        import navegacao
        from lib import data as d

        alvo = Path(marts) if marts else d.RAIZ / "data" / "marts"
        if d.MARTS != alvo:  # o módulo e o cache sobrevivem entre os testes
            d.MARTS = alvo
            st.cache_data.clear()
        st.session_state.setdefault("cd_ibge", municipio)
        for chave, valor in (estado or {}).items():
            st.session_state.setdefault(chave, valor)
        navegacao.executar(pagina)

    return AppTest.from_function(
        roteiro, kwargs={"pagina": pagina, "municipio": municipio, "marts": marts, "estado": estado},
        default_timeout=60,
    ).run()


SEGUNDO_TURNO_2026 = data.tem_dados(2026, 2)
sem_2t_2026 = pytest.mark.skipif(SEGUNDO_TURNO_2026, reason="2º turno de 2026 já carregado")


@pytest.fixture(scope="module")
def marts_com_2t(tmp_path_factory):
    """Cópia das marts com um 2º turno 2026 simulado (= 1º turno), para testar a carga futura."""
    destino = tmp_path_factory.mktemp("marts")
    for nome in ("mart_zona_indicadores", "mart_municipio_indicadores",
                 "mart_uf_brasil_indicadores", "mart_municipio_benchmark"):
        df = pd.read_parquet(data.MARTS / f"{nome}.parquet")
        df = df[~((df["ano"] == 2026) & (df["turno"] == 2))]
        t2 = df[(df["ano"] == 2026) & (df["turno"] == 1)].assign(turno=2)
        pd.concat([df, t2], ignore_index=True).to_parquet(destino / f"{nome}.parquet")
    c = pd.read_parquet(data.MARTS / "mart_municipio_comparativo.parquet")
    chave = ["sg_uf", "cd_municipio_tse"]
    for tipo, ano_base, turno_base in (("turnos", 2026, 1), ("anos", 2022, 2)):
        alvo = (c["tipo_comparacao"] == tipo) & (c["ano_base"] == ano_base) & (c["turno_base"] == turno_base)
        if tipo == "turnos":  # 2º turno 2026 igual ao 1º
            fonte = c[alvo].set_index(chave)[[f"{k}_pct_base" for k in data.INDICADORES] + ["aptos_base"]]
        else:  # 2026 T2 = 2026 T1, que é a comparação do par anos/turno 1
            base = (c["tipo_comparacao"] == "anos") & (c["turno_base"] == 1)
            fonte = c[base].set_index(chave)[[f"{k}_pct_comparacao" for k in data.INDICADORES] + ["aptos_comparacao"]]
        fonte.columns = [f"{k}_pct_comparacao" for k in data.INDICADORES] + ["aptos_comparacao"]
        linhas = c[alvo].set_index(chave)
        linhas.update(fonte)
        for k in data.INDICADORES:
            linhas[f"{k}_delta_pp"] = linhas[f"{k}_pct_comparacao"] - linhas[f"{k}_pct_base"]
        linhas["aptos_variacao_pct"] = 100 * (linhas["aptos_comparacao"] - linhas["aptos_base"]) / linhas["aptos_base"]
        linhas["status_comparacao"] = "disponivel"
        c = pd.concat([c[~alvo], linhas.reset_index()[c.columns]], ignore_index=True)
    c.to_parquet(destino / "mart_municipio_comparativo.parquet")
    return str(destino)


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


@sem_2t_2026
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
    assert fmt.mil(873_613) == "874 mil"
    assert fmt.mil(999) == "999"
    assert fmt.mil(34_812_345) == "34,8 milhões"
    assert fmt.milhar_curto(7_812) == "7,8 mil"
    assert fmt.milhar_curto(31_600) == "31,6 mil"
    assert fmt.milhar_curto(850) == "850"


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


def test_virada_em_relacao_ao_brasil_na_leitura_rapida():
    itens = narrativa.leitura_rapida(1.0, 0.8, 0.9, 4.0, 0.2, comp_delta_br_2022=-0.7, nome="X")
    assert itens[1] == "Em 2022, X votava menos que a média do país. Em 2026, passou à frente."
    itens = narrativa.leitura_rapida(1.0, -0.8, 0.9, 4.0, 0.2, comp_delta_br_2022=0.7, nome="X")
    assert itens[1].endswith("Em 2026, ficou para trás.")
    sem_virada = narrativa.leitura_rapida(1.0, 0.8, 0.9, 4.0, 0.2, comp_delta_br_2022=0.7, nome="X")
    assert sem_virada[1] == "O comparecimento subiu 0,9 p.p. desde 2022."


@pytest.mark.parametrize(
    ("delta_br", "delta_uf", "antes", "depois"),
    [
        (1.0, -1.0, "X foi mais às urnas do que o Brasil:", ", e a abstenção ficou abaixo da média do estado."),
        (-1.0, 1.0, "X foi menos às urnas do que o Brasil:", ", e a abstenção ficou acima da média do estado."),
        (0.1, 0.1, "X votou na mesma proporção que o Brasil:", ", e a abstenção ficou na média do estado."),
    ],
)
def test_manchete_explore(delta_br, delta_uf, antes, depois):
    partes = narrativa.manchete_explore("X", 78.2, delta_br, delta_uf)
    assert partes == {"antes": antes, "destaque": "8 em cada 10 eleitores votaram", "depois": depois}


@pytest.mark.parametrize(
    ("aptos", "comp", "bn", "esperado"),
    [
        ((880_000, 872_200), -1.7, 0.1,
         "X perdeu 7,8 mil eleitores e [ficou menos participativa]: o comparecimento caiu 1,7 p.p. "
         "e brancos e nulos ficaram praticamente iguais."),
        ((800_000, 831_600), 0.9, -1.2,
         "X ganhou 31,6 mil eleitores e [ficou mais participativa]: o comparecimento subiu 0,9 p.p. "
         "e brancos e nulos caíram 1,2 p.p."),
        ((1000, 1000), 0.2, 0.6,
         "X manteve o número de eleitores e [manteve o nível de participação]: o comparecimento "
         "ficou praticamente igual e brancos e nulos subiram 0,6 p.p."),
    ],
)
def test_manchete_comparativo(aptos, comp, bn, esperado):
    p = narrativa.manchete_comparativo("X", *aptos, comp, bn)
    assert f"{p['antes']} [{p['destaque']}]{p['depois']}" == esperado


@pytest.mark.parametrize(
    ("comp", "bn", "esperado"),
    [
        (-0.6, -3.4, "Em 2022, o comparecimento caiu 0,6 p.p. do 1º para o 2º turno, e brancos e nulos recuaram 3,4 p.p."),
        (0.8, 1.1, "Em 2022, o comparecimento subiu 0,8 p.p. do 1º para o 2º turno, e brancos e nulos aumentaram 1,1 p.p."),
        (0.1, -0.2, "Em 2022, o comparecimento ficou praticamente igual do 1º para o 2º turno, e brancos e nulos ficaram praticamente iguais."),
    ],
)
def test_entre_turnos(comp, bn, esperado):
    assert narrativa.entre_turnos(2022, comp, bn) == esperado


@pytest.mark.parametrize(
    ("pontos", "esperado"),
    [([73, 2, 4, 21], "73 votaram em um candidato, 2 votaram em branco, 4 votaram nulo e 21 não compareceram."),
     ([78, 1, 1, 20], "78 votaram em um candidato, 1 votou em branco, 1 votou nulo e 20 não compareceram."),
     ([80, 0, 3, 17], "80 votaram em um candidato, nenhum votou em branco, 3 votaram nulo e 17 não compareceram.")],
)
def test_resumo_100_plural_singular_e_zero(pontos, esperado):
    texto = narrativa.resumo_100("Campinas", 2026, 1, pontos)
    assert texto == f"Exibindo 2026, 1º turno. De cada 100 eleitores aptos de Campinas, {esperado}"
    assert narrativa.resumo_100("X", 2022, 1, None).endswith("Não há dados desta eleição para X.")


def test_pontos_100_exemplo_e_empate():
    assert data.pontos_100([631391, 17824, 36334, 177863], 863412) == [73, 2, 4, 21]
    assert data.pontos_100([1, 1, 1], 3) == [34, 33, 33]  # restos iguais: menor índice ganha
    assert data.pontos_100([0, 0, 0, 0], 0) == [0, 0, 0, 0]


def test_pontos_100_soma_100_em_toda_a_mart():
    b = data.carregar("mart_municipio_benchmark")
    b = b[b["aptos"] > 0]
    somas = {sum(data.pontos_100(data.contagens_100(linha), int(linha["aptos"])))
             for _, linha in b.iterrows()}
    assert somas == {100}


def test_bloco_100_percentuais_visiveis_sobre_aptos():
    import re

    from app.lib import ui

    ind = data.indicadores(3509502, 2026, 1)
    pontos = data.pontos_100(data.contagens_100(ind), int(ind["aptos"]))
    bloco = ui.bloco_100(ind, pontos, 2026, 1, "resumo")
    visivel = bloco.split("<details")[0]
    soma = sum(float(v.replace(",", ".")) for v in re.findall(r"<b>([\d,]+)%</b>", visivel))
    assert 99.8 <= soma <= 100.2
    assert bloco.count('class="e100-pt ') == 100 and 'aria-hidden="true"' in bloco


@sem_2t_2026
def test_explore_segundo_turno_2026_sem_bloco_100():
    at = abrir("explore")
    at.radio(key="explore_eleicao").set_value((2026, 2)).run()
    assert not at.exception
    assert not any('class="e100' in m.value for m in at.markdown)


def test_bloco_100_indisponivel_para_municipio_novo_em_2022():
    at = abrir("explore", municipio=5101837)  # Boa Esperança do Norte (MT), só existe em 2026
    at.radio(key="e100_ano").set_value(2022).run()
    assert not at.exception, [e.value for e in at.exception]
    html = " ".join(m.value for m in at.markdown)
    assert "Sem dados para 2022" in html and "Dados de 2022, 1º turno, indisponíveis" in html
    assert "Ver distribuição entre quem votou" not in html


def test_bloco_100_volta_ao_ano_da_consulta():
    at = abrir("explore")
    at.radio(key="explore_eleicao").set_value((2022, 1)).run()
    assert at.radio(key="e100_ano").value == 2022
    at.radio(key="e100_ano").set_value(2026).run()
    assert at.radio(key="e100_ano").value == 2026
    assert any("Exibindo <b>2026 · 1º turno</b>" in m.value for m in at.markdown)
    at.radio(key="explore_eleicao").set_value((2022, 2)).run()
    assert at.radio(key="e100_ano").value == 2022


@pytest.mark.parametrize("regiao", [None, "Norte", "Sul"])
def test_mapa_ufs_mostra_27_e_esmaece_fora_da_regiao(regiao):
    ufs = data.uf_brasil(2026, 1)
    ufs = ufs[ufs["nivel"] == "UF"]
    valores = dict(zip(ufs["localidade"], ufs["comparecimento_pct"].astype(float), strict=True))
    realce = set(ufs["localidade"] if regiao is None else ufs[ufs["regiao"] == regiao]["localidade"])
    fig = charts.mapa_ufs(valores, "SP", realce)
    estados = fig.data[0]
    assert len(estados.locations) == 27
    opacidade = dict(zip(estados.locations, estados.marker.opacity, strict=True))
    assert {s for s, o in opacidade.items() if o == 1} == realce
    assert {o for o in opacidade.values()} <= {1, 0.25}


def test_inclinacao_mostra_so_2022_e_2026():
    fig = charts.inclinacao({"Município": (78.0, 76.4), "Estado": (79.0, 77.5), "Brasil": (79.2, 79.2)},
                            {"Município": "X", "Estado": "SP", "Brasil": "Brasil"})
    assert list(fig.layout.xaxis.tickvals) == [0, 1]
    assert list(fig.layout.xaxis.ticktext) == ["2022", "2026"]
    assert all(list(t.x) == [0, 1] for t in fig.data)


@sem_2t_2026
def test_brasil_segundo_turno_2026_aguardando():
    at = abrir("brasil")
    at.selectbox(key="brasil_eleicao").set_value((2026, 2)).run()
    assert not at.exception
    assert any("Aguardando apuração" in m.value for m in at.markdown)


def test_app_sem_caminho_abre_o_explore():
    home = Path(__file__).resolve().parents[1] / "app" / "Home.py"  # relativo ao teste no Streamlit novo
    at = AppTest.from_file(str(home), default_timeout=60).run()
    assert not at.exception, [e.value for e in at.exception]
    assert any("<h1>Explore seu município</h1>" in m.value for m in at.markdown)


@pytest.mark.parametrize("pagina,chave", [("explore", "explore_eleicao"), ("brasil", "brasil_eleicao"),
                                          ("mapa", "mapa_eleicao")])
def test_segundo_turno_2026_carregado_aparece_sem_mudar_codigo(marts_com_2t, pagina, chave):
    at = abrir(pagina, marts=marts_com_2t)
    widget = at.radio(key=chave) if pagina == "explore" else at.selectbox(key=chave)
    widget.set_value((2026, 2)).run()
    assert not at.exception, [e.value for e in at.exception]
    assert not any("Aguardando apuração" in m.value for m in at.markdown)
    assert any("Apuração concluída" in m.value for m in at.markdown)


def test_comparativo_com_segundo_turno_2026(marts_com_2t):
    at = abrir("comparativo", marts=marts_com_2t)
    assert not at.exception, [e.value for e in at.exception]
    html = " ".join(m.value for m in at.markdown)
    assert html.count("Apuração concluída") >= 3  # selo do topo + 2022 + 2026
    assert "aparecem aqui automaticamente" not in html


def test_selo_pendente_muda_depois_do_dia_da_eleicao(monkeypatch):
    from datetime import date

    from app.lib import ui

    class Hoje(date):
        dia = date(2026, 10, 25)

        @classmethod
        def today(cls):
            return cls.dia

    monkeypatch.setattr(ui, "date", Hoje)
    assert ui.segundo_turno_pendente() == "2º turno em 25/10"
    Hoje.dia = date(2026, 10, 26)
    assert ui.segundo_turno_pendente() == "2º turno em totalização"


def test_loader_igual_a_referencia_e_acessivel():
    from app.lib import loader

    cheio = loader.loader_html()
    assert 'role="status"' in cheio and "Carregando dados eleitorais" in cheio
    assert cheio.count('class="bau-ponto"') == 8
    assert all(m in cheio for m in loader.MENSAGENS_LOADER)
    mini = loader.loader_compacto_html("Carregando Campinas (SP)", "Buscando…")
    assert "bau-compacto" in mini and "Carregando Campinas (SP)" in mini
    ids = ['id="bau-ld"', 'id="bau-ld-mini"', 'id="bau-ld-sobre"', 'id="bau-ld-graf"']
    trechos = [cheio, mini, loader.sobreposicao_html(), loader.loader_grafico("a", "b")]
    assert all(i in t for i, t in zip(ids, trechos, strict=True))  # sem id repetido na página


def test_loader_nao_importa_pandas():
    """O Home.py mostra o loader antes de importar o resto do app: o módulo tem de ser leve."""
    import subprocess
    import sys

    codigo = "import sys; sys.path.insert(0, 'app'); from lib import loader; print('pandas' in sys.modules)"
    saida = subprocess.run([sys.executable, "-c", codigo], capture_output=True, text=True, check=True)
    assert saida.stdout.strip() == "False"


def test_home_mostra_loader_so_no_primeiro_acesso():
    at = AppTest.from_file(str(Path("app/Home.py").resolve()), default_timeout=60).run()
    assert not at.exception
    valores = [m.value for m in at.markdown]
    assert valores[0].startswith("<style>") and ".bau-sobre" in valores[0]  # loader.css
    assert "bau-sobre" in valores[1] and "bau-loader" in valores[1]  # 1º bloco visível
    assert any("st-key-rodape" in v for v in valores if v.startswith("<style>"))  # some pelo CSS
    at.run()
    assert not any("bau-sobre" in m.value for m in at.markdown if not m.value.startswith("<style>"))


def test_loader_do_primeiro_acesso_respeita_alto_contraste():
    from app.lib import loader

    assert 'class="bau-sobre contraste"' in loader.sobreposicao_html(True)
    assert 'class="bau-sobre"' in loader.sobreposicao_html(False)


@pytest.mark.parametrize("pagina", ["explore", "comparativo", "brasil", "mapa"])
def test_loader_some_depois_de_carregar(pagina):
    at = abrir(pagina)
    assert not at.exception
    html = [m.value for m in at.markdown if not m.value.startswith("<style>")]
    assert not any("bau-loader" in v for v in html)
    # no Mapa só fica o loader do gráfico, que o CSS esconde quando o Plotly termina de desenhar
    assert all("bau-grafico" in v for v in html if "bau-compacto" in v)
    assert any("bau-grafico" in v for v in html) == (pagina == "mapa")


def test_mapa_municipios_tem_loader_sobre_o_grafico():
    at = abrir("mapa")
    at.radio(key="mapa_nivel").set_value("Municípios").run()
    assert not at.exception
    assert any("bau-grafico" in m.value and "Desenhando os municípios" in m.value for m in at.markdown)


@pytest.mark.parametrize(("anterior", "atual", "esperado"), [
    ("explore", "mapa", 1), ("brasil", "comparativo", -1), ("mapa", "mapa", 0), (None, "explore", 0),
    ("brasil", "metodologia", 1), ("contato", "explore", -1),
])
def test_direcao_da_transicao_segue_a_ordem_das_abas(anterior, atual, esperado):
    from app.lib import ui

    assert ui.direcao(anterior, atual) == esperado


def _css(at) -> str:
    return " ".join(m.value for m in at.markdown if m.value.startswith("<style>"))


@pytest.mark.parametrize(("anterior", "pagina", "animacao"), [
    ("mapa", "explore", "entrar-esquerda"), ("explore", "brasil", "entrar-direita"),
])
def test_troca_de_pagina_desliza_do_lado_certo(anterior, pagina, animacao):
    at = abrir(pagina, estado={"_pagina": anterior})
    assert not at.exception
    assert f"animation: {animacao}" in _css(at)
    at.run()  # outra execução na mesma página: sem transição
    assert "animation: entrar-" not in _css(at)


def test_sem_transicao_no_primeiro_acesso_e_no_alto_contraste():
    assert "animation: entrar-" not in _css(abrir("explore"))
    at = abrir("brasil", estado={"_pagina": "explore", "alto_contraste": True})
    assert "animation: entrar-" not in _css(at)
