from __future__ import annotations

from typing import Any


SCHEMAS: dict[str, dict[str, type | tuple[type, ...]]] = {
    "plan": {"steps": list, "reasoning": str},
    "pattern_extraction": {"pattern_summary": str, "fixed_vs_variable_policy": str, "confidence": (int, float)},
    "grounded_generation": {"drafting_strategy": str, "grounding_chunk_ids": list, "warnings": list},
    "draft_document": {"draft_markdown": str, "grounding_chunk_ids": list, "assumptions": list},
    "qa_critique": {"decision": str, "critique": list, "legal_risk": str},
    "revision": {"draft_markdown": str, "revision_summary": str, "changed": bool},
}


class SchemaValidationError(ValueError):
    """Raised when an LLM response does not match the expected JSON shape."""


def validate_llm_response(purpose: str, response: dict[str, Any]) -> dict[str, Any]:
    schema = SCHEMAS.get(purpose)
    if schema is None:
        return response

    missing = [field for field in schema if field not in response]
    if missing:
        raise SchemaValidationError(f"LLM response for {purpose} is missing fields: {', '.join(missing)}")

    wrong_types: list[str] = []
    for field, expected_type in schema.items():
        if not isinstance(response[field], expected_type):
            wrong_types.append(field)
    if wrong_types:
        raise SchemaValidationError(f"LLM response for {purpose} has invalid field types: {', '.join(wrong_types)}")

    return response
