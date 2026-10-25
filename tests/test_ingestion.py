import pandas as pd
import pytest

from ingestion import crosswalk, download, parse_tse, validate
from ingestion.config import RAIZ, carregar_sources

_CFG = carregar_sources()["tse"]["detalhe_votacao_munzona"]
# data/raw/ não vai para o git: no CI (sem os zips do TSE) estes testes são pulados.
pytestmark = pytest.mark.skipif(
    not all((RAIZ / _CFG[a]["arquivo_local"]).exists() for a in (2022, 2026)),
    reason="arquivos brutos do TSE ausentes em data/raw/ (rode python -m ingestion.download)",
)


@pytest.fixture(scope="module")
def zona():
    return pd.concat(
        [parse_tse.parse_zona(download.arquivo_detalhe_votacao(a), a) for a in (2022, 2026)]
    )


@pytest.fixture(scope="module")
def dim():
    return crosswalk.montar_dim_municipio(crosswalk.ler_crosswalk(download.arquivo_crosswalk()))


def test_so_presidente_e_linhas_esperadas(zona):
    t = zona.groupby(["ano", "turno"]).size()
    assert t[(2022, 1)] == 6283 and t[(2022, 2)] == 6283 and t[(2026, 1)] == 6292


def test_consistencia_zona(zona):
    assert validate.validar_zona(zona) == []


def test_nulos_tecnicos_ficam_em_nulos(zona):
    # 5.246 votos nulos técnicos em 2026 já estão em QT_TOTAL_VOTOS_NULOS
    assert zona[zona.ano == 2026].nulos.sum() > 5246


def test_total_brasil_2022(zona):
    assert validate.validar_totais(zona) == []


def test_agregacao_preserva_totais(zona):
    mun = parse_tse.agregar_municipio(zona)
    assert mun.aptos.sum() == zona.aptos.sum()
    assert mun.n_zonas.sum() == len(zona)


def test_crosswalk_100_por_cento(zona, dim):
    mun = parse_tse.agregar_municipio(zona)
    casados, nao = crosswalk.casar(mun, dim)
    assert nao.empty
    assert casados.cd_municipio_ibge.notna().all()
    assert dim.cd_municipio_ibge.is_unique and dim.cd_municipio_tse.is_unique


def test_boa_esperanca_do_norte_so_em_2026(zona, dim):
    assert dim.cd_municipio_ibge.eq(5101837).sum() == 1
    anos = zona[zona.cd_municipio_tse == 73709].ano.unique()
    assert list(anos) == [2026]
