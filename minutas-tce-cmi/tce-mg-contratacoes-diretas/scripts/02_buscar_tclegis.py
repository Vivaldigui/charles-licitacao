# -*- coding: utf-8 -*-
"""02_buscar_tclegis.py — Busca documentada por assunto no TCLEGIS (Fase 2).

Serializa sobre ``busca_tclegis_agenda`` da config.yaml (termos da agenda de
contratação direta), executa POST /Home/RetornoBusca com o campo ``termos``
(campo de texto real do formulário — descoberto na Fase 1), grava a resposta
bruta canonizada em registros_web/ e salva resultados estruturados em
00_CONTROLE/busca/ com proveniência (token, data, status, sha256).

Não inventa dado: resultado é o que o TCLEGIS devolveu. Idempotente (não regrava
evidência com mesmo hash) e educado (pausa configurada).

Uso:
    python scripts/02_buscar_tclegis.py                # agenda completa da config
    python scripts/02_buscar_tclegis.py --termo "estudo técnico preliminar"
    python scripts/02_buscar_tclegis.py --so-listar    # mostra agenda sem buscar
"""
import argparse
import json
import os
import re
import sys
import urllib.parse
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import (caminho, fetch, grava_evidencia_web, json_dump, le_config,
                   pausa_educada, slug, token_antiforgery)  # noqa: E402


def extrai_resultados(html):
    """Lista de {id, titulo, ementa} do HTML de RetornoBusca.

    Formato verificado (evidência: registros_web/tclegis_resultado_*.html):
        <ul class="LinhasRetornoBusca">
          <li><a href="/Home/Detalhe/{id}">
            <p>titulo</p>
            <p>ementa</p>
          </a></li>
    """
    out = []
    # ordem dos atributos não é garantida: 'href' pode vir depois de 'target'.
    for m in re.finditer(r'<li>\s*<a[^>]*href="/Home/Detalhe/(\d+)"[^>]*>(.*?)</a>\s*</li>',
                         html, re.S):
        id_ = m.group(1)
        ps = re.findall(r"<p>(.*?)</p>", m.group(2), re.S)
        limpo = lambda s: re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s)).strip()
        titulo = limpo(ps[0]) if ps else ""
        ementa = limpo(ps[1]) if len(ps) > 1 else ""
        out.append({"id": id_, "titulo": titulo[:200], "ementa": ementa[:400]})
    return out


def monta_campos(token, termo, agenda, page=1):
    cam = {
        "__RequestVerificationToken": token,
        "tipoConsulta": "TCE",
        "numNorma": "", "numAno": "", "dataInicio": "", "dataFim": "",
        "tipoNorma": "", "tipoOrigem": "", "indRevogada": "",
        "qtdPorPagina": str(agenda.get("qtdPorPagina", 100)),
        "orderby": "", "page": str(page),
        "termos": termo,
    }
    for ck in agenda.get("campos_checados", []):
        cam[ck] = "true"
    return cam


def busca_termo(cfg, token, termo):
    """Roda a busca no TCLEGIS; retorna (status, registro_evidencia, itens)."""
    t = cfg["fontes"]["tclegis"]
    base = t["base"]
    agenda = cfg["busca_tclegis_agenda"]
    campos = monta_campos(token, termo, agenda)
    body = urllib.parse.urlencode(campos).encode("utf-8")
    st, hdrs, raw = fetch(
        f"{base}/Home/RetornoBusca", data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded",
                 "Referer": f"{base}/Home/Index/TCE"},
        timeout=90)
    html = raw.decode("utf-8", "replace")
    s = slug(termo)
    reg = grava_evidencia_web(
        "busca_tclegis", f"tclegis_resultado_{s}.html", raw,
        tag=f"busca_tclegis:{termo}",
        fonte_url=f"{base}/Home/RetornoBusca")
    itens = extrai_resultados(html)
    return st, reg, itens


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--termo", help="busca um termo específico (ignora agenda)")
    ap.add_argument("--so-listar", action="store_true", help="lista a agenda da config")
    ap.add_argument("--forcar", action="store_true",
                    help="refaz busca mesmo sem nova evidência")
    args = ap.parse_args()

    cfg = le_config()
    t = cfg["fontes"]["tclegis"]
    base = t["base"]
    agenda = cfg["busca_tclegis_agenda"]
    termos = [args.termo] if args.termo else agenda.get("termos", [])

    if args.so_listar:
        for termo in termos:
            print(f"- {termo}")
        return

    # token fresco
    st, hdrs, raw = fetch(f"{base}{t['index']}")
    token = token_antiforgery(raw.decode("utf-8", "replace"))
    if not token:
        sys.exit("Não localizei __RequestVerificationToken na página de busca.")
    print(f"[info] token obtido ({len(token)} chars)")

    todas = []
    for termo in termos:
        st, reg, itens = busca_termo(cfg, token, termo)
        print(f"[{termo}] status {st} · {len(itens)} resultados · "
              f"{'evidência nova' if not reg['ja_existia'] else 'já registrada'}")
        todas.append({"termo": termo, "qtd": len(itens),
                      "sha256_html": reg["sha256"], "resultados": itens})
        pausa_educada()

    json_dump(caminho("00_CONTROLE/busca/resultados_busca.json"), {
        "gerado_em": datetime.now(timezone.utc).isoformat(),
        "fonte": f"{base}/Home/RetornoBusca",
        "config_usada": "busca_tclegis_agenda em scripts/config.yaml",
        "termos": todas,
    })
    print(f"[fim] resultados consolidados em 00_CONTROLE/busca/resultados_busca.json")


if __name__ == "__main__":
    main()