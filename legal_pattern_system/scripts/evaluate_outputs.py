"""Evaluate an existing generated draft against a saved learned template."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    # Allows running the script without installing the package.
    sys.path.insert(0, str(SRC))

from legal_pattern_system.agents.qa_agent import QaAgent
from legal_pattern_system.models import FieldPattern, GeneratedDocument, LearnedTemplate, SectionPattern


def load_template(path: Path) -> LearnedTemplate:
    """Rehydrate a template JSON artifact into typed Python objects."""
    data = json.loads(path.read_text(encoding="utf-8"))
    return LearnedTemplate(
        document_type=data["document_type"],
        source_count=data["source_count"],
        title=data["title"],
        metadata_fields=[FieldPattern(**item) for item in data["metadata_fields"]],
        party_fields={
            party: [FieldPattern(**item) for item in fields]
            for party, fields in data["party_fields"].items()
        },
        sections=[SectionPattern(**item) for item in data["sections"]],
        legal_citations=data["legal_citations"],
        placeholders=data["placeholders"],
        required_sections=data.get("required_sections", []),
        optional_sections=data.get("optional_sections", []),
        variable_fields=data.get("variable_fields", data["placeholders"]),
        locked_legal_citations=data.get("locked_legal_citations", data["legal_citations"]),
        confidence=data.get("confidence", 0.0),
        source_examples=data.get("source_examples", []),
        notes=data["notes"],
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate a generated draft against a learned template.")
    parser.add_argument("--template", required=True, type=Path)
    parser.add_argument("--draft", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    template = load_template(args.template)
    # This wrapper lets QA operate on any Markdown draft, including one edited by
    # a human after initial generation.
    generated = GeneratedDocument(
        document_type=template.document_type,
        content=args.draft.read_text(encoding="utf-8"),
        used_placeholders=[],
        unresolved_placeholders=[],
    )
    report = QaAgent().evaluate(template, generated)
    args.output.write_text(json.dumps(report.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"QA score: {report.score}")
    print(f"QA report: {args.output}")


if __name__ == "__main__":
    main()
