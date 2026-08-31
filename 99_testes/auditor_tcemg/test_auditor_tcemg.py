from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pypdf import PdfWriter

from scripts.auditor_tcemg.database import (
    connect,
    corpus_stats,
    occurrence_is_current,
    search,
    upsert_document,
)
from scripts.auditor_tcemg.extractors import (
    ExtractionResult,
    PageText,
    _ocr_pdf,
    extract_document,
    sha256_file,
)
from scripts.auditor_tcemg.metadata import (
    analyze_document,
    identify_regime,
    normalize_process_number,
)
from scripts.auditor_tcemg.reports import build_ficha


class AuditorTCEMGTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.db_path = self.root / "auditor.sqlite3"
        self.connection = connect(self.db_path)

    def tearDown(self) -> None:
        self.connection.close()
        self.temp.cleanup()

    def _add(
        self,
        *,
        process: str,
        text: str,
        source: str,
        sha: str | None = None,
        relevance: str | None = None,
        date: str = "2025-01-15",
    ) -> dict:
        path = self.root / f"2025-01-15_Processo_{process}.txt"
        path.write_text(text, encoding="utf-8")
        extraction = extract_document(path)
        digest = sha or sha256_file(path)
        metadata = analyze_document(
            path,
            extraction,
            digest,
            {
                "processo": process,
                "sessao": "15/01/2025",
                "natureza": "DENÚNCIA",
                "colegiado": "PRIMEIRA CÂMARA",
                "relator": "CONS. TESTE",
            },
        )
        metadata["judgment_date"] = date
        if relevance:
            metadata["relevance"] = relevance
        upsert_document(
            self.connection,
            metadata=metadata,
            extraction=extraction,
            source_path=source,
            corpus="teste",
            file_format="txt",
            size_bytes=path.stat().st_size,
            text_path="texto.txt",
            ficha_path="",
        )
        return metadata

    def test_sha256(self) -> None:
        path = self.root / "a.txt"
        path.write_bytes(b"Charles")
        self.assertEqual(sha256_file(path), hashlib.sha256(b"Charles").hexdigest().upper())

    def test_normalizacao_numero_processo(self) -> None:
        self.assertEqual(normalize_process_number("Processo nº 001.104.833"), "1104833")
        self.assertEqual(normalize_process_number(None), "")

    def test_identificacao_regime_predominante(self) -> None:
        self.assertEqual(identify_regime("Lei nº 14.133/2021 " * 3 + " Lei 8.666/1993"), "lei-14133")
        self.assertEqual(identify_regime("Lei 8.666/1993"), "lei-8666")
        self.assertEqual(identify_regime("Lei 14.133/2021 e Lei 8.666/1993"), "transicao")

    def test_marcadores_de_pagina(self) -> None:
        result = ExtractionResult([PageText(1, "Primeira"), PageText(2, "Segunda")])
        marked = result.as_marked_text()
        self.assertIn("<!-- pagina: 1 -->", marked)
        self.assertIn("<!-- pagina: 2 -->", marked)

    def test_pdf_sem_texto_sinaliza_ocr(self) -> None:
        path = self.root / "blank.pdf"
        writer = PdfWriter()
        writer.add_blank_page(width=100, height=100)
        with path.open("wb") as stream:
            writer.write(stream)
        result = extract_document(path)
        self.assertTrue(result.needs_ocr)
        self.assertEqual(result.status, "ocr_necessario")

    def test_ocr_indisponivel_falha_controlada(self) -> None:
        path = self.root / "blank.pdf"
        path.write_bytes(b"%PDF-1.4\n%%EOF")
        with patch("scripts.auditor_tcemg.extractors._find_command", return_value=None):
            result = _ocr_pdf(path)
        self.assertEqual(result.status, "ocr_indisponivel")
        self.assertTrue(result.needs_ocr)

    def test_preserva_original(self) -> None:
        path = self.root / "original.txt"
        path.write_text("contratação direta", encoding="utf-8")
        before = sha256_file(path)
        extract_document(path)
        after = sha256_file(path)
        self.assertEqual(before, after)

    def test_idempotencia_por_caminho_e_hash(self) -> None:
        metadata = self._add(process="1100001", text="dispensa de licitação por valor", source="a/doc.txt")
        self.assertTrue(occurrence_is_current(self.connection, "a/doc.txt", metadata["sha256"]))
        count = self.connection.execute("SELECT COUNT(*) FROM occurrences").fetchone()[0]
        self.assertEqual(count, 1)

    def test_deteccao_de_duplicidade_por_hash(self) -> None:
        text = "contratação direta e pesquisa de preços"
        first = self._add(process="1100002", text=text, source="corpus-a/doc.txt")
        self._add(process="1100002", text=text, source="corpus-b/doc.txt", sha=first["sha256"])
        stats = corpus_stats(self.connection)
        self.assertEqual(stats["duplicate_groups"], 1)
        self.assertEqual(stats["duplicate_copies"], 1)
        self.assertEqual(stats["documents"], 1)

    def test_frontmatter_e_citacao(self) -> None:
        metadata = self._add(
            process="1100003",
            text="contratação direta. Dispensa de licitação. Pesquisa de preços.",
            source="corpus/doc.txt",
        )
        ficha = build_ficha(metadata, "corpus/doc.pdf")
        self.assertIn("tipo: jurisprudencia", ficha)
        self.assertIn("[Fonte: corpus/doc.pdf, p. 1]", ficha)
        self.assertIn("Não identificado no documento", ficha)

    def test_fts5_retorna_pagina_e_fonte(self) -> None:
        self._add(
            process="1100004",
            text="A pesquisa de preços deve ser documentada. Contratação direta. Dispensa de licitação.",
            source="corpus/precos.txt",
        )
        results = search(self.connection, query="pesquisa de preços", limit=5)
        self.assertEqual(results[0]["page_number"], 1)
        self.assertEqual(results[0]["source_path"], "corpus/precos.txt")

    def test_busca_por_tema(self) -> None:
        self._add(
            process="1100005",
            text="Houve fracionamento de despesas na contratação direta. Dispensa de licitação.",
            source="corpus/fracionamento.txt",
        )
        results = search(self.connection, theme="fracionamento", limit=5)
        self.assertEqual(results[0]["process_number"], "1100005")

    def test_filtro_temporal(self) -> None:
        self._add(process="1100006", text="contratação direta. dispensa de licitação.", source="a.txt", date="2024-01-01")
        self._add(process="1100007", text="contratação direta. dispensa de licitação.", source="b.txt", date="2026-01-01")
        results = search(self.connection, date_from="2025-01-01", limit=10)
        self.assertEqual({item["process_number"] for item in results}, {"1100007"})

    def test_filtro_por_regime(self) -> None:
        self._add(process="1100008", text="Lei 8.666/1993. contratação direta. dispensa de licitação.", source="old.txt")
        self._add(process="1100009", text="Lei 14.133/2021. contratação direta. dispensa de licitação.", source="new.txt")
        results = search(self.connection, filters={"regime": "lei-14133"}, limit=10)
        self.assertEqual({item["process_number"] for item in results}, {"1100009"})

    def test_filtros_objeto_artigo_e_gravidade(self) -> None:
        metadata = self._add(
            process="1100013",
            text="Contratação direta. Dispensa de licitação. Art. 72. Pesquisa de preços.",
            source="filtros.txt",
        )
        self.connection.execute(
            "UPDATE documents SET contract_object=? WHERE id=?",
            ("manutenção de áudio", metadata["id"]),
        )
        self.connection.execute(
            "INSERT INTO findings(document_id,page_number,evidence,category,severity) VALUES (?,?,?,?,?)",
            (metadata["id"], 1, "pesquisa", "pesquisa de preços", "alta"),
        )
        self.connection.commit()
        self.assertTrue(search(self.connection, filters={"objeto": "áudio"}, limit=5))
        self.assertTrue(search(self.connection, filters={"artigo": "72"}, limit=5))
        self.assertTrue(search(self.connection, filters={"gravidade": "alta"}, limit=5))

    def test_incidental_fora_da_busca_padrao(self) -> None:
        self._add(process="1100010", text="Apenas menção a dispensa de licitação.", source="incidental.txt", relevance="incidental")
        self.assertEqual(search(self.connection, query="dispensa de licitação", limit=5), [])
        self.assertTrue(search(self.connection, query="dispensa de licitação", include_incidental=True, limit=5))

    def test_recuperacao_preserva_trecho(self) -> None:
        phrase = "A justificativa do preço deve constar do processo."
        self._add(process="1100011", text=phrase + " Contratação direta. Dispensa de licitação.", source="evidencia.txt")
        result = search(self.connection, query="justificativa do preço", limit=1)[0]
        self.assertIn("justificativa", result["snippet"].lower())
        self.assertEqual(result["page_number"], 1)

    def test_ficha_deterministica_nao_duplica(self) -> None:
        metadata = self._add(process="1100012", text="contratação direta. dispensa de licitação.", source="det.txt")
        first = build_ficha(metadata, "det.pdf")
        second = build_ficha(metadata, "det.pdf")
        self.assertEqual(first, second)

    def test_cenarios_e_regras_anti_alucinacao_estao_documentados(self) -> None:
        root = Path(__file__).resolve().parents[2]
        checklist = (root / "07_checklists" / "roteiro-modo-auditor-contratacao-direta.md").read_text(encoding="utf-8")
        scenarios = (Path(__file__).parent / "cenarios_modo_auditor.yaml").read_text(encoding="utf-8")
        rules = checklist.split("## 10. Regras anti-alucinação", 1)[1].split("## 11.", 1)[0]
        self.assertEqual(sum(f"\n{number}. " in rules for number in range(1, 21)), 20)
        for expected in (
            "aumento_preco", "uma_proposta", "supressao_aviso", "fracionamento",
            "emergencia", "inexigibilidade", "documento_incompleto",
        ):
            self.assertIn(expected, scenarios.casefold())


if __name__ == "__main__":
    unittest.main()
