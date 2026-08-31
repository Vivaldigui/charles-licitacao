#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
preencher_minuta.py — Lista e preenche campos {{CAMPO}} em minutas DOCX.

DOCX é tratado como ZIP+XML. Somente `word/document.xml` pode ser alterado;
styles, headers e footers são copiados byte a byte. A minuta-mãe nunca é
sobrescrita.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from xml.etree import ElementTree as ET

CAMPO_RE = re.compile(r"\{\{([A-Z0-9_]+)\}\}")
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W_NS}
ET.register_namespace("w", W_NS)

AUTOR_PADRAO = "Câmara Municipal de Itanhandu"

CP_NS = "http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
DC_NS = "http://purl.org/dc/elements/1.1/"
DCTERMS_NS = "http://purl.org/dc/terms/"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"
CORE_NS = {"cp": CP_NS, "dc": DC_NS, "dcterms": DCTERMS_NS, "xsi": XSI_NS}
for _prefixo, _uri in CORE_NS.items():
    ET.register_namespace(_prefixo, _uri)


def _definir_metadados_core(xml: bytes, titulo: Optional[str]) -> bytes:
    """Força autor/último editor institucionais e ajusta o título do documento.

    Minutas-mãe carregam metadados pessoais residuais (criador e título de quem
    editou o arquivo pela última vez no Word). Como o restante do pacote DOCX é
    copiado byte a byte, sem isto esses dados vazam para todo documento gerado.
    """
    root = ET.fromstring(xml)

    def _obter_ou_criar(nome_local: str, ns: str) -> ET.Element:
        el = root.find(f"{{{ns}}}{nome_local}")
        if el is None:
            el = ET.SubElement(root, f"{{{ns}}}{nome_local}")
        return el

    _obter_ou_criar("creator", DC_NS).text = AUTOR_PADRAO
    _obter_ou_criar("lastModifiedBy", CP_NS).text = AUTOR_PADRAO
    if titulo is not None:
        _obter_ou_criar("title", DC_NS).text = titulo

    modificado = _obter_ou_criar("modified", DCTERMS_NS)
    modificado.text = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    modificado.set(f"{{{XSI_NS}}}type", "dcterms:W3CDTF")

    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def _document_xml(caminho: Path) -> bytes:
    with zipfile.ZipFile(caminho, "r") as zf:
        return zf.read("word/document.xml")


def _campos_em_xml(xml: bytes) -> list[str]:
    root = ET.fromstring(xml)
    campos: set[str] = set()
    for paragrafo in root.findall(".//w:p", NS):
        textos = paragrafo.findall(".//w:t", NS)
        combinado = "".join(t.text or "" for t in textos)
        campos.update(CAMPO_RE.findall(combinado))
    return sorted(campos)


def listar_campos(caminho: Path) -> list[str]:
    """Lista campos {{CAMPO}} encontrados, inclusive fragmentados entre runs."""
    return _campos_em_xml(_document_xml(caminho))


def _substituir_xml(xml: bytes, campos: dict[str, Any]) -> tuple[bytes, list[str], list[str]]:
    root = ET.fromstring(xml)
    preenchidos: set[str] = set()
    for paragrafo in root.findall(".//w:p", NS):
        textos = paragrafo.findall(".//w:t", NS)
        if not textos:
            continue
        original = "".join(t.text or "" for t in textos)
        if "{{" not in original:
            continue

        def troca(match: re.Match[str]) -> str:
            nome = match.group(1)
            if nome in campos:
                preenchidos.add(nome)
                return str(campos[nome])
            return match.group(0)

        novo = CAMPO_RE.sub(troca, original)
        if novo != original:
            textos[0].text = novo
            for t in textos[1:]:
                t.text = ""
    remanescentes = _campos_em_xml(ET.tostring(root, encoding="utf-8"))
    return ET.tostring(root, encoding="utf-8", xml_declaration=True), sorted(preenchidos), remanescentes


def preencher_docx(
    origem: Path, campos_json: Path, destino: Path, titulo: Optional[str] = None
) -> dict[str, Any]:
    """Preenche campos presentes no JSON e grava em novo DOCX.

    `titulo`, quando informado, substitui o título (metadado `dc:title`) do
    documento gerado. O autor e o último editor são sempre fixados como
    `AUTOR_PADRAO`, independentemente do que constava na minuta-mãe.
    """
    origem_resolvida = origem.resolve()
    destino_resolvido = destino.resolve()
    if origem_resolvida == destino_resolvido:
        raise ValueError("Destino não pode ser igual à minuta-mãe de origem.")
    with campos_json.open("r", encoding="utf-8") as f:
        campos = json.load(f)
    if not isinstance(campos, dict):
        raise ValueError("campos.json deve conter um objeto JSON.")

    campos_existentes = set(listar_campos(origem))
    extras = sorted(set(campos) - campos_existentes)
    if extras:
        raise ValueError(
            "campos.json contém chave sem campo correspondente na minuta: " + ", ".join(extras)
        )

    xml = _document_xml(origem)
    novo_xml, preenchidos, remanescentes = _substituir_xml(xml, campos)
    destino.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(origem, "r") as zin, zipfile.ZipFile(destino, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        for info in zin.infolist():
            dados = zin.read(info.filename)
            if info.filename == "word/document.xml":
                dados = novo_xml
            elif info.filename == "docProps/core.xml":
                dados = _definir_metadados_core(dados, titulo)
            zout.writestr(info, dados)

    return {
        "preenchidos": preenchidos,
        "remanescentes": remanescentes,
        "chaves_sem_campo": extras,
        "saida": str(destino),
    }


def construir_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Lista ou preenche campos {{CAMPO}} de uma minuta DOCX.")
    sub = ap.add_subparsers(dest="comando", required=True)
    listar = sub.add_parser("listar", help="Lista campos existentes na minuta.")
    listar.add_argument("minuta", help="Caminho da minuta DOCX.")
    preencher = sub.add_parser("preencher", help="Preenche campos em novo DOCX.")
    preencher.add_argument("minuta", help="Caminho da minuta DOCX.")
    preencher.add_argument("campos", help="JSON com campos a preencher.")
    preencher.add_argument("--saida", required=True, help="Destino DOCX novo.")
    preencher.add_argument(
        "--titulo",
        help="Título do documento (metadado dc:title). Se omitido, o título "
        "existente na minuta-mãe é preservado — informe sempre que a minuta "
        "carregar um título residual de outro documento.",
    )
    return ap


def main(argv: Optional[list[str]] = None) -> int:
    parser = construir_parser()
    args = parser.parse_args(argv)
    try:
        if args.comando == "listar":
            for campo in listar_campos(Path(args.minuta)):
                print(campo)
            return 0
        if args.comando == "preencher":
            relatorio = preencher_docx(
                Path(args.minuta), Path(args.campos), Path(args.saida), titulo=args.titulo
            )
            print("# Relatório de preenchimento")
            print("Preenchidos: " + (", ".join(relatorio["preenchidos"]) or "nenhum"))
            print("Remanescentes: " + (", ".join(relatorio["remanescentes"]) or "nenhum"))
            print("Chaves do JSON sem campo correspondente: nenhum")
            print(f"Autor/último editor: {AUTOR_PADRAO}")
            print(f"Saída: {relatorio['saida']}")
            return 0
    except (OSError, KeyError, zipfile.BadZipFile, ET.ParseError, ValueError) as exc:
        print(f"[ERRO] {exc}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

