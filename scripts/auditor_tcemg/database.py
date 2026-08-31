"""SQLite/FTS5 do corpus jurisprudencial."""
from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .config import DEFAULT_RELEVANCES
from .extractors import ExtractionResult, PageText


SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    sha256 TEXT NOT NULL,
    canonical_source_path TEXT NOT NULL,
    file_name TEXT NOT NULL,
    format TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    page_count INTEGER NOT NULL DEFAULT 0,
    total_chars INTEGER NOT NULL DEFAULT 0,
    text_path TEXT,
    ficha_path TEXT,
    process_number TEXT,
    process_year TEXT,
    process_class TEXT,
    process_nature TEXT,
    judging_body TEXT,
    rapporteur TEXT,
    session_date TEXT,
    judgment_date TEXT,
    publication_date TEXT,
    exercise_analyzed TEXT,
    entity TEXT,
    municipality TEXT,
    responsible_parties TEXT,
    legal_regime TEXT,
    direct_contract_type TEXT,
    legal_basis TEXT,
    contract_object TEXT,
    contract_value TEXT,
    contract_period TEXT,
    main_facts TEXT,
    defense_arguments TEXT,
    technical_opinion TEXT,
    mpc_opinion TEXT,
    vote_grounds TEXT,
    extractable_thesis TEXT,
    recognized_irregularities TEXT,
    dismissed_irregularities TEXT,
    caveats TEXT,
    recommendations TEXT,
    determinations TEXT,
    sanctions TEXT,
    judgment_result TEXT,
    official_summary TEXT,
    relevance TEXT NOT NULL,
    relevance_score REAL NOT NULL DEFAULT 0,
    relevance_reason TEXT,
    confidence TEXT,
    extraction_status TEXT NOT NULL,
    needs_ocr INTEGER NOT NULL DEFAULT 0,
    extractor TEXT,
    review_notes TEXT,
    warnings_json TEXT,
    error TEXT,
    index_metadata_json TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_documents_sha ON documents(sha256);
CREATE INDEX IF NOT EXISTS idx_documents_process ON documents(process_number);
CREATE INDEX IF NOT EXISTS idx_documents_regime ON documents(legal_regime);
CREATE INDEX IF NOT EXISTS idx_documents_relevance ON documents(relevance);
CREATE INDEX IF NOT EXISTS idx_documents_dates ON documents(judgment_date, publication_date);

CREATE TABLE IF NOT EXISTS occurrences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    source_path TEXT NOT NULL UNIQUE,
    corpus TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    index_file TEXT,
    source_metadata_json TEXT,
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_occurrences_hash ON occurrences(sha256);

CREATE TABLE IF NOT EXISTS pages (
    document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    page_number INTEGER NOT NULL,
    page_text TEXT NOT NULL,
    char_count INTEGER NOT NULL,
    PRIMARY KEY(document_id, page_number)
);

CREATE TABLE IF NOT EXISTS metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    pages_json TEXT NOT NULL DEFAULT '[]',
    confidence TEXT NOT NULL DEFAULT 'baixa',
    UNIQUE(document_id, key)
);

CREATE TABLE IF NOT EXISTS themes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    theme TEXT NOT NULL,
    page_number INTEGER,
    evidence TEXT,
    confidence TEXT,
    UNIQUE(document_id, theme)
);
CREATE INDEX IF NOT EXISTS idx_themes_theme ON themes(theme);

CREATE TABLE IF NOT EXISTS theses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    thesis TEXT NOT NULL,
    page_number INTEGER,
    evidence TEXT,
    source_kind TEXT NOT NULL DEFAULT 'revisao_humana_pendente',
    confidence TEXT NOT NULL DEFAULT 'baixa'
);

CREATE TABLE IF NOT EXISTS findings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    page_number INTEGER,
    evidence TEXT,
    category TEXT NOT NULL,
    severity TEXT NOT NULL DEFAULT 'indeterminada',
    legal_regime TEXT,
    status TEXT NOT NULL DEFAULT 'triagem_mecanica',
    confidence TEXT NOT NULL DEFAULT 'baixa'
);

CREATE TABLE IF NOT EXISTS legal_provisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    provision TEXT NOT NULL,
    page_number INTEGER,
    UNIQUE(document_id, provision)
);

CREATE TABLE IF NOT EXISTS citations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    page_number INTEGER NOT NULL,
    evidence TEXT NOT NULL,
    citation_kind TEXT NOT NULL DEFAULT 'trecho_recuperado'
);

CREATE TABLE IF NOT EXISTS case_relations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    related_process TEXT NOT NULL,
    relation_type TEXT NOT NULL DEFAULT 'citado_no_texto',
    UNIQUE(document_id, related_process, relation_type)
);

CREATE TABLE IF NOT EXISTS processing_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_path TEXT NOT NULL,
    document_id TEXT,
    sha256 TEXT,
    status TEXT NOT NULL,
    message TEXT,
    processed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS human_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    reviewer TEXT,
    reviewed_at TEXT,
    field_name TEXT,
    previous_value TEXT,
    corrected_value TEXT,
    notes TEXT,
    status TEXT NOT NULL DEFAULT 'pendente'
);

CREATE VIRTUAL TABLE IF NOT EXISTS pages_fts USING fts5(
    document_id UNINDEXED,
    page_number UNINDEXED,
    page_text,
    theme_text,
    metadata_text,
    tokenize='unicode61 remove_diacritics 2'
);
"""


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA foreign_keys=ON")
    connection.executescript(SCHEMA)
    return connection


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def occurrence_is_current(connection: sqlite3.Connection, source_path: str, sha256: str) -> bool:
    row = connection.execute(
        "SELECT 1 FROM occurrences WHERE source_path=? AND sha256=?", (source_path, sha256)
    ).fetchone()
    return row is not None


def extraction_by_hash(connection: sqlite3.Connection, sha256: str) -> ExtractionResult | None:
    """Reaproveita texto de binário idêntico sem reler o PDF."""
    row = connection.execute(
        "SELECT id,extraction_status,needs_ocr,extractor,warnings_json,error FROM documents WHERE sha256=? LIMIT 1",
        (sha256,),
    ).fetchone()
    if row is None:
        return None
    pages = [
        PageText(int(page["page_number"]), str(page["page_text"]))
        for page in connection.execute(
            "SELECT page_number,page_text FROM pages WHERE document_id=? ORDER BY page_number", (row["id"],)
        ).fetchall()
    ]
    try:
        warnings = json.loads(row["warnings_json"] or "[]")
    except json.JSONDecodeError:
        warnings = []
    return ExtractionResult(
        pages=pages,
        status=row["extraction_status"],
        needs_ocr=bool(row["needs_ocr"]),
        extractor=f"{row['extractor']} (reuso SHA-256)",
        warnings=warnings,
        error=row["error"] or "",
    )


DOCUMENT_COLUMNS = [
    "process_number", "process_year", "process_class", "process_nature", "judging_body",
    "rapporteur", "session_date", "judgment_date", "publication_date", "exercise_analyzed",
    "entity", "municipality", "responsible_parties", "legal_regime", "direct_contract_type",
    "legal_basis", "contract_object", "contract_value", "contract_period", "main_facts",
    "defense_arguments", "technical_opinion", "mpc_opinion", "vote_grounds",
    "extractable_thesis", "recognized_irregularities", "dismissed_irregularities", "caveats",
    "recommendations", "determinations", "sanctions", "judgment_result", "official_summary",
    "relevance", "relevance_score", "relevance_reason", "confidence", "extraction_status",
    "extractor", "review_notes", "error",
]


def upsert_document(
    connection: sqlite3.Connection,
    *,
    metadata: dict[str, Any],
    extraction: ExtractionResult,
    source_path: str,
    corpus: str,
    file_format: str,
    size_bytes: int,
    text_path: str,
    ficha_path: str,
) -> None:
    now = utc_now()
    existing = connection.execute("SELECT created_at FROM documents WHERE id=?", (metadata["id"],)).fetchone()
    values: dict[str, Any] = {
        "id": metadata["id"],
        "sha256": metadata["sha256"],
        "canonical_source_path": source_path,
        "file_name": metadata["file_name"],
        "format": file_format,
        "size_bytes": size_bytes,
        "page_count": metadata["page_count"],
        "total_chars": metadata["total_chars"],
        "text_path": text_path,
        "ficha_path": ficha_path,
        "needs_ocr": int(bool(metadata["needs_ocr"])),
        "warnings_json": json.dumps(metadata.get("warnings", []), ensure_ascii=False),
        "index_metadata_json": json.dumps(metadata.get("index_metadata", {}), ensure_ascii=False),
        "created_at": existing["created_at"] if existing else now,
        "updated_at": now,
    }
    for column in DOCUMENT_COLUMNS:
        values[column] = metadata.get(column, "")
    columns = list(values)
    placeholders = ",".join("?" for _ in columns)
    assignments = ",".join(f"{column}=excluded.{column}" for column in columns if column != "id")
    connection.execute(
        f"INSERT INTO documents ({','.join(columns)}) VALUES ({placeholders}) "
        f"ON CONFLICT(id) DO UPDATE SET {assignments}",
        [values[column] for column in columns],
    )
    source_meta = metadata.get("index_metadata", {})
    connection.execute(
        """INSERT INTO occurrences
        (document_id, source_path, corpus, sha256, size_bytes, index_file, source_metadata_json, first_seen_at, last_seen_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(source_path) DO UPDATE SET
          document_id=excluded.document_id, corpus=excluded.corpus, sha256=excluded.sha256,
          size_bytes=excluded.size_bytes, index_file=excluded.index_file,
          source_metadata_json=excluded.source_metadata_json, last_seen_at=excluded.last_seen_at""",
        (
            metadata["id"], source_path, corpus, metadata["sha256"], size_bytes,
            source_meta.get("_index_file", ""), json.dumps(source_meta, ensure_ascii=False), now, now,
        ),
    )

    for table in ("pages", "metadata", "themes", "theses", "findings", "legal_provisions", "citations", "case_relations"):
        connection.execute(f"DELETE FROM {table} WHERE document_id=?", (metadata["id"],))
    connection.execute("DELETE FROM pages_fts WHERE document_id=?", (metadata["id"],))

    theme_text = " ".join(item["theme"] for item in metadata.get("themes", []))
    meta_text = " ".join(
        str(metadata.get(key, ""))
        for key in ("process_number", "rapporteur", "judging_body", "municipality", "legal_basis", "legal_regime", "judgment_result", "official_summary")
    )
    for page in extraction.pages:
        connection.execute(
            "INSERT INTO pages(document_id,page_number,page_text,char_count) VALUES (?,?,?,?)",
            (metadata["id"], page.number, page.text, len(page.text)),
        )
        connection.execute(
            "INSERT INTO pages_fts(document_id,page_number,page_text,theme_text,metadata_text) VALUES (?,?,?,?,?)",
            (metadata["id"], page.number, page.text, theme_text, meta_text),
        )

    for key in (
        "process_number", "rapporteur", "judging_body", "session_date", "publication_date",
        "legal_regime", "direct_contract_type", "legal_basis", "judgment_result", "official_summary",
    ):
        connection.execute(
            "INSERT INTO metadata(document_id,key,value,pages_json,confidence) VALUES (?,?,?,?,?)",
            (metadata["id"], key, str(metadata.get(key, "")), json.dumps(metadata.get("metadata_pages", {}).get("identification", [])), metadata.get("confidence", "baixa")),
        )
    for theme in metadata.get("themes", []):
        connection.execute(
            "INSERT INTO themes(document_id,theme,page_number,evidence,confidence) VALUES (?,?,?,?,?)",
            (metadata["id"], theme["theme"], theme.get("evidence_page"), theme.get("evidence", ""), theme.get("confidence", "baixa")),
        )
    for provision in metadata.get("cited_legal_articles", []):
        connection.execute(
            "INSERT OR IGNORE INTO legal_provisions(document_id,provision,page_number) VALUES (?,?,NULL)",
            (metadata["id"], provision),
        )
    for excerpt in metadata.get("excerpts", []):
        connection.execute(
            "INSERT INTO citations(document_id,page_number,evidence,citation_kind) VALUES (?,?,?,?)",
            (metadata["id"], excerpt["page"], excerpt["text"], "trecho_mecanicamente_recuperado"),
        )
    for related in metadata.get("cited_cases", []):
        connection.execute(
            "INSERT OR IGNORE INTO case_relations(document_id,related_process,relation_type) VALUES (?,?,?)",
            (metadata["id"], related, "citado_no_texto"),
        )
    connection.execute(
        "INSERT INTO processing_history(source_path,document_id,sha256,status,message,processed_at) VALUES (?,?,?,?,?,?)",
        (source_path, metadata["id"], metadata["sha256"], metadata["extraction_status"], metadata.get("error") or "; ".join(metadata.get("warnings", [])), now),
    )
    connection.commit()


def record_skipped(connection: sqlite3.Connection, source_path: str, sha256: str) -> None:
    connection.execute(
        "INSERT INTO processing_history(source_path,document_id,sha256,status,message,processed_at) VALUES (?,?,?,'ignorado_idempotencia',?,?)",
        (source_path, None, sha256, "Ocorrência e hash já processados.", utc_now()),
    )
    connection.commit()


def _fts_query(text: str) -> str:
    tokens = re.findall(r"[0-9A-Za-zÀ-ÖØ-öø-ÿ]{2,}", text)
    return " AND ".join(f'"{token.replace(chr(34), chr(34)*2)}"*' for token in tokens[:20])


FILTER_COLUMNS = {
    "processo": "d.process_number",
    "regime": "d.legal_regime",
    "relator": "d.rapporteur",
    "municipio": "d.municipality",
    "resultado": "d.judgment_result",
    "relevancia": "d.relevance",
    "especie": "d.direct_contract_type",
    "objeto": "d.contract_object",
    "fundamento": "d.legal_basis",
    "irregularidade": "d.recognized_irregularities",
}


def search(
    connection: sqlite3.Connection,
    *,
    query: str = "",
    filters: dict[str, str] | None = None,
    theme: str = "",
    date_from: str = "",
    date_to: str = "",
    include_incidental: bool = False,
    limit: int = 20,
) -> list[dict[str, Any]]:
    filters = filters or {}
    where: list[str] = []
    params: list[Any] = []
    if not include_incidental and not filters.get("relevancia"):
        where.append("d.relevance IN (?,?)")
        params.extend(DEFAULT_RELEVANCES)
    for name, value in filters.items():
        if not value:
            continue
        if name in FILTER_COLUMNS:
            where.append(f"LOWER({FILTER_COLUMNS[name]}) LIKE LOWER(?)")
            params.append(f"%{value}%")
        elif name == "artigo":
            where.append(
                "EXISTS (SELECT 1 FROM legal_provisions lp WHERE lp.document_id=d.id "
                "AND LOWER(lp.provision) LIKE LOWER(?))"
            )
            params.append(f"%{value}%")
        elif name == "gravidade":
            where.append(
                "EXISTS (SELECT 1 FROM findings fd WHERE fd.document_id=d.id "
                "AND LOWER(fd.severity) LIKE LOWER(?))"
            )
            params.append(f"%{value}%")
    if theme:
        where.append("EXISTS (SELECT 1 FROM themes t WHERE t.document_id=d.id AND LOWER(t.theme) LIKE LOWER(?))")
        params.append(f"%{theme}%")
    if date_from:
        where.append("d.judgment_date >= ?")
        params.append(date_from)
    if date_to:
        where.append("d.judgment_date <= ?")
        params.append(date_to)
    where_sql = " AND ".join(where) if where else "1=1"

    fts = _fts_query(query)
    if fts:
        sql = f"""
        SELECT d.*, f.page_number,
               snippet(pages_fts, 2, '[', ']', '…', 35) AS snippet,
               bm25(pages_fts, 1.0, 2.0, 1.5) AS raw_score
        FROM pages_fts f JOIN documents d ON d.id=f.document_id
        WHERE pages_fts MATCH ? AND {where_sql}
        ORDER BY raw_score ASC, d.relevance_score DESC
        LIMIT ?
        """
        rows = connection.execute(sql, [fts, *params, max(5, min(limit * 5, 500))]).fetchall()
    elif theme:
        sql = f"""
        SELECT d.*,
               COALESCE((SELECT t2.page_number FROM themes t2
                         WHERE t2.document_id=d.id AND LOWER(t2.theme) LIKE LOWER(?)
                         ORDER BY t2.page_number LIMIT 1), 1) AS page_number,
               COALESCE((SELECT t3.evidence FROM themes t3
                         WHERE t3.document_id=d.id AND LOWER(t3.theme) LIKE LOWER(?)
                         ORDER BY t3.page_number LIMIT 1), substr(p.page_text,1,700)) AS snippet,
               0.0 AS raw_score
        FROM documents d LEFT JOIN pages p ON p.document_id=d.id AND p.page_number=1
        WHERE {where_sql}
        ORDER BY d.relevance_score DESC, d.judgment_date DESC
        LIMIT ?
        """
        theme_like = f"%{theme}%"
        rows = connection.execute(
            sql, [theme_like, theme_like, *params, max(1, min(limit, 200))]
        ).fetchall()
    else:
        sql = f"""
        SELECT d.*, p.page_number, substr(p.page_text,1,700) AS snippet, 0.0 AS raw_score
        FROM documents d LEFT JOIN pages p ON p.document_id=d.id AND p.page_number=1
        WHERE {where_sql}
        ORDER BY d.relevance_score DESC, d.judgment_date DESC
        LIMIT ?
        """
        rows = connection.execute(sql, [*params, max(1, min(limit, 200))]).fetchall()
    results: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        key = str(row["id"])
        if key in seen:
            continue
        seen.add(key)
        item = dict(row)
        item["score"] = round(-float(item.pop("raw_score", 0.0)), 6)
        occurrence = connection.execute(
            "SELECT source_path FROM occurrences WHERE document_id=? ORDER BY source_path LIMIT 1", (row["id"],)
        ).fetchone()
        item["source_path"] = occurrence["source_path"] if occurrence else row["canonical_source_path"]
        results.append(item)
        if len(results) >= limit:
            break
    return results


def catalog_rows(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = connection.execute("SELECT * FROM documents ORDER BY process_number, id").fetchall()
    output: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["source_paths"] = [
            occurrence["source_path"]
            for occurrence in connection.execute(
                "SELECT source_path FROM occurrences WHERE document_id=? ORDER BY source_path", (row["id"],)
            ).fetchall()
        ]
        item["themes"] = [
            theme["theme"]
            for theme in connection.execute(
                "SELECT theme FROM themes WHERE document_id=? ORDER BY theme", (row["id"],)
            ).fetchall()
        ]
        item["legal_provisions"] = [
            provision["provision"]
            for provision in connection.execute(
                "SELECT provision FROM legal_provisions WHERE document_id=? ORDER BY provision", (row["id"],)
            ).fetchall()
        ]
        output.append(item)
    return output


def corpus_stats(connection: sqlite3.Connection) -> dict[str, Any]:
    def scalar(sql: str, params: Iterable[Any] = ()) -> int:
        return int(connection.execute(sql, tuple(params)).fetchone()[0])
    relevance = {row[0]: row[1] for row in connection.execute("SELECT relevance,COUNT(*) FROM documents GROUP BY relevance")}
    statuses = {row[0]: row[1] for row in connection.execute("SELECT extraction_status,COUNT(*) FROM documents GROUP BY extraction_status")}
    return {
        "documents": scalar("SELECT COUNT(*) FROM documents"),
        "occurrences": scalar("SELECT COUNT(*) FROM occurrences"),
        "unique_hashes": scalar("SELECT COUNT(DISTINCT sha256) FROM occurrences"),
        "duplicate_groups": scalar("SELECT COUNT(*) FROM (SELECT sha256 FROM occurrences GROUP BY sha256 HAVING COUNT(*)>1)"),
        "duplicate_copies": scalar("SELECT COALESCE(SUM(c-1),0) FROM (SELECT COUNT(*) c FROM occurrences GROUP BY sha256 HAVING COUNT(*)>1)"),
        "pages": scalar("SELECT COUNT(*) FROM pages"),
        "needs_ocr": scalar("SELECT COUNT(*) FROM documents WHERE needs_ocr=1"),
        "failures": scalar("SELECT COUNT(*) FROM documents WHERE extraction_status LIKE 'falha%' OR extraction_status='formato_nao_suportado'"),
        "fichas": scalar("SELECT COUNT(*) FROM documents WHERE ficha_path IS NOT NULL AND ficha_path<>''"),
        "relevance": relevance,
        "statuses": statuses,
    }
