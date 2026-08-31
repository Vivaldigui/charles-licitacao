"""Triagem mecânica e metadados conservadores dos julgados."""
from __future__ import annotations

import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import NOT_IDENTIFIED, THEME_KEYWORDS
from .extractors import ExtractionResult, PageText

DIRECT_TERMS = (
    "contratação direta",
    "contratacao direta",
    "dispensa de licitação",
    "dispensa de licitacao",
    "inexigibilidade de licitação",
    "inexigibilidade de licitacao",
)


def repair_mojibake(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    current = value
    for _ in range(2):
        if not any(marker in current for marker in ("Ã", "Â", "â€", "ðŸ")):
            break
        try:
            repaired = current.encode("latin1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            break
        if repaired == current:
            break
        current = repaired
    return current


def normalize_for_search(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    no_marks = "".join(char for char in decomposed if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", no_marks).strip()


def normalize_process_number(value: Any) -> str:
    if value is None:
        return ""
    digits = re.sub(r"\D", "", str(value))
    return digits.lstrip("0") or ("0" if digits else "")


def _date_iso(value: Any) -> str:
    if not value:
        return ""
    text = str(repair_mojibake(value)).strip()
    for fmt in ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    return ""


def _first_match(patterns: tuple[str, ...], text: str, flags: int = re.IGNORECASE) -> str:
    for pattern in patterns:
        match = re.search(pattern, text, flags)
        if match:
            return re.sub(r"\s+", " ", match.group(1)).strip(" .;:-")
    return ""


def _process_from_path(path: Path) -> str:
    match = re.search(r"(?i)processo[_\s-]*(\d{5,12})", path.stem)
    return normalize_process_number(match.group(1)) if match else ""


def _page_numbers_for_terms(pages: list[PageText], terms: tuple[str, ...]) -> list[int]:
    normalized_terms = sorted({normalize_for_search(term) for term in terms})
    result: list[int] = []
    for page in pages:
        normalized = normalize_for_search(page.text)
        if any(term in normalized for term in normalized_terms):
            result.append(page.number)
    return result


def _count_terms(pages: list[PageText], terms: tuple[str, ...]) -> int:
    text = normalize_for_search("\n".join(page.text for page in pages))
    normalized_terms = {normalize_for_search(term) for term in terms}
    return sum(text.count(term) for term in normalized_terms)


def identify_regime(text: str) -> str:
    normalized = normalize_for_search(text)
    count_14133 = len(re.findall(r"lei\s*(?:n[ºo.]*)?\s*14[.]?133", normalized))
    count_8666 = len(re.findall(r"lei\s*(?:n[ºo.]*)?\s*8[.]?666", normalized))
    if count_14133 and count_8666:
        if count_14133 >= count_8666 * 2:
            return "lei-14133"
        if count_8666 >= count_14133 * 2:
            return "lei-8666"
        return "transicao"
    if count_14133:
        return "lei-14133"
    if count_8666:
        return "lei-8666"
    return "nao-identificado"


def identify_contract_type(text: str) -> str:
    normalized = normalize_for_search(text)
    checks = (
        ("dispensa emergencial", ("dispensa emergencial", "situacao de emergencia", "emergencia ou calamidade")),
        ("dispensa deserta ou fracassada", ("licitacao deserta", "licitacao fracassada", "certame deserto")),
        ("dispensa por valor", ("dispensa em razao do valor", "dispensa por valor", "art. 75, i", "art. 75, ii")),
        ("credenciamento", ("credenciamento",)),
        ("contratacao de remanescente", ("remanescente de obra", "remanescente de servico")),
        ("inexigibilidade", ("inexigibilidade", "inviabilidade de competicao")),
    )
    for label, terms in checks:
        if any(term in normalized for term in terms):
            return label
    if "dispensa" in normalized:
        return "outra"
    return "nao-identificada"


def extract_legal_articles(text: str) -> list[str]:
    patterns = (
        r"(?i)art\.?\s*\d+[A-Za-zº°-]*(?:\s*,\s*(?:§+\s*\d+[º°]?|inciso\s+[IVXLCDM]+))?",
        r"(?i)lei\s*(?:n[ºo.]*)?\s*\d{1,2}(?:\.\d{3})?/\d{2,4}",
    )
    found: set[str] = set()
    for pattern in patterns:
        for match in re.findall(pattern, text):
            found.add(re.sub(r"\s+", " ", match).strip())
    return sorted(found, key=normalize_for_search)[:100]


def extract_cited_cases(text: str, own_process: str) -> list[str]:
    candidates = re.findall(r"(?i)(?:processo|consulta|denúncia|recurso)\s*(?:n[ºo.]*)?\s*(\d{5,12})", text)
    normalized = {normalize_process_number(item) for item in candidates}
    normalized.discard(own_process)
    normalized.discard("")
    return sorted(normalized)[:100]


def classify_relevance(pages: list[PageText], index_meta: dict[str, Any], status: str) -> tuple[str, float, str]:
    if status in {"falha", "ocr_necessario", "ocr_indisponivel", "falha_ocr", "formato_nao_suportado"}:
        return "pendente_revisao", 0.0, "Extração insuficiente para classificar."
    count = _count_terms(pages, DIRECT_TERMS)
    term_pages = _page_numbers_for_terms(pages, DIRECT_TERMS)
    ementa = normalize_for_search(str(index_meta.get("ementa") or ""))
    ementa_hit = any(normalize_for_search(term) in ementa for term in DIRECT_TERMS)
    first_pages = normalize_for_search("\n".join(page.text for page in pages[:2]))
    first_hit = any(normalize_for_search(term) in first_pages for term in DIRECT_TERMS)
    if ementa_hit or (count >= 3 and len(term_pages) >= 2) or (count >= 2 and first_hit):
        score = min(1.0, 0.65 + min(count, 10) * 0.03 + (0.08 if ementa_hit else 0.0))
        return "direta", score, "Tema na ementa/cabeçalho ou desenvolvido em múltiplas ocorrências."
    if count >= 2 or (count == 1 and first_hit):
        return "parcial", 0.55, "Tema presente com desenvolvimento limitado; exige revisão humana."
    if count == 1:
        return "incidental", 0.35, "Uma menção localizada sem desenvolvimento mecânico identificado."
    return "falso_positivo", 0.15, "Expressões centrais não localizadas no texto extraído."


def extract_themes(pages: list[PageText]) -> list[dict[str, Any]]:
    themes: list[dict[str, Any]] = []
    normalized_pages = [(page, normalize_for_search(page.text)) for page in pages]
    for theme, keywords in THEME_KEYWORDS.items():
        normalized_keywords = {normalize_for_search(keyword) for keyword in keywords}
        page_numbers = [
            page.number
            for page, normalized_text in normalized_pages
            if any(keyword in normalized_text for keyword in normalized_keywords)
        ]
        if not page_numbers:
            continue
        evidence_page = next(page for page in pages if page.number == page_numbers[0])
        snippet = excerpt_around_terms(evidence_page.text, keywords)
        themes.append(
            {
                "theme": theme,
                "pages": page_numbers,
                "evidence_page": page_numbers[0],
                "evidence": snippet,
                "confidence": "media" if len(page_numbers) == 1 else "alta",
            }
        )
    return themes


def excerpt_around_terms(text: str, terms: tuple[str, ...], radius: int = 280) -> str:
    normalized = normalize_for_search(text)
    positions = [normalized.find(normalize_for_search(term)) for term in terms]
    positions = [pos for pos in positions if pos >= 0]
    if not positions:
        return re.sub(r"\s+", " ", text).strip()[: radius * 2]
    # Índice normalizado é aproximação suficiente para a janela; não altera a evidência armazenada.
    position = min(positions)
    clean = re.sub(r"\s+", " ", text).strip()
    start = max(0, position - radius)
    end = min(len(clean), position + radius)
    prefix = "…" if start else ""
    suffix = "…" if end < len(clean) else ""
    return prefix + clean[start:end].strip() + suffix


def select_relevant_excerpts(pages: list[PageText], limit: int = 3) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for page in pages:
        normalized = normalize_for_search(page.text)
        matching = tuple(term for term in DIRECT_TERMS if normalize_for_search(term) in normalized)
        if matching:
            selected.append({"page": page.number, "text": excerpt_around_terms(page.text, matching)})
        if len(selected) >= limit:
            break
    return selected


def extract_official_summary(first_page: str) -> str:
    """Extrai a ementa oficial da página 1, sem convertê-la em conclusão do Charles."""
    body_match = re.search(
        r"(?im)^\s*(?:TRIBUNAL PLENO|PRIMEIRA CÂMARA|SEGUNDA CÂMARA)\s*[–-]\s*\d{1,2}/\d{1,2}/\d{4}\s*$",
        first_page,
    )
    if not body_match:
        return ""
    tail = first_page[body_match.end() :]
    end = re.search(r"(?im)^\s*(?:ACÓRDÃO|PARECER|RELATÓRIO)\s*$", tail)
    summary = tail[: end.start()] if end else tail
    return re.sub(r"\s+", " ", summary).strip()


def extract_object_from_summary(summary: str) -> str:
    patterns = (
        r"(?is)CONTRATAÇ(?:ÃO|ÕES)\s+DE\s+(.{8,500}?)(?:\.|\n)",
        r"(?is)\bOBJETO\s*:\s*(.{8,500}?)(?:\.|\n)",
    )
    value = _first_match(patterns, summary, flags=re.IGNORECASE | re.DOTALL)
    return re.sub(r"\s+", " ", value).strip() if value else ""


def extract_result(text: str, summary: str) -> str:
    normalized = normalize_for_search(summary)
    outcome_patterns = (
        ("recurso parcialmente provido", r"\brecurso parcialmente provido\b"),
        ("recurso provido", r"\brecurso provido\b"),
        ("recurso improvido", r"\brecurso improvido\b"),
        ("procedência parcial", r"\bprocedencia parcial\b"),
        ("improcedência", r"\bimprocedencia\b"),
        ("procedência", r"(?<!im)\bprocedencia\b(?! parcial)"),
        ("contas regulares", r"\bcontas regulares\b"),
        ("contas irregulares", r"\bcontas irregulares\b"),
        ("arquivamento", r"\barquivamento\b"),
    )
    found = [label for label, pattern in outcome_patterns if re.search(pattern, normalized)]
    if found:
        return "; ".join(found)
    patterns = (
        r"(?is)\b(julg(?:ar|o|am-se|ou)\s+(?:improcedentes?|procedentes?|regulares?|irregulares?)[^.;]{0,260})",
        r"(?is)\b((?:recurso|pedido)\s+(?:parcialmente\s+)?(?:provido|improvido)[^.;]{0,180})",
        r"(?is)\b(contas\s+(?:regulares|irregulares)[^.;]{0,180})",
    )
    value = _first_match(patterns, text, flags=re.IGNORECASE | re.DOTALL)
    if value:
        return re.sub(r"\s+", " ", value).strip()
    return ""


def analyze_document(
    path: Path,
    extraction: ExtractionResult,
    sha256: str,
    index_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    index_meta = {key: repair_mojibake(value) for key, value in (index_meta or {}).items()}
    full_text = "\n".join(page.text for page in extraction.pages)
    first = "\n".join(page.text for page in extraction.pages[:2])
    process = normalize_process_number(index_meta.get("processo")) or _process_from_path(path)
    if not process:
        process = normalize_process_number(_first_match((r"(?i)processo\s*:?\s*(\d{5,12})",), first))
    session_date = _date_iso(index_meta.get("sessao"))
    if not session_date:
        session_date = _date_iso(_first_match((r"(?i)(\d{1,2}/\d{1,2}/\d{4})",), first))
    publication_date = _date_iso(index_meta.get("publicacao"))
    rapporteur = str(index_meta.get("relator") or "").strip()
    if not rapporteur:
        rapporteur = _first_match((r"(?im)^\s*relator\s*:?\s*(.+)$", r"(?im)^\s*relatora\s*:?\s*(.+)$"), first)
    nature = str(index_meta.get("natureza") or "").strip()
    if not nature:
        nature = _first_match((r"(?im)^\s*natureza\s*:?\s*(.+)$",), first)
    judging_body = str(index_meta.get("colegiado") or "").strip()
    if not judging_body:
        judging_body = _first_match((r"(?im)^\s*(tribunal pleno|primeira câmara|segunda câmara)\b.*$",), first)
    entity = _first_match((r"(?im)^\s*(?:jurisdicionado|órgão|entidade|procedência|consulente)\s*:?\s*(.+)$",), first)
    municipality = _first_match((r"(?i)(?:município|prefeitura municipal|câmara municipal)\s+(?:de\s+)?([A-ZÁÉÍÓÚÂÊÔÃÕÇ][A-Za-zÁÉÍÓÚáéíóúÂÊÔâêôÃÕãõÇç\s-]{2,60})",), first)
    regime = identify_regime(full_text)
    contract_type = identify_contract_type(full_text)
    relevance, relevance_score, relevance_reason = classify_relevance(extraction.pages, index_meta, extraction.status)
    themes = extract_themes(extraction.pages)
    articles = extract_legal_articles(full_text)
    legal_basis = "; ".join(articles[:12]) or NOT_IDENTIFIED
    pdf_summary = extract_official_summary(extraction.pages[0].text if extraction.pages else "")
    ementa = str(index_meta.get("ementa") or "").strip() or pdf_summary
    object_from_summary = extract_object_from_summary(ementa)
    decision_scope = "\n".join(page.text for page in extraction.pages[:2] + extraction.pages[-3:])
    result = extract_result(decision_scope, ementa)
    confidence = "baixa" if extraction.needs_ocr or relevance == "pendente_revisao" else ("alta" if index_meta and extraction.total_chars > 500 else "media")
    doc_id = f"tcemg-{process or 'sem-processo'}-{sha256[:12].lower()}"
    return {
        "id": doc_id,
        "sha256": sha256,
        "file_name": path.name,
        "process_number": process or NOT_IDENTIFIED,
        "process_year": (session_date[:4] if session_date else NOT_IDENTIFIED),
        "process_class": nature or NOT_IDENTIFIED,
        "process_nature": nature or NOT_IDENTIFIED,
        "judging_body": judging_body or NOT_IDENTIFIED,
        "rapporteur": rapporteur or NOT_IDENTIFIED,
        "session_date": session_date or NOT_IDENTIFIED,
        "judgment_date": session_date or NOT_IDENTIFIED,
        "publication_date": publication_date or NOT_IDENTIFIED,
        "exercise_analyzed": NOT_IDENTIFIED,
        "entity": entity or NOT_IDENTIFIED,
        "municipality": municipality or NOT_IDENTIFIED,
        "responsible_parties": NOT_IDENTIFIED,
        "applicable_legislation": articles,
        "legal_regime": regime,
        "direct_contract_type": contract_type,
        "legal_basis": legal_basis,
        "contract_object": object_from_summary or NOT_IDENTIFIED,
        "contract_value": NOT_IDENTIFIED,
        "contract_period": NOT_IDENTIFIED,
        "main_facts": NOT_IDENTIFIED,
        "defense_arguments": NOT_IDENTIFIED,
        "technical_opinion": NOT_IDENTIFIED,
        "mpc_opinion": NOT_IDENTIFIED,
        "vote_grounds": NOT_IDENTIFIED,
        "extractable_thesis": (f"Ementa oficial (p. 1): {ementa[:2500]}" if ementa else NOT_IDENTIFIED),
        "recognized_irregularities": NOT_IDENTIFIED,
        "dismissed_irregularities": NOT_IDENTIFIED,
        "caveats": NOT_IDENTIFIED,
        "recommendations": NOT_IDENTIFIED,
        "determinations": NOT_IDENTIFIED,
        "sanctions": NOT_IDENTIFIED,
        "judgment_result": result or NOT_IDENTIFIED,
        "cited_legal_articles": articles,
        "cited_cases": extract_cited_cases(full_text, process),
        "keywords": sorted({theme["theme"] for theme in themes}),
        "themes": themes,
        "relevance": relevance,
        "relevance_score": round(relevance_score, 3),
        "relevance_reason": relevance_reason,
        "confidence": confidence,
        "metadata_pages": {"identification": [1] if extraction.pages else []},
        "extraction_status": extraction.status,
        "review_notes": "Revisão humana pendente",
        "official_summary": ementa or NOT_IDENTIFIED,
        "official_summary_source": ("indice_oficial" if index_meta.get("ementa") else "pdf_pagina_1" if pdf_summary else "nao_identificado"),
        "excerpts": select_relevant_excerpts(extraction.pages),
        "page_count": len(extraction.pages),
        "total_chars": extraction.total_chars,
        "needs_ocr": extraction.needs_ocr,
        "extractor": extraction.extractor,
        "warnings": extraction.warnings,
        "error": extraction.error,
        "index_metadata": index_meta,
    }


def load_index_metadata(input_root: Path) -> dict[str, dict[str, Any]]:
    """Mapeia o caminho absoluto esperado do PDF ao registro do índice oficial."""
    result: dict[str, dict[str, Any]] = {}
    for index_file in input_root.rglob("indice.json"):
        try:
            data = json.loads(index_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(data, list):
            continue
        for raw in data:
            if not isinstance(raw, dict):
                continue
            repaired = {str(key): repair_mojibake(value) for key, value in raw.items()}
            relative = repaired.get("arquivo_pdf")
            if not relative:
                continue
            path = (index_file.parent / str(relative)).resolve()
            repaired["_index_file"] = index_file.resolve().as_posix()
            result[str(path).casefold()] = repaired
    return result
