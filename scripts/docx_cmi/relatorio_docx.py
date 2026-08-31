#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
relatorio_docx.py — Relatório de padronização documental (Markdown + JSON).

A estrutura das seções é fixa e segue o item 23 do escopo do módulo, para que
o relatório possa ser anexado ao processo administrativo sempre no mesmo
formato.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SECOES = [
    "Documento analisado",
    "Minuta-mãe utilizada",
    "Perfil documental aplicado",
    "Data da execução",
    "Diagnóstico inicial",
    "Fontes encontradas",
    "Tamanhos encontrados",
    "Cores encontradas",
    "Estilos encontrados",
    "Problemas de numeração",
    "Problemas de tabelas",
    "Problemas de paginação",
    "Campos pendentes",
    "Correções automáticas aplicadas",
    "Correções não aplicadas",
    "Alterações que exigem validação humana",
    "Validação de preservação do conteúdo",
    "Resultado dos testes",
    "Arquivo final",
    "Status",
]


def _lista(itens, vazio: str = "Nenhum.") -> str:
    itens = [i for i in (itens or []) if i]
    if not itens:
        return vazio
    return "\n".join(f"- {i}" for i in itens)


def _contagem(mapa: dict[Any, Any], vazio: str = "Nenhuma.") -> str:
    if not mapa:
        return vazio
    linhas = sorted(mapa.items(), key=lambda kv: (-kv[1], str(kv[0])))
    return "\n".join(f"- `{chave}` — {valor} ocorrência(s)" for chave, valor in linhas)


def render_markdown(dados: dict[str, Any]) -> str:
    """Monta o relatório em Markdown a partir do diagnóstico estruturado."""
    inventario = dados.get("inventario", {})
    numeracao = dados.get("numeracao", {})
    tabelas = dados.get("tabelas", {})
    pendencias = dados.get("pendencias", {})
    revisao = dados.get("revisao", {})
    validacao = dados.get("validacao_conteudo")
    testes = dados.get("testes")
    cabecalho = dados.get("cabecalho_rodape", {})

    partes: list[str] = ["# Relatório de Padronização Documental", ""]

    def secao(titulo: str, corpo: str) -> None:
        partes.append(f"## {titulo}")
        partes.append("")
        partes.append(corpo.rstrip())
        partes.append("")

    secao("Documento analisado", f"`{dados.get('documento', '(não informado)')}`")
    secao("Minuta-mãe utilizada",
          f"`{dados['minuta_mae']}`" if dados.get("minuta_mae")
          else "Não informada. A comparação de timbre com a minuta-mãe **não foi executada**.")
    secao("Perfil documental aplicado",
          f"`{dados.get('perfil')}` — {dados.get('perfil_nome', '')}".strip(" —"))
    secao("Data da execução", dados.get("data", ""))

    diagnostico_inicial = [
        f"Modo: **{dados.get('modo', 'auditoria')}**",
        f"Parágrafos com formatação direta: "
        f"{inventario.get('runs_com_formatacao_direta', 0)} de "
        f"{inventario.get('runs_totais', 0)} runs "
        f"({int(100 * inventario.get('proporcao_formatacao_direta', 0))}%)",
        f"Estilo Normal do documento: "
        f"{inventario.get('fonte_do_estilo_normal')} "
        f"{inventario.get('tamanho_do_estilo_normal')} pt",
        f"Seções do documento: {cabecalho.get('secoes', '?')}",
        f"Imagens no cabeçalho: {cabecalho.get('imagens_cabecalho', '?')} | "
        f"no rodapé: {cabecalho.get('imagens_rodape', '?')}",
        f"Campo de paginação no rodapé: "
        f"{'sim' if cabecalho.get('campo_pagina_no_rodape') else 'não'}",
        f"Tabelas: {tabelas.get('total', 0)}",
        f"Comentários internos: {'SIM' if revisao.get('comentarios') else 'não'} | "
        f"Controle de alterações: {revisao.get('controle_alteracoes', 0)} marca(s) | "
        f"Texto oculto: {revisao.get('texto_oculto', 0)}",
    ]
    secao("Diagnóstico inicial", _lista(diagnostico_inicial))

    fora = dados.get("fontes_fora_do_padrao") or []
    corpo_fontes = _contagem(inventario.get("fontes", {}))
    if fora:
        corpo_fontes += "\n\n**Fora do padrão institucional:** " + ", ".join(fora)
    secao("Fontes encontradas", corpo_fontes)
    secao("Tamanhos encontrados", _contagem(inventario.get("tamanhos", {})))
    secao("Cores encontradas",
          _contagem(inventario.get("cores", {}),
                    "Nenhuma cor explícita — todo o texto herda a cor do estilo."))
    secao("Estilos encontrados", _contagem(inventario.get("estilos", {})))

    linhas_num = [
        f"{p['tipo']} (parágrafo {p['paragrafo']}, rótulo '{p['rotulo']}'): {p['detalhe']}"
        + (f" — sugestão: {p['sugestao']}" if p.get("sugestao") else "")
        + ("  [corrigível automaticamente]" if p.get("corrigivel")
           else "  [EXIGE DECISÃO HUMANA]")
        for p in numeracao.get("problemas", [])
    ]
    if numeracao.get("fragmentacao"):
        linhas_num.append(f"Fragmentação: {numeracao['fragmentacao']}")
    if numeracao.get("referencias_afetadas"):
        linhas_num.append(
            "Referências internas afetadas: "
            + "; ".join(numeracao["referencias_afetadas"])
        )
    rodape_num = (
        f"\n\nItens numerados manualmente: {numeracao.get('itens', 0)} | "
        f"Referências internas detectadas: {numeracao.get('referencias_internas', 0)}"
    )
    secao("Problemas de numeração", _lista(linhas_num) + rodape_num)

    secao("Problemas de tabelas", _lista(tabelas.get("problemas")))
    secao("Problemas de paginação",
          _lista((dados.get("paginacao", {}).get("problemas") or [])
                 + (dados.get("estrutura", {}).get("problemas") or [])
                 + (dados.get("pagina", {}).get("problemas") or [])))

    linhas_pend = list(pendencias.get("campos_pendentes") or [])
    if pendencias.get("blocos_ou"):
        linhas_pend.append(
            "Blocos alternativos 'OU' não resolvidos nos parágrafos: "
            + ", ".join(str(i) for i in pendencias["blocos_ou"])
        )
    if pendencias.get("opcoes_nao_marcadas"):
        linhas_pend.append(
            "Opções '( )' não marcadas nos parágrafos: "
            + ", ".join(str(i) for i in pendencias["opcoes_nao_marcadas"])
        )
    linhas_pend += list(pendencias.get("texto_destacado") or [])
    secao("Campos pendentes",
          _lista(linhas_pend, "Nenhum marcador pendente localizado."))

    secao("Correções automáticas aplicadas",
          _lista(dados.get("correcoes_aplicadas"),
                 "Nenhuma — execução em modo auditoria (documento não alterado)."))
    secao("Correções não aplicadas",
          _lista(dados.get("correcoes_nao_aplicadas")
                 or dados.get("correcoes_automaticas_possiveis"),
                 "Nenhuma."))
    secao("Alterações que exigem validação humana",
          _lista(dados.get("correcoes_que_exigem_humano")))

    if validacao is None:
        corpo_validacao = (
            "Não aplicável — nenhuma alteração foi gravada nesta execução."
        )
    else:
        corpo_validacao = _lista([
            f"Hash do conteúdo antes:  `{validacao.get('hash_antes')}`",
            f"Hash do conteúdo depois: `{validacao.get('hash_depois')}`",
            f"Parágrafos: {validacao.get('paragrafos_antes')} -> "
            f"{validacao.get('paragrafos_depois')}",
            f"Células de tabela: {validacao.get('celulas_antes')} -> "
            f"{validacao.get('celulas_depois')}",
            f"Conteúdo preservado: "
            f"{'SIM' if validacao.get('conteudo_preservado') else 'NÃO'}",
            f"Partes protegidas (cabeçalho/rodapé/mídia) intactas: "
            f"{'SIM' if validacao.get('partes_protegidas_intactas') else 'NÃO'}",
        ])
        diferencas = validacao.get("diferencas") or []
        if diferencas:
            corpo_validacao += "\n\n**Diferenças classificadas:**\n" + "\n".join(
                f"- [{'autorizada' if d['autorizada'] else 'NÃO AUTORIZADA'}] "
                f"{d['tipo']}: {d['motivo']}"
                for d in diferencas
            )
    secao("Validação de preservação do conteúdo", corpo_validacao)

    if testes is None:
        corpo_testes = (
            "Não executados nesta rodada. Os testes do módulo ficam em "
            "`99_testes/padronizacao_documental/`."
        )
    else:
        linhas = [
            f"Idempotência: {testes.get('idempotencia', 'não verificada')}",
            f"Validação visual (PDF): {testes.get('validacao_visual', 'não executada')}",
        ]
        visual = dados.get("validacao_visual") or {}
        if visual.get("executada"):
            linhas.append(f"Conversor usado: {visual.get('conversor')}")
            if visual.get("pdf_depois"):
                linhas.append(f"PDF conferível: `{visual['pdf_depois']}`")
        corpo_testes = _lista(linhas)
    secao("Resultado dos testes", corpo_testes)

    secao("Arquivo final",
          f"`{dados['arquivo_final']}`" if dados.get("arquivo_final")
          else "Nenhum arquivo gravado — modo auditoria.")
    secao("Status",
          f"**{dados.get('status', 'EXIGE CONFERÊNCIA HUMANA')}**\n\n"
          f"Nota de padronização: **{dados.get('nota_padronizacao', '?')}/100**")

    return "\n".join(partes).rstrip() + "\n"


def gravar(dados: dict[str, Any], destino_md: Path) -> tuple[Path, Path]:
    """Grava o relatório em Markdown e o JSON irmão."""
    destino_md = Path(destino_md)
    destino_md.parent.mkdir(parents=True, exist_ok=True)
    destino_md.write_text(render_markdown(dados), encoding="utf-8")
    destino_json = destino_md.with_suffix(".json")
    destino_json.write_text(
        json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return destino_md, destino_json
