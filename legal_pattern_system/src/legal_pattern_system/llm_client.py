from __future__ import annotations

import json
import os
import re
import socket
from typing import Any, Protocol
from urllib.error import URLError
from urllib.request import Request, urlopen

from legal_pattern_system.schema_validation import (
    SchemaValidationError,
    normalize_llm_response,
    schema_instructions,
    validate_llm_response,
)


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
        response: dict[str, Any]
        if purpose == "plan":
            response = {
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
            return validate_llm_response(purpose, response)
        if purpose == "pattern_extraction":
            response = {
                "pattern_summary": "The source family has stable metadata, party blocks, statement of claim, legal grounds, relief/evidence, and conclusion sections.",
                "fixed_vs_variable_policy": "Treat repeated structure and legal citations as controlled template material; treat names, dates, IDs, amounts, and addresses as variables.",
                "confidence": context.get("template_confidence", 0.0),
            }
            return validate_llm_response(purpose, response)
        if purpose == "grounded_generation":
            response = {
                "drafting_strategy": "Use the learned template as structure and retrieved chunks only as grounding references, not text to copy verbatim.",
                "grounding_chunk_ids": [chunk["chunk_id"] for chunk in context.get("retrieved_chunks", [])],
                "warnings": ["Generated text remains a lawyer-review draft, not a filing-ready legal opinion."],
            }
            return validate_llm_response(purpose, response)
        if purpose == "draft_document":
            response = {
                "draft_markdown": _mock_draft_markdown(context),
                "grounding_chunk_ids": [chunk["chunk_id"] for chunk in context.get("retrieved_chunks", [])],
                "assumptions": ["Draft is generated for lawyer review and must not be filed without human approval."],
            }
            return validate_llm_response(purpose, response)
        if purpose == "qa_critique":
            findings = context.get("qa_findings", [])
            response = {
                "decision": "revise" if findings else "accept",
                "critique": findings or ["No deterministic QA findings. Keep lawyer review requirement."],
                "legal_risk": "medium" if findings else "low",
            }
            return validate_llm_response(purpose, response)
        if purpose == "revision":
            original = context.get("draft_markdown", "")
            qa_findings = context.get("qa_findings", [])
            expansion = ""
            if any("unusually short" in finding for finding in qa_findings):
                expansion = (
                    "\n\n## LAWYER REVIEW CHECKLIST\n"
                    "- Confirm jurisdiction, venue, limitation periods, and procedural requirements.\n"
                    "- Verify all party names, addresses, registrations, employee identifiers, dates, and amounts against the matter file.\n"
                    "- Confirm that each cited statute or authority applies to the specific facts and court.\n"
                    "- Replace generic factual language with verified case-specific allegations before filing.\n"
                    "- Attach supporting evidence and confirm witness availability.\n"
                    "- Review the final draft for privilege, confidentiality, and PII handling.\n"
                )
            response = {
                "draft_markdown": original if not qa_findings else original + expansion,
                "revision_summary": "Preserved template structure, avoided old source facts, kept citations visible, and added no unsupported legal conclusions.",
                "changed": bool(qa_findings),
            }
            return validate_llm_response(purpose, response)
        return {"purpose": purpose, "raw_context": json.dumps(context, ensure_ascii=False)[:1000]}


class LlmProviderError(RuntimeError):
    """Raised when a real LLM provider cannot return structured JSON."""


class OllamaLlmClient:
    """Local Llama-compatible client through Ollama's HTTP API.

    Expected local setup:

    ```bash
    ollama serve
    ollama pull llama3.1
    ```

    Then run the agentic pipeline with `--llm ollama`.
    """

    def __init__(self, *, model: str = "llama3.1", base_url: str = "http://localhost:11434") -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = int(os.environ.get("LLM_TIMEOUT_SECONDS", "240"))

    def complete_json(self, *, purpose: str, prompt: str, context: dict[str, Any]) -> dict[str, Any]:
        user_prompt = _structured_prompt(purpose=purpose, prompt=prompt, context=context)
        payload = {
            "model": self.model,
            "prompt": user_prompt,
            "stream": False,
            "format": "json",
            "options": _ollama_options(purpose, temperature=0.1),
        }
        response = _post_json(f"{self.base_url}/api/generate", payload, timeout_seconds=self.timeout_seconds)
        text = response.get("response", "")
        parsed = normalize_llm_response(purpose, _parse_json_response(text, provider=f"ollama:{self.model}"))
        try:
            return validate_llm_response(purpose, parsed)
        except SchemaValidationError as exc:
            return self._repair_json(purpose=purpose, invalid_response=parsed, validation_error=str(exc))

    def _repair_json(self, *, purpose: str, invalid_response: dict[str, Any], validation_error: str) -> dict[str, Any]:
        repair_prompt = _repair_prompt(purpose=purpose, invalid_response=invalid_response, validation_error=validation_error)
        payload = {
            "model": self.model,
            "prompt": repair_prompt,
            "stream": False,
            "format": "json",
            "options": _ollama_options(purpose, temperature=0.0, repair=True),
        }
        response = _post_json(f"{self.base_url}/api/generate", payload, timeout_seconds=self.timeout_seconds)
        repaired = normalize_llm_response(
            purpose,
            _parse_json_response(response.get("response", ""), provider=f"ollama:{self.model}:repair"),
        )
        try:
            return validate_llm_response(purpose, repaired)
        except SchemaValidationError:
            if purpose == "plan":
                return validate_llm_response(purpose, _canonical_plan_response(provider=f"ollama:{self.model}"))
            raise


class OpenAICompatibleLlmClient:
    """OpenAI-compatible chat-completions client using only the standard library.

    It works with OpenAI-compatible providers by setting:

    - `OPENAI_API_KEY`
    - optionally `OPENAI_BASE_URL`
    - optionally `OPENAI_MODEL`

    Default base URL is OpenAI's chat-completions endpoint.
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.model = model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        self.base_url = (base_url or os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")).rstrip("/")
        if not self.api_key:
            raise LlmProviderError("OPENAI_API_KEY is required for --llm openai-compatible.")
        self.timeout_seconds = int(os.environ.get("LLM_TIMEOUT_SECONDS", "240"))

    def complete_json(self, *, purpose: str, prompt: str, context: dict[str, Any]) -> dict[str, Any]:
        payload = {
            "model": self.model,
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": "You are a legal-tech AI agent. Return only valid JSON. Do not provide legal advice or certify legal validity.",
                },
                {"role": "user", "content": _structured_prompt(purpose=purpose, prompt=prompt, context=context)},
            ],
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}
        response = _post_json(f"{self.base_url}/chat/completions", payload, headers=headers, timeout_seconds=self.timeout_seconds)
        text = response["choices"][0]["message"]["content"]
        parsed = normalize_llm_response(purpose, _parse_json_response(text, provider=f"openai-compatible:{self.model}"))
        try:
            return validate_llm_response(purpose, parsed)
        except SchemaValidationError as exc:
            return self._repair_json(purpose=purpose, invalid_response=parsed, validation_error=str(exc))

    def _repair_json(self, *, purpose: str, invalid_response: dict[str, Any], validation_error: str) -> dict[str, Any]:
        payload = {
            "model": self.model,
            "temperature": 0.0,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": "Return only valid JSON matching the requested schema."},
                {"role": "user", "content": _repair_prompt(purpose=purpose, invalid_response=invalid_response, validation_error=validation_error)},
            ],
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}
        response = _post_json(f"{self.base_url}/chat/completions", payload, headers=headers, timeout_seconds=self.timeout_seconds)
        repaired = normalize_llm_response(
            purpose,
            _parse_json_response(response["choices"][0]["message"]["content"], provider=f"openai-compatible:{self.model}:repair"),
        )
        try:
            return validate_llm_response(purpose, repaired)
        except SchemaValidationError:
            if purpose == "plan":
                return validate_llm_response(purpose, _canonical_plan_response(provider=f"openai-compatible:{self.model}"))
            raise


def create_llm_client(
    provider: str,
    *,
    model: str | None = None,
    base_url: str | None = None,
    api_key: str | None = None,
) -> LlmClient:
    if provider == "mock":
        return MockLlmClient()
    if provider == "ollama":
        return OllamaLlmClient(model=model or os.environ.get("OLLAMA_MODEL", "llama3.1"), base_url=base_url or os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"))
    if provider == "openai-compatible":
        return OpenAICompatibleLlmClient(api_key=api_key, model=model, base_url=base_url)
    raise ValueError(f"Unsupported LLM provider: {provider}")


def _canonical_plan_response(*, provider: str) -> dict[str, Any]:
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
        "reasoning": f"{provider} failed to repair the fixed orchestration plan shape, so the canonical agent plan was used as a guardrail.",
    }


def _structured_prompt(*, purpose: str, prompt: str, context: dict[str, Any]) -> str:
    return "\n\n".join(
        [
            f"Purpose: {purpose}",
            "Instructions:",
            prompt,
            "Context JSON:",
            json.dumps(context, ensure_ascii=False, indent=2),
            "Required JSON schema:",
            schema_instructions(purpose),
            "Return only one valid JSON object.",
        ]
    )


def _ollama_options(purpose: str, *, temperature: float, repair: bool = False) -> dict[str, Any]:
    """Keep local-model calls bounded so agent steps do not hang indefinitely."""

    num_predict_by_purpose = {
        "plan": 256,
        "pattern_extraction": 256,
        "grounded_generation": 256,
        "draft_document": 2200,
        "qa_critique": 256,
        "revision": 1600,
    }
    return {
        "temperature": temperature,
        "num_ctx": 4096,
        "num_predict": 512 if repair else num_predict_by_purpose.get(purpose, 512),
    }


def _repair_prompt(*, purpose: str, invalid_response: dict[str, Any], validation_error: str) -> str:
    return "\n\n".join(
        [
            f"Repair this JSON response for purpose: {purpose}",
            f"Validation error: {validation_error}",
            "Required JSON schema:",
            schema_instructions(purpose),
            "Invalid response JSON:",
            json.dumps(invalid_response, ensure_ascii=False, indent=2),
            "Return only the corrected JSON object. Do not add explanations.",
        ]
    )


def _post_json(
    url: str,
    payload: dict[str, Any],
    headers: dict[str, str] | None = None,
    *,
    timeout_seconds: int = 240,
) -> dict[str, Any]:
    request_headers = {"Content-Type": "application/json", **(headers or {})}
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=request_headers,
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))
    except TimeoutError as exc:
        raise LlmProviderError(f"LLM provider request timed out after {timeout_seconds} seconds: {url}") from exc
    except socket.timeout as exc:
        raise LlmProviderError(f"LLM provider request timed out after {timeout_seconds} seconds: {url}") from exc
    except URLError as exc:
        raise LlmProviderError(f"LLM provider request failed: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise LlmProviderError(f"LLM provider returned non-JSON HTTP response from {url}") from exc


def _parse_json_response(text: str, *, provider: str) -> dict[str, Any]:
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            raise LlmProviderError(f"{provider} did not return a JSON object.")
        parsed = json.loads(match.group(0))
    if not isinstance(parsed, dict):
        raise LlmProviderError(f"{provider} returned JSON, but not an object.")
    return parsed


def _mock_draft_markdown(context: dict[str, Any]) -> str:
    case_data = context.get("case_data", {})
    template = context.get("template", {})
    citations = ", ".join(template.get("locked_legal_citations", [])[:3])
    title = template.get("title", "LEGAL DRAFT")
    plaintiff = case_data.get("plaintiff_name", "the Plaintiff")
    defendant = case_data.get("defendant_company") or case_data.get("defendant_name", "the Defendant")

    lines = [
        f"# {title}",
        "",
        f"**Case No.:** {case_data.get('case_no', '{{case_no}}')}  ",
        f"**Court:** {case_data.get('court', '{{court}}')}  ",
        f"**Date Filed:** {case_data.get('date_filed', '{{date_filed}}')}  ",
        "",
        "---",
        "",
        "## PLAINTIFF",
        f"**Name:** {plaintiff}  ",
        f"**Address:** {case_data.get('plaintiff_address', '{{plaintiff_address}}')}  ",
        "",
        "## DEFENDANT",
        f"**Name/Company:** {defendant}  ",
        f"**Address:** {case_data.get('defendant_address', '{{defendant_address}}')}  ",
        "",
        "## STATEMENT OF CLAIM",
        "The Plaintiff submits this draft based on the learned firm template, supplied case data, and retrieved grounding excerpts.",
        "",
        "### I. FACTUAL BACKGROUND",
        f"1. {plaintiff} and {defendant} are the relevant parties in this matter.",
        "2. The case-specific facts should be completed and verified against the matter file.",
        "3. Disputed facts should remain separated from confirmed documentary evidence.",
        "",
        "### II. LEGAL GROUNDS",
        f"1. The learned source materials identify legal authorities for lawyer review: {citations}.",
        "2. The legal argument should map verified facts to the applicable elements and remain subject to lawyer approval.",
        "",
        "### III. RELIEF SOUGHT",
        "The Plaintiff respectfully requests appropriate relief supported by the facts, evidence, and applicable law.",
        "",
        "## SUPPORTING EVIDENCE",
        "### DOCUMENTS ATTACHED",
        "- A. Governing agreement, employment record, or other primary document",
        "- B. Notices, correspondence, and relevant communications",
        "- C. Matter-specific financial, employment, or damages records",
        "",
        "### WITNESS LIST",
        "1. Matter-specific witness or expert to be confirmed by counsel",
        "",
        "## CONCLUSION",
        f"For the reasons above, {plaintiff} requests relief against {defendant}. This LLM-generated draft requires lawyer review before use.",
    ]

    if template.get("document_type") == "claims_for_damages":
        lines.insert(lines.index("### III. RELIEF SOUGHT"), "### III. DAMAGES CLAIMED")
        lines.insert(lines.index("### III. RELIEF SOUGHT"), f"Total claimed damages for review: {case_data.get('total_damages', '{{total_damages}}')}.")
        lines[lines.index("### III. RELIEF SOUGHT")] = "### IV. RELIEF SOUGHT"

    return "\n".join(lines) + "\n"
