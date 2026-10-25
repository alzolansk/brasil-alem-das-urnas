"""Páginas de texto do rodapé. Rascunhos: o texto final é aprovado por uma pessoa (tarefa 3.8)."""

from pathlib import Path

import streamlit as st
from lib import data, ui

DOCS = Path(__file__).resolve().parents[2] / "docs"

AVISO = "Texto em rascunho, a ser revisado antes da publicação."

TEXTOS = {
    "dados": """
## Sobre os dados

- **Eleições:** Presidente da República, 1º e 2º turnos de 2022 e 1º turno de 2026. O 2º turno de 2026
  entra quando o TSE publicar os resultados.
- **Fonte dos resultados:** Portal de Dados Abertos do TSE (detalhe da votação por município e zona).
- **Municípios:** IBGE (códigos, regiões e malhas). Os votos do exterior ficam fora do mapa e dos
  municípios, mas entram no total do Brasil.
- **Última atualização dos dados do app:** {atualizacao}.
- **Conferência:** os totais nacionais foram comparados com o painel oficial do TSE. Veja o
  detalhe em *Metodologia*.
""",
    "acessibilidade": """
## Acessibilidade

- Texto com contraste mínimo de 4,5:1 (WCAG AA) e opção **Alto contraste** no topo da página.
- Navegação pelo teclado, com foco visível.
- Todo gráfico tem uma alternativa em tabela ou lista.
- Variações sempre com seta e sinal, não só com cor.
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
        "sobre quem compareceu."
    )


def _metodologia() -> str:
    arquivo = DOCS / "metodologia.md"
    return arquivo.read_text(encoding="utf-8") if arquivo.exists() else "## Metodologia"


def pagina(chave: str):
    def render():
        ui.cabecalho(chave)
        if chave == "dicionario":
            texto = _dicionario()
        elif chave == "metodologia":
            texto = _metodologia()
        else:
            texto = TEXTOS[chave].replace("{atualizacao}", data.ultima_atualizacao())
        st.markdown(texto)
        st.caption(AVISO)
        ui.rodape()

    render.__name__ = f"pagina_{chave}"
    return render
