"""Adapter for the separate DocClassifier project.

The backend calls this script through DOCUMENT_CLASSIFIER_COMMAND and sends a
JSON object on stdin:

```json
{"filename": "example.pdf", "content": "extracted document text"}
```

The script returns only JSON on stdout so the legal drafting app can route the
document type without importing the classifier project directly.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


LABEL_MAP: dict[str, dict[str, str]] = {
    "Kundigung": {
        "practice_area": "Employment Law",
        "document_type": "employer_notice_of_termination",
        "topic": "Employer Notice of Termination",
    },
    "Klageschrift": {
        "practice_area": "Civil Law",
        "document_type": "civil_commercial_litigation",
        "topic": "Litigation Filing / Klageschrift",
    },
    "Schriftsatz": {
        "practice_area": "Civil Law",
        "document_type": "court_brief",
        "topic": "Court Brief / Schriftsatz",
    },
    "Vertrag&Vereinbarung": {
        "practice_area": "Commercial / Corporate Law",
        "document_type": "contract_or_agreement",
        "topic": "Contract / Agreement",
    },
    "Mahnung": {
        "practice_area": "Civil Law",
        "document_type": "demand_letter",
        "topic": "Demand Letter / Mahnung",
    },
    "Vergleich": {
        "practice_area": "Employment Law",
        "document_type": "settlement_agreement",
        "topic": "Settlement Agreement",
    },
    "Berufung": {
        "practice_area": "Civil Law",
        "document_type": "appeal",
        "topic": "Appeal / Berufung",
    },
    "Lizenzierung": {
        "practice_area": "Intellectual Property",
        "document_type": "licensing_agreement",
        "topic": "Licensing Agreement",
    },
    "Steuererklärung": {
        "practice_area": "Administrative Law",
        "document_type": "tax_filing",
        "topic": "Tax Filing",
    },
    "Rechnung": {
        "practice_area": "Civil Law",
        "document_type": "invoice",
        "topic": "Invoice",
    },
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path(r"C:\Users\DELL\Documents\Tasks\JUPUS\DocClassifier"))
    parser.add_argument("--model", type=Path, default=None)
    args = parser.parse_args()

    request = json.loads(sys.stdin.read() or "{}")
    content = str(request.get("content", "")).strip()
    filename = str(request.get("filename", "uploaded-document"))
    if not content:
        print(json.dumps({"status": "error", "message": "No content supplied.", "filename": filename}))
        return

    project_root = args.project_root.resolve()
    model_path = (args.model or project_root / "best_document_classifier.joblib").resolve()
    sys.path.insert(0, str(project_root))

    try:
        import joblib
    except ImportError:
        print(json.dumps({"status": "error", "message": "Install joblib and scikit-learn in the backend environment."}))
        return

    try:
        model = joblib.load(model_path)
        label = str(model.predict([content])[0])
        confidence = _confidence(model, content)
        mapped = LABEL_MAP.get(label, _fallback_mapping(label))
        print(
            json.dumps(
                {
                    "classifier": "docclassifier_external_adapter",
                    "status": "classified",
                    "filename": filename,
                    "raw_label": label,
                    "confidence": confidence,
                    "signals": [f"DocClassifier label: {label}"],
                    **mapped,
                },
                ensure_ascii=False,
            )
        )
    except Exception as exc:
        print(json.dumps({"status": "error", "message": str(exc), "filename": filename}))


def _confidence(model: Any, content: str) -> float:
    if hasattr(model, "predict_proba"):
        probabilities = model.predict_proba([content])[0]
        return round(float(max(probabilities)), 4)
    if hasattr(model, "decision_function"):
        scores = model.decision_function([content])
        values = scores[0] if hasattr(scores, "__len__") else [scores]
        if hasattr(values, "tolist"):
            values = values.tolist()
        top = max(float(value) for value in values)
        return round(max(0.01, min(0.99, 1 / (1 + pow(2.71828, -top)))), 4)
    return 0.5


def _fallback_mapping(label: str) -> dict[str, str]:
    return {
        "practice_area": "Civil Law",
        "document_type": "custom_legal_document",
        "topic": label or "Custom legal document",
    }


if __name__ == "__main__":
    main()
