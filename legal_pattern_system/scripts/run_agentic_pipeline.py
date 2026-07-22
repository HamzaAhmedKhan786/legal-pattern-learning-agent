"""Run the corrected LLM-style agentic pipeline.

This path demonstrates what the first submission was missing: planning, prompt
templates, retrieval grounding, critique/revision, and trace artifacts. It uses
a deterministic mock LLM client by default so the project remains runnable
without API keys. Use `--llm ollama` for local Llama via Ollama, or
`--llm openai-compatible` with an API key.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from legal_pattern_system.agentic_orchestrator import AgenticLegalPatternOrchestrator
from legal_pattern_system.llm_client import create_llm_client


CASE_DATA_FILES = {
    "dismissal_protection_suits": "dismissal_case_data.json",
    "claims_for_damages": "damages_case_data.json",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the LLM-style agentic legal pattern pipeline.")
    parser.add_argument("--doc-type", choices=sorted(CASE_DATA_FILES), default="dismissal_protection_suits")
    parser.add_argument("--llm", choices=["mock", "ollama", "openai-compatible"], default="mock")
    parser.add_argument("--model", help="Model name for ollama or openai-compatible providers.")
    parser.add_argument("--base-url", help="Provider base URL. Ollama default: http://localhost:11434. OpenAI-compatible default: https://api.openai.com/v1.")
    parser.add_argument("--api-key", help="API key for openai-compatible provider. Prefer OPENAI_API_KEY env var.")
    args = parser.parse_args()

    document_dir = ROOT.parent / "sample_documents" / args.doc_type
    case_data_path = ROOT / "examples" / CASE_DATA_FILES[args.doc_type]
    case_data = json.loads(case_data_path.read_text(encoding="utf-8"))

    llm = create_llm_client(args.llm, model=args.model, base_url=args.base_url, api_key=args.api_key)
    report = AgenticLegalPatternOrchestrator(llm=llm).run(
        document_dir=document_dir,
        case_data=case_data,
        output_root=ROOT / "outputs",
    )

    print(f"LLM provider: {args.llm}")
    if args.model:
        print(f"Model: {args.model}")
    print(f"Agentic run id: {report.run_id}")
    print(f"Document type: {report.document_type}")
    print(f"Retrieval coverage: {report.retrieval_coverage}")
    print(f"Initial QA score: {report.initial_qa_score}")
    print(f"Final QA score: {report.final_qa_score}")
    print(f"Trace directory: {report.trace_dir}")


if __name__ == "__main__":
    main()
