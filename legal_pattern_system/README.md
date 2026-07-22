# Legal Pattern Learning Prototype

This is a proof-of-concept submission for the legal document pattern learning
challenge. It is intentionally small, dependency-free, and easy to inspect. The
main goal is to demonstrate the agentic architecture and the end-to-end workflow,
not to build a production legal drafting system.

## What This Solves

The challenge asks for a system that can learn from multiple past legal
documents, separate stable legal structure from variable case details, generate a
new firm-specific draft, and validate the output before lawyer review.

This prototype:

- parses the provided Markdown legal documents into normalized document objects,
- compares multiple examples from the same document family,
- learns stable sections, variable fields, legal citations, and repeated patterns,
- builds a reusable JSON template,
- can generate a new Markdown draft through a mock LLM, local Ollama model, or
  OpenAI-compatible API,
- validates structured LLM JSON, retries/normalizes common provider shape
  issues, and runs QA over the generated draft,
- documents the production architecture, tradeoffs, and answers to the three
  additional challenge questions.

## App Screenshots

Workspace:

![Workspace dashboard](screenshots/workspace.png)

Generated draft output:

![Generated draft output](screenshots/generated-output.png)

Live generation process:

![Running process indicator](screenshots/running-process.png)

Sample library:

![Sample library](screenshots/library.png)

History:

![History](screenshots/history.png)

Profile:

![Profile](screenshots/profile.png)

Settings:

![Settings](screenshots/settings.png)

Firm admin:

![Firm admin](screenshots/admin.png)

Contact and AI support chatbot:

![Contact](screenshots/contact.png)

Login:

![Login](screenshots/login.png)

Signup:

![Signup](screenshots/signup.png)

About:

![About](screenshots/about.png)

Careers:

![Careers](screenshots/careers.png)

Privacy policy:

![Privacy policy](screenshots/privacy.png)

Terms:

![Terms](screenshots/terms.png)

Impressum:

![Impressum](screenshots/impressum.png)

GDPR:

![GDPR](screenshots/gdpr.png)

## Current Scope vs. Production

Current prototype:

- uses Markdown because the provided files are Markdown,
- uses a deterministic mock LLM by default so behavior is reproducible,
- can switch to real LLM execution with Ollama or an OpenAI-compatible API,
- uses only the Python standard library for the core pipeline,
- writes learned templates, generated drafts, QA reports, prompt manifests, and
  agent traces to disk.

Production version:

- would add PDF/DOCX/OCR parser adapters,
- would add retrieval over approved firm documents and legal knowledge,
- would use LLMs through structured-output interfaces,
- would include clause locking, redline comparison, template versioning, lawyer
  approval workflows, and observability.

## Frontend And Backend

The original assessment can still be reviewed through the CLI scripts, because
the brief mainly evaluates system design and agentic architecture. The project
now also includes a product-style web app to demonstrate how the same workflow
would look for a law firm.

- Backend: FastAPI in `web/backend`.
- Frontend: React/Vite in `web/frontend`.
- Database: PostgreSQL schema in `web/backend/schema.sql`.
- Auth: backend register/login/session endpoints with bearer tokens.
- Profile/settings: DB-backed profile update, email verification request, and
  password reset request endpoints.
- Provider vault: encrypted provider API-key storage with metadata-only reads.
- Subscription usage: server-side free/paid draft limit tracking before
  generation.
- RAG/MCP/support: upload/search scaffolding, audited MCP policy gate, contact
  tickets, and AI chatbot support tickets.

## Agents

The system now has two runnable paths:

- `scripts/run_pipeline.py`: deterministic baseline for reproducible template
  learning, generation, and QA.
- `scripts/run_agentic_pipeline.py`: LLM-style agent loop with planning,
  retrieval grounding, structured prompts, drafting, critique, revision, schema
  validation, and trace artifacts.

The agentic path can use:

- `mock`: deterministic LLM-shaped responses for easy reviewer execution,
- `ollama`: local Llama through Ollama,
- `openai-compatible`: hosted API provider with JSON response mode.

- `DocumentParserAgent`: turns source files into normalized `LegalDocument`
  objects.
- `PatternDetectorAgent`: detects variable fields, required sections, repeated
  language, and legal citations across multiple examples.
- `TemplateBuilderAgent`: builds a reusable `LearnedTemplate`.
- `DocumentGeneratorAgent`: creates a new draft from the learned template and
  case data.
- `QaAgent`: checks unresolved placeholders, missing required sections, missing
  citations, and suspiciously short drafts.
- `PlanningAgent`, `LLMPatternAgent`, `GroundedDraftingAgent`, `CritiqueAgent`,
  and `RevisionAgent`: LLM-facing roles in the corrected agentic pipeline.
- `LegalPatternOrchestrator`: coordinates the full workflow.

## Dependencies

The core CLI pipeline uses only the Python standard library.

The project uses:

- `argparse` for CLI arguments,
- `dataclasses` for typed models,
- `json` for output artifacts,
- `pathlib` for filesystem paths,
- `re` for Markdown/field/citation extraction,
- `unittest` for tests.

The web backend adds FastAPI, Pydantic, psycopg, cryptography, and optional Redis
rate limiting. Production document ingestion would add PyMuPDF/pdfplumber,
python-docx, OCR tooling, an embeddings/vector database layer, and an LLM client
with schema validation.

## What Is Dynamic?

Dynamically handled:

- number of Markdown files in a document family,
- metadata fields found in source documents,
- plaintiff/defendant fields found in source documents,
- section headings and heading levels,
- required vs. optional sections based on occurrence rate,
- legal citations found in source text,
- generated output paths by document type,
- QA findings based on generated content.

Hardcoded only for prototype/demo convenience:

- the two sample document family names used by the challenge,
- small sample case data inside `scripts/run_pipeline.py`,
- QA thresholds such as required section occurrence rate and short-document word
  count.

Those hardcoded items are isolated and easy to replace with CLI JSON input,
configuration, or a database in a production version.

## Folder Structure

```text
legal_pattern_system/
  README.md
  pyproject.toml
  src/legal_pattern_system/
    models.py
    agents/
      document_parser.py
      pattern_detector.py
      template_builder.py
      document_generator.py
      qa_agent.py
      orchestrator.py
    utils/
      section_parser.py
      text_cleaning.py
  scripts/
    run_pipeline.py
    generate_sample.py
    evaluate_outputs.py
  docs/
    architecture.md
    design_decisions.md
    additional_questions.md
    loom_script.md
  outputs/
    templates/
    generated_documents/
    qa_reports/
  tests/
    test_parser.py
```

## How To Run

Open a terminal in this folder:

```bash
cd C:\Users\DELL\Documents\Tasks\JUPUS\ai-challenge\legal_pattern_system
```

Run the full pipeline for dismissal protection suits:

```bash
python scripts\run_pipeline.py --doc-type dismissal_protection_suits
```

Run the full pipeline for claims for damages:

```bash
python scripts\run_pipeline.py --doc-type claims_for_damages
```

Run the corrected LLM-style agentic pipeline:

```bash
python scripts\run_agentic_pipeline.py --doc-type dismissal_protection_suits
python scripts\run_agentic_pipeline.py --doc-type claims_for_damages
```

By default this uses a deterministic mock LLM provider so the project runs
without credentials. To use a local Llama model through Ollama:

```bash
ollama serve
ollama pull llama3.1
python scripts\run_agentic_pipeline.py --doc-type dismissal_protection_suits --llm ollama --model llama3.1
```

To use an API-key based OpenAI-compatible provider:

```bash
set OPENAI_API_KEY=your_key_here
python scripts\run_agentic_pipeline.py --doc-type dismissal_protection_suits --llm openai-compatible --model gpt-4o-mini
```

Optional environment variables:

```text
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1
LLM_TIMEOUT_SECONDS=360
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
```

This agentic path adds the missing AI-engineering layer:

- planning step,
- prompt templates in `prompts/`,
- retrieval grounding over parsed source sections,
- structured LLM outputs via mock, Ollama/local-Llama, or OpenAI-compatible providers,
- schema validation plus conservative normalization for common LLM JSON shape errors,
- draft critique,
- revision decision,
- deterministic safety guardrail if an LLM revision makes no QA improvement,
- run traces in `outputs/runs/`.

Run tests:

```bash
python -m unittest discover -s tests
```

Compile-check the code:

```bash
python -m compileall src scripts tests
```

Run the web backend with PostgreSQL enabled:

```bash
cd C:\Users\DELL\Documents\Tasks\JUPUS\ai-challenge\legal_pattern_system\web\backend
pip install -r requirements-web.txt
set DATABASE_URL=postgresql://postgres:your_password@localhost:5432/legal_pattern_system
set APP_ENCRYPTION_KEY=generate_with_cryptography_fernet_generate_key
python ..\..\scripts\init_database.py
python -m uvicorn app:app --host 127.0.0.1 --port 8001
```

Run the web frontend:

```bash
cd C:\Users\DELL\Documents\Tasks\JUPUS\ai-challenge\legal_pattern_system\web\frontend
npm install
npm run dev
```

The Vite dev server proxies API calls to `http://127.0.0.1:8001`.

## Inputs

The full pipeline reads source examples from:

```text
../sample_documents/dismissal_protection_suits/*.md
../sample_documents/claims_for_damages/*.md
```

The demo case data is currently inside `scripts/run_pipeline.py` under
`SAMPLE_CASES`.

To generate from a saved template and your own case-data JSON:

```bash
python scripts\generate_sample.py --template outputs\templates\dismissal_protection_suits_template.json --case-data examples\dismissal_case_data.json --output outputs\generated_documents\my_generated.md
```

Example case-data files are included:

- `examples/dismissal_case_data.json`
- `examples/damages_case_data.json`

Example structure:

```json
{
  "case_no": "DPS-2024-999",
  "court": "Labor Court Berlin",
  "date_filed": "June 20, 2024",
  "plaintiff_name": "Example Employee",
  "plaintiff_address": "Example Street 1, 10115 Berlin, Germany",
  "defendant_company": "Example Employer GmbH",
  "defendant_address": "Employer Avenue 10, 10117 Berlin, Germany"
}
```

## Outputs

The pipeline writes:

- `outputs/templates/<doc_type>_template.json`
- `outputs/generated_documents/<doc_type>_generated.md`
- `outputs/qa_reports/<doc_type>_qa.json`
- `outputs/runs/<doc_type>_<run_id>/`

## Design Notes

See:

- `docs/architecture.md`
- `docs/design_decisions.md`
- `docs/additional_questions.md`
- `docs/loom_script.md`
- `docs/qa_score_comparison.md`
- `docs/v2_agentic_corrections.md`
- `docs/production_web_plan.md`
- `RESULTS.md`

## Future Production Suggestions

For production, I would keep this prototype's agent boundaries but replace the
lightweight internals with more robust services and review workflows.

My next production improvements would be:

- Add PDF, DOCX, and OCR ingestion adapters so the same downstream agents can
  work with real law-firm documents, not only Markdown samples.
- Add retrieval over approved firm templates, prior filings, and clause libraries
  so generation is grounded in reviewed source material.
- Introduce LLMs through structured-output contracts for semantic clause
  classification, template-variable suggestions, and controlled draft
  generation.
- Add locked clauses and redline comparison so critical legal language cannot be
  silently rewritten.
- Add a lawyer approval workflow for templates, generated drafts, low-confidence
  sections, and agent disagreements.
- Track lawyer edits after review and use that feedback as an evaluation signal
  for future template improvements.
- Add jurisdiction-specific rule checks, citation validation, PII controls,
  audit logs, and tenant isolation.
- Add observability for latency, cost, parser confidence, template confidence,
  QA findings, and post-review edit distance.

My production direction would be to treat the AI as a drafting and pattern
learning assistant, while keeping lawyers in control of legal judgment,
template approval, and final filing decisions.
