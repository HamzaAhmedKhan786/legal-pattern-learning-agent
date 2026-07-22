# Production Web Application Plan

## Recommended Stack

Backend: **FastAPI**

Reasoning:

- The existing prototype is Python-based.
- FastAPI uses Python type hints and Pydantic-style validation.
- It provides OpenAPI documentation, which is useful for frontend integration
  and reviewer/debug workflows.
- It fits asynchronous upload and long-running agent jobs.

Frontend: **React + TypeScript + Vite**

Reasoning:

- React is a strong fit for review-heavy interfaces such as document viewers,
  redlines, QA dashboards, and approval flows.
- Vite is a modern lightweight build tool and supports React + TypeScript
  templates.
- TypeScript helps keep API contracts explicit.

References:

- FastAPI docs: https://fastapi.tiangolo.com/
- Vite guide: https://vite.dev/guide/
- React installation docs: https://react.dev/learn/installation

## Production Workflow

```text
Lawyer uploads prior documents
  -> ingestion service parses Markdown/PDF/DOCX/OCR
  -> chunking + embeddings index source clauses
  -> LLM pattern agent extracts fixed vs variable structure
  -> lawyer approves learned template
  -> new case intake form collects facts
  -> retrieval agent fetches grounding chunks
  -> drafting agent generates draft
  -> QA critique agent reviews draft
  -> revision agent produces v2
  -> lawyer reviews redline and approves/rejects
  -> feedback becomes evaluation data
```

## Backend Services

- upload service,
- ingestion service,
- retrieval/indexing service,
- template service,
- agent orchestration service,
- LLM provider gateway,
- QA/evaluation service,
- human review service,
- audit/trace service.

## Frontend Screens

- document upload,
- source document list,
- learned template review,
- case-data intake,
- generated draft viewer,
- retrieved grounding panel,
- QA findings panel,
- redline comparison,
- lawyer approval/feedback form,
- run trace/debug view.

## Production Data Stores

- relational database for cases, templates, approvals, users, and runs,
- object storage for source docs and generated drafts,
- vector database for clause retrieval,
- append-only audit log for legal/compliance traceability.

## Still Missing Before Production

- real OCR and layout preservation,
- robust LLM JSON schema validation and retries,
- real embeddings provider/vector database,
- authentication and role-based access,
- tenant isolation,
- PII detection/redaction,
- lawyer-scored evaluation dataset,
- redline/diff implementation,
- cost/latency/token observability,
- deployment and secrets management.

