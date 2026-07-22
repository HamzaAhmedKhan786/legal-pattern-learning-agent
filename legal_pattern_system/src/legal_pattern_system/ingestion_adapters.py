from __future__ import annotations

from pathlib import Path

from legal_pattern_system.agents.document_parser import DocumentParser, FutureDocxParser, FuturePdfLayoutParser, MarkdownDocumentParser
from legal_pattern_system.models import LegalDocument


class UnsupportedIngestionFormat(ValueError):
    """Raised when no parser adapter exists for an uploaded document type."""


class IngestionRouter:
    """Route uploaded files to the right parser adapter.

    Markdown is implemented for the take-home data. PDF/DOCX/OCR adapters are
    explicit production extension points so web/API code can be wired without
    changing downstream agents.
    """

    def __init__(self) -> None:
        self._parsers: dict[str, DocumentParser] = {
            ".md": MarkdownDocumentParser(),
            ".markdown": MarkdownDocumentParser(),
            ".pdf": FuturePdfLayoutParser(),
            ".docx": FutureDocxParser(),
        }

    def parse(self, path: Path) -> LegalDocument:
        parser = self._parsers.get(path.suffix.lower())
        if parser is None:
            raise UnsupportedIngestionFormat(f"No parser configured for {path.suffix or 'unknown'} files.")
        return parser.parse(path)


class FutureOcrParser:
    """Production placeholder for scanned documents.

    Expected production design:
    - OCR text extraction
    - page layout reconstruction
    - confidence by page/span
    - source-span references for every extracted clause
    """

    def parse(self, path: Path) -> LegalDocument:
        raise NotImplementedError("OCR parsing is a production adapter and is not needed for Markdown samples.")
