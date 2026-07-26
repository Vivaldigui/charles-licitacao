#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extrair_dados_tr.py — leitura do Termo de Referência já elaborado.

O TR é a fonte dos itens, quantidades e prazos que o aviso e o modelo de
proposta precisam repetir. Este módulo apenas LÊ: não corrige, não completa e
não normaliza o que o TR diz. Quando um dado não está no TR, ele fica ausente e
é reportado — inventar quantidade ou prazo seria falsificar a instrução do
processo.
"""
from __future__ import annotations

import re
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "docx_cmi"))

from ocorrencias import Registro
from util_ooxml import (
    exigir_python_docx,
    iter_paragrafos_corpo,
    marcadores_pendentes,
    texto_paragrafo,
)

ETAPA = "extração do Termo de Referência"

RE_PROCESSO = re.compile(
    r"processo\s*(?:administrativo)?\s*n?[.ºo°]*\s*[:\-]?\s*(\d{1,4}\s*/\s*\d{4})",
    re.IGNORECASE)
# O número precisa vir COLADO à palavra 'dispensa'. Com folga de algumas
# palavras no meio, "dispensa de licitação, nos termos da Lei nº 14.133/2021" e
# "dispensa ... Portaria nº 06/2024" seriam lidos como número da dispensa. O
# lookbehind afasta o mesmo erro vindo de "14.133".
RE_DISPENSA = re.compile(
    r"(?:dispensa(?:\s+de\s+licita[çc][ãa]o|\s+eletr[ôo]nica)?"
    r"|aviso\s+de\s+contrata[çc][ãa]o\s+direta)"
    r"\s*n?[.ºo°]{0,3}\s*[:\-]?\s*(?<![\d.])(\d{1,4}\s*/\s*\d{4})",
    re.IGNORECASE)
RE_SOLICITACAO = re.compile(
    r"solicita[çc][ãa]o\s*n?[.ºo°]*\s*[:\-]?\s*(\d{1,4}\s*/\s*\d{4})", re.IGNORECASE)
RE_OBJETO = re.compile(r"^\s*(?:1\s*[\-.–]?\s*)?OBJETO\s*[:\-]\s*(.+)$",
                       re.IGNORECASE)

# Colunas do quadro de itens, em todas as grafias já vistas nas minutas da Câmara.
COLUNAS = {
    "item": ("item", "n", "no", "num", "numero"),
    "codigo": ("codigo", "catmat", "catser", "cod"),
    "descricao": ("especificacao", "descricao", "discriminacao", "objeto",
                  "especificacoes"),
    "unidade": ("unidade", "unidade de medida", "und", "un", "um"),
    "quantidade": ("quantidade", "quantidade estimada", "qntd", "qtde", "qtd"),
    "valor_unitario": ("valor medio", "valor unitario", "preco unitario",
                       "valor unitario estimado", "valor medio unitario"),
    "valor_total": ("valor total", "valor total estimado", "total"),
}

# Exigências que só entram no Anexo I se o TR as previr (item 7 do escopo).
SINAIS_TR = {
    "qualificacao_tecnica": re.compile(
        r"(atestado\s+de\s+capacidade\s+t[ée]cnica|qualifica[çc][ãa]o\s+t[ée]cnica"
        r"|registro\s+(?:no|junto\s+ao)\s+(?:CREA|CRC|CRM|conselho))", re.IGNORECASE),
    "qualificacao_economica": re.compile(
        r"(qualifica[çc][ãa]o\s+econ[ôo]mic|balan[çc]o\s+patrimonial"
        r"|certid[ãa]o\s+negativa\s+de\s+fal[êe]ncia)", re.IGNORECASE),
    "amostra": re.compile(r"\bamostra", re.IGNORECASE),
    "catalogo": re.compile(r"(cat[áa]logo|ficha\s+t[ée]cnica|prospecto)", re.IGNORECASE),
    "garantia": re.compile(r"\bgarantia\b", re.IGNORECASE),
    "marca": re.compile(r"\bmarca\b", re.IGNORECASE),
}

# Sem isto, "Não será exigida qualificação econômico-financeira" seria lido como
# exigência de qualificação econômico-financeira — e o Anexo I passaria a ser
# acusado de omitir um documento que o TR justamente dispensou.
RE_NEGACAO = re.compile(
    r"\bn[ãa]o\s+(?:ser[áã]o?|se|haver[áã]|foi|s[ãa]o)?\s*"
    r"(?:exigid|exigir|aplic|demandad|requerid|solicitad|necess[áa]ri)",
    re.IGNORECASE)

PRAZOS = {
    "prazo_entrega": re.compile(
        r"prazo\s+(?:m[áa]ximo\s+)?(?:de|para)\s+entrega[^.\n]{0,120}", re.IGNORECASE),
    "prazo_execucao": re.compile(
        r"prazo\s+(?:de|para)\s+execu[çc][ãa]o[^.\n]{0,120}", re.IGNORECASE),
    "prazo_vigencia": re.compile(
        r"(?:prazo\s+de\s+)?vig[êe]ncia[^.\n]{0,120}", re.IGNORECASE),
    "validade_proposta": re.compile(
        r"(?:prazo\s+de\s+)?validade\s+da\s+proposta[^.\n]{0,120}", re.IGNORECASE),
    "local_entrega": re.compile(r"local\s+de\s+entrega[^.\n]{0,140}", re.IGNORECASE),
    "forma_pagamento": re.compile(
        r"(?:forma|condi[çc][õo]es)\s+de\s+pagamento[^.\n]{0,140}", re.IGNORECASE),
}


@dataclass
class ItemTR:
    """Uma linha do quadro de itens do TR, exatamente como está escrita nele."""

    numero: str
    descricao: str
    unidade: str
    quantidade: str
    codigo: str = ""
    valor_unitario: str = ""
    valor_total: str = ""

    def como_dicionario(self) -> dict[str, str]:
        return {
            "item": self.numero,
            "descricao": self.descricao,
            "unidade": self.unidade,
            "quantidade": self.quantidade,
            "codigo": self.codigo,
        }


@dataclass
class DadosTR:
    """Tudo o que a montagem precisa saber do TR — e nada além disso."""

    caminho: Path
    texto: str = ""
    numero_processo: Optional[str] = None
    numero_dispensa: Optional[str] = None
    objeto: Optional[str] = None
    itens: list[ItemTR] = field(default_factory=list)
    prazos: dict[str, str] = field(default_factory=dict)
    sinais: dict[str, bool] = field(default_factory=dict)
    evidencias: dict[str, str] = field(default_factory=dict)
    campos_pendentes: list[str] = field(default_factory=list)

    def como_dicionario(self) -> dict[str, Any]:
        return {
            "arquivo": self.caminho.name,
            "numero_processo": self.numero_processo,
            "numero_dispensa": self.numero_dispensa,
            "objeto": self.objeto,
            "quantidade_de_itens": len(self.itens),
            "itens": [item.como_dicionario() for item in self.itens],
            "prazos": self.prazos,
            "sinais": self.sinais,
            "evidencias": self.evidencias,
            "campos_pendentes": self.campos_pendentes,
        }


def _chave(texto: str) -> str:
    """Normaliza cabeçalho de coluna: sem acento, minúsculo, espaços colapsados."""
    sem_acento = "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )
    return re.sub(r"[^a-z0-9 ]+", " ", sem_acento.lower()).strip()


def _mapear_colunas(linha) -> dict[str, int]:
    """Casa os cabeçalhos da tabela com os campos conhecidos do quadro de itens."""
    mapa: dict[str, int] = {}
    for indice, celula in enumerate(linha.cells):
        chave = _chave(celula.text)
        if not chave:
            continue
        for campo, sinonimos in COLUNAS.items():
            if campo in mapa:
                continue
            if chave in sinonimos or any(chave.startswith(s) for s in sinonimos):
                mapa[campo] = indice
                break
    return mapa


def _quadro_de_itens(documento):
    """
    Escolhe a tabela que é o quadro de itens.

    Critério: cabeçalho com descrição e (unidade ou quantidade). Documentos da
    Câmara têm também tabelas de dados cadastrais e de dotação — se a escolha
    fosse "a maior tabela", o modelo de proposta sairia com as linhas erradas.
    """
    melhor, melhor_mapa, melhor_nota = None, {}, 0
    for tabela in documento.tables:
        if len(tabela.rows) < 2:
            continue
        mapa = _mapear_colunas(tabela.rows[0])
        if "descricao" not in mapa or not ({"unidade", "quantidade"} & set(mapa)):
            continue
        nota = len(mapa) * 100 + len(tabela.rows)
        if nota > melhor_nota:
            melhor, melhor_mapa, melhor_nota = tabela, mapa, nota
    return melhor, melhor_mapa


def _valor(linha, mapa: dict[str, int], campo: str) -> str:
    indice = mapa.get(campo)
    if indice is None or indice >= len(linha.cells):
        return ""
    return re.sub(r"\s+", " ", linha.cells[indice].text).strip()


def _exigencia_afirmativa(texto: str, padrao: re.Pattern[str]) -> tuple[bool, str]:
    """
    Diz se o TR EXIGE aquilo, e não apenas se menciona a palavra.

    Devolve também o trecho que sustentou a conclusão, para que o relatório possa
    mostrar a evidência em vez de pedir que se confie na regex.
    """
    ultima_negada = ""
    for achado in padrao.finditer(texto):
        janela = texto[max(0, achado.start() - 140): achado.end() + 140]
        trecho = re.sub(r"\s+", " ", janela).strip()
        if RE_NEGACAO.search(janela):
            ultima_negada = trecho
            continue
        return True, trecho
    return False, ultima_negada


def extrair(caminho: Path, registro: Registro) -> DadosTR:
    """Lê o TR e devolve os dados que alimentam o aviso e o modelo de proposta."""
    exigir_python_docx()
    from docx import Document

    caminho = Path(caminho)
    dados = DadosTR(caminho=caminho)
    documento = Document(str(caminho))

    linhas = [texto_paragrafo(p).strip() for p in iter_paragrafos_corpo(documento)]
    dados.texto = "\n".join(linha for linha in linhas if linha)

    for linha in linhas:
        if dados.objeto is None:
            achado = RE_OBJETO.match(linha)
            if achado and len(achado.group(1).strip()) > 10:
                dados.objeto = achado.group(1).strip()

    achado = RE_PROCESSO.search(dados.texto) or RE_SOLICITACAO.search(dados.texto)
    if achado:
        dados.numero_processo = re.sub(r"\s+", "", achado.group(1))
    achado = RE_DISPENSA.search(dados.texto)
    if achado:
        dados.numero_dispensa = re.sub(r"\s+", "", achado.group(1))

    tabela, mapa = _quadro_de_itens(documento)
    if tabela is None:
        registro.alerta(
            ETAPA,
            "Nenhum quadro de itens foi identificado no TR. O modelo de proposta "
            "não pode ser gerado a partir dos itens e depende de conferência "
            "humana.",
            origem=caminho.name,
        )
    else:
        for indice, linha in enumerate(tabela.rows[1:], start=1):
            descricao = _valor(linha, mapa, "descricao")
            if not descricao:
                continue
            dados.itens.append(ItemTR(
                numero=_valor(linha, mapa, "item") or str(indice),
                descricao=descricao,
                unidade=_valor(linha, mapa, "unidade"),
                quantidade=_valor(linha, mapa, "quantidade"),
                codigo=_valor(linha, mapa, "codigo"),
                valor_unitario=_valor(linha, mapa, "valor_unitario"),
                valor_total=_valor(linha, mapa, "valor_total"),
            ))
        registro.informacao(
            ETAPA,
            f"{len(dados.itens)} item(ns) extraído(s) do quadro do TR "
            f"({len(tabela.rows) - 1} linha(s) de dados).",
            origem=caminho.name,
        )

    for campo, padrao in PRAZOS.items():
        achado = padrao.search(dados.texto)
        if achado:
            dados.prazos[campo] = re.sub(r"\s+", " ", achado.group(0)).strip()

    for nome, padrao in SINAIS_TR.items():
        exigido, evidencia = _exigencia_afirmativa(dados.texto, padrao)
        dados.sinais[nome] = exigido
        if evidencia:
            dados.evidencias[nome] = evidencia

    pendentes: list[str] = []
    for linha in linhas:
        pendentes += marcadores_pendentes(linha)
    dados.campos_pendentes = sorted(set(pendentes))
    if dados.campos_pendentes:
        registro.bloqueante(
            ETAPA,
            f"O Termo de Referência tem {len(dados.campos_pendentes)} campo(s) "
            "pendente(s) de preenchimento: "
            + ", ".join(dados.campos_pendentes[:8])
            + ("..." if len(dados.campos_pendentes) > 8 else "")
            + ". TR com campo em aberto não pode ser publicado como Anexo II.",
            origem=caminho.name,
        )

    if not dados.itens:
        registro.alerta(
            ETAPA, "Nenhum item foi extraído do TR.", origem=caminho.name)
    if dados.objeto is None:
        registro.alerta(
            ETAPA,
            "Objeto não identificado no TR (esperado um parágrafo iniciado por "
            "'OBJETO:'). O objeto do manifesto será usado sem conferência cruzada.",
            origem=caminho.name,
        )
    return dados
