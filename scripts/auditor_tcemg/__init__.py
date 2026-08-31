"""Pipeline local do Modo Auditor de contratações diretas do TCE-MG."""

from .extractors import ExtractionResult, PageText, extract_document, sha256_file
from .metadata import analyze_document, normalize_process_number

__all__ = [
    "ExtractionResult",
    "PageText",
    "analyze_document",
    "extract_document",
    "normalize_process_number",
    "sha256_file",
]

__version__ = "1.0.0"
