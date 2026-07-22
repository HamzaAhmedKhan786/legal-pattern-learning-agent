"""Build a backend reference library for all document types shown in the UI.

The frontend displays a broad German-law drafting taxonomy. This script creates
prototype reference data for every listed template so the backend can expose the
same catalog instead of only knowing the two challenge families. The generated
examples are intentionally synthetic and marked for lawyer review.
"""

from __future__ import annotations

import json
from pathlib import Path


CATALOG = [
    ("Employment Law", "Arbeitsrecht", [
        "Dismissal Protection Suit", "Warning Letter", "Response to Warning", "Employment Contract",
        "Amendment Agreement", "Settlement Agreement", "Termination Agreement", "Employer Notice of Termination",
        "Employee Resignation", "Salary Claim", "Overtime Claim", "Vacation Compensation Claim",
        "Employment Certificate Request", "Temporary Injunction", "Appeal",
    ]),
    ("Civil Law", "Zivilrecht", [
        "Claim for Damages", "Payment Claim", "Contract Breach Claim", "Debt Collection Claim", "Loan Recovery",
        "Warranty Claim", "Consumer Complaint", "Contract Rescission", "Contract Cancellation", "Demand Letter",
    ]),
    ("Commercial / Corporate Law", "Handels- und Gesellschaftsrecht", [
        "Shareholder Resolution", "Partnership Agreement", "NDA", "Service Agreement", "Software Agreement",
        "Licensing Agreement", "Supplier Agreement", "Distribution Agreement", "Purchase Agreement",
        "Commercial Litigation",
    ]),
    ("Family Law", "Familienrecht", [
        "Divorce Petition", "Child Custody Petition", "Child Support Claim", "Spousal Maintenance",
        "Property Division", "Adoption Application", "Name Change Application",
    ]),
    ("Real Estate", "Immobilienrecht", [
        "Lease Agreement", "Eviction Action", "Rent Increase Notice", "Security Deposit Claim",
        "Property Purchase Agreement", "Construction Dispute",
    ]),
    ("Criminal Law", "Strafrecht", [
        "Criminal Complaint", "Defense Statement", "Appeal", "Witness Statement", "Bail Application",
    ]),
    ("Administrative Law", "Verwaltungsrecht", [
        "Visa Appeal", "Residence Permit Appeal", "Tax Appeal", "Building Permit Appeal", "Social Benefits Appeal",
    ]),
    ("Intellectual Property", "IP-Recht", [
        "Trademark Registration", "Patent Application", "Copyright Infringement", "Cease and Desist Letter",
        "Licensing Agreement",
    ]),
    ("Data Privacy / GDPR", "Datenschutzrecht", [
        "GDPR Complaint", "Data Deletion Request", "Subject Access Request", "Privacy Policy",
        "Data Processing Agreement",
    ]),
    ("Banking / Finance", "Bank- und Finanzrecht", [
        "Loan Agreement", "Guarantee", "Debt Settlement", "Insurance Claim", "Investment Dispute",
    ]),
]

RUNNABLE = {
    ("Employment Law", "Dismissal Protection Suit"): "challenge-dismissal",
    ("Civil Law", "Claim for Damages"): "challenge-damages",
    ("Commercial / Corporate Law", "Commercial Litigation"): "commercial-damages",
}


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    output_path = root / "reference_data" / "legal_document_sample_library.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(build_library(), indent=2, ensure_ascii=False), encoding="utf-8")
    print(output_path)


def build_library() -> dict[str, object]:
    practice_areas = []
    templates = []
    for area_index, (area, german, documents) in enumerate(CATALOG, start=1):
        practice_areas.append({"area": area, "german": german, "documents": documents})
        for document_index, document_type in enumerate(documents, start=1):
            template_id = _slug(f"{area}-{document_type}")
            fields = _fields_for(area, document_type)
            sample_case = _sample_case(area, document_type, fields, area_index, document_index)
            templates.append(
                {
                    "id": template_id,
                    "practice_area": area,
                    "german_area": german,
                    "document_type": document_type,
                    "status": "runnable" if (area, document_type) in RUNNABLE else "reference",
                    "sample_pack_id": RUNNABLE.get((area, document_type)),
                    "required_fields": [field for field in fields if field["required"]],
                    "optional_fields": [field for field in fields if not field["required"]],
                    "sample_case_data": sample_case,
                    "sample_source_document": _sample_source_document(area, document_type, sample_case),
                    "lawyer_review_required": True,
                    "data_note": "Synthetic prototype reference data generated for UI/backend alignment; not legal advice.",
                }
            )
    return {
        "version": "2026-07-22",
        "source": "Generated from the frontend legal document taxonomy for prototype reference usage.",
        "practice_areas": practice_areas,
        "templates": templates,
    }


def _fields_for(area: str, document_type: str) -> list[dict[str, object]]:
    base = [
        {"key": "matter_no", "label": "Matter number", "required": True},
        {"key": "jurisdiction", "label": "Court or forum", "required": True},
        {"key": "draft_date", "label": "Draft date", "required": True},
        {"key": "client_name", "label": "Client name", "required": True},
        {"key": "client_address", "label": "Client address", "required": False},
        {"key": "opposing_party", "label": "Opposing party", "required": True},
        {"key": "opposing_party_address", "label": "Opposing party address", "required": False},
        {"key": "matter_summary", "label": "Matter summary", "required": True},
        {"key": "requested_outcome", "label": "Requested outcome", "required": True},
        {"key": "supporting_evidence", "label": "Supporting evidence", "required": False},
        {"key": "reviewer_notes", "label": "Reviewer notes", "required": False},
    ]
    if area == "Employment Law":
        base.insert(5, {"key": "employment_start_date", "label": "Employment start date", "required": False})
        base.insert(6, {"key": "employee_position", "label": "Employee position", "required": False})
    if "Damages" in document_type or "Claim" in document_type or area == "Banking / Finance":
        base.insert(8, {"key": "amount_claimed", "label": "Amount claimed", "required": "Claim" in document_type or "Damages" in document_type})
    if area in {"Commercial / Corporate Law", "Data Privacy / GDPR", "Intellectual Property"}:
        base.append({"key": "registration_or_identifier", "label": "Registration or identifier", "required": False})
    return base


def _sample_case(area: str, document_type: str, fields: list[dict[str, object]], area_index: int, document_index: int) -> dict[str, str]:
    slug = _slug(document_type).replace("_", "-").upper()[:12]
    values = {
        "matter_no": f"{slug}-{area_index:02d}{document_index:02d}-001",
        "jurisdiction": _default_forum(area),
        "draft_date": "2026-07-22",
        "client_name": f"Sample Client {document_index} GmbH",
        "client_address": "Sample Client Street 10, 10115 Berlin, Germany",
        "opposing_party": f"Sample Opposing Party {document_index} AG",
        "opposing_party_address": "Opposing Party Avenue 20, 10117 Berlin, Germany",
        "matter_summary": f"Synthetic {document_type} example for {area}. Replace with verified matter facts before drafting.",
        "requested_outcome": f"Prepare a lawyer-reviewed {document_type} draft with clear facts, legal basis, and requested relief.",
        "supporting_evidence": "Contract, correspondence, notices, invoices, witness notes, and reviewer-approved exhibits.",
        "reviewer_notes": "Confirm jurisdiction, limitation periods, citations, and factual support before use.",
        "employment_start_date": "2021-05-01",
        "employee_position": "Senior Specialist",
        "amount_claimed": "EUR 125,000",
        "registration_or_identifier": "HRB 00000 B, Amtsgericht Berlin-Charlottenburg",
    }
    return {str(field["key"]): values.get(str(field["key"]), "") for field in fields}


def _sample_source_document(area: str, document_type: str, case_data: dict[str, str]) -> dict[str, str]:
    title = document_type.upper()
    content = f"""# {title}

**Matter No.:** {case_data.get("matter_no")}
**Forum:** {case_data.get("jurisdiction")}
**Draft Date:** {case_data.get("draft_date")}

## PARTIES
Client: {case_data.get("client_name")}
Opposing Party: {case_data.get("opposing_party")}

## FACTUAL BACKGROUND
{case_data.get("matter_summary")}

## LEGAL BASIS
The draft should identify the applicable German-law basis for the {document_type} and separate verified facts from assumptions.

## REQUESTED OUTCOME
{case_data.get("requested_outcome")}

## SUPPORTING EVIDENCE
{case_data.get("supporting_evidence")}

## LAWYER REVIEW
This synthetic reference sample is for pattern-learning demonstration only and requires qualified lawyer review.
"""
    return {"name": f"{_slug(area)}_{_slug(document_type)}_reference.md", "content": content}


def _default_forum(area: str) -> str:
    if area == "Employment Law":
        return "Labor Court Berlin"
    if area in {"Criminal Law", "Administrative Law"}:
        return "Competent German authority or court"
    return "Regional Court Berlin"


def _slug(value: str) -> str:
    return "_".join(part for part in "".join(character.lower() if character.isalnum() else "_" for character in value).split("_") if part)


if __name__ == "__main__":
    main()
