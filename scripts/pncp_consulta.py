#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pncp_consulta.py — Consulta ao Portal Nacional de Contratações Públicas (PNCP).

Mantém a busca textual como fallback e adiciona a API pública de dados abertos
em `https://pncp.gov.br/api/consulta/v1/...`, com paginação, filtros e coleta
opcional de itens/resultados para tentar identificar preço unitário homologado.

Parser defensivo: campo ausente vira "", nunca dado inventado.
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
from pathlib import Path
from typing import Any, Optional

PNCP_PORTAL_URL = "https://pncp.gov.br"
PNCP_API_BASE_URL = os.environ.get("PNCP_API_BASE_URL", "https://pncp.gov.br/api").rstrip("/")
PNCP_SEARCH_PATH = os.environ.get("PNCP_SEARCH_PATH", "/search/")
PNCP_CONSULTA_BASE_URL = os.environ.get(
    "PNCP_CONSULTA_BASE_URL",
    "https://pncp.gov.br/api/consulta/v1",
).rstrip("/")
PNCP_ORGAOS_BASE_URL = os.environ.get(
    "PNCP_ORGAOS_BASE_URL",
    "https://pncp.gov.br/api/pncp/v1",
).rstrip("/")
USER_AGENT = os.environ.get(
    "PNCP_USER_AGENT",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
)
TIMEOUT = int(os.environ.get("PNCP_TIMEOUT", "25"))


def _agora_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _timestamp_arquivo() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def _primeiro(d: dict, *chaves: str, default: Any = "") -> Any:
    """Retorna o primeiro valor presente e não-vazio entre as chaves candidatas."""
    for k in chaves:
        if k in d and d[k] not in (None, ""):
            return d[k]
    return default


def _http_get_json(url: str) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


def _extrair_lista(dados: Any) -> list[dict]:
    """Extrai lista de registros de esquemas comuns do PNCP."""
    if isinstance(dados, list):
        return [item for item in dados if isinstance(item, dict)]
    if not isinstance(dados, dict):
        return []
    for chave in ("data", "items", "itens", "results", "resultado", "content"):
        valor = dados.get(chave)
        if isinstance(valor, list):
            return [item for item in valor if isinstance(item, dict)]
    return []


def _total_resposta(dados: Any) -> Any:
    if not isinstance(dados, dict):
        return None
    return _primeiro(dados, "total", "totalRegistros", "totalElements", "count", default=None)


def _registrar_evidencia(pasta: Optional[Path], tipo: str, url: str, dados: Any, total: Any) -> None:
    """Grava JSON bruto e consultas.log, quando solicitado."""
    if pasta is None:
        return
    pasta.mkdir(parents=True, exist_ok=True)
    destino = pasta / f"pncp-{tipo}-{_timestamp_arquivo()}.json"
    destino.write_text(json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    log = pasta / "consultas.log"
    with log.open("a", encoding="utf-8") as f:
        f.write(f"{_agora_iso()};{tipo};total={total};url={url}\n")


def _montar_link(item: dict) -> str:
    """Monta o link público do edital/contratação quando houver campos suficientes."""
    cnpj = _primeiro(item, "orgao_cnpj", "cnpj", "cnpj_orgao", "cnpjOrgao", "orgaoEntidade.cnpj", default="")
    orgao_entidade = item.get("orgaoEntidade")
    if not cnpj and isinstance(orgao_entidade, dict):
        cnpj = _primeiro(orgao_entidade, "cnpj", "cnpjOrgao", default="")
    ano = _primeiro(item, "ano", "ano_compra", "anoCompra", default="")
    seq = _primeiro(
        item,
        "numero_sequencial",
        "sequencial",
        "numero_sequencial_compra",
        "sequencialCompra",
        "numeroSequencialCompra",
        default="",
    )
    if cnpj and ano and seq:
        return f"{PNCP_PORTAL_URL}/app/editais/{cnpj}/{ano}/{seq}"
    url = _primeiro(item, "item_url", "url", "link", "uri", default="")
    if url:
        if url.startswith("http"):
            return url
        if url.startswith("/compras/"):
            url = url.replace("/compras/", "/app/editais/", 1)
        return PNCP_PORTAL_URL + url
    return ""


def _normalizar_item(item: dict) -> dict:
    """Extrai registro padronizado de contratação PNCP, de forma defensiva."""
    orgao_entidade = item.get("orgaoEntidade") if isinstance(item.get("orgaoEntidade"), dict) else {}
    unidade = item.get("unidadeOrgao") if isinstance(item.get("unidadeOrgao"), dict) else {}
    cnpj = _primeiro(item, "orgao_cnpj", "cnpj", "cnpj_orgao", "cnpjOrgao", default="")
    if not cnpj:
        cnpj = _primeiro(orgao_entidade, "cnpj", default="")
    ano = _primeiro(item, "ano", "ano_compra", "anoCompra", default="")
    sequencial = _primeiro(
        item,
        "numero_sequencial",
        "sequencial",
        "numero_sequencial_compra",
        "sequencialCompra",
        "numeroSequencialCompra",
        default="",
    )
    return {
        "fonte": "PNCP",
        "objeto_encontrado": _primeiro(
            item,
            "description",
            "objeto",
            "objetoCompra",
            "title",
            "descricao",
            "ementa",
        ),
        "orgao": _primeiro(item, "orgao_nome", "nome_orgao", "orgao", "razao_social", default="")
        or _primeiro(orgao_entidade, "razaoSocial", "nome", default=""),
        "unidade": _primeiro(item, "unidade_nome", "nome_unidade", "unidade", default="")
        or _primeiro(unidade, "nomeUnidade", "nome", default=""),
        "municipio": _primeiro(item, "municipio_nome", "municipio", "nome_municipio", default="")
        or _primeiro(unidade, "municipioNome", "municipio", default=""),
        "uf": _primeiro(item, "uf", "sigla_uf", "estado", default="")
        or _primeiro(unidade, "ufSigla", "uf", default=""),
        "modalidade": _primeiro(
            item,
            "modalidade_licitacao_nome",
            "modalidade",
            "modalidade_nome",
            "modalidadeNome",
            "modalidadeContratacaoNome",
        ),
        "numero_contratacao": _primeiro(
            item,
            "numero_controle_pncp",
            "numeroControlePNCP",
            "numero_controle",
            "numero",
            "id",
        ),
        "data": _primeiro(
            item,
            "data_publicacao_pncp",
            "dataPublicacaoPncp",
            "data_publicacao",
            "dataPublicacao",
            "dataAberturaProposta",
            "data",
        ),
        "valor_total": _primeiro(item, "valor_global", "valorTotalEstimado", "valor_total", "valorTotal", "valor"),
        "valor_unitario": _primeiro(item, "valor_unitario", "valorUnitario", "valorUnitarioHomologado"),
        "quantidade": _primeiro(item, "quantidade", "qtd"),
        "unidade_medida": _primeiro(item, "unidade_medida", "unidade_fornecimento", "und"),
        "link": _montar_link(item),
        "cnpj": cnpj,
        "ano": ano,
        "sequencial": sequencial,
        "_campos_brutos": list(item.keys()),
    }


def _normalizar_item_compra(item: dict) -> dict:
    """Normaliza item de compra e tenta priorizar preço unitário homologado."""
    valor_unitario = _primeiro(
        item,
        "valorUnitarioHomologado",
        "valorUnitarioResultado",
        "valorUnitarioEstimado",
        "valorUnitario",
        "valor_unitario",
    )
    return {
        "numero_item": _primeiro(item, "numeroItem", "numero_item", "item", default=""),
        "descricao": _primeiro(item, "descricao", "descricaoItem", "itemDescricao", "materialOuServicoNome"),
        "quantidade": _primeiro(item, "quantidade", "quantidadeItem", "qtd"),
        "unidade_medida": _primeiro(item, "unidadeMedida", "unidade_medida", "unidadeFornecimento"),
        "valor_unitario": valor_unitario,
        "valor_total": _primeiro(item, "valorTotal", "valorTotalHomologado", "valorTotalEstimado"),
        "situacao": _primeiro(item, "situacao", "situacaoCompraItemNome", "resultado"),
        "_campos_brutos": list(item.keys()),
    }


def _url_textual(objeto: str, data_inicial: Optional[str], data_final: Optional[str], uf: Optional[str], tipos_documento: str, max_itens: int) -> str:
    params = {
        "q": objeto,
        "tipos_documento": tipos_documento,
        "ordenacao": "-data",
        "pagina": "1",
        "tam_pagina": str(max(1, min(max_itens, 50))),
    }
    if uf:
        params["uf"] = uf.upper()
    if data_inicial:
        params["data_inicial"] = data_inicial
    if data_final:
        params["data_final"] = data_final
    return f"{PNCP_API_BASE_URL}{PNCP_SEARCH_PATH}?" + urllib.parse.urlencode(params)


def consultar_pncp_textual(
    objeto: str,
    *,
    data_inicial: Optional[str] = None,
    data_final: Optional[str] = None,
    uf: Optional[str] = None,
    tipos_documento: str = "edital",
    max_itens: int = 10,
    evidencia: Optional[Path] = None,
) -> dict:
    """Consulta a busca textual do PNCP e devolve resultados padronizados."""
    data_consulta = _agora_iso()
    url = _url_textual(objeto, data_inicial, data_final, uf, tipos_documento, max_itens)
    base = {
        "fonte": "PNCP",
        "modo": "busca_textual",
        "objeto_pesquisado": objeto,
        "url_consultada": url,
        "data_consulta": data_consulta,
        "total": None,
        "itens": [],
        "erro": None,
    }
    try:
        dados = _http_get_json(url)
        _registrar_evidencia(evidencia, "busca-textual", url, dados, _total_resposta(dados))
    except urllib.error.HTTPError as e:
        base["erro"] = f"HTTP {e.code} ao consultar o PNCP: {e.reason}."
        return base
    except urllib.error.URLError as e:
        base["erro"] = f"Falha de rede ao consultar o PNCP: {e.reason}. Tente novamente ou use o modo manual."
        return base
    except Exception as e:  # noqa: BLE001
        base["erro"] = f"Erro inesperado na consulta textual ao PNCP: {e}"
        return base

    itens_brutos = _extrair_lista(dados)
    base["total"] = _total_resposta(dados)
    if not itens_brutos:
        base["erro"] = "Consulta textual sem resultados ou com esquema inesperado."
        base["_resposta_chaves"] = list(dados.keys()) if isinstance(dados, dict) else type(dados).__name__
        return base
    base["itens"] = [_normalizar_item(it) for it in itens_brutos]
    return base


def _url_consulta_publicacao(
    *,
    data_inicial: Optional[str],
    data_final: Optional[str],
    uf: Optional[str],
    municipio: Optional[str],
    modalidade: Optional[str],
    pagina: int,
    tamanho_pagina: int,
) -> str:
    params: dict[str, str] = {
        "pagina": str(pagina),
        "tamanhoPagina": str(tamanho_pagina),
    }
    if data_inicial:
        params["dataInicial"] = data_inicial
    if data_final:
        params["dataFinal"] = data_final
    if uf:
        params["uf"] = uf.upper()
    if municipio:
        if municipio.isdigit():
            params["codigoMunicipioIbge"] = municipio
        else:
            params["municipioNome"] = municipio
    if modalidade:
        if modalidade.isdigit():
            params["codigoModalidadeContratacao"] = modalidade
        else:
            params["modalidadeNome"] = modalidade
    return f"{PNCP_CONSULTA_BASE_URL}/contratacoes/publicacao?" + urllib.parse.urlencode(params)


def _compatibilidade_textual(item: dict, objeto: str) -> bool:
    if not objeto:
        return True
    alvo = objeto.lower()
    texto = " ".join(
        str(item.get(chave, ""))
        for chave in ("objeto_encontrado", "orgao", "modalidade", "numero_contratacao")
    ).lower()
    termos = [parte for parte in re_split_objeto(alvo) if len(parte) >= 4]
    return any(termo in texto for termo in termos) if termos else alvo in texto


def re_split_objeto(texto: str) -> list[str]:
    return [parte.strip() for parte in texto.replace("/", " ").replace("-", " ").split()]


def consultar_api_publicacao(
    objeto: str,
    *,
    data_inicial: Optional[str] = None,
    data_final: Optional[str] = None,
    uf: Optional[str] = None,
    municipio: Optional[str] = None,
    modalidade: Optional[str] = None,
    max_itens: int = 10,
    evidencia: Optional[Path] = None,
) -> dict:
    """Consulta `/api/consulta/v1/contratacoes/publicacao` com paginação."""
    data_consulta = _agora_iso()
    itens: list[dict] = []
    erros: list[str] = []
    pagina = 1
    tamanho = min(max(max_itens, 1), 50)
    total_reportado = None
    ultima_url = ""
    while len(itens) < max_itens:
        url = _url_consulta_publicacao(
            data_inicial=data_inicial,
            data_final=data_final,
            uf=uf,
            municipio=municipio,
            modalidade=modalidade,
            pagina=pagina,
            tamanho_pagina=tamanho,
        )
        ultima_url = url
        try:
            dados = _http_get_json(url)
            total_reportado = _total_resposta(dados)
            _registrar_evidencia(evidencia, "contratacoes", url, dados, total_reportado)
        except urllib.error.HTTPError as e:
            erros.append(f"HTTP {e.code} ao consultar dados abertos PNCP: {e.reason}.")
            break
        except urllib.error.URLError as e:
            erros.append(f"Falha de rede ao consultar dados abertos PNCP: {e.reason}.")
            break
        except Exception as e:  # noqa: BLE001
            erros.append(f"Erro inesperado nos dados abertos PNCP: {e}")
            break
        brutos = _extrair_lista(dados)
        if not brutos:
            break
        for bruto in brutos:
            normalizado = _normalizar_item(bruto)
            if _compatibilidade_textual(normalizado, objeto):
                itens.append(normalizado)
            if len(itens) >= max_itens:
                break
        pagina += 1
        if len(brutos) < tamanho:
            break
    return {
        "fonte": "PNCP",
        "modo": "api_consulta_v1",
        "objeto_pesquisado": objeto,
        "url_consultada": ultima_url,
        "data_consulta": data_consulta,
        "total": total_reportado,
        "itens": itens[:max_itens],
        "erro": "; ".join(erros) if erros else None,
    }


def consultar_itens_compra(cnpj: str, ano: str, sequencial: str, *, evidencia: Optional[Path] = None) -> list[dict]:
    """Consulta itens de uma compra em `/api/pncp/v1/orgaos/.../itens`."""
    if not (cnpj and ano and sequencial):
        return []
    url = f"{PNCP_ORGAOS_BASE_URL}/orgaos/{cnpj}/compras/{ano}/{sequencial}/itens"
    try:
        dados = _http_get_json(url)
        _registrar_evidencia(evidencia, "itens", url, dados, _total_resposta(dados))
    except Exception:
        return []
    return [_normalizar_item_compra(item) for item in _extrair_lista(dados)]


def consultar_resultados_item(
    cnpj: str,
    ano: str,
    sequencial: str,
    numero_item: str,
    *,
    evidencia: Optional[Path] = None,
) -> list[dict]:
    """Consulta resultados de item quando o endpoint estiver disponível."""
    if not (cnpj and ano and sequencial and numero_item):
        return []
    url = f"{PNCP_ORGAOS_BASE_URL}/orgaos/{cnpj}/compras/{ano}/{sequencial}/itens/{numero_item}/resultados"
    try:
        dados = _http_get_json(url)
        _registrar_evidencia(evidencia, "resultados", url, dados, _total_resposta(dados))
    except Exception:
        return []
    return [_normalizar_item_compra(item) for item in _extrair_lista(dados)]


def enriquecer_com_itens(resultado: dict, *, evidencia: Optional[Path] = None) -> dict:
    """Adiciona itens/resultados e preenche valor unitário quando seguro."""
    for contratacao in resultado.get("itens", []):
        itens = consultar_itens_compra(
            str(contratacao.get("cnpj", "")),
            str(contratacao.get("ano", "")),
            str(contratacao.get("sequencial", "")),
            evidencia=evidencia,
        )
        for item in itens:
            resultados = consultar_resultados_item(
                str(contratacao.get("cnpj", "")),
                str(contratacao.get("ano", "")),
                str(contratacao.get("sequencial", "")),
                str(item.get("numero_item", "")),
                evidencia=evidencia,
            )
            if resultados:
                item["resultados"] = resultados
                if not item.get("valor_unitario"):
                    item["valor_unitario"] = _primeiro(resultados[0], "valor_unitario", default="")
        contratacao["itens_compra"] = itens
        primeiro_com_preco = next((item for item in itens if item.get("valor_unitario")), None)
        if primeiro_com_preco:
            contratacao["valor_unitario"] = primeiro_com_preco.get("valor_unitario", "")
            contratacao["quantidade"] = primeiro_com_preco.get("quantidade", "")
            contratacao["unidade_medida"] = primeiro_com_preco.get("unidade_medida", "")
            contratacao["observacao_itens"] = "Preço unitário obtido da consulta de itens/resultados do PNCP; conferir comparabilidade."
    return resultado


def consultar_pncp(
    objeto: str,
    *,
    data_inicial: Optional[str] = None,
    data_final: Optional[str] = None,
    uf: Optional[str] = None,
    municipio: Optional[str] = None,
    modalidade: Optional[str] = None,
    tipos_documento: str = "edital",
    max_itens: int = 10,
    itens: bool = False,
    evidencia: Optional[str | Path] = None,
    somente_textual: bool = False,
) -> dict:
    """Consulta PNCP por dados abertos e usa busca textual como fallback."""
    evidencia_path = Path(evidencia) if evidencia else None
    usar_api = not somente_textual and any([data_inicial, data_final, uf, municipio, modalidade, itens])
    resultado = None
    if usar_api:
        resultado = consultar_api_publicacao(
            objeto,
            data_inicial=data_inicial,
            data_final=data_final,
            uf=uf,
            municipio=municipio,
            modalidade=modalidade,
            max_itens=max_itens,
            evidencia=evidencia_path,
        )
        if itens and resultado.get("itens"):
            resultado = enriquecer_com_itens(resultado, evidencia=evidencia_path)
    if not resultado or not resultado.get("itens"):
        fallback = consultar_pncp_textual(
            objeto,
            data_inicial=data_inicial,
            data_final=data_final,
            uf=uf,
            tipos_documento=tipos_documento,
            max_itens=max_itens,
            evidencia=evidencia_path,
        )
        if resultado and resultado.get("erro"):
            fallback["erro_api_consulta"] = resultado.get("erro")
        return fallback
    return resultado


def _chave_dedupe(item: dict) -> str:
    """Chave de deduplicação de contratações entre palavras-chave/páginas."""
    numero = str(item.get("numero_contratacao", "")).strip()
    if numero:
        return f"num:{numero}"
    link = str(item.get("link", "")).strip()
    if link:
        return f"link:{link}"
    # Sem número nem link: usa órgão + objeto (defensivo, evita falso duplicado).
    return "of:" + (str(item.get("orgao", "")) + "|" + str(item.get("objeto_encontrado", ""))).strip().lower()


def consultar_pncp_multi(
    palavras_chave: list[str],
    *,
    data_inicial: Optional[str] = None,
    data_final: Optional[str] = None,
    uf: Optional[str] = None,
    municipio: Optional[str] = None,
    modalidade: Optional[str] = None,
    tipos_documento: str = "edital",
    max_por_termo: int = 10,
    max_total: int = 30,
    evidencia: Optional[str | Path] = None,
    somente_textual: bool = False,
) -> dict:
    """Consulta o PNCP para VÁRIAS palavras-chave e deduplica os resultados.

    Reaproveita `consultar_pncp` por termo (sem inventar endpoint) e junta os
    itens, eliminando duplicatas por número de controle/link. A `modalidade`
    NÃO é aplicada por padrão (fica como metadado), atendendo à pesquisa de
    contratações similares independente de modalidade. Cada item recebe o campo
    `termo_origem` com a palavra-chave que o localizou.
    """
    data_consulta = _agora_iso()
    termos = [t.strip() for t in palavras_chave if t and t.strip()]
    itens: list[dict] = []
    vistos: set[str] = set()
    consultas: list[dict] = []
    erros: list[str] = []
    for termo in termos:
        if len(itens) >= max_total:
            break
        res = consultar_pncp(
            termo,
            data_inicial=data_inicial,
            data_final=data_final,
            uf=uf,
            municipio=municipio,
            modalidade=modalidade,
            tipos_documento=tipos_documento,
            max_itens=max_por_termo,
            evidencia=evidencia,
            somente_textual=somente_textual,
        )
        consultas.append({
            "termo": termo,
            "modo": res.get("modo"),
            "url_consultada": res.get("url_consultada"),
            "total": res.get("total"),
            "erro": res.get("erro"),
        })
        if res.get("erro"):
            erros.append(f"{termo}: {res['erro']}")
        for it in res.get("itens", []):
            chave = _chave_dedupe(it)
            if chave in vistos:
                continue
            vistos.add(chave)
            it = dict(it)
            it["termo_origem"] = termo
            itens.append(it)
            if len(itens) >= max_total:
                break
    return {
        "fonte": "PNCP",
        "modo": "multi_palavra_chave",
        "termos_pesquisados": termos,
        "data_consulta": data_consulta,
        "consultas": consultas,
        "total_dedup": len(itens),
        "itens": itens[:max_total],
        "erro": "; ".join(erros) if erros else None,
    }


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Consulta contratações similares no PNCP.")
    ap.add_argument("--objeto", required=True, help="Termo principal do objeto.")
    ap.add_argument("--data-inicial", help="AAAA-MM-DD (opcional; ativa dados abertos).")
    ap.add_argument("--data-final", help="AAAA-MM-DD (opcional; ativa dados abertos).")
    ap.add_argument("--uf", help="UF (ex.: MG).")
    ap.add_argument("--municipio", help="Nome do município ou código IBGE.")
    ap.add_argument("--modalidade", help="Nome ou código da modalidade.")
    ap.add_argument("--tipos-documento", default="edital", help="Fallback textual. Default: edital.")
    ap.add_argument("--max", type=int, default=10, help="Máx. de itens (1-50).")
    ap.add_argument("--itens", action="store_true", help="Consultar itens/resultados das contratações selecionadas.")
    ap.add_argument("--evidencia", help="Pasta para gravar JSON bruto e consultas.log.")
    ap.add_argument("--textual", action="store_true", help="Forçar apenas busca textual antiga.")
    ap.add_argument("--json", action="store_true", help="Saída JSON crua.")
    args = ap.parse_args(argv)

    res = consultar_pncp(
        args.objeto,
        data_inicial=args.data_inicial,
        data_final=args.data_final,
        uf=args.uf,
        municipio=args.municipio,
        modalidade=args.modalidade,
        tipos_documento=args.tipos_documento,
        max_itens=args.max,
        itens=args.itens,
        evidencia=args.evidencia,
        somente_textual=args.textual,
    )

    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0

    print(f"# Consulta PNCP — {res['data_consulta']}")
    print(f"Modo: {res.get('modo', '—')}")
    print(f"Objeto: {res['objeto_pesquisado']}")
    print(f"URL: {res['url_consultada']}")
    if res.get("erro_api_consulta"):
        print(f"\n[ATENÇÃO] Dados abertos: {res['erro_api_consulta']}")
    if res.get("erro"):
        print(f"\n[ATENÇÃO] {res['erro']}")
    print(f"\nItens retornados: {len(res['itens'])} (total reportado: {res['total']})\n")
    for i, it in enumerate(res["itens"], 1):
        print(f"## {i}. {it['orgao'] or '[órgão não informado]'} — {it['municipio']}/{it['uf']}")
        print(f"   Objeto: {it['objeto_encontrado'] or '[sem descrição]'}")
        print(f"   Modalidade: {it['modalidade'] or '—'} | Data: {it['data'] or '—'}")
        print(f"   Nº: {it['numero_contratacao'] or '—'} | Valor total: {it['valor_total'] or '—'}")
        print(f"   Valor unitário: {it['valor_unitario'] or '[não identificado — validação humana]'}")
        print(f"   Link: {it['link'] or '[não informado — não inventar]'}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

