"""Interface de linha de comando do auditor TCE-MG."""
from __future__ import annotations

import argparse
import json
import logging
import sqlite3
import sys
from pathlib import Path
from typing import Any

from .config import DATABASE_PATH, DEFAULT_INPUT, REPORTS_DIR
from .database import connect, corpus_stats, search, utc_now
from .pipeline import diagnose, ingest, prepare_audit_context, reclassify_database, validate_database
from .reports import write_all_reports

LOG = logging.getLogger("auditor_tcemg")


def _configure_streams() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except OSError:
                pass


def _json_print(data: Any) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2, default=str))


def _diagnostic_markdown(data: dict[str, Any]) -> str:
    lines = [
        "# Diagnóstico do corpus TCE-MG", "",
        f"- Entrada: `{data['input']}`",
        f"- Arquivos: {data['total_files']}",
        f"- Formatos: `{json.dumps(data['formats'], ensure_ascii=False)}`",
        f"- Formatos suportados: {data['supported_files']}",
        f"- Candidatos a julgado: {data['candidate_documents']}",
        f"- Arquivos auxiliares: {data['auxiliary_files']}",
        f"- Hashes únicos: {data['unique_hashes']}",
        f"- Grupos duplicados: {data['duplicate_groups']}",
        f"- Cópias duplicadas: {data['duplicate_copies']}", "",
        "## Amostra de extração", "",
        "| Arquivo | Status | Páginas | Caracteres | OCR |", "|---|---|---:|---:|---|",
    ]
    for item in data["sample_extraction"]:
        lines.append(f"| `{item['path']}` | {item['status']} | {item['pages']} | {item['chars']} | {'sim' if item['needs_ocr'] else 'não'} |")
    if data["failures"]:
        lines += ["", "## Falhas", ""]
        lines.extend(f"- `{item['path']}`: {item['error']}" for item in data["failures"])
    return "\n".join(lines) + "\n"


def _print_search(results: list[dict[str, Any]]) -> None:
    if not results:
        print("Nenhum resultado encontrado com os filtros informados.")
        return
    for index, item in enumerate(results, start=1):
        print(f"## {index}. Processo {item['process_number']} — p. {item['page_number']}")
        print(f"Arquivo: {item['source_path']}")
        print(f"Órgão/data: {item['judging_body']} / {item['judgment_date']}")
        print(f"Regime/relevância: {item['legal_regime']} / {item['relevance']}")
        print(f"Score BM25 normalizado: {item['score']}")
        print(f"Trecho: {item['snippet']}")
        print(f"Citação: [Fonte: {item['source_path']}, p. {item['page_number']}]\n")


REVIEWABLE_FIELDS = {
    "process_number", "process_year", "process_class", "process_nature", "judging_body",
    "rapporteur", "session_date", "judgment_date", "publication_date", "exercise_analyzed",
    "entity", "municipality", "responsible_parties", "legal_regime", "direct_contract_type",
    "legal_basis", "contract_object", "contract_value", "contract_period", "main_facts",
    "defense_arguments", "technical_opinion", "mpc_opinion", "vote_grounds",
    "extractable_thesis", "recognized_irregularities", "dismissed_irregularities", "caveats",
    "recommendations", "determinations", "sanctions", "judgment_result", "official_summary",
    "relevance", "confidence", "review_notes",
}


def _review(args: argparse.Namespace) -> int:
    if args.campo not in REVIEWABLE_FIELDS:
        print(f"[ERRO] Campo não revisável. Permitidos: {', '.join(sorted(REVIEWABLE_FIELDS))}", file=sys.stderr)
        return 2
    connection = connect(Path(args.banco))
    try:
        row = connection.execute(f"SELECT {args.campo} FROM documents WHERE id=?", (args.documento,)).fetchone()
        if row is None:
            print(f"[ERRO] Documento não encontrado: {args.documento}", file=sys.stderr)
            return 2
        previous = row[args.campo]
        connection.execute(f"UPDATE documents SET {args.campo}=?,updated_at=? WHERE id=?", (args.valor, utc_now(), args.documento))
        connection.execute(
            """INSERT INTO human_reviews
            (document_id,reviewer,reviewed_at,field_name,previous_value,corrected_value,notes,status)
            VALUES (?,?,?,?,?,?,?,'concluida')""",
            (args.documento, args.revisor, utc_now(), args.campo, str(previous or ""), args.valor, args.notas),
        )
        connection.commit()
        print(f"Revisão registrada: {args.documento}.{args.campo}: {previous!r} -> {args.valor!r}")
        print("Rode `relatorio-corpus` para atualizar os catálogos e consolidações.")
        return 0
    finally:
        connection.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m scripts.auditor_tcemg",
        description="Ingestão, busca e preparação de auditorias com jurisprudência local do TCE-MG.",
    )
    parser.add_argument("--verbose", action="store_true", help="Exibe logs detalhados.")
    sub = parser.add_subparsers(dest="command", required=True)

    diagnostic = sub.add_parser("diagnosticar", help="Inventaria formatos, hashes, duplicidades e amostra de extração; não altera originais.")
    diagnostic.add_argument("--entrada", type=Path, default=DEFAULT_INPUT)
    diagnostic.add_argument("--saida", type=Path, help="Grava também o diagnóstico em Markdown.")
    diagnostic.add_argument("--json", action="store_true", help="Saída JSON em vez de Markdown.")

    ingest_parser = sub.add_parser("ingerir", help="Processa incrementalmente o corpus e atualiza catálogos/FTS5.")
    ingest_parser.add_argument("--entrada", type=Path, default=DEFAULT_INPUT)
    ingest_parser.add_argument("--banco", type=Path, default=DATABASE_PATH)
    ingest_parser.add_argument("--limite", type=int, help="Processa somente amostra representativa de N arquivos.")
    ingest_parser.add_argument("--ocr", action="store_true", help="Tenta OCR apenas em PDFs sem texto; requer tesseract/pdftoppm.")
    ingest_parser.add_argument("--forcar", action="store_true", help="Reprocessa ocorrências mesmo com o mesmo hash.")
    ingest_parser.add_argument("--simular", action="store_true", help="Lista o que seria processado, sem gravar.")
    ingest_parser.add_argument("--sem-relatorios", action="store_true", help="Não regenera relatórios/consolidações ao final.")

    validate = sub.add_parser("validar", help="Valida integridade, páginas, citações, FTS5 e seleciona amostra humana.")
    validate.add_argument("--banco", type=Path, default=DATABASE_PATH)
    validate.add_argument("--amostra", type=int, default=10)
    validate.add_argument("--confirmacoes", type=Path, help="JSON com conferências humanas da amostra.")

    find = sub.add_parser("buscar", help="Busca FTS5/BM25 com filtros; retorna arquivo, página e trecho.")
    find.add_argument("--banco", type=Path, default=DATABASE_PATH)
    find.add_argument("--consulta", default="")
    find.add_argument("--processo", default="")
    find.add_argument("--tema", default="")
    find.add_argument("--regime", default="")
    find.add_argument("--relator", default="")
    find.add_argument("--municipio", default="")
    find.add_argument("--resultado", default="")
    find.add_argument("--objeto", default="")
    find.add_argument("--fundamento", default="")
    find.add_argument("--irregularidade", default="")
    find.add_argument("--artigo", default="")
    find.add_argument("--gravidade", default="")
    find.add_argument("--relevancia", default="")
    find.add_argument("--especie", default="")
    find.add_argument("--data-inicial", default="")
    find.add_argument("--data-final", default="")
    find.add_argument("--incluir-incidentais", action="store_true")
    find.add_argument("--limite", type=int, default=20)
    find.add_argument("--json", action="store_true")

    prepare = sub.add_parser("preparar-auditoria", help="Inventaria um processo e gera pacote jurisprudencial auditável.")
    prepare.add_argument("--processo", type=Path, required=True)
    prepare.add_argument("--saida", type=Path, required=True)
    prepare.add_argument("--banco", type=Path, default=DATABASE_PATH)
    prepare.add_argument("--limite-por-consulta", type=int, default=5)

    corpus_report = sub.add_parser("relatorio-corpus", help="Regenera catálogos, relatórios e consolidações do banco atual.")
    corpus_report.add_argument("--entrada", type=Path, default=DEFAULT_INPUT)
    corpus_report.add_argument("--banco", type=Path, default=DATABASE_PATH)

    reclassify = sub.add_parser("reclassificar", help="Recalcula relevância e fichas sem reextrair os PDFs.")
    reclassify.add_argument("--entrada", type=Path, default=DEFAULT_INPUT)
    reclassify.add_argument("--banco", type=Path, default=DATABASE_PATH)

    review = sub.add_parser("revisar", help="Registra correção humana de metadado com histórico.")
    review.add_argument("--banco", type=Path, default=DATABASE_PATH)
    review.add_argument("--documento", required=True)
    review.add_argument("--campo", required=True)
    review.add_argument("--valor", required=True)
    review.add_argument("--revisor", required=True)
    review.add_argument("--notas", default="")
    return parser


def main(argv: list[str] | None = None) -> int:
    _configure_streams()
    parser = build_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s %(message)s")
    try:
        if args.command == "diagnosticar":
            if not args.entrada.exists():
                raise FileNotFoundError(f"Entrada não encontrada: {args.entrada}")
            data = diagnose(args.entrada)
            text = _diagnostic_markdown(data)
            if args.saida:
                args.saida.parent.mkdir(parents=True, exist_ok=True)
                args.saida.write_text(text, encoding="utf-8")
            _json_print(data) if args.json else print(text, end="")
            return 0 if not data["failures"] else 1
        if args.command == "ingerir":
            if not args.entrada.exists():
                raise FileNotFoundError(f"Entrada não encontrada: {args.entrada}")
            result = ingest(
                args.entrada, database_path=args.banco, limit=args.limite, ocr=args.ocr,
                force=args.forcar, simulate=args.simular, generate_reports=not args.sem_relatorios,
            )
            _json_print(result)
            return 1 if result.get("errors") else 0
        if args.command == "validar":
            errors, warnings, stats = validate_database(args.banco, sample_size=args.amostra, confirmations_path=args.confirmacoes)
            for warning in warnings:
                print(f"[AVISO] {warning}")
            for error in errors:
                print(f"[ERRO] {error}", file=sys.stderr)
            _json_print(stats)
            return 1 if errors else 0
        if args.command == "buscar":
            connection = connect(args.banco)
            try:
                results = search(
                    connection,
                    query=args.consulta,
                    filters={
                        "processo": args.processo, "regime": args.regime, "relator": args.relator,
                        "municipio": args.municipio, "resultado": args.resultado,
                        "relevancia": args.relevancia, "especie": args.especie,
                        "objeto": args.objeto, "fundamento": args.fundamento,
                        "irregularidade": args.irregularidade, "artigo": args.artigo,
                        "gravidade": args.gravidade,
                    },
                    theme=args.tema, date_from=args.data_inicial, date_to=args.data_final,
                    include_incidental=args.incluir_incidentais, limit=args.limite,
                )
            finally:
                connection.close()
            _json_print(results) if args.json else _print_search(results)
            return 0
        if args.command == "preparar-auditoria":
            if not args.processo.exists():
                raise FileNotFoundError(f"Processo não encontrado: {args.processo}")
            result = prepare_audit_context(args.processo, args.saida, database_path=args.banco, limit_per_query=args.limite_por_consulta)
            _json_print(result)
            return 0
        if args.command == "relatorio-corpus":
            connection = connect(args.banco)
            try:
                write_all_reports(connection, args.entrada)
                stats = corpus_stats(connection)
            finally:
                connection.close()
            _json_print(stats)
            return 0
        if args.command == "reclassificar":
            result = reclassify_database(args.banco, input_root=args.entrada)
            _json_print(result)
            return 0
        if args.command == "revisar":
            return _review(args)
    except (OSError, sqlite3.Error, json.JSONDecodeError, ValueError) as exc:
        LOG.exception("Falha", exc_info=args.verbose)
        print(f"[ERRO] {exc}", file=sys.stderr)
        return 2
    parser.print_help()
    return 2
