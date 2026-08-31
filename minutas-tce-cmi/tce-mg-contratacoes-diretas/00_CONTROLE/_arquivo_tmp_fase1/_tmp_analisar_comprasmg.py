# -*- coding: utf-8 -*-
import io, re
html = io.open(r"G:\Outros computadores\Meu computador (1)\Charles\tce-mg-contratacoes-diretas\00_CONTROLE\_tmp_comprasmg_resultado.html", encoding="latin-1", errors="replace").read()
for kw in ["Nenhum registro", "nenhum", "encontrad", "Processo(s)", "processos encontrados", "N.", "Processo", "TOTAL", "quantidade", "resultado", "caption"]:
    idxs = [m.start() for m in re.finditer(re.escape(kw), html, re.I)]
    print(kw, "->", len(idxs))
print("=== contexto tabConsultaProcessoCompra (todas) ===")
for mm in re.finditer(r"tabConsultaProcessoCompra", html):
    s = max(0, mm.start() - 100)
    e = min(len(html), mm.end() + 400)
    print("----")
    print(html[s:e].replace("\n", " ")[:500])