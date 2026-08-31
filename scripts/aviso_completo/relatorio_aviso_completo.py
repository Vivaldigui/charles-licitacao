#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
relatorio_aviso_completo.py — relatório de montagem e validação.

O relatório é a prova do que a automação fez e do que ela NÃO fez. Por isso ele
sempre fecha com a ressalva de conferência humana, mesmo quando nada falhou:
nenhuma validação automática substitui a leitura do agente de contratação antes
da publicação.

Saída em Markdown (leitura) e JSON (rastreabilidade e testes), nos moldes do
relatório do Módulo de Padronização Documental.
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path
from typing import Any, Optional

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from ocorrencias import ALERTA, BLOQUEANTE, PENDENCIA, STATUS_PUBLICACAO

SECOES = [
    ("identificacao", "Identificação do processo"),
    ("componentes", "Componentes localizados"),
    ("minutas", "Minutas oficiais utilizadas"),
    ("termo_referencia", "Termo de Referência utilizado"),
    ("instrumento", "Instrumento contratual definido"),
    ("anexos", "Ordem dos anexos"),
    ("dados_tr", "Dados extraídos do TR"),
    ("habilitacao", "Validação da habilitação"),
    ("proposta", "Validação do modelo de proposta"),
    ("contrato", "Validação da minuta de contrato"),
    ("declaracao", "Validação da declaração conjunta"),
    ("divergencias", "Divergências encontradas"),
    ("campos_pendentes", "Campos pendentes"),
    ("correcoes", "Correções realizadas"),
    ("validacao_conteudo", "Validação de conteúdo"),
    ("validacao_formatacao", "Validação de formatação"),
    ("arquivos", "Arquivos produzidos"),
]

RESSALVA = (
    "> Conferência humana final obrigatória. A validação automática confere "
    "correspondência entre as peças, campos pendentes, numeração e preservação "
    "de conteúdo — não confere o mérito administrativo nem substitui a leitura "
    "do agente de contratação e, quando exigida, a manifestação da assessoria "
    "jurídica."
)


def _lista(itens: Any, vazio: str = "Nenhum.") -> str:
    if not itens:
        return vazio
    if isinstance(itens, dict):
        return "\n".join(f"- **{chave}:** {valor}" for chave, valor in itens.items()
                         if valor not in (None, "", []))
    if isinstance(itens, str):
        return itens
    return "\n".join(f"- {item}" for item in itens)


def _tabela_anexos(anexos: list[dict[str, str]]) -> str:
    if not anexos:
        return "Nenhum anexo montado."
    linhas = ["| Ordem | Anexo | Componente | Arquivo |",
              "| --- | --- | --- | --- |"]
    for anexo in anexos:
        linhas.append(
            f"| {anexo['ordem']} | {anexo['rotulo']} | {anexo['componente']} "
            f"| {anexo['arquivo']} |")
    return "\n".join(linhas)


def _tabela_itens(itens: list[dict[str, str]]) -> str:
    if not itens:
        return "Nenhum item extraído."
    linhas = ["| Item | Descrição | Und. | Qtd. |", "| --- | --- | --- | --- |"]
    for item in itens:
        descricao = item.get("descricao", "")
        if len(descricao) > 90:
            descricao = descricao[:87] + "..."
        linhas.append(
            f"| {item.get('item','')} | {descricao} | {item.get('unidade','')} "
            f"| {item.get('quantidade','')} |")
    return "\n".join(linhas)


def _ocorrencias(ocorrencias: list[dict[str, Any]], severidade: str) -> str:
    filtradas = [o for o in ocorrencias if o["severidade"] == severidade]
    if not filtradas:
        return "Nenhuma."
    linhas = []
    for ocorrencia in filtradas:
        origem = f" ({ocorrencia['origem']})" if ocorrencia.get("origem") else ""
        linhas.append(f"- **{ocorrencia['etapa']}**{origem}: {ocorrencia['mensagem']}")
    return "\n".join(linhas)


def render_markdown(dados: dict[str, Any]) -> str:
    """Monta o relatório em Markdown na ordem fixa do item 17 do escopo."""
    ocorrencias = dados.get("ocorrencias", [])
    partes = [
        "# Relatório — Aviso de Dispensa Completo",
        "",
        f"- **Gerado em:** {dados.get('gerado_em', date.today().isoformat())}",
        f"- **Modo:** {dados.get('modo', 'montagem')}",
        f"- **Status:** {dados.get('status', 'não informado')}",
        "",
    ]

    conteudo = {
        "identificacao": _lista(dados.get("identificacao")),
        "componentes": _lista(dados.get("componentes")),
        "minutas": _lista(dados.get("minutas"), "Nenhuma minuta oficial utilizada."),
        "termo_referencia": _lista(dados.get("termo_referencia"),
                                   "Termo de Referência não localizado."),
        "instrumento": _lista(dados.get("instrumento")),
        "anexos": _tabela_anexos(dados.get("anexos", [])),
        "dados_tr": _tabela_itens(dados.get("itens_tr", [])),
        "habilitacao": _lista(dados.get("habilitacao")),
        "proposta": _lista(dados.get("proposta")),
        "contrato": _lista(dados.get("contrato"),
                           "Não há minuta de contrato neste aviso."),
        "declaracao": _lista(dados.get("declaracao")),
        "divergencias": (
            "### Erros bloqueantes\n" + _ocorrencias(ocorrencias, BLOQUEANTE)
            + "\n\n### Alertas\n" + _ocorrencias(ocorrencias, ALERTA)
            + "\n\n### Pendências humanas\n" + _ocorrencias(ocorrencias, PENDENCIA)
        ),
        "campos_pendentes": _lista(dados.get("campos_pendentes"),
                                   "Nenhum campo pendente detectado."),
        "correcoes": _lista(dados.get("correcoes"),
                            "Nenhuma correção automática aplicada."),
        "validacao_conteudo": _lista(dados.get("validacao_conteudo")),
        "validacao_formatacao": _lista(dados.get("validacao_formatacao")),
        "arquivos": _lista(dados.get("arquivos"), "Nenhum arquivo produzido."),
    }

    for chave, titulo in SECOES:
        partes += [f"## {titulo}", "", conteudo.get(chave, "Nenhum."), ""]

    partes += [
        "## Resultado",
        "",
        f"**{dados.get('status', 'não informado')}**",
        "",
        _lista(dados.get("resumo_resultado")),
        "",
        RESSALVA,
        "",
        "## Registro completo de ocorrências",
        "",
        _lista([f"[{o['severidade']}] {o['etapa']}: {o['mensagem']}"
                for o in ocorrencias], "Nenhuma ocorrência registrada."),
        "",
    ]
    return "\n".join(partes)


def gravar(dados: dict[str, Any], destino_md: Path) -> tuple[Path, Path]:
    """Grava o relatório em `.md` e `.json` e devolve os dois caminhos."""
    destino_md = Path(destino_md)
    destino_md.parent.mkdir(parents=True, exist_ok=True)
    destino_md.write_text(render_markdown(dados), encoding="utf-8")

    destino_json = destino_md.with_suffix(".json")
    destino_json.write_text(
        json.dumps(dados, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8")
    return destino_md, destino_json


def status_permitido(status: str) -> str:
    """
    Barreira final contra o status que a automação não pode conceder.

    `APTO PARA PUBLICAÇÃO` depende de conferência humana; se algum caminho tentar
    emiti-lo, ele é rebaixado aqui.
    """
    if status == STATUS_PUBLICACAO:
        return "APTO PARA CONFERÊNCIA"
    return status
