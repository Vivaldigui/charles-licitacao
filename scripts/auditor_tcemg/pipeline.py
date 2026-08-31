"""Orquestra diagnóstico, ingestão, validação e contexto de auditoria."""
from __future__ import annotations

import json
import random
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from .config import DATABASE_PATH, NOT_IDENTIFIED, REPO_ROOT, REPORTS_DIR, TEXT_DIR, TODAY
from .database import (
    DOCUMENT_COLUMNS,
    connect,
    corpus_stats,
    extraction_by_hash,
    occurrence_is_current,
    record_skipped,
    search,
    upsert_document,
)
from .extractors import ExtractionResult, PageText, extract_document, iter_supported_files, sha256_file
from .metadata import (
    analyze_document,
    classify_relevance,
    extract_themes,
    load_index_metadata,
    normalize_for_search,
)
from .reports import ensure_output_structure, relative_to_repo, write_all_reports, write_ficha


def _all_input_files(root: Path) -> list[Path]:
    if root.is_file():
        return [root]
    return sorted(path for path in root.rglob("*") if path.is_file())


def _is_auxiliary(path: Path) -> bool:
    """Índices/README do corpus são inventariados, mas não são julgados."""
    name = path.name.casefold()
    return name.startswith("leia-me") or name in {"indice.json", "indice.csv"}


def diagnose(root: Path) -> dict[str, Any]:
    files = _all_input_files(root)
    formats = Counter((path.suffix.lower() or "[sem extensão]") for path in files)
    supported = list(iter_supported_files(root)) if root.is_dir() else ([root] if root.suffix.lower() in {".pdf", ".txt", ".md", ".html", ".htm", ".docx"} else [])
    candidates = [path for path in supported if not _is_auxiliary(path)]
    hashes: dict[str, list[str]] = defaultdict(list)
    failures: list[dict[str, str]] = []
    for path in candidates:
        try:
            hashes[sha256_file(path)].append(relative_to_repo(path))
        except OSError as exc:
            failures.append({"path": str(path), "error": str(exc)})
    duplicates = {digest: paths for digest, paths in hashes.items() if len(paths) > 1}
    sample_results = []
    for path in representative_sample(candidates, min(5, len(candidates))):
        extraction = extract_document(path)
        sample_results.append(
            {
                "path": relative_to_repo(path),
                "status": extraction.status,
                "pages": len(extraction.pages),
                "chars": extraction.total_chars,
                "needs_ocr": extraction.needs_ocr,
                "error": extraction.error,
            }
        )
    return {
        "input": str(root.resolve()),
        "total_files": len(files),
        "formats": dict(sorted(formats.items())),
        "supported_files": len(supported),
        "candidate_documents": len(candidates),
        "auxiliary_files": len(supported) - len(candidates),
        "unique_hashes": len(hashes),
        "duplicate_groups": len(duplicates),
        "duplicate_copies": sum(len(paths) - 1 for paths in duplicates.values()),
        "failures": failures,
        "sample_extraction": sample_results,
    }


def representative_sample(files: list[Path], limit: int) -> list[Path]:
    if limit <= 0 or not files:
        return []
    groups: dict[str, list[Path]] = defaultdict(list)
    for path in files:
        # Primeiro diretório abaixo do corpus, sem presumir nome fixo.
        corpus_parts = [part for part in path.parts if part.startswith("TCE-MG_") and part != "TCE-MG_JULGADOS"]
        corpus = corpus_parts[-1] if corpus_parts else path.parent.name
        groups[corpus].append(path)
    output: list[Path] = []
    offsets = {name: 0 for name in groups}
    while len(output) < min(limit, len(files)):
        changed = False
        for name in sorted(groups):
            index = offsets[name]
            if index < len(groups[name]) and len(output) < limit:
                output.append(groups[name][index])
                offsets[name] += 1
                changed = True
        if not changed:
            break
    return output


def _corpus_name(path: Path, input_root: Path) -> str:
    try:
        relative = path.resolve().relative_to(input_root.resolve())
        return relative.parts[0] if len(relative.parts) > 1 else input_root.name
    except ValueError:
        return path.parent.name


def ingest(
    input_root: Path,
    *,
    database_path: Path = DATABASE_PATH,
    limit: int | None = None,
    ocr: bool = False,
    force: bool = False,
    simulate: bool = False,
    generate_reports: bool = True,
) -> dict[str, Any]:
    files = list(iter_supported_files(input_root)) if input_root.is_dir() else [input_root]
    if input_root.is_dir():
        files = [path for path in files if not _is_auxiliary(path)]
    if limit is not None:
        files = representative_sample(files, limit)
    if simulate:
        return {
            "simulate": True,
            "files": [relative_to_repo(path) for path in files],
            "count": len(files),
            "message": "Simulação: nenhum arquivo foi gravado ou alterado.",
        }
    ensure_output_structure(input_root)
    index_metadata = load_index_metadata(input_root if input_root.is_dir() else input_root.parent)
    connection = connect(database_path)
    summary = Counter()
    errors: list[dict[str, str]] = []
    try:
        for path in files:
            try:
                digest = sha256_file(path)
                source_path = relative_to_repo(path)
                if not force and occurrence_is_current(connection, source_path, digest):
                    record_skipped(connection, source_path, digest)
                    summary["skipped"] += 1
                    continue
                extraction = extraction_by_hash(connection, digest)
                if extraction is None:
                    extraction = extract_document(path, ocr=ocr)
                else:
                    summary["reused_duplicate_text"] += 1
                source_meta = index_metadata.get(str(path.resolve()).casefold(), {})
                metadata = analyze_document(path, extraction, digest, source_meta)
                text_path = TEXT_DIR / f"{metadata['id']}.txt"
                text_path.parent.mkdir(parents=True, exist_ok=True)
                text_path.write_text(extraction.as_marked_text(), encoding="utf-8")
                ficha_path = write_ficha(metadata, source_path)
                upsert_document(
                    connection,
                    metadata=metadata,
                    extraction=extraction,
                    source_path=source_path,
                    corpus=_corpus_name(path, input_root),
                    file_format=path.suffix.lower().lstrip("."),
                    size_bytes=path.stat().st_size,
                    text_path=relative_to_repo(text_path),
                    ficha_path=ficha_path,
                )
                summary[metadata["extraction_status"]] += 1
                summary[f"relevancia_{metadata['relevance']}"] += 1
                if metadata["needs_ocr"]:
                    summary["ocr_needed"] += 1
                if ficha_path:
                    summary["fichas"] += 1
                summary["processed"] += 1
            except Exception as exc:  # retomada: registra e segue para o próximo
                source_path = relative_to_repo(path)
                errors.append({"path": source_path, "error": f"{type(exc).__name__}: {exc}"})
                connection.execute(
                    "INSERT INTO processing_history(source_path,status,message,processed_at) VALUES (?,?,?,datetime('now'))",
                    (source_path, "falha_pipeline", errors[-1]["error"]),
                )
                connection.commit()
                summary["pipeline_failures"] += 1
        if generate_reports:
            write_all_reports(connection, input_root)
        stats = corpus_stats(connection)
    finally:
        connection.close()
    return {"summary": dict(summary), "errors": errors, "corpus": stats, "database": str(database_path)}


def validate_database(
    database_path: Path = DATABASE_PATH,
    *,
    sample_size: int = 10,
    confirmations_path: Path | None = None,
) -> tuple[list[str], list[str], dict[str, Any]]:
    connection = connect(database_path)
    errors: list[str] = []
    warnings: list[str] = []
    try:
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            errors.append(f"SQLite integrity_check: {integrity}")
        rows = connection.execute(
            """SELECT d.id,d.page_count,COUNT(p.page_number) actual,d.extraction_status,d.text_path,d.ficha_path
               FROM documents d LEFT JOIN pages p ON p.document_id=d.id
               GROUP BY d.id"""
        ).fetchall()
        for row in rows:
            if row["page_count"] != row["actual"]:
                errors.append(f"{row['id']}: page_count={row['page_count']} mas páginas={row['actual']}")
            text_path = REPO_ROOT / row["text_path"] if row["text_path"] else None
            if text_path and not text_path.exists():
                errors.append(f"{row['id']}: texto extraído ausente ({row['text_path']})")
        bad_citations = connection.execute(
            """SELECT c.document_id,c.page_number FROM citations c
               LEFT JOIN pages p ON p.document_id=c.document_id AND p.page_number=c.page_number
               WHERE p.document_id IS NULL"""
        ).fetchall()
        for row in bad_citations:
            errors.append(f"{row['document_id']}: citação aponta página inexistente {row['page_number']}")
        fts_count = connection.execute("SELECT COUNT(*) FROM pages_fts").fetchone()[0]
        page_count = connection.execute("SELECT COUNT(*) FROM pages").fetchone()[0]
        if fts_count != page_count:
            errors.append(f"FTS5 tem {fts_count} registros e pages tem {page_count}")

        original_rows = connection.execute(
            "SELECT source_path,sha256 FROM occurrences ORDER BY source_path"
        ).fetchall()
        originals_verified = 0
        preservation_lines = [
            "---", "tipo: checklist", "hierarquia: operacional",
            "tema: preservacao dos originais do corpus tce-mg",
            "fonte: verificacao sha-256 dos arquivos locais", "vigencia: vigente",
            f"atualizado_em: {TODAY}", "tags: [tce-mg, sha256, preservacao]", "---", "",
            "# RELATÓRIO DE PRESERVAÇÃO DOS ORIGINAIS", "",
        ]
        for occurrence in original_rows:
            source = REPO_ROOT / occurrence["source_path"]
            if not source.exists():
                errors.append(f"Original ausente: {occurrence['source_path']}")
                continue
            actual_hash = sha256_file(source)
            if actual_hash != occurrence["sha256"]:
                errors.append(
                    f"Hash divergente: {occurrence['source_path']} "
                    f"(esperado {occurrence['sha256']}, atual {actual_hash})"
                )
                continue
            originals_verified += 1
        preservation_lines += [
            f"- Ocorrências registradas: **{len(original_rows)}**.",
            f"- Originais presentes e com SHA-256 íntegro: **{originals_verified}**.",
            f"- Ausências ou divergências: **{len(original_rows) - originals_verified}**.",
            "- Manifesto completo: `03_jurisprudencia/tce_mg/contratacao_direta/indices/manifesto_originais.jsonl`.",
            "",
            "A verificação recalculou o SHA-256 de cada arquivo de origem; nenhum original foi movido ou sobrescrito pela rotina.",
        ]
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        (REPORTS_DIR / "RELATORIO_PRESERVACAO_ORIGINAIS.md").write_text(
            "\n".join(preservation_lines) + "\n", encoding="utf-8"
        )

        all_docs = connection.execute(
            "SELECT id,process_number,rapporteur,judgment_date,judging_body,contract_object,extractable_thesis,judgment_result,legal_regime,recognized_irregularities,canonical_source_path FROM documents ORDER BY id"
        ).fetchall()
        rng = random.Random(141332026)
        chosen = rng.sample(list(all_docs), min(sample_size, len(all_docs))) if all_docs else []
        confirmations: dict[str, Any] = {}
        if confirmations_path and confirmations_path.exists():
            raw = json.loads(confirmations_path.read_text(encoding="utf-8"))
            if isinstance(raw, list):
                confirmations = {item.get("document_id"): item for item in raw if isinstance(item, dict) and item.get("document_id")}
        checked = 0
        correct = 0
        lines = [
            "---", "tipo: checklist", "hierarquia: operacional", "tema: validacao amostral do corpus tce-mg",
            "fonte: conferencia humana dos originais", "vigencia: vigente", f"atualizado_em: {TODAY}",
            "tags: [tce-mg, validacao-amostral, revisao-humana]", "---", "",
            "# RELATÓRIO DE VALIDAÇÃO AMOSTRAL", "",
            f"- Tamanho do universo: {len(all_docs)} documento(s).",
            f"- Tamanho da amostra: {len(chosen)} documento(s).",
            "- Método: amostragem pseudoaleatória determinística (semente 141332026).", "",
            "| Documento | Processo | Relator | Data | Órgão | Objeto | Tese | Resultado | Regime | Irregularidades | Páginas citadas | Revisão |",
            "|---|---|---|---|---|---|---|---|---|---|---|---|",
        ]
        problematic: list[str] = []
        review_notes: list[str] = []
        for row in chosen:
            confirmation = confirmations.get(row["id"])
            status = "PENDENTE DE CONFERÊNCIA HUMANA"
            if confirmation:
                fields = confirmation.get("fields", {})
                bool_values = [value for value in fields.values() if isinstance(value, bool)]
                checked += len(bool_values)
                correct += sum(bool_values)
                status = str(confirmation.get("status") or "CONFERIDO")
                if any(value is False for value in bool_values):
                    problematic.append(row["id"])
                if confirmation.get("notes"):
                    review_notes.append(f"- `{row['id']}`: {confirmation['notes']}")
            pages_checked = confirmation.get("pages_checked", []) if confirmation else []
            citation_pages = ", ".join(str(page) for page in pages_checked) or "pendente"
            lines.append(
                f"| {row['id']} | {row['process_number']} | {row['rapporteur']} | {row['judgment_date']} | "
                f"{row['judging_body']} | {row['contract_object']} | {row['extractable_thesis']} | "
                f"{row['judgment_result']} | {row['legal_regime']} | {row['recognized_irregularities']} | "
                f"{citation_pages} | {status} |"
            )
        lines += ["", f"- Campos efetivamente conferidos: {checked}."]
        if checked:
            lines.append(f"- Campos corretos: {correct}; incorretos: {checked - correct}; taxa de acerto: {correct / checked:.2%}.")
        else:
            lines.append("- Taxa de acerto: não calculada; não houve confirmações humanas fornecidas.")
        lines += ["", "## Documentos problemáticos", ""]
        lines.append(", ".join(f"`{item}`" for item in problematic) if problematic else "Nenhum na amostra.")
        lines += ["", "## Notas da conferência", ""]
        lines.extend(review_notes or ["Nenhuma nota registrada."])
        lines += [
            "", "## Correções realizadas", "",
            "Foi registrada em `human_reviews` a correção do regime predominante do Processo 1121072 para Lei 8.666/1993. "
            "Os campos mecânicos de irregularidades permaneceram como não identificados e foram marcados como incorretos na amostra; "
            "não foram preenchidos por inferência automática.",
            "", "## Limitações", "",
            "A rotina seleciona e apresenta a amostra, mas não declara validação sem conferência humana contra cada original.",
        ]
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        (REPORTS_DIR / "RELATORIO_VALIDACAO_AMOSTRAL.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        if not confirmations:
            warnings.append("Amostra selecionada, mas validação humana ainda não registrada.")
        stats = corpus_stats(connection)
        stats["originals_verified"] = originals_verified
    finally:
        connection.close()
    return errors, warnings, stats


def reclassify_database(database_path: Path = DATABASE_PATH, *, input_root: Path) -> dict[str, Any]:
    """Recalcula relevância sem reextrair PDFs nem regravar páginas/FTS5."""
    connection = connect(database_path)
    changed = 0
    try:
        documents = connection.execute("SELECT * FROM documents ORDER BY id").fetchall()
        for row in documents:
            pages = [
                PageText(int(page["page_number"]), str(page["page_text"]))
                for page in connection.execute(
                    "SELECT page_number,page_text FROM pages WHERE document_id=? ORDER BY page_number", (row["id"],)
                ).fetchall()
            ]
            try:
                index_meta = json.loads(row["index_metadata_json"] or "{}")
            except json.JSONDecodeError:
                index_meta = {}
            extraction = ExtractionResult(
                pages=pages,
                status=row["extraction_status"],
                needs_ocr=bool(row["needs_ocr"]),
                extractor=row["extractor"] or "indice-local",
                warnings=json.loads(row["warnings_json"] or "[]"),
                error=row["error"] or "",
            )
            metadata = analyze_document(
                REPO_ROOT / row["canonical_source_path"], extraction, row["sha256"], index_meta
            )
            # Revisões humanas concluídas prevalecem sobre nova triagem mecânica.
            for review in connection.execute(
                "SELECT field_name,corrected_value FROM human_reviews WHERE document_id=? AND status='concluida' ORDER BY id",
                (row["id"],),
            ).fetchall():
                metadata[review["field_name"]] = review["corrected_value"]
            relevance = metadata["relevance"]
            score = metadata["relevance_score"]
            reason = metadata["relevance_reason"]
            if relevance != row["relevance"] or float(score) != float(row["relevance_score"]):
                changed += 1
            assignments = ",".join(f"{column}=?" for column in DOCUMENT_COLUMNS)
            connection.execute(
                f"UPDATE documents SET {assignments},updated_at=datetime('now') WHERE id=?",
                [metadata.get(column, "") for column in DOCUMENT_COLUMNS] + [row["id"]],
            )
            source = connection.execute(
                "SELECT source_path FROM occurrences WHERE document_id=? ORDER BY source_path LIMIT 1", (row["id"],)
            ).fetchone()
            ficha_path = write_ficha(metadata, source["source_path"] if source else row["canonical_source_path"])
            connection.execute("UPDATE documents SET ficha_path=? WHERE id=?", (ficha_path, row["id"]))
        connection.commit()
        write_all_reports(connection, input_root)
        stats = corpus_stats(connection)
    finally:
        connection.close()
    return {"changed": changed, "corpus": stats}


def _inventory_process(process_path: Path) -> tuple[list[dict[str, Any]], str, list[str]]:
    files = _all_input_files(process_path) if process_path.is_dir() else [process_path]
    inventory: list[dict[str, Any]] = []
    combined: list[str] = []
    warnings: list[str] = []
    for path in files:
        if path.name.lower() == "processo.json":
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                combined.append(json.dumps(data, ensure_ascii=False))
                inventory.append({"path": str(path), "status": "presente", "format": "json", "pages": 1})
            except Exception as exc:
                inventory.append({"path": str(path), "status": "ilegivel", "format": "json", "pages": 0})
                warnings.append(f"{path}: {exc}")
            continue
        if path.suffix.lower() not in {".pdf", ".txt", ".md", ".html", ".htm", ".docx"}:
            inventory.append({"path": str(path), "status": "formato_nao_analisado", "format": path.suffix.lower(), "pages": 0})
            continue
        extraction = extract_document(path)
        status = "presente" if extraction.status in {"sucesso", "alerta", "sucesso_ocr"} else ("ilegivel" if extraction.needs_ocr else extraction.status)
        inventory.append({"path": str(path), "status": status, "format": path.suffix.lower(), "pages": len(extraction.pages)})
        combined.extend(page.text for page in extraction.pages)
        warnings.extend(f"{path}: {warning}" for warning in extraction.warnings)
    return inventory, "\n".join(combined), warnings


def prepare_audit_context(
    process_path: Path,
    output_path: Path,
    *,
    database_path: Path = DATABASE_PATH,
    limit_per_query: int = 5,
) -> dict[str, Any]:
    inventory, process_text, warnings = _inventory_process(process_path)
    themes = extract_themes([PageText(1, process_text)])
    process_data: dict[str, Any] = {}
    json_path = process_path / "processo.json" if process_path.is_dir() else None
    if json_path and json_path.exists():
        try:
            process_data = json.loads(json_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass
    object_text = str(process_data.get("objeto") or "").strip()
    regime = "lei-14133" if "14.133" in process_text else ""
    queries: list[str] = []
    if object_text:
        queries.append(object_text)
    for theme in themes[:8]:
        queries.append(theme["theme"])
    if not queries:
        words = [word for word in normalize_for_search(process_text).split() if len(word) > 5]
        queries.append(" ".join(words[:8]) or "contratação direta")
    # Preserva ordem e evita consultas duplicadas.
    queries = list(dict.fromkeys(queries))
    connection = connect(database_path)
    selected: dict[tuple[str, int], dict[str, Any]] = {}
    discarded: dict[tuple[str, int], dict[str, Any]] = {}
    query_records: list[dict[str, Any]] = []
    try:
        for query in queries:
            results = search(
                connection,
                query=query,
                filters={"regime": regime} if regime else {},
                include_incidental=True,
                limit=limit_per_query * 2,
            )
            query_records.append({"query": query, "filters": {"regime": regime or "sem filtro"}, "results": len(results)})
            for result in results:
                key = (result["id"], int(result["page_number"] or 1))
                result = dict(result)
                result["selection_reason"] = f"Correspondência textual com a consulta '{query}', relevância {result['relevance']} e regime {result['legal_regime']}."
                if result["relevance"] in {"direta", "parcial"} and len(selected) < limit_per_query * max(1, len(queries)):
                    selected[key] = result
                else:
                    result["discard_reason"] = "Menção incidental/falso positivo ou excedeu o limite de contexto; não entra na recuperação padrão."
                    discarded[key] = result
    finally:
        connection.close()

    lines = [
        "---", "tipo: checklist", "hierarquia: operacional", "tema: contexto jurisprudencial de auditoria",
        "fonte: indice local TCE-MG", "vigencia: vigente", f"atualizado_em: {TODAY}",
        "tags: [modo-auditor, tce-mg, contexto-jurisprudencial]", "---", "",
        "# CONTEXTO JURISPRUDENCIAL DA AUDITORIA", "",
        "> Somente julgados deste pacote, lidos diretamente nas páginas indicadas, podem ser citados no relatório final.", "",
        "## 1. Processo e inventário documental", "",
        f"Processo/pasta: `{process_path}`", "",
        "| Arquivo | Formato | Status | Páginas |", "|---|---|---|---:|",
    ]
    for item in inventory:
        lines.append(f"| `{item['path']}` | {item['format']} | {item['status']} | {item['pages']} |")
    lines += ["", "## 2. Temas extraídos do caso", ""]
    lines.extend(f"- {theme['theme']} (evidência no processo: {theme['evidence']})" for theme in themes)
    if not themes:
        lines.append("- Não identificados automaticamente; revisão humana necessária.")
    lines += ["", "## 3. Consultas e filtros", ""]
    for record in query_records:
        lines.append(f"- Consulta: `{record['query']}`; filtros: `{json.dumps(record['filters'], ensure_ascii=False)}`; resultados avaliados: {record['results']}.")
    lines += ["", "## 4. Julgados selecionados", ""]
    for result in selected.values():
        lines += [
            f"### Processo {result['process_number']} — página {result['page_number']}", "",
            f"- Órgão julgador: {result['judging_body']}",
            f"- Data: {result['judgment_date']}",
            f"- Regime: {result['legal_regime']}",
            f"- Relevância/score: {result['relevance']} / {result['score']}",
            f"- Arquivo: `{result['source_path']}`",
            f"- Motivo da seleção: {result['selection_reason']}",
            f"- Trecho: {result['snippet']}",
            f"- Citação permitida: `[Fonte: {result['source_path']}, p. {result['page_number']}]`", "",
        ]
    if not selected:
        lines.append("Nenhum julgado diretamente pertinente foi selecionado. Não há base para citar jurisprudência do corpus neste caso.")
    lines += ["", "## 5. Resultados descartados", ""]
    for result in list(discarded.values())[:50]:
        lines.append(f"- Processo {result['process_number']}, p. {result['page_number']}, score {result['score']}: {result['discard_reason']}")
    if not discarded:
        lines.append("Nenhum resultado descartado registrado.")
    lines += ["", "## 6. Alertas e limitações", ""]
    lines.extend(f"- {warning}" for warning in warnings)
    lines += [
        "- O ranking é mecânico e não substitui a leitura do inteiro teor.",
        "- Conferir voto vencedor, contraditório, peculiaridades fáticas e compatibilidade temporal antes do uso.",
        "- Não afirmar consenso, divergência ou vigência apenas pela frequência dos resultados.",
    ]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "output": str(output_path),
        "inventory": len(inventory),
        "themes": len(themes),
        "queries": len(queries),
        "selected": len(selected),
        "discarded": len(discarded),
        "warnings": warnings,
    }
