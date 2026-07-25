#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
numeracao_docx.py — Diagnóstico e correção da numeração de tópicos.

Trata apenas numeração ESTRUTURAL digitada no texto (1., 1.1., 1.1.1.). Nunca
toca em numeração que seja conteúdo jurídico: artigos, incisos, cláusulas,
números de processo/portaria, datas, valores, CATMAT/CATSER/CNAE.

A renumeração é sempre proposta antes de ser aplicada, e é bloqueada quando há
referência interna que ficaria inconsistente.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, Optional

from util_ooxml import qn, texto_paragrafo

# --------------------------------------------------------------------------- #
# Reconhecimento de rótulos
# --------------------------------------------------------------------------- #

RE_ROTULO = re.compile(r"^(\s*)(\d+(?:\.\d+)*)(\s*)([\.\)\-–—])?(\s+)(?=\S)")

# Contextos em que o número NÃO é tópico estrutural.
RE_PROIBIDO = re.compile(
    r"(?:^|\s)(?:"
    r"[Aa]rt\.?\s*\d+"
    r"|artigo\s+\d+"
    r"|inciso\s+[IVXLC]+"
    r"|§\s*\d+"
    r"|[Ll]ei\s+n?[ºo°.]?\s*\d"
    r"|[Dd]ecreto\s+n?[ºo°.]?\s*\d"
    r"|[Pp]ortaria\s+n?[ºo°.]?\s*\d"
    r"|[Pp]rocesso\s+n?[ºo°.]?\s*\d"
    r"|CATMAT|CATSER|CNAE|CNPJ|CPF"
    r"|R\$\s*[\d.]"
    r"|\d{2}/\d{2}/\d{4}"
    r")"
)
RE_CLAUSULA_EXTENSO = re.compile(r"^\s*(CL[ÁA]USULA|PAR[ÁA]GRAFO)\b", re.IGNORECASE)

# Referências internas que a renumeração pode invalidar.
RE_REFERENCIA_INTERNA = re.compile(
    r"(?:\b(?:conforme|nos termos d[oa]|previst[oa] n[oa]|constante d[oa]|"
    r"referid[oa] n[oa]|vide|ver)\s+)?"
    r"\b(item|subitem|subitens|itens|cl[áa]usula|subcl[áa]usula|se[çc][ãa]o|anexo)\s+"
    r"([0-9]+(?:\.[0-9]+)*|[IVXLC]+|[A-Za-zçãéêó]+)",
    re.IGNORECASE,
)


@dataclass
class ItemNumerado:
    """Um tópico numerado manualmente no texto."""

    indice_paragrafo: int
    rotulo: str
    nivel: int
    separador: str
    texto: str
    automatico: bool = False


@dataclass
class ProblemaNumeracao:
    """Inconsistência detectada na numeração."""

    tipo: str
    indice_paragrafo: int
    rotulo: str
    detalhe: str
    corrigivel: bool
    sugestao: Optional[str] = None


@dataclass
class DiagnosticoNumeracao:
    itens: list[ItemNumerado] = field(default_factory=list)
    problemas: list[ProblemaNumeracao] = field(default_factory=list)
    referencias_internas: list[tuple[int, str, str]] = field(default_factory=list)
    separadores: set[str] = field(default_factory=set)
    mistura_manual_automatica: bool = False

    @property
    def corrigivel_automaticamente(self) -> bool:
        return bool(self.problemas) and all(p.corrigivel for p in self.problemas)


def _tem_numeracao_automatica(paragrafo) -> bool:
    pPr = paragrafo._p.find(qn("w:pPr"))
    return pPr is not None and pPr.find(qn("w:numPr")) is not None


def eh_numeracao_protegida(texto: str) -> bool:
    """True quando o número no início do parágrafo é conteúdo, não estrutura."""
    if RE_CLAUSULA_EXTENSO.match(texto):
        return True
    inicio = texto[:120]
    return bool(RE_PROIBIDO.search(inicio))


def extrair_referencias_internas(texto: str) -> list[tuple[str, str]]:
    """Devolve pares (tipo, alvo) de referências internas encontradas."""
    achados: list[tuple[str, str]] = []
    for casamento in RE_REFERENCIA_INTERNA.finditer(texto):
        achados.append((casamento.group(1).lower(), casamento.group(2)))
    return achados


def analisar(paragrafos: Iterable,
             clausulas_por_extenso: bool = False) -> DiagnosticoNumeracao:
    """
    Analisa a numeração manual dos parágrafos e devolve o diagnóstico.

    Detecta: duplicidade, item pulado, subitem órfão (1.1 sem 1), reinício
    indevido, separadores misturados e mistura de lista manual com automática.

    `clausulas_por_extenso=True` (perfis de contrato e termo aditivo): o nível
    superior é escrito por extenso — "CLÁUSULA PRIMEIRA", "CLÁUSULA SEGUNDA" —
    e não como "1.". Sem isso, toda subcláusula "1.1" seria acusada de órfã, o
    que é falso: o item "1" existe, só que redigido por extenso.
    """
    diagnostico = DiagnosticoNumeracao()
    tem_automatica = False
    prefixos_por_extenso: set[str] = set()
    clausulas_vistas = 0

    for indice, paragrafo in enumerate(paragrafos):
        texto = texto_paragrafo(paragrafo).strip()
        if not texto:
            continue
        if clausulas_por_extenso and RE_CLAUSULA_EXTENSO.match(texto):
            clausulas_vistas += 1
            prefixos_por_extenso.add(str(clausulas_vistas))
        if _tem_numeracao_automatica(paragrafo):
            tem_automatica = True
            continue
        casamento = RE_ROTULO.match(texto)
        if not casamento:
            continue
        if eh_numeracao_protegida(texto):
            continue
        rotulo = casamento.group(2)
        separador = casamento.group(4) or ""
        resto = texto[casamento.end():]
        diagnostico.separadores.add(separador)
        diagnostico.itens.append(
            ItemNumerado(
                indice_paragrafo=indice,
                rotulo=rotulo,
                nivel=rotulo.count(".") + 1,
                separador=separador,
                texto=resto,
            )
        )

    diagnostico.mistura_manual_automatica = bool(diagnostico.itens) and tem_automatica

    for indice, paragrafo in enumerate(paragrafos):
        texto = texto_paragrafo(paragrafo)
        for tipo, alvo in extrair_referencias_internas(texto):
            diagnostico.referencias_internas.append((indice, tipo, alvo))

    _detectar_problemas(diagnostico, prefixos_por_extenso)
    return diagnostico


def _detectar_problemas(diagnostico: DiagnosticoNumeracao,
                        prefixos_por_extenso: Optional[set[str]] = None) -> None:
    vistos: dict[str, int] = {}
    esperado: dict[str, int] = {}   # prefixo -> próximo número esperado
    # Prefixos já existentes por outra via (cláusulas escritas por extenso).
    prefixos_conhecidos: set[str] = set(prefixos_por_extenso or set())

    for item in diagnostico.itens:
        partes = item.rotulo.split(".")
        prefixo = ".".join(partes[:-1])
        ultimo = int(partes[-1])

        if item.rotulo in vistos:
            diagnostico.problemas.append(ProblemaNumeracao(
                tipo="numero_duplicado",
                indice_paragrafo=item.indice_paragrafo,
                rotulo=item.rotulo,
                detalhe=f"Rótulo '{item.rotulo}' já usado no parágrafo "
                        f"{vistos[item.rotulo]}.",
                corrigivel=True,
            ))
        else:
            vistos[item.rotulo] = item.indice_paragrafo

        if prefixo and prefixo not in prefixos_conhecidos:
            diagnostico.problemas.append(ProblemaNumeracao(
                tipo="subitem_orfao",
                indice_paragrafo=item.indice_paragrafo,
                rotulo=item.rotulo,
                detalhe=f"Subitem '{item.rotulo}' aparece sem o item superior "
                        f"'{prefixo}'.",
                corrigivel=False,
                sugestao="Exige decisão humana: criar o item superior ou "
                         "rebaixar o subitem.",
            ))

        proximo = esperado.get(prefixo, 1)
        if ultimo > proximo:
            faltantes = ", ".join(
                f"{prefixo + '.' if prefixo else ''}{n}" for n in range(proximo, ultimo)
            )
            diagnostico.problemas.append(ProblemaNumeracao(
                tipo="numero_pulado",
                indice_paragrafo=item.indice_paragrafo,
                rotulo=item.rotulo,
                detalhe=f"Salto de numeração: faltam {faltantes}.",
                corrigivel=True,
                sugestao=f"{prefixo + '.' if prefixo else ''}{proximo}",
            ))
        elif ultimo < proximo:
            diagnostico.problemas.append(ProblemaNumeracao(
                tipo="reinicio_indevido",
                indice_paragrafo=item.indice_paragrafo,
                rotulo=item.rotulo,
                detalhe=f"Numeração retrocedeu: esperado "
                        f"{prefixo + '.' if prefixo else ''}{proximo}.",
                corrigivel=True,
                sugestao=f"{prefixo + '.' if prefixo else ''}{proximo}",
            ))

        esperado[prefixo] = max(proximo, ultimo) + 1
        prefixos_conhecidos.add(item.rotulo)
        # Ao mudar de item de nível superior, os níveis abaixo reiniciam.
        for chave in list(esperado):
            if chave.startswith(item.rotulo + ".") or (
                prefixo and chave.startswith(prefixo + ".") and chave != prefixo
                and chave.count(".") > item.rotulo.count(".")
            ):
                del esperado[chave]

    separadores_reais = {s for s in diagnostico.separadores if s}
    if len(separadores_reais) > 1:
        diagnostico.problemas.append(ProblemaNumeracao(
            tipo="separadores_misturados",
            indice_paragrafo=-1,
            rotulo="",
            detalhe="Separadores misturados nos rótulos: "
                    + ", ".join(sorted(repr(s) for s in separadores_reais)),
            corrigivel=True,
            sugestao="Padronizar em '.'",
        ))

    if diagnostico.mistura_manual_automatica:
        diagnostico.problemas.append(ProblemaNumeracao(
            tipo="lista_manual_e_automatica",
            indice_paragrafo=-1,
            rotulo="",
            detalhe="O documento mistura numeração digitada manualmente com "
                    "lista automática do Word.",
            corrigivel=False,
            sugestao="Exige decisão humana: unificar em um dos dois modos.",
        ))


def propor_renumeracao(diagnostico: DiagnosticoNumeracao,
                       separador: str = ".") -> dict[int, tuple[str, str]]:
    """
    Propõe a numeração corrigida.

    Devolve {indice_paragrafo: (rotulo_antigo, rotulo_novo)}, apenas para itens
    cujo rótulo mudaria. Não aplica nada.
    """
    contadores: dict[str, int] = {}
    proposta: dict[int, tuple[str, str]] = {}
    mapa_antigo_novo: dict[str, str] = {}

    for item in diagnostico.itens:
        partes = item.rotulo.split(".")
        prefixo_antigo = ".".join(partes[:-1])
        prefixo_novo = mapa_antigo_novo.get(prefixo_antigo, prefixo_antigo)
        contadores[prefixo_novo] = contadores.get(prefixo_novo, 0) + 1
        numero = contadores[prefixo_novo]
        novo = f"{prefixo_novo}.{numero}" if prefixo_novo else str(numero)
        mapa_antigo_novo[item.rotulo] = novo
        # Reinicia contadores dos níveis abaixo deste item.
        for chave in list(contadores):
            if chave.startswith(novo + "."):
                del contadores[chave]
        if novo != item.rotulo or item.separador != separador:
            proposta[item.indice_paragrafo] = (item.rotulo, novo)
    return proposta


def referencias_afetadas(diagnostico: DiagnosticoNumeracao,
                         proposta: dict[int, tuple[str, str]]) -> list[str]:
    """Referências internas que apontam para rótulos que mudariam."""
    alterados = {antigo for antigo, novo in proposta.values() if antigo != novo}
    afetadas: list[str] = []
    for indice, tipo, alvo in diagnostico.referencias_internas:
        if alvo in alterados:
            afetadas.append(
                f"parágrafo {indice}: '{tipo} {alvo}' aponta para rótulo que "
                f"seria renumerado"
            )
    return afetadas


def aplicar_renumeracao(paragrafos: list, proposta: dict[int, tuple[str, str]],
                        separador: str = ".") -> list[str]:
    """
    Reescreve apenas o rótulo numérico no início dos parágrafos indicados.

    Altera o texto do primeiro w:t do parágrafo, preservando a formatação. É a
    única função do módulo que muda texto — por isso só roda com autorização
    expressa (`--corrigir-numeracao`) e com a validação de referências internas
    já aprovada.
    """
    from util_ooxml import definir_texto, elementos_texto

    aplicadas: list[str] = []
    for indice, (antigo, novo) in sorted(proposta.items()):
        paragrafo = paragrafos[indice]
        elementos = elementos_texto(paragrafo)
        if not elementos:
            continue
        completo = "".join(e.text or "" for e in elementos)
        casamento = RE_ROTULO.match(completo.strip())
        if not casamento or casamento.group(2) != antigo:
            continue
        espacos_iniciais = len(completo) - len(completo.lstrip())
        prefixo = completo[:espacos_iniciais]
        resto = completo.strip()[casamento.end():]
        novo_completo = f"{prefixo}{novo}{separador} {resto}"
        definir_texto(elementos[0], novo_completo)
        for elemento in elementos[1:]:
            definir_texto(elemento, "")
        aplicadas.append(f"{antigo} -> {novo}")
    return aplicadas


def detectar_fragmentacao(paragrafos: Iterable, limite_curto: int = 90,
                          proporcao: float = 0.45) -> Optional[str]:
    """
    Sinaliza documento excessivamente fragmentado em tópicos.

    Nunca funde parágrafos: fusão é alteração de conteúdo. Apenas reporta.
    """
    numerados = 0
    curtos = 0
    total = 0
    for paragrafo in paragrafos:
        texto = texto_paragrafo(paragrafo).strip()
        if not texto:
            continue
        total += 1
        if RE_ROTULO.match(texto) or _tem_numeracao_automatica(paragrafo):
            numerados += 1
            if len(texto) <= limite_curto:
                curtos += 1
    if total < 15 or numerados == 0:
        return None
    if numerados / total >= proporcao and curtos / max(numerados, 1) >= 0.5:
        return (
            f"{numerados} de {total} parágrafos são tópicos numerados e "
            f"{curtos} deles têm menos de {limite_curto} caracteres. "
            "Indício de fragmentação excessiva — a consolidação depende de "
            "autorização expressa (altera conteúdo)."
        )
    return None
