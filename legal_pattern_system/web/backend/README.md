# Backend

The backend is a FastAPI application that exposes authentication, drafting,
feedback, admin, export, legal verification, support, and production-integration
scaffolding for Legal AI Pattern Drafting Studio.

## Run Locally

```bash
cd C:\Users\DELL\Documents\Tasks\JUPUS\ai-challenge\legal_pattern_system\web\backend
pip install -r requirements-web.txt
set DATABASE_URL=postgresql://postgres:your_password@localhost:5432/legal_pattern_system
set APP_ENCRYPTION_KEY=your_fernet_key
python ..\..\scripts\init_database.py
python -m uvicorn app:app --host 127.0.0.1 --port 8001
```

Health check:

```text
GET http://127.0.0.1:8001/health
```

## Important Environment Variables

```text
DATABASE_URL=postgresql://user:password@host:5432/legal_pattern_system
APP_ENCRYPTION_KEY=<valid Fernet key>
REDIS_URL=redis://localhost:6379/0
SMTP_HOST=smtp.provider.com
SMTP_PORT=587
SMTP_USERNAME=your_smtp_user
SMTP_PASSWORD=your_smtp_password
SMTP_FROM=noreply@yourdomain.com
OPENAI_API_KEY=optional_api_key
OPENAI_BASE_URL=https://api.openai.com/v1
OLLAMA_BASE_URL=http://localhost:11434
DOCUMENT_CLASSIFIER_COMMAND=python C:\path\to\classifier\classify.py --json
STRIPE_SECRET_KEY=sk_live_or_test_key
STRIPE_WEBHOOK_SECRET=whsec_...
```

Local `DocClassifier` adapter example:

```powershell
$env:DOCUMENT_CLASSIFIER_COMMAND='python C:\Users\DELL\Documents\Tasks\JUPUS\ai-challenge\legal_pattern_system\scripts\classify_with_docclassifier.py --project-root C:\Users\DELL\Documents\Tasks\JUPUS\DocClassifier'
```

Safer production form:

```powershell
$env:DOCUMENT_CLASSIFIER_COMMAND='["python","C:\\Users\\DELL\\Documents\\Tasks\\JUPUS\\ai-challenge\\legal_pattern_system\\scripts\\classify_with_docclassifier.py","--project-root","C:\\Users\\DELL\\Documents\\Tasks\\JUPUS\\DocClassifier"]'
```

Generate a Fernet key:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## Endpoint Groups

Auth:

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `POST /api/auth/request-email-verification`
- `POST /api/auth/request-password-reset`

Drafting:

- `POST /generate`
- `POST /api/classify-document`
- `POST /api/classify-documents`
- `GET /api/agents/status`
- `GET /api/sample-library`
- `POST /api/export/markdown`
- `POST /api/export/docx`
- `POST /api/export/pdf`

History and learning:

- `POST /api/feedback`
- `GET /api/history`
- `POST /api/learned-drafts`
- `GET /api/learned-drafts`

Profile, settings, and provider vault:

- `GET /api/profile`
- `POST /api/profile`
- `POST /api/provider-config`
- `GET /api/provider-config`

Firm admin:

- `GET /api/admin/overview`
- `POST /api/admin/invite-user`
- `POST /api/admin/assign-matter`

Legal validation and MCP:

- `POST /api/legal-verification`
- `POST /api/legal-web-fetch`
- `POST /api/mcp/tool-call`

Support:

- `POST /api/contact`
- `POST /api/support/chat`

## Backend Flow

```mermaid
sequenceDiagram
    participant UI as Frontend
    participant API as FastAPI
    participant DB as PostgreSQL
    participant Agents as Agent Orchestrator
    participant LLM as LLM Provider

    UI->>API: Authenticated draft request
    API->>DB: Validate user, role, usage
    API->>Agents: Run planning, retrieval, drafting, QA
    Agents->>LLM: Structured prompts
    Agents->>DB: Save draft, trace, feedback placeholders
    API-->>UI: Draft response and execution events
```

## Database

Schema:

```text
web/backend/schema.sql
```

Initialize:

```bash
python ..\..\scripts\init_database.py
```

Production database guidance is in:

- `docs/production_backend_rag_plan.md`
- `docs/production_integration_guide.md`

## Production Notes

- Use PostgreSQL in production, not JSON fallback.
- Store raw uploads and large exports in object storage.
- Use Redis for distributed rate limiting and long-running job status.
- Encrypt provider API keys with `APP_ENCRYPTION_KEY`.
- Validate legal citations only through approved official-source allowlists.
- Audit every MCP call before returning results to an agent.
