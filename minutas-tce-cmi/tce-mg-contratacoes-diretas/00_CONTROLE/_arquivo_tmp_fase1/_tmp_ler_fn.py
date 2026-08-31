# -*- coding: utf-8 -*-
import io, re, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
html = io.open(r"G:\Outros computadores\Meu computador (1)\Charles\tce-mg-contratacoes-diretas\00_CONTROLE\_tmp_comprasmg_resultado.html", encoding="latin-1", errors="replace").read()

def corpo_fn(nome):
    m = re.search(r"function\s+" + re.escape(nome) + r"\s*\([^)]*\)\s*\{", html)
    if not m:
        return "(nao achou)"
    s = m.start(); depth = 0; i = s; e = s
    while i < len(html):
        c = html[i]
        if c == "{": depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                e = i + 1; break
        i += 1
    return html[s:e]

for fn in ["validarComCaptchaSeNecessario_", "podeSubmeterFormularioPesquisaValidacaoDatas",
           "executarTratamentoDeRespostaDemorada", "antesOnclickDoLink"]:
    print("==== " + fn + " ====")
    print(corpo_fn(fn)[:1800])
    print()