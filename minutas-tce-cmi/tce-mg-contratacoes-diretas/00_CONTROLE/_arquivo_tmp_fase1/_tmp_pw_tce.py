# -*- coding: utf-8 -*-
"""Fase 1 - Renderizar portal da transparencia TCE-MG (public/licitacoes) em navegador real.
Captura a API de licitacoes (fonte=SIAD / Admin) e ve se a tabela renderiza.
"""
import json, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True)
    ctx = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0 Safari/537.36",
                              locale="pt-BR")
    page = ctx.new_page()
    api_hits = []
    def on_response(resp):
        url = resp.url
        if "arabiasaudita" in url or "CompraLicitacao" in url or "p-portal-transparencia" in url:
            try:
                ct = resp.headers.get("content-type", "")
                body = resp.text() if ("json" in ct or resp.status == 200) and resp.status < 400 else ""
                api_hits.append({"url": url[:220], "status": resp.status, "ct": ct, "len": len(body),
                                 "body": body[:3000]})
            except Exception as e:
                api_hits.append({"url": url[:220], "status": resp.status, "ct": "?", "body": "erro:" + str(e)[:200]})
    page.on("response", on_response)
    try:
        page.goto("https://transparencia.tce.mg.gov.br/public/licitacoes", wait_until="domcontentloaded", timeout=90000)
        page.wait_for_timeout(15000)
        html = page.content()
        open(r"G:\Outros computadores\Meu computador (1)\Charles\tce-mg-contratacoes-diretas\00_CONTROLE\_tmp_tce_pw.html", "w", encoding="utf-8").write(html)
        print("html len:", len(html))
        for probe in ["Nenhum registro encontrado", "Total de itens", "Data Atualização", "Dispensa",
                      "Inexigibilidade", "Pregão", "resultado", "captcha", "p-button"]:
            print("[probe]", probe, "->", probe.lower() in html.lower())
        # texto da tabela
        import re
        txt = re.sub(r"<[^>]+>", "|", html)
        txt = re.sub(r"\s+", " ", txt)
        ln = [l for l in txt.split("|") if l.strip() and len(l.strip()) > 3]
        print("\n=== trechos do texto ===")
        for l in ln[:120]:
            print("  ", l.strip()[:110])
    except Exception as e:
        print("[erro]", repr(e)[:500])
    print("\n=== API hits ===")
    for h in api_hits:
        print("---", h["status"], h["ct"], h["len"], h["url"])
    browser.close()