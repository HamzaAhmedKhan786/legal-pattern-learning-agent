from __future__ import annotations

import json
import os
import re
from typing import Any, Protocol
from urllib.error import URLError
from urllib.request import Request, urlopen


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

    def complete_json(self, *, purpose: str, prompt: str, context: dict[str, Any]) -> dict[str, Any]:
        user_prompt = _structured_prompt(purpose=purpose, prompt=prompt, context=context)
        payload = {
            "model": self.model,
            "prompt": user_prompt,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.1},
        }
        response = _post_json(f"{self.base_url}/api/generate", payload)
        text = response.get("response", "")
        return _parse_json_response(text, provider=f"ollama:{self.model}")


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
        response = _post_json(f"{self.base_url}/chat/completions", payload, headers=headers)
        text = response["choices"][0]["message"]["content"]
        return _parse_json_response(text, provider=f"openai-compatible:{self.model}")


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


def _structured_prompt(*, purpose: str, prompt: str, context: dict[str, Any]) -> str:
    return "\n\n".join(
        [
            f"Purpose: {purpose}",
            "Instructions:",
            prompt,
            "Context JSON:",
            json.dumps(context, ensure_ascii=False, indent=2),
            "Return only one valid JSON object.",
        ]
    )


def _post_json(url: str, payload: dict[str, Any], headers: dict[str, str] | None = None) -> dict[str, Any]:
    request_headers = {"Content-Type": "application/json", **(headers or {})}
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=request_headers,
        method="POST",
    )
    try:
        with urlopen(request, timeout=120) as response:
            return json.loads(response.read().decode("utf-8"))
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
