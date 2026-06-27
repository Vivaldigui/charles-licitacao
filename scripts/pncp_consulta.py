#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pncp_consulta.py — Consulta ao Portal Nacional de Contratações Públicas (PNCP)
para localizar contratações similares ao objeto, compondo a pesquisa de preços
(Lei 14.133/2021, art. 23, I e II; Portaria 03/2024, art. 4º, I e II).

Puro stdlib (urllib) — não exige `pip install`. Funciona sem nenhuma chave: o
PNCP expõe dados públicos.

ENDPOINT
--------
Usa a API pública de BUSCA TEXTUAL do PNCP (a mesma que alimenta o portal),
configurável por variável de ambiente:

    PNCP_API_BASE_URL   (default: https://pncp.gov.br/api)
    PNCP_SEARCH_PATH    (default: /search/)

A busca textual aceita o termo do objeto e devolve itens ranqueados por
relevância. Como o esquema de campos do PNCP pode mudar, o parser é DEFENSIVO:
lê os campos por vários nomes possíveis e, se não achar, deixa o campo vazio —
NUNCA inventa valor, órgão, número de contratação ou link.

REGRAS ANTIALUCINAÇÃO (ver 07_checklists/regras-pesquisa-de-precos.md)
  - Sem resultado -> retorna lista vazia + motivo, não preenche nada.
  - Campo ausente na resposta -> fica vazio (""), nunca é "chutado".
  - Toda saída registra a data/hora da consulta e a URL efetivamente chamada,
    para rastreabilidade nos autos.

Uso CLI:
    python pncp_consulta.py --objeto "aquisição de cadeiras de escritório" \
        --data-inicial 2024-01-01 --data-final 2025-12-31 --uf MG --max 10
    python pncp_consulta.py --objeto "toner impressora" --json > pncp.json

Uso como módulo:
    from pncp_consulta import consultar_pncp
    res = consultar_pncp("notebooks", uf="MG", max_itens=10)
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
from typing import Any, Optional

PNCP_API_BASE_URL = os.environ.get("PNCP_API_BASE_URL", "https://pncp.gov.br/api").rstrip("/")
PNCP_SEARCH_PATH = os.environ.get("PNCP_SEARCH_PATH", "/search/")
# O PNCP rejeita User-Agents não-navegador (fecha a conexão). Usamos um UA
# browser-like; é configurável por variável de ambiente se necessário.
USER_AGENT = os.environ.get(
    "PNCP_USER_AGENT",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
)
TIMEOUT = int(os.environ.get("PNCP_TIMEOUT", "25"))


def _primeiro(d: dict, *chaves: str, default: Any = "") -> Any:
    """Retorna o primeiro valor presente e não-vazio entre as chaves candidatas."""
    for k in chaves:
        if k in d and d[k] not in (None, ""):
            return d[k]
    return default


def _montar_link(item: dict) -> str:
    """Tenta montar o link público do edital/contratação a partir dos campos.

    Se houver um campo de URL direto, usa-o. Caso contrário, tenta o padrão
    /app/editais/{cnpj}/{ano}/{sequencial}. Se não houver dados suficientes,
    retorna "" (não inventa)."""
    # Preferimos montar o link público visualizável (/app/editais/...) a partir
    # dos componentes — é o que abre no navegador para o cidadão/agente.
    cnpj = _primeiro(item, "orgao_cnpj", "cnpj", "cnpj_orgao", default="")
    ano = _primeiro(item, "ano", "ano_compra", default="")
    seq = _primeiro(item, "numero_sequencial", "sequencial", "numero_sequencial_compra", default="")
    if cnpj and ano and seq:
        return f"https://pncp.gov.br/app/editais/{cnpj}/{ano}/{seq}"
    # Fallback: usar o item_url da API. Ele vem como "/compras/{cnpj}/{ano}/{seq}";
    # convertemos para a rota pública "/app/editais/..." quando aplicável.
    url = _primeiro(item, "item_url", "url", "link", default="")
    if url:
        if url.startswith("http"):
            return url
        if url.startswith("/compras/"):
            url = url.replace("/compras/", "/app/editais/", 1)
        return "https://pncp.gov.br" + url
    return ""


def _normalizar_item(item: dict) -> dict:
    """Extrai um registro padronizado de um item da busca PNCP, de forma defensiva."""
    return {
        "fonte": "PNCP",
        "objeto_encontrado": _primeiro(item, "description", "objeto", "title", "descricao", "ementa"),
        "orgao": _primeiro(item, "orgao_nome", "nome_orgao", "orgao", "razao_social"),
        "unidade": _primeiro(item, "unidade_nome", "nome_unidade", "unidade"),
        "municipio": _primeiro(item, "municipio_nome", "municipio", "nome_municipio"),
        "uf": _primeiro(item, "uf", "sigla_uf", "estado"),
        "modalidade": _primeiro(item, "modalidade_licitacao_nome", "modalidade", "modalidade_nome"),
        "numero_contratacao": _primeiro(
            item, "numero_controle_pncp", "numero_controle", "numero", "id"
        ),
        "data": _primeiro(
            item, "data_publicacao_pncp", "data_publicacao", "data", "dataPublicacao"
        ),
        "valor_total": _primeiro(item, "valor_global", "valor_total", "valorTotal", "valor"),
        "valor_unitario": _primeiro(item, "valor_unitario", "valorUnitario"),
        "quantidade": _primeiro(item, "quantidade", "qtd"),
        "unidade_medida": _primeiro(item, "unidade_medida", "unidade_fornecimento", "und"),
        "link": _montar_link(item),
        "_campos_brutos": list(item.keys()),  # rastreabilidade: o que veio na resposta
    }


def consultar_pncp(
    objeto: str,
    *,
    data_inicial: Optional[str] = None,
    data_final: Optional[str] = None,
    uf: Optional[str] = None,
    tipos_documento: str = "edital",
    max_itens: int = 10,
) -> dict:
    """Consulta a busca textual do PNCP e devolve resultados padronizados.

    Retorna um dicionário com: parâmetros, url chamada, data da consulta,
    total reportado, lista de itens e (se houver) mensagem de erro/ausência.
    NUNCA levanta exceção para o chamador — erros viram campo 'erro'.
    """
    data_consulta = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    params = {
        "q": objeto,
        "tipos_documento": tipos_documento,
        "ordenacao": "-data",
        "pagina": "1",
        "tam_pagina": str(max(1, min(max_itens, 50))),
    }
    if uf:
        params["uf"] = uf.upper()
    # Campos de período são repassados quando informados; nomes podem variar por versão.
    if data_inicial:
        params["data_inicial"] = data_inicial
    if data_final:
        params["data_final"] = data_final

    url = f"{PNCP_API_BASE_URL}{PNCP_SEARCH_PATH}?" + urllib.parse.urlencode(params)
    base = {
        "fonte": "PNCP",
        "objeto_pesquisado": objeto,
        "parametros": params,
        "url_consultada": url,
        "data_consulta": data_consulta,
        "total": None,
        "itens": [],
        "erro": None,
    }

    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            corpo = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        base["erro"] = f"HTTP {e.code} ao consultar o PNCP: {e.reason}. Verifique PNCP_API_BASE_URL/PNCP_SEARCH_PATH."
        return base
    except urllib.error.URLError as e:
        base["erro"] = f"Falha de rede ao consultar o PNCP: {e.reason}. Tente novamente ou use o modo manual."
        return base
    except Exception as e:  # noqa: BLE001 — robustez: nada deve quebrar a pesquisa
        base["erro"] = f"Erro inesperado na consulta ao PNCP: {e}"
        return base

    try:
        dados = json.loads(corpo)
    except json.JSONDecodeError:
        base["erro"] = "Resposta do PNCP não é JSON válido (a API pode ter mudado). Use o modo manual."
        return base

    # A resposta costuma ser {"items": [...], "total": N}; mas pode variar.
    itens_brutos = None
    if isinstance(dados, dict):
        for chave in ("items", "itens", "results", "resultado", "data"):
            if isinstance(dados.get(chave), list):
                itens_brutos = dados[chave]
                break
        base["total"] = _primeiro(dados, "total", "totalRegistros", "count", default=None)
    elif isinstance(dados, list):
        itens_brutos = dados

    if itens_brutos is None:
        base["erro"] = "Não foi possível localizar a lista de itens na resposta do PNCP (esquema inesperado)."
        base["_resposta_chaves"] = list(dados.keys()) if isinstance(dados, dict) else "lista"
        return base

    base["itens"] = [_normalizar_item(it) for it in itens_brutos if isinstance(it, dict)]
    if not base["itens"]:
        base["erro"] = "Consulta sem resultados para o termo informado. Sugerir novos termos/ampliar período."
    return base


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Consulta contratações similares no PNCP.")
    ap.add_argument("--objeto", required=True, help="Termo principal do objeto.")
    ap.add_argument("--data-inicial", help="AAAA-MM-DD (opcional).")
    ap.add_argument("--data-final", help="AAAA-MM-DD (opcional).")
    ap.add_argument("--uf", help="UF (ex.: MG).")
    ap.add_argument("--tipos-documento", default="edital", help="Default: edital.")
    ap.add_argument("--max", type=int, default=10, help="Máx. de itens (1-50).")
    ap.add_argument("--json", action="store_true", help="Saída JSON crua.")
    args = ap.parse_args(argv)

    res = consultar_pncp(
        args.objeto,
        data_inicial=args.data_inicial,
        data_final=args.data_final,
        uf=args.uf,
        tipos_documento=args.tipos_documento,
        max_itens=args.max,
    )

    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0

    print(f"# Consulta PNCP — {res['data_consulta']}")
    print(f"Objeto: {res['objeto_pesquisado']}")
    print(f"URL: {res['url_consultada']}")
    if res["erro"]:
        print(f"\n[ATENÇÃO] {res['erro']}")
    print(f"\nItens retornados: {len(res['itens'])} (total reportado: {res['total']})\n")
    for i, it in enumerate(res["itens"], 1):
        print(f"## {i}. {it['orgao'] or '[órgão não informado]'} — {it['municipio']}/{it['uf']}")
        print(f"   Objeto: {it['objeto_encontrado'] or '[sem descrição]'}")
        print(f"   Modalidade: {it['modalidade'] or '—'} | Data: {it['data'] or '—'}")
        print(f"   Nº: {it['numero_contratacao'] or '—'} | Valor total: {it['valor_total'] or '—'}")
        print(f"   Link: {it['link'] or '[não informado — não inventar]'}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
