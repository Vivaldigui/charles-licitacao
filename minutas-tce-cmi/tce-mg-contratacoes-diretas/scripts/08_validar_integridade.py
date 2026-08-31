# -*- coding: utf-8 -*-
"""Valida PDFs, hashes, índices de processos e portabilidade dos metadados.

O modo padrão é somente leitura. ``--normalizar-caminhos`` troca caminhos
absolutos situados dentro da base por caminhos relativos, sem tocar nos PDFs.
``--relatorio`` atualiza ``00_CONTROLE/relatorio_qualidade.md``.
"""
import argparse
import csv
import hashlib
import json
import os
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HASHES = os.path.join(ROOT, "00_CONTROLE", "hashes")
RELATORIO = os.path.join(ROOT, "00_CONTROLE", "relatorio_qualidade.md")
INDICES = os.path.join(ROOT, "03_INDICES")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for bloco in iter(lambda: f.read(1024 * 1024), b""):
            h.update(bloco)
    return h.hexdigest()


def resolve(caminho_arquivo):
    if os.path.isabs(caminho_arquivo):
        return os.path.normpath(caminho_arquivo)
    return os.path.normpath(os.path.join(ROOT, caminho_arquivo))


def relativo_se_interno(path):
    absoluto = os.path.abspath(path)
    try:
        comum = os.path.commonpath((ROOT, absoluto))
    except ValueError:
        return None
    if os.path.normcase(comum) != os.path.normcase(ROOT):
        return None
    return os.path.relpath(absoluto, ROOT).replace("\\", "/")


def grava_atomico(path, dados):
    tmp = path + ".tmp-integridade"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp, path)


def valida(normalizar=False):
    resultado = {
        "arquivos_hash": 0,
        "documentos": 0,
        "pdf_validos": 0,
        "caminhos_normalizados": 0,
        "erros": [],
        "avisos": [],
        "catalogo_candidatos": 0,
        "candidatos_por_ano": {},
        "processos_catalogados": 0,
        "documentos_indexados": 0,
        "duplicatas_indexadas": 0,
    }
    for nome in sorted(os.listdir(HASHES)):
        if not nome.endswith(".json") or not nome.startswith(("norma_", "processo_")):
            continue
        path_meta = os.path.join(HASHES, nome)
        with open(path_meta, "r", encoding="utf-8") as f:
            meta = json.load(f)
        resultado["arquivos_hash"] += 1
        alterado = False
        for doc in meta.get("documentos", meta.get("arquivos", [])):
            resultado["documentos"] += 1
            registrado = doc.get("arquivo") or ""
            path_doc = resolve(registrado)
            if os.path.isabs(registrado):
                rel = relativo_se_interno(path_doc)
                if rel and normalizar:
                    doc["arquivo"] = rel
                    alterado = True
                    resultado["caminhos_normalizados"] += 1
                elif rel:
                    resultado["avisos"].append(f"caminho absoluto: {nome} -> {registrado}")
                else:
                    resultado["erros"].append(f"caminho fora da base: {nome} -> {registrado}")
            if not os.path.isfile(path_doc):
                resultado["erros"].append(f"ausente: {nome} -> {registrado}")
                continue
            if os.path.getsize(path_doc) == 0:
                resultado["erros"].append(f"zero bytes: {registrado}")
                continue
            with open(path_doc, "rb") as f:
                magic = f.read(5)
            if magic != b"%PDF-":
                resultado["erros"].append(f"não PDF: {registrado}")
                continue
            obtido = sha256(path_doc)
            if obtido != doc.get("sha256"):
                resultado["erros"].append(f"SHA-256 divergente: {registrado}")
                continue
            resultado["pdf_validos"] += 1
        if alterado:
            grava_atomico(path_meta, meta)

    # Reconcilia os índices CSV/JSON sem promover candidatos a processos coletados.
    candidatos_json = os.path.join(INDICES, "processos_candidatos.json")
    candidatos_csv = os.path.join(INDICES, "processos_candidatos.csv")
    if os.path.isfile(candidatos_json) and os.path.isfile(candidatos_csv):
        try:
            with open(candidatos_json, "r", encoding="utf-8") as f:
                candidatos = json.load(f).get("processos", [])
            with open(candidatos_csv, "r", encoding="utf-8-sig", newline="") as f:
                candidatos_csv_rows = list(csv.DictReader(f))
            resultado["catalogo_candidatos"] = len(candidatos)
            for item in candidatos:
                ano = str(item.get("ano"))
                resultado["candidatos_por_ano"][ano] = (
                    resultado["candidatos_por_ano"].get(ano, 0) + 1
                )
            if len(candidatos) != len(candidatos_csv_rows):
                resultado["erros"].append(
                    "processos_candidatos.csv e .json têm quantidades divergentes"
                )
            ids = [x.get("id_interno") for x in candidatos]
            if len(ids) != len(set(ids)):
                resultado["erros"].append("identificadores duplicados em processos_candidatos.json")
        except (OSError, ValueError, TypeError) as exc:
            resultado["erros"].append(f"catálogo de candidatos inválido: {exc}")

    processos_json = os.path.join(INDICES, "processos.json")
    if os.path.isfile(processos_json):
        try:
            with open(processos_json, "r", encoding="utf-8") as f:
                processos = json.load(f)
            resultado["processos_catalogados"] = len(processos)
            for processo in processos:
                pasta = processo.get("pasta_local") or ""
                if not os.path.isdir(resolve(pasta)):
                    resultado["erros"].append(
                        f"pasta de processo ausente: {processo.get('id_interno')} -> {pasta}"
                    )
        except (OSError, ValueError, TypeError) as exc:
            resultado["erros"].append(f"índice de processos inválido: {exc}")

    documentos_json = os.path.join(INDICES, "documentos.json")
    if os.path.isfile(documentos_json):
        try:
            with open(documentos_json, "r", encoding="utf-8") as f:
                documentos = json.load(f)
            resultado["documentos_indexados"] = len(documentos)
            resultado["duplicatas_indexadas"] = sum(
                1 for doc in documentos if doc.get("duplicate_of")
            )
            for doc in documentos:
                texto = doc.get("texto_extraido")
                if texto and not texto.startswith("duplicate_of:") and not os.path.isfile(resolve(texto)):
                    resultado["erros"].append(f"texto extraído ausente: {texto}")
        except (OSError, ValueError, TypeError) as exc:
            resultado["erros"].append(f"índice de documentos inválido: {exc}")
    return resultado


def escreve_relatorio(r):
    agora = datetime.now(timezone.utc).isoformat()
    status = "SEM ERROS" if not r["erros"] else "COM ERROS"
    linhas = [
        "# Relatório de qualidade — base TCE-MG",
        "",
        f"Gerado em: `{agora}`",
        "",
        f"Status: **{status}**",
        "",
        f"- Metadados de hash: {r['arquivos_hash']}",
        f"- Documentos referenciados: {r['documentos']}",
        f"- PDFs com assinatura e SHA-256 válidos: {r['pdf_validos']}",
        f"- Processos candidatos reconciliados: {r['catalogo_candidatos']}",
        f"- Processos documentais catalogados: {r['processos_catalogados']}",
        f"- Documentos de processos indexados: {r['documentos_indexados']}",
        f"- Duplicatas binárias indexadas: {r['duplicatas_indexadas']}",
        f"- Caminhos absolutos normalizados nesta execução: {r['caminhos_normalizados']}",
        f"- Erros: {len(r['erros'])}",
        f"- Avisos: {len(r['avisos'])}",
        "",
        "## Erros",
        "",
    ]
    linhas += [f"- {x}" for x in r["erros"]] or ["- Nenhum."]
    linhas += ["", "## Avisos", ""]
    linhas += [f"- {x}" for x in r["avisos"]] or ["- Nenhum."]
    linhas += [
        "",
        "## Catálogo de processos candidatos",
        "",
        f"- Registros CSV/JSON reconciliados: {r['catalogo_candidatos']}.",
        "- Distribuição anual: " + "; ".join(
            f"{ano} = {quantidade}"
            for ano, quantidade in sorted(r["candidatos_por_ano"].items())
        ) + ".",
        "- O CSV oficial bruto foi preservado, mas não é fonte de ingestão porque "
        "não escapa corretamente vírgulas e quebras de linha.",
        "",
        "## Processos documentais",
        "",
        f"- Processos catalogados: {r['processos_catalogados']}.",
        f"- Documentos indexados: {r['documentos_indexados']}, dos quais "
        f"{r['duplicatas_indexadas']} são duplicatas binárias registradas.",
        "",
        "## Limites desta validação",
        "",
        "A validação confirma integridade binária e rastreabilidade dos PDFs já "
        "catalogados, além da consistência básica dos índices CSV/JSON. Ela não "
        "confirma vigência jurídica, identidade administrativa de pares número/ano "
        "repetidos nem completude temática.",
        "",
    ]
    with open(RELATORIO, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--normalizar-caminhos", action="store_true")
    ap.add_argument("--relatorio", action="store_true")
    args = ap.parse_args()
    r = valida(args.normalizar_caminhos)
    if args.relatorio:
        escreve_relatorio(r)
    print(json.dumps(r, ensure_ascii=False, indent=2))
    raise SystemExit(1 if r["erros"] else 0)


if __name__ == "__main__":
    main()
