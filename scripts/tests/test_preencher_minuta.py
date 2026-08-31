from __future__ import annotations

import json
import zipfile
from pathlib import Path

from preencher_minuta import listar_campos, preencher_docx


DOCUMENT_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:r><w:t>Olá {{NOME}}</w:t></w:r></w:p>
    <w:p><w:r><w:t>{{VA</w:t></w:r><w:r><w:t>LOR}}</w:t></w:r></w:p>
  </w:body>
</w:document>
"""


def _criar_docx(caminho: Path) -> None:
    with zipfile.ZipFile(caminho, "w") as zf:
        zf.writestr("[Content_Types].xml", "<Types></Types>")
        zf.writestr("word/document.xml", DOCUMENT_XML)
        zf.writestr("word/styles.xml", b"STYLE-BYTES")


def test_listar_campos_fragmentados(tmp_path: Path) -> None:
    docx = tmp_path / "minuta.docx"
    _criar_docx(docx)
    assert listar_campos(docx) == ["NOME", "VALOR"]


def test_preencher_preserva_styles_e_lista_remanescentes(tmp_path: Path) -> None:
    docx = tmp_path / "minuta.docx"
    saida = tmp_path / "saida.docx"
    campos = tmp_path / "campos.json"
    _criar_docx(docx)
    campos.write_text(json.dumps({"NOME": "Charles"}, ensure_ascii=False), encoding="utf-8")

    relatorio = preencher_docx(docx, campos, saida)
    assert relatorio["preenchidos"] == ["NOME"]
    assert relatorio["remanescentes"] == ["VALOR"]
    with zipfile.ZipFile(saida, "r") as zf:
        assert zf.read("word/styles.xml") == b"STYLE-BYTES"


def test_erro_campo_inexistente_nao_grava(tmp_path: Path) -> None:
    docx = tmp_path / "minuta.docx"
    saida = tmp_path / "saida.docx"
    campos = tmp_path / "campos.json"
    _criar_docx(docx)
    campos.write_text(json.dumps({"INVENTADO": "x"}, ensure_ascii=False), encoding="utf-8")
    try:
        preencher_docx(docx, campos, saida)
    except ValueError as exc:
        assert "sem campo correspondente" in str(exc)
    else:
        raise AssertionError("campo inexistente deveria abortar")
    assert not saida.exists()

