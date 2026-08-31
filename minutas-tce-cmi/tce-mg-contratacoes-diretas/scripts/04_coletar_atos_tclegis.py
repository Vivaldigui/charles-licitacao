# -*- coding: utf-8 -*-
"""04_coletar_atos_tclegis.py — Coleta estruturada dos atos do TCLEGIS (Fase 2).

Parte de ``00_CONTROLE/busca/resultados_busca.json`` (gerado pelo 02) e separa os
atos que já estão no índice (``01_ATOS_NORMATIVOS/indice_normas.json``). Em duas
fases, sempre com evidência real (nunca julgamento por título):

  Fase 1 — TRIAGEM (padrão):
    para cada candidato novo, GET /Home/Detalhe/{id}, grava o HTML cru canonizado
    em ``registros_web/tclegis_detalhe/`` e extrai ementa/indexação/VIDE/pdfs.
    Resultado: ``00_CONTROLE/coleta/candidatos_triagem.json`` (idempotente).

  Fase 2 — COLETA (--coleta):
    para os IDs marcados ``relevante`` na triagem, baixa o PDF (COMPILADO
    prioridade, senão COMPLETO, senão ORIGINAL — que sempre funciona), extrai
    texto para .md, grava em ``01_ATOS_NORMATIVOS/<pasta_canonica>/<id>/``
    (situação ``alterada`` e ``vigente`` → ``vigentes/``; ``revogado`` →
    ``revogados/``; o restante → ``situacao_nao_confirmada/``) e registra
    proveniência + SHA-256 em ``00_CONTROLE/hashes/norma_<id>.json``.
    Não baixa nem cataloga ato classificado ``irrelevante`` — fica documentado
    em ``00_CONTROLE/coleta/descarte.json`` com o motivo.

A classificação de relevância é SEMPRE aprovada por leitura da ementa/indexação
extraída (campo ``classificacao`` na triagem), nunca chute do robo.

Uso:
    python scripts/04_coletar_atos_tclegis.py                # triagem
    python scripts/04_coletar_atos_tclegis.py --coleta       # coleta dos relevantes
    python scripts/04_coletar_atos_tclegis.py --indices      # mescla coletados no índice
    python scripts/04_coletar_atos_tclegis.py --status       # estado da triagem
"""
import argparse
import io
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import (caminho, fetch, grava_evidencia_web, json_dump, le_config,  # noqa: E402
                   pausa_educada, slug)

BASE_TCLEGIS = "https://tclegis.tce.mg.gov.br"


def parse_detalhe(html):
    """Extrai metadados da página Detalhe do TCLEGIS (espelha o 01)."""
    out = {}
    t = re.search(r'<td[^>]*>\s*([A-ZÀ-ſ][^<]{5,180}?)\s*</td>', html)
    out["titulo"] = t.group(1).strip() if t else None
    em = re.search(r'<div class="acDivChild">\s*([\s\S]*?)</div>', html)
    if em:
        out["ementa"] = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", em.group(1))).strip()[:400]
    fo = re.search(r'FONTE:\s*</div>\s*<div class="acDivChild">\s*([\s\S]*?)</div>', html)
    if fo:
        out["fonte"] = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", fo.group(1))).strip()[:300]
    vides = re.findall(r"Detalhe/(\d+)[^>]*>([^<]*)", html)
    out["vides"] = []
    for vid, txt in vides:
        if vid:
            out["vides"].append({"id": vid, "texto": re.sub(r"\s+", " ", txt).strip()[:200]})
    out["pdfs"] = re.findall(r"value=\"(/Home/DownloadPDF\w+?/(\d+))\"", html)
    ix = re.search(r'INDEXAÇÃO:.*?<div class="acDivChild">\s*([\s\S]*?)</div>', html, re.S)
    if ix:
        out["indexacao"] = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", ix.group(1))).strip()[:400]
    return out


# Convenção de pastas do repositório (README): vigentes/ (incl. "alterada",
# ainda em vigor), revogados/, situacao_nao_confirmada/. A situação bruta do
# TCLEGIS nunca vira nome de pasta.
_PASTA_POR_SITUACAO = {
    "vigente": "vigentes", "vigentes": "vigentes",
    "alterada": "vigentes", "alterado": "vigentes",
    "revogado": "revogados", "revogada": "revogados",
    "revogados": "revogados",
    "situacao_nao_confirmada": "situacao_nao_confirmada",
}


def pasta_situacao(situacao):
    s = (situacao or "situacao_nao_confirmada").strip().lower()
    return _PASTA_POR_SITUACAO.get(s, "situacao_nao_confirmada")


def carrega_indice():
    p = caminho("01_ATOS_NORMATIVOS", "indice_normas.json")
    if os.path.exists(p):
        return json.load(open(p, encoding="utf-8"))
    return []


def candidatos_novos():
    """Lista de dicts {id, titulo, termos} ainda fora do índice."""
    idx = carrega_indice()
    ja = {str(i["tclegis"]) for i in idx}
    bus = json.load(open(caminho("00_CONTROLE/busca", "resultados_busca.json"), encoding="utf-8"))
    vistos = {}
    for t in bus["termos"]:
        for r in t["resultados"]:
            if r["id"] not in vistos:
                vistos[r["id"]] = {"id": r["id"], "titulo": r["titulo"], "termos": []}
            vistos[r["id"]]["termos"].append(t["termo"])
    return [v for k, v in sorted(vistos.items(), key=lambda x: int(x[0])) if k not in ja]


def triagem(cfg, forcar=False):
    t = cfg["fontes"]["tclegis"]
    base = t["base"]
    novos = candidatos_novos()
    dest = caminho("00_CONTROLE", "coleta", "candidatos_triagem.json")
    dados = {}
    if os.path.exists(dest) and not forcar:
        dados = json.load(open(dest, encoding="utf-8"))

    print(f"[info] {len(novos)} candidatos novos para triagem")
    for c in novos:
        did = c["id"]
        if did in dados and not forcar:
            print(f"  {did}: já triado (pula) — use --forcar para refazer")
            continue
        st, hdrs, raw = fetch(f"{base}{t['detalhe'].format(id=did)}")
        html = raw.decode("utf-8", "replace")
        reg = grava_evidencia_web(
            "tclegis_detalhe", f"tclegis_detalhe_{did}.html", raw,
            tag=f"tclegis_detalhe:{did}",
            fonte_url=f"{base}{t['detalhe'].format(id=did)}")
        meta = parse_detalhe(html)
        dados[did] = {
            "id_tclegis": did,
            "titulo_busca": c["titulo"],
            "termos": c["termos"],
            "titulo_detalhe": meta.get("titulo"),
            "ementa": meta.get("ementa"),
            "fonte": meta.get("fonte"),
            "indexacao": meta.get("indexacao"),
            "vides": meta.get("vides", []),
            "pdfs": meta.get("pdfs", []),
            "evidencia_html": reg["caminho"],
            "sha256_html": reg["sha256"],
            "classificacao": dados.get(did, {}).get("classificacao"),  # preserva classificação manual
            "motivo": dados.get(did, {}).get("motivo"),
        }
        print(f"  {did}: {meta.get('ementa', '(sem ementa)')[:90]}")
        pausa_educada()
    json_dump(dest, dados)
    print(f"[fim] triagem em {dest}")


def baixa_pdfs_ato(cfg, did, ato_id, situacao, ementa):
    """Baixa as variantes do PDF do ato; retorna lista de documentos."""
    t = cfg["fontes"]["tclegis"]
    base = t["base"]
    pasta = caminho("01_ATOS_NORMATIVOS", pasta_situacao(situacao), ato_id)
    os.makedirs(pasta, exist_ok=True)
    docs = []
    variantes = [
        ("COMPILADO", "/Home/DownloadPDFCompilado/"),
        ("COMPLETO", "/Home/DownloadPDFCompleto/"),
        ("ORIGINAL", "/Home/DownloadPDFOriginal/"),
    ]
    for nome, path in variantes:
        fn = os.path.join(pasta, f"{ato_id}_{nome}.pdf")
        if os.path.exists(fn) and os.path.getsize(fn) > 0:
            b = open(fn, "rb").read()
            docs.append({"variante": nome,
                         "arquivo": os.path.relpath(fn, caminho(".")).replace("\\", "/"),
                         "sha256": sha(b)})
            print(f"      {nome}: já existe")
            continue
        try:
            st, h2, raw = fetch(f"{base}{path}{did}", timeout=90)
            if st == 200 and raw[:5] == b"%PDF-":
                open(fn, "wb").write(raw)
                docs.append({"variante": nome,
                             "arquivo": os.path.relpath(fn, caminho(".")).replace("\\", "/"),
                             "sha256": sha(raw)})
                print(f"      {nome}: OK {len(raw)} bytes")
                try:
                    from pypdf import PdfReader
                    rd = PdfReader(io.BytesIO(raw))
                    txt = "\n\n".join((p.extract_text() or "") for p in rd.pages)
                    if txt.strip():
                        open(fn[:-4] + ".md", "w", encoding="utf-8").write(txt)
                        print(f"      {nome}: texto {len(txt)} chars")
                except Exception as e:
                    print(f"      {nome}: sem extração ({e})")
            elif st == 200:
                print(f"      {nome}: resposta não-PDF ({raw[:40]!r})")
        except Exception as e:
            print(f"      {nome}: ERRO {e}")
        pausa_educada()
    return docs


def coleta(cfg, filtro_situacao=None):
    dest = caminho("00_CONTROLE", "coleta", "candidatos_triagem.json")
    if not os.path.exists(dest):
        sys.exit("Rode a triagem primeiro (sem --coleta).")
    dados = json.load(open(dest, encoding="utf-8"))
    relevantes = {k: v for k, v in dados.items()
                  if v.get("classificacao") in ("relevante", "contexto", "a_conferir")}
    print(f"[info] {len(relevantes)} relevantes para coletar")
    for did, v in sorted(relevantes.items(), key=lambda x: int(x[0])):
        ato_id = v.get("id_interno") or f"tclegis-{did}"
        situacao = v.get("situacao") or "situacao_nao_confirmada"
        if filtro_situacao and situacao != filtro_situacao:
            continue
        print(f"  [{did}] {v.get('ementa','')[:80]}")
        docs = baixa_pdfs_ato(cfg, did, ato_id, situacao, v.get("ementa"))
        prov = {
            "id_interno": ato_id, "id_tclegis": did,
            "url_detalhe": f"{cfg['fontes']['tclegis']['base']}{cfg['fontes']['tclegis']['detalhe'].format(id=did)}",
            "ementa": v.get("ementa"),
            "situacao": situacao,
            "classificacao": v.get("classificacao"),
            "data_hora_download": None,
            "documentos": docs,
        }
        # data_hora simples: use o do sistema
        from datetime import datetime, timezone
        prov["data_hora_download"] = datetime.now(timezone.utc).isoformat()
        json_dump(caminho("00_CONTROLE", "hashes", f"norma_{ato_id}.json"), prov)
    print("[fim] coleta concluída")


# Conectivos que não levam maiúscula em meio ao tipo ("Ordem de Serviço").
_CONECTIVOS = {"da", "das", "de", "do", "dos", "e", "em", "para", "por", "com"}


def _titula(palavras):
    if not palavras:
        return ""
    partes = []
    for i, w in enumerate(palavras):
        if i > 0 and w.lower() in _CONECTIVOS:
            partes.append(w.lower())
        else:
            partes.append(w.capitalize())
    return " ".join(partes)


def parse_tipo_numero(titulo):
    """Deriva (tipo, numero) do título TCLEGIS, sem inventar.

    Ex.: 'PORTARIA nº 000114, de 01/01/2010 - PRESIDÊNCIA' ->
         ('Portaria', '114/2010'). 'REGIMENTO INTERNO nº S/N, de 13/12/2023'
         -> ('Regimento Interno', 'S/N/2023'). 'ORDEM DE SERVIÇO nº 000002, ...'
         -> ('Ordem de Serviço', '02/1997').
    """
    titulo = titulo or ""
    tipo_raw = (re.match(r"^\s*([A-ZÀ-Ź\s]+?)nº", titulo) or [None, ""])[1].strip()
    tipo = _titula(tipo_raw.split()) or "Ato"
    m_num = re.search(r"nº\s*(\d+)", titulo)
    # O TCLEGIS grava a data como DD/MM/AAAA (ex.: 'de 01/01/2010'), por isso
    # três grupos numéricos; sem falha, o ano é o último grupo de 4 dígitos
    # presente no título (recuo de segurança).
    m_ano = re.search(r"de\s+(\d{2})/(\d{2})/(\d{4})", titulo)
    if not m_ano:
        gm = re.search(r"(\b\d{4}\b)", titulo)
        ano = gm.group(1) if gm else ""
    else:
        ano = m_ano.group(3)
    if m_num:
        return tipo, f"{int(m_num.group(1)):02d}/{ano}"
    if "S/N" in titulo.upper() or "SEM N"[0:3] in titulo.upper():
        return tipo, f"S/N/{ano}"
    return tipo, ""


def gera_indices(atos):
    """Reescreve indice_normas.json + .csv (idempotente; preserva os 18 do núcleo)."""
    p_json = caminho("01_ATOS_NORMATIVOS", "indice_normas.json")
    p_csv = caminho("01_ATOS_NORMATIVOS", "indice_normas.csv")
    with open(p_json, "w", encoding="utf-8") as f:
        json.dump(atos, f, ensure_ascii=False, indent=2)
    cols = ["id_interno", "tipo", "numero", "ementa", "situacao", "id_tclegis",
            "url_detalhe", "titulo_tclegis", "fonte_tclegis", "vides"]
    import csv
    with open(p_csv, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for a in atos:
            # o 01 gravava com chaves 'id'/'tclegis' e o CSV saía vazio nessas
            # colunas; aqui padroniza a projeção (idempotente para os 18 antigos).
            w.writerow({
                "id_interno": a.get("id"),
                "tipo": a.get("tipo"),
                "numero": a.get("numero"),
                "ementa": a.get("ementa"),
                "situacao": a.get("situacao"),
                "id_tclegis": a.get("tclegis"),
                "url_detalhe": a.get("url_detalhe")
                or f"{BASE_TCLEGIS}/Home/Detalhe/{a.get('tclegis')}",
                "titulo_tclegis": a.get("titulo"),
                "fonte_tclegis": a.get("fonte"),
                "vides": a.get("vides"),
            })
    print(f"[ok] índices: {p_json} e {p_csv} ({len(atos)} atos)")


def indices():
    """Reconstrói a lista dos atos coletados na Fase 2 no índice, sem tocar no núcleo.

    A entrada de cada ato marcado ``relevante``/``contexto`` (e já baixado) é
    REBUILDADA a cada execução a partir de ``hashes/norma_*.json`` +
    ``candidatos_triagem.json`` — por isso o índice fica idempotente e correções
    de parse (ex.: número com ano, "Ordem de Serviço") se propagam num simples
    rerun, sem apagar nada. O núcleo curado (os 18 atos originais, sem campo
    ``coletado_em``) é preservado integralmente, inclusive o ``numero`` com a
    notação curatorial ("83/PRES./2023").

    Os caminhos de ``documentos[].arquivo`` saem relativos à raiz do
    repositório (portáveis no git); o registro absoluto da máquina fica em
    ``hashes/norma_*.json`` e em ``99_ORIGINAIS/``.
    """
    idx = carrega_indice()
    nucleo = [a for a in idx if not a.get("coletado_em")]
    tri = json.load(open(caminho("00_CONTROLE", "coleta", "candidatos_triagem.json"),
                         encoding="utf-8"))
    hashes_dir = caminho("00_CONTROLE", "hashes")
    raiz = os.path.abspath(caminho("."))
    construidos = []
    for fn in sorted(os.listdir(hashes_dir)):
        if not fn.startswith("norma_"):
            continue
        prov = json.load(open(os.path.join(hashes_dir, fn), encoding="utf-8"))
        if prov.get("classificacao") not in ("relevante", "contexto"):
            continue
        did = str(prov.get("id_tclegis"))
        if not did:
            continue
        t = tri.get(did, {})
        situacao = prov.get("situacao") or "situacao_nao_confirmada"
        tipo, numero = parse_tipo_numero(t.get("titulo_detalhe"))
        docs = []
        for d in prov.get("documentos", []):
            arq = d.get("arquivo") or ""
            if arq and os.path.isabs(arq):
                try:
                    arq = os.path.relpath(arq, raiz).replace("\\", "/")
                except ValueError:
                    pass
            docs.append({"variante": d.get("variante"), "arquivo": arq,
                         "sha256": d.get("sha256")})
        construidos.append({
            "id": prov.get("id_interno"),
            "tclegis": did,
            "tipo": prov.get("tipo") or tipo,
            "numero": prov.get("numero") or numero,
            "ementa": t.get("ementa") or prov.get("ementa"),
            "situacao": situacao,
            "alteracoes": t.get("alteracoes", []),
            "titulo": t.get("titulo_detalhe"),
            "fonte": t.get("fonte"),
            "vides": t.get("vides", []),
            "pdfs": t.get("pdfs", []),
            "indexacao": t.get("indexacao", ""),
            "coletado_em": prov.get("data_hora_download"),
            "documentos": docs,
        })
    # Ordem estável: núcleo na ordem original; a Fase 2 por id TCLEGIS.
    fase2 = sorted(construidos, key=lambda a: int(a["tclegis"]))
    originais = [a.get("tclegis") for a in nucleo]
    extras = [a for a in fase2 if a["tclegis"] not in originais]
    gera_indices(nucleo + extras)
    print(f"[ok] índice: {len(nucleo)} do núcleo preservados + {len(extras)} da Fase 2 "
          f"(total {len(nucleo) + len(extras)}).")


def status():
    dest = caminho("00_CONTROLE", "coleta", "candidatos_triagem.json")
    if not os.path.exists(dest):
        sys.exit("Nenhuma triagem ainda.")
    dados = json.load(open(dest, encoding="utf-8"))
    from collections import Counter
    print(f"{len(dados)} candidatos triados")
    print("classificação:", dict(Counter(v.get("classificacao") or "sem_classificacao" for v in dados.values())))


def sha(b):
    import hashlib
    return hashlib.sha256(b).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--coleta", action="store_true", help="baixa PDFs dos relevantes")
    ap.add_argument("--indices", action="store_true", help="mescla coletados no índice")
    ap.add_argument("--status", action="store_true", help="estado da triagem")
    ap.add_argument("--forcar", action="store_true", help="refaz triagem mesmo já feita")
    ap.add_argument("--situacao", help="filtra coleta por situação (ex.: vigentes)")
    args = ap.parse_args()
    cfg = le_config()
    if args.status:
        status()
    elif args.coleta:
        coleta(cfg, args.situacao)
    elif args.indices:
        indices()
    else:
        triagem(cfg, args.forcar)


if __name__ == "__main__":
    main()
