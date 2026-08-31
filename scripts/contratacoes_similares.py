#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
contratacoes_similares.py — Orquestrador do MODO PESQUISA DE CONTRATAÇÕES SIMILARES.

Localiza, reúne e organiza contratações públicas SEMELHANTES ao objeto que a Câmara
Municipal de Itanhandu pretende contratar, para uso como REFERÊNCIA TÉCNICA e
REDACIONAL (DFD, ETP, TR, requisitos, obrigações, prazos, garantias). NÃO é a
pesquisa formal de preços — para estimar valor, use `cesta_precos.py`.

DIVISÃO DE PAPÉIS (igual à pesquisa de preços):
  - Este script faz a parte MECÂNICA: gera palavras-chave, consulta o PNCP
    (várias palavras-chave, independente da modalidade), prepara/roda a busca web,
    junta e deduplica resultados, sugere uma relevância PRELIMINAR por sobreposição
    de termos, monta a fila de documentos para leitura e escreve o relatório inicial.
  - O JUÍZO (ler os documentos, confirmar relevância, extrair requisitos, separar
    referência técnica de regra local, adaptar para Itanhandu) é do Charles/servidor.
  - NADA é inventado: sem provedor de busca, apenas consultas/links manuais; sem
    documento aberto, a evidência é "indício"/"parcial", nunca "confirmada".

ENTRADA (ficha JSON da demanda) — ver scripts/exemplos/demanda-exemplo.json:
  {
    "objeto": "...", "necessidade": "...", "finalidade": "...",
    "quantidade": "...", "unidade": "...", "prazo": "...",
    "setor_requisitante": "...", "continuada": false, "urgencia": false,
    "palavras_chave": ["...", "..."], "sinonimos": ["..."],
    "filtros": {"uf": "MG", "municipio": "...", "data_inicial": "AAAA-MM-DD",
                "data_final": "AAAA-MM-DD"},
    "max_por_termo": 10, "max_total": 30, "processo_nome": "..."
  }

Itens MANUAIS (JSON, lista) — referências já coletadas pelo humano:
  [{"orgao": "...", "municipio": "...", "uf": "...", "modalidade": "...",
    "objeto_encontrado": "...", "numero_contratacao": "...", "link": "...",
    "documentos_lidos": ["TR", "edital"], "relevancia": "alta",
    "evidencia": "confirmada", "data_acesso": "AAAA-MM-DD", "observacao": "..."}]

Uso:
  # Coleta automática (PNCP multi + plano de busca web) e gera o relatório:
  python contratacoes_similares.py --demanda demanda.json --pncp --web --saida-dir saida/

  # Só o plano/relatório (sem rede), com itens manuais:
  python contratacoes_similares.py --demanda demanda.json --manual manual.json --saida relatorio.md
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

try:
    from pncp_consulta import consultar_pncp_multi
except Exception:  # noqa: BLE001 — PNCP é opcional
    consultar_pncp_multi = None
try:
    from busca_web import buscar_web, gerar_consultas
except Exception:  # noqa: BLE001 — web é opcional
    buscar_web = None
    gerar_consultas = None


VALIDACAO = "[VALIDAÇÃO HUMANA]"

# Documentos técnicos que devem ser procurados em cada processo (para a fila de leitura).
DOCUMENTOS_PROCURADOS = [
    "DFD", "ETP", "Termo de Referência", "projeto básico", "edital",
    "aviso de contratação direta", "mapa de riscos", "pesquisa de preços",
    "proposta vencedora", "ata de julgamento", "termo de homologação",
    "contrato", "ata de registro de preços", "nota de empenho",
]

# Sufixos usados para variar a busca por objeto (documentos técnicos + modalidades).
SUFIXOS_DOCUMENTAIS = [
    "", "termo de referência", "estudo técnico preliminar",
    "documento de formalização da demanda", "projeto básico", "edital",
    "contrato", "ata de registro de preços",
]

_STOPWORDS = {
    "de", "da", "do", "das", "dos", "e", "para", "com", "sem", "por", "a", "o",
    "as", "os", "um", "uma", "em", "no", "na", "aquisicao", "aquisicao", "compra",
    "contratacao", "servico", "servicos", "fornecimento",
}


def _agora_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _sem_acento(texto: str) -> str:
    norm = unicodedata.normalize("NFKD", str(texto or ""))
    return "".join(c for c in norm if not unicodedata.combining(c))


def _tokens(texto: str) -> set[str]:
    """Tokens significativos (minúsculos, sem acento, sem stopword, >= 3 letras)."""
    limpo = _sem_acento(texto).lower()
    brutos = re.split(r"[^a-z0-9]+", limpo)
    return {t for t in brutos if len(t) >= 3 and t not in _STOPWORDS}


def gerar_palavras_chave(demanda: dict) -> list[str]:
    """Palavras-chave nucleares para a consulta ao PNCP (objeto + sinônimos + termos).

    Mantém a ordem de prioridade (objeto primeiro) e deduplica preservando ordem.
    Não inventa termos: usa apenas o que está na ficha da demanda.
    """
    candidatos: list[str] = []
    objeto = str(demanda.get("objeto", "")).strip()
    if objeto:
        candidatos.append(objeto)
    for chave in ("palavras_chave", "sinonimos"):
        for termo in demanda.get(chave, []) or []:
            termo = str(termo).strip()
            if termo:
                candidatos.append(termo)
    vistos: set[str] = set()
    ordenados: list[str] = []
    for termo in candidatos:
        chave = _sem_acento(termo).lower()
        if chave and chave not in vistos:
            vistos.add(chave)
            ordenados.append(termo)
    return ordenados


def gerar_consultas_web_plano(demanda: dict) -> list[str]:
    """Consultas sugeridas para busca web manual (objeto + sinônimos × documentos).

    Serve como plano de pesquisa quando não há provedor de busca. Reaproveita os
    modelos de busca_web (modo similares) para o objeto principal e acrescenta
    variações por sinônimo.
    """
    consultas: list[str] = []
    if gerar_consultas is not None and demanda.get("objeto"):
        consultas.extend(gerar_consultas(str(demanda["objeto"]), modo="similares"))
    for sin in demanda.get("sinonimos", []) or []:
        sin = str(sin).strip()
        for suf in SUFIXOS_DOCUMENTAIS:
            consulta = f"{sin} {suf}".strip()
            if consulta:
                consultas.append(consulta)
    # dedup preservando ordem
    vistos: set[str] = set()
    saida: list[str] = []
    for c in consultas:
        if c not in vistos:
            vistos.add(c)
            saida.append(c)
    return saida


def _ref_base() -> dict:
    return {
        "origem": "",  # PNCP | Web | Manual
        "orgao": "", "unidade": "", "municipio": "", "uf": "",
        "numero_contratacao": "", "modalidade": "", "data": "",
        "objeto_encontrado": "", "quantidade": "", "unidade_medida": "",
        "valor_total": "", "valor_unitario": "", "link": "",
        "termo_origem": "", "data_acesso": "",
        "documentos_lidos": [],
        "relevancia": VALIDACAO,
        "relevancia_sugerida": "",
        "score_termos": 0.0,
        "evidencia": "",
        "status_link": "",
        "observacao": "",
    }


def _score_termos(objeto: str, objeto_encontrado: str) -> float:
    """Sobreposição de tokens (Jaccard) entre o objeto da demanda e o encontrado.

    Heurística MECÂNICA apenas para ordenar/sinalizar — não decide relevância.
    """
    a = _tokens(objeto)
    b = _tokens(objeto_encontrado)
    if not a or not b:
        return 0.0
    inter = len(a & b)
    uniao = len(a | b)
    return round(inter / uniao, 3) if uniao else 0.0


def _relevancia_sugerida(score: float, tem_link: bool) -> str:
    """Sugestão preliminar (SEMPRE confirmar). Baseada só em sobreposição de termos."""
    if score >= 0.5:
        base = "alta (sugerida)"
    elif score >= 0.25:
        base = "média (sugerida)"
    elif score > 0:
        base = "baixa (sugerida)"
    else:
        base = "a avaliar"
    if not tem_link:
        base += " — sem link"
    return base


def normalizar_pncp(item: dict, objeto: str, data_consulta: str) -> dict:
    ref = _ref_base()
    link = item.get("link", "")
    score = _score_termos(objeto, item.get("objeto_encontrado", ""))
    ref.update({
        "origem": "PNCP",
        "orgao": item.get("orgao", ""),
        "unidade": item.get("unidade", ""),
        "municipio": item.get("municipio", ""),
        "uf": item.get("uf", ""),
        "numero_contratacao": item.get("numero_contratacao", ""),
        "modalidade": item.get("modalidade", ""),  # metadado; não filtra
        "data": item.get("data", ""),
        "objeto_encontrado": item.get("objeto_encontrado", ""),
        "quantidade": item.get("quantidade", ""),
        "unidade_medida": item.get("unidade_medida", ""),
        "valor_total": item.get("valor_total", ""),
        "valor_unitario": item.get("valor_unitario", ""),
        "link": link,
        "termo_origem": item.get("termo_origem", ""),
        "data_acesso": data_consulta,
        "score_termos": score,
        "relevancia_sugerida": _relevancia_sugerida(score, bool(link)),
        # Página do processo localizada, mas documentos ainda não abertos/lidos:
        "evidencia": "parcial" if link else "indicio",
        "status_link": "a_verificar" if link else "sem_link",
        "observacao": "Origem PNCP — abrir a página e ler os documentos antes de usar como referência.",
    })
    return ref


def normalizar_web(item: dict, objeto: str) -> dict:
    ref = _ref_base()
    link = item.get("link", "")
    score = _score_termos(objeto, item.get("titulo", ""))
    ref.update({
        "origem": "Web",
        "objeto_encontrado": item.get("titulo", ""),
        "link": link,
        "termo_origem": item.get("consulta_origem", ""),
        "data_acesso": item.get("data_acesso", ""),
        "score_termos": score,
        "relevancia_sugerida": _relevancia_sugerida(score, bool(link)),
        "evidencia": "indicio",  # resultado de buscador: descoberta, não prova
        "status_link": "a_verificar" if link else "sem_link",
        "observacao": ("Confiabilidade do domínio: " + str(item.get("confiabilidade", "?"))
                       + ". Indício de buscador — confirmar na fonte oficial.").strip(),
    })
    return ref


def normalizar_manual(item: dict, objeto: str) -> dict:
    ref = _ref_base()
    ref.update({k: v for k, v in item.items() if k in ref})
    ref["origem"] = "Manual"
    if not ref.get("score_termos"):
        ref["score_termos"] = _score_termos(objeto, ref.get("objeto_encontrado", ""))
    ref["relevancia"] = item.get("relevancia", VALIDACAO)
    ref["evidencia"] = item.get("evidencia", "") or VALIDACAO
    docs = item.get("documentos_lidos") or []
    ref["documentos_lidos"] = list(docs) if isinstance(docs, list) else [str(docs)]
    if not ref.get("relevancia_sugerida"):
        ref["relevancia_sugerida"] = _relevancia_sugerida(ref["score_termos"], bool(ref.get("link")))
    return ref


def _chave_dedupe(ref: dict) -> str:
    numero = str(ref.get("numero_contratacao", "")).strip()
    if numero:
        return f"num:{numero}"
    link = str(ref.get("link", "")).strip()
    if link:
        return f"link:{link}"
    return "of:" + (str(ref.get("orgao", "")) + "|" + str(ref.get("objeto_encontrado", ""))).strip().lower()


def deduplicar(refs: list[dict]) -> list[dict]:
    """Remove duplicatas por número/link/órgão+objeto, preservando a 1ª ocorrência."""
    vistos: set[str] = set()
    saida: list[dict] = []
    for ref in refs:
        chave = _chave_dedupe(ref)
        if chave in vistos:
            continue
        vistos.add(chave)
        saida.append(ref)
    return saida


def montar_fila_leitura(refs: list[dict]) -> list[dict]:
    """Fila de documentos a baixar/ler, por referência com página localizada."""
    fila = []
    for i, ref in enumerate(refs, 1):
        if not ref.get("link"):
            continue
        fila.append({
            "referencia": i,
            "orgao": ref.get("orgao", "") or VALIDACAO,
            "objeto_encontrado": ref.get("objeto_encontrado", ""),
            "link": ref.get("link", ""),
            "documentos_esperados": DOCUMENTOS_PROCURADOS,
            "documentos_lidos": ref.get("documentos_lidos", []),
            "status": "a_baixar",
        })
    return fila


def coletar_pncp(demanda: dict, palavras: list[str]) -> tuple[list[dict], dict]:
    if consultar_pncp_multi is None:
        return [], {"erro": "pncp_consulta indisponível.", "itens": []}
    filtros = demanda.get("filtros", {}) or {}
    res = consultar_pncp_multi(
        palavras,
        data_inicial=filtros.get("data_inicial"),
        data_final=filtros.get("data_final"),
        uf=filtros.get("uf"),
        municipio=filtros.get("municipio"),
        modalidade=filtros.get("modalidade"),  # normalmente None: modalidade não filtra
        max_por_termo=int(demanda.get("max_por_termo", 10)),
        max_total=int(demanda.get("max_total", 30)),
    )
    objeto = str(demanda.get("objeto", ""))
    refs = [normalizar_pncp(it, objeto, res.get("data_consulta", "")) for it in res.get("itens", [])]
    return refs, res


def coletar_web(demanda: dict) -> tuple[list[dict], dict]:
    if buscar_web is None:
        return [], {"erro": "busca_web indisponível.", "resultados": []}
    objeto = str(demanda.get("objeto", ""))
    meta = buscar_web(objeto, modo="similares")
    refs = [normalizar_web(r, objeto) for r in meta.get("resultados", [])]
    return refs, meta


# --------------------------------------------------------------------------- #
# Relatório                                                                    #
# --------------------------------------------------------------------------- #

def _tab_linha(cols: list[Any]) -> str:
    return "| " + " | ".join(str(c).replace("|", "/") if c not in (None, "") else "—" for c in cols) + " |"


def gerar_relatorio(demanda: dict, refs: list[dict], fila: list[dict],
                    palavras: list[str], consultas_web: list[str],
                    pncp_meta: Optional[dict], web_meta: Optional[dict],
                    erros: list[str]) -> str:
    objeto = demanda.get("objeto", "[PREENCHER: objeto]")
    L: list[str] = []

    L.append(f"# Relatório de Pesquisa de Contratações Similares — {objeto}")
    L.append(f"_Relatório gerado por contratacoes_similares.py em {_agora_iso()}._")
    L.append("")
    L.append("> **Documento de trabalho — referência técnica, NÃO pesquisa formal de preços.** "
             "A coleta é mecânica; a leitura dos documentos, a confirmação de relevância, a "
             "extração de requisitos e a adaptação para a Câmara são do Charles/servidor. "
             "Marcadores `[VALIDAÇÃO HUMANA]` exigem decisão humana. Valores aqui são apenas "
             "contexto — para estimar o valor, use a Pesquisa de Preços (`cesta_precos.py`).")
    L.append("")

    # 1. Demanda
    L.append("## 1. Demanda da Câmara")
    L.append(f"- **Órgão:** Câmara Municipal de Itanhandu/MG")
    L.append(f"- **Setor requisitante:** {demanda.get('setor_requisitante', '[A preencher pela Câmara]')}")
    L.append(f"- **Objeto pretendido:** {objeto}")
    L.append(f"- **Necessidade administrativa:** {demanda.get('necessidade', '[A preencher pela Câmara]')}")
    L.append(f"- **Finalidade pública:** {demanda.get('finalidade', '[A preencher pela Câmara]')}")
    L.append(f"- **Quantidade / Unidade:** {demanda.get('quantidade', '—')} / {demanda.get('unidade', '—')}")
    L.append(f"- **Prazo desejado:** {demanda.get('prazo', '[A preencher pela Câmara]')}")
    L.append(f"- **Continuada:** {demanda.get('continuada', '[A preencher]')} | "
             f"**Urgência:** {demanda.get('urgencia', '[A preencher]')}")
    L.append("")

    # 2. Estratégia de pesquisa
    L.append("## 2. Estratégia de pesquisa")
    L.append("- PNCP por várias palavras-chave, **independente da modalidade** (a modalidade é "
             "registrada como metadado, não como filtro de exclusão).")
    L.append("- Busca web (modo similares) priorizando domínios oficiais (`.gov.br`, `.leg.br`, "
             "`.jus.br`) e documentos técnicos (DFD, ETP, TR, projeto básico, edital, contrato).")
    L.append("- Camadas: objeto exato → sinônimos → solução → finalidade → ampliação geográfica/temporal.")
    L.append("")

    # 3. Palavras-chave e consultas
    L.append("## 3. Palavras-chave utilizadas")
    L.append("**Termos nucleares (PNCP):**")
    for p in palavras:
        L.append(f"- `{p}`")
    L.append("")
    L.append("**Consultas web sugeridas (executar manualmente se não houver provedor):**")
    for c in consultas_web:
        L.append(f"- `{c}`")
    L.append("")

    # 4. Fontes consultadas / erros
    L.append("## 4. Fontes consultadas")
    if pncp_meta:
        L.append(f"- **PNCP:** {len(pncp_meta.get('itens', []))} contratação(ões) após deduplicação; "
                 f"termos: {', '.join(pncp_meta.get('termos_pesquisados', [])) or '—'}.")
        if pncp_meta.get("erro"):
            L.append(f"  - [ATENÇÃO] {pncp_meta['erro']}")
    else:
        L.append("- **PNCP:** não consultado nesta execução.")
    if web_meta:
        L.append(f"- **Web:** provedor = {web_meta.get('provedor', 'none')}; "
                 f"resultados = {len(web_meta.get('resultados', []))}.")
        if web_meta.get("aviso"):
            L.append(f"  - [ATENÇÃO] {web_meta['aviso']}")
        for lm in web_meta.get("links_manuais", []) or []:
            L.append(f"  - manual: {lm['consulta']} — {lm['url']}")
    else:
        L.append("- **Web:** não consultada nesta execução.")
    for e in erros:
        L.append(f"- [ERRO] {e}")
    L.append("")

    # 5. Contratações localizadas
    L.append("## 5. Contratações localizadas")
    L.append("| Nº | Origem | Órgão | Município/UF | Modalidade | Objeto encontrado | Data | Nº controle | Score termos | Relevância (sugerida) | Evidência | Link |")
    L.append("| -- | ------ | ----- | ------------ | ---------- | ----------------- | ---- | ----------- | -----------: | --------------------- | --------- | ---- |")
    if refs:
        for i, r in enumerate(refs, 1):
            L.append(_tab_linha([
                i, r.get("origem"), r.get("orgao"),
                f"{r.get('municipio','')}/{r.get('uf','')}".strip("/"),
                r.get("modalidade"),
                (r.get("objeto_encontrado", "") or "")[:80],
                r.get("data"), r.get("numero_contratacao"),
                r.get("score_termos"), r.get("relevancia_sugerida"),
                r.get("evidencia"), r.get("link"),
            ]))
    else:
        L.append("| — | — | — | — | — | _nenhuma contratação localizada_ | — | — | — | — | — | — |")
    L.append("")
    L.append("> A coluna **Relevância (sugerida)** é heurística (sobreposição de termos). "
             "A relevância real (alta/média/baixa/descartada) só se confirma após **ler os "
             "documentos** — ver §6.")
    L.append("")

    # 6. Fila de documentos para leitura
    L.append("## 6. Documentos a baixar e ler (fila)")
    if fila:
        L.append("Para cada referência com página localizada, procurar/baixar e LER: "
                 + ", ".join(DOCUMENTOS_PROCURADOS) + ".")
        L.append("")
        L.append("| Ref. | Órgão | Link | Documentos já lidos | Status |")
        L.append("| ---- | ----- | ---- | ------------------- | ------ |")
        for f in fila:
            L.append(_tab_linha([
                f["referencia"], f["orgao"], f["link"],
                ", ".join(f["documentos_lidos"]) or "—", f["status"],
            ]))
    else:
        L.append("- _Nenhuma referência com link para baixar documentos nesta execução._")
    L.append("")
    L.append("> **Não afirmar que leu documento não aberto.** PDF digitalizado sem texto: registrar "
             "`DOCUMENTO DIGITALIZADO — depende de OCR/conferência manual`. Página inacessível: "
             "registrar endereço, data e tipo de erro.")
    L.append("")

    # 7. Suficiência
    L.append("## 7. Suficiência da pesquisa")
    com_link = sum(1 for r in refs if r.get("link"))
    L.append(f"- Contratações localizadas: **{len(refs)}** | com página/link: **{com_link}**.")
    L.append("- Meta: ≥5 relevantes, idealmente 8–15; ≥3 com documentos técnicos efetivamente lidos.")
    if len(refs) < 5 or com_link < 3:
        L.append("- [ATENÇÃO] **Pesquisa possivelmente insuficiente.** Ampliar palavras-chave, "
                 "sinônimos, período e abrangência geográfica antes de concluir. Não preencher "
                 "quantidade mínima com resultados irrelevantes.")
        L.append("- Frase padrão, se persistir: _\"A pesquisa não localizou quantidade suficiente de "
                 "contratações com documentos técnicos acessíveis. Os resultados encontrados foram "
                 "apresentados, mas não permitem afirmar que representam um padrão consolidado de "
                 "contratação.\"_")
    L.append("")

    # 8-10. Blocos de extração/aplicação (dependem da leitura humana)
    L.append("## 8. Extração técnica (preencher após leitura)")
    L.append("Para cada referência lida, registrar em `05_fichas_de_leitura/`: objeto, necessidade, "
             "solução, especificações, requisitos, obrigações, prazos, garantia, critérios de "
             "aceitação, habilitação/qualificação, valores (contexto), documentos lidos e links. "
             "Campo sem informação no documento: `Não identificado no documento analisado`.")
    L.append("")
    L.append("## 9. Aplicação à Câmara de Itanhandu (preencher após leitura)")
    L.append("- **Pode servir de referência:** descrição do objeto, requisitos técnicos, modelo de "
             "execução, obrigações, prazo, garantia, critérios de aceitação.")
    L.append("- **NÃO copiar automaticamente:** fundamento jurídico/modalidade do outro órgão, rito "
             "procedimental, autoridade competente, regras de regulamento interno alheio, exigências "
             "de plataforma, limites financeiros, competências administrativas.")
    L.append(f"- Sugestões de objeto/solução/requisitos: usar `08_.../aplicacao_itanhandu/` e marcar "
             f"`SUGESTÃO ADICIONAL — depende de avaliação da Câmara`. Ao gerar documento, usar "
             f"**exclusivamente** as minutas de `05_minutas/`.")
    L.append("")

    # 11. Validação humana
    L.append("## 10. Validação humana obrigatória")
    for item in [
        "os links abrem e os documentos pertencem ao processo indicado;",
        "os trechos foram extraídos corretamente e a modalidade foi registrada certa;",
        "não houve importação de regra local de outro órgão como se fosse obrigação da Câmara;",
        "as referências estão atuais e os valores foram tratados apenas como contexto;",
        "a relevância sugerida foi confirmada após a leitura;",
        "a minuta oficial foi preservada e os campos pendentes identificados.",
    ]:
        L.append(f"- [ ] {item}")
    L.append("")
    L.append("> Esta pesquisa é **apoio ao Agente de Contratação**. Não substitui o setor "
             "requisitante, a autoridade competente, a contabilidade nem a assessoria jurídica.")
    L.append("")

    return "\n".join(L)


# --------------------------------------------------------------------------- #
# Execução                                                                     #
# --------------------------------------------------------------------------- #

def carregar_json(caminho: str) -> Any:
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)


def _nome_processo(demanda: dict) -> str:
    nome = str(demanda.get("processo_nome") or demanda.get("objeto") or "pesquisa").strip()
    slug = re.sub(r"[^a-z0-9]+", "-", _sem_acento(nome).lower()).strip("-")
    return slug[:60] or "pesquisa"


def escrever_saida_dir(base: Path, demanda: dict, refs: list[dict], fila: list[dict],
                       relatorio: str, pncp_meta: Optional[dict], web_meta: Optional[dict],
                       manual: Optional[list]) -> Path:
    """Cria a estrutura de pastas da pesquisa e grava os artefatos brutos + relatório."""
    raiz = base / "pesquisa_contratacoes_similares"
    (raiz / "03_resultados_brutos").mkdir(parents=True, exist_ok=True)
    (raiz / "04_documentos_originais").mkdir(parents=True, exist_ok=True)
    (raiz / "05_fichas_de_leitura").mkdir(parents=True, exist_ok=True)
    (raiz / "06_quadros_comparativos").mkdir(parents=True, exist_ok=True)
    (raiz / "07_relatorio").mkdir(parents=True, exist_ok=True)
    (raiz / "08_aplicacao_itanhandu").mkdir(parents=True, exist_ok=True)

    (raiz / "01_ficha_demanda.md").write_text(
        "# Ficha da Demanda\n\n```json\n"
        + json.dumps(demanda, ensure_ascii=False, indent=2) + "\n```\n",
        encoding="utf-8",
    )
    if pncp_meta is not None:
        (raiz / "03_resultados_brutos" / "pncp.json").write_text(
            json.dumps(pncp_meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if web_meta is not None:
        (raiz / "03_resultados_brutos" / "web.json").write_text(
            json.dumps(web_meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if manual is not None:
        (raiz / "03_resultados_brutos" / "manual.json").write_text(
            json.dumps(manual, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (raiz / "03_resultados_brutos" / "referencias.json").write_text(
        json.dumps(refs, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (raiz / "03_resultados_brutos" / "fila_leitura.json").write_text(
        json.dumps(fila, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (raiz / "07_relatorio" / "relatorio_contratacoes_similares.md").write_text(
        relatorio, encoding="utf-8")
    return raiz


def pesquisar(demanda: dict, *, usar_pncp: bool, usar_web: bool,
              manual: Optional[list] = None) -> dict:
    """Executa a pesquisa e devolve o pacote completo (refs, metas, relatório)."""
    palavras = gerar_palavras_chave(demanda)
    consultas_web = gerar_consultas_web_plano(demanda)
    refs: list[dict] = []
    pncp_meta: Optional[dict] = None
    web_meta: Optional[dict] = None
    erros: list[str] = []

    objeto = str(demanda.get("objeto", ""))
    if manual:
        refs.extend(normalizar_manual(m, objeto) for m in manual)
    if usar_pncp:
        if consultar_pncp_multi is None:
            erros.append("pncp_consulta indisponível.")
        else:
            pncp_refs, pncp_meta = coletar_pncp(demanda, palavras)
            refs.extend(pncp_refs)
    if usar_web:
        if buscar_web is None:
            erros.append("busca_web indisponível.")
        else:
            web_refs, web_meta = coletar_web(demanda)
            refs.extend(web_refs)

    refs = deduplicar(refs)
    # Ordena por score de termos (desc), mantendo estabilidade — só triagem.
    refs.sort(key=lambda r: r.get("score_termos", 0.0), reverse=True)
    fila = montar_fila_leitura(refs)
    relatorio = gerar_relatorio(demanda, refs, fila, palavras, consultas_web,
                                pncp_meta, web_meta, erros)
    return {
        "palavras_chave": palavras,
        "consultas_web": consultas_web,
        "referencias": refs,
        "fila_leitura": fila,
        "pncp_meta": pncp_meta,
        "web_meta": web_meta,
        "erros": erros,
        "relatorio": relatorio,
    }


def main(argv: Optional[list[str]] = None) -> int:
    # Console Windows (cp1252) não imprime alguns caracteres (ex.: "→"); força UTF-8.
    for _fluxo in (sys.stdout, sys.stderr):
        try:
            _fluxo.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except Exception:  # noqa: BLE001
            pass
    ap = argparse.ArgumentParser(
        description="Pesquisa de contratações similares (referência técnica; NÃO pesquisa de preços).")
    ap.add_argument("--demanda", required=True, help="JSON com a ficha da demanda.")
    ap.add_argument("--manual", help="JSON (lista) com referências já coletadas.")
    ap.add_argument("--pncp", action="store_true", help="Consultar o PNCP (multi palavra-chave).")
    ap.add_argument("--web", action="store_true", help="Executar/sugerir busca web (modo similares).")
    ap.add_argument("--saida", help="Arquivo .md do relatório. Default: stdout.")
    ap.add_argument("--saida-dir", help="Pasta-base para gravar a estrutura completa da pesquisa.")
    args = ap.parse_args(argv)

    demanda = carregar_json(args.demanda)
    manual = carregar_json(args.manual) if args.manual else None

    pacote = pesquisar(demanda, usar_pncp=args.pncp, usar_web=args.web, manual=manual)
    relatorio = pacote["relatorio"]

    if args.saida_dir:
        base = Path(args.saida_dir)
        if base.name != _nome_processo(demanda):
            base = base / _nome_processo(demanda)
        raiz = escrever_saida_dir(base, demanda, pacote["referencias"], pacote["fila_leitura"],
                                  relatorio, pacote["pncp_meta"], pacote["web_meta"], manual)
        print(f"Pesquisa gravada em {raiz} ({len(pacote['referencias'])} referência(s)).")
    if args.saida:
        Path(args.saida).write_text(relatorio, encoding="utf-8")
        print(f"Relatório gravado em {args.saida}.")
    if not args.saida and not args.saida_dir:
        print(relatorio)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
