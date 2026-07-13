"""Run the full proof-of-concept workflow.

This script is the easiest entry point for reviewers. It learns a template from
one of the provided sample document folders, generates a draft from small demo
case data, and writes all artifacts to the outputs folder.
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


SAMPLE_CASES = {
    # Demo data for the end-to-end prototype. In production this would come from
    # a form, API request, case-management system, or uploaded intake file.
    "dismissal_protection_suits": {
        "case_no": "DPS-2024-999",
        "court": "Labor Court Berlin",
        "date_filed": "June 20, 2024",
        "plaintiff_name": "Example Employee",
        "plaintiff_address": "Example Street 1, 10115 Berlin, Germany",
        "plaintiff_employee_id": "EMP-2024-0999",
        "plaintiff_position": "Senior Product Manager",
        "plaintiff_department": "Product",
        "plaintiff_hire_date": "May 1, 2020",
        "defendant_company": "Example Employer GmbH",
        "defendant_address": "Employer Avenue 10, 10117 Berlin, Germany",
        "defendant_legal_representative": "Dr. Example Counsel",
        "defendant_hr_contact": "Example HR Director",
    },
    "claims_for_damages": {
        "case_no": "CFD-2024-999",
        "court": "District Court Berlin",
        "date_filed": "June 20, 2024",
        "plaintiff_name": "Example Claimant GmbH",
        "plaintiff_address": "Example Street 2, 10115 Berlin, Germany",
        "plaintiff_legal_representative": "CEO Example Representative",
        "plaintiff_registration": "HRB 99999 B, Amtsgericht Berlin-Charlottenburg",
        "defendant_name": "Example Defendant AG",
        "defendant_address": "Defendant Avenue 20, 10117 Berlin, Germany",
        "defendant_legal_representative": "Board of Directors",
        "defendant_registration": "HRB 88888 B, Amtsgericht Berlin-Charlottenburg",
        "total_damages": "€325,000",
    },
}


def main() -> None:
    # Choose which source document family to learn from. The values match the
    # folders provided in the challenge sample data.
    parser = argparse.ArgumentParser(description="Run the legal pattern learning prototype.")
    parser.add_argument("--doc-type", choices=sorted(SAMPLE_CASES), default="dismissal_protection_suits")
    args = parser.parse_args()

    sample_dir = ROOT.parent / "sample_documents" / args.doc_type
    output_dir = ROOT / "outputs"

    # The orchestrator owns the agent workflow: parse -> detect -> template ->
    # generate -> QA. The script only handles CLI input and artifact persistence.
    orchestrator = LegalPatternOrchestrator()
    template, documents = orchestrator.learn_template(sample_dir)
    generated, qa_report = orchestrator.generate_and_evaluate(template, SAMPLE_CASES[args.doc_type])

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
    print(f"Template: {template_path}")
    print(f"Generated draft: {generated_path}")
    print(f"QA report: {qa_path}")
    print(f"QA score: {qa_report.score}")


if __name__ == "__main__":
    main()
