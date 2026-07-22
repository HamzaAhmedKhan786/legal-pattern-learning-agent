from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from typing import Any

try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
except ImportError as exc:  # pragma: no cover - optional production scaffold
    raise RuntimeError("Install web dependencies with: pip install -r requirements-web.txt") from exc

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from legal_pattern_system.agentic_orchestrator import AgenticLegalPatternOrchestrator
from legal_pattern_system.llm_client import create_llm_client


class SourceDocument(BaseModel):
    name: str
    content: str


class GenerateRequest(BaseModel):
    doc_type: str
    case_data: dict[str, Any]
    llm_provider: str = "mock"
    model: str | None = None
    source_documents: list[SourceDocument] | None = None


app = FastAPI(title="Legal Pattern Learning Agent API")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/generate")
def generate(request: GenerateRequest) -> dict[str, Any]:
    llm = create_llm_client(request.llm_provider, model=request.model)

    if request.source_documents:
        with tempfile.TemporaryDirectory(prefix="legal_pattern_sources_") as temp_dir:
            document_dir = _write_source_documents(Path(temp_dir), request.doc_type, request.source_documents)
            report = AgenticLegalPatternOrchestrator(llm=llm).run(
                document_dir=document_dir,
                case_data=request.case_data,
                output_root=ROOT / "outputs",
            )
    else:
        document_dir = ROOT.parent / "sample_documents" / request.doc_type
        if not document_dir.exists():
            raise HTTPException(status_code=404, detail=f"Unknown document type: {request.doc_type}")
        report = AgenticLegalPatternOrchestrator(llm=llm).run(
            document_dir=document_dir,
            case_data=request.case_data,
            output_root=ROOT / "outputs",
        )

    trace_path = Path(report.trace_dir) / "11_trace.json"
    trace = json.loads(trace_path.read_text(encoding="utf-8"))
    trace["draft_markdown"] = _read_text_if_exists(Path(report.trace_dir) / "09_draft_v2.md")
    trace["human_review"] = _read_json_if_exists(Path(report.trace_dir) / "12_human_review_packet.json")
    return trace


@app.post("/human-review/{run_id}/decision")
def human_review_decision(run_id: str, decision: dict[str, Any]) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "decision_recorded": True,
        "decision": decision,
        "note": "Production version would persist this to the review database and update template feedback metrics.",
    }


def _write_source_documents(root: Path, doc_type: str, source_documents: list[SourceDocument]) -> Path:
    document_dir = root / _safe_name(doc_type or "custom_legal_documents")
    document_dir.mkdir(parents=True, exist_ok=True)

    valid_documents = [doc for doc in source_documents if doc.content.strip()]
    if not valid_documents:
        raise HTTPException(status_code=400, detail="Provide at least one non-empty source document.")

    for index, document in enumerate(valid_documents, start=1):
        filename = _safe_name(document.name or f"source_{index}") or f"source_{index}"
        if not filename.endswith(".md"):
            filename = f"{filename}.md"
        (document_dir / filename).write_text(document.content.strip() + "\n", encoding="utf-8")

    return document_dir


def _safe_name(value: str) -> str:
    allowed = [character.lower() if character.isalnum() else "_" for character in value.strip()]
    collapsed = "_".join(part for part in "".join(allowed).split("_") if part)
    return collapsed[:80]


def _read_text_if_exists(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _read_json_if_exists(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
