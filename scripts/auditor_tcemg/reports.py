"""Fichas, catálogos, consolidações e relatórios auditáveis."""
from __future__ import annotations

import csv
import json
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from .config import (
    CATALOG_CSV,
    CATALOG_JSONL,
    CONSOLIDATIONS_DIR,
    DEFAULT_OUTPUT,
    FICHAS_DIR,
    NOT_IDENTIFIED,
    ORIGINALS_MANIFEST_JSONL,
    RAW_REFERENCE_DIR,
    REPORTS_DIR,
    REPO_ROOT,
    TODAY,
)
from .database import catalog_rows, corpus_stats


def relative_to_repo(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def ensure_output_structure(input_root: Path) -> None:
    for directory in (
        RAW_REFERENCE_DIR,
        DEFAULT_OUTPUT / "texto_extraido",
        FICHAS_DIR,
        DEFAULT_OUTPUT / "indices",
        CONSOLIDATIONS_DIR,
        REPORTS_DIR,
    ):
        directory.mkdir(parents=True, exist_ok=True)
    readme = RAW_REFERENCE_DIR / "README.md"
    if not readme.exists():
        readme.write_text(
            """---
tipo: checklist
hierarquia: operacional
tema: camada bruta da jurisprudencia tce-mg
fonte: base Charles
vigencia: vigente
atualizado_em: 2026-07-31
tags: [tce-mg, originais, preservacao, sha256]
---

# Camada documental bruta

Os arquivos originais permanecem, sem alteração, em `TCE-MG_JULGADOS/`. Este diretório é uma
ponte de governança: o manifesto, o catálogo e a tabela `occurrences` do SQLite associam cada
original ao SHA-256 e ao documento processado. O pipeline não move, não sobrescreve e não exclui
originais. A ausência de cópia aqui evita duplicar aproximadamente 445 MB de PDFs.
""",
            encoding="utf-8",
        )


def _yaml(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def build_ficha(metadata: dict[str, Any], source_path: str) -> str:
    process = metadata.get("process_number") or NOT_IDENTIFIED
    source = source_path.replace("\\", "/")
    page_one_citation = f"[Fonte: {source}, p. 1]"
    excerpts = metadata.get("excerpts", [])
    excerpt_lines = []
    for excerpt in excerpts:
        excerpt_lines.append(
            f"> {excerpt['text']}\n>\n> [Fonte: {source}, p. {excerpt['page']}]"
        )
    if not excerpt_lines:
        excerpt_lines = ["Não identificado no documento. A extração não forneceu trecho pertinente com página."]
    official_summary = metadata.get("official_summary") or NOT_IDENTIFIED
    if official_summary != NOT_IDENTIFIED:
        summary_source = (
            f"[Fonte: {source}, p. 1]"
            if metadata.get("official_summary_source") == "pdf_pagina_1"
            else f"[Fonte auxiliar: {metadata.get('index_metadata', {}).get('_index_file', 'índice do corpus')}, registro do processo {process}]"
        )
        official_summary_block = (
            f"**Ementa/registro oficial do índice (não substitui a leitura do inteiro teor):** "
            f"{official_summary} {summary_source}"
        )
    else:
        official_summary_block = NOT_IDENTIFIED
    themes = [item["theme"] for item in metadata.get("themes", [])]
    return f"""---
tipo: jurisprudencia
hierarquia: persuasiva
tema: contratacao direta
subtemas: {_yaml(themes)}
fonte: Tribunal de Contas do Estado de Minas Gerais
processo: {_yaml(process)}
relator: {_yaml(metadata.get('rapporteur', NOT_IDENTIFIED))}
orgao_julgador: {_yaml(metadata.get('judging_body', NOT_IDENTIFIED))}
data_julgamento: {_yaml(metadata.get('judgment_date', NOT_IDENTIFIED))}
regime_legal: {_yaml(metadata.get('legal_regime', 'nao-identificado'))}
relevancia: {_yaml(metadata.get('relevance', 'pendente_revisao'))}
status_precedente: verificar
vigencia: vigente
atualizado_em: {TODAY}
arquivo_original: {_yaml(source)}
sha256: {_yaml(metadata.get('sha256', ''))}
tags: {_yaml(['tce-mg', 'contratacao-direta', *themes[:8]])}
---

# Processo nº {process}

> **Status:** ficha gerada por extração/triagem mecânica. Exige conferência humana contra o
> inteiro teor antes de sustentar conclusão jurídica. Campos não confirmados não foram completados.

## 1. Identificação

- Processo: {process} {page_one_citation}
- Natureza/classe: {metadata.get('process_nature', NOT_IDENTIFIED)} {page_one_citation}
- Relator: {metadata.get('rapporteur', NOT_IDENTIFIED)} {page_one_citation}
- Órgão julgador: {metadata.get('judging_body', NOT_IDENTIFIED)} {page_one_citation}
- Data: {metadata.get('judgment_date', NOT_IDENTIFIED)} {page_one_citation}
- Regime detectado: {metadata.get('legal_regime', 'nao-identificado')} (triagem mecânica; conferir o caso).

## 2. Contexto fático

**Fato confirmado no inteiro teor:** {metadata.get('main_facts', NOT_IDENTIFIED)}

{official_summary_block}

## 3. Questão analisada

{NOT_IDENTIFIED}. A presença dos temas {', '.join(themes) if themes else 'não identificados'} é
triagem textual, não formulação jurídica definitiva.

## 4. Irregularidades apontadas

{metadata.get('recognized_irregularities', NOT_IDENTIFIED)}

## 5. Argumentos da defesa

{metadata.get('defense_arguments', NOT_IDENTIFIED)}

## 6. Fundamentos do voto

{metadata.get('vote_grounds', NOT_IDENTIFIED)}

## 7. Decisão

**Resultado mecanicamente localizado:** {metadata.get('judgment_result', NOT_IDENTIFIED)}.
Não confundir esse recorte com a decisão colegiada completa; conferir o dispositivo no inteiro teor.

## 8. Tese extraída

{metadata.get('extractable_thesis', NOT_IDENTIFIED)} {page_one_citation}. Não foi criada tese por inferência automática.

## 9. Condutas consideradas adequadas

{NOT_IDENTIFIED}

## 10. Condutas consideradas inadequadas

{NOT_IDENTIFIED}

## 11. Aplicação prática para a Câmara de Itanhandu

**Interpretação do Charles — pendente de validação humana:** o julgado foi recuperado pelos temas
{', '.join(themes) if themes else 'não identificados'}. Sua pertinência depende da comparação dos
fatos, do regime legal e da decisão efetivamente vencedora; a triagem não autoriza transplante automático.

## 12. Limites de aplicação do precedente

- Relevância mecânica: {metadata.get('relevance')} — {metadata.get('relevance_reason')}.
- Nível de confiança da extração: {metadata.get('confidence')}.
- Não foi verificado automaticamente se há voto vencido, peculiaridade fática determinante ou superação.

## 13. Regime legal e compatibilidade com a Lei nº 14.133/2021

Regime detectado: **{metadata.get('legal_regime', 'nao-identificado')}**. A compatibilidade com o
regime atual não foi presumida. Precedente da Lei nº 8.666/1993 exige comparação expressa com a
legislação atual existente na base antes do uso.

## 14. Trechos relevantes

{chr(10).join(excerpt_lines)}

## 15. Riscos e cautelas

- Não tratar alegação técnica, defesa, manifestação do MPC ou voto vencido como decisão do Tribunal.
- Não usar a ementa como substituta do inteiro teor.
- Conferir as páginas citadas e registrar correções em revisão humana.

## 16. Fontes e páginas utilizadas

- `{source}` — páginas {', '.join(str(item['page']) for item in excerpts) if excerpts else 'não identificadas'}.
- `{metadata.get('index_metadata', {}).get('_index_file', 'índice do corpus')}` — metadados auxiliares; sem paginação.
"""


def write_ficha(metadata: dict[str, Any], source_path: str) -> str:
    FICHAS_DIR.mkdir(parents=True, exist_ok=True)
    path = FICHAS_DIR / f"{metadata['id']}.md"
    if metadata.get("relevance") not in {"direta", "parcial"}:
        if path.exists():
            path.unlink()
        return ""
    path.write_text(build_ficha(metadata, source_path), encoding="utf-8")
    return relative_to_repo(path)


CATALOG_COLUMNS = [
    "id", "sha256", "process_number", "process_year", "process_nature", "judging_body",
    "rapporteur", "judgment_date", "publication_date", "entity", "municipality", "legal_regime",
    "direct_contract_type", "legal_basis", "contract_object", "contract_value", "judgment_result",
    "relevance", "relevance_score", "confidence", "extraction_status", "needs_ocr", "page_count",
    "total_chars", "canonical_source_path", "text_path", "ficha_path", "themes", "legal_provisions",
    "source_paths", "review_notes",
]


def write_catalogs(connection: sqlite3.Connection) -> None:
    rows = catalog_rows(connection)
    CATALOG_JSONL.parent.mkdir(parents=True, exist_ok=True)
    with CATALOG_JSONL.open("w", encoding="utf-8", newline="\n") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    with CATALOG_CSV.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=CATALOG_COLUMNS, delimiter=";")
        writer.writeheader()
        for row in rows:
            output = {}
            for column in CATALOG_COLUMNS:
                value = row.get(column, "")
                output[column] = " | ".join(str(item) for item in value) if isinstance(value, list) else value
            writer.writerow(output)

    occurrences = connection.execute(
        """SELECT o.source_path,o.corpus,o.sha256,o.size_bytes,d.format AS file_format,o.document_id,
                  o.first_seen_at,o.last_seen_at,d.process_number,d.canonical_source_path
           FROM occurrences o JOIN documents d ON d.id=o.document_id
           ORDER BY o.source_path"""
    ).fetchall()
    with ORIGINALS_MANIFEST_JSONL.open("w", encoding="utf-8", newline="\n") as stream:
        for occurrence in occurrences:
            stream.write(json.dumps(dict(occurrence), ensure_ascii=False, sort_keys=True) + "\n")


def _frontmatter(title: str, tags: list[str]) -> str:
    return f"""---
tipo: checklist
hierarquia: operacional
tema: {title}
fonte: corpus local TCE-MG / processamento mecânico do Charles
vigencia: vigente
atualizado_em: {TODAY}
tags: {_yaml(tags)}
---

"""


def write_processing_reports(connection: sqlite3.Connection, input_root: Path) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    stats = corpus_stats(connection)
    rows = catalog_rows(connection)
    report = _frontmatter("relatorio de processamento tce-mg", ["tce-mg", "processamento", "auditor"]) + f"""# RELATÓRIO DE PROCESSAMENTO

- Entrada bruta: `{relative_to_repo(input_root)}`
- Ocorrências inventariadas: **{stats['occurrences']}**
- Documentos lógicos: **{stats['documents']}**
- Hashes únicos: **{stats['unique_hashes']}**
- Páginas extraídas: **{stats['pages']}**
- Falhas: **{stats['failures']}**
- OCR necessário: **{stats['needs_ocr']}**
- Grupos duplicados: **{stats['duplicate_groups']}** ({stats['duplicate_copies']} cópias excedentes)
- Fichas relevantes: **{stats['fichas']}**
- Relevância: `{json.dumps(stats['relevance'], ensure_ascii=False)}`
- Status: `{json.dumps(stats['statuses'], ensure_ascii=False)}`

Os originais não foram movidos nem sobrescritos. A associação é feita por caminho relativo e SHA-256.
"""
    (REPORTS_DIR / "RELATORIO_PROCESSAMENTO.md").write_text(report, encoding="utf-8")

    failures = [row for row in rows if str(row.get("extraction_status", "")).startswith("falha") or row.get("extraction_status") == "formato_nao_suportado"]
    text = _frontmatter("documentos com falha", ["tce-mg", "falhas"]) + "# DOCUMENTOS COM FALHA\n\n"
    text += "Nenhum documento com falha.\n" if not failures else "\n".join(
        f"- `{row['canonical_source_path']}` — {row['extraction_status']}: {row.get('error') or 'sem detalhe'}" for row in failures
    ) + "\n"
    (REPORTS_DIR / "DOCUMENTOS_COM_FALHA.md").write_text(text, encoding="utf-8")

    pending = [row for row in rows if row.get("needs_ocr") or row.get("relevance") in {"pendente_revisao", "incidental"} or row.get("confidence") == "baixa"]
    text = _frontmatter("documentos pendentes de revisao", ["tce-mg", "revisao-humana"]) + "# DOCUMENTOS PENDENTES DE REVISÃO\n\n"
    text += "Nenhum documento pendente.\n" if not pending else "\n".join(
        f"- `{row['canonical_source_path']}` — processo {row['process_number']}; relevância {row['relevance']}; extração {row['extraction_status']}." for row in pending
    ) + "\n"
    (REPORTS_DIR / "DOCUMENTOS_PENDENTES_REVISAO.md").write_text(text, encoding="utf-8")

    groups = connection.execute(
        "SELECT sha256,COUNT(*) c FROM occurrences GROUP BY sha256 HAVING COUNT(*)>1 ORDER BY c DESC,sha256"
    ).fetchall()
    lines = [_frontmatter("duplicidades identificadas", ["tce-mg", "sha256", "duplicidades"]), "# DUPLICIDADES IDENTIFICADAS", ""]
    if not groups:
        lines.append("Nenhuma duplicidade exata por SHA-256.")
    for group in groups:
        lines.append(f"## {group['sha256']} — {group['c']} ocorrências")
        lines.append("")
        for occurrence in connection.execute(
            "SELECT source_path,document_id FROM occurrences WHERE sha256=? ORDER BY source_path", (group["sha256"],)
        ):
            lines.append(f"- `{occurrence['source_path']}` → `{occurrence['document_id']}`")
        lines.append("")
    lines.append("> Mesmo hash com números de processo distintos não foi colapsado como equivalência jurídica; exige revisão humana.")
    (REPORTS_DIR / "DUPLICIDADES_IDENTIFICADAS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _source_citation(row: dict[str, Any], page: int | None = None) -> str:
    p = page or 1
    return f"[Fonte: {row['canonical_source_path']}, p. {p}]"


def write_consolidations(connection: sqlite3.Connection) -> None:
    CONSOLIDATIONS_DIR.mkdir(parents=True, exist_ok=True)
    rows = [row for row in catalog_rows(connection) if row.get("relevance") in {"direta", "parcial"}]
    by_theme: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        for theme in row.get("themes", []):
            by_theme[theme].append(row)

    lines = [_frontmatter("teses consolidadas", ["tce-mg", "teses", "revisao-humana"]), "# TESES CONSOLIDADAS", "", "> Não há consolidação jurídica automática. Abaixo estão ementas oficiais/indicadores recuperados, que exigem leitura do inteiro teor e validação humana.", ""]
    for theme, items in sorted(by_theme.items()):
        lines.append(f"## {theme}")
        lines.append("")
        for row in items[:10]:
            summary = row.get("official_summary")
            if summary and summary != NOT_IDENTIFIED:
                lines.append(f"- Processo {row['process_number']} ({row['legal_regime']}): {summary} {_source_citation(row)}")
            else:
                lines.append(f"- Processo {row['process_number']}: tese não identificada automaticamente. {_source_citation(row)}")
        lines.append("")
    (CONSOLIDATIONS_DIR / "TESES_CONSOLIDADAS.md").write_text("\n".join(lines), encoding="utf-8")

    matrix = [_frontmatter("matriz de riscos tce-mg", ["tce-mg", "riscos"]), "# MATRIZ DE RISCOS TCE-MG", "", "| Tema | Julgados recuperados | Evidências exemplificativas | Status |", "|---|---:|---|---|"]
    for theme, items in sorted(by_theme.items(), key=lambda pair: (-len(pair[1]), pair[0])):
        evidence = "; ".join(f"proc. {row['process_number']} {_source_citation(row)}" for row in items[:3])
        matrix.append(f"| {theme} | {len(items)} | {evidence} | Triagem; gravidade depende do caso concreto |")
    (CONSOLIDATIONS_DIR / "MATRIZ_RISCOS_TCE_MG.md").write_text("\n".join(matrix) + "\n", encoding="utf-8")

    irregular = [_frontmatter("irregularidades recorrentes", ["tce-mg", "irregularidades"]), "# IRREGULARIDADES RECORRENTES", "", "> Contagem de temas/termos, não reconhecimento automático de irregularidade. Conferir decisão e contraditório.", ""]
    for theme, items in sorted(by_theme.items(), key=lambda pair: (-len(pair[1]), pair[0])):
        irregular.append(f"- **{theme}** — {len(items)} julgado(s) recuperado(s); exemplos: " + ", ".join(f"{r['process_number']} ({r['canonical_source_path']}, p. 1)" for r in items[:5]))
    (CONSOLIDATIONS_DIR / "IRREGULARIDADES_RECORRENTES.md").write_text("\n".join(irregular) + "\n", encoding="utf-8")

    good = _frontmatter("boas praticas reconhecidas", ["tce-mg", "boas-praticas"]) + """# BOAS PRÁTICAS RECONHECIDAS

Não foram consolidadas boas práticas automaticamente. Essa classificação exige distinguir fato,
unidade técnica, defesa, voto e decisão colegiada. Use `TESES_CONSOLIDADAS.md` apenas como fila de
revisão e registre cada boa prática com processo, página e trecho após conferência humana.
"""
    (CONSOLIDATIONS_DIR / "BOAS_PRATICAS_RECONHECIDAS.md").write_text(good, encoding="utf-8")

    divergences = [_frontmatter("divergencias jurisprudenciais", ["tce-mg", "divergencias"]), "# DIVERGÊNCIAS JURISPRUDENCIAIS", "", "> Não transformar coexistência de julgados em divergência nem em consenso sem análise humana.", ""]
    for theme, items in sorted(by_theme.items()):
        regimes = sorted({row["legal_regime"] for row in items})
        if len(items) >= 2 and len(regimes) >= 2:
            divergences.append(f"- **{theme}** — revisão necessária entre regimes {', '.join(regimes)}: " + ", ".join(f"proc. {row['process_number']} ({row['judgment_date']})" for row in items[:8]))
    divergences.append("\nA posição mais recente e a existência de consolidação permanecem pendentes de validação humana.")
    (CONSOLIDATIONS_DIR / "DIVERGENCIAS_JURISPRUDENCIAIS.md").write_text("\n".join(divergences) + "\n", encoding="utf-8")

    years = Counter(row.get("process_year") for row in rows)
    evolution = [_frontmatter("evolucao temporal dos entendimentos", ["tce-mg", "evolucao-temporal"]), "# EVOLUÇÃO TEMPORAL DOS ENTENDIMENTOS", "", "> Frequência documental não equivale a mudança de entendimento.", "", "| Ano | Julgados relevantes recuperados |", "|---|---:|"]
    evolution.extend(f"| {year} | {count} |" for year, count in sorted(years.items()))
    (CONSOLIDATIONS_DIR / "EVOLUCAO_TEMPORAL_ENTENDIMENTOS.md").write_text("\n".join(evolution) + "\n", encoding="utf-8")

    regimes = Counter(row.get("legal_regime") for row in rows)
    compare = [_frontmatter("entendimentos lei 8666 versus lei 14133", ["tce-mg", "regime-legal"]), "# ENTENDIMENTOS — LEI 8.666 VERSUS LEI 14.133", "", "| Regime detectado | Documentos |", "|---|---:|"]
    compare.extend(f"| {regime} | {count} |" for regime, count in sorted(regimes.items()))
    compare += ["", "Precedente da Lei nº 8.666/1993 não é aplicado automaticamente à Lei nº 14.133/2021. A identidade de princípio, o dispositivo atual e os limites de transplante devem ser explicitados no relatório de auditoria."]
    (CONSOLIDATIONS_DIR / "ENTENDIMENTOS_LEI_8666_VERSUS_LEI_14133.md").write_text("\n".join(compare) + "\n", encoding="utf-8")

    thematic = [_frontmatter("mapa tematico contratacao direta", ["tce-mg", "mapa-tematico"]), "# MAPA TEMÁTICO — CONTRATAÇÃO DIRETA", ""]
    for theme, items in sorted(by_theme.items(), key=lambda pair: (-len(pair[1]), pair[0])):
        thematic.append(f"## {theme} ({len(items)})")
        thematic.append("")
        thematic.extend(f"- Processo {row['process_number']} — `{row['ficha_path'] or row['canonical_source_path']}`" for row in items[:20])
        thematic.append("")
    (CONSOLIDATIONS_DIR / "MAPA_TEMATICO_CONTRATACAO_DIRETA.md").write_text("\n".join(thematic), encoding="utf-8")


def write_all_reports(connection: sqlite3.Connection, input_root: Path) -> None:
    write_catalogs(connection)
    write_processing_reports(connection, input_root)
    write_consolidations(connection)
