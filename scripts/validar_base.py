#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validar_base.py — Lint da base documental do Charles.

Sai com código diferente de zero quando encontra erro bloqueante. O objetivo é
detectar problemas mecânicos; decisão jurídica continua humana.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any

from base_markdown import caminho_relativo, ler_frontmatter, primeiro_h1, slug_de_arquivo
from indexar_base import SAIDA_PADRAO, arquivos_markdown, gerar_indice

RAIZ = Path(__file__).resolve().parents[1]
CHAVES_OBRIGATORIAS = {
    "tipo",
    "hierarquia",
    "tema",
    "fonte",
    "vigencia",
    "atualizado_em",
    "tags",
}
VIGENCIAS_VALIDAS = {"vigente", "revogado", "alterado"}


def _data_iso(valor: Any) -> date | None:
    try:
        return datetime.strptime(str(valor), "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def _wiki_links(texto: str) -> list[tuple[str, int]]:
    return [(m.group(1).strip(), m.start()) for m in re.finditer(r"\[\[([^\]]+)\]\]", texto)]


def _slug_texto(texto: str) -> str:
    bruto = texto.lower()
    mapa = str.maketrans(
        "áàâãäéèêëíìîïóòôõöúùûüçñ",
        "aaaaaeeeeiiiiooooouuuucn",
    )
    bruto = bruto.translate(mapa)
    bruto = re.sub(r"[^a-z0-9]+", "-", bruto).strip("-")
    return bruto


def _carregar_indice_json() -> list[dict[str, Any]] | None:
    if not SAIDA_PADRAO.exists():
        return None
    try:
        return json.loads(SAIDA_PADRAO.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _normalizar_indice(indice: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(item.get("arquivo")): item for item in indice if item.get("arquivo")}


def validar() -> tuple[list[str], list[str]]:
    """Retorna erros e avisos da validação."""
    erros: list[str] = []
    avisos: list[str] = []
    arquivos = arquivos_markdown(RAIZ)
    textos: dict[Path, str] = {}
    metadados: dict[Path, dict[str, Any]] = {}
    slugs: dict[str, Path] = {}

    for caminho in arquivos:
        texto = caminho.read_text(encoding="utf-8")
        textos[caminho] = texto
        frontmatter, corpo, presente = ler_frontmatter(texto)
        rel = caminho_relativo(caminho, RAIZ)
        if not presente:
            erros.append(f"{rel}: frontmatter ausente.")
            continue
        faltantes = sorted(chave for chave in CHAVES_OBRIGATORIAS if chave not in frontmatter)
        if faltantes:
            erros.append(f"{rel}: frontmatter incompleto; faltam {', '.join(faltantes)}.")
        if frontmatter.get("vigencia") not in VIGENCIAS_VALIDAS:
            erros.append(f"{rel}: vigencia inválida ({frontmatter.get('vigencia')}).")
        if _data_iso(frontmatter.get("atualizado_em")) is None:
            erros.append(f"{rel}: atualizado_em inválido ({frontmatter.get('atualizado_em')}).")
        metadados[caminho] = frontmatter
        slug = slug_de_arquivo(caminho)
        slugs.setdefault(slug, caminho)
        slug_arquivo = _slug_texto(caminho.stem)
        slugs.setdefault(slug_arquivo, caminho)
        slug_sem_ficha = re.sub(r"-ficha-de-uso$", "", slug_arquivo)
        slugs.setdefault(slug_sem_ficha, caminho)
        titulo = primeiro_h1(corpo)
        if titulo:
            titulo_base = titulo.split("(", 1)[0].strip()
            for candidato in {_slug_texto(titulo), _slug_texto(titulo_base)}:
                slugs.setdefault(candidato, caminho)
                sem_prefixo = re.sub(r"^ficha-de-uso-", "", candidato)
                slugs.setdefault(sem_prefixo, caminho)
                slugs.setdefault(sem_prefixo.replace("-contratacao-", "-de-contratacao-"), caminho)
                slugs.setdefault(sem_prefixo.replace("-fornecimento", "-de-fornecimento"), caminho)
                slugs.setdefault(sem_prefixo.replace("termo-de-adjudicacao-homologacao", "termo-de-adjudicacao-e-homologacao"), caminho)

    for caminho, texto in textos.items():
        rel = caminho_relativo(caminho, RAIZ)
        for destino, pos in _wiki_links(texto):
            destino_slug = destino.split("|", 1)[0].split("#", 1)[0].strip()
            if destino_slug not in slugs:
                erros.append(f"{rel}: link wiki aponta para slug inexistente [[{destino}]].")
                continue
            destino_path = slugs[destino_slug]
            if metadados.get(destino_path, {}).get("vigencia") == "revogado":
                janela = texto[max(0, pos - 120) : pos + 160].lower()
                if not re.search(r"revogad|ressalv|desatualiz|hist[oó]ric", janela):
                    erros.append(
                        f"{rel}: referencia fonte revogada [[{destino}]] sem ressalva próxima."
                    )

        frontmatter = metadados.get(caminho, {})
        atualizado = _data_iso(frontmatter.get("atualizado_em"))
        if "⚠️" in texto and atualizado:
            idade = (date.today() - atualizado).days
            if idade > 365:
                erros.append(f"{rel}: marcado com manutenção anual e atualizado há mais de 12 meses.")

    indice_atual = gerar_indice(RAIZ)
    indice_gravado = _carregar_indice_json()
    if indice_gravado is None:
        erros.append("00_indices/BASE_INDEXADA.json ausente ou inválido; rode python scripts/indexar_base.py.")
    else:
        atual = _normalizar_indice(indice_atual)
        gravado = _normalizar_indice(indice_gravado)
        if set(atual) != set(gravado):
            faltam = sorted(set(atual) - set(gravado))
            sobram = sorted(set(gravado) - set(atual))
            if faltam:
                erros.append("BASE_INDEXADA.json desatualizado; faltam: " + ", ".join(faltam[:10]))
            if sobram:
                erros.append("BASE_INDEXADA.json desatualizado; sobram: " + ", ".join(sobram[:10]))
        else:
            for rel, item in atual.items():
                salvo = gravado[rel]
                campos = ["tipo", "hierarquia", "tema", "vigencia", "atualizado_em", "titulo", "tamanho_linhas"]
                divergentes = [campo for campo in campos if item.get(campo) != salvo.get(campo)]
                if divergentes:
                    erros.append(
                        f"{rel}: divergência em BASE_INDEXADA.json ({', '.join(divergentes)}); rode reindexação."
                    )
                    break

    if not erros:
        avisos.append("Base validada sem erros bloqueantes.")
    return erros, avisos


def main() -> int:
    erros, avisos = validar()
    for aviso in avisos:
        print(f"[OK] {aviso}")
    if erros:
        print("# Pendências da base")
        for erro in erros:
            print(f"- [ERRO] {erro}")
        print("\nSugestão: corrija as pendências e rode `python scripts/indexar_base.py`.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
