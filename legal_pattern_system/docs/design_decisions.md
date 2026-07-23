# Design Decisions

This document explains why the project is shaped this way and what tradeoffs
were made.

## 1. Agent Boundaries Are Real Responsibilities

The system uses separate agents for meaningful responsibility boundaries:

- classification,
- parsing,
- pattern extraction,
- retrieval,
- drafting,
- legal source validation,
- critique,
- revision,
- human review.

This avoids both extremes:

- one large prompt that does everything with no traceability,
- too many tiny agents that add latency without improving quality.

## 2. LLM-Ready, But Still Auditable

The first version was intentionally deterministic for reproducibility. After
feedback, the project added an LLM-ready path with:

- prompt templates,
- mock provider,
- Ollama provider,
- OpenAI-compatible provider,
- structured JSON validation,
- critique and revision loop,
- trace artifacts.

The current design keeps deterministic policy checks around the LLM. This is
important for legal work because the model should not decide access control,
payment limits, law-source trust, or final lawyer approval.

## 3. Parser Adapter Instead Of Parser Lock-In

The provided challenge files are Markdown, so the assessment pipeline uses a
Markdown parser. Downstream agents consume normalized document objects, which
keeps the design ready for:

- PDF,
- DOCX,
- OCR,
- scanned files,
- layout-aware document intelligence.

The parser can improve without rewriting pattern extraction or drafting.

## 4. Retrieval Before Fine-Tuning

The production direction is RAG first, fine-tuning later.

RAG is the better first step because it:

- keeps firm data scoped and auditable,
- lets lawyers inspect sources,
- supports country-specific legal grounding,
- improves behavior without training infrastructure,
- reduces risk of memorizing confidential data.

Fine-tuning should happen only after enough lawyer-approved drafts, redlines,
and rejection examples are available.

## 5. Human Review Is A Core Product Feature

The product is designed for lawyer control:

- generated drafts require review,
- senior lawyers can review junior work,
- negative feedback is stored separately,
- positive examples can become training candidates only after approval,
- legal citation validation produces warnings or blocks instead of silently
  trusting model output.

## 6. Production Data Separation

PostgreSQL stores structured records. Object storage stores large files and
exports. A vector store stores embeddings and retrieval metadata.

This prevents the main database from becoming a dumping ground for large draft
files, PDFs, OCR outputs, and trace bundles.

## 7. Provider Vault Instead Of Plain API Keys

Provider keys should be encrypted with `APP_ENCRYPTION_KEY`. The frontend should
only see provider metadata, never the raw key after saving.

Production secrets should live in a secret manager, not in Git and not in a
developer-only `.env` file.

## 8. Country-Based Legal Validation

Legal validation must be country-aware. A German employment-law draft should not
silently use another country's law. The official-source allowlist and audit layer
exist for this reason.

## 9. What I Would Improve Next

Immediate production improvements:

- connect real SMTP,
- connect Stripe or Paddle,
- use Redis for job status and rate limits,
- wire the pretrained classifier command,
- add object storage,
- add live official-law retrieval,
- add real MCP servers behind policy checks,
- deploy with TLS, backups, and monitoring.

Deep improvements:

- redline comparison,
- lawyer-scored evaluation set,
- retrieval quality metrics,
- citation matching metrics,
- template approval workflow,
- prompt version dashboards,
- optional LoRA fine-tuning after reviewed data exists.
