# Application Flow

This document describes how the application behaves from login to generated
draft, review, feedback, and future learning.

## Page-Level Flow

```mermaid
flowchart LR
    Login["/login"] --> Workspace["/"]
    Signup["/signup"] --> Workspace
    Workspace --> Library["/library"]
    Workspace --> Classifier["/classifier"]
    Workspace --> History["/history"]
    Workspace --> Profile["/profile"]
    Workspace --> Settings["/settings"]
    Workspace --> Admin["/admin"]
    Workspace --> Contact["/contact"]
    Workspace --> Legal["Privacy / Terms / Impressum / GDPR"]
    Library --> Workspace
    Classifier --> Workspace
    History --> Workspace
    Admin --> Workspace
    Contact --> SupportTicket["Support Ticket"]
```

## Workspace Flow

```mermaid
flowchart TB
    Start["Open Workspace"] --> Area["Select practice area"]
    Area --> Type["Select document type"]
    Type --> Language["Select output language"]
    Language --> Source["Choose built-in samples or custom examples"]
    Source --> Facts["Enter required and optional case facts"]
    Facts --> Upload["Optional intake upload"]
    Upload --> Provider["Choose provider and model"]
    Provider --> Generate["Generate draft"]
    Generate --> Process["Show live agent process"]
    Process --> Draft["Display final draft"]
    Draft --> Export["Export Markdown / DOCX / PDF"]
    Draft --> Feedback["Save positive or negative feedback"]
    Feedback --> History["History tab"]
```

## Library To Workspace Flow

```mermaid
sequenceDiagram
    actor U as User
    participant L as Sample Library
    participant UI as Workspace UI
    participant API as Backend

    U->>L: Hover document type
    L-->>U: Show required and optional fields
    U->>L: Click document type
    L->>UI: Navigate to workspace with selected practice area and type
    UI->>API: Load sample pack metadata
    API-->>UI: Return fields, sample description, runnable status
    UI-->>U: Show matching dropdowns and fact fields
```

## Classifier To Workspace Flow

```mermaid
sequenceDiagram
    actor U as User
    participant C as Classifier Page
    participant API as Backend
    participant W as Workspace

    U->>C: Upload or paste document
    C->>API: POST /api/classify-documents
    API->>API: Security scan
    API->>API: External classifier or heuristic fallback
    API-->>C: Practice area, document type, confidence
    U->>C: Open in Workspace
    C->>W: Preselect practice area and document type
    U->>C: Add as source
    C->>W: Add classified document to source examples
```

## Draft Generation Flow

```mermaid
sequenceDiagram
    actor User
    participant UI as React UI
    participant API as FastAPI
    participant DB as PostgreSQL
    participant Agents as Agent Orchestrator
    participant LLM as LLM Provider
    participant Law as Official Law Gate

    User->>UI: Click Generate Draft
    UI->>API: POST /generate
    API->>DB: Check session and role
    API->>DB: Check subscription usage
    API->>Agents: Create run with prompt version
    Agents-->>UI: RequestGateway started
    Agents-->>UI: ProviderRouter running
    Agents->>LLM: Prepare structured-output client
    Agents-->>UI: DocumentParserAgent running
    Agents->>Agents: Parse examples and uploaded text
    Agents-->>UI: PlanningAgent running
    Agents->>Agents: Select workflow steps
    Agents-->>UI: LLMPatternAgent running
    Agents->>LLM: Extract template, variables, sections
    Agents-->>UI: RetrievalAgent running
    Agents->>Agents: Retrieve grounding chunks
    Agents-->>UI: GroundedDraftingAgent running
    Agents->>LLM: Generate draft
    Agents-->>UI: LegalSourceVerifierAgent running
    Agents->>Law: Validate citations against country allowlist
    Agents-->>UI: CritiqueAgent running
    Agents->>LLM: Critique draft
    Agents-->>UI: RevisionAgent running
    Agents->>LLM: Revise if needed
    Agents->>DB: Save run, draft, QA, trace
    API-->>UI: Return final response
    UI-->>User: Hide process steps and show draft
```

## User Feedback Flow

```mermaid
flowchart TB
    Draft["Generated draft"] --> Decision{"User feedback"}
    Decision --> Positive["Positive"]
    Decision --> Negative["Negative"]
    Positive --> PosHistory["Positive history"]
    Negative --> NegHistory["Negative history"]
    PosHistory --> Reuse["Can reuse as firm/user example"]
    NegHistory --> Improve["Used to improve prompts, QA, or template"]
    Reuse --> Approval["Senior/lawyer approval before learning"]
    Improve --> Review["Engineering and lawyer review"]
```

## Firm Admin Flow

```mermaid
flowchart LR
    Admin["Senior lawyer / firm admin"] --> Invite["Invite user"]
    Admin --> Assign["Assign matter"]
    Admin --> Queue["Review junior drafts"]
    Admin --> Visibility["Control visibility"]
    Invite --> Junior["Junior account"]
    Assign --> Matter["Matter access"]
    Queue --> Approve["Approve / reject / request changes"]
    Visibility --> RBAC["Server-enforced RBAC"]
```

## Profile And Settings Flow

```mermaid
flowchart TB
    User["User"] --> Profile["Profile page"]
    Profile --> Update["Update name and role metadata"]
    Profile --> Verify["Request email verification"]
    Profile --> Reset["Request password reset"]
    User --> Settings["Settings page"]
    Settings --> Provider["Save provider config"]
    Settings --> Country["Select country for legal validation"]
    Settings --> Plan["Subscription and usage"]
```

## Contact And AI Support Flow

```mermaid
sequenceDiagram
    actor U as User
    participant Bot as AI Support Chatbot
    participant API as Support API
    participant DB as PostgreSQL
    participant Team as Development Team

    U->>Bot: Ask app question or report complaint
    Bot->>API: Create support ticket
    API->>DB: Save message, category, severity, ticket number
    API-->>Bot: Return ticket number
    Bot-->>U: Show guidance and ticket number
    API-->>Team: Ticket available for representative follow-up
```

## Export Flow

```mermaid
flowchart LR
    Draft["Final draft"] --> Markdown["Download Markdown"]
    Draft --> DOCX["Download DOCX"]
    Draft --> PDF["Download PDF"]
    Markdown --> Record["Export audit record"]
    DOCX --> Record
    PDF --> Record
```

Production exports should store a file hash, export timestamp, user ID, matter
ID, and draft version. The lawyer should be able to prove which text was
generated, reviewed, exported, and approved.

## Backend Status Messages

The frontend should show the process as short live steps, then fade them out
when complete:

```text
ProviderRouter
DocumentParserAgent
PlanningAgent
LLMPatternAgent
RetrievalAgent
GroundedDraftingAgent
LegalSourceVerifierAgent
CritiqueAgent
RevisionAgent
HumanReviewAgent
```

The full detailed run log remains available in the trace/debug panel for
developers and reviewers.
