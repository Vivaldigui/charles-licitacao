#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validar_respostas.py — Runner do gabarito de perguntas do Charles.

Lê `99_testes/casos_validacao.yaml` com parser simples (sem PyYAML) e valida
respostas por arquivo/stdin ou por comando headless.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional


def _limpar(valor: str) -> str:
    texto = valor.strip()
    if texto.startswith('"') and texto.endswith('"'):
        return texto[1:-1].replace('\\"', '"')
    if texto.startswith("'") and texto.endswith("'"):
        return texto[1:-1]
    return texto


def carregar_casos(caminho: Path) -> list[dict[str, Any]]:
    """Parser YAML mínimo para a estrutura de casos_validacao.yaml."""
    casos: list[dict[str, Any]] = []
    atual: dict[str, Any] | None = None
    lista_atual: str | None = None
    for bruto in caminho.read_text(encoding="utf-8").splitlines():
        linha = bruto.rstrip()
        if not linha.strip() or linha.lstrip().startswith("#"):
            continue
        if linha.startswith("- "):
            resto = linha[2:]
            if ":" in resto:
                if atual:
                    casos.append(atual)
                chave, valor = resto.split(":", 1)
                atual = {chave.strip(): _limpar(valor)}
                lista_atual = None
            elif atual is not None and lista_atual:
                atual.setdefault(lista_atual, []).append(_limpar(resto))
            continue
        if atual is None:
            continue
        if re.match(r"^\s+-\s+", linha) and lista_atual:
            atual.setdefault(lista_atual, []).append(_limpar(re.sub(r"^\s+-\s+", "", linha)))
            continue
        if ":" in linha:
            chave, valor = linha.split(":", 1)
            chave = chave.strip()
            valor = valor.strip()
            if valor == "[]":
                atual[chave] = []
                lista_atual = None
            elif valor == "":
                atual[chave] = []
                lista_atual = chave
            else:
                atual[chave] = _limpar(valor)
                lista_atual = None
    if atual:
        casos.append(atual)
    return casos


def avaliar_resposta(caso: dict[str, Any], resposta: str) -> list[str]:
    """Retorna falhas encontradas na resposta."""
    falhas: list[str] = []
    for trecho in caso.get("deve_conter", []) or []:
        if trecho not in resposta:
            falhas.append(f"não contém trecho obrigatório: {trecho}")
    for trecho in caso.get("nao_pode_conter", []) or []:
        if trecho and trecho in resposta:
            falhas.append(f"contém trecho proibido: {trecho}")
    for padrao in caso.get("nao_pode_conter_regex", []) or []:
        if padrao and re.search(padrao, resposta, flags=re.IGNORECASE):
            falhas.append(f"contém regex proibida: {padrao}")
    for fonte in caso.get("fontes_esperadas", []) or []:
        if fonte and fonte not in resposta:
            falhas.append(f"não cita fonte esperada: {fonte}")
    return falhas


def _resposta_por_arquivo(pasta: Path, caso: dict[str, Any]) -> str:
    caminho = pasta / f"{caso['id']}.txt"
    if not caminho.exists():
        return ""
    return caminho.read_text(encoding="utf-8")


def _executar_headless(modelo: str, pergunta: str) -> str:
    comando = modelo.replace("{pergunta}", pergunta)
    proc = subprocess.run(
        comando,
        shell=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return (proc.stdout or "") + (proc.stderr or "")


def construir_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Valida respostas do Charles contra gabarito YAML.")
    ap.add_argument("--casos", default="99_testes/casos_validacao.yaml", help="Arquivo YAML de casos.")
    ap.add_argument("--respostas-dir", help="Pasta com arquivos <id>.txt.")
    ap.add_argument("--resposta-arquivo", help="Arquivo único de resposta; usado para todos os casos.")
    ap.add_argument("--headless", help='Comando por caso, usando "{pergunta}" como placeholder.')
    return ap


def main(argv: Optional[list[str]] = None) -> int:
    args = construir_parser().parse_args(argv)
    casos = carregar_casos(Path(args.casos))
    resultados: list[tuple[str, list[str]]] = []

    resposta_unica = None
    if args.resposta_arquivo:
        resposta_unica = Path(args.resposta_arquivo).read_text(encoding="utf-8")

    for caso in casos:
        pergunta = str(caso.get("pergunta", ""))
        if args.headless:
            resposta = _executar_headless(args.headless, pergunta)
        elif args.respostas_dir:
            resposta = _resposta_por_arquivo(Path(args.respostas_dir), caso)
        elif resposta_unica is not None:
            resposta = resposta_unica
        else:
            print(f"\n## {caso.get('id')} — {pergunta}")
            print("Cole a resposta e finalize com Ctrl+Z/Enter (Windows) ou Ctrl+D:")
            resposta = sys.stdin.read()
        falhas = avaliar_resposta(caso, resposta)
        resultados.append((str(caso.get("id")), falhas))

    aprovados = 0
    print("# Relatório de validação de respostas")
    for caso_id, falhas in resultados:
        if falhas:
            print(f"- {caso_id}: REPROVADO")
            for falha in falhas:
                print(f"  - {falha}")
        else:
            aprovados += 1
            print(f"- {caso_id}: APROVADO")
    print(f"\nResumo: {aprovados}/{len(resultados)} caso(s) aprovados.")
    return 0 if aprovados == len(resultados) else 1


if __name__ == "__main__":
    raise SystemExit(main())

