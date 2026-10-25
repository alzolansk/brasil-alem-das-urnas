"""Páginas de texto do rodapé. Rascunhos: o texto final é aprovado por uma pessoa (tarefa 3.8)."""

from pathlib import Path

import streamlit as st
from lib import data, ui

DOCS = Path(__file__).resolve().parents[2] / "docs"

AVISO = "Texto em rascunho, a ser revisado antes da publicação."

TEXTOS = {
    "dados": """
## Sobre os dados

- **Eleições:** Presidente da República, {eleicoes}.
- **Fonte dos resultados:** Portal de Dados Abertos do TSE (detalhe da votação por município e zona).
- **Quem ficou em casa?:** perfil do eleitorado que compareceu e que se absteve, também do TSE
  (gênero, faixa etária e escolaridade). É a base do painel oficial de comparecimento; por isso a
  taxa do município nessa tela pode diferir em alguns décimos da do Explore.
- **Municípios:** IBGE (códigos, regiões e malhas). Os votos do exterior ficam fora do mapa e dos
  municípios, mas entram no total do Brasil, indicado como "Brasil + Exterior" (como no total
  oficial do TSE).
- **Última atualização dos dados do app:** {atualizacao}.
- **Conferência:** os totais nacionais foram comparados com o painel oficial do TSE. Veja o
  detalhe em *Metodologia*.
""",
    "acessibilidade": """
## Acessibilidade

- Texto com contraste mínimo de 4,5:1 (WCAG AA) e opção **Alto contraste** no topo da página.
- Navegação pelo teclado, com foco visível.
- Todo gráfico tem uma alternativa em tabela ou lista.
- Variações sempre com seta e sinal, não só com cor. Azul ▲ indica aumento e laranja ▼ indica
  queda: a cor indica só a direção da mudança, não se ela é boa ou ruim.
- As animações aparecem só no primeiro carregamento de cada tela e ficam desligadas se o seu
  sistema pede menos movimento ou com o alto contraste ligado.
- Se encontrar uma barreira, conte pela página *Contato*.
""",
    "termos": """
## Termos de uso

Esta é uma ferramenta **independente**, sem vínculo com o TSE, o IBGE, partidos ou governos.
Os dados são públicos e vêm do Portal de Dados Abertos do TSE; podem ser corrigidos pelo órgão
depois da publicação. Não use a ferramenta como documento oficial. Para dados oficiais,
consulte o TSE. Os resultados aparecem sem juízo de valor sobre candidatos ou partidos.
""",
    "contato": """
## Contato

Para relatar erro nos dados, sugerir melhorias ou relatar problema de acessibilidade, abra uma
*issue* no repositório do projeto no GitHub. (Canal de contato definitivo: a definir.)
""",
}


def _dicionario() -> str:
    linhas = "\n".join(
        f"| {nome} | {descricao} |" for nome, descricao in data.INDICADORES.values()
    )
    return (
        "## Dicionário de dados\n\n| Indicador | O que significa |\n|---|---|\n"
        f"{linhas}\n\n**Eleitores aptos:** quem podia votar. **p.p.:** ponto percentual, a "
        "diferença simples entre duas porcentagens (de 78,5% para 79,4% = +0,9 p.p.). "
        "Comparecimento e abstenção são calculados sobre os aptos; válidos, brancos e nulos, "
        "sobre quem compareceu.\n\n**Abstenção de um grupo** (Quem ficou em casa?): eleitores do "
        "grupo que não compareceram ÷ eleitores aptos do grupo. Grupos com menos de 50 eleitores "
        "aptos aparecem com * e ficam fora dos destaques."
    )


def _metodologia() -> str:
    arquivo = DOCS / "metodologia.md"
    return arquivo.read_text(encoding="utf-8") if arquivo.exists() else "## Metodologia"


def _eleicoes() -> str:
    if data.tem_dados(2026, 2):
        return "1º e 2º turnos de 2022 e de 2026"
    return ("1º e 2º turnos de 2022 e 1º turno de 2026. O 2º turno de 2026 entra quando o TSE "
            "publicar os resultados")


def pagina(chave: str):
    def render():
        ui.cabecalho(chave)
        if chave == "dicionario":
            texto = _dicionario()
        elif chave == "metodologia":
            texto = _metodologia()
        else:
            texto = (TEXTOS[chave].replace("{atualizacao}", data.ultima_atualizacao())
                     .replace("{eleicoes}", _eleicoes()))
        st.markdown(texto)
        st.caption(AVISO)
        ui.rodape()

    render.__name__ = f"pagina_{chave}"
    return render
