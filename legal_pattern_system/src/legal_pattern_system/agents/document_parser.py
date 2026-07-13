from __future__ import annotations

from pathlib import Path
from typing import Protocol

from legal_pattern_system.models import LegalDocument
from legal_pattern_system.utils.section_parser import extract_bold_fields, parse_markdown_sections
from legal_pattern_system.utils.text_cleaning import clean_text


class DocumentParser(Protocol):
    """Parser adapter interface for Markdown now and PDF/DOCX/OCR later."""

    def parse(self, path: Path) -> LegalDocument:
        ...


class MarkdownDocumentParser:
    """Parse the challenge Markdown files into the normalized document model."""

    def parse(self, path: Path) -> LegalDocument:
        # Normalize common encoding artifacts before extracting fields. The
        # sample files contain mojibake such as "â‚¬" for "€", which is realistic
        # for document ingestion pipelines.
        raw_text = clean_text(path.read_text(encoding="utf-8"))
        title, sections = parse_markdown_sections(raw_text)

        # Metadata appears before the first horizontal rule in the sample files.
        metadata = extract_bold_fields(raw_text.split("---", 1)[0])
        parties: dict[str, dict[str, str]] = {}
        for section in sections:
            # Party blocks are structured as bold-label lines, so they can be
            # parsed without an LLM.
            if section.heading in {"PLAINTIFF", "DEFENDANT"}:
                parties[section.heading.lower()] = extract_bold_fields(section.content)

        return LegalDocument(
            source_path=path,
            document_type=path.parent.name,
            title=title,
            metadata=metadata,
            parties=parties,
            sections=sections,
            raw_text=raw_text,
        )


class FuturePdfLayoutParser:
    """Production adapter placeholder for PyMuPDF/pdfplumber or document AI output."""

    def parse(self, path: Path) -> LegalDocument:
        raise NotImplementedError("PDF layout parsing is a production adapter, not needed for Markdown samples.")


class FutureDocxParser:
    """Production adapter placeholder for python-docx or mammoth-based extraction."""

    def parse(self, path: Path) -> LegalDocument:
        raise NotImplementedError("DOCX parsing is a production adapter, not needed for Markdown samples.")
