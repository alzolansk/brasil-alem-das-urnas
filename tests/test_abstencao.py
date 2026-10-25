"""Quem ficou em casa?: pipeline do perfil (arquivo sintético), mart publicada, cálculos, textos e tela."""

import hashlib
import json
import zipfile

import pandas as pd
import pytest

from app.lib import data, narrativa, perfil
from ingestion import perfil as ing
from ingestion.config import RAIZ
from tests.test_app import abrir

SAO_PAULO, BOA_ESPERANCA_DO_NORTE = 3550308, 5101837
MART = RAIZ / "data" / "marts" / "mart_perfil_abstencao.parquet"


# --- pipeline sobre um arquivo do TSE sintético (roda no CI, sem data/raw/) ----------------

COLUNAS_2026 = [
    "DT_GERACAO", "HH_GERACAO", "ANO_ELEICAO", "NR_TURNO", "SG_UF", "CD_MUNICIPIO", "NM_MUNICIPIO",
    "NR_ZONA", "CD_GENERO", "DS_GENERO", "CD_ESTADO_CIVIL", "DS_ESTADO_CIVIL", "CD_FAIXA_ETARIA",
    "DS_FAIXA_ETARIA", "CD_GRAU_INSTRUCAO", "DS_GRAU_INSTRUCAO", "QT_APTOS", "QT_COMPARECIMENTO",
    "QT_ABSTENCAO",
]  # fmt: skip


def _zip(tmp_path, linhas, ano=2026):
    """linhas: (uf, cd_mun, cd_gen, ds_gen, cd_faixa, ds_faixa, cd_esc, ds_esc, aptos, comp, abst)."""
    texto = ";".join(f'"{c}"' for c in COLUNAS_2026) + "\n"
    for uf, mun, cg, dg, cf, df, ce, de, ap, co, ab in linhas:
        valores = ["13/10/2026", "16:46:32", ano, 1, uf, f"{mun:05d}", "X", 1, cg, dg, 1, "SOLTEIRO",
                   cf, df, ce, de, ap, co, ab]  # fmt: skip
        texto += ";".join(f'"{v}"' for v in valores) + "\n"
    caminho = tmp_path / f"perfil_{ano}.zip"
    with zipfile.ZipFile(caminho, "w") as z:
        z.writestr(f"perfil_comparecimento_abstencao_{ano}_BRASIL.csv", texto.encode("latin-1"))
    return caminho


LINHAS_OK = [
    ("SP", 62910, 4, "FEMININO", 1600, "16 anos", 6, "ENSINO MÉDIO COMPLETO", 10, 8, 2),
    ("SP", 62910, 2, "MASCULINO", 1600, "16 anos", 6, "ENSINO MÉDIO COMPLETO", 20, 15, 5),
    ("SP", 62910, 2, "MASCULINO", 2124, "21 a 24 anos", 8, "SUPERIOR COMPLETO", 30, 21, 9),
    ("SP", 62910, 0, "NÃO INFORMADO", -3, "Inválido", 0, "NÃO INFORMADO", 4, 1, 3),
    ("ZZ", 29360, 2, "MASCULINO", 3539, "35 a 39 anos", 8, "SUPERIOR COMPLETO", 6, 3, 3),
]
DIM = pd.DataFrame({"cd_municipio_tse": pd.Series([62910], dtype="int32"),
                    "cd_municipio_ibge": pd.Series([3509502], dtype="int32"),
                    "nm_municipio": ["Campinas"]})  # fmt: skip


def test_pipeline_soma_marginais_sem_dupla_contagem(tmp_path):
    marg, v = ing.ler(_zip(tmp_path, LINHAS_OK), 2026, tamanho_bloco=2)  # força vários blocos
    assert ing.validar_arquivo(2026, v, [1], set(marg["turno"])) == []
    mart, erros = ing.montar_mart(marg, DIM)
    assert erros == [] and ing.validar_mart(mart, {}) == []
    assert set(mart["sg_uf"]) == {"SP"}  # exterior fora da mart
    linha = mart.set_index(["dimensao", "cd_categoria"])
    assert linha.loc[("total", 0), "aptos"] == 64 and linha.loc[("total", 0), "abstencoes"] == 19
    assert linha.loc[("faixa_etaria", 1600), "aptos"] == 30  # 16 anos: feminino + masculino
    assert linha.loc[("faixa_etaria", 1600), "abstencao_pct"] == pytest.approx(100 * 7 / 30)
    assert linha.loc[("faixa_etaria", 1600), "voto_facultativo"]
    assert not linha.loc[("faixa_etaria", 2124), "voto_facultativo"]
    assert not linha.loc[("genero", 0), "informado"] and linha.loc[("genero", 0), "ordem"] == 99
    for d in ing.DIMENSOES:  # cada dimensão fecha o total do município
        assert mart[mart["dimensao"] == d]["aptos"].sum() == 64
    totais, erros = ing.conferir_totais(marg, {(2026, 1): {"aptos": 70}})  # 64 + 6 do exterior
    assert erros == [] and totais[0]["diferenca"] == 0


def test_pipeline_aponta_categoria_desconhecida_e_soma_errada(tmp_path):
    ruins = [
        ("SP", 62910, 2, "MASCULINO", 1600, "dezesseis", 6, "ENSINO MÉDIO COMPLETO", 10, 8, 3),
        ("SP", 62910, 2, "MASCULINO", 1234, "?", 9, "DOUTORADO", 10, 8, 2),
    ]
    marg, v = ing.ler(_zip(tmp_path, ruins), 2026)
    erros = " | ".join(ing.validar_arquivo(2026, v, [1, 2], set(marg["turno"])))
    assert "aptos diferente da soma" in erros
    assert "descrito como 'dezesseis'" in erros
    assert "código 1234" in erros and "código 9" in erros
    assert "turno 2 está em sources.yaml" in erros


def test_mart_sem_codigo_ibge_e_reprovada(tmp_path):
    marg, _ = ing.ler(_zip(tmp_path, LINHAS_OK), 2026)
    _, erros = ing.montar_mart(marg, DIM.assign(cd_municipio_tse=pd.Series([1], dtype="int32")))
    assert erros and "sem código IBGE" in erros[0]


# --- mart publicada (data/marts/mart_perfil_abstencao.parquet) ------------------------------


@pytest.fixture(scope="module")
def mart():
    return pd.read_parquet(MART)


def test_mart_bate_com_o_manifesto(mart):
    manifest = json.loads((MART.parent / "manifest.json").read_text(encoding="utf-8"))
    info = manifest["arquivos"][MART.name]
    assert info["linhas"] == len(mart)
    assert info["sha256"] == hashlib.sha256(MART.read_bytes()).hexdigest()


def test_mart_regras_de_qualidade(mart):
    from ingestion.validate import MUNICIPIOS_ESPERADOS

    assert ing.validar_mart(mart, MUNICIPIOS_ESPERADOS) == []
    assert (mart["abstencao_pct"] - 100 * mart["abstencoes"] / mart["aptos"]).abs().max() < 1e-9
    assert mart["abstencao_pct"].between(0, 100).all()
    facultativos = set(map(tuple, mart.loc[mart["voto_facultativo"], ["dimensao", "cd_categoria"]]
                           .drop_duplicates().values))  # fmt: skip
    assert facultativos == {(d, cd) for d, cds in ing.FACULTATIVO.items() for cd in cds}
    assert ("escolaridade", 1) in facultativos  # analfabetos (CF, art. 14, § 1º, II)


def test_mart_categorias_iguais_em_2022_e_2026(mart):
    info = mart[mart["informado"] & (mart["dimensao"] != "total")]
    por_ano = {ano: set(map(tuple, g[["dimensao", "cd_categoria"]].drop_duplicates().values))
               for ano, g in info.groupby("ano")}  # fmt: skip
    assert por_ano[2022] == por_ano[2026]
    oficiais = {(d, cd) for d, (_, cats) in ing.DIMENSOES.items() for cd, (_, ok) in cats.items() if ok}
    assert por_ano[2026] == oficiais


def test_mart_bate_com_a_evidencia_do_pipeline(mart):
    evidencia = json.loads((RAIZ / "docs/validacao/perfil_execucao.json").read_text(encoding="utf-8"))
    assert evidencia["problemas"] == [] and evidencia["categorias_informadas_iguais_entre_anos"]
    assert all(t["diferenca"] == 0 for t in evidencia["totais_brasil_com_exterior_vs_painel_tse"])
    total = mart[mart["dimensao"] == "total"].groupby(["ano", "turno"])["aptos"].sum()
    for linha in evidencia["perfil_vs_detalhe_votacao_por_municipio"]:
        assert total[(linha["ano"], linha["turno"])] == linha["aptos_perfil"]


def test_eleicoes_disponiveis_no_perfil():
    assert data.tem_perfil(2022, 1) and data.tem_perfil(2022, 2) and data.tem_perfil(2026, 1)
    assert data.perfil(BOA_ESPERANCA_DO_NORTE, 2022, 1).empty
    assert not data.perfil(BOA_ESPERANCA_DO_NORTE, 2026, 1).empty


# --- cálculos e textos ---------------------------------------------------------------------


def _df(linhas, ano=2026):
    """linhas: (dimensao, cd, categoria, ordem, aptos, abstencoes, facultativo)."""
    df = pd.DataFrame(linhas, columns=["dimensao", "cd_categoria", "categoria", "ordem", "aptos",
                                       "abstencoes", "voto_facultativo"])  # fmt: skip
    df["informado"] = df["ordem"] != 99
    df["comparecimento"] = df["aptos"] - df["abstencoes"]
    df["abstencao_pct"] = 100 * df["abstencoes"] / df["aptos"]
    return df.assign(ano=ano)


BASE = [
    ("total", 0, "Todos os eleitores", 0, 10_000, 2_000, False),
    ("faixa_etaria", 1600, "16 anos", 1, 100, 10, True),
    ("faixa_etaria", 2124, "21 a 24 anos", 6, 3_000, 900, False),
    ("faixa_etaria", 5559, "55 a 59 anos", 13, 3_000, 300, False),
    ("faixa_etaria", 9999, "100 anos ou mais", 22, 40, 39, True),  # base pequena
    ("faixa_etaria", 8084, "80 a 84 anos", 18, 3_860, 751, True),
    ("faixa_etaria", -3, "Inválido", 99, 0, 0, False),
    ("genero", 4, "Feminino", 2, 5_000, 950, False),
    ("genero", 2, "Masculino", 1, 4_990, 1_045, False),
    ("genero", 0, "Não informado", 99, 10, 5, False),
    ("escolaridade", 1, "Analfabeto", 1, 500, 300, True),
    ("escolaridade", 8, "Superior completo", 8, 9_500, 1_700, False),
]


def test_grupos_extremos_ignoram_nao_informado_e_base_pequena():
    df = _df(BASE)
    g = perfil.grupos(df, "faixa_etaria")
    assert list(g["categoria"]) == ["16 anos", "21 a 24 anos", "55 a 59 anos", "80 a 84 anos",
                                    "100 anos ou mais"]  # fmt: skip
    assert list(g["base_pequena"]) == [False, False, False, False, True]
    maior, menor = perfil.extremos(g)
    assert maior["categoria"] == "21 a 24 anos" and menor["categoria"] == "16 anos"
    assert perfil.nao_informados(df, "genero") == 10
    assert perfil.extremos(g.iloc[:0]) == (None, None)


def test_destaques_so_quando_a_diferenca_chega_a_meio_ponto():
    g = perfil.grupos(_df([("genero", 2, "Masculino", 1, 1000, 234, False),
                           ("genero", 4, "Feminino", 2, 1000, 238, False)]), "genero")  # fmt: skip
    assert perfil.destaques(g) == (None, None)  # 23,8% × 23,4%: praticamente igual
    assert perfil.destaques(perfil.grupos(_df(BASE), "faixa_etaria")) == (2124, 1600)


def test_empate_fica_com_a_primeira_categoria_oficial():
    g = perfil.grupos(_df([("genero", 2, "Masculino", 1, 100, 20, False),
                           ("genero", 4, "Feminino", 2, 100, 20, False)]), "genero")  # fmt: skip
    maior, menor = perfil.extremos(g)
    assert maior["categoria"] == menor["categoria"] == "Masculino"


def test_comparacao_em_pontos_percentuais_e_grupos_comparaveis():
    antes = _df(BASE, 2022)
    depois = _df(BASE).assign(abstencoes=lambda d: d["abstencoes"] + (d["aptos"] * 0.01).round())
    depois["abstencao_pct"] = 100 * depois["abstencoes"] / depois["aptos"]
    c = perfil.comparacao(antes, depois)
    assert "Inválido" not in set(c["categoria"]) and "Não informado" not in set(c["categoria"])
    linha = c.set_index("categoria").loc["21 a 24 anos"]
    assert linha["delta_pp"] == pytest.approx(1.0)
    assert not c.set_index("categoria").loc["100 anos ou mais", "comparavel"]
    alta, queda = perfil.maiores_variacoes(c)
    assert alta["dimensao"] != "total" and queda["dimensao"] != "total"


def _revelam(df, historico=("pendente", None)):
    return narrativa.revelam("X", 2026, 1, perfil.total(df), perfil.grupos(df, "faixa_etaria"),
                             perfil.grupos(df, "genero"), perfil.grupos(df, "escolaridade"),
                             historico)  # fmt: skip


def test_o_que_os_dados_revelam_com_numeros_reais_do_df():
    itens = _revelam(_df(BASE))
    assert itens == [
        "Em X, 20,0% dos eleitores aptos (2.000 de 10.000) não foram votar no 1º turno de 2026.",
        "Entre as faixas de 18 a 69 anos, a abstenção foi maior entre eleitores de 21 a 24 anos "
        "(30,0%) e menor entre os de 55 a 59 anos (10,0%).",
        "A taxa de abstenção de eleitores analfabetos, que têm voto facultativo, ficou 40,0 p.p. "
        "acima da média municipal (60,0% contra 20,0%); a menor foi entre eleitores com superior "
        "completo (17,9%).",
        "Por gênero, a abstenção foi de 19,0% no feminino e de 20,9% no masculino, uma diferença "
        "de 1,9 p.p.",
        "O TSE ainda não publicou o perfil do 1º turno de 2026; a comparação com 2022 neste turno "
        "aparece quando ele sair.",
    ]


def test_idade_facultativa_vem_depois_e_como_registro_do_cadastro():
    linhas = [r if r[1] != 8084 else (*r[:4], 3_860, 2_500, True) for r in BASE]
    itens = _revelam(_df(linhas))
    assert itens[1].startswith("Entre as faixas de 18 a 69 anos, a abstenção foi maior entre "
                               "eleitores de 21 a 24 anos")  # fmt: skip
    assert itens[4] == ("Nas idades de voto facultativo, a taxa mais alta foi a dos registros de "
                        "eleitores de 80 a 84 anos no cadastro eleitoral: 64,8% (2.500 de 3.860).")  # fmt: skip
    assert not any("obrigatório" in item for item in itens)  # analfabetos também são facultativos


def test_genero_praticamente_igual_e_historico_com_limite_de_seis():
    linhas = [r if r[0] != "genero" or r[1] == 0 else (*r[:4], 5_000, 1_000, False) for r in BASE]
    linhas = [r if r[1] != 8084 else (*r[:4], 3_860, 2_500, True) for r in linhas]
    df = _df(linhas)
    antes = _df(linhas, 2022)
    variacao = [0, 0, 3, -2, 0, 0, 0, 0, 0, 0, 0, 0]  # +3 p.p. em 21 a 24 anos, −2 em 55 a 59
    c = perfil.comparacao(antes, df.assign(abstencao_pct=df["abstencao_pct"] + variacao))
    alta, queda = perfil.maiores_variacoes(c)
    tot = perfil.total(df)
    itens = _revelam(df, ("disponivel", (tot, tot, alta, queda)))
    assert len(itens) == narrativa.MAX_REVELAM == 6
    assert itens[0].endswith("no 1º turno de 2026. Em 2022, eram 20,0%.")
    assert itens[2] == ("Entre 2022 e 2026, a abstenção de eleitores de 21 a 24 anos aumentou 3,0 "
                        "p.p., a maior alta entre os grupos (de 30,0% para 33,0%).")  # fmt: skip
    assert itens[4] == "Por gênero, a abstenção foi praticamente igual: 20,0% no feminino e 20,0% no masculino."
    assert itens[5] == ("A maior queda foi entre eleitores de 55 a 59 anos: 2,0 p.p. a menos (de "
                        "10,0% para 8,0%).")  # fmt: skip
    # a frase das idades facultativas tem prioridade menor e fica fora do limite
    assert not any("registros" in item for item in itens)
    sem = _revelam(df, ("sem_base", None))
    assert sem[-1].startswith("Não há dados de 2022 para X")


def test_tres_primeiros_itens_de_sao_paulo_priorizam_jovens_adultos():
    df = data.perfil(SAO_PAULO, 2026, 1)
    base = data.perfil(SAO_PAULO, 2022, 1)
    alta, queda = perfil.maiores_variacoes(perfil.comparacao(base, df))
    itens = _revelam(df, ("disponivel", (perfil.total(base), perfil.total(df), alta, queda)))
    assert len(itens) <= 6
    assert "21 a 24 anos" in itens[1] and "100 anos" not in " ".join(itens[:3])


def test_cartao_mostra_tres_e_o_resto_em_ver_mais():
    from app.lib import ui

    html = ui.cartao_leitura(["a", "b", "c", "d", "e"], rotulo="O que os dados revelam?", visiveis=3)
    visivel, escondido = html.split('<details class="mais">')
    assert visivel.count("<li>") == 3 and escondido.count("<li>") == 2
    assert "Ver mais (2)" in escondido and '<ol start="4">' in escondido
    assert "<details" not in ui.cartao_leitura(["a", "b"], visiveis=3)


def test_textos_descrevem_sem_atribuir_causa():
    proibidas = ("porque", "devido", "motivo", "causa", "desinteresse", "culpa", "óbito", "morre")
    df = data.perfil(SAO_PAULO, 2026, 1)
    c = perfil.comparacao(data.perfil(SAO_PAULO, 2022, 1), df)
    alta, queda = perfil.maiores_variacoes(c)
    hist = ("disponivel", (perfil.total(data.perfil(SAO_PAULO, 2022, 1)), perfil.total(df), alta, queda))
    texto = " ".join(_revelam(df, hist) + _revelam(df)).casefold()
    assert not [p for p in proibidas if p in texto]


def test_manchete_singular_e_plural():
    assert narrativa.manchete_abstencao("X", 21.4, 2026, 1) == {
        "antes": "Em X,", "destaque": "21 em cada 100 eleitores",
        "depois": " ficaram em casa no 1º turno de 2026."}  # fmt: skip
    assert narrativa.manchete_abstencao("X", 1.2, 2026, 1)["depois"].startswith(" ficou")


# --- tela -----------------------------------------------------------------------------------


def _html(at) -> str:
    return " ".join(m.value for m in at.markdown)


def test_tela_mostra_os_quatro_blocos_e_a_nota():
    at = abrir("abstencao")
    assert not at.exception, [e.value for e in at.exception]
    html = _html(at)
    for trecho in ("<h1>Quem ficou em casa?</h1>", "O que os dados revelam?", "Por faixa etária",
                   "Por gênero", "Por escolaridade", "Comparação 2022 × 2026", "Como ler estes",
                   "Maior taxa", "Menor taxa", "Média do município", "Voto facultativo",
                   "não identificam o comportamento de ninguém"):  # fmt: skip
        assert trecho in html, trecho


def test_ordenar_por_taxa_poe_a_maior_primeiro():
    import re

    at = abrir("abstencao")
    at.radio(key="abstencao_ordem").set_value("Maior taxa primeiro").run()
    assert not at.exception
    lista = next(m.value for m in at.markdown if 'class="grupos' in m.value and "16 anos" in m.value)
    taxas = [float(v.replace(",", ".")) for v in re.findall(r'class="val">([\d,]+)%', lista)]
    assert taxas == sorted(taxas, reverse=True) and len(taxas) == len(ing.FAIXA_ETARIA) - 1


def test_comparacao_troca_de_dimensao():
    at = abrir("abstencao")
    at.radio(key="abstencao_hist_dim").set_value("escolaridade").run()
    assert not at.exception
    assert "Superior completo" in _html(at) and "Todos os eleitores" in _html(at)


@pytest.mark.skipif(data.tem_perfil(2026, 2), reason="perfil do 2º turno de 2026 já carregado")
def test_segundo_turno_2026_aguardando_e_2022_t2_sem_comparacao():
    at = abrir("abstencao")
    at.radio(key="abstencao_eleicao").set_value((2026, 2)).run()
    assert not at.exception
    assert "ainda não foi publicado" in _html(at) and "Aguardando apuração" in _html(at)
    at.radio(key="abstencao_eleicao").set_value((2022, 2)).run()
    assert not at.exception
    html = _html(at)
    assert "Por faixa etária" in html and "Perfil do 2º turno de 2026 ainda não publicado" in html


def test_municipio_novo_sem_2022():
    at = abrir("abstencao", municipio=BOA_ESPERANCA_DO_NORTE)
    assert not at.exception
    assert "não tem dados de 2022" in _html(at)
    at.radio(key="abstencao_eleicao").set_value((2022, 1)).run()
    assert not at.exception and "Não há dados desta eleição" in _html(at)


@pytest.mark.parametrize(("pagina", "chave"), [("abstencao", "abstencao_eleicao"),
                                               ("explore", "explore_eleicao"),
                                               ("brasil", "brasil_eleicao"), ("mapa", "mapa_eleicao")])
def test_eleicao_escolhida_vale_em_todas_as_telas(pagina, chave):
    at = abrir(pagina, estado={"_eleicao": (2022, 1)})
    assert not at.exception, [e.value for e in at.exception]
    widget = at.radio(key=chave) if pagina in ("abstencao", "explore") else at.selectbox(key=chave)
    assert widget.value == (2022, 1)
    widget.set_value((2022, 2)).run()
    assert at.session_state["_eleicao"] == (2022, 2)


def test_aba_na_navegacao_principal():
    from app.lib import ui

    assert ("abstencao", "Quem ficou em casa?") in ui.ABAS
    at = abrir("explore")
    assert not at.exception
    assert "Quem ficou em casa?" in [link.proto.label for link in at.get("page_link")]


def _lista(at, contem: str) -> str:
    return next(m.value for m in at.markdown if 'class="grupos' in m.value and contem in m.value)


def test_filtros_de_voto_facultativo_em_cada_secao():
    at = abrir("abstencao")
    assert "Voto facultativo: analfabetos" in _html(at)
    assert "registros de 100 anos ou mais" in _html(at)  # contexto junto do gráfico de idade
    at.toggle(key="abstencao_fac_faixa_etaria").set_value(False).run()
    assert not at.exception
    idade = _lista(at, "18 anos")
    assert "16 anos" not in idade and "100 anos ou mais" not in idade and "65 a 69 anos" in idade
    assert "Idades de voto facultativo ocultas pelo filtro" in _html(at)
    assert "registros de 100 anos ou mais" not in _html(at)
    barra = '<span class="nome">Analfabeto'
    assert barra in _lista(at, "Superior completo")  # o filtro é só da seção
    at.toggle(key="abstencao_fac_escolaridade").set_value(False).run()
    assert barra not in _lista(at, "Superior completo")
    assert "Analfabetos ocultos pelo filtro" in _html(at)
    tabela = next(m.value for m in at.markdown if "Aptos em 2026" in m.value)
    assert "16 anos" in tabela
    at.toggle(key="abstencao_fac_historico").set_value(False).run()
    tabela = next(m.value for m in at.markdown if "Aptos em 2026" in m.value)
    assert "16 anos" not in tabela and "70 a 74 anos" not in tabela and "Todos os eleitores" in tabela


def test_legenda_e_nota_nao_chamam_18_a_69_de_obrigatorio():
    at = abrir("abstencao")
    html = _html(at)
    assert "Voto obrigatório" not in html and "voto obrigatório" not in html
    assert "Analfabetos têm voto facultativo em qualquer idade" in html
    assert "As taxas podem diferir entre as bases; normalmente a diferença é pequena, mas há exceções." in html
    assert "décimos" not in html
    assert "Ver mais (" in html
