#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
numerar_anexos.py — ordem, numeração e referências dos anexos.

A numeração dos anexos é a única numeração que este módulo pode tocar. Artigo,
inciso, cláusula, item do TR, número de processo e número de dispensa ficam
intactos — renumerá-los alteraria conteúdo jurídico.

Com minuta de contrato:   I habilitação · II TR · III proposta · IV contrato · V declaração
Sem minuta de contrato:   I habilitação · II TR · III proposta · IV declaração

Não existe lacuna: a declaração sobe para IV quando não há contrato, e todos os
rótulos, nomes de arquivo e referências internas acompanham.
"""
from __future__ import annotations

import re
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "docx_cmi"))

from localizar_componentes import Componente, Componentes
from ocorrencias import Registro
from util_ooxml import definir_texto, elementos_texto, texto_paragrafo

ETAPA = "numeração dos anexos"

# Ordem canônica dos anexos. `contrato` é condicional; o resto é fixo.
ORDEM_CANONICA = ("habilitacao", "tr", "proposta", "contrato", "declaracao")

RE_ITEM_RELACAO = re.compile(
    r"^\s*(?:\d+(?:\.\d+)*\s*[\-–—]?\s*)?ANEXO\s+([IVXLC]+)\s*[\-–—]\s*(.+?)\s*;?\s*$",
    re.IGNORECASE)
RE_REFERENCIA = re.compile(r"\bANEXO\s+([IVXLC]+)\b", re.IGNORECASE)

_ROMANOS = ("I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X")


def romano(numero: int) -> str:
    """Converte 1..10 em algarismo romano. Mais de 10 anexos não é caso real aqui."""
    if not 1 <= numero <= len(_ROMANOS):
        raise ValueError(f"Numeração de anexo fora da faixa suportada: {numero}")
    return _ROMANOS[numero - 1]


def _ascii_maiusculo(texto: str) -> str:
    """Nome de arquivo sem acento e sem espaço — para o pacote de publicação."""
    sem_acento = "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )
    return re.sub(r"_+", "_", re.sub(r"[^A-Za-z0-9]+", "_", sem_acento)).strip("_").upper()


@dataclass
class Anexo:
    """Um anexo já posicionado e nomeado."""

    ordem: int
    chave: str
    titulo: str
    componente: Componente

    @property
    def romano(self) -> str:
        return romano(self.ordem)

    @property
    def rotulo(self) -> str:
        return f"ANEXO {self.romano} — {self.titulo}"

    @property
    def nome_componente(self) -> str:
        return f"{self.ordem:02d}_{_ascii_maiusculo(self.titulo)}.docx"

    @property
    def nome_publicacao(self) -> str:
        return f"ANEXO_{self.romano}_{_ascii_maiusculo(self.titulo)}"


@dataclass
class PlanoAnexos:
    """A ordem definitiva dos anexos deste aviso."""

    anexos: list[Anexo] = field(default_factory=list)
    aviso: Optional[Componente] = None

    @property
    def romanos(self) -> set[str]:
        return {anexo.romano for anexo in self.anexos}

    def por_chave(self, chave: str) -> Optional[Anexo]:
        return next((a for a in self.anexos if a.chave == chave), None)

    def como_lista(self) -> list[dict[str, str]]:
        return [
            {
                "ordem": str(anexo.ordem),
                "romano": anexo.romano,
                "rotulo": anexo.rotulo,
                "componente": anexo.chave,
                "arquivo": anexo.nome_componente,
                "origem": (anexo.componente.caminho.name
                           if anexo.componente.caminho else ""),
            }
            for anexo in self.anexos
        ]


def planejar(componentes: Componentes, registro: Registro) -> PlanoAnexos:
    """Monta o plano de anexos a partir dos componentes efetivamente incluídos."""
    plano = PlanoAnexos(aviso=componentes.obter("aviso"))
    ordem = 0
    for chave in ORDEM_CANONICA:
        componente = componentes.obter(chave)
        if componente is None or not componente.incluir or componente.caminho is None:
            continue
        ordem += 1
        plano.anexos.append(Anexo(ordem, chave, componente.titulo, componente))

    if not plano.anexos:
        registro.bloqueante(ETAPA, "Nenhum anexo pôde ser incluído no aviso.")
        return plano

    romanos = [anexo.romano for anexo in plano.anexos]
    if len(set(romanos)) != len(romanos):
        registro.bloqueante(
            ETAPA, f"Numeração de anexos duplicada: {', '.join(romanos)}.")
    if romanos != [romano(i) for i in range(1, len(romanos) + 1)]:
        registro.bloqueante(
            ETAPA, f"Lacuna na numeração dos anexos: {', '.join(romanos)}.")

    registro.informacao(
        ETAPA,
        "Ordem definida: " + " · ".join(a.rotulo for a in plano.anexos),
    )
    declaracao = plano.por_chave("declaracao")
    if declaracao is not None:
        registro.informacao(
            ETAPA,
            f"Declaração conjunta numerada como {declaracao.rotulo.split(' —')[0]} "
            + ("(há minuta de contrato)" if plano.por_chave("contrato")
               else "(não há minuta de contrato)") + ".",
        )
    return plano


# --------------------------------------------------------------------------- #
# Relação de anexos no corpo do aviso
# --------------------------------------------------------------------------- #

def _reescrever(paragrafo, novo_texto: str) -> None:
    """
    Reescreve o texto do parágrafo preservando a formatação do primeiro run.

    Todo o texto vai para o primeiro w:t e os demais ficam vazios: o parágrafo é
    um rótulo curto e homogêneo, e essa é a forma de trocá-lo sem criar run novo
    com fonte diferente.
    """
    elementos = elementos_texto(paragrafo)
    if not elementos:
        return
    definir_texto(elementos[0], novo_texto)
    for elemento in elementos[1:]:
        definir_texto(elemento, "")


def localizar_relacao(paragrafos: list) -> list[int]:
    """
    Índices dos parágrafos que formam a relação de anexos do aviso.

    Só é considerada relação uma sequência de duas ou mais linhas 'ANEXO N — ...'.
    Uma menção isolada no meio do texto é referência, não relação.
    """
    indices = [
        indice for indice, paragrafo in enumerate(paragrafos)
        if RE_ITEM_RELACAO.match(texto_paragrafo(paragrafo).strip())
    ]
    if len(indices) < 2:
        return []
    blocos: list[list[int]] = []
    atual = [indices[0]]
    for anterior, indice in zip(indices, indices[1:]):
        if indice - anterior <= 3:      # tolera linhas em branco entre os itens
            atual.append(indice)
        else:
            blocos.append(atual)
            atual = [indice]
    blocos.append(atual)
    maior = max(blocos, key=len)
    return maior if len(maior) >= 2 else []


def atualizar_relacao(documento, plano: PlanoAnexos, registro: Registro) -> list[str]:
    """
    Sincroniza a relação de anexos do aviso com o plano.

    A minuta-mãe da Câmara não traz relação de anexos — ela cita apenas o Anexo I
    no item de habilitação. Nesse caso, inserir uma relação seria criar seção que
    a minuta não tem, o que a regra proíbe. Por isso a ausência vira pendência
    humana explícita, e não um bloco improvisado.
    """
    paragrafos = list(documento.paragraphs)
    indices = localizar_relacao(paragrafos)
    if not indices:
        registro.pendencia(
            ETAPA,
            "A minuta-mãe do aviso não traz relação de anexos ('ANEXO I — ...', "
            "'ANEXO II — ...'). Os anexos foram numerados e rotulados no "
            "documento montado, mas o corpo do aviso não os relaciona. Incluir "
            "essa relação exige revisão expressa da minuta-mãe.",
        )
        return []

    aplicadas: list[str] = []
    if len(indices) != len(plano.anexos):
        registro.bloqueante(
            ETAPA,
            f"A relação de anexos do aviso tem {len(indices)} entrada(s) e a "
            f"montagem produziu {len(plano.anexos)} anexo(s). Corrigir isso "
            "significaria acrescentar ou suprimir linha da minuta — decisão "
            "humana.",
        )
        return []

    for indice, anexo in zip(indices, plano.anexos):
        paragrafo = paragrafos[indice]
        atual = texto_paragrafo(paragrafo).strip()
        novo = f"{anexo.rotulo};"
        if atual.rstrip(";") == anexo.rotulo:
            continue
        _reescrever(paragrafo, novo)
        aplicadas.append(f"Relação de anexos: '{atual}' → '{novo}'")
    if aplicadas:
        registro.informacao(
            ETAPA, f"{len(aplicadas)} entrada(s) da relação de anexos atualizada(s).")
    return aplicadas


def verificar_referencias(paragrafos: Iterable, plano: PlanoAnexos,
                          registro: Registro, origem: str = "aviso") -> None:
    """Toda referência 'Anexo N' precisa apontar para um anexo que existe."""
    validos = plano.romanos
    vistos: dict[str, int] = {}
    for paragrafo in paragrafos:
        texto = texto_paragrafo(paragrafo)
        for achado in RE_REFERENCIA.finditer(texto):
            numeral = achado.group(1).upper()
            vistos[numeral] = vistos.get(numeral, 0) + 1
    for numeral, ocorrencias in sorted(vistos.items()):
        if numeral not in validos:
            registro.bloqueante(
                ETAPA,
                f"Referência a ANEXO {numeral} ({ocorrencias} ocorrência(s)) sem "
                f"anexo correspondente. Anexos deste aviso: "
                f"{', '.join(sorted(validos, key=_ROMANOS.index))}.",
                origem=origem,
            )
    if vistos:
        registro.informacao(
            ETAPA,
            "Referências internas conferidas: "
            + ", ".join(f"ANEXO {n} ({q}x)" for n, q in sorted(vistos.items())),
            origem=origem,
        )
