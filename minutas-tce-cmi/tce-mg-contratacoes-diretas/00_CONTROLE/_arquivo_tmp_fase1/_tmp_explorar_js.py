# -*- coding: utf-8 -*-
"""Exploracao rapida do bundle JS do Portal da Transparencia TCE-MG (Fase 1)."""
import re, sys, io

path = r"G:\Outros computadores\Meu computador (1)\Charles\tce-mg-contratacoes-diretas\00_CONTROLE\_tmp_tce_main.js"
js = io.open(path, encoding="utf-8", errors="replace").read()
print("len:", len(js))

# Strings entre aspas
m = re.findall(r'["\']([a-zA-Z0-9_\\/.\-]{4,80})["\']', js)
uniq = sorted(set(m))

cand = [u for u in uniq if re.search(
    r'licit|dispen|inexig|preg|contrat|compra|edit|chamada|result|homolog|ata|proposta|arquiv|norma|resoluc',
    u, re.I)]
print("candidatos:", len(cand))
for c in cand[:80]:
    print("   ", c[:110])

print("\n=== nomes de chunks/deps (.js) ===")
for c in uniq:
    if c.endswith(".js") and not c.startswith("http"):
        print("   ", c[:130])

print("\n=== urls completas ===")
for u in sorted(set(re.findall(r'https?://[^"\'() ]+', js))):
    print("   ", u[:150])