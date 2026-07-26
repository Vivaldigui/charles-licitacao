#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
indexar_base.py — Gera índice JSON estruturado da base Markdown do Charles.

Varre as pastas 00 a 07 e 99, lê frontmatter YAML simples, extrai título,
tags, vigência, atualização, dispositivos citados e tamanho em linhas.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from base_markdown import caminho_relativo, ler_frontmatter, primeiro_h1

RAIZ = Path(__file__).resolve().parents[1]
PASTAS_INDEXADAS = [
    "00_indices",
    "01_legislacao",
    "02_normas_internas",
    "03_jurisprudencia",
    "04_doutrina_artigos",
    "05_minutas",
    "06_precedentes_camara",
    "07_checklists",
    "09_padronizacao_documental",
    "10_gestao_documental",
    "99_testes",
]
# Subpastas de saída gerada — nunca indexadas nem validadas como ficha.
# Saída gerada e exemplos de processo: não são fichas da base.
PASTAS_DE_SAIDA = {"relatorios", "exemplos"}
SAIDA_PADRAO = RAIZ / "00_indices" / "BASE_INDEXADA.json"

PADROES_DISPOSITIVOS = [
    r"\bart\. ?\d+[A-Za-zº°-]*",
    r"\bS[úu]mula ?\d+",
    r"\bPortaria(?: nº| n\.| no\.?)? ?\d+/\d{4}",
    r"§ ?\d+[º°]?",
    r"\bincisos? [IVXLCDM]+(?: e [IVXLCDM]+)?",
    r"\bartigos? \d+(?: e \d+)?",
]


def arquivos_markdown(raiz: Path = RAIZ) -> list[Path]:
    """
    Lista fichas Markdown indexáveis.

    Diretórios de SAÍDA gerada ficam de fora: o que está em
    `09_padronizacao_documental/relatorios/` é relatório produzido pelos
    scripts, não ficha da base, e não tem (nem deve ter) frontmatter. O mesmo
    vale para `10_gestao_documental/exemplos/`, que é processo fictício de
    demonstração — painel e manifesto, não ficha.
    """
    caminhos: list[Path] = []
    for pasta in PASTAS_INDEXADAS:
        base = raiz / pasta
        if not base.exists():
            continue
        caminhos.extend(
            caminho for caminho in base.rglob("*.md")
            if not any(parte in PASTAS_DE_SAIDA for parte in caminho.parts)
        )
    return sorted(caminhos, key=lambda p: caminho_relativo(p, raiz))


def extrair_dispositivos(corpo: str) -> list[str]:
    """Extrai dispositivos citados no corpo por regex conservadora."""
    achados: set[str] = set()
    for padrao in PADROES_DISPOSITIVOS:
        for item in re.findall(padrao, corpo, flags=re.IGNORECASE):
            achados.add(re.sub(r"\s+", " ", item).strip())
    return sorted(achados, key=lambda s: s.lower())


def normalizar_tags(valor: Any) -> list[str]:
    """Normaliza tags do frontmatter para lista de strings."""
    if isinstance(valor, list):
        return [str(item).strip() for item in valor if str(item).strip()]
    if isinstance(valor, str) and valor.strip():
        return [valor.strip()]
    return []


def indexar_arquivo(caminho: Path, raiz: Path = RAIZ) -> dict[str, Any]:
    """Cria o registro JSON de uma ficha Markdown."""
    texto = caminho.read_text(encoding="utf-8")
    frontmatter, corpo, _ = ler_frontmatter(texto)
    rel = caminho_relativo(caminho, raiz)
    return {
        "arquivo": rel,
        "tipo": frontmatter.get("tipo"),
        "hierarquia": frontmatter.get("hierarquia"),
        "tema": frontmatter.get("tema"),
        "vigencia": frontmatter.get("vigencia"),
        "atualizado_em": frontmatter.get("atualizado_em"),
        "titulo": primeiro_h1(corpo),
        "tags": normalizar_tags(frontmatter.get("tags")),
        "dispositivos": extrair_dispositivos(corpo),
        "tamanho_linhas": len(texto.splitlines()),
    }


def gerar_indice(raiz: Path = RAIZ) -> list[dict[str, Any]]:
    """Gera a lista completa de registros indexados."""
    return [indexar_arquivo(caminho, raiz=raiz) for caminho in arquivos_markdown(raiz)]


def main() -> int:
    indice = gerar_indice()
    SAIDA_PADRAO.parent.mkdir(parents=True, exist_ok=True)
    SAIDA_PADRAO.write_text(
        json.dumps(indice, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Índice gerado em {SAIDA_PADRAO} ({len(indice)} arquivo(s)).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

