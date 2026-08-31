#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gerar_painel.py — Gera painel HTML local, estático e somente leitura.

Fontes:
  - 06_precedentes_camara/contratacoes.csv
  - 06_precedentes_camara/limites.json
  - 08_processos_em_andamento/**/processo.json
  - 05_minutas/_CONTROLE_MINUTAS.md
  - scripts/validar_base.py
"""
from __future__ import annotations

import html
import json
import re
from pathlib import Path
from typing import Any

from controle_cnae import carregar_contratacoes, carregar_limites, decimal_para_brl, moeda_para_decimal, obter_limite
from validar_base import validar

RAIZ = Path(__file__).resolve().parents[1]
SAIDA = RAIZ / "painel" / "index.html"


def _esc(valor: Any) -> str:
    return html.escape(str(valor if valor is not None else ""))


def _acumulados() -> list[dict[str, Any]]:
    registros = carregar_contratacoes()
    limites = carregar_limites()
    grupos: dict[tuple[str, str, str], Any] = {}
    for registro in registros:
        if str(registro.get("conta_para_limite", "")).strip().upper() not in {"S", "SIM"}:
            continue
        valor = moeda_para_decimal(registro.get("valor"))
        if valor is None:
            continue
        chave = (
            registro.get("exercicio", ""),
            registro.get("cnae_subclasse", ""),
            (registro.get("inciso", "") or "II").upper(),
        )
        grupos[chave] = grupos.get(chave, valor * 0) + valor
    saida = []
    for (exercicio, cnae, inciso), total in sorted(grupos.items()):
        limite, decreto, fonte = obter_limite(limites, exercicio=exercicio, inciso=inciso)
        percentual = None
        cor = "cinza"
        if limite and limite > 0:
            percentual = float(total / limite * 100)
            if percentual < 60:
                cor = "verde"
            elif percentual <= 85:
                cor = "amarelo"
            else:
                cor = "vermelho"
        saida.append({
            "exercicio": exercicio,
            "cnae": cnae,
            "inciso": inciso,
            "total": total,
            "limite": limite,
            "percentual": percentual,
            "cor": cor,
            "decreto": decreto,
            "fonte": fonte,
        })
    return saida


def _processos() -> list[dict[str, Any]]:
    processos = []
    base = RAIZ / "08_processos_em_andamento"
    if not base.exists():
        return processos
    for caminho in sorted(base.rglob("processo.json")):
        if "_MODELO" in caminho.parts:
            continue
        try:
            dados = json.loads(caminho.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            dados = {}
        bruto = json.dumps(dados, ensure_ascii=False)
        pendencias = bruto.count("[PREENCHER") + bruto.count("null")
        processos.append({
            "arquivo": caminho.relative_to(RAIZ).as_posix(),
            "numero": dados.get("numero_processo", ""),
            "objeto": dados.get("objeto", ""),
            "fase": dados.get("status_fase", ""),
            "pendencias": pendencias,
        })
    return processos


def _minutas() -> list[dict[str, str]]:
    controle = RAIZ / "05_minutas" / "_CONTROLE_MINUTAS.md"
    if not controle.exists():
        return []
    linhas = controle.read_text(encoding="utf-8").splitlines()
    capturar = False
    itens = []
    for linha in linhas:
        if linha.startswith("| Documento | Minuta-mãe |"):
            capturar = True
            continue
        if capturar and (not linha.startswith("|") or linha.startswith("|---")):
            continue
        if capturar and linha.startswith("|"):
            partes = [p.strip() for p in linha.strip("|").split("|")]
            if len(partes) >= 5:
                itens.append({
                    "documento": re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", partes[0]),
                    "versao": partes[3],
                    "status": partes[4],
                })
    return itens


def _alertas_base() -> list[str]:
    erros, avisos = validar()
    return erros or avisos


def _barra(item: dict[str, Any]) -> str:
    if item["percentual"] is None:
        largura = 100
        texto = "limite não confirmado"
    else:
        largura = max(0, min(item["percentual"], 100))
        texto = f"{item['percentual']:.1f}%"
    return (
        f'<div class="barra"><span class="{item["cor"]}" style="width:{largura:.1f}%"></span></div>'
        f'<small>{_esc(texto)}</small>'
    )


def gerar_html() -> str:
    acumulados = _acumulados()
    processos = _processos()
    minutas = _minutas()
    alertas = _alertas_base()
    css = """
body{font-family:Segoe UI,Arial,sans-serif;margin:0;background:#f6f7f9;color:#1f2933}
header{background:#243447;color:white;padding:24px 32px}
main{max-width:1180px;margin:0 auto;padding:24px}
section{margin:0 0 28px 0}
h1{margin:0;font-size:28px}h2{font-size:20px;margin:0 0 12px}
table{width:100%;border-collapse:collapse;background:white;border:1px solid #d9dee7}
th,td{padding:10px 12px;border-bottom:1px solid #e6eaf0;text-align:left;font-size:14px;vertical-align:top}
th{background:#eef2f6}
.barra{height:12px;background:#e1e6ee;border-radius:6px;overflow:hidden;min-width:140px}
.barra span{display:block;height:100%}.verde{background:#2f9e44}.amarelo{background:#f59f00}.vermelho{background:#e03131}.cinza{background:#868e96}
.alerta{background:white;border-left:4px solid #e03131;padding:10px 12px;margin:8px 0}
.ok{border-left-color:#2f9e44}
small{color:#52606d}
"""
    partes = [
        "<!doctype html><html lang=\"pt-BR\"><meta charset=\"utf-8\">",
        "<title>Painel Charles</title>",
        f"<style>{css}</style>",
        "<header><h1>Painel local Charles</h1><small>Somente leitura · gerado de arquivos locais</small></header><main>",
        "<section><h2>Acumulado por CNAE</h2><table><tr><th>Exercício</th><th>CNAE</th><th>Inciso</th><th>Total</th><th>Limite</th><th>Uso</th></tr>",
    ]
    if acumulados:
        for item in acumulados:
            limite = "não confirmado" if item["limite"] is None else "R$ " + decimal_para_brl(item["limite"])
            partes.append(
                f"<tr><td>{_esc(item['exercicio'])}</td><td>{_esc(item['cnae'])}</td>"
                f"<td>{_esc(item['inciso'])}</td><td>R$ {_esc(decimal_para_brl(item['total']))}</td>"
                f"<td>{_esc(limite)}</td><td>{_barra(item)}</td></tr>"
            )
    else:
        partes.append("<tr><td colspan=\"6\">Nenhum acumulado registrado.</td></tr>")
    partes.append("</table></section>")

    partes.append("<section><h2>Processos em andamento</h2><table><tr><th>Arquivo</th><th>Número</th><th>Objeto</th><th>Fase</th><th>Pendências</th></tr>")
    if processos:
        for proc in processos:
            partes.append(
                f"<tr><td>{_esc(proc['arquivo'])}</td><td>{_esc(proc['numero'])}</td>"
                f"<td>{_esc(proc['objeto'])}</td><td>{_esc(proc['fase'])}</td><td>{_esc(proc['pendencias'])}</td></tr>"
            )
    else:
        partes.append("<tr><td colspan=\"5\">Nenhum processo com processo.json localizado.</td></tr>")
    partes.append("</table></section>")

    partes.append("<section><h2>Minutas</h2><table><tr><th>Documento</th><th>Versão</th><th>Status</th></tr>")
    for minuta in minutas:
        partes.append(
            f"<tr><td>{_esc(minuta['documento'])}</td><td>{_esc(minuta['versao'])}</td><td>{_esc(minuta['status'])}</td></tr>"
        )
    partes.append("</table></section>")

    partes.append("<section><h2>Alertas de manutenção</h2>")
    for alerta in alertas:
        classe = "ok" if str(alerta).startswith("Base validada") else "alerta"
        partes.append(f"<div class=\"alerta {classe}\">{_esc(alerta)}</div>")
    partes.append("</section></main></html>")
    return "\n".join(partes)


def main() -> int:
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text(gerar_html(), encoding="utf-8")
    print(f"Painel gerado em {SAIDA}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

