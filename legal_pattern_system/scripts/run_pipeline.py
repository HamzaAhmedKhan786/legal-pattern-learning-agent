"""Run the full proof-of-concept workflow.

This script is the easiest entry point for reviewers. It learns a template from
one of the provided sample document folders, loads new-case details from the
examples folder, generates a draft, and writes all artifacts to the outputs
folder.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    # Keep the project dependency-free: no editable install is required to run
    # the scripts from a freshly unzipped submission.
    sys.path.insert(0, str(SRC))

from legal_pattern_system.agents.orchestrator import LegalPatternOrchestrator


CASE_DATA_FILES = {
    "dismissal_protection_suits": "dismissal_case_data.json",
    "claims_for_damages": "damages_case_data.json",
}


def main() -> None:
    # Choose which source document family to learn from. The values match the
    # folders provided in the challenge sample data.
    parser = argparse.ArgumentParser(description="Run the legal pattern learning prototype.")
    parser.add_argument("--doc-type", choices=sorted(CASE_DATA_FILES), default="dismissal_protection_suits")
    args = parser.parse_args()

    sample_dir = ROOT.parent / "sample_documents" / args.doc_type
    case_data_path = ROOT / "examples" / CASE_DATA_FILES[args.doc_type]
    output_dir = ROOT / "outputs"

    # The orchestrator owns the agent workflow: parse -> detect -> template ->
    # generate -> QA. The script only handles CLI input and artifact persistence.
    orchestrator = LegalPatternOrchestrator()
    template, documents = orchestrator.learn_template(sample_dir)
    case_data = json.loads(case_data_path.read_text(encoding="utf-8"))
    generated, qa_report = orchestrator.generate_and_evaluate(template, case_data)

    template_path = output_dir / "templates" / f"{args.doc_type}_template.json"
    generated_path = output_dir / "generated_documents" / f"{args.doc_type}_generated.md"
    qa_path = output_dir / "qa_reports" / f"{args.doc_type}_qa.json"

    # Persisting intermediate artifacts is important for reviewability. A lawyer,
    # engineer, or evaluator can inspect the learned template separately from the
    # generated draft and QA report.
    template_path.write_text(json.dumps(template.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    generated_path.write_text(generated.content, encoding="utf-8")
    qa_path.write_text(json.dumps(qa_report.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Parsed {len(documents)} source documents from {sample_dir}")
    print(f"Loaded case data from {case_data_path}")
    print(f"Template: {template_path}")
    print(f"Generated draft: {generated_path}")
    print(f"QA report: {qa_path}")
    print(f"QA score: {qa_report.score}")


if __name__ == "__main__":
    main()
