# -*- coding: utf-8 -*-
"""Reconcilia ou confere o manifesto de evidências brutas.

Cada chave é o caminho relativo a ``00_CONTROLE/registros_web``. Isso evita
colisão entre arquivos homônimos em subpastas. ``--check`` é estritamente
somente leitura: confere cobertura, tamanho e SHA-256 sem regravar o manifesto.

Uso:
    python scripts/09_reconciliar_manifesto.py
    python scripts/09_reconciliar_manifesto.py --check
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import caminho, le_config, sha256_bytes  # noqa: E402

_METADADOS = {"gerado_em", "proposito", "nota", "esquema", "total_entradas"}


def _carrega_existente(cfg):
    path = caminho(cfg["diretorios"]["registros_web"], "MANIFESTO_EVIDENCIAS.json")
    if not os.path.exists(path):
        return None, {}
    with open(path, "r", encoding="utf-8") as f:
        dados = json.load(f)
    prov = {}
    for e in dados.get("arquivos", []) or []:
        chave = (e.get("arquivo_canonico") or e.get("arquivo") or "").replace("\\", "/")
        if chave:
            prov[chave] = e
    for v in dados.values():
        if isinstance(v, dict) and "sha256" in v and "arquivo" in v:
            chave = v["arquivo"].replace("\\", "/")
            prov.setdefault(chave, v)
            # Compatibilidade de migração com o manifesto antigo (basename).
            prov.setdefault(os.path.basename(chave), v)
    return dados, prov


def _fonte_default(nome):
    low = nome.lower()
    if "tclegis" in low:
        return "https://tclegis.tce.mg.gov.br"
    if "comprasmg" in low or low.startswith("compras"):
        return "https://www1.compras.mg.gov.br"
    if "chunk" in low or "transparencia" in low:
        return "https://transparencia.tce.mg.gov.br"
    return "não localizada na fase 1"


def _varre_disco(cfg, prov):
    reg_dir = caminho(cfg["diretorios"]["registros_web"])
    novo = {}
    agora = datetime.now(timezone.utc).isoformat()
    for root, _, files in os.walk(reg_dir):
        for nome in sorted(files):
            if nome in ("MANIFESTO_EVIDENCIAS.json", ".gitkeep"):
                continue
            path = os.path.join(root, nome)
            rel = os.path.relpath(path, reg_dir).replace("\\", "/")
            with open(path, "rb") as f:
                conteudo = f.read()
            anterior = prov.get(rel, prov.get(nome, {}))
            entrada = {
                "arquivo": rel,
                "sha256": sha256_bytes(conteudo),
                "bytes": len(conteudo),
            }
            for campo in ("fonte_url", "fonte", "tag", "data_hora",
                          "arquivo_original", "captura"):
                if anterior.get(campo):
                    entrada[campo] = anterior[campo]
            entrada.setdefault("tag", "fase-1:reconciliacao")
            entrada.setdefault("data_hora", agora)
            if "fonte" not in entrada and "fonte_url" not in entrada:
                entrada["fonte_url"] = _fonte_default(nome)
                entrada["nota"] = ("fonte e hora reconstruídas na reconciliação; "
                                   "conferir o diagnóstico antes de citar")
            novo[rel] = entrada
    return novo, agora


def _entradas_manifesto(dados):
    return {k: v for k, v in dados.items()
            if k not in _METADADOS and isinstance(v, dict)
            and "arquivo" in v and "sha256" in v}


def confere(cfg):
    existente, prov = _carrega_existente(cfg)
    disco, _ = _varre_disco(cfg, prov)
    if existente is None:
        print("[erro] manifesto ausente")
        return 1
    manifesto = _entradas_manifesto(existente)
    faltantes = sorted(set(disco) - set(manifesto))
    excedentes = sorted(set(manifesto) - set(disco))
    divergentes = sorted(
        k for k in set(disco) & set(manifesto)
        if disco[k]["sha256"] != manifesto[k]["sha256"]
        or disco[k]["bytes"] != manifesto[k].get("bytes")
    )
    if faltantes or excedentes or divergentes:
        print(f"[erro] disco={len(disco)} manifesto={len(manifesto)} "
              f"faltantes={len(faltantes)} excedentes={len(excedentes)} "
              f"divergentes={len(divergentes)}")
        for rotulo, itens in (("faltante", faltantes), ("excedente", excedentes),
                              ("divergente", divergentes)):
            for item in itens[:20]:
                print(f"  {rotulo}: {item}")
        return 1
    print(f"[ok] manifesto íntegro: {len(disco)} arquivos, caminhos e SHA-256 conferidos")
    return 0


def reconcilia(cfg):
    _, prov = _carrega_existente(cfg)
    novo, agora = _varre_disco(cfg, prov)
    manifesto = {
        "gerado_em": agora,
        "proposito": "evidências brutas capturadas e coletadas",
        "nota": ("chave e campo 'arquivo' são o caminho relativo a "
                 "registros_web/; proveniência reconstruída é explicitamente marcada"),
        "esquema": "flat-relative-path",
        "total_entradas": len(novo),
    }
    manifesto.update(novo)
    out = caminho(cfg["diretorios"]["registros_web"], "MANIFESTO_EVIDENCIAS.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(manifesto, f, ensure_ascii=False, indent=2)
    print(f"[ok] {len(novo)} entradas -> {out}")
    print("      com nota de proveniência reconstruída: "
          f"{sum(1 for v in novo.values() if 'nota' in v)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="confere cobertura e hashes sem regravar")
    args = ap.parse_args()
    cfg = le_config()
    if args.check:
        raise SystemExit(confere(cfg))
    reconcilia(cfg)


if __name__ == "__main__":
    main()
