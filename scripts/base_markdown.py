#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Funções comuns para ler fichas Markdown da base Charles."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any


def parse_valor_yaml(valor: str) -> Any:
    """Parser YAML mínimo: strings, null e listas inline."""
    texto = valor.strip()
    if texto in {"", "null", "None", "~"}:
        return None
    if texto.startswith("[") and texto.endswith("]"):
        miolo = texto[1:-1].strip()
        if not miolo:
            return []
        return [parte.strip().strip("'\"") for parte in miolo.split(",")]
    return texto.strip("'\"")


def ler_frontmatter(texto: str) -> tuple[dict[str, Any], str, bool]:
    """Retorna frontmatter, corpo e indicação de presença do bloco."""
    if not texto.startswith("---"):
        return {}, texto, False
    linhas = texto.splitlines()
    fim = None
    for i in range(1, len(linhas)):
        if linhas[i].strip() == "---":
            fim = i
            break
    if fim is None:
        return {}, texto, False

    dados: dict[str, Any] = {}
    chave_lista: str | None = None
    for linha in linhas[1:fim]:
        bruto = linha.rstrip()
        if not bruto.strip() or bruto.lstrip().startswith("#"):
            continue
        if chave_lista and re.match(r"^\s*-\s+", bruto):
            dados.setdefault(chave_lista, []).append(re.sub(r"^\s*-\s+", "", bruto).strip().strip("'\""))
            continue
        chave_lista = None
        if ":" not in bruto:
            continue
        chave, valor = bruto.split(":", 1)
        chave = chave.strip()
        valor = valor.strip()
        if valor == "":
            dados[chave] = []
            chave_lista = chave
        else:
            dados[chave] = parse_valor_yaml(valor)
    corpo = "\n".join(linhas[fim + 1 :])
    if texto.endswith("\n"):
        corpo += "\n"
    return dados, corpo, True


def primeiro_h1(corpo: str) -> str:
    """Extrai o primeiro título H1 do corpo."""
    for linha in corpo.splitlines():
        if linha.startswith("# "):
            return linha[2:].strip()
    return ""


def slug_de_arquivo(caminho: Path) -> str:
    """Slug simples usado em links wiki: nome do arquivo sem extensão."""
    return caminho.stem


def caminho_relativo(caminho: Path, raiz: Path) -> str:
    """Caminho relativo com barra POSIX para JSON/relatórios."""
    return caminho.relative_to(raiz).as_posix()

