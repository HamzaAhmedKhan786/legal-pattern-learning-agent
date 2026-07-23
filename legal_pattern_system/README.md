# Legal AI Pattern Drafting Studio

Legal AI Pattern Drafting Studio is a prototype-to-production blueprint for an
agentic legal drafting system. It learns reusable drafting patterns from a law
firm's approved past documents, collects new case facts, retrieves grounding
material, generates a new draft, validates the result, and routes it to lawyer
review.

The original assessment was a system design and architecture challenge. This
project now includes both:

- a runnable Python agentic pipeline for the assessment,
- a production-style FastAPI and React web application showing how the workflow
  would look for lawyers, juniors, firm admins, and individual users.

## Current Status

Implemented locally:

- Markdown sample ingestion from the provided challenge documents.
- LLM-ready agent orchestration with mock, Ollama, and OpenAI-compatible modes.
- Structured prompt files and JSON schema validation helpers.
- Retrieval grounding over parsed source examples.
- Draft generation, critique, revision, QA, lawyer-review checklist, and run
  trace artifacts.
- React web UI with workspace, sample library, document classifier, history,
  profile, settings, admin, support, auth, legal pages, language selection,
  feedback history, and export buttons.
- FastAPI backend with PostgreSQL schema, auth endpoints, provider key vault
  helpers, subscription usage scaffolding, support tickets, firm admin routes,
  learned draft records, official-source validation gates, and MCP audit
  scaffolding.
- MVP security guardrails in code: agent capability map, generation pre-flight
  prompt-injection scan, generated-draft safety scan, RAG upload scan, MCP tool
  policy evaluator, official-source domain enforcement, and unit tests for the
  highest-risk cases.
- Production documentation for deployment, subscriptions, RAG, MCP, and model
  strategy.

Still external before real production:

- SMTP credentials for verification and password reset emails.
- Stripe or Paddle live checkout and webhook secrets.
- Redis service for distributed rate limiting and background job state.
- Real MCP servers connected behind the audit and policy layer.
- Production hosting with Nginx/TLS, backups, monitoring, and worker queue.
- Your pretrained document classifier connected through
  `DOCUMENT_CLASSIFIER_COMMAND`.
- Live official-law retrieval using only approved government/legal sources.
- Stable production `APP_ENCRYPTION_KEY` stored in a secrets manager.
- Full production safety platform: Langfuse tracing, DeepEval/Ragas evaluation
  suites, larger red-team dataset, model-based toxicity/bias classifier, and
  continuous safety regression tests.

## High-Level Architecture

```mermaid
flowchart LR
    User["Lawyer / Junior / Firm Admin"] --> UI["React Web App"]
    UI --> API["FastAPI Backend"]

    API --> Auth["Auth, RBAC, Sessions"]
    API --> Billing["Subscription and Usage Gate"]
    API --> Orchestrator["Agent Orchestrator"]
    API --> Vault["Encrypted Provider Vault"]
    API --> Export["DOCX / PDF / Markdown Export"]

    Orchestrator --> Classifier["Document Classifier"]
    Orchestrator --> Parser["Document Parser Agent"]
    Orchestrator --> Pattern["Pattern Extraction Agent"]
    Orchestrator --> RAG["Retrieval Agent"]
    Orchestrator --> Draft["Drafting Agent"]
    Orchestrator --> Law["Official Law Validation Agent"]
    Orchestrator --> Critique["Critique Agent"]
    Orchestrator --> Revise["Revision Agent"]
    Orchestrator --> Review["Human Review Agent"]

    Auth --> DB[("PostgreSQL")]
    Billing --> DB
    Orchestrator --> DB
    Vault --> DB
    RAG --> Vector[("Vector Store / pgvector")]
    Parser --> ObjectStore[("Object Storage")]
    Export --> ObjectStore
    Law --> Official["Official Country Law Sources"]
    Orchestrator --> LLM["Mock / Ollama / OpenAI-Compatible LLM"]
    API --> Redis[("Redis")]
    API --> MCP["Audited MCP Client Layer"]
```

## Application Flow

```mermaid
sequenceDiagram
    actor U as User
    participant UI as React UI
    participant API as FastAPI
    participant GW as Request Gateway
    participant AG as Agent Orchestrator
    participant DB as PostgreSQL
    participant LLM as LLM Provider
    participant LAW as Official Law Gate

    U->>UI: Select practice area, document type, language, facts
    UI->>API: POST /generate with auth token
    API->>DB: Validate session, role, usage limit
    API->>GW: Normalize request metadata
    GW->>AG: Start drafting run
    AG->>AG: Plan workflow
    AG->>AG: Parse source examples
    AG->>AG: Learn template and variables
    AG->>AG: Retrieve firm/source chunks
    AG->>LLM: Generate grounded draft
    AG->>LAW: Validate citations by country allowlist
    AG->>LLM: Critique and revise when needed
    AG->>DB: Save draft, trace, QA, feedback placeholders
    AG->>API: Return draft, events, exports, review packet
    API->>UI: Show process, then final output
    U->>UI: Positive or negative feedback
    UI->>API: Save feedback and history record
```

For the full diagrams, see:

- [docs/README.md](docs/README.md)
- [docs/architecture.md](docs/architecture.md)
- [docs/system_design.md](docs/system_design.md)
- [docs/application_flow.md](docs/application_flow.md)
- [docs/agent_security_sandboxing.md](docs/agent_security_sandboxing.md)
- [docs/document_classifier_training_data.md](docs/document_classifier_training_data.md)
- [docs/production_integration_guide.md](docs/production_integration_guide.md)

## App Screenshots

Workspace:

![Workspace dashboard](screenshots/workspace.png)

Generated draft output:

![Generated draft output](screenshots/generated-output.png)

Live generation process:

![Running process indicator](screenshots/running-process.png)

Sample library:

![Sample library](screenshots/library.png)

Document classifier:

![Document classifier](screenshots/classifier.png)

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

## Repository Structure

```text
legal_pattern_system/
  README.md
  RESULTS.md
  docs/
    architecture.md
    system_design.md
    application_flow.md
    production_integration_guide.md
    production_backend_rag_plan.md
    production_deployment_subscription_mcp_solution.md
    design_decisions.md
    additional_questions.md
  prompts/
    planning.md
    pattern_extraction.md
    grounded_generation.md
    qa_critique.md
    revision.md
  scripts/
    run_pipeline.py
    run_agentic_pipeline.py
    generate_sample.py
    evaluate_outputs.py
    build_sample_library.py
    init_database.py
  src/legal_pattern_system/
    agents/
    agentic_orchestrator.py
    llm_client.py
    retrieval.py
    schema_validation.py
  web/
    backend/
      app.py
      database.py
      schema.sql
      security.py
      official_sources.py
    frontend/
      src/App.tsx
      src/App.css
      public/flags/
  outputs/
  screenshots/
```

## Run The Assessment Pipeline

Open a terminal in this folder:

```bash
cd C:\Users\DELL\Documents\Tasks\JUPUS\ai-challenge\legal_pattern_system
```

Run the deterministic baseline:

```bash
python scripts\run_pipeline.py --doc-type dismissal_protection_suits
python scripts\run_pipeline.py --doc-type claims_for_damages
```

Run the LLM-style agentic pipeline:

```bash
python scripts\run_agentic_pipeline.py --doc-type dismissal_protection_suits
python scripts\run_agentic_pipeline.py --doc-type claims_for_damages
```

Run the optional LangGraph state-machine workflow:

```bash
pip install ".[langgraph]"
python scripts\run_agentic_pipeline.py --doc-type dismissal_protection_suits --workflow langgraph
```

Run with local Ollama:

```bash
ollama serve
ollama pull llama3.1
python scripts\run_agentic_pipeline.py --doc-type dismissal_protection_suits --llm ollama --model llama3.1
```

Run with an OpenAI-compatible API:

```bash
set OPENAI_API_KEY=your_key_here
python scripts\run_agentic_pipeline.py --doc-type dismissal_protection_suits --llm openai-compatible --model gpt-4o-mini
```

## Run The Web Application

Backend:

```bash
cd C:\Users\DELL\Documents\Tasks\JUPUS\ai-challenge\legal_pattern_system\web\backend
pip install -r requirements-web.txt
set DATABASE_URL=postgresql://postgres:your_password@localhost:5432/legal_pattern_system
set APP_ENCRYPTION_KEY=your_fernet_key
python ..\..\scripts\init_database.py
python -m uvicorn app:app --host 127.0.0.1 --port 8001
```

Frontend:

```bash
cd C:\Users\DELL\Documents\Tasks\JUPUS\ai-challenge\legal_pattern_system\web\frontend
npm install
npm run dev
```

Open:

```text
http://127.0.0.1:5173
```

Classifier page:

```text
http://127.0.0.1:5173/classifier
```

The classifier page is an intake and routing tool. It identifies uploaded or
pasted documents, shows the predicted practice area and document type, and lets
the user either open that route in Workspace or add the classified document as a
custom source example.

## Inputs

The assessment pipeline learns from the challenge samples:

```text
../sample_documents/dismissal_protection_suits/*.md
../sample_documents/claims_for_damages/*.md
```

The web application can use:

- built-in sample packs,
- custom pasted source examples,
- uploaded intake JSON or key-value facts,
- future PDF/DOCX/OCR ingestion adapters,
- future classifier output through `DOCUMENT_CLASSIFIER_COMMAND`.

To connect the separate local classifier project:

```powershell
$env:DOCUMENT_CLASSIFIER_COMMAND='python C:\Users\DELL\Documents\Tasks\JUPUS\ai-challenge\legal_pattern_system\scripts\classify_with_docclassifier.py --project-root C:\Users\DELL\Documents\Tasks\JUPUS\DocClassifier'
```

Safer production form:

```powershell
$env:DOCUMENT_CLASSIFIER_COMMAND='["python","C:\\Users\\DELL\\Documents\\Tasks\\JUPUS\\ai-challenge\\legal_pattern_system\\scripts\\classify_with_docclassifier.py","--project-root","C:\\Users\\DELL\\Documents\\Tasks\\JUPUS\\DocClassifier"]'
```

See [docs/document_classifier_training_data.md](docs/document_classifier_training_data.md).

Classifier coverage today:

- Platform catalog: 73+ target draft types.
- Local classifier: 17 broad raw labels.
- Direct platform mappings: about 10 useful routes.
- Remaining work: collect labeled examples for the other granular platform
  document types, especially exact litigation, employment, family, real estate,
  criminal, administrative, GDPR, and finance draft categories.

## Outputs

Pipeline outputs:

```text
outputs/templates/<doc_type>_template.json
outputs/generated_documents/<doc_type>_generated.md
outputs/qa_reports/<doc_type>_qa.json
outputs/runs/<doc_type>_<run_id>/
```

Web outputs:

- generated draft text,
- event timeline,
- QA and legal validation results,
- history records with positive or negative feedback,
- Markdown, DOCX, and PDF export responses,
- support tickets and admin workflow records.

## Production Integration Checklist

Use [docs/production_integration_guide.md](docs/production_integration_guide.md)
as the step-by-step guide for:

- SMTP credentials,
- Stripe or Paddle,
- Redis,
- MCP servers,
- production hosting,
- pretrained classifier integration,
- official-law retrieval,
- stable encryption key storage.

## Security And Safety Guardrails

Implemented MVP controls:

- `web/backend/agent_security.py` defines agent capabilities and blocked actions.
- `/generate` scans case facts and uploaded source examples before any LLM call.
- `/generate` scans the generated draft before returning it to the UI.
- `/api/rag/upload` blocks uploaded text containing high-risk prompt-injection,
  jailbreak, toxic, biased, or unsafe legal instructions.
- `/api/mcp/tool-call` runs a deterministic policy check before allowing MCP-like
  tool calls and blocks non-official legal/search sources.
- `/api/legal-web-fetch` fetches only country allowlisted official sources.
- Tests in `tests/test_agent_security.py` cover prompt injection, official-source
  enforcement, unsafe output, agent permissions, and bias/toxicity patterns.

Not yet implemented as real integrations:

- LangChain,
- LangGraph,
- Langfuse,
- DeepEval,
- Ragas.

Current choice: the app uses a small custom orchestrator because it is easier to
inspect for an assessment and avoids framework complexity. For production, I
would add:

- **Langfuse** for prompt/run tracing, latency, token cost, prompt versions, and
  model debugging.
- **DeepEval** for red-team, toxicity, bias, faithfulness, and regression tests.
- **Ragas** for RAG retrieval and grounding evaluation.
- **LangGraph** if the workflow needs a formal state-machine agent graph with
  retries, branches, and resumable execution. An optional LangGraph orchestrator
  is now available through `--workflow langgraph`.
- **LangChain** only for specific integrations where it removes real work,
  rather than as a default dependency.

## Test Commands

```bash
python -m unittest discover -s tests
python -m py_compile web\backend\app.py web\backend\database.py web\backend\security.py
cd web\frontend
npm run build
```

## Design Notes

Core notes:

- [docs/architecture.md](docs/architecture.md)
- [docs/system_design.md](docs/system_design.md)
- [docs/application_flow.md](docs/application_flow.md)
- [docs/design_decisions.md](docs/design_decisions.md)
- [docs/additional_questions.md](docs/additional_questions.md)
- [docs/qa_score_comparison.md](docs/qa_score_comparison.md)
- [docs/v2_agentic_corrections.md](docs/v2_agentic_corrections.md)
- [docs/production_backend_rag_plan.md](docs/production_backend_rag_plan.md)
- [docs/production_deployment_subscription_mcp_solution.md](docs/production_deployment_subscription_mcp_solution.md)

## Production Direction

The intended production posture is not "AI replaces lawyer." The system should
act as a controlled drafting assistant:

- learn only from approved firm material,
- retrieve only scoped firm/matter/legal sources,
- validate citations against official country sources,
- sandbox tools and enforce agent permissions outside the LLM,
- defend against prompt injection and jailbreak attempts in uploaded or
  retrieved documents,
- preserve traceability for every agent decision,
- allow senior lawyers to review junior work,
- capture feedback and redlines as future evaluation data,
- protect PII, tenant data, and provider secrets.
