#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tabelas_docx.py — Auditoria e padronização de tabelas.

Nenhuma função remove célula, linha, coluna ou mesclagem. As larguras são
reescaladas proporcionalmente, de modo que a tabela caiba na área útil sem
alterar a proporção entre colunas nem o conteúdo.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from util_ooxml import (
    celulas_mescladas,
    definir_alinhamento_vertical,
    definir_margens_internas_tabela,
    definir_nao_dividir_linha,
    definir_repetir_cabecalho,
    iter_paragrafos_tabela,
    qn,
    sombrear_celula,
    texto_paragrafo,
)

TWIPS_POR_EMU = 1 / 635.0  # 1 twip = 635 EMU


@dataclass
class DiagnosticoTabela:
    indice: int
    linhas: int
    colunas: int
    largura_twips: Optional[int]
    largura_util_twips: int
    excede_margens: bool
    cabecalho_repetido: bool
    linhas_divisiveis: int
    celulas_mescladas: int
    fontes: set[str] = field(default_factory=set)
    tamanhos: set[float] = field(default_factory=set)
    problemas: list[str] = field(default_factory=list)


def largura_util_twips(secao) -> int:
    """Largura da mancha gráfica (página menos margens), em twips."""
    # Length é subclasse de int em EMU; a subtração devolve int puro.
    largura_emu = int(secao.page_width) - int(secao.left_margin) - int(secao.right_margin)
    return int(round(largura_emu * TWIPS_POR_EMU))


def _largura_grid_twips(tabela) -> Optional[int]:
    grid = tabela._tbl.find(qn("w:tblGrid"))
    if grid is None:
        return None
    total = 0
    achou = False
    for coluna in grid.findall(qn("w:gridCol")):
        valor = coluna.get(qn("w:w"))
        if valor is None:
            continue
        try:
            total += int(valor)
            achou = True
        except ValueError:
            continue
    return total if achou else None


def _largura_declarada_twips(tabela) -> Optional[int]:
    tblW = tabela._tbl.tblPr.find(qn("w:tblW"))
    if tblW is None:
        return None
    if tblW.get(qn("w:type")) != "dxa":
        return None
    valor = tblW.get(qn("w:w"))
    try:
        return int(valor) if valor is not None else None
    except ValueError:
        return None


def diagnosticar(documento, padrao) -> list[DiagnosticoTabela]:
    """Levanta problemas de todas as tabelas do documento, sem alterá-las."""
    from util_ooxml import iter_tabelas

    secao = documento.sections[0]
    util = largura_util_twips(secao)
    diagnosticos: list[DiagnosticoTabela] = []

    for indice, tabela in enumerate(iter_tabelas(documento)):
        largura = _largura_grid_twips(tabela) or _largura_declarada_twips(tabela)
        excede = largura is not None and largura > util + 20  # tolerância ~0,35 mm

        divisiveis = 0
        for linha in tabela.rows:
            trPr = linha._tr.find(qn("w:trPr"))
            if trPr is None or trPr.find(qn("w:cantSplit")) is None:
                divisiveis += 1

        primeira = tabela.rows[0] if tabela.rows else None
        trPr = primeira._tr.find(qn("w:trPr")) if primeira is not None else None
        repetido = trPr is not None and trPr.find(qn("w:tblHeader")) is not None

        fontes: set[str] = set()
        tamanhos: set[float] = set()
        for paragrafo in iter_paragrafos_tabela(tabela):
            for run in paragrafo.runs:
                if not (run.text or ""):
                    continue
                if run.font.name:
                    fontes.add(run.font.name)
                if run.font.size:
                    tamanhos.add(round(run.font.size.pt, 1))

        diag = DiagnosticoTabela(
            indice=indice,
            linhas=len(tabela.rows),
            colunas=len(tabela.columns),
            largura_twips=largura,
            largura_util_twips=util,
            excede_margens=excede,
            cabecalho_repetido=repetido,
            linhas_divisiveis=divisiveis,
            celulas_mescladas=celulas_mescladas(tabela),
            fontes=fontes,
            tamanhos=tamanhos,
        )
        if excede:
            diag.problemas.append(
                f"Tabela {indice}: largura {largura} twips excede a área útil "
                f"({util} twips) — ultrapassa a margem."
            )
        if len(tabela.rows) > 1 and not repetido:
            diag.problemas.append(
                f"Tabela {indice}: linha de cabeçalho não se repete nas páginas seguintes."
            )
        if divisiveis:
            diag.problemas.append(
                f"Tabela {indice}: {divisiveis} linha(s) podem se dividir entre páginas."
            )
        if len(fontes) > 1:
            diag.problemas.append(
                f"Tabela {indice}: fontes diferentes entre células ({', '.join(sorted(fontes))})."
            )
        if len(tamanhos) > 1:
            diag.problemas.append(
                f"Tabela {indice}: tamanhos de fonte diferentes entre células "
                f"({', '.join(str(t) for t in sorted(tamanhos))})."
            )
        diagnosticos.append(diag)
    return diagnosticos


def _reescalar(tabela, util: int) -> list[str]:
    """
    Reduz proporcionalmente as larguras para caber na área útil e garante que
    `tblW` (largura declarada da tabela) seja `type="dxa"` batendo com a soma
    do `tblGrid`.

    A segunda parte roda mesmo quando a tabela já cabe na área útil (`fator`
    fica em 1, colunas não mudam de valor). Existe porque tabelas geradas via
    `python-docx` costumam sair com `tblW type="auto" w="0"` mesmo depois de
    receber larguras de coluna explícitas — o Word, ao contrário do
    LibreOffice, trata essa combinação como "sem largura declarada" e
    colapsa as colunas ao conteúdo mínimo (uma letra por linha). Deixar
    `tblW` sempre explícito evita esse colapso.
    """
    mudancas: list[str] = []
    grid = tabela._tbl.find(qn("w:tblGrid"))
    total = _largura_grid_twips(tabela)
    if grid is None or not total:
        return mudancas

    fator = min(util / total, 1.0)
    colunas = grid.findall(qn("w:gridCol"))
    novos: list[int] = []
    for coluna in colunas:
        atual = int(coluna.get(qn("w:w")) or 0)
        novo = max(int(atual * fator), 200)  # nunca abaixo de ~0,35 cm
        coluna.set(qn("w:w"), str(novo))
        novos.append(novo)

    # Ajusta a largura declarada de cada célula, preservando gridSpan.
    for linha in tabela.rows:
        indice_coluna = 0
        for tc in linha._tr.findall(qn("w:tc")):
            tcPr = tc.find(qn("w:tcPr"))
            span = 1
            if tcPr is not None:
                gridSpan = tcPr.find(qn("w:gridSpan"))
                if gridSpan is not None:
                    try:
                        span = int(gridSpan.get(qn("w:val")) or 1)
                    except ValueError:
                        span = 1
            largura = sum(novos[indice_coluna:indice_coluna + span]) or 200
            if tcPr is None:
                tcPr = tc.makeelement(qn("w:tcPr"), {})
                tc.insert(0, tcPr)
            tcW = tcPr.find(qn("w:tcW"))
            if tcW is None:
                tcW = tcPr.makeelement(qn("w:tcW"), {})
                tcPr.append(tcW)
            tcW.set(qn("w:w"), str(largura))
            tcW.set(qn("w:type"), "dxa")
            indice_coluna += span

    tblW = tabela._tbl.tblPr.find(qn("w:tblW"))
    if tblW is None:
        tblW = tabela._tbl.tblPr.makeelement(qn("w:tblW"), {})
        tabela._tbl.tblPr.append(tblW)
    largura_total = sum(novos)
    ja_correto = (tblW.get(qn("w:type")) == "dxa"
                  and tblW.get(qn("w:w")) == str(largura_total))
    tblW.set(qn("w:w"), str(largura_total))
    tblW.set(qn("w:type"), "dxa")

    tblPr = tabela._tbl.tblPr
    layout = tblPr.find(qn("w:tblLayout"))
    if layout is None:
        layout = tblPr.makeelement(qn("w:tblLayout"), {})
        tblPr.append(layout)
    layout.set(qn("w:type"), "fixed")

    if fator < 1.0:
        mudancas.append(
            f"largura reescalada de {total} para {largura_total} twips (área útil {util})"
        )
    elif not ja_correto:
        mudancas.append(
            f"largura declarada da tabela (tblW) corrigida para {largura_total} twips "
            f"dxa, batendo com o tblGrid — evita colapso de coluna no Word"
        )
    return mudancas


def padronizar(documento, padrao) -> list[str]:
    """
    Aplica o padrão de tabelas do perfil. Devolve a lista de mudanças.

    Idempotente: em segunda execução as propriedades já estão no valor alvo e
    nada é reescrito.
    """
    from util_ooxml import iter_tabelas

    config = {**padrao.base["tabelas"], **padrao.perfil.get("tabelas_overrides", {})}
    secao = documento.sections[0]
    util = largura_util_twips(secao)
    mudancas: list[str] = []

    for indice, tabela in enumerate(iter_tabelas(documento)):
        if config.get("ajustar_largura_area_util"):
            for item in _reescalar(tabela, util):
                mudancas.append(f"Tabela {indice}: {item}")

        if config.get("impedir_quebra_de_linha"):
            alteradas = sum(1 for linha in tabela.rows
                            if definir_nao_dividir_linha(linha, True))
            if alteradas:
                mudancas.append(
                    f"Tabela {indice}: {alteradas} linha(s) marcadas para não "
                    f"dividir entre páginas."
                )

        if config.get("repetir_cabecalho") and len(tabela.rows) > 1:
            if definir_repetir_cabecalho(tabela.rows[0], True):
                mudancas.append(f"Tabela {indice}: cabeçalho passa a repetir nas páginas.")

        margem = config.get("margens_internas_cm")
        if margem is not None and definir_margens_internas_tabela(tabela, float(margem)):
            mudancas.append(f"Tabela {indice}: margens internas uniformizadas em {margem} cm.")

        valign = config.get("alinhamento_vertical")
        if valign:
            alteradas = 0
            for linha in tabela.rows:
                for celula in linha.cells:
                    if definir_alinhamento_vertical(celula, valign):
                        alteradas += 1
            if alteradas:
                mudancas.append(
                    f"Tabela {indice}: alinhamento vertical '{valign}' em {alteradas} célula(s)."
                )

        if config.get("sombrear_cabecalho") and tabela.rows:
            cor = padrao.cor("sombreado_cabecalho_tabela")
            alteradas = 0
            vistas = set()
            for celula in tabela.rows[0].cells:
                if id(celula._tc) in vistas:
                    continue
                vistas.add(id(celula._tc))
                if sombrear_celula(celula, cor):
                    alteradas += 1
            if alteradas:
                mudancas.append(
                    f"Tabela {indice}: sombreamento {cor} aplicado ao cabeçalho "
                    f"({alteradas} célula(s))."
                )
    return mudancas


def celulas_perdidas(antes: list[list[list[str]]],
                     depois: list[list[list[str]]]) -> list[str]:
    """Compara a grade textual das tabelas antes e depois."""
    problemas: list[str] = []
    if len(antes) != len(depois):
        problemas.append(
            f"Quantidade de tabelas mudou: {len(antes)} -> {len(depois)}."
        )
        return problemas
    for indice, (a, d) in enumerate(zip(antes, depois)):
        if len(a) != len(d):
            problemas.append(f"Tabela {indice}: linhas {len(a)} -> {len(d)}.")
            continue
        for linha, (la, ld) in enumerate(zip(a, d)):
            if len(la) != len(ld):
                problemas.append(
                    f"Tabela {indice}, linha {linha}: células {len(la)} -> {len(ld)}."
                )
                continue
            for coluna, (ca, cd) in enumerate(zip(la, ld)):
                if ca != cd:
                    problemas.append(
                        f"Tabela {indice}, célula [{linha}][{coluna}]: conteúdo alterado."
                    )
    return problemas


def grade_textual(documento) -> list[list[list[str]]]:
    """Conteúdo textual normalizado de todas as tabelas, para validação."""
    from util_ooxml import iter_tabelas, normalizar_texto

    grade: list[list[list[str]]] = []
    for tabela in iter_tabelas(documento):
        linhas: list[list[str]] = []
        for linha in tabela.rows:
            linhas.append([normalizar_texto(celula.text) for celula in linha.cells])
        grade.append(linhas)
    return grade
