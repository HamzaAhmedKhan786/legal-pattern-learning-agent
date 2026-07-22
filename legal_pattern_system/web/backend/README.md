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

