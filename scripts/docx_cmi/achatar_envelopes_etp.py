#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
achatar_envelopes_etp.py — Remove a estrutura de tabela-envelope por seção do ETP.

Script de uso único (revisão de minuta-mãe / documento gerado), não parte do
pipeline de padronização recorrente. Transforma cada tabela-envelope de 1
coluna (uma por seção, hoje usada para aplicar cantSplit) em parágrafos soltos
no corpo do documento — o primeiro parágrafo de cada célula (o título, em
negrito) recebe o estilo "CMI Titulo 1"; os demais recebem "CMI Corpo".
Tabelas aninhadas dentro da célula (quadros de dados de verdade: alternativas,
resultados, etapas, cesta de preços) são preservadas e promovidas para o nível
raiz do documento, na mesma posição.

Também remove todo sombreamento cinza (w:shd) que sobrar — do envelope (fundo
das seções) e dos cabeçalhos dos quadros de dados promovidos — e corrige a
largura declarada (tblW) dos quadros de dados promovidos para "dxa" batendo
com a soma do tblGrid. Sem isso, o Word ignora o tblGrid e colapsa as colunas
ao mínimo (o defeito que motivou este script).

Nada aqui reduz linha, coluna, mesclagem ou texto. Roda sobre uma CÓPIA;
quem chama decide onde salvar.
"""
from __future__ import annotations

import sys
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn


def _extrair_texto(elemento) -> str:
    return "".join(t.text or "" for t in elemento.findall(".//" + qn("w:t")))


def _remover_shd(elemento) -> int:
    """Remove todo <w:shd> dentro do elemento (cinza de célula ou de parágrafo)."""
    removidos = 0
    for shd in elemento.findall(".//" + qn("w:shd")):
        pai = shd.getparent()
        pai.remove(shd)
        removidos += 1
    return removidos


def _corrigir_tblw(tabela_xml) -> bool:
    """Garante tblW type=dxa batendo com a soma do tblGrid. Devolve se mudou algo."""
    grid = tabela_xml.find(qn("w:tblGrid"))
    if grid is None:
        return False
    total = 0
    for col in grid.findall(qn("w:gridCol")):
        valor = col.get(qn("w:w"))
        if valor:
            try:
                total += int(valor)
            except ValueError:
                pass
    if not total:
        return False
    tblPr = tabela_xml.find(qn("w:tblPr"))
    if tblPr is None:
        return False
    tblW = tblPr.find(qn("w:tblW"))
    mudou = False
    if tblW is None:
        tblW = tblPr.makeelement(qn("w:tblW"), {})
        tblPr.append(tblW)
        mudou = True
    if tblW.get(qn("w:type")) != "dxa" or tblW.get(qn("w:w")) != str(total):
        tblW.set(qn("w:type"), "dxa")
        tblW.set(qn("w:w"), str(total))
        mudou = True
    layout = tblPr.find(qn("w:tblLayout"))
    if layout is None:
        layout = tblPr.makeelement(qn("w:tblLayout"), {})
        tblPr.append(layout)
        mudou = True
    if layout.get(qn("w:type")) != "fixed":
        layout.set(qn("w:type"), "fixed")
        mudou = True
    return mudou


def _titulo_de_secao(primeiro_paragrafo) -> bool:
    """Heurística: parágrafo de título tem algum run em negrito com texto."""
    for run in primeiro_paragrafo.findall(".//" + qn("w:r")):
        rpr = run.find(qn("w:rPr"))
        texto = "".join(t.text or "" for t in run.findall(qn("w:t")))
        if texto.strip() and rpr is not None and rpr.find(qn("w:b")) is not None:
            return True
    return False


def _definir_estilo(paragrafo_xml, estilo_id: str) -> None:
    pPr = paragrafo_xml.find(qn("w:pPr"))
    if pPr is None:
        pPr = paragrafo_xml.makeelement(qn("w:pPr"), {})
        paragrafo_xml.insert(0, pPr)
    pStyle = pPr.find(qn("w:pStyle"))
    if pStyle is None:
        pStyle = pPr.makeelement(qn("w:pStyle"), {})
        pPr.insert(0, pStyle)
    pStyle.set(qn("w:val"), estilo_id)


def achatar(doc: Document) -> dict[str, int]:
    """Achata toda tabela-envelope de 1 coluna no corpo do documento."""
    corpo = doc.element.body
    relatorio = {
        "tabelas_achatadas": 0,
        "tabelas_promovidas": 0,
        "shd_removidos": 0,
        "tblw_corrigidos": 0,
        "paragrafos_titulo": 0,
        "paragrafos_corpo": 0,
    }

    tabelas = [c for c in list(corpo) if c.tag == qn("w:tbl")]
    for tabela in tabelas:
        grid = tabela.find(qn("w:tblGrid"))
        n_colunas = len(grid.findall(qn("w:gridCol"))) if grid is not None else 0
        if n_colunas != 1:
            # Não é envelope de seção (não deveria ocorrer no ETP); preserva.
            relatorio["shd_removidos"] += _remover_shd(tabela)
            if _corrigir_tblw(tabela):
                relatorio["tblw_corrigidos"] += 1
            continue

        novos_elementos = []
        primeiro_p_visto = False
        for tr in tabela.findall(qn("w:tr")):
            for tc in tr.findall(qn("w:tc")):
                for filho in list(tc):
                    tag = filho.tag
                    if tag == qn("w:p"):
                        if not primeiro_p_visto and _titulo_de_secao(filho):
                            _definir_estilo(filho, "CMITitulo1")
                            relatorio["paragrafos_titulo"] += 1
                        elif _extrair_texto(filho).strip():
                            _definir_estilo(filho, "CMICorpo")
                            relatorio["paragrafos_corpo"] += 1
                        primeiro_p_visto = True
                        novos_elementos.append(filho)
                    elif tag == qn("w:tbl"):
                        relatorio["shd_removidos"] += _remover_shd(filho)
                        if _corrigir_tblw(filho):
                            relatorio["tblw_corrigidos"] += 1
                        relatorio["tabelas_promovidas"] += 1
                        novos_elementos.append(filho)

        pai = tabela.getparent()
        indice = list(pai).index(tabela)
        for offset, elemento in enumerate(novos_elementos):
            pai.insert(indice + offset, elemento)
        pai.remove(tabela)
        relatorio["tabelas_achatadas"] += 1

    # Sombreamento residual em qualquer outro ponto do corpo (ex.: parágrafos
    # soltos com w:shd de fundo, se algum sobrar fora de tabela).
    relatorio["shd_removidos"] += _remover_shd(corpo)

    return relatorio


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if len(argv) != 2:
        print("uso: achatar_envelopes_etp.py <entrada.docx> <saida.docx>")
        return 2
    entrada, saida = Path(argv[0]), Path(argv[1])
    doc = Document(str(entrada))
    relatorio = achatar(doc)
    saida.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(saida))
    for chave, valor in relatorio.items():
        print(f"{chave}: {valor}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
