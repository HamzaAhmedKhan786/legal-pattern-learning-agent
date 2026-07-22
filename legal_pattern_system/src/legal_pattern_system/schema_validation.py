from __future__ import annotations

from collections.abc import Callable
from typing import Any


FieldValidator = Callable[[Any], bool]


def _is_string_list(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def _is_nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_substantial_markdown(value: Any) -> bool:
    return isinstance(value, str) and len(value.split()) >= 120 and "##" in value


def _is_agent_plan(value: Any) -> bool:
    expected = {
        "parse_source_documents",
        "learn_template",
        "retrieve_grounding_chunks",
        "generate_grounded_draft",
        "critique_draft",
        "revise_if_needed",
        "write_trace",
    }
    return _is_string_list(value) and expected.issubset(set(value))


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _is_bool(value: Any) -> bool:
    return isinstance(value, bool)


def _is_decision(value: Any) -> bool:
    return value in {"accept", "revise", "reject"}


def _is_legal_risk(value: Any) -> bool:
    return value in {"low", "medium", "high"}


SCHEMAS: dict[str, dict[str, FieldValidator]] = {
    "plan": {"steps": _is_agent_plan, "reasoning": _is_nonempty_string},
    "pattern_extraction": {
        "pattern_summary": _is_nonempty_string,
        "fixed_vs_variable_policy": _is_nonempty_string,
        "confidence": _is_number,
    },
    "grounded_generation": {
        "drafting_strategy": _is_nonempty_string,
        "grounding_chunk_ids": _is_string_list,
        "warnings": _is_string_list,
    },
    "draft_document": {
        "draft_markdown": _is_substantial_markdown,
        "grounding_chunk_ids": _is_string_list,
        "assumptions": _is_string_list,
    },
    "qa_critique": {"decision": _is_decision, "critique": _is_string_list, "legal_risk": _is_legal_risk},
    "revision": {
        "draft_markdown": _is_substantial_markdown,
        "revision_summary": _is_nonempty_string,
        "changed": _is_bool,
    },
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

    invalid_fields = [field for field, validator in schema.items() if not validator(response[field])]
    if invalid_fields:
        raise SchemaValidationError(f"LLM response for {purpose} has invalid field values: {', '.join(invalid_fields)}")

    return response


def normalize_llm_response(purpose: str, response: dict[str, Any]) -> dict[str, Any]:
    """Coerce common real-LLM JSON shape errors before strict validation.

    This keeps the orchestration layer strict while accepting harmless provider
    variations such as `steps: [{"name": "..."}]` instead of `steps: ["..."]`.
    It does not invent missing required fields.
    """

    normalized = dict(response)
    for field in ("steps", "grounding_chunk_ids", "warnings", "assumptions", "critique"):
        if field in normalized and isinstance(normalized[field], list):
            normalized[field] = [_stringify_list_item(item) for item in normalized[field]]

    if purpose == "qa_critique" and "decision" in normalized:
        decision = str(normalized["decision"]).strip().lower()
        normalized["decision"] = decision if decision in {"accept", "revise", "reject"} else "revise"

    if purpose == "qa_critique" and "legal_risk" in normalized:
        risk = str(normalized["legal_risk"]).strip().lower()
        normalized["legal_risk"] = risk if risk in {"low", "medium", "high"} else "medium"

    if purpose == "revision" and "changed" in normalized and isinstance(normalized["changed"], str):
        normalized["changed"] = normalized["changed"].strip().lower() in {"true", "yes", "1", "changed"}

    return normalized


def _stringify_list_item(item: Any) -> str:
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        for key in ("name", "step", "id", "chunk_id", "message", "text", "description"):
            value = item.get(key)
            if isinstance(value, str):
                return value
    return str(item)


def schema_instructions(purpose: str) -> str:
    """Return a compact JSON contract for prompts and repair requests."""

    contracts = {
        "plan": '{"steps": ["string"], "reasoning": "string"}',
        "pattern_extraction": '{"pattern_summary": "string", "fixed_vs_variable_policy": "string", "confidence": 0.0}',
        "grounded_generation": '{"drafting_strategy": "string", "grounding_chunk_ids": ["string"], "warnings": ["string"]}',
        "draft_document": '{"draft_markdown": "string", "grounding_chunk_ids": ["string"], "assumptions": ["string"]}',
        "qa_critique": '{"decision": "accept|revise|reject", "critique": ["string"], "legal_risk": "low|medium|high"}',
        "revision": '{"draft_markdown": "string", "revision_summary": "string", "changed": true}',
    }
    return contracts.get(purpose, "{}")
