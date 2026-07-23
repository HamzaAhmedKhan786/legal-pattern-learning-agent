# Architecture

This document explains the technical architecture of Legal AI Pattern Drafting
Studio from prototype to production. The design keeps the assessment pipeline
easy to run while showing how the same responsibilities scale into a real
multi-tenant legal drafting product.

## Architecture Goals

- Learn drafting patterns from approved prior documents.
- Separate fixed firm language from matter-specific variables.
- Retrieve grounding material from firm examples and official law sources.
- Generate drafts in the requested output language.
- Validate citations, completeness, consistency, and missing facts.
- Keep lawyers in control through review, feedback, and approval flows.
- Preserve traceability for every agent decision, prompt, source, and output.
- Support individual users and firms with senior/junior access controls.

## System Context

```mermaid
flowchart TB
    Browser["User Browser"]
    Lawyer["Lawyer / Junior / Admin"]
    Frontend["React + TypeScript Frontend"]
    Backend["FastAPI Backend"]
    Database[("PostgreSQL")]
    Redis[("Redis")]
    ObjectStore[("Object Storage")]
    VectorStore[("Vector Store / pgvector")]
    LLM["Mock, Ollama, or OpenAI-Compatible LLM"]
    SMTP["SMTP Provider"]
    Payments["Stripe or Paddle"]
    OfficialLaw["Official Legal Sources"]
    MCP["MCP Servers"]

    Lawyer --> Browser
    Browser --> Frontend
    Frontend --> Backend
    Backend --> Database
    Backend --> Redis
    Backend --> ObjectStore
    Backend --> VectorStore
    Backend --> LLM
    Backend --> SMTP
    Backend --> Payments
    Backend --> OfficialLaw
    Backend --> MCP
```

## Layered Architecture

```mermaid
flowchart TB
    subgraph Presentation["Presentation Layer"]
        UI["Workspace, Library, History, Profile, Admin, Support"]
        Forms["Case Facts, Uploads, Language, Provider Settings"]
        Viewer["Draft Viewer, Process Timeline, Export Buttons"]
    end

    subgraph API["API Layer"]
        Gateway["Request Gateway"]
        Auth["Auth and Session Service"]
        RBAC["Firm RBAC Policy"]
        Usage["Subscription and Usage Service"]
        Provider["Provider Vault Service"]
        Export["Export Service"]
    end

    subgraph Agentic["Agentic Workflow Layer"]
        Plan["PlanningAgent"]
        Classify["ClassifierAgent"]
        Parse["DocumentParserAgent"]
        Pattern["LLMPatternAgent"]
        Retrieve["RetrievalAgent"]
        Draft["GroundedDraftingAgent"]
        Legal["LegalSourceVerifierAgent"]
        Critique["CritiqueAgent"]
        Revise["RevisionAgent"]
        Human["HumanReviewAgent"]
    end

    subgraph Persistence["Persistence Layer"]
        PG[("PostgreSQL")]
        Obj[("Object Storage")]
        Vec[("Vector Index")]
        Audit[("Audit Log")]
    end

    UI --> Gateway
    Forms --> Gateway
    Viewer --> Gateway

    Gateway --> Auth
    Auth --> RBAC
    RBAC --> Usage
    Usage --> Provider
    Provider --> Plan

    Plan --> Classify
    Classify --> Parse
    Parse --> Pattern
    Pattern --> Retrieve
    Retrieve --> Draft
    Draft --> Legal
    Legal --> Critique
    Critique --> Revise
    Revise --> Human

    Auth --> PG
    Usage --> PG
    Provider --> PG
    Parse --> Obj
    Retrieve --> Vec
    Human --> Audit
```

## Agent Responsibilities

| Agent | Responsibility | Current State | Production Upgrade |
|---|---|---|---|
| `RequestGateway` | Normalize request metadata and create run ID | Implemented in backend flow | Add idempotency keys and async jobs |
| `ProviderRouter` | Select mock, Ollama, or API provider | Implemented | Add cost policy, fallback, health checks |
| `PlanningAgent` | Decide workflow steps and prompt versions | Implemented | Add dynamic tool planning and retries |
| `ClassifierAgent` | Classify uploaded document type | Heuristic and command hook | Connect pretrained classifier |
| `DocumentParserAgent` | Parse Markdown/source examples | Implemented | Add PDF, DOCX, OCR, layout parsing |
| `LLMPatternAgent` | Learn sections, variables, fixed language | Implemented with structured output | Add lawyer approval and template versions |
| `RetrievalAgent` | Retrieve grounding source chunks | Lexical prototype | Add embeddings, reranker, tenant filters |
| `GroundedDraftingAgent` | Generate draft from facts, template, chunks | Implemented | Add stronger model and clause locking |
| `LegalSourceVerifierAgent` | Validate country-specific official law sources | Allowlist gate scaffold | Add live official search and citation matching |
| `CritiqueAgent` | Review quality, missing facts, risk | Implemented | Add rubric and lawyer-scored eval set |
| `RevisionAgent` | Revise based on critique | Implemented | Add redline diff and version comparison |
| `HumanReviewAgent` | Persist review packet and feedback | Implemented as review workflow scaffold | Add senior approval queue and redlines |

## Orchestration Options

The project has two orchestration paths:

| Workflow | File | Purpose |
|---|---|---|
| Custom orchestrator | `src/legal_pattern_system/agentic_orchestrator.py` | Default assessment/MVP path with no extra dependencies |
| LangGraph orchestrator | `src/legal_pattern_system/langgraph_orchestrator.py` | Optional production-style state-machine workflow |

The LangGraph path keeps each major agent step as an explicit graph node:

```mermaid
flowchart LR
    Init["initialize"] --> Plan["plan"]
    Plan --> Learn["learn_template"]
    Learn --> Pattern["extract_patterns"]
    Pattern --> Retrieve["retrieve"]
    Retrieve --> Draft["draft"]
    Draft --> Critique["critique"]
    Critique --> Revise["revise"]
    Revise --> Finalize["finalize"]
```

Run it with:

```bash
pip install ".[langgraph]"
python scripts\run_agentic_pipeline.py --doc-type dismissal_protection_suits --workflow langgraph
```

Future LangGraph upgrades should add conditional edges for blocked security
checks, weak retrieval, missing facts, failed citation verification, and human
review interrupts.

## Data Architecture

```mermaid
erDiagram
    FIRMS ||--o{ USERS : has
    USERS ||--o{ USER_SESSIONS : owns
    FIRMS ||--o{ MATTERS : owns
    USERS ||--o{ MATTERS : assigned
    MATTERS ||--o{ DOCUMENT_ASSETS : contains
    DOCUMENT_ASSETS ||--o{ RAG_CHUNKS : parsed_into
    MATTERS ||--o{ AGENT_RUNS : runs
    AGENT_RUNS ||--o{ GENERATED_DRAFTS : creates
    GENERATED_DRAFTS ||--o{ REVIEW_FEEDBACK : receives
    FIRMS ||--o{ PROVIDER_CONFIGS : configures
    USERS ||--o{ PROVIDER_CONFIGS : configures
    AGENT_RUNS ||--o{ OFFICIAL_SOURCE_AUDITS : verifies
    USERS ||--o{ SUPPORT_TICKETS : opens
```

PostgreSQL stores structured data and references. Large files and exports should
move to object storage in production. Embeddings should move to `pgvector` or a
dedicated vector database when retrieval grows.

## Multi-Tenant Access Model

```mermaid
flowchart LR
    Senior["Senior Lawyer"]
    Junior["Junior Lawyer"]
    Individual["Individual User"]

    Senior --> FirmMatter["All firm matters"]
    Senior --> ReviewQueue["Review queue"]
    Senior --> AssignedJunior["Assigned junior work"]

    Junior --> OwnMatter["Own matters"]
    Junior --> AssignedMatter["Senior-assigned matters"]
    Junior -. blocked .-> SeniorPrivate["Senior private data"]

    Individual --> Personal["Personal drafts and history"]
```

Rules:

- Senior lawyers can review firm-level work and assigned junior work.
- Juniors cannot see senior private drafts unless explicitly assigned.
- Individual users remain isolated from firm tenants.
- Retrieval must always filter by tenant, matter, user role, and data policy.

## LLM And Tool Boundary

The LLM should propose structured outputs. The backend remains responsible for
validation, policy, storage, and audit.

```mermaid
flowchart LR
    Agent["Agent Prompt"] --> LLM["LLM Response"]
    LLM --> Schema["Schema Validation"]
    Schema --> Policy["Policy and RBAC Check"]
    Policy --> Tools["Approved Tool Calls"]
    Tools --> Audit["Audit Log"]
    Audit --> Agent
```

Important production rule: do not let the model directly execute MCP, web
search, payment, email, or storage actions. The orchestrator must approve,
execute, sanitize, and audit every tool call.

For the detailed security model, see
`docs/agent_security_sandboxing.md`.

## Prompt-Injection And Jailbreak Defense

Uploaded documents, pasted facts, retrieved source chunks, legal web pages, and
MCP tool outputs are untrusted data. They must not be treated as instructions.

Production defenses:

- label source text as untrusted evidence in prompts,
- never place provider keys or secrets in prompts,
- validate every LLM response against a schema,
- block tool calls that do not pass backend policy,
- filter retrieval by tenant, matter, role, country, and approved source,
- audit allowed and denied tool calls,
- quarantine suspicious outputs that attempt to bypass jurisdiction, RBAC, or
  lawyer-review rules.

## Failure Handling

| Failure | Expected Handling |
|---|---|
| Missing required facts | Block generation or return required-fields response |
| Unsupported document type | Classify as custom and ask for sample examples |
| LLM malformed JSON | Retry, normalize conservative shapes, or fail safely |
| Legal source from wrong country | Reject source and log audit event |
| Junior requests unassigned matter | Return forbidden and audit |
| Usage limit reached | Return upgrade/payment response |
| Long OCR or drafting job | Queue background job and stream status |
| Low QA or citation confidence | Route to lawyer review with warning |

## Observability

Every run should have:

- run ID,
- user ID and firm ID,
- document type and jurisdiction,
- prompt versions,
- model/provider version,
- retrieved source IDs,
- legal source audit records,
- execution log events,
- QA score and findings,
- revision decision,
- export events,
- feedback outcome,
- latency, token use, and estimated cost.

## Production Deployment Shape

```mermaid
flowchart TB
    Internet["Internet"] --> Nginx["Nginx / TLS"]
    Nginx --> Frontend["Static React Build"]
    Nginx --> API["FastAPI Containers"]
    API --> Worker["Background Workers"]
    API --> PG[("Managed PostgreSQL")]
    API --> Redis[("Redis")]
    API --> Obj[("S3 / MinIO")]
    API --> Vector[("pgvector / Vector DB")]
    API --> LLM["Ollama / vLLM / Hosted LLM"]
    API --> SMTP["Email Provider"]
    API --> Pay["Stripe / Paddle"]
    API --> Logs["Sentry / OpenTelemetry / Metrics"]
    Worker --> Obj
    Worker --> Vector
    Worker --> LLM
```

Start with this split:

- one CPU server/container group for frontend and API,
- managed PostgreSQL if possible,
- Redis for queues and rate limits,
- object storage for files and exports,
- separate GPU server for Ollama or vLLM when local model inference is needed.
