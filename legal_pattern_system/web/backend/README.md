# Backend Scaffold

Recommended production backend: **FastAPI**.

Why FastAPI:

- Python-native and fits the existing codebase.
- Type-hint driven request/response models.
- OpenAPI docs and client generation.
- Good fit for async upload and agent-run endpoints.

Run in production only after installing web dependencies:

```bash
pip install -r requirements-web.txt
uvicorn app:app --reload
```

Prototype endpoints:

- `POST /api/auth/register` creates an individual or firm user in PostgreSQL.
- `POST /api/auth/login` returns a bearer session token.
- `GET /api/auth/me` validates a session token.
- `POST /api/auth/request-email-verification` sends verification email through SMTP settings.
- `POST /api/auth/request-password-reset` sends password reset email through SMTP settings.
- `POST /generate` runs the agentic legal-drafting workflow.
- `GET /api/sample-library` returns the saved 73-template reference catalog.
- `GET /api/agents/status` shows active agents and LLM provider options.
- `POST /api/legal-verification` checks that legal source URLs match the selected country's official-source allowlist.
- `POST /api/legal-web-fetch` fetches only allowlisted official legal URLs and audits rejected sources.
- `POST /api/feedback` saves lawyer feedback for positive/negative history.
- `GET /api/history?account_scope=firm&firm_id=...` returns reusable firm history.
- `GET /api/history?account_scope=individual&user_email=...` returns personal history.

PostgreSQL setup:

```bash
set DATABASE_URL=postgresql://legal_ai:change-me@localhost:5432/legal_pattern_system
python legal_pattern_system/scripts/init_database.py
```

If `DATABASE_URL` is not set, the backend stays in local JSON fallback mode for
demo feedback history. Auth endpoints require PostgreSQL.

Reference sample data is generated with:

```bash
python legal_pattern_system/scripts/build_sample_library.py
```

Provider keys are accepted per request for prototype testing only. A production deployment should move API keys to a
tenant secrets vault, encrypt provider configuration, and block legal verification unless the country and official
source policy are explicitly selected.
