# Design Decisions

## Keep the Prototype Lightweight

The assessment asks for system design and agentic architecture, with a small
prototype encouraged. The sample data is Markdown, so a heavy parser would add
complexity without proving much. The prototype therefore uses standard-library
parsing and focuses on clear agent boundaries.

## Parser Adapter Instead of Parser Lock-In

All downstream agents consume a normalized `LegalDocument`. This means the parser
can change from Markdown to PDF, DOCX, OCR, or document AI later without changing
pattern detection, generation, or QA.

## Deterministic First, LLM Later

The prototype uses deterministic extraction and QA so the output is reproducible.
For production, LLMs are best introduced behind structured-output interfaces:

- classify clause types,
- infer semantic roles,
- propose template variables,
- draft case-specific language,
- explain QA concerns.

The LLM should not be the source of truth for locked legal language.

## Avoid Over-Agentification

The design uses agents where responsibilities are meaningfully different:

- parsing,
- pattern detection,
- template building,
- generation,
- QA,
- orchestration.

It does not split every tiny task into an agent. That keeps the prototype
understandable and keeps production latency/cost realistic.

## Human Review Is a Product Feature

The system should assist lawyers, not bypass them. Critical legal language,
low-confidence template changes, new jurisdictions, unusual facts, and agent
disagreements should require human approval.

## What I Would Add for Production

- PDF/DOCX/OCR ingestion with layout preservation.
- Vector retrieval over approved firm documents and legal knowledge.
- Structured LLM outputs with JSON schema validation.
- Clause locking and redline comparison.
- Template versioning and approval workflow.
- PII controls and tenant-isolated storage.
- Evaluation set with lawyer-scored drafts.
- Monitoring for latency, cost, confidence, and post-review edit distance.

