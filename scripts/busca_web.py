#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
busca_web.py — Busca complementar na internet para a pesquisa de preços,
priorizando portais oficiais (Lei 14.133/2021, art. 23, III; Portaria 03/2024,
art. 4º, III).

Dois modos:
  1) COM provedor configurado (Google Programmable Search ou SerpAPI):
     executa a busca e devolve resultados reais (título, link, trecho).
  2) SEM provedor (default): gera as CONSULTAS SUGERIDAS e as URLs prontas
     para pesquisa MANUAL no Google. Não inventa resultado algum.

Variáveis de ambiente:
    SEARCH_PROVIDER       google | serpapi | none   (default: none)
    GOOGLE_SEARCH_API_KEY chave da Google Programmable Search API
    GOOGLE_SEARCH_CX      ID do mecanismo (cx) da Google Programmable Search
    SERPAPI_KEY           chave da SerpAPI

REGRAS (ver 07_checklists/regras-pesquisa-de-precos.md):
  - Priorizar .gov.br, .leg.br, portais de transparência, câmaras, prefeituras,
    tribunais e diários oficiais. Evitar marketplaces/blogs como fonte principal.
  - Cada resultado recebe um grau de confiabilidade preliminar (alto/médio/baixo)
    a partir do domínio — é triagem mecânica, NÃO dispensa a análise humana de
    comparabilidade.
  - Sem provedor, NUNCA simular resultados: apenas entregar as consultas e links
    para o humano executar e colar no modo manual.

Uso CLI:
    python busca_web.py --objeto "cadeira de escritório giratória"
    python busca_web.py --objeto "toner HP" --json

Uso como módulo:
    from busca_web import buscar_web, gerar_consultas
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Optional

USER_AGENT = os.environ.get(
    "SEARCH_USER_AGENT",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
)
TIMEOUT = int(os.environ.get("SEARCH_TIMEOUT", "25"))

# Modelos de consulta exigidos pela funcionalidade (o {{OBJETO}} é substituído).
MODELOS_CONSULTA = [
    "{obj} dispensa de licitação",
    "{obj} licitação",
    "{obj} contratação direta",
    "{obj} termo de referência",
    "{obj} contrato",
    "{obj} preço de referência",
    "{obj} site:.gov.br",
    "{obj} site:.leg.br",
    "{obj} portal da transparência",
    "{obj} PNCP",
]

# Domínios oficiais -> confiabilidade preliminar.
DOMINIOS_ALTA = (".gov.br", ".leg.br", ".jus.br", ".mp.br", ".tc.br")
DOMINIOS_MEDIA = ("transparencia", "diariooficial", "doe", "imprensaoficial", "pncp.gov.br")
DOMINIOS_BAIXA = (
    "mercadolivre", "amazon", "americanas", "magazineluiza", "shopee",
    "olx", "blogspot", "wordpress", "facebook", "instagram",
)


def gerar_consultas(objeto: str) -> list[str]:
    """Gera a lista de consultas sugeridas a partir do objeto."""
    return [m.format(obj=objeto.strip()) for m in MODELOS_CONSULTA]


def url_google_manual(consulta: str) -> str:
    """URL de pesquisa manual no Google para a consulta dada."""
    return "https://www.google.com/search?q=" + urllib.parse.quote_plus(consulta)


def confiabilidade_por_dominio(link: str) -> str:
    """Triagem mecânica de confiabilidade a partir do domínio do link."""
    l = (link or "").lower()
    if any(d in l for d in DOMINIOS_BAIXA):
        return "baixo"
    if any(l.split("/")[2].endswith(d) for d in DOMINIOS_ALTA if "//" in l and len(l.split("/")) > 2):
        return "alto"
    if any(d in l for d in DOMINIOS_ALTA):
        return "alto"
    if any(d in l for d in DOMINIOS_MEDIA):
        return "médio"
    return "baixo"


def _http_get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


def _buscar_google(consulta: str, max_itens: int) -> dict:
    key = os.environ.get("GOOGLE_SEARCH_API_KEY", "")
    cx = os.environ.get("GOOGLE_SEARCH_CX", "")
    if not key or not cx:
        return {"erro": "GOOGLE_SEARCH_API_KEY/GOOGLE_SEARCH_CX ausentes.", "itens": []}
    params = {"key": key, "cx": cx, "q": consulta, "num": max(1, min(max_itens, 10))}
    url = "https://www.googleapis.com/customsearch/v1?" + urllib.parse.urlencode(params)
    try:
        dados = _http_get_json(url)
    except Exception as e:  # noqa: BLE001
        return {"erro": f"Google CSE: {e}", "itens": []}
    itens = []
    for it in dados.get("items", []) or []:
        link = it.get("link", "")
        itens.append({
            "titulo": it.get("title", ""),
            "link": link,
            "trecho": it.get("snippet", ""),
            "confiabilidade": confiabilidade_por_dominio(link),
        })
    return {"erro": None, "itens": itens}


def _buscar_serpapi(consulta: str, max_itens: int) -> dict:
    key = os.environ.get("SERPAPI_KEY", "")
    if not key:
        return {"erro": "SERPAPI_KEY ausente.", "itens": []}
    params = {"engine": "google", "q": consulta, "api_key": key, "num": max(1, min(max_itens, 10)), "hl": "pt-BR", "gl": "br"}
    url = "https://serpapi.com/search.json?" + urllib.parse.urlencode(params)
    try:
        dados = _http_get_json(url)
    except Exception as e:  # noqa: BLE001
        return {"erro": f"SerpAPI: {e}", "itens": []}
    itens = []
    for it in dados.get("organic_results", []) or []:
        link = it.get("link", "")
        itens.append({
            "titulo": it.get("title", ""),
            "link": link,
            "trecho": it.get("snippet", ""),
            "confiabilidade": confiabilidade_por_dominio(link),
        })
    return {"erro": None, "itens": itens}


def buscar_web(objeto: str, *, max_por_consulta: int = 5) -> dict:
    """Executa (ou sugere) a busca complementar.

    Retorna estrutura com: provedor usado, consultas, resultados (se houver
    provedor) e/ou links manuais (sempre), além da data da consulta.
    """
    provider = os.environ.get("SEARCH_PROVIDER", "none").lower()
    data_consulta = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    consultas = gerar_consultas(objeto)

    out = {
        "objeto_pesquisado": objeto,
        "provedor": provider,
        "data_consulta": data_consulta,
        "consultas_sugeridas": consultas,
        "links_manuais": [{"consulta": c, "url": url_google_manual(c)} for c in consultas],
        "resultados": [],
        "aviso": None,
    }

    if provider not in ("google", "serpapi"):
        out["aviso"] = (
            "Nenhum provedor de busca configurado (SEARCH_PROVIDER=none). Foram geradas "
            "as consultas e os links para pesquisa MANUAL. Cole os achados no modo manual "
            "(cesta_precos.py --manual)."
        )
        return out

    buscador = _buscar_google if provider == "google" else _buscar_serpapi
    for consulta in consultas:
        res = buscador(consulta, max_por_consulta)
        for it in res["itens"]:
            it["consulta_origem"] = consulta
            it["data_acesso"] = data_consulta
        out["resultados"].extend(res["itens"])
        if res.get("erro"):
            out["aviso"] = res["erro"]
            break

    # Ordena por confiabilidade (alto > médio > baixo) para facilitar a triagem.
    ordem = {"alto": 0, "médio": 1, "baixo": 2}
    out["resultados"].sort(key=lambda r: ordem.get(r.get("confiabilidade"), 3))
    if not out["resultados"] and not out["aviso"]:
        out["aviso"] = "Provedor configurado, mas sem resultados. Sugerir novos termos/ampliar período."
    return out


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Busca complementar em portais oficiais (ou gera consultas manuais).")
    ap.add_argument("--objeto", required=True, help="Objeto da contratação.")
    ap.add_argument("--max", type=int, default=5, help="Máx. de resultados por consulta (com provedor).")
    ap.add_argument("--json", action="store_true", help="Saída JSON crua.")
    args = ap.parse_args(argv)

    res = buscar_web(args.objeto, max_por_consulta=args.max)
    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0

    print(f"# Busca complementar — {res['data_consulta']}")
    print(f"Objeto: {res['objeto_pesquisado']} | Provedor: {res['provedor']}")
    if res["aviso"]:
        print(f"\n[ATENÇÃO] {res['aviso']}")
    print("\n## Consultas sugeridas / links para pesquisa manual:")
    for lm in res["links_manuais"]:
        print(f"  - {lm['consulta']}\n    {lm['url']}")
    if res["resultados"]:
        print("\n## Resultados encontrados (triagem por domínio):")
        for i, it in enumerate(res["resultados"], 1):
            print(f"  {i}. [{it['confiabilidade'].upper()}] {it['titulo']}")
            print(f"     {it['link']}")
            print(f"     {it['trecho']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
