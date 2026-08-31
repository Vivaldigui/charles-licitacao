# -*- coding: utf-8 -*-
"""01_descobrir_normas.py — Descoberta e coleta de atos normativos do TCE-MG (Fase 1/2).

Fonte: TCLEGIS (https://tclegis.tce.mg.gov.br) + pagina oficial de Atos Normativos.

Fase 1 deste script: NUCLEO INICIAL — lista curada de atos encontrados em
https://www.tce.mg.gov.br/Noticia/Detalhe/30 (Atos Normativos TCEMG - licitacoes/contratacoes).
Fase 2: busca completa no TCLEGIS por assuntos (inexigibilidade, ETP, TR, pesquisa de precos...).

Uso:
    python scripts/01_descobrir_normas.py            # coleta o nucleo inicial
    python scripts/01_descobrir_normas.py --busca    # tenta busca no TCLEGIS (experimental)
"""
import argparse
import hashlib
import io
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NORMA_DIR = os.path.join(ROOT, "01_ATOS_NORMATIVOS")
CONTROLE = os.path.join(ROOT, "00_CONTROLE")
VIG = os.path.join(NORMA_DIR, "vigentes")
REV = os.path.join(NORMA_DIR, "revogados")
SNC = os.path.join(NORMA_DIR, "situacao_nao_confirmada")
for d in (VIG, REV, SNC, os.path.join(CONTROLE, "hashes")):
    os.makedirs(d, exist_ok=True)

UA = "TCE-MG-contratacoes-diretas/0.1 (pesquisa publica; uso institucional)"
TCE_URL = "https://tclegis.tce.mg.gov.br"

# ---------------------------------------------------------------------------
# Nucleo: atos identificados na pagina oficial (tce.mg.gov.br/Atos Normativos)
# e confirmados no TCLEGIS.  id_tclegis = chave de detalhe.
# situacao: vigente_confirmada / alterada / revogada_confirmada / situacao_nao_confirmada
# A classificação VEM da evidência (campo VIDE/link revogação no TCLEGIS), nunca de chute.
# 'alteracoes' lista os atos que alteram este ato (id_tclegis deles, quando visto).
# 'altera' aponta o ato original alterado por este ato (ato novo = ato alterador).
# Todos os IDs abaixo foram verificados manualmente no TCLEGIS (GET /Home/Detalhe/{id}),
# com a ementa conferida em 2026-08-09.
# ---------------------------------------------------------------------------
NUCLEO = [
    # ---- atos matrizes sobre contratação (Lei 14.133/2021) ----
    dict(id="83-2023-transicao", tclegis="1141937", tipo="Portaria", numero="83/PRES./2023",
         ementa="Dispõe sobre o regime de transição de que trata o art. 191 da Lei Federal nº 14.133/2021.",
         situacao="situacao_nao_confirmada", alteracoes=[]),
    dict(id="1-2024-pca", tclegis="1142001", tipo="Portaria", numero="1/PRES./2024",
         ementa="Dispõe sobre o Plano de Contratações Anual.",
         situacao="alterada",
         alteracoes=[("1142041", "Portaria 14/PRES./2024"), ("1142608", "Portaria 26/PRES./2025"),
                     ("1143165", "Portaria 22/PRES./2026")]),
    dict(id="2-2024-dispensa-art75", tclegis="1142002", tipo="Portaria", numero="2/PRES./2024",
         ementa="Contratação direta por dispensa de licitação (art. 75, I e II, Lei 14.133/2021).",
         situacao="alterada",
         alteracoes=[("1142983", "Portaria 141/PRES./2025")]),
    dict(id="8-2024-agente-contratacao", tclegis="1142025", tipo="Portaria", numero="8/PRES./2024",
         ementa="Agente de contratação, equipe de apoio, comissão de contratação, gestor e fiscal de contrato.",
         situacao="alterada",
         alteracoes=[("1142723", "Portaria 60/PRES./2025")]),
    dict(id="9-2024-etp", tclegis="1142024", tipo="Portaria", numero="9/PRES./2024",
         ementa="Elaboração de Estudo Técnico Preliminar (ETP).",
         situacao="alterada",
         alteracoes=[("1142586", "Portaria 20/PRES./2025")]),
    dict(id="43-2024-registro-precos", tclegis="1142265", tipo="Portaria", numero="43/PRES./2024",
         ementa="Regulamenta o sistema de registro de preços (Lei 14.133/2021).",
         situacao="situacao_nao_confirmada", alteracoes=[]),
    dict(id="os-4-2024-dispensa-param-legal", tclegis="1142053", tipo="Ordem de Serviço", numero="4/PRES./2024",
         ementa="Dispensa a análise jurídica em processo de contratação nas hipóteses que menciona.",
         situacao="situacao_nao_confirmada", alteracoes=[]),
    dict(id="res-6-2024-bens-comuns-luxo", tclegis="1142355", tipo="Resolução", numero="06/2024",
         ementa="Enquadramento de bens nas categorias de qualidade comum e de luxo.",
         situacao="situacao_nao_confirmada", alteracoes=[]),
    dict(id="res-7-2024-sancoes", tclegis="1142356", tipo="Resolução", numero="07/2024",
         ementa="Responsabilização e aplicação de sanções em licitações e contratos administrativos.",
         situacao="situacao_nao_confirmada", alteracoes=[]),
    # ---- atos alteradores encontrados via busca "termos" + VIDE ----
    dict(id="141-2025-altera-dispensa", tclegis="1142983", tipo="Portaria", numero="141/PRES./2025",
         ementa="Altera a Portaria 02/PRES./2024 (contratação direta por dispensa, art. 75, I e II).",
         situacao="situacao_nao_confirmada", alteracoes=[],
         altera="2-2024-dispensa-art75"),
    dict(id="60-2025-altera-agente", tclegis="1142723", tipo="Portaria", numero="60/PRES./2025",
         ementa="Altera a Portaria 08/PRES./2024 (agente de contratação, equipe, comissão, gestor e fiscal).",
         situacao="situacao_nao_confirmada", alteracoes=[],
         altera="8-2024-agente-contratacao"),
    dict(id="20-2025-altera-etp", tclegis="1142586", tipo="Portaria", numero="20/PRES./2025",
         ementa="Altera a Portaria 09/PRES./2024 (elaboração de ETP).",
         situacao="situacao_nao_confirmada", alteracoes=[],
         altera="9-2024-etp"),
    dict(id="14-2024-altera-pca", tclegis="1142041", tipo="Portaria", numero="14/PRES./2024",
         ementa="Altera a Portaria 1/PRES./2024 (PCA).",
         situacao="situacao_nao_confirmada", alteracoes=[],
         altera="1-2024-pca"),
    dict(id="26-2025-altera-pca", tclegis="1142608", tipo="Portaria", numero="26/PRES./2025",
         ementa="Altera a Portaria 1/PRES./2024 (PCA).",
         situacao="situacao_nao_confirmada", alteracoes=[],
         altera="1-2024-pca"),
    dict(id="22-2026-altera-pca", tclegis="1143165", tipo="Portaria", numero="22/PRES./2026",
         ementa="Altera a Portaria 1/PRES./2024 (PCA).",
         situacao="situacao_nao_confirmada", alteracoes=[],
         altera="1-2024-pca"),
    # ---- envio de informações de licitações ao TCE (SICOM) ----
    dict(id="in-2-2023-sicom-licitacoes", tclegis="1141996", tipo="Instrução Normativa", numero="02/2023",
         ementa="Remessa e prazos de envio de informações e documentos de procedimentos licitatórios (Módulo Edital e Licitação do SICOM).",
         situacao="alterada",
         alteracoes=[("1142380", "Instrução Normativa 01/2024")]),
    dict(id="in-1-2024-altera-sicom", tclegis="1142380", tipo="Instrução Normativa", numero="01/2024",
         ementa="Altera a IN 02/2023 (envio de informações e documentos relativos a procedimentos licitatórios pelo SICOM).",
         situacao="situacao_nao_confirmada", alteracoes=[],
         altera="in-2-2023-sicom-licitacoes"),
    # ---- ato organizacional ligado à fase preparatória (qualificação econômico-financeira) ----
    dict(id="85-2025-comissao-qualif-ecofin", tclegis="1142812", tipo="Portaria", numero="85/PRES./2025",
         ementa="Institui a Comissão de Análise da Qualificação Econômico-financeira das Licitações do TCE-MG.",
         situacao="situacao_nao_confirmada", alteracoes=[]),
]

NORMAS_JSON = os.path.join(NORMA_DIR, "indice_normas.json")
NORMAS_CSV = os.path.join(NORMA_DIR, "indice_normas.csv")


def var_chunks_variants():
    """Variantes de texto do PDF para baixar (Compilado deve ser prioridade)."""
    return ["Compilado", "Completo", "Original"]


def fetch(url, data=None, headers=None, timeout=60, retries=3):
    """GET/POST simples com retry/backoff e User-Agent identificável."""
    h = {"User-Agent": UA}
    if headers:
        h.update(headers)
    last = None
    for i in range(retries):
        try:
            if data is None:
                req = urllib.request.Request(url, headers=h)
            else:
                req = urllib.request.Request(url, data=data, headers=h)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw = r.read()
                return r.status, dict(r.getheaders()), raw
        except Exception as e:
            last = e
            wait = 1.5 * (2 ** i)
            print(f"    [retry {i+1}] {e} ... dorme {wait:.1f}s")
            time.sleep(min(wait, 8))
    raise last


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def caminho_relativo(fn):
    """Caminho portável, relativo à raiz da base."""
    return os.path.relpath(fn, ROOT).replace("\\", "/")


def parse_detalhe(html):
    """Extrai metadados da pagina Detalhe do TCLEGIS."""
    m = re.search(r'<tr>\s*<td[^>]*>\s*([^<]{5,200}?)(?:</td>)', html, re.S)
    # titulo vem antes: "PORTARIA nº ..."
    out = {}
    t = re.search(r'<td[^>]*>\s*([A-ZÀ-ſ][^<]{5,180}?)\s*</td>', html)
    out["titulo"] = t.group(1).strip() if t else None
    em = re.search(r'<div class="acDivChild">\s*([\s\S]*?)</div>', html)
    if em:
        txt = re.sub(r"<[^>]+>", " ", em.group(1))
        out["ementa"] = re.sub(r"\s+", " ", txt).strip()[:400]
    fo = re.search(r'FONTE:\s*</div>\s*<div class="acDivChild">\s*([\s\S]*?)</div>', html)
    if fo:
        out["fonte"] = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", fo.group(1))).strip()[:300]
    # VIDE -> relacoes
    vides = re.findall(r"Detalhe/(\d+)[^>]*>([^<]*)", html)
    out["vides"] = []
    for vid, txt in vides:
        if vid != "":
            out["vides"].append({"id": vid, "texto": re.sub(r"\s+", " ", txt).strip()[:200]})
    # download PDFs
    out["pdfs"] = re.findall(r"value=\"(/Home/DownloadPDF\w+?/(\d+))\"", html)
    # indexacao
    ix = re.search(r'INDEXAÇÃO:.*?<div class="acDivChild">\s*([\s\S]*?)</div>', html, re.S)
    if ix:
        out["indexacao"] = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", ix.group(1))).strip()[:400]
    return out


def coleta_ato(ato):
    """Baixa detalhe + PDFs e extrai texto. Retorna dict do ato atualizado."""
    did = ato["tclegis"]
    pasta = os.path.join(VIG, ato["id"])
    os.makedirs(pasta, exist_ok=True)
    status, hdrs, raw = fetch(f"{TCE_URL}/Home/Detalhe/{did}")
    html = raw.decode("utf-8", errors="replace")
    meta = parse_detalhe(html)
    print(f"  [{ato['id']}] titulo: {meta.get('titulo')}")
    if meta.get("ementa"):
        print(f"      ementa: {meta['ementa'][:130]}")
    if meta.get("vides"):
        print(f"      VIDE: {meta['vides']}")

    # regra: se a norma esta alterada/revogada, esta pasta vai para o nome -- mas
    # preservamos a chave. A situacao final e reavaliada manualmente.
    baixados = []
    variantes = [
        ("COMPILADO", "/Home/DownloadPDFCompilado/"),
        ("COMPLETO", "/Home/DownloadPDFCompleto/"),
        ("ORIGINAL", "/Home/DownloadPDFOriginal/"),
    ]
    for nome, path in variantes:
        url = f"{TCE_URL}{path}{did}"
        fn = os.path.join(pasta, f"{ato['id']}_{nome}.pdf")
        if os.path.exists(fn) and os.path.getsize(fn) > 0:
            print(f"      ja existe {nome}")
            b = open(fn, "rb").read()
            baixados.append({"variante": nome, "arquivo": caminho_relativo(fn),
                             "sha256": sha256_bytes(b)})
            continue
        try:
            st, h2, raw = fetch(url, timeout=90)
            if st == 200 and raw[:5] == b"%PDF-":
                open(fn, "wb").write(raw)
                print(f"      {nome}: OK {len(raw)} bytes")
                baixados.append({"variante": nome, "arquivo": caminho_relativo(fn),
                                 "sha256": sha256_bytes(raw)})
                # texto
                try:
                    from pypdf import PdfReader
                    rd = PdfReader(io.BytesIO(raw))
                    txt = "\n\n".join((p.extract_text() or "") for p in rd.pages)
                    if txt.strip():
                        open(fn[:-4] + ".md", "w", encoding="utf-8").write(txt)
                        print(f"      {nome}: texto extraído {len(txt)} chars")
                except Exception as e:
                    print(f"      {nome}: sem extracao ({e})")
            elif st == 200:
                print(f"      {nome}: resposta nao-PDF ({raw[:40]!r})")
        except Exception as e:
            print(f"      {nome}: ERRO {e}")
        time.sleep(0.4)

    # proveniencia
    prov = {
        "id_interno": ato["id"], "id_tclegis": did, "url_detalhe": f"{TCE_URL}/Home/Detalhe/{did}",
        "data_hora_download": datetime.now(timezone.utc).isoformat(),
        "http_status": status, "content_type": hdrs.get("Content-Type"),
        "metadata_tclegis": {k: v for k, v in meta.items() if k != "pdfs"},
        "documentos": baixados,
    }
    with open(os.path.join(CONTROLE, "hashes", f"norma_{ato['id']}.json"), "w", encoding="utf-8") as f:
        json.dump(prov, f, ensure_ascii=False, indent=2)
    return {**ato, **meta}


def gera_indices(atos):
    with open(NORMAS_JSON, "w", encoding="utf-8") as f:
        json.dump(atos, f, ensure_ascii=False, indent=2)
    # CSV
    cols = ["id_interno", "tipo", "numero", "ementa", "situacao", "id_tclegis",
            "url_detalhe", "titulo_tclegis", "fonte_tclegis", "vides"]
    with open(NORMAS_CSV, "w", encoding="utf-8-sig", newline="") as f:
        import csv
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for a in atos:
            a = dict(a)
            a["url_detalhe"] = f"{TCE_URL}/Home/Detalhe/{a.get('tclegis')}"
            w.writerow(a)
    print(f"[info] índices gravados: {NORMAS_CSV}")


def preserva_fase2(nucleo_atualizado):
    """Mantém no índice os atos agregados pelos coletores posteriores."""
    if not os.path.exists(NORMAS_JSON):
        return nucleo_atualizado
    with open(NORMAS_JSON, "r", encoding="utf-8") as f:
        existente = json.load(f)
    ids_nucleo = {str(a.get("tclegis")) for a in nucleo_atualizado}
    extras = [a for a in existente if str(a.get("tclegis")) not in ids_nucleo]
    return nucleo_atualizado + extras


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--busca", action="store_true", help="(experimental) tenta busca por assuntos no TCLEGIS")
    ap.add_argument("--so-parse", action="store_true",
                    help="regrava o índice sem baixar; preserva os atos da Fase 2")
    args = ap.parse_args()

    if args.busca:
        print("Busca automática no TCLEGIS: implementação fase 2 (ver diagnóstico).")
        return

    if args.so_parse:
        if os.path.exists(NORMAS_JSON):
            with open(NORMAS_JSON, "r", encoding="utf-8") as f:
                existente = json.load(f)
            ids = {str(a["tclegis"]) for a in NUCLEO}
            nucleo_existente = [a for a in existente if str(a.get("tclegis")) in ids]
            gera_indices(preserva_fase2(nucleo_existente or NUCLEO))
        else:
            gera_indices(NUCLEO)
        return

    print(f"[info] Coletando {len(NUCLEO)} atos do núcleo inicial (TCLEGIS)...")
    atos = []
    for i, ato in enumerate(NUCLEO):
        print(f"[{i+1}/{len(NUCLEO)}] {ato['numero']} — {ato['ementa'][:70]}...")
        try:
            atos.append(coleta_ato(ato))
        except Exception as e:
            print("   ERRO geral:", e)
            atos.append(ato)
    gera_indices(preserva_fase2(atos))
    print("[fim] OK.")


if __name__ == "__main__":
    main()
