"""Extração preservando páginas e conteúdo original."""
from __future__ import annotations

import hashlib
import html
import re
import shutil
import subprocess
import tempfile
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree as ET

from .config import SUPPORTED_EXTENSIONS


@dataclass(frozen=True)
class PageText:
    number: int
    text: str


@dataclass
class ExtractionResult:
    pages: list[PageText] = field(default_factory=list)
    status: str = "sucesso"
    needs_ocr: bool = False
    extractor: str = ""
    warnings: list[str] = field(default_factory=list)
    error: str = ""

    @property
    def total_chars(self) -> int:
        return sum(len(page.text) for page in self.pages)

    def as_marked_text(self) -> str:
        blocks = []
        for page in self.pages:
            blocks.append(f"<!-- pagina: {page.number} -->\n{page.text.rstrip()}\n")
        return "\n".join(blocks).rstrip() + ("\n" if blocks else "")


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest().upper()


def normalize_whitespace(text: str) -> str:
    """Normaliza espaços sem reescrever palavras ou pontuação jurídica."""
    text = text.replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")
    lines = [re.sub(r"[ \t\f\v]+", " ", line).rstrip() for line in text.split("\n")]
    out: list[str] = []
    blank = False
    for line in lines:
        if line.strip():
            out.append(line.strip())
            blank = False
        elif not blank:
            out.append("")
            blank = True
    return "\n".join(out).strip()


def _extract_pdf(path: Path) -> ExtractionResult:
    try:
        from pypdf import PdfReader
    except ImportError:
        return ExtractionResult(
            status="falha",
            extractor="indisponivel",
            error="Dependência pypdf ausente. Instale requirements-auditor.txt.",
        )
    try:
        reader = PdfReader(path, strict=False)
        pages: list[PageText] = []
        warnings: list[str] = []
        for number, page in enumerate(reader.pages, start=1):
            try:
                extracted = page.extract_text() or ""
            except Exception as exc:  # documento defeituoso não derruba o corpus
                extracted = ""
                warnings.append(f"Página {number}: falha de extração ({type(exc).__name__}: {exc}).")
            pages.append(PageText(number, normalize_whitespace(extracted)))
        useful = [len(p.text) for p in pages]
        total = sum(useful)
        empty_pages = sum(1 for size in useful if size < 20)
        needs_ocr = total < 100 or (bool(pages) and empty_pages / len(pages) > 0.80)
        status = "ocr_necessario" if needs_ocr else ("alerta" if warnings else "sucesso")
        if needs_ocr:
            warnings.append("PDF sem texto aproveitável; OCR opcional necessário.")
        return ExtractionResult(pages, status, needs_ocr, "pypdf", warnings)
    except Exception as exc:
        return ExtractionResult(status="falha", extractor="pypdf", error=f"{type(exc).__name__}: {exc}")


def _extract_docx(path: Path) -> ExtractionResult:
    try:
        with zipfile.ZipFile(path, "r") as archive:
            xml = archive.read("word/document.xml")
        root = ET.fromstring(xml)
        texts = [node.text or "" for node in root.iter() if node.tag.endswith("}t")]
        text = normalize_whitespace("\n".join(texts))
        return ExtractionResult([PageText(1, text)], "sucesso", False, "docx-stdlib")
    except Exception as exc:
        return ExtractionResult(status="falha", extractor="docx-stdlib", error=f"{type(exc).__name__}: {exc}")


def _extract_html(path: Path) -> ExtractionResult:
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
        raw = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", raw)
        raw = re.sub(r"(?s)<[^>]+>", "\n", raw)
        text = normalize_whitespace(html.unescape(raw))
        return ExtractionResult([PageText(1, text)], "sucesso", False, "html-stdlib")
    except OSError as exc:
        return ExtractionResult(status="falha", extractor="html-stdlib", error=str(exc))


def _extract_text(path: Path) -> ExtractionResult:
    try:
        text = normalize_whitespace(path.read_text(encoding="utf-8", errors="replace"))
        status = "ocr_necessario" if len(text) < 20 else "sucesso"
        return ExtractionResult([PageText(1, text)], status, status != "sucesso", "texto-utf8")
    except OSError as exc:
        return ExtractionResult(status="falha", extractor="texto-utf8", error=str(exc))


def _find_command(name: str) -> str | None:
    return shutil.which(name) or shutil.which(name + ".exe") or shutil.which(name + ".cmd")


def _ocr_pdf(path: Path, language: str = "por") -> ExtractionResult:
    """OCR opcional; nunca acionado sem ``ocr=True``."""
    tesseract = _find_command("tesseract")
    pdftoppm = _find_command("pdftoppm")
    if not tesseract or not pdftoppm:
        return ExtractionResult(
            status="ocr_indisponivel",
            needs_ocr=True,
            extractor="ocr",
            warnings=["OCR solicitado, mas tesseract e/ou pdftoppm não estão disponíveis."],
        )
    pages: list[PageText] = []
    try:
        with tempfile.TemporaryDirectory(prefix="auditor_tcemg_ocr_") as tmp:
            prefix = Path(tmp) / "page"
            render = subprocess.run(
                [pdftoppm, "-png", "-r", "200", str(path), str(prefix)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            if render.returncode != 0:
                raise RuntimeError(render.stderr.strip() or "pdftoppm falhou")
            images = sorted(Path(tmp).glob("page-*.png"))
            if not images:
                raise RuntimeError("pdftoppm não gerou páginas")
            for number, image in enumerate(images, start=1):
                proc = subprocess.run(
                    [tesseract, str(image), "stdout", "-l", language],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    check=False,
                )
                if proc.returncode != 0:
                    raise RuntimeError(proc.stderr.strip() or f"tesseract falhou na página {number}")
                pages.append(PageText(number, normalize_whitespace(proc.stdout)))
        return ExtractionResult(pages, "sucesso_ocr", False, "tesseract")
    except Exception as exc:
        return ExtractionResult(
            status="falha_ocr",
            needs_ocr=True,
            extractor="ocr",
            error=f"{type(exc).__name__}: {exc}",
        )


def extract_document(path: Path, *, ocr: bool = False) -> ExtractionResult:
    extension = path.suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        return ExtractionResult(status="formato_nao_suportado", error=f"Formato não suportado: {extension}")
    if extension == ".pdf":
        result = _extract_pdf(path)
        if result.needs_ocr and ocr:
            return _ocr_pdf(path)
        return result
    if extension == ".docx":
        return _extract_docx(path)
    if extension in {".html", ".htm"}:
        return _extract_html(path)
    return _extract_text(path)


def iter_supported_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            yield path
