from __future__ import annotations

import json
from typing import Any, Protocol


class LlmClient(Protocol):
    """Structured-output LLM interface used by the agentic pipeline."""

    def complete_json(self, *, purpose: str, prompt: str, context: dict[str, Any]) -> dict[str, Any]:
        ...


class MockLlmClient:
    """Deterministic stand-in for an LLM.

    The point of this class is not to pretend rule-based code is an LLM. It gives
    the prototype the same control flow a real LLM implementation would use:
    prompt construction, structured JSON output, validation-friendly responses,
    and traceable agent decisions. A production client can implement the same
    interface with OpenAI, Anthropic, or an internal model gateway.
    """

    def complete_json(self, *, purpose: str, prompt: str, context: dict[str, Any]) -> dict[str, Any]:
        if purpose == "plan":
            return {
                "steps": [
                    "parse_source_documents",
                    "learn_template",
                    "retrieve_grounding_chunks",
                    "generate_grounded_draft",
                    "critique_draft",
                    "revise_if_needed",
                    "write_trace",
                ],
                "reasoning": "Use sample documents for learning, retrieved source chunks for grounding, and QA critique for iteration.",
            }
        if purpose == "pattern_extraction":
            return {
                "pattern_summary": "The source family has stable metadata, party blocks, statement of claim, legal grounds, relief/evidence, and conclusion sections.",
                "fixed_vs_variable_policy": "Treat repeated structure and legal citations as controlled template material; treat names, dates, IDs, amounts, and addresses as variables.",
                "confidence": context.get("template_confidence", 0.0),
            }
        if purpose == "grounded_generation":
            return {
                "drafting_strategy": "Use the learned template as structure and retrieved chunks only as grounding references, not text to copy verbatim.",
                "grounding_chunk_ids": [chunk["chunk_id"] for chunk in context.get("retrieved_chunks", [])],
                "warnings": ["Generated text remains a lawyer-review draft, not a filing-ready legal opinion."],
            }
        if purpose == "qa_critique":
            findings = context.get("qa_findings", [])
            return {
                "decision": "revise" if findings else "accept",
                "critique": findings or ["No deterministic QA findings. Keep lawyer review requirement."],
                "legal_risk": "medium" if findings else "low",
            }
        if purpose == "revision":
            return {
                "revision_strategy": "Preserve template structure, do not copy old source facts, keep citations visible, and add no unsupported legal conclusions.",
                "changed": bool(context.get("qa_findings")),
            }
        return {"purpose": purpose, "raw_context": json.dumps(context, ensure_ascii=False)[:1000]}
