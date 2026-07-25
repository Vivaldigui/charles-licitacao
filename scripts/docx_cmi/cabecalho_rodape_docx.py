#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cabecalho_rodape_docx.py — Proteção do timbre institucional.

Cabeçalho, rodapé e mídia (brasão, logotipo, faixa institucional) são partes
PROTEGIDAS. Este módulo apenas:

  * fotografa (hash) as partes protegidas antes e depois da formatação;
  * compara o documento com a minuta-mãe;
  * relata divergências.

Ele nunca recria, redimensiona, reposiciona ou substitui cabeçalho e rodapé.
Nas minutas da Câmara de Itanhandu o timbre é imagem (3 desenhos no cabeçalho,
2 no rodapé, na maioria dos modelos), de modo que qualquer reescrita dessas
partes destruiria o brasão.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from util_ooxml import (
    partes_cabecalho_rodape,
    assinaturas_partes,
    iter_paragrafos_tabela,
    normalizar_texto,
    partes_do_pacote,
    qn,
)


@dataclass
class ResumoCabecalhoRodape:
    secoes: int = 0
    imagens_cabecalho: int = 0
    imagens_rodape: int = 0
    textos_cabecalho: list[str] = field(default_factory=list)
    textos_rodape: list[str] = field(default_factory=list)
    campo_pagina_no_rodape: bool = False
    distancia_cabecalho_cm: Optional[float] = None
    distancia_rodape_cm: Optional[float] = None
    partes: dict[str, str] = field(default_factory=dict)
    divergencia_entre_secoes: list[str] = field(default_factory=list)


def _textos(parte) -> list[str]:
    if parte is None:
        return []
    textos = [normalizar_texto(p.text) for p in parte.paragraphs]
    for tabela in parte.tables:
        for paragrafo in iter_paragrafos_tabela(tabela):
            textos.append(normalizar_texto(paragrafo.text))
    return [t for t in textos if t]


def _conta_desenhos(parte) -> int:
    if parte is None:
        return 0
    return sum(1 for _ in parte._element.iter(qn("w:drawing")))


def _tem_campo_pagina(parte) -> bool:
    if parte is None:
        return False
    for elemento in parte._element.iter():
        if elemento.tag == qn("w:instrText") and elemento.text:
            if re.search(r"\bPAGE\b", elemento.text):
                return True
        if elemento.tag == qn("w:fldSimple"):
            instrucao = elemento.get(qn("w:instr")) or ""
            if re.search(r"\bPAGE\b", instrucao):
                return True
    return False


def resumir(documento, caminho: Optional[Path] = None) -> ResumoCabecalhoRodape:
    """Levanta o estado do cabeçalho e do rodapé, sem alterá-los."""
    resumo = ResumoCabecalhoRodape(secoes=len(documento.sections))
    assinaturas_por_secao: list[tuple[str, str]] = []

    for indice, secao in enumerate(documento.sections):
        # Só lê partes já existentes — ler as demais criaria o cabeçalho no
        # pacote (ver `partes_cabecalho_rodape` em util_ooxml).
        cabecalho = None if secao.header.is_linked_to_previous else secao.header
        rodape = None if secao.footer.is_linked_to_previous else secao.footer
        if indice == 0:
            resumo.imagens_cabecalho = _conta_desenhos(cabecalho)
            resumo.imagens_rodape = _conta_desenhos(rodape)
            resumo.textos_cabecalho = _textos(cabecalho)
            resumo.textos_rodape = _textos(rodape)
            resumo.campo_pagina_no_rodape = _tem_campo_pagina(rodape)
            if secao.header_distance is not None:
                resumo.distancia_cabecalho_cm = round(secao.header_distance.cm, 2)
            if secao.footer_distance is not None:
                resumo.distancia_rodape_cm = round(secao.footer_distance.cm, 2)
        assinaturas_por_secao.append((
            "|".join(_textos(cabecalho)) + f"#img{_conta_desenhos(cabecalho)}",
            "|".join(_textos(rodape)) + f"#img{_conta_desenhos(rodape)}",
        ))

    if len(assinaturas_por_secao) > 1:
        base = assinaturas_por_secao[0]
        for indice, atual in enumerate(assinaturas_por_secao[1:], start=1):
            if atual[0] != base[0]:
                resumo.divergencia_entre_secoes.append(
                    f"Seção {indice}: cabeçalho difere da seção 1."
                )
            if atual[1] != base[1]:
                resumo.divergencia_entre_secoes.append(
                    f"Seção {indice}: rodapé difere da seção 1."
                )

    if caminho is not None:
        resumo.partes = assinaturas_partes(Path(caminho))
    return resumo


def comparar_partes_protegidas(antes: dict[str, str],
                               depois: dict[str, str]) -> list[str]:
    """Compara os hashes das partes protegidas antes e depois da formatação."""
    divergencias: list[str] = []
    faltando = sorted(set(antes) - set(depois))
    novas = sorted(set(depois) - set(antes))
    for nome in faltando:
        divergencias.append(f"Parte protegida REMOVIDA: {nome}")
    for nome in novas:
        divergencias.append(f"Parte protegida ACRESCENTADA: {nome}")
    for nome in sorted(set(antes) & set(depois)):
        if antes[nome] != depois[nome]:
            divergencias.append(f"Parte protegida ALTERADA: {nome}")
    return divergencias


def comparar_com_minuta_mae(caminho_documento: Path,
                            caminho_minuta: Path) -> list[str]:
    """
    Compara cabeçalho, rodapé e mídia do documento com os da minuta-mãe.

    Diferença aqui é sinal de que o timbre foi perdido no caminho — é reportada,
    nunca "corrigida" automaticamente.
    """
    from docx import Document

    divergencias: list[str] = []
    partes_doc = assinaturas_partes(caminho_documento)
    partes_min = assinaturas_partes(caminho_minuta)

    midia_doc = {k for k in partes_doc if k.startswith("word/media/")}
    midia_min = {k for k in partes_min if k.startswith("word/media/")}
    if len(midia_doc) < len(midia_min):
        divergencias.append(
            f"O documento tem {len(midia_doc)} arquivo(s) de mídia contra "
            f"{len(midia_min)} da minuta-mãe — possível perda de brasão/logotipo."
        )

    hashes_doc = set(partes_doc.values())
    ausentes = [n for n, h in partes_min.items()
                if n.startswith("word/media/") and h not in hashes_doc]
    if ausentes:
        divergencias.append(
            "Imagens da minuta-mãe não encontradas no documento: "
            + ", ".join(sorted(ausentes))
        )

    resumo_doc = resumir(Document(str(caminho_documento)))
    resumo_min = resumir(Document(str(caminho_minuta)))
    if resumo_doc.imagens_cabecalho != resumo_min.imagens_cabecalho:
        divergencias.append(
            f"Imagens no cabeçalho: documento {resumo_doc.imagens_cabecalho}, "
            f"minuta-mãe {resumo_min.imagens_cabecalho}."
        )
    if resumo_doc.imagens_rodape != resumo_min.imagens_rodape:
        divergencias.append(
            f"Imagens no rodapé: documento {resumo_doc.imagens_rodape}, "
            f"minuta-mãe {resumo_min.imagens_rodape}."
        )
    if resumo_doc.textos_cabecalho != resumo_min.textos_cabecalho:
        divergencias.append("Texto do cabeçalho difere do da minuta-mãe.")
    if resumo_doc.textos_rodape != resumo_min.textos_rodape:
        divergencias.append("Texto do rodapé difere do da minuta-mãe.")
    if resumo_doc.campo_pagina_no_rodape != resumo_min.campo_pagina_no_rodape:
        divergencias.append("Presença do campo de paginação no rodapé difere da minuta-mãe.")
    return divergencias


def partes_protegidas_intactas(origem: Path, destino: Path) -> tuple[bool, list[str]]:
    """Verificação final: nenhuma parte protegida pode ter mudado."""
    divergencias = comparar_partes_protegidas(
        assinaturas_partes(origem), assinaturas_partes(destino)
    )
    return (not divergencias), divergencias
