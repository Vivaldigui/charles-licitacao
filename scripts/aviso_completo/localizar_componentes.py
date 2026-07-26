#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
localizar_componentes.py — descoberta e qualificação das peças do aviso completo.

Responde a três perguntas, e recusa-se a responder por conta própria àquilo que
é decisão administrativa:

1. Onde estão o aviso, o TR, o modelo de proposta, a declaração e o contrato?
2. O TR encontrado pertence MESMO a este processo e está apto a ser anexado?
3. Haverá Termo de Contrato? — decidido pela ordem de precedência do item 4 do
   escopo, nunca por semelhança de nome do objeto.

Nada aqui grava arquivo: a etapa só localiza, lê e classifica.
"""
from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "docx_cmi"))

from ocorrencias import Registro

RAIZ = Path(__file__).resolve().parents[2]
PASTA_MINUTAS = RAIZ / "05_minutas"

MINUTA_AVISO = PASTA_MINUTAS / "AVISO" / "AVISO_CONTRATACAO_DIRETA_MINUTA_MAE.docx"
FICHA_AVISO = PASTA_MINUTAS / "AVISO" / "AVISO_CONTRATACAO_DIRETA_FICHA_DE_USO.md"
MINUTA_PROPOSTA = (PASTA_MINUTAS / "PROPOSTA_COMERCIAL"
                   / "PROPOSTA_COMERCIAL_MINUTA_MAE.docx")
MINUTA_DECLARACAO = (PASTA_MINUTAS / "DECLARACAO_UNIFICADA"
                     / "DECLARACAO_UNIFICADA_MINUTA_MAE.docx")

ETAPA = "localização de componentes"

# Tipos de instrumento previstos no manifesto (item 4 do escopo).
TIPOS_INSTRUMENTO = (
    "contrato",
    "ordem_fornecimento",
    "nota_empenho",
    "autorizacao_fornecimento",
    "outro",
)

MSG_SEM_MINUTA_CONTRATO = (
    "Não há minuta de contrato oficial adequada cadastrada para este objeto."
)

# Nomes que denunciam um TR que não pode ser anexado (item 2.3 do escopo).
RE_TR_RASCUNHO = re.compile(
    r"(rascunho|draft|provis[oó]ri|prelimin|vers[aã]o[_ -]?0|_wip|minuta_mae)",
    re.IGNORECASE,
)
RE_TR_NOME = re.compile(r"(^|[_\-\s])TR([_\-\s]|$)|TERMO[_\-\s]?DE[_\-\s]?REFER",
                        re.IGNORECASE)


# --------------------------------------------------------------------------- #
# Manifesto
# --------------------------------------------------------------------------- #

MANIFESTO_PADRAO = "manifesto_aviso_completo.json"


def carregar_manifesto(caminho: Path) -> dict[str, Any]:
    """Lê o manifesto do processo. Erro de JSON é erro de entrada, não silêncio."""
    caminho = Path(caminho)
    if not caminho.exists():
        raise FileNotFoundError(f"Manifesto não encontrado: {caminho}")
    try:
        return json.loads(caminho.read_text(encoding="utf-8"))
    except json.JSONDecodeError as erro:
        raise ValueError(f"Manifesto inválido ({caminho}): {erro}") from erro


def descobrir_manifesto(pasta_processo: Path) -> Optional[Path]:
    """Procura o manifesto na pasta do processo e em `07_AVISO_COMPLETO/`."""
    candidatos = [
        pasta_processo / MANIFESTO_PADRAO,
        pasta_processo / "07_AVISO_COMPLETO" / MANIFESTO_PADRAO,
    ]
    return next((c for c in candidatos if c.exists()), None)


# --------------------------------------------------------------------------- #
# Estruturas
# --------------------------------------------------------------------------- #

@dataclass
class Componente:
    """Uma peça do aviso completo, já localizada em disco."""

    chave: str                  # aviso | habilitacao | tr | proposta | contrato | declaracao
    titulo: str                 # título do anexo, sem o rótulo "ANEXO N"
    caminho: Optional[Path]
    origem: str                 # de onde veio (minuta oficial, processo, manifesto)
    obrigatorio: bool = True
    incluir: bool = True
    perfil: str = "generico"    # perfil documental de padronização
    observacoes: list[str] = field(default_factory=list)


@dataclass
class InstrumentoContratual:
    """Decisão sobre a formalização da contratação."""

    tipo: Optional[str] = None
    incluir_minuta: bool = False
    minuta: Optional[Path] = None
    fonte_da_decisao: Optional[str] = None
    definido: bool = False


@dataclass
class Componentes:
    """Resultado da etapa de localização."""

    manifesto: dict[str, Any]
    caminho_manifesto: Optional[Path]
    pasta_processo: Optional[Path]
    instrumento: InstrumentoContratual
    itens: list[Componente] = field(default_factory=list)
    ficha_aviso: Optional[str] = None
    minutas_utilizadas: list[str] = field(default_factory=list)

    def obter(self, chave: str) -> Optional[Componente]:
        return next((c for c in self.itens if c.chave == chave), None)

    def incluidos(self) -> list[Componente]:
        return [c for c in self.itens if c.incluir and c.caminho is not None]


# --------------------------------------------------------------------------- #
# Termo de Referência
# --------------------------------------------------------------------------- #

def catalogo_minutas_contrato() -> dict[str, Path]:
    """Minutas de contrato oficiais cadastradas na biblioteca da Câmara."""
    catalogo: dict[str, Path] = {}
    for pasta in sorted(PASTA_MINUTAS.glob("CONTRATO*")):
        if not pasta.is_dir():
            continue
        for minuta in sorted(pasta.glob("*_MINUTA_MAE.docx")):
            catalogo[minuta.name] = minuta
    return catalogo


def _candidatos_tr(pasta_processo: Path) -> list[Path]:
    """TRs plausíveis dentro da pasta do processo, do mais canônico ao menos."""
    canonico = pasta_processo / "03_TR" / "TR_FINAL.docx"
    if canonico.exists():
        return [canonico]
    encontrados = [
        arquivo
        for arquivo in sorted(pasta_processo.rglob("*.docx"))
        if RE_TR_NOME.search(arquivo.name) and not arquivo.name.startswith("~$")
    ]
    return encontrados


def localizar_tr(manifesto: dict[str, Any], pasta_processo: Optional[Path],
                 registro: Registro,
                 caminho_explicito: Optional[Path] = None) -> Optional[Path]:
    """
    Localiza o Termo de Referência JÁ ELABORADO do processo.

    O TR nunca é gerado nem escolhido por aproximação: ou veio indicado, ou está
    no caminho canônico do processo, ou a montagem para. Ambiguidade entre vários
    arquivos é bloqueio, não sorteio.
    """
    indicado = caminho_explicito or manifesto.get("arquivos", {}).get("termo_referencia")
    if indicado:
        caminho = Path(indicado)
        if not caminho.is_absolute():
            caminho = (RAIZ / caminho) if (RAIZ / caminho).exists() else caminho
        if not caminho.exists():
            registro.bloqueante(
                ETAPA, f"Termo de Referência indicado não foi localizado: {indicado}.",
                origem=str(indicado),
            )
            return None
        return caminho

    if pasta_processo is None:
        registro.bloqueante(
            ETAPA,
            "Termo de Referência não indicado e nenhuma pasta de processo "
            "informada. Informe --tr ou o campo arquivos.termo_referencia.",
        )
        return None

    candidatos = _candidatos_tr(pasta_processo)
    if not candidatos:
        registro.bloqueante(
            ETAPA,
            f"Termo de Referência não localizado em {pasta_processo}. O aviso "
            "completo não gera TR: ele anexa o TR já elaborado e aprovado.",
        )
        return None
    if len(candidatos) > 1:
        nomes = ", ".join(c.name for c in candidatos)
        registro.bloqueante(
            ETAPA,
            "Mais de um Termo de Referência candidato na pasta do processo "
            f"({nomes}). Indique qual usar em arquivos.termo_referencia ou --tr — "
            "a escolha do TR não pode ser adivinhada.",
        )
        return None
    return candidatos[0]


def qualificar_tr(caminho: Path, registro: Registro,
                  autorizar_rascunho: bool = False) -> None:
    """Recusa TR que a regra proíbe anexar: minuta-mãe vazia ou rascunho."""
    try:
        dentro_das_minutas = caminho.resolve().is_relative_to(PASTA_MINUTAS.resolve())
    except (OSError, ValueError):
        dentro_das_minutas = False
    if dentro_das_minutas:
        registro.bloqueante(
            ETAPA,
            "O arquivo indicado como TR é a minuta-mãe da biblioteca "
            f"({caminho.name}). A minuta-mãe é modelo em branco e não pode ser "
            "anexada como Anexo II.",
            origem=str(caminho),
        )
        return
    if RE_TR_RASCUNHO.search(caminho.name):
        if autorizar_rascunho:
            registro.alerta(
                ETAPA,
                f"O TR '{caminho.name}' tem nome de rascunho e foi aceito por "
                "autorização expressa (--autorizar-tr-rascunho).",
                origem=str(caminho),
            )
        else:
            registro.bloqueante(
                ETAPA,
                f"O TR '{caminho.name}' aparenta ser rascunho ou versão "
                "preliminar. Use o TR final aprovado ou autorize expressamente "
                "com --autorizar-tr-rascunho.",
                origem=str(caminho),
            )


# --------------------------------------------------------------------------- #
# Instrumento contratual
# --------------------------------------------------------------------------- #

RE_TR_CONTRATO = re.compile(
    r"(ser[áa]\s+(?:formalizad[ao]|firmad[ao])\s+(?:por\s+)?(?:termo\s+de\s+)?contrato"
    r"|instrumento\s+contratual\s*:\s*contrato)", re.IGNORECASE)
RE_TR_EQUIVALENTE = re.compile(
    r"(nota\s+de\s+empenho|ordem\s+de\s+fornecimento|autoriza[çc][ãa]o\s+de\s+fornecimento)"
    r"\s*(?:,|\.|\s+em\s+substitui|\s+substituir[áa])", re.IGNORECASE)


def decidir_instrumento(manifesto: dict[str, Any], registro: Registro,
                        texto_tr: str = "",
                        decisao_usuario: Optional[bool] = None,
                        minuta_usuario: Optional[Path] = None) -> InstrumentoContratual:
    """
    Resolve se haverá contrato, na ordem de precedência do item 4 do escopo.

    O Charles não decide isso sozinho. Ele lê o campo estruturado do processo, a
    determinação expressa do usuário e o TR — e, se essas fontes divergirem ou
    silenciarem, bloqueia e devolve a decisão a quem tem competência para tomá-la.
    """
    instrumento = InstrumentoContratual()
    bloco = manifesto.get("instrumento_contratual") or {}

    tipo_manifesto = (bloco.get("tipo") or "").strip().lower() or None
    if tipo_manifesto and tipo_manifesto not in TIPOS_INSTRUMENTO:
        registro.bloqueante(
            ETAPA,
            f"instrumento_contratual.tipo inválido: '{tipo_manifesto}'. "
            f"Valores aceitos: {', '.join(TIPOS_INSTRUMENTO)}.",
        )
        return instrumento

    incluir_manifesto = bloco.get("incluir_minuta_no_aviso")
    if tipo_manifesto:
        instrumento.tipo = tipo_manifesto
        instrumento.incluir_minuta = bool(
            incluir_manifesto if incluir_manifesto is not None
            else tipo_manifesto == "contrato"
        )
        instrumento.fonte_da_decisao = "campo estruturado do processo (manifesto)"
        instrumento.definido = True

    # 2. Determinação expressa do usuário — prevalece, mas divergência é bloqueio.
    if decisao_usuario is not None:
        if instrumento.definido and instrumento.incluir_minuta != decisao_usuario:
            registro.bloqueante(
                ETAPA,
                "PENDÊNCIA: definir se a contratação será formalizada por "
                "contrato ou instrumento equivalente. O manifesto indica "
                f"'{instrumento.tipo}' (incluir minuta: {instrumento.incluir_minuta}) "
                f"e a linha de comando determinou o oposto ({decisao_usuario}). "
                "Resolva a divergência no processo antes de montar o aviso.",
            )
            instrumento.definido = False
            return instrumento
        instrumento.incluir_minuta = decisao_usuario
        instrumento.tipo = instrumento.tipo or ("contrato" if decisao_usuario else "outro")
        instrumento.fonte_da_decisao = "determinação expressa do usuário"
        instrumento.definido = True

    # 3. Termo de Referência — só é consultado se as fontes acima silenciaram.
    if not instrumento.definido and texto_tr:
        if RE_TR_CONTRATO.search(texto_tr) and not RE_TR_EQUIVALENTE.search(texto_tr):
            instrumento.tipo = "contrato"
            instrumento.incluir_minuta = True
            instrumento.fonte_da_decisao = "Termo de Referência"
            instrumento.definido = True
        elif RE_TR_EQUIVALENTE.search(texto_tr) and not RE_TR_CONTRATO.search(texto_tr):
            instrumento.tipo = "outro"
            instrumento.incluir_minuta = False
            instrumento.fonte_da_decisao = "Termo de Referência"
            instrumento.definido = True

    if not instrumento.definido:
        registro.bloqueante(
            ETAPA,
            "PENDÊNCIA: definir se a contratação será formalizada por contrato "
            "ou instrumento equivalente. Nenhuma fonte do processo (manifesto, "
            "determinação do usuário ou Termo de Referência) define o "
            "instrumento contratual.",
        )
        return instrumento

    if instrumento.incluir_minuta and instrumento.tipo != "contrato":
        registro.bloqueante(
            ETAPA,
            f"O instrumento definido é '{instrumento.tipo}', mas o processo pede "
            "a inclusão de minuta de contrato no aviso. Instrumento equivalente "
            "(empenho, ordem ou autorização de fornecimento) não leva minuta de "
            "contrato anexa.",
        )
        instrumento.definido = False
        return instrumento

    if instrumento.incluir_minuta:
        _resolver_minuta_contrato(instrumento, bloco, minuta_usuario, registro)
    else:
        registro.informacao(
            ETAPA,
            f"Instrumento definido como '{instrumento.tipo}' "
            f"(fonte: {instrumento.fonte_da_decisao}). Minuta de contrato não "
            "será anexada.",
        )
    return instrumento


def _resolver_minuta_contrato(instrumento: InstrumentoContratual,
                              bloco: dict[str, Any],
                              minuta_usuario: Optional[Path],
                              registro: Registro) -> None:
    """Aceita apenas minuta de contrato oficial, indicada explicitamente."""
    catalogo = catalogo_minutas_contrato()
    indicada = minuta_usuario or bloco.get("minuta_selecionada")
    if not indicada:
        registro.bloqueante(
            ETAPA,
            "Haverá Termo de Contrato, mas nenhuma minuta foi selecionada. A "
            "minuta é escolhida no processo (natureza do objeto, duração, "
            "execução imediata ou continuada), nunca por semelhança de nome. "
            "Cadastradas: " + ", ".join(sorted(catalogo)) + ".",
        )
        instrumento.definido = False
        return

    caminho = Path(indicada)
    if not caminho.is_absolute() and (RAIZ / caminho).exists():
        caminho = RAIZ / caminho
    oficial = catalogo.get(caminho.name)
    if oficial is None or not caminho.exists():
        registro.bloqueante(ETAPA, MSG_SEM_MINUTA_CONTRATO, origem=str(indicada))
        instrumento.definido = False
        return
    if oficial.resolve() != caminho.resolve():
        registro.bloqueante(
            ETAPA,
            f"A minuta indicada ({caminho}) não é a minuta oficial de mesmo nome "
            f"({oficial}). Contrato só é anexado a partir da biblioteca oficial.",
            origem=str(indicada),
        )
        instrumento.definido = False
        return

    instrumento.minuta = oficial
    registro.informacao(
        ETAPA,
        f"Minuta de contrato selecionada: {oficial.relative_to(RAIZ).as_posix()} "
        f"(fonte da decisão: {instrumento.fonte_da_decisao}).",
    )


# --------------------------------------------------------------------------- #
# Orquestração da etapa
# --------------------------------------------------------------------------- #

def _exigir(caminho: Path, rotulo: str, registro: Registro) -> Optional[Path]:
    if caminho.exists():
        return caminho
    registro.bloqueante(ETAPA, f"{rotulo} não encontrado(a): {caminho}.")
    return None


def localizar(manifesto: dict[str, Any], registro: Registro,
              pasta_processo: Optional[Path] = None,
              caminho_manifesto: Optional[Path] = None,
              tr_explicito: Optional[Path] = None,
              aviso_explicito: Optional[Path] = None,
              contrato_explicito: Optional[Path] = None,
              decisao_contrato: Optional[bool] = None,
              autorizar_tr_rascunho: bool = False,
              texto_tr: str = "") -> Componentes:
    """Executa as etapas 2 a 5 e 10 a 11 do fluxo de montagem (item 6 do escopo)."""
    aviso = Path(aviso_explicito) if aviso_explicito else Path(
        manifesto.get("arquivos", {}).get("aviso_minuta") or MINUTA_AVISO
    )
    if not aviso.is_absolute() and (RAIZ / aviso).exists():
        aviso = RAIZ / aviso
    aviso = _exigir(aviso, "Minuta-mãe do aviso", registro)

    ficha = None
    if FICHA_AVISO.exists():
        ficha = FICHA_AVISO.read_text(encoding="utf-8")
        registro.informacao(
            ETAPA,
            "Ficha de uso do aviso lida: "
            f"{FICHA_AVISO.relative_to(RAIZ).as_posix()}.",
        )
    else:
        registro.alerta(
            ETAPA,
            f"Ficha de uso do aviso não encontrada em {FICHA_AVISO}. A montagem "
            "seguiu sem as instruções de uso da minuta.",
        )

    tr = localizar_tr(manifesto, pasta_processo, registro, tr_explicito)
    if tr is not None:
        qualificar_tr(tr, registro, autorizar_tr_rascunho)

    instrumento = decidir_instrumento(
        manifesto, registro, texto_tr=texto_tr,
        decisao_usuario=decisao_contrato,
        minuta_usuario=contrato_explicito,
    )

    itens = [
        Componente("aviso", "AVISO DE CONTRATAÇÃO DIRETA", aviso,
                   "minuta oficial", perfil="aviso"),
        Componente("habilitacao", "DOCUMENTOS EXIGIDOS PARA HABILITAÇÃO", aviso,
                   "minuta oficial do aviso (Anexo I incorporado)", perfil="aviso"),
        Componente("tr", "TERMO DE REFERÊNCIA", tr,
                   "documento do processo", perfil="tr"),
        Componente("proposta", "MODELO DE PROPOSTA COMERCIAL",
                   _exigir(MINUTA_PROPOSTA, "Minuta do modelo de proposta", registro),
                   "minuta oficial", perfil="declaracao"),
        Componente("contrato", "MINUTA DE CONTRATO", instrumento.minuta,
                   "minuta oficial", obrigatorio=False,
                   incluir=bool(instrumento.incluir_minuta and instrumento.minuta),
                   perfil="contrato"),
        Componente("declaracao", "DECLARAÇÃO CONJUNTA",
                   _exigir(MINUTA_DECLARACAO, "Minuta da declaração", registro),
                   "minuta oficial", perfil="declaracao"),
    ]

    minutas = [
        c.caminho.relative_to(RAIZ).as_posix()
        for c in itens
        if c.caminho is not None and c.incluir
        and _dentro_das_minutas(c.caminho) and c.chave != "habilitacao"
    ]

    return Componentes(
        manifesto=manifesto,
        caminho_manifesto=caminho_manifesto,
        pasta_processo=pasta_processo,
        instrumento=instrumento,
        itens=itens,
        ficha_aviso=ficha,
        minutas_utilizadas=sorted(set(minutas)),
    )


def _dentro_das_minutas(caminho: Path) -> bool:
    try:
        return caminho.resolve().is_relative_to(PASTA_MINUTAS.resolve())
    except (OSError, ValueError):
        return False
