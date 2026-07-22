from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Section:
    heading: str
    level: int
    content: str
    children: list["Section"] = field(default_factory=list)


@dataclass(frozen=True)
class LegalDocument:
    source_path: Path
    document_type: str
    title: str
    metadata: dict[str, str]
    parties: dict[str, dict[str, str]]
    sections: list[Section]
    raw_text: str

    def top_level_headings(self) -> list[str]:
        return [section.heading for section in self.sections]


@dataclass(frozen=True)
class FieldPattern:
    label: str
    values: list[str]
    stability: str
    confidence: float


@dataclass(frozen=True)
class SectionPattern:
    heading: str
    level: int
    occurrence_rate: float
    required: bool
    variants: list[str]
    representative_content: str


@dataclass(frozen=True)
class LearnedTemplate:
    document_type: str
    source_count: int
    title: str
    metadata_fields: list[FieldPattern]
    party_fields: dict[str, list[FieldPattern]]
    sections: list[SectionPattern]
    legal_citations: list[str]
    placeholders: list[str]
    required_sections: list[str]
    optional_sections: list[str]
    variable_fields: list[str]
    locked_legal_citations: list[str]
    confidence: float
    source_examples: list[str]
    notes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GeneratedDocument:
    document_type: str
    content: str
    used_placeholders: list[str]
    unresolved_placeholders: list[str]


@dataclass(frozen=True)
class QaFinding:
    severity: str
    message: str
    agent: str = "qa_agent"


@dataclass(frozen=True)
class QaReport:
    document_type: str
    score: float
    findings: list[QaFinding]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RetrievalChunk:
    chunk_id: str
    source_path: str
    heading: str
    text: str
    score: float


@dataclass(frozen=True)
class AgentStep:
    name: str
    purpose: str
    input_summary: str
    output_summary: str
    artifact_path: str | None = None


@dataclass(frozen=True)
class AgentRunReport:
    run_id: str
    document_type: str
    steps: list[AgentStep]
    retrieval_coverage: float
    initial_qa_score: float
    final_qa_score: float
    trace_dir: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
