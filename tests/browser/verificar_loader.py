"""Aceite real do loader (Playwright + Chrome locais, fora da suíte pytest).

Com o Streamlit rodando: python tests/browser/verificar_loader.py --saida <pasta>
O AppTest não executa CSS; esta sondagem mede os quadros exibidos no navegador.
"""

import argparse
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

from app.lib.loader import sobreposicao_html  # noqa: E402

SONDA = """
window.__loader = {quadros: [], pronto: null};
function registrar() {
  const el = document.querySelector('.bau-sobre');
  const css = el && getComputedStyle(el);
  const visivel = !!(el && el.getBoundingClientRect().width &&
    css.display !== 'none' && css.visibility === 'visible');
  const log = window.__loader;
  const agora = performance.now();
  if (!log.quadros.length || log.quadros.at(-1).visivel !== visivel)
    log.quadros.push({ms: agora, visivel,
      relogio: el?.getAnimations().map(a => ({nome: a.animationName, tempo: a.currentTime}))});
  if (log.pronto === null && document.querySelector('.st-key-rodape'))
    log.pronto = agora;
}
function observar() { registrar(); requestAnimationFrame(observar); }
new MutationObserver(registrar).observe(document, {childList: true, subtree: true});
requestAnimationFrame(observar);
"""


def medir(pagina):
    pagina.locator(".bau-sobre").wait_for(state="hidden")
    pagina.wait_for_timeout(80)  # deixa a sondagem registrar o primeiro quadro oculto
    log = pagina.evaluate("window.__loader")
    inicio = next(q["ms"] for q in log["quadros"] if q["visivel"])
    fim = next(q["ms"] for q in log["quadros"] if not q["visivel"] and q["ms"] > inicio)
    assert fim - inicio >= 1480, log  # tolerância de um quadro a 60 Hz
    if log["pronto"] is not None:
        assert fim >= log["pronto"], log
    return {"visivel_ms": round(fim - inicio), "quadros": log["quadros"]}


def verificar(base, saida):
    saida.mkdir(parents=True, exist_ok=True)
    resultados = {}
    css = (RAIZ / "app/assets/loader.css").read_text(encoding="utf-8")
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome")
        # Servidor frio na primeira execução; o mesmo processo fica aquecido depois.
        for nome, largura, movimento, consulta in [
            ("primeira_abertura", 1280, "no-preference", ""),
            ("cache_aquecido", 1280, "no-preference", ""),
            ("movimento_reduzido", 390, "reduce", ""),
            ("alto_contraste", 390, "no-preference", "&c=1"),
        ]:
            pagina = browser.new_page(
                viewport={"width": largura, "height": 900}, reduced_motion=movimento,
            )
            pagina.add_init_script(SONDA)
            pagina.goto(base + "/?m=3509502" + consulta)
            pagina.locator(".bau-sobre").wait_for(state="visible")
            pagina.wait_for_timeout(1000)
            pagina.screenshot(path=str(saida / f"{nome}.png"))
            contorno = pagina.locator(".bau-sobre .bau-contorno")
            animacao = contorno.evaluate("e => getComputedStyle(e).animationName")
            if movimento == "reduce" or consulta:
                assert animacao == "none", animacao
                assert contorno.evaluate("e => getComputedStyle(e).strokeDashoffset") == "0px"
                assert pagina.locator(".bau-sobre .bau-ponto").first.evaluate(
                    "e => getComputedStyle(e).transform"
                ) == "none"
                assert pagina.locator(".bau-sobre .bau-msgs span").first.evaluate(
                    "e => getComputedStyle(e).opacity"
                ) == "1"
            else:
                assert animacao == "bau-tracar", animacao
                assert contorno.evaluate("e => getComputedStyle(e).animationDuration") == "3.6s"
            assert contorno.get_attribute("pathLength") == "1"
            assert pagina.locator(".bau-sobre .bau-ponto").count() == 8
            resultados[nome] = medir(pagina)
            assert pagina.locator('[data-testid="stException"]').count() == 0
            assert pagina.evaluate("document.documentElement.scrollWidth <= innerWidth")
            if nome == "cache_aquecido":
                for aba in ["Mapa eleitoral", "Comparativo 2022 × 2026"]:
                    pagina.evaluate("window.__loader.quadros = []")
                    pagina.get_by_role("link", name=aba).first.click()
                    pagina.wait_for_timeout(2000)
                    assert not any(q["visivel"] for q in pagina.evaluate(
                        "window.__loader.quadros"
                    )), aba
                pagina.reload()
                pagina.locator(".bau-sobre").wait_for(state="visible")
                resultados["recarregar_rota_interna"] = medir(pagina)
            pagina.close()

        # Isola as duas condições: conteúdo pronto antes/depois do tempo mínimo.
        for pronto in [True, False]:
            pagina = browser.new_page()
            rodape = '<footer class="st-key-rodape"></footer>' if pronto else ""
            pagina.set_content(f'<style>{css}</style><div class="stApp">'
                               f'{sobreposicao_html()}{rodape}</div>')
            pagina.evaluate(SONDA)
            pagina.locator(".bau-sobre").wait_for(state="visible")
            if not pronto:
                pagina.wait_for_timeout(2100)
                assert pagina.locator(".bau-sobre").is_visible()
                pagina.evaluate("document.querySelector('.stApp').insertAdjacentHTML("
                                "'beforeend', '<footer class=st-key-rodape></footer>')")
            resultados[f"conteudo_pronto_{pronto}"] = medir(pagina)
            pagina.close()
        browser.close()
    (saida / "tempos.json").write_text(
        json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8",
    )
    print(json.dumps({k: v["visivel_ms"] for k, v in resultados.items()}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="http://localhost:8599")
    parser.add_argument("--saida", type=Path, required=True)
    args = parser.parse_args()
    verificar(args.base, args.saida)
