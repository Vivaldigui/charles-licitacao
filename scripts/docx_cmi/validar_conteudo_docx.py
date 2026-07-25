#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validar_conteudo_docx.py — Garantia de que a formatação não alterou o conteúdo.

Extrai uma representação normalizada do documento antes e depois da
padronização, compara e classifica cada diferença. Diferença não autorizada
BLOQUEIA a saída.

A representação normalizada ignora espaços redundantes e parágrafos vazios —
por isso remover espaçador em branco e colapsar espaço duplo não aparecem como
diferença de conteúdo (são as diferenças permitidas do item 21 do escopo).
"""
from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field
from typing import Optional

from util_ooxml import (
    hash_conteudo,
    iter_paragrafos_cabecalho_rodape,
    iter_paragrafos_corpo,
    normalizar_texto,
    texto_paragrafo,
)

RE_ROTULO_INICIAL = re.compile(r"^(\d+(?:\.\d+)*)\s*[\.\)\-–—]?\s+")


@dataclass
class Conteudo:
    """Representação normalizada e comparável de um documento."""

    paragrafos: list[str] = field(default_factory=list)
    celulas: list[str] = field(default_factory=list)
    cabecalho_rodape: list[str] = field(default_factory=list)
    assinatura: str = ""

    def linhas(self) -> list[str]:
        return (
            [f"P|{t}" for t in self.paragrafos]
            + [f"C|{t}" for t in self.celulas]
            + [f"H|{t}" for t in self.cabecalho_rodape]
        )


@dataclass
class Diferenca:
    tipo: str
    antes: str
    depois: str
    autorizada: bool
    motivo: str = ""


@dataclass
class ResultadoValidacao:
    hash_antes: str
    hash_depois: str
    diferencas: list[Diferenca] = field(default_factory=list)
    paragrafos_antes: int = 0
    paragrafos_depois: int = 0
    celulas_antes: int = 0
    celulas_depois: int = 0

    @property
    def conteudo_preservado(self) -> bool:
        return all(d.autorizada for d in self.diferencas)

    @property
    def nao_autorizadas(self) -> list[Diferenca]:
        return [d for d in self.diferencas if not d.autorizada]


def extrair(documento) -> Conteudo:
    """Extrai o conteúdo normalizado do documento."""
    from tabelas_docx import grade_textual

    conteudo = Conteudo()
    for paragrafo in documento.paragraphs:
        texto = normalizar_texto(texto_paragrafo(paragrafo))
        if texto:
            conteudo.paragrafos.append(texto)
    for tabela in grade_textual(documento):
        for linha in tabela:
            for celula in linha:
                if celula:
                    conteudo.celulas.append(celula)
    for paragrafo in iter_paragrafos_cabecalho_rodape(documento):
        texto = normalizar_texto(texto_paragrafo(paragrafo))
        if texto:
            conteudo.cabecalho_rodape.append(texto)
    conteudo.assinatura = hash_conteudo(conteudo.linhas())
    return conteudo


def _classificar(antes: str, depois: str,
                 renumeracoes: dict[str, set[str]],
                 substituicoes: dict[str, str]) -> Diferenca:
    """Decide se uma linha alterada corresponde a mudança autorizada."""
    sem_marca_antes = antes[2:] if antes[1:2] == "|" else antes
    sem_marca_depois = depois[2:] if depois[1:2] == "|" else depois

    # Renumeração previamente autorizada: só o rótulo inicial mudou.
    m_antes = RE_ROTULO_INICIAL.match(sem_marca_antes)
    m_depois = RE_ROTULO_INICIAL.match(sem_marca_depois)
    if m_antes and m_depois:
        resto_antes = sem_marca_antes[m_antes.end():]
        resto_depois = sem_marca_depois[m_depois.end():]
        if resto_antes == resto_depois:
            rotulo_antigo, rotulo_novo = m_antes.group(1), m_depois.group(1)
            # Um mesmo rótulo antigo pode ter mais de um destino quando o
            # documento o repetia (ex.: dois itens "4.1." viram "3.1." e "3.2.").
            if rotulo_novo in renumeracoes.get(rotulo_antigo, set()):
                return Diferenca(
                    tipo="renumeracao_autorizada", antes=antes, depois=depois,
                    autorizada=True,
                    motivo=f"Renumeração aprovada: {rotulo_antigo} -> {rotulo_novo}.",
                )
            return Diferenca(
                tipo="renumeracao_nao_autorizada", antes=antes, depois=depois,
                autorizada=False,
                motivo=f"Rótulo mudou de {rotulo_antigo} para {rotulo_novo} sem "
                       f"autorização de renumeração.",
            )

    # Substituição de campo declarada.
    if substituicoes:
        esperado = sem_marca_antes
        for marcador, valor in substituicoes.items():
            esperado = esperado.replace(marcador, valor)
        if normalizar_texto(esperado) == sem_marca_depois:
            return Diferenca(
                tipo="campo_preenchido", antes=antes, depois=depois,
                autorizada=True,
                motivo="Marcador de campo substituído conforme declarado.",
            )

    return Diferenca(
        tipo="texto_alterado", antes=antes, depois=depois, autorizada=False,
        motivo="Texto de conteúdo foi alterado pela formatação.",
    )


def comparar(antes: Conteudo, depois: Conteudo,
             renumeracoes: Optional[dict[str, set[str]]] = None,
             substituicoes: Optional[dict[str, str]] = None,
             blocos_removidos_autorizados: Optional[list[str]] = None
             ) -> ResultadoValidacao:
    """
    Compara os dois conteúdos e classifica as diferenças.

    `renumeracoes`: {rotulo_antigo: {rotulos_novos}} já aprovados.
    `substituicoes`: {marcador: valor} já aplicados no preenchimento.
    `blocos_removidos_autorizados`: textos de blocos alternativos ("OU") cuja
    remoção foi decidida antes da formatação.
    """
    renumeracoes = renumeracoes or {}
    substituicoes = substituicoes or {}
    autorizados = {normalizar_texto(t) for t in (blocos_removidos_autorizados or [])}

    resultado = ResultadoValidacao(
        hash_antes=antes.assinatura,
        hash_depois=depois.assinatura,
        paragrafos_antes=len(antes.paragrafos),
        paragrafos_depois=len(depois.paragrafos),
        celulas_antes=len(antes.celulas),
        celulas_depois=len(depois.celulas),
    )
    if antes.assinatura == depois.assinatura:
        return resultado

    linhas_antes, linhas_depois = antes.linhas(), depois.linhas()
    matcher = difflib.SequenceMatcher(a=linhas_antes, b=linhas_depois, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        if tag == "replace":
            bloco_a = linhas_antes[i1:i2]
            bloco_b = linhas_depois[j1:j2]
            for indice in range(max(len(bloco_a), len(bloco_b))):
                a = bloco_a[indice] if indice < len(bloco_a) else ""
                b = bloco_b[indice] if indice < len(bloco_b) else ""
                if a and b:
                    resultado.diferencas.append(
                        _classificar(a, b, renumeracoes, substituicoes)
                    )
                elif a:
                    resultado.diferencas.append(_perda(a, autorizados))
                else:
                    resultado.diferencas.append(_acrescimo(b))
        elif tag == "delete":
            for a in linhas_antes[i1:i2]:
                resultado.diferencas.append(_perda(a, autorizados))
        elif tag == "insert":
            for b in linhas_depois[j1:j2]:
                resultado.diferencas.append(_acrescimo(b))
    return resultado


def _perda(linha: str, autorizados: set[str]) -> Diferenca:
    texto = linha[2:] if linha[1:2] == "|" else linha
    if texto in autorizados:
        return Diferenca(
            tipo="bloco_alternativo_removido", antes=linha, depois="",
            autorizada=True,
            motivo="Bloco alternativo não aplicável, removido por decisão prévia.",
        )
    return Diferenca(
        tipo="conteudo_perdido", antes=linha, depois="", autorizada=False,
        motivo="Trecho existente antes da formatação desapareceu.",
    )


def _acrescimo(linha: str) -> Diferenca:
    return Diferenca(
        tipo="conteudo_acrescentado", antes="", depois=linha, autorizada=False,
        motivo="Texto que não existia foi acrescentado pela formatação.",
    )


# --------------------------------------------------------------------------- #
# Pendências do documento final
# --------------------------------------------------------------------------- #

@dataclass
class Pendencias:
    campos_pendentes: list[str] = field(default_factory=list)
    blocos_ou: list[int] = field(default_factory=list)
    opcoes_nao_marcadas: list[int] = field(default_factory=list)
    texto_destacado: list[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        return (len(self.campos_pendentes) + len(self.blocos_ou)
                + len(self.opcoes_nao_marcadas) + len(self.texto_destacado))


def levantar_pendencias(documento) -> Pendencias:
    """Marcadores, blocos alternativos e destaques que impedem a assinatura."""
    from util_ooxml import BLOCO_OU_RE, OPCAO_NAO_MARCADA_RE, marcadores_pendentes

    pendencias = Pendencias()
    for indice, paragrafo in enumerate(iter_paragrafos_corpo(documento)):
        texto = texto_paragrafo(paragrafo)
        if not texto.strip():
            continue
        for marcador in marcadores_pendentes(texto):
            pendencias.campos_pendentes.append(f"parágrafo {indice}: {marcador}")
        if BLOCO_OU_RE.match(texto.strip()):
            pendencias.blocos_ou.append(indice)
        if OPCAO_NAO_MARCADA_RE.search(texto):
            pendencias.opcoes_nao_marcadas.append(indice)
        for run in paragrafo.runs:
            if not (run.text or "").strip():
                continue
            cor = run.font.color
            if cor is not None and cor.type is not None and cor.rgb is not None:
                valor = str(cor.rgb)
                if cor_avermelhada(valor):
                    pendencias.texto_destacado.append(
                        f"parágrafo {indice}: texto em #{valor} — "
                        f"provável instrução de preenchimento"
                    )
                    break
    return pendencias


def cor_avermelhada(hexadecimal: str) -> bool:
    """
    True para vermelhos usados como marcação de preenchimento nas minutas.

    Nas minutas de contrato da Câmara o vermelho (FF0000, CC0000, C00000)
    identifica campo a completar. É pendência a reportar — nunca cor a
    "corrigir" silenciosamente.
    """
    try:
        vermelho = int(hexadecimal[0:2], 16)
        verde = int(hexadecimal[2:4], 16)
        azul = int(hexadecimal[4:6], 16)
    except (ValueError, IndexError):
        return False
    return vermelho >= 0x80 and vermelho - verde >= 0x40 and vermelho - azul >= 0x40
