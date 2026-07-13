from __future__ import annotations

from pathlib import Path
from typing import Any

from legal_pattern_system.agents.document_generator import DocumentGeneratorAgent
from legal_pattern_system.agents.document_parser import DocumentParser, MarkdownDocumentParser
from legal_pattern_system.agents.pattern_detector import PatternDetectorAgent
from legal_pattern_system.agents.qa_agent import QaAgent
from legal_pattern_system.agents.template_builder import TemplateBuilderAgent
from legal_pattern_system.models import GeneratedDocument, LearnedTemplate, LegalDocument, QaReport


class LegalPatternOrchestrator:
    """Coordinate agent execution for learning, generation, and QA."""

    def __init__(self, parser: DocumentParser | None = None) -> None:
        # Dependency injection keeps ingestion replaceable. Tests or production
        # code can provide a PDF/DOCX/OCR parser without changing the workflow.
        self.parser = parser or MarkdownDocumentParser()
        self.pattern_detector = PatternDetectorAgent()
        self.template_builder = TemplateBuilderAgent()
        self.generator = DocumentGeneratorAgent()
        self.qa = QaAgent()

    def learn_template(self, document_dir: Path) -> tuple[LearnedTemplate, list[LegalDocument]]:
        # Load every Markdown example in the selected document family. The system
        # learns from multiple examples, which is a key challenge requirement.
        documents = [self.parser.parse(path) for path in sorted(document_dir.glob("*.md"))]
        if not documents:
            raise ValueError(f"No Markdown documents found in {document_dir}")

        # Each downstream agent receives typed outputs from the previous step.
        # This makes communication explicit and avoids hidden shared state.
        metadata_fields, party_fields = self.pattern_detector.detect_field_patterns(documents)
        sections = self.pattern_detector.detect_section_patterns(documents)
        citations = self.pattern_detector.detect_legal_citations(documents)
        template = self.template_builder.build(documents, metadata_fields, party_fields, sections, citations)
        return template, documents

    def generate_and_evaluate(self, template: LearnedTemplate, case_data: dict[str, Any]) -> tuple[GeneratedDocument, QaReport]:
        # Generation and QA are intentionally separate agents so disagreement can
        # be surfaced instead of hidden inside one drafting step.
        generated = self.generator.generate(template, case_data)
        report = self.qa.evaluate(template, generated)
        return generated, report
