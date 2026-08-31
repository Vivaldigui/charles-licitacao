#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
normalizar_precos.py — Tratamento e estatística de preços para a pesquisa de
preços da Câmara Municipal de Itanhandu (Lei 14.133/2021, art. 23; Portaria
03/2024, arts. 1º, 2º, 5º).

Funções utilitárias (puro stdlib, sem dependências externas):
  - parse_brl: converte texto de moeda brasileira (R$ 1.234,56) em float;
  - parse_brl_verboso: retorna também o motivo quando o valor é inválido;
  - recalcular_unitario: deriva valor unitário a partir de valor total/quantidade;
  - detectar_outliers: marca valores discrepantes por IQR (1.5*IQR), apenas como
    CANDIDATOS a exclusão — a exclusão é decisão fundamentada do agente/Charles
    (Portaria 03/2024, art. 5º, §4º), nunca automática;
  - estatisticas: média, mediana e menor preço sobre o conjunto de preços VÁLIDOS;
  - sugerir_metodologia: texto-base de apoio (não substitui a justificativa humana).

REGRAS ANTIALUCINAÇÃO (ver 07_checklists/regras-pesquisa-de-precos.md):
  - O script NUNCA inventa preço. Valor ausente ou ilegível -> None (não é zero).
  - O script SINALIZA discrepância; quem exclui, com justificativa nos autos, é o
    agente/Charles. A exclusão automática é proibida.
  - Mínimo de 3 preços válidos para média/mediana/menor (Portaria 03/2024, art. 5º).
    Menos de 3 só com justificativa aprovada pelo Presidente (art. 5º, §7º).

Uso como módulo:
    from normalizar_precos import parse_brl, estatisticas, detectar_outliers

Uso como CLI (lê uma lista JSON de números ou de itens no stdin):
    echo '[100.0, 110.5, 250.0]' | python normalizar_precos.py
    python normalizar_precos.py --arquivo precos.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from statistics import median, mean
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Conversão de moeda
# ---------------------------------------------------------------------------
def parse_brl(valor: Any) -> Optional[float]:
    """Converte um valor em float.

    Aceita números (int/float) e strings no padrão brasileiro
    ("R$ 1.234,56", "1.234,56", "1234,56") e também o padrão com ponto decimal
    ("1234.56"). Retorna None quando NÃO for possível identificar um número
    seguro — jamais inventa zero.
    """
    numero, _motivo = parse_brl_verboso(valor)
    return numero


def parse_brl_verboso(valor: Any) -> tuple[Optional[float], Optional[str]]:
    """Converte valor para float e informa motivo quando não for seguro.

    A string com um único ponto, exatamente 3 dígitos depois dele e sem vírgula
    (ex.: "1.234") é ambígua no padrão BR: pode significar milhar ou decimal.
    Nesse caso retorna None e exige validação humana.
    """
    if valor is None:
        return None, "valor ausente"
    if isinstance(valor, (int, float)):
        v = float(valor)
        return (v, None) if v > 0 else (None, "valor menor ou igual a zero")
    if not isinstance(valor, str):
        return None, "tipo de valor não suportado"

    txt = valor.strip()
    if not txt:
        return None, "valor vazio"

    # Remove símbolo de moeda, espaços e texto, mantendo dígitos, ponto, vírgula e sinal.
    txt = re.sub(r"(?i)r\$\s*", "", txt)
    txt = re.sub(r"[^\d.,\-]", "", txt)
    if not txt or txt in {"-", ".", ","}:
        return None, "valor sem número identificável"

    tem_virgula = "," in txt
    tem_ponto = "." in txt
    if txt.startswith("-"):
        return None, "valor menor ou igual a zero"

    if tem_ponto and not tem_virgula and txt.count(".") == 1:
        antes, depois = txt.split(".", 1)
        if antes.isdigit() and depois.isdigit() and len(depois) == 3:
            return None, "valor ambíguo — validação humana"

    if tem_virgula and tem_ponto:
        # Assume padrão BR: ponto = milhar, vírgula = decimal -> remove pontos, vírgula vira ponto.
        txt = txt.replace(".", "").replace(",", ".")
    elif tem_virgula:
        # Apenas vírgula: decimal brasileiro.
        txt = txt.replace(",", ".")
    # else: apenas ponto -> já é decimal padrão.

    try:
        v = float(txt)
    except ValueError:
        return None, "valor ilegível"
    return (v, None) if v > 0 else (None, "valor menor ou igual a zero")


def recalcular_unitario(valor_total: Any, quantidade: Any) -> Optional[float]:
    """Deriva o valor unitário a partir do total e da quantidade.

    Útil quando a fonte só traz valor global. Retorna None se não for possível
    calcular com segurança (quantidade ausente, zero ou não numérica).
    """
    total = parse_brl(valor_total)
    try:
        qtd = float(str(quantidade).replace(",", ".")) if quantidade is not None else None
    except (ValueError, TypeError):
        qtd = None
    if total is None or not qtd or qtd <= 0:
        return None
    return round(total / qtd, 4)


# ---------------------------------------------------------------------------
# Discrepância (outliers) — apenas CANDIDATOS a exclusão
# ---------------------------------------------------------------------------
def detectar_outliers(precos: list[float], fator: float = 1.5) -> dict:
    """Marca candidatos a valor discrepante pelo método do intervalo interquartil.

    Retorna um dicionário com os limites (inferior/superior) e os índices dos
    valores fora do intervalo [Q1 - fator*IQR, Q3 + fator*IQR].

    IMPORTANTE: estes são apenas CANDIDATOS. A desconsideração depende de
    critério fundamentado descrito nos autos (Portaria 03/2024, art. 5º, §4º).
    Inexequível/inconsistente (§§5º-6º) é juízo do agente, não calculado aqui.
    """
    validos = [p for p in precos if isinstance(p, (int, float)) and p > 0]
    n = len(validos)
    resultado = {
        "n_validos": n,
        "limite_inferior": None,
        "limite_superior": None,
        "indices_discrepantes": [],
        "valores_discrepantes": [],
        "observacao": "",
    }
    if n < 4:
        resultado["observacao"] = (
            "Amostra pequena (<4): não se aplica detecção estatística de discrepância. "
            "Avaliar manualmente cada preço."
        )
        return resultado

    ordenados = sorted(validos)

    def _quartil(dados: list[float], q: float) -> float:
        pos = (len(dados) - 1) * q
        base = int(pos)
        resto = pos - base
        if base + 1 < len(dados):
            return dados[base] + resto * (dados[base + 1] - dados[base])
        return dados[base]

    q1 = _quartil(ordenados, 0.25)
    q3 = _quartil(ordenados, 0.75)
    iqr = q3 - q1
    li = q1 - fator * iqr
    ls = q3 + fator * iqr
    resultado["limite_inferior"] = round(li, 4)
    resultado["limite_superior"] = round(ls, 4)
    for i, p in enumerate(precos):
        if isinstance(p, (int, float)) and p > 0 and (p < li or p > ls):
            resultado["indices_discrepantes"].append(i)
            resultado["valores_discrepantes"].append(p)
    if resultado["indices_discrepantes"]:
        resultado["observacao"] = (
            "Há candidatos a valor discrepante (fora de [Q1-1.5*IQR, Q3+1.5*IQR]). "
            "A exclusão exige justificativa fundamentada nos autos (Portaria 03/2024, art. 5º, §4º)."
        )
    else:
        resultado["observacao"] = "Nenhum candidato a discrepante pelo critério IQR."
    return resultado


# ---------------------------------------------------------------------------
# Estatística (média, mediana, menor)
# ---------------------------------------------------------------------------
def estatisticas(precos_validos: list[float]) -> dict:
    """Calcula média, mediana e menor preço sobre o conjunto de preços VÁLIDOS.

    'Válidos' = já depurados de inexequíveis/inconsistentes/excessivos pelo
    agente. O script apenas calcula sobre o que recebe.

    Sinaliza quando há menos de 3 preços (Portaria 03/2024, art. 5º): nesse caso
    os cálculos ainda são retornados, mas com alerta de que dependem de
    justificativa aprovada pelo Presidente (art. 5º, §7º).
    """
    validos = [float(p) for p in precos_validos if isinstance(p, (int, float)) and p > 0]
    n = len(validos)
    out: dict = {
        "n": n,
        "media": None,
        "mediana": None,
        "menor": None,
        "maior": None,
        "alerta_minimo": None,
    }
    if n == 0:
        out["alerta_minimo"] = (
            "Nenhum preço válido. Não há base para estimativa — registrar a "
            "insuficiência e propor diligência (ver roteiro)."
        )
        return out
    out["media"] = round(mean(validos), 4)
    out["mediana"] = round(median(validos), 4)
    out["menor"] = round(min(validos), 4)
    out["maior"] = round(max(validos), 4)
    if n < 3:
        out["alerta_minimo"] = (
            f"Apenas {n} preço(s) válido(s). O mínimo é 3 (Portaria 03/2024, art. 5º). "
            "Estimativa com menos de 3 só com justificativa aprovada pelo Presidente "
            "(art. 5º, §7º), OU complementar a cesta com novos parâmetros do art. 23."
        )
    return out


def fmt_brl(valor: Optional[float]) -> str:
    """Formata um float como moeda brasileira (R$ 1.234,56). None -> '—'."""
    if valor is None:
        return "—"
    s = f"{valor:,.2f}"
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"


def sugerir_metodologia(stats: dict, outliers: dict) -> str:
    """Texto-base de apoio à escolha de metodologia (NÃO substitui a justificativa
    humana exigida pela Portaria 03/2024, art. 2º, VI). Apenas orienta."""
    n = stats.get("n", 0)
    if n == 0:
        return ("Sem preços válidos: não há metodologia a sugerir. Registrar insuficiência.")
    partes = []
    if n < 3:
        partes.append(
            "Conjunto com menos de 3 preços: por padrão, não calcular média/mediana "
            "sem justificativa aprovada pelo Presidente (art. 5º, §7º). Preferir "
            "complementar a cesta."
        )
    if outliers.get("indices_discrepantes"):
        partes.append(
            "Há candidatos a discrepante: avaliar exclusão fundamentada (art. 5º, §4º) "
            "ou adotar a MEDIANA, que é mais robusta a valores extremos."
        )
    else:
        partes.append(
            "Sem discrepantes evidentes: a MÉDIA dos preços válidos é aceitável; "
            "a MEDIANA ou o MENOR preço podem ser adotados, desde que justificado."
        )
    partes.append(
        "Decisão final de método (média/mediana/menor) e de exclusões é do agente "
        "responsável, registrada na minuta (campos {{JUSTIFICATIVA_METODOLOGIA}} e "
        "{{MEMORIA_CALCULO}})."
    )
    return " ".join(partes)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _coletar_precos(dados: Any) -> list[Optional[float]]:
    """Aceita lista de números, de strings de moeda ou de itens (dict com
    'valor_unitario'/'valor_total'+'quantidade')."""
    precos: list[Optional[float]] = []
    if isinstance(dados, list):
        for item in dados:
            if isinstance(item, dict):
                vu = parse_brl(item.get("valor_unitario"))
                if vu is None:
                    vu = recalcular_unitario(item.get("valor_total"), item.get("quantidade"))
                precos.append(vu)
            else:
                precos.append(parse_brl(item))
    return precos


def _coletar_precos_verboso(dados: Any) -> tuple[list[Optional[float]], list[dict[str, Any]]]:
    """Coleta preços e registra motivos de itens sem valor."""
    precos: list[Optional[float]] = []
    motivos: list[dict[str, Any]] = []
    if isinstance(dados, list):
        for indice, item in enumerate(dados):
            if isinstance(item, dict):
                vu, motivo = parse_brl_verboso(item.get("valor_unitario"))
                if vu is None:
                    vu = recalcular_unitario(item.get("valor_total"), item.get("quantidade"))
                    if vu is not None:
                        motivo = None
                precos.append(vu)
            else:
                vu, motivo = parse_brl_verboso(item)
                precos.append(vu)
            if precos[-1] is None:
                motivos.append({"indice": indice, "motivo": motivo or "valor não identificado"})
    return precos, motivos


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Normaliza e calcula estatística de preços (BR).")
    ap.add_argument("--arquivo", help="JSON com lista de preços ou de itens. Default: stdin.")
    args = ap.parse_args(argv)

    bruto = open(args.arquivo, encoding="utf-8").read() if args.arquivo else sys.stdin.read()
    try:
        dados = json.loads(bruto)
    except json.JSONDecodeError as e:
        print(json.dumps({"erro": f"JSON inválido: {e}"}, ensure_ascii=False))
        return 2

    precos, motivos_sem_valor = _coletar_precos_verboso(dados)
    validos = [p for p in precos if p is not None]
    out = detectar_outliers(validos)
    stats = estatisticas(validos)
    relatorio = {
        "precos_recebidos": precos,
        "precos_validos": validos,
        "n_sem_valor": sum(1 for p in precos if p is None),
        "motivos_sem_valor": motivos_sem_valor,
        "outliers": out,
        "estatisticas": stats,
        "media_formatada": fmt_brl(stats["media"]),
        "mediana_formatada": fmt_brl(stats["mediana"]),
        "menor_formatado": fmt_brl(stats["menor"]),
        "sugestao_metodologia": sugerir_metodologia(stats, out),
    }
    print(json.dumps(relatorio, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
