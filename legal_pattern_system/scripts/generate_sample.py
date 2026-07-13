"""Generate a document from a saved template and a case-data JSON file.

This script demonstrates how the learned template can be reused after the
learning step. It is intentionally thin: loading, rendering, and saving are kept
separate from the generator agent's actual drafting logic.
"""

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

from legal_pattern_system.agents.document_generator import DocumentGeneratorAgent
from legal_pattern_system.models import FieldPattern, LearnedTemplate, SectionPattern


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
    # Required inputs are explicit so the script can be used with any learned
    # template and any compatible case-data JSON.
    parser = argparse.ArgumentParser(description="Generate a draft from a learned template and case-data JSON.")
    parser.add_argument("--template", required=True, type=Path)
    parser.add_argument("--case-data", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    template = load_template(args.template)
    case_data = json.loads(args.case_data.read_text(encoding="utf-8"))
    # The generator fills known fields and leaves unresolved placeholders visible
    # for QA/human review instead of silently dropping missing data.
    generated = DocumentGeneratorAgent().generate(template, case_data)
    args.output.write_text(generated.content, encoding="utf-8")
    print(f"Generated draft: {args.output}")


if __name__ == "__main__":
    main()
