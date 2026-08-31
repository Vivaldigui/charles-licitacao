# -*- coding: utf-8 -*-
"""Fase 1 - Reproduzir consulta Compras MG (orgao 1020) em navegador real com Playwright.
Captura requisicoes de rede e verifica se a grade de resultados renderiza.
"""
import json, sys, io
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from playwright.sync_api import sync_playwright

URL = ("https://www1.compras.mg.gov.br/processocompra/processo/consultaProcessoCompra.html?"
       "orgaoEntidade=1020&metodo=pesquisar&estaPesquisando=true")

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True)
    ctx = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0 Safari/537.36",
                              locale="pt-BR")
    page = ctx.new_page()
    requests_log = []
    def on_response(resp):
        ct = resp.headers.get("content-type", "")
        url = resp.url
        if ".html" in url or "json" in ct or "processocompra" in url and resp.status != 404:
            requests_log.append({"url": url[:200], "status": resp.status, "ct": ct[:60]})
    page.on("response", on_response)
    try:
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(8000)  # deixa o JS rodar
        # tenta clicar em Buscar se presente
        try:
            page.click("a#textoAcaoPesquisa", timeout=4000)
            page.wait_for_timeout(8000)
        except Exception:
            print("[info] botao Buscar nao clicavel; segue")
        html = page.content()
        open(r"G:\Outros computadores\Meu computador (1)\Charles\tce-mg-contratacoes-diretas\00_CONTROLE\_tmp_cmpmg_pw.html", "w", encoding="utf-8").write(html)
        print("[info] html salvo, len=", len(html))
        # verificar elementos
        for probe in ["Nenhum registro encontrado", "IDDOPROCESSO", "quantidadeItems",
                      "captcha", "CAPTCHA", "validarComCaptcha", "Resultado", "radio",
                      "Processo de Compra:", "Nº do processo"]:
            print("[probe]", probe, "->", probe.lower() in html.lower())
    except Exception as e:
        print("[erro]", repr(e)[:400])
    print("\n=== requests observados ===")
    for rl in requests_log:
        print(rl)
    browser.close()