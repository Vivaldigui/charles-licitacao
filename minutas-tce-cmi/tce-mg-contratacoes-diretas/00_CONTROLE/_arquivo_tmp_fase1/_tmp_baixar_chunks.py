# -*- coding: utf-8 -*-
"""Fase 1 - Baixar todos os chunks JS do portal e procurar endpoints de API."""
import os, re, sys, io, urllib.request

BASE_URL = "https://transparencia.tce.mg.gov.br/"
LOCAL = r"G:\Outros computadores\Meu computador (1)\Charles\tce-mg-contratacoes-diretas\00_CONTROLE\_tmp_chunks"
os.makedirs(LOCAL, exist_ok=True)

orig = io.open(r"G:\Outros computadores\Meu computador (1)\Charles\tce-mg-contratacoes-diretas\00_CONTROLE\_tmp_tce_main.js",
               encoding="utf-8", errors="replace").read()
chunks = sorted(set(re.findall(r'\./chunk-[A-Za-z0-9_-]+\.js', orig)))
print(f"{len(chunks)} chunks para baixar")

for c in chunks:
    fname = os.path.basename(c)
    dest = os.path.join(LOCAL, fname)
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        continue
    url = BASE_URL + fname
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 parses-web"})
        with urllib.request.urlopen(req, timeout=60) as r:
            data = r.read()
        with open(dest, "wb") as f:
            f.write(data)
        print(f"  OK {fname} {len(data)} bytes")
    except Exception as e:
        print(f"  ERR {fname}: {e}")

apis = set()
for root, _, files in os.walk(LOCAL):
    for fn in files:
        if not fn.endswith(".js"):
            continue
        js = io.open(os.path.join(root, fn), encoding="utf-8", errors="replace").read()
        # caminhos de API: "/xxxx/..." ou "/api/..."
        for p in re.findall(r'["\'](/[a-zA-Z0-9_./\-]{3,90})["\']', js):
            if any(k in p.lower() for k in ["licitac", "compra", "contrat", "dispe", "inexig", "portal", "consult",
                                             "api", "download", "arquiv", "anexo", "detalhe", "processo", "preg",
                                             "ata", "edital", "public", "extern", "norma", "resoluc", "informativo"]):
                apis.add(p)
        for p in re.findall(r'`(/[a-zA-Z0-9_./$\-]{3,90})`', js):
            if any(k in p.lower() for k in ["licitac", "compra", "contrat", "dispe", "inexig", "portal", "consult",
                                             "api", "download", "arquiv", "anexo", "detalhe", "processo"]):
                apis.add(p)

print("\n=== Caminhos de API candidatos ===")
for a in sorted(apis):
    print("  ", a)