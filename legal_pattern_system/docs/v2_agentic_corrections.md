# V2 Agentic Corrections

This document describes the corrections made after the feedback that the first
prototype was too deterministic and did not demonstrate enough LLM-agentic
behavior.

## What Was Added

### LLM Client Interface

File:

```text
src/legal_pattern_system/llm_client.py
```

The project now has an `LlmClient` protocol and a deterministic `MockLlmClient`.
The mock client does not claim to be real AI. It exists so the same code path can
show prompt construction, structured JSON responses, and agent decisions without
requiring API keys.

The same interface now also supports:

- `OllamaLlmClient` for local Llama-style models through Ollama.
- `OpenAICompatibleLlmClient` for API-key based chat-completions providers.

### Prompt Templates

Folder:

```text
prompts/
```

Prompts were added for:

- planning,
- pattern extraction,
- grounded generation,
- QA critique,
- revision.

### Retrieval Grounding

File:

```text
src/legal_pattern_system/retrieval.py
```

The retriever chunks parsed legal documents by section and retrieves top source
chunks for the new case. This gives generation and QA a grounding artifact.

### Agentic Orchestrator

File:

```text
src/legal_pattern_system/agentic_orchestrator.py
```

The agentic flow is:

```text
PlanningAgent
  -> LLMPatternAgent
  -> RetrievalAgent
  -> GroundedDraftingAgent
  -> CritiqueAgent
  -> RevisionAgent
  -> Trace writer
```

### Trace Artifacts

Each agentic run writes artifacts to:

```text
outputs/runs/<doc_type>_<run_id>/
```

Example artifacts:

```text
01_plan.json
02_template.json
03_pattern_llm_response.json
04_retrieval.json
05_generation_llm_response.json
06_draft_v1.md
07_qa_v1.json
08_critique.json
09_draft_v2.md
10_qa_v2.json
11_trace.json
```

This addresses the observability/debugging gap from the feedback.

## How To Run

From `legal_pattern_system/`:

```bash
python scripts\run_agentic_pipeline.py --doc-type dismissal_protection_suits
python scripts\run_agentic_pipeline.py --doc-type claims_for_damages
```

Local Llama through Ollama:

```bash
ollama serve
ollama pull llama3.1
python scripts\run_agentic_pipeline.py --doc-type dismissal_protection_suits --llm ollama --model llama3.1
```

OpenAI-compatible API mode:

```bash
set OPENAI_API_KEY=your_key_here
python scripts\run_agentic_pipeline.py --doc-type dismissal_protection_suits --llm openai-compatible --model gpt-4o-mini
```

## What This Still Is

This is still not a production LLM system. It is an LLM-ready prototype with
mock, local, and API provider options. A production version would add stricter
schema validation, retries, token/cost tracking, safety filters, and model
evaluation.
