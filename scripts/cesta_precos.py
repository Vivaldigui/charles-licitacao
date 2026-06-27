#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cesta_precos.py — Orquestrador da funcionalidade "Executar Pesquisa de Preços".

Reúne as fontes (PNCP + busca web/manual), normaliza os valores, monta a CESTA
DE PREÇOS, calcula média/mediana/menor, sinaliza discrepantes e gera um
RELATÓRIO ESTRUTURADO (Markdown) com os 13 blocos exigidos, além dos textos
prontos para os campos {{...}} da minuta-mãe oficial de Pesquisa de Preços.

IMPORTANTE — DIVISÃO DE PAPÉIS
  - Este script faz a parte MECÂNICA: coleta, normalização, estatística,
    triagem de discrepantes e montagem do esqueleto do relatório.
  - O JUÍZO jurídico (comparabilidade final, exclusões fundamentadas, escolha
    de metodologia, redação institucional) é do agente/Charles, conforme o
    roteiro 07_checklists/roteiro-executar-pesquisa-de-precos.md.
  - Por isso o relatório traz marcadores [PREENCHER: ...] e [VALIDAÇÃO HUMANA]
    onde a decisão não pode ser automatizada. NADA é inventado.

ENTRADA (JSON do processo) — ver scripts/exemplos/entrada-exemplo.json:
  {
    "objeto": "...", "descricao_detalhada": "...", "unidade": "unid.",
    "quantidade": 30, "categoria": "mobiliário", "periodo_busca": "2024-2025",
    "filtros": {"uf": "MG", "municipio": "Itanhandu", "modalidade": "dispensa"},
    "valor_estimado_inicial": "1500,00", "observacoes": "...",
    "minuta": "05_minutas/PESQUISA_DE_PRECOS/PESQUISA_PRECOS_MINUTA_MAE.docx"
  }

Itens MANUAIS (JSON, lista) — ver scripts/exemplos/manual-exemplo.json:
  [{"fonte": "...", "orgao": "...", "objeto_encontrado": "...",
    "modalidade": "...", "data": "2025-03-10", "quantidade": 30,
    "unidade": "unid.", "valor_unitario": "289,90", "valor_total": "",
    "link": "https://...", "comparabilidade": "alta", "data_acesso": "2026-06-27"}]

Uso:
  # Coleta automática (PNCP) + busca web/sugestões, e gera o relatório:
  python cesta_precos.py --processo entrada.json --pncp --web --saida relatorio.md

  # Modo manual (cola dados já coletados pelo humano):
  python cesta_precos.py --processo entrada.json --manual manual.json --saida relatorio.md

  # Combinar tudo:
  python cesta_precos.py --processo entrada.json --pncp --web --manual manual.json
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from typing import Any, Optional

from normalizar_precos import (
    parse_brl,
    recalcular_unitario,
    detectar_outliers,
    estatisticas,
    fmt_brl,
    sugerir_metodologia,
)

try:
    from pncp_consulta import consultar_pncp
except Exception:  # noqa: BLE001 — PNCP é opcional
    consultar_pncp = None  # type: ignore
try:
    from busca_web import buscar_web
except Exception:  # noqa: BLE001 — web é opcional
    buscar_web = None  # type: ignore


# Situações possíveis da cesta (Portaria 03/2024, art. 5º; art. 4º).
SIT_VALIDO = "válido"
SIT_VALIDO_RESSALVA = "válido com ressalva"
SIT_SEM_VALOR = "excluído por ausência de valor"
SIT_DISCREPANTE = "excluído por valor discrepante"  # candidato — exige justificativa
SIT_DATA_ANTIGA = "excluído por data antiga"
SIT_BAIXA_COMPARAB = "excluído por baixa comparabilidade"
SIT_ESPEC_INCOMPAT = "excluído por especificação incompatível"


def _hoje_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _ano_de(data_str: Any) -> Optional[int]:
    """Extrai o ano de uma data textual (AAAA-MM-DD, DD/MM/AAAA etc.)."""
    s = str(data_str or "")
    import re

    m = re.search(r"(19|20)\d{2}", s)
    return int(m.group(0)) if m else None


def _item_base() -> dict:
    return {
        "fonte": "", "orgao": "", "objeto_encontrado": "", "modalidade": "",
        "data": "", "quantidade": "", "unidade": "", "valor_unitario": "",
        "valor_total": "", "link": "", "comparabilidade": "", "data_acesso": "",
        "situacao": "", "observacao": "",
    }


def coletar_pncp(processo: dict) -> list[dict]:
    """Coleta itens do PNCP a partir do objeto do processo."""
    if consultar_pncp is None:
        return []
    filtros = processo.get("filtros", {}) or {}
    res = consultar_pncp(
        processo.get("objeto", ""),
        uf=filtros.get("uf"),
        max_itens=int(processo.get("max_pncp", 10)),
    )
    itens = []
    for it in res.get("itens", []):
        novo = _item_base()
        novo.update({
            "fonte": "PNCP",
            "orgao": it.get("orgao", ""),
            "objeto_encontrado": it.get("objeto_encontrado", ""),
            "modalidade": it.get("modalidade", ""),
            "data": it.get("data", ""),
            "quantidade": it.get("quantidade", ""),
            "unidade": it.get("unidade_medida", ""),
            "valor_unitario": it.get("valor_unitario", ""),
            "valor_total": it.get("valor_total", ""),
            "link": it.get("link", ""),
            "data_acesso": res.get("data_consulta", ""),
            "comparabilidade": "[VALIDAÇÃO HUMANA]",
            "observacao": "Origem PNCP — conferir item/objeto antes de usar.",
        })
        itens.append(novo)
    return itens, res  # type: ignore[return-value]


def montar_cesta(itens: list[dict], processo: dict) -> list[dict]:
    """Aplica triagem MECÂNICA de situação a cada item e calcula unitário quando faltar.

    Decisões automatizáveis: ausência de valor e idade da contratação.
    Decisões que dependem de juízo (comparabilidade, exclusão de discrepante)
    ficam marcadas para validação humana — não exclui sozinho.
    """
    ano_corte = datetime.now().year - 1  # art. 4º, II: 1 ano; III/IV: 6 meses (alerta no relatório)
    precos_validos: list[float] = []

    for it in itens:
        # 1) resolve valor unitário (parse direto ou recálculo a partir do total)
        vu = parse_brl(it.get("valor_unitario"))
        if vu is None:
            vu = recalcular_unitario(it.get("valor_total"), it.get("quantidade"))
            if vu is not None:
                it["observacao"] = (it.get("observacao", "") + " Unitário recalculado do total/qtd.").strip()
        it["_valor_unitario_num"] = vu

        # 2) situação preliminar
        if vu is None:
            it["situacao"] = SIT_SEM_VALOR
            continue

        ano = _ano_de(it.get("data"))
        if ano is not None and ano < ano_corte:
            it["situacao"] = SIT_DATA_ANTIGA
            it["observacao"] = (it.get("observacao", "") + f" Data {ano} anterior ao corte ({ano_corte}); usar só com índice de atualização justificado.").strip()
            continue

        # comparabilidade declarada como baixa -> exclui; caso contrário, válido (com ressalva se sem juízo)
        comp = str(it.get("comparabilidade", "")).strip().lower()
        if comp in ("baixa", "baixo"):
            it["situacao"] = SIT_BAIXA_COMPARAB
            continue
        if comp in ("", "[validação humana]"):
            it["situacao"] = SIT_VALIDO_RESSALVA
            it["observacao"] = (it.get("observacao", "") + " Comparabilidade pendente de validação humana.").strip()
        else:
            it["situacao"] = SIT_VALIDO
        precos_validos.append(vu)

    # 3) discrepância sobre os preços considerados válidos/ressalva
    outliers = detectar_outliers(precos_validos)
    discrepantes = set(outliers.get("valores_discrepantes", []))
    for it in itens:
        if it.get("situacao") in (SIT_VALIDO, SIT_VALIDO_RESSALVA):
            if it.get("_valor_unitario_num") in discrepantes:
                it["observacao"] = (it.get("observacao", "") + " CANDIDATO a discrepante (IQR) — avaliar exclusão fundamentada (art. 5º, §4º).").strip()
    return itens, outliers  # type: ignore[return-value]


def _precos_para_calculo(itens: list[dict]) -> list[float]:
    """Preços que entram no cálculo: válidos e válidos-com-ressalva (não excluídos)."""
    out = []
    for it in itens:
        if it.get("situacao") in (SIT_VALIDO, SIT_VALIDO_RESSALVA):
            v = it.get("_valor_unitario_num")
            if v is not None:
                out.append(v)
    return out


def _linha_tabela(n: int, it: dict) -> str:
    vu = fmt_brl(it.get("_valor_unitario_num")) if it.get("_valor_unitario_num") is not None else "—"
    vt = fmt_brl(parse_brl(it.get("valor_total"))) if parse_brl(it.get("valor_total")) is not None else "—"
    cols = [
        str(n),
        it.get("fonte", "") or "—",
        it.get("orgao", "") or "—",
        (it.get("objeto_encontrado", "") or "—").replace("|", "/")[:80],
        it.get("modalidade", "") or "—",
        it.get("data", "") or "—",
        str(it.get("quantidade", "") or "—"),
        it.get("unidade", "") or "—",
        vu,
        vt,
        (it.get("link", "") or "—"),
        it.get("comparabilidade", "") or "[VALIDAÇÃO HUMANA]",
        it.get("situacao", "") or "—",
    ]
    return "| " + " | ".join(cols) + " |"


def gerar_relatorio(processo: dict, itens: list[dict], outliers: dict,
                    pncp_meta: Optional[dict], web_meta: Optional[dict]) -> str:
    """Gera o relatório Markdown com os 13 blocos + textos para a minuta."""
    precos = _precos_para_calculo(itens)
    stats = estatisticas(precos)
    objeto = processo.get("objeto", "[PREENCHER: objeto]")
    minuta = processo.get("minuta", "05_minutas/PESQUISA_DE_PRECOS/PESQUISA_PRECOS_MINUTA_MAE.docx")
    L: list[str] = []

    L.append(f"# Pesquisa de Preços — {objeto}")
    L.append(f"_Relatório gerado por cesta_precos.py em {_hoje_iso()}._")
    L.append("")
    L.append("> **Documento de trabalho.** Os cálculos são mecânicos; a redação institucional, "
             "a comparabilidade final e as exclusões são de responsabilidade do agente/Charles "
             "(Lei 14.133/2021, art. 23; Portaria 03/2024). Marcadores `[PREENCHER]` e "
             "`[VALIDAÇÃO HUMANA]` exigem decisão humana.")
    L.append("")

    # 1. Resumo
    L.append("## 1. Resumo da pesquisa realizada")
    L.append(f"- **Objeto:** {objeto}")
    L.append(f"- **Descrição detalhada:** {processo.get('descricao_detalhada', '[PREENCHER]')}")
    L.append(f"- **Unidade / Quantidade:** {processo.get('unidade', '—')} / {processo.get('quantidade', '—')}")
    L.append(f"- **Categoria:** {processo.get('categoria', '—')}")
    L.append(f"- **Período de busca:** {processo.get('periodo_busca', '—')}")
    L.append(f"- **Filtros:** {json.dumps(processo.get('filtros', {}), ensure_ascii=False)}")
    L.append(f"- **Valor estimado inicial (se houver):** {processo.get('valor_estimado_inicial', '—')}")
    L.append(f"- **Fontes coletadas:** {len(itens)} | **Válidas p/ cálculo:** {len(precos)}")
    L.append("")

    # 2. Termos pesquisados
    L.append("## 2. Termos pesquisados")
    if web_meta and web_meta.get("consultas_sugeridas"):
        for c in web_meta["consultas_sugeridas"]:
            L.append(f"- `{c}`")
    else:
        L.append(f"- `{objeto}` (termo principal)")
    L.append("")

    # 3. Fontes PNCP
    L.append("## 3. Fontes PNCP encontradas")
    if pncp_meta:
        L.append(f"- Consulta: {pncp_meta.get('url_consultada', '—')}")
        L.append(f"- Data da consulta: {pncp_meta.get('data_consulta', '—')}")
        if pncp_meta.get("erro"):
            L.append(f"- [ATENÇÃO] {pncp_meta['erro']}")
    pncp_itens = [it for it in itens if it.get("fonte") == "PNCP"]
    L.append(f"- Itens do PNCP na cesta: {len(pncp_itens)}")
    L.append("")

    # 4. Fontes externas
    L.append("## 4. Fontes externas encontradas")
    if web_meta:
        L.append(f"- Provedor de busca: {web_meta.get('provedor', 'none')}")
        if web_meta.get("aviso"):
            L.append(f"- [ATENÇÃO] {web_meta['aviso']}")
        if web_meta.get("links_manuais"):
            L.append("- Links para pesquisa manual (executar e colar no modo manual):")
            for lm in web_meta["links_manuais"]:
                L.append(f"  - {lm['consulta']}: {lm['url']}")
    ext_itens = [it for it in itens if it.get("fonte") not in ("PNCP", "")]
    L.append(f"- Itens externos na cesta: {len(ext_itens)}")
    L.append("")

    # 5. Tabela da cesta
    L.append("## 5. Tabela da cesta de preços")
    L.append("| Nº | Fonte | Órgão | Objeto encontrado | Modalidade | Data | Quantidade | Unidade | Valor unitário | Valor total | Link | Comparabilidade | Situação |")
    L.append("| -- | ----- | ----- | ----------------- | ---------- | ---- | ---------- | ------- | -------------- | ----------- | ---- | --------------- | -------- |")
    if itens:
        for i, it in enumerate(itens, 1):
            L.append(_linha_tabela(i, it))
    else:
        L.append("| — | — | — | _nenhuma fonte coletada_ | — | — | — | — | — | — | — | — | — |")
    L.append("")

    # 6. Análise de comparabilidade
    L.append("## 6. Análise de comparabilidade")
    L.append("[VALIDAÇÃO HUMANA] Confirmar, item a item, a similaridade quanto a: especificação técnica, "
             "unidade de medida, quantidade, localidade, data, modalidade, condições de fornecimento "
             "(frete/instalação/garantia/suporte) e se o preço é unitário ou global "
             "(Portaria 03/2024, art. 3º). Justificar cada exclusão por baixa comparabilidade.")
    L.append("")

    # 7. Tratamento de discrepantes
    L.append("## 7. Tratamento de valores discrepantes")
    L.append(f"- Limites IQR (sobre válidos): inferior {fmt_brl(outliers.get('limite_inferior'))}, "
             f"superior {fmt_brl(outliers.get('limite_superior'))}.")
    L.append(f"- {outliers.get('observacao', '')}")
    if outliers.get("valores_discrepantes"):
        L.append(f"- Candidatos a discrepante: {[fmt_brl(v) for v in outliers['valores_discrepantes']]}")
    L.append("- [VALIDAÇÃO HUMANA] Decidir exclusão de inexequíveis/inconsistentes/excessivos com "
             "critério fundamentado (Portaria 03/2024, art. 5º, §§4º-6º).")
    L.append("")

    # 8. Memória de cálculo
    L.append("## 8. Memória de cálculo")
    L.append(f"- Preços considerados (válidos/ressalva): {[fmt_brl(p) for p in precos]}")
    L.append(f"- **Quantidade de preços (n):** {stats['n']}")
    L.append(f"- **Média:** {fmt_brl(stats['media'])}")
    L.append(f"- **Mediana:** {fmt_brl(stats['mediana'])}")
    L.append(f"- **Menor preço:** {fmt_brl(stats['menor'])}")
    if stats.get("alerta_minimo"):
        L.append(f"- [ATENÇÃO] {stats['alerta_minimo']}")
    qtd = parse_brl(processo.get("quantidade")) or processo.get("quantidade")
    L.append(f"- Quantidade estimada do processo: {processo.get('quantidade', '—')} "
             f"(valor global = unitário escolhido × quantidade) [PREENCHER após escolher o método].")
    L.append("")

    # 9. Valor estimado sugerido
    L.append("## 9. Valor estimado sugerido")
    if stats["n"] >= 3:
        L.append(f"- Sugestão preliminar (a confirmar): **média {fmt_brl(stats['media'])}** por "
                 f"{processo.get('unidade', 'unidade')}.")
    else:
        L.append("- [ATENÇÃO] Menos de 3 preços válidos — **não** fixar valor sem complementar a cesta "
                 "ou justificar (art. 5º, §7º).")
    L.append("- [VALIDAÇÃO HUMANA] Confirmar método (média/mediana/menor) e o valor unitário/global final.")
    L.append("")

    # 10. Justificativa da metodologia
    L.append("## 10. Justificativa da metodologia")
    L.append(sugerir_metodologia(stats, outliers))
    L.append("")

    # 11. Texto para a minuta-mãe
    L.append("## 11. Texto pronto para a minuta-mãe de Pesquisa de Preços")
    L.append(f"**Minuta-mãe:** `{minuta}` (preencher os campos `{{{{...}}}}`; não alterar estrutura/timbre).")
    L.append("")
    L.append("```text")
    L.append(f"{{{{OBJETO}}}} = {objeto}")
    L.append(f"{{{{PERIODO_PESQUISA}}}} = {processo.get('periodo_busca', '[PREENCHER]')}")
    L.append("{{SERIE_PRECOS_COLETADOS}} =")
    for i, it in enumerate(itens, 1):
        vu = fmt_brl(it.get("_valor_unitario_num")) if it.get("_valor_unitario_num") is not None else "[sem valor]"
        L.append(f"  {i}. {it.get('fonte','?')} — {it.get('orgao','?')} — {vu} "
                 f"({it.get('data','s/data')}) — {it.get('link','s/link')} [{it.get('situacao','?')}]")
    L.append("{{JUSTIFICATIVA_METODOLOGIA}} = [PREENCHER: método escolhido e tratamento de valores "
             "inexequíveis/inconsistentes/excessivos, art. 5º, §4º]")
    L.append("{{MEMORIA_CALCULO}} = [PREENCHER: ver bloco 8 — operação que levou ao valor final]")
    L.append("{{JUSTIFICATIVA_FORNECEDORES}} = [PREENCHER apenas se houver pesquisa direta — art. 4º, §2º]")
    L.append("{{VALOR_REFERENCIA}} = [PREENCHER: valor final escolhido] / {{VALOR_REFERENCIA_EXTENSO}} = [PREENCHER]")
    L.append("{{NUMERO_FOLHAS}} = [PREENCHER] / {{NUMERO_FOLHAS_EXTENSO}} = [PREENCHER]")
    L.append("{{DIA}}/{{MES}}/{{ANO}} = [PREENCHER: data da assinatura]")
    L.append("Metodologia (  ) Média (  ) Mediana (  ) Menor Preço (  ) Outra -> {{OUTRA_METODOLOGIA}}")
    L.append("Fontes (art. 23/art. 4º): marcar (  ) as efetivamente utilizadas.")
    L.append("```")
    L.append("")

    # 12. Fontes utilizadas
    L.append("## 12. Fontes utilizadas")
    for i, it in enumerate(itens, 1):
        L.append(f"- [{i}] {it.get('fonte','?')} — {it.get('orgao','?')} — {it.get('link','s/link')} "
                 f"(acesso: {it.get('data_acesso','—')})")
    if not itens:
        L.append("- _Nenhuma fonte coletada._")
    L.append("")

    # 13. Alertas e ressalvas
    L.append("## 13. Alertas e ressalvas")
    L.append("- Priorizar parâmetros dos incisos I e II (PNCP/contratações similares); se não usados, "
             "justificar nos autos (Portaria 03/2024, art. 4º, §1º).")
    if stats["n"] < 3:
        L.append("- **Cesta insuficiente (<3 preços válidos):** ampliar período, rever termos, consultar "
                 "fornecedores (pesquisa direta, art. 4º, IV) ou base interna. Não concluir artificialmente.")
    L.append("- Sítios eletrônicos só valem com data e hora de acesso (art. 4º, III).")
    L.append("- Pesquisa direta exige propostas formais com os dados do art. 4º, §2º (CNPJ/CPF, validade "
             "≥ 90 dias etc.) e registro de quem não respondeu.")
    L.append("- Em dispensa dos incisos I e II do art. 75, a estimativa pode ser concomitante à seleção "
             "(art. 6º, §4º).")
    L.append("- **Este relatório NÃO substitui a análise humana.** Validar antes de juntar ao processo.")
    L.append("")

    return "\n".join(L)


def carregar_json(caminho: str) -> Any:
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Orquestra a pesquisa de preços e gera o relatório.")
    ap.add_argument("--processo", required=True, help="JSON com os dados do processo.")
    ap.add_argument("--manual", help="JSON (lista) com itens coletados manualmente.")
    ap.add_argument("--pncp", action="store_true", help="Consultar o PNCP.")
    ap.add_argument("--web", action="store_true", help="Executar/sugerir busca complementar.")
    ap.add_argument("--saida", help="Arquivo .md de saída. Default: stdout.")
    args = ap.parse_args(argv)

    processo = carregar_json(args.processo)
    itens: list[dict] = []
    pncp_meta: Optional[dict] = None
    web_meta: Optional[dict] = None

    if args.manual:
        manuais = carregar_json(args.manual)
        for m in manuais:
            it = _item_base()
            it.update(m)
            it["fonte"] = it.get("fonte") or "Externa"
            itens.append(it)

    if args.pncp:
        if consultar_pncp is None:
            print("[ATENÇÃO] pncp_consulta indisponível.", file=sys.stderr)
        else:
            pncp_itens, pncp_meta = coletar_pncp(processo)
            itens.extend(pncp_itens)

    if args.web:
        if buscar_web is None:
            print("[ATENÇÃO] busca_web indisponível.", file=sys.stderr)
        else:
            web_meta = buscar_web(processo.get("objeto", ""))
            # Resultados reais (com provedor) entram como itens externos SEM valor —
            # o valor precisa ser confirmado pelo humano (a busca traz link/trecho, não preço seguro).
            for r in web_meta.get("resultados", []):
                it = _item_base()
                it.update({
                    "fonte": "Web", "orgao": "[VALIDAÇÃO HUMANA]",
                    "objeto_encontrado": r.get("titulo", ""), "link": r.get("link", ""),
                    "data_acesso": r.get("data_acesso", ""), "observacao": r.get("trecho", ""),
                    "comparabilidade": r.get("confiabilidade", ""),
                })
                itens.append(it)

    itens, outliers = montar_cesta(itens, processo)
    relatorio = gerar_relatorio(processo, itens, outliers, pncp_meta, web_meta)

    if args.saida:
        with open(args.saida, "w", encoding="utf-8") as f:
            f.write(relatorio)
        print(f"Relatório gravado em {args.saida} ({len(itens)} fonte(s)).")
    else:
        print(relatorio)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
