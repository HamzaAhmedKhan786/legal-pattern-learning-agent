# Feedback Postmortem: What Was Missing

This note summarizes the rejection feedback and what should be improved in a
future version. It is written as a learning document after the take-home review.

## Summary

The submission was strong as a clean software-engineering prototype, but it was
not strong enough as an AI-engineering / LLM-agent prototype.

The main gap:

> The system was mostly deterministic and did not demonstrate an LLM-driven
> agentic workflow with retrieval, prompt design, tool use, planning, iterative
> critique, and observability.

## What They Liked

### Code Quality

They liked:

- typed dataclass models,
- frozen models,
- full type hints,
- explanatory docstrings,
- clean separation across agents, utils, and models,
- Protocol-based parser adapter,
- dependency injection,
- no dead code,
- no unnecessary dependencies,
- standard-library-only implementation.

This means the software hygiene and maintainability were good.

### Architecture

They liked:

- clear responsibilities across parse, detect, build, generate, QA, and
  orchestration,
- typed inputs and outputs,
- no hidden shared state,
- separate generation and QA agents,
- severity-based conflict handling in the design docs,
- resilience discussion,
- versioned template-store idea,
- human-in-the-loop thinking.

This means the system design was understandable and not over-engineered.

## Main Things Missing

### 1. LLM-Driven Agentic System

What we built:

- deterministic Python agents,
- rule-based parsing,
- rule-based pattern detection,
- rule-based generation,
- rule-based QA.

What they expected:

- agents that use an LLM to reason,
- tool use,
- planning,
- structured-output prompts,
- an agent loop,
- iterative generation and critique.

Better v2 direction:

```text
Agent receives goal
  -> plans steps
  -> calls parser/retriever tools
  -> asks LLM for structured reasoning
  -> validates response
  -> decides next action
  -> produces artifact
```

### 2. Tool Use and Planning Loop

What we built:

```text
parse -> detect -> build template -> generate -> QA
```

This is clean orchestration, but it is linear.

What was missing:

```text
plan -> call tool -> inspect result -> call next tool -> revise plan -> final output
```

Better v2 direction:

- a planning agent creates a workflow plan,
- agents call tools such as parser, retriever, template store, QA checker,
- the orchestrator records tool calls and decisions,
- QA can trigger a revision loop.

Example:

```text
Draft v1
  -> QA critique
  -> Generator revises draft
  -> QA re-checks
  -> stop if threshold is met, otherwise route to human review
```

### 3. Retrieval

What we built:

- direct parsing and comparison of documents.

What was missing:

- retrieval over source clauses/sections,
- grounding generated text in retrieved examples,
- source references for generation,
- retrieval-quality checks.

Better v2 direction:

- chunk each legal document by section and clause,
- store chunks in a lightweight retrieval index,
- use lexical retrieval first, optionally embeddings later,
- retrieve relevant examples for a new case,
- pass retrieved evidence into the drafting prompt,
- save retrieved chunks in trace files.

Minimum simple retrieval implementation:

```text
source docs -> section chunks -> keyword/TF-IDF style retriever
new case facts -> retrieve top-k relevant clauses
retrieved clauses -> generation prompt
```

### 4. Prompt Design

What we built:

- no actual prompts,
- only documentation saying where LLMs would fit later.

What was missing:

- concrete prompt templates,
- structured JSON output schemas,
- prompt/version tracking,
- examples of LLM inputs and outputs.

Better v2 direction:

Add prompt files for:

- document section classification,
- fixed vs variable field detection,
- semantic clause classification,
- template generation,
- grounded drafting,
- QA critique.

Example prompt output format:

```json
{
  "section_type": "LEGAL_GROUNDS",
  "fixed_language": [],
  "variable_fields": [],
  "legal_citations": [],
  "confidence": 0.0,
  "source_spans": []
}
```

### 5. Evaluation and Iteration Loop

What we built:

- a deterministic QA score,
- tests,
- generated QA reports.

What was missing:

- stronger evaluation beyond one self-defined score,
- before/after iterations,
- LLM-as-judge or rubric-based critique,
- retrieval grounding score,
- hallucination/leakage rate,
- measured revision improvement.

Better v2 direction:

Use multiple evaluation signals:

- required-section coverage,
- placeholder completion,
- citation coverage,
- source-grounding coverage,
- old-case leakage detection,
- legal-risk rubric,
- draft revision delta,
- simulated lawyer review comments.

Example loop:

```text
generate draft v1
evaluate v1
produce critique
revise draft v2
evaluate v2
compare scores and findings
save result summary
```

### 6. Observability and Debugging

What we built:

- CLI print output,
- output files,
- QA report.

What was missing:

- run-level traces,
- per-agent inputs and outputs,
- prompt logs,
- retrieved chunks,
- timing,
- token/cost estimates,
- confidence by step,
- error and retry tracking.

Better v2 direction:

Create a trace folder per run:

```text
outputs/runs/<run_id>/
  01_parse.json
  02_chunks.json
  03_retrieval.json
  04_pattern_prompt.txt
  05_pattern_response.json
  06_template.json
  07_generation_prompt.txt
  08_draft_v1.md
  09_qa_report_v1.json
  10_draft_v2.md
  11_qa_report_v2.json
  trace.json
```

This would make the agent behavior easier to debug and discuss.

## Why the Submission Missed the Core Signal

The challenge was for an AI Engineer role. The reviewers were looking for proof
that the system could be designed and implemented around modern LLM workflows.

The submitted version showed:

- strong Python,
- strong architecture,
- strong deterministic workflow.

But it did not show enough:

- LLM orchestration,
- prompt engineering,
- retrieval grounding,
- iterative agent behavior,
- AI evaluation methodology.

## What a Stronger V2 Would Include

### Minimal V2 Scope

Keep the current deterministic system, but add an optional LLM layer:

- `llm_client.py`
- `prompts/`
- `retrieval/`
- `tracing/`
- `agent_loop.py`

Add agents:

- `PlanningAgent`
- `RetrievalAgent`
- `LLMPatternAgent`
- `LLMTemplateAgent`
- `GroundedDraftingAgent`
- `CritiqueAgent`
- `RevisionAgent`

### V2 Flow

```text
1. Parse provided sample documents
2. Chunk sections and clauses
3. Retrieve relevant examples
4. LLM extracts fixed/variable patterns as structured JSON
5. LLM builds a flexible template
6. LLM drafts from template + retrieved clauses + case data
7. QA agent critiques draft
8. Revision agent updates draft
9. Final QA report compares v1 vs v2
10. Save full trace
```

### V2 Deliverables

- runnable CLI,
- optional API key support,
- fallback mock LLM mode,
- prompt templates,
- retrieval traces,
- generated draft v1/v2,
- QA comparison report,
- observability trace,
- design explanation.

## How to Explain This Learning

The right takeaway:

> The submitted prototype was intentionally deterministic and strong from a
> software architecture perspective, but I underweighted the LLM-agent component
> that the reviewers considered central. A stronger version would keep the same
> clean boundaries, but add prompt-driven agents, retrieval grounding, iterative
> critique/revision, and richer observability.

## Short Version

What we missed:

- real LLM-driven agents,
- tool-use/planning loop,
- retrieval,
- prompt templates,
- iterative QA/revision,
- stronger evaluation,
- richer observability traces.

What we did well:

- clean code,
- typed models,
- maintainable architecture,
- clear docs,
- deterministic prototype,
- sensible agent separation.

Main lesson:

> For AI Engineer take-homes, a clean deterministic prototype is not enough when
> the prompt asks for an agentic system. The prototype must demonstrate the AI
> behavior, not only describe where it would go.

## Corrections Added After This Feedback

The repository now includes a v2-style agentic path that addresses the main
missing signals:

- `src/legal_pattern_system/llm_client.py` adds an LLM client protocol, mock
  structured-output provider, local Ollama provider, and OpenAI-compatible API
  provider.
- `prompts/` contains planning, pattern extraction, grounded generation, QA
  critique, and revision prompts.
- `src/legal_pattern_system/retrieval.py` adds retrieval over parsed source
  sections.
- `src/legal_pattern_system/agentic_orchestrator.py` adds a planning ->
  retrieval -> grounded draft -> critique -> revision -> trace loop.
- `scripts/run_agentic_pipeline.py` runs the corrected workflow.
- `outputs/runs/` stores per-agent trace artifacts.
- `tests/test_agentic_pipeline.py` verifies retrieval and trace generation.

This does not turn the project into a production LLM system, but it corrects the
main demo gap: the project now contains an executable agentic workflow rather
than only documentation describing where LLMs could fit later.
