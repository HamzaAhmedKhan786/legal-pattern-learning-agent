from __future__ import annotations

import json
import sys
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


class GenerateRequest(BaseModel):
    doc_type: str
    case_data: dict[str, Any]
    llm_provider: str = "mock"
    model: str | None = None


app = FastAPI(title="Legal Pattern Learning Agent API")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/generate")
def generate(request: GenerateRequest) -> dict[str, Any]:
    document_dir = ROOT.parent / "sample_documents" / request.doc_type
    if not document_dir.exists():
        raise HTTPException(status_code=404, detail=f"Unknown document type: {request.doc_type}")

    llm = create_llm_client(request.llm_provider, model=request.model)
    report = AgenticLegalPatternOrchestrator(llm=llm).run(
        document_dir=document_dir,
        case_data=request.case_data,
        output_root=ROOT / "outputs",
    )
    trace_path = Path(report.trace_dir) / "11_trace.json"
    return json.loads(trace_path.read_text(encoding="utf-8"))


@app.post("/human-review/{run_id}/decision")
def human_review_decision(run_id: str, decision: dict[str, Any]) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "decision_recorded": True,
        "decision": decision,
        "note": "Production version would persist this to the review database and update template feedback metrics.",
    }
