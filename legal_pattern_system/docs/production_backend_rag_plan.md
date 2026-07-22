# Production Backend, Database, RAG, and Model Plan

## What Goes In PostgreSQL

Core tenant data:

- `firms`: firm tenant records.
- `users`: profile, email, role, firm membership, password hash.
- `user_sessions`: hashed session tokens and expiry.
- `provider_configs`: provider/model/base URL and encrypted API keys.
- `matters`: one legal matter or drafting workspace.
- `document_assets`: uploaded source files, storage URI, hash, PII classification.
- `rag_chunks`: parsed chunks with text, metadata, embedding model, and embedding vector.
- `agent_runs`: every orchestration run, provider, model, QA scores, trace location.
- `generated_drafts`: generated Markdown versions.
- `review_feedback`: positive/negative lawyer feedback scoped by firm or individual.
- `official_source_audits`: legal verification records and rejected non-official sources.
- `audit_logs`: immutable security and workflow event trail.

Large raw files should not live directly in PostgreSQL. Store them in object storage
such as S3, Azure Blob, GCS, or MinIO, then keep hashes and `storage_uri` in
`document_assets`.

## How We Handle It

Request flow:

1. User logs in and receives a session token.
2. Backend loads user, firm, and role from the session.
3. Senior lawyers can see firm matters and junior work.
4. Junior users can see only assigned matters and their own drafts.
5. Uploaded documents are stored, hashed, parsed, chunked, and embedded.
6. Retrieval selects chunks from the same firm/matter scope only.
7. LLM receives selected chunks, case facts, jurisdiction guardrail, and prompt version.
8. Draft, trace, QA, legal verification, and feedback are persisted.

## Official-Only Legal Verification

The backend now has an official-source allowlist per country. Any web-fetch or
future search connector must pass through this gate before retrieval or drafting.
For example, German legal checks should use domains such as official statute and
court sites, not arbitrary blogs.

## Agentic RAG Integration

Recommended production agents:

- `IngestionAgent`: PDF/DOCX/OCR extraction, PII classification, hash, storage.
- `ChunkingAgent`: section-aware chunking and metadata.
- `EmbeddingAgent`: creates embeddings for approved firm documents and official law.
- `RetrieverAgent`: filters by tenant, matter, document type, country, and source policy.
- `LegalSourceVerifierAgent`: official-source-only law retrieval and audit.
- `DraftingAgent`: grounded generation from case facts and retrieved chunks.
- `CitationAgent`: checks that citations come from official or approved sources.
- `CritiqueAgent`: validates completeness, contradictions, and missing facts.
- `RevisionAgent`: revises from critique.
- `HumanReviewAgent`: approval, redline, feedback capture.

Start with PostgreSQL arrays for embeddings in the prototype. For production,
use `pgvector`, Qdrant, Weaviate, Pinecone, or OpenSearch vector search.

## Deployment Path

Minimum production stack:

- FastAPI backend behind Nginx or cloud load balancer.
- PostgreSQL managed database.
- Object storage for source documents and generated exports.
- Redis for rate limiting, queues, and session revocation.
- Worker queue for ingestion, OCR, embeddings, and long agent runs.
- Secrets manager for provider keys and `APP_ENCRYPTION_KEY`.
- SMTP provider for verification/reset emails.
- Structured logs and metrics.
- CI pipeline running tests, linting, migrations, and build.

Suggested commands:

```bash
pip install -r legal_pattern_system/web/backend/requirements-web.txt
set DATABASE_URL=postgresql://postgres:your_password@localhost:5432/legal_pattern_system
set APP_ENCRYPTION_KEY=generate_with_cryptography_fernet_generate_key
python legal_pattern_system/scripts/init_database.py
uvicorn app:app --host 0.0.0.0 --port 8001
```

## Fine-Tuning Recommendation

Do not fine-tune first. Start with RAG, prompt versioning, and lawyer feedback
metrics. Fine-tune only after you have enough reviewed examples.

Good first fine-tuning target:

- `Qwen2.5-14B-Instruct` for open Apache-2.0 licensing, long context, multilingual
  support, and strong JSON/structured-output behavior.
- `Llama-3.1-8B-Instruct` if local deployment is more important and the Llama
  license fits the business use case.
- Mistral open models are attractive because many are Apache-2.0, but check the
  current model card and commercial terms before use.

Training data format:

- input: document type, jurisdiction, approved template, facts, retrieved chunks.
- output: lawyer-approved draft or section.
- labels: required facts, citations, review outcome, redline summary.

Use LoRA/QLoRA first. Keep a held-out lawyer-scored evaluation set. Measure:

- factual faithfulness,
- source citation correctness,
- jurisdiction leakage,
- old-client data leakage,
- section completeness,
- lawyer edit distance,
- approval rate after first draft.

## Open Legal Data

For German legal data, Open Legal Data provides APIs and data dumps. Use it for
retrieval/evaluation datasets where licensing permits, but keep firm-confidential
documents separate from public law/case-law corpora.
