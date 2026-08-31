#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validar_documento.py — Validação mecânica de documento gerado.

Recebe DOCX ou Markdown e um processo.json. A saída lista pendências; código
de saída diferente de zero indica pendência bloqueante.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from xml.etree import ElementTree as ET

from normalizar_precos import fmt_brl, parse_brl

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W_NS}
ORDEM_DATAS = [
    "dfd",
    "autorizacao",
    "aviso",
    "julgamento",
    "homologacao",
    "contrato",
]


def texto_docx(caminho: Path) -> str:
    """Extrai texto simples de word/document.xml."""
    with zipfile.ZipFile(caminho, "r") as zf:
        xml = zf.read("word/document.xml")
    root = ET.fromstring(xml)
    partes = [t.text or "" for t in root.findall(".//w:t", NS)]
    return "\n".join(partes)


def ler_texto_documento(caminho: Path) -> str:
    """Lê DOCX ou Markdown como texto."""
    if caminho.suffix.lower() == ".docx":
        return texto_docx(caminho)
    if caminho.suffix.lower() == ".md":
        return caminho.read_text(encoding="utf-8")
    raise ValueError("Formato suportado: .docx ou .md.")


def _achatar(dados: dict[str, Any], prefixo: str = "") -> dict[str, Any]:
    out: dict[str, Any] = {}
    for chave, valor in dados.items():
        nome = f"{prefixo}.{chave}" if prefixo else chave
        if isinstance(valor, dict):
            out.update(_achatar(valor, nome))
        else:
            out[nome] = valor
    return out


def _data(valor: Any) -> datetime | None:
    if not valor:
        return None
    texto = str(valor).strip()
    for formato in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(texto, formato)
        except ValueError:
            continue
    return None


def validar_documento(caminho: Path, processo_json: Path) -> tuple[list[str], list[str]]:
    """Retorna pendências bloqueantes e avisos."""
    texto = ler_texto_documento(caminho)
    with processo_json.open("r", encoding="utf-8") as f:
        processo = json.load(f)
    if not isinstance(processo, dict):
        raise ValueError("processo.json deve conter um objeto JSON.")

    bloqueantes: list[str] = []
    avisos: list[str] = []

    campos = sorted(set(re.findall(r"\{\{[A-Z0-9_]+\}\}", texto)))
    if campos:
        bloqueantes.append("Campos de minuta remanescentes: " + ", ".join(campos))
    if "[PREENCHER" in texto:
        bloqueantes.append("Marcador [PREENCHER] remanescente no documento.")

    achatado = _achatar(processo)
    for chave, valor in achatado.items():
        nome = chave.split(".")[-1].upper()
        if nome.startswith("VALOR_") and nome.endswith("_EXTENSO") and not str(valor or "").strip():
            bloqueantes.append(f"Campo por extenso vazio em processo.json: {chave}.")

    objeto = str(processo.get("objeto") or "").strip()
    if objeto and objeto.lower() not in texto.lower():
        bloqueantes.append("Objeto do processo.json não localizado no documento.")

    valor_estimado = processo.get("valor_estimado")
    valor_num = parse_brl(valor_estimado)
    if valor_estimado and valor_num is not None:
        candidatos = {
            str(valor_estimado),
            fmt_brl(valor_num),
            fmt_brl(valor_num).replace("R$ ", ""),
        }
        if not any(c in texto for c in candidatos):
            bloqueantes.append("Valor estimado do processo.json não localizado no documento.")

    datas = processo.get("datas", {}) if isinstance(processo.get("datas"), dict) else {}
    anteriores: tuple[str, datetime] | None = None
    for chave in ORDEM_DATAS:
        atual = _data(datas.get(chave))
        if atual is None:
            continue
        if anteriores and atual < anteriores[1]:
            bloqueantes.append(
                f"Data fora de ordem: {chave} ({datas.get(chave)}) antes de {anteriores[0]}."
            )
        anteriores = (chave, atual)

    if not bloqueantes:
        avisos.append("Documento validado sem pendências bloqueantes.")
    return bloqueantes, avisos


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Valida documento gerado contra processo.json.")
    ap.add_argument("documento", help="Documento .docx ou .md gerado.")
    ap.add_argument("processo", help="processo.json de referência.")
    args = ap.parse_args(argv)
    try:
        bloqueantes, avisos = validar_documento(Path(args.documento), Path(args.processo))
    except (OSError, ValueError, json.JSONDecodeError, zipfile.BadZipFile, ET.ParseError) as exc:
        print(f"[ERRO] {exc}", file=sys.stderr)
        return 2
    for aviso in avisos:
        print(f"[OK] {aviso}")
    if bloqueantes:
        print("# Pendências do documento")
        for pendencia in bloqueantes:
            print(f"- [BLOQUEANTE] {pendencia}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

