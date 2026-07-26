#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ocorrencias.py — vocabulário comum de achados do Aviso de Dispensa Completo.

Todo módulo da montagem reporta o que encontrou como `Ocorrencia`, sempre com
uma das quatro classificações do escopo (item 8):

    ERRO BLOQUEANTE  — impede a geração final; só sai como rascunho.
    ALERTA           — não impede, mas o documento não pode ser dado por pronto.
    PENDÊNCIA HUMANA — falta decisão ou dado que o Charles não pode inventar.
    INFORMAÇÃO       — registro de rastreabilidade.

A separação existe para que a decisão de bloquear seja de um lugar só
(`decidir_status`) e não fique espalhada por nove módulos.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Optional

BLOQUEANTE = "ERRO BLOQUEANTE"
ALERTA = "ALERTA"
PENDENCIA = "PENDÊNCIA HUMANA"
INFORMACAO = "INFORMAÇÃO"

SEVERIDADES = (BLOQUEANTE, ALERTA, PENDENCIA, INFORMACAO)
_ORDEM = {severidade: indice for indice, severidade in enumerate(SEVERIDADES)}

# Status finais possíveis (item 17 do escopo).
STATUS_PUBLICACAO = "APTO PARA PUBLICAÇÃO"
STATUS_CONFERENCIA = "APTO PARA CONFERÊNCIA"
STATUS_RESSALVAS = "APTO COM RESSALVAS"
STATUS_RASCUNHO = "RASCUNHO — NÃO PUBLICAR"
STATUS_BLOQUEADO = "BLOQUEADO"

AVISO_RASCUNHO = "DOCUMENTO DE TRABALHO — NÃO PUBLICAR"


@dataclass
class Ocorrencia:
    """Um achado da montagem, sempre atribuído a uma etapa e a uma origem."""

    severidade: str
    etapa: str
    mensagem: str
    origem: Optional[str] = None

    def __post_init__(self) -> None:
        if self.severidade not in _ORDEM:
            raise ValueError(f"Severidade desconhecida: {self.severidade}")

    def __str__(self) -> str:
        alvo = f" [{self.origem}]" if self.origem else ""
        return f"{self.severidade} — {self.etapa}{alvo}: {self.mensagem}"

    def como_dicionario(self) -> dict[str, Optional[str]]:
        return {
            "severidade": self.severidade,
            "etapa": self.etapa,
            "mensagem": self.mensagem,
            "origem": self.origem,
        }


@dataclass
class Registro:
    """Coletor de ocorrências compartilhado pelas etapas da montagem."""

    itens: list[Ocorrencia] = field(default_factory=list)

    def _adicionar(self, severidade: str, etapa: str, mensagem: str,
                   origem: Optional[str] = None) -> Ocorrencia:
        ocorrencia = Ocorrencia(severidade, etapa, mensagem, origem)
        self.itens.append(ocorrencia)
        return ocorrencia

    def bloqueante(self, etapa: str, mensagem: str, origem: Optional[str] = None):
        return self._adicionar(BLOQUEANTE, etapa, mensagem, origem)

    def alerta(self, etapa: str, mensagem: str, origem: Optional[str] = None):
        return self._adicionar(ALERTA, etapa, mensagem, origem)

    def pendencia(self, etapa: str, mensagem: str, origem: Optional[str] = None):
        return self._adicionar(PENDENCIA, etapa, mensagem, origem)

    def informacao(self, etapa: str, mensagem: str, origem: Optional[str] = None):
        return self._adicionar(INFORMACAO, etapa, mensagem, origem)

    def estender(self, outras: Iterable[Ocorrencia]) -> None:
        self.itens.extend(outras)

    def por_severidade(self, severidade: str) -> list[Ocorrencia]:
        return [item for item in self.itens if item.severidade == severidade]

    @property
    def bloqueantes(self) -> list[Ocorrencia]:
        return self.por_severidade(BLOQUEANTE)

    @property
    def pendencias(self) -> list[Ocorrencia]:
        return self.por_severidade(PENDENCIA)

    @property
    def alertas(self) -> list[Ocorrencia]:
        return self.por_severidade(ALERTA)

    def tem_bloqueio(self) -> bool:
        return bool(self.bloqueantes)

    def ordenadas(self) -> list[Ocorrencia]:
        return sorted(self.itens, key=lambda o: (_ORDEM[o.severidade], o.etapa))

    def como_lista(self) -> list[dict[str, Optional[str]]]:
        return [item.como_dicionario() for item in self.ordenadas()]

    def contagem(self) -> dict[str, int]:
        return {s: len(self.por_severidade(s)) for s in SEVERIDADES}


def decidir_status(registro: Registro, rascunho_solicitado: bool = False) -> str:
    """
    Converte o conjunto de ocorrências no status final do item 17 do escopo.

    Regra deliberada: `APTO PARA PUBLICAÇÃO` NUNCA é decidido aqui. A conferência
    humana final é sempre necessária, então o melhor status que a automação
    concede é `APTO PARA CONFERÊNCIA` — quem publica é pessoa, não script.
    """
    if registro.tem_bloqueio():
        return STATUS_RASCUNHO if rascunho_solicitado else STATUS_BLOQUEADO
    if rascunho_solicitado:
        return STATUS_RASCUNHO
    if registro.pendencias or registro.alertas:
        return STATUS_RESSALVAS
    return STATUS_CONFERENCIA
