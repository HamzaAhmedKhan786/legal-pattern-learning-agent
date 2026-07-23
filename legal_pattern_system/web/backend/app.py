from __future__ import annotations

import json
import os
import time
import sys
import subprocess
import tempfile
import hashlib
import html
import io
import re
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:
    from fastapi import FastAPI, HTTPException, Query, Request, UploadFile, File, Form
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse, Response
    from pydantic import BaseModel, Field
except ImportError as exc:  # pragma: no cover - optional production scaffold
    raise RuntimeError("Install web dependencies with: pip install -r requirements-web.txt") from exc

try:
    import redis
except ImportError:  # pragma: no cover - Redis is optional for local development.
    redis = None

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from legal_pattern_system.agentic_orchestrator import AgenticLegalPatternOrchestrator
from legal_pattern_system.llm_client import create_llm_client

from database import (
    audit_mcp_tool,
    create_or_update_subscription_from_payment,
    create_session,
    create_support_ticket,
    create_user_account,
    get_user_by_email,
    get_user_by_session,
    list_learned_draft_chunks,
    get_or_create_subscription,
    get_provider_configs,
    is_database_enabled,
    list_feedback_records,
    reserve_draft_generation,
    save_document_chunks,
    save_feedback_record,
    save_provider_config,
    search_rag_chunks,
    update_user_profile,
    usage_snapshot,
    write_audit_log,
)
from agent_security import assess_generation_payload, assess_llm_output, assess_text_security, evaluate_tool_policy
from classifier_adapter import classifier_command_args
from security import create_session_token, encrypt_secret, hash_password, hash_token, verify_password
from email_service import send_email
from official_sources import fetch_official_sources


class SourceDocument(BaseModel):
    name: str
    content: str


class GenerateRequest(BaseModel):
    doc_type: str
    case_data: dict[str, Any]
    llm_provider: str = "mock"
    model: str | None = None
    source_documents: list[SourceDocument] | None = None
    account_scope: str = "guest"
    firm_id: str = "guest-firm"
    user_email: str = "guest"
    api_key: str | None = None
    base_url: str | None = None
    legal_country: str = "DE"
    output_language: str = "EN"


class FeedbackRequest(BaseModel):
    run_id: str
    sentiment: str
    comment: str = ""
    document_type: str = ""
    draft_markdown: str = ""
    case_data: dict[str, Any] = Field(default_factory=dict)
    qa_score: float | None = None
    reviewer: str = "guest"
    account_scope: str = "guest"
    firm_id: str = "guest-firm"
    user_email: str = "guest"


class LegalVerificationRequest(BaseModel):
    country: str
    legal_question: str
    source_urls: list[str] = Field(default_factory=list)


class OfficialFetchRequest(BaseModel):
    country: str
    source_urls: list[str]


class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str
    account_type: str = "individual"
    role: str = "senior_lawyer"
    firm_name: str = ""


class LoginRequest(BaseModel):
    email: str
    password: str


class EmailActionRequest(BaseModel):
    email: str


class ProfileUpdateRequest(BaseModel):
    name: str
    email: str
    accountType: str
    role: str


class ProviderConfigRequest(BaseModel):
    provider: str
    model: str = ""
    base_url: str = ""
    api_key: str = ""
    legal_country: str = "DE"


class PaymentWebhookRequest(BaseModel):
    user_email: str
    plan_code: str
    billing_interval: str = "monthly"
    status: str = "active"
    draft_limit: int = 50


class RagSearchRequest(BaseModel):
    query: str
    firm_id: str = ""
    limit: int = 6


class McpToolRequest(BaseModel):
    tool_name: str
    country: str = "DE"
    payload: dict[str, Any] = Field(default_factory=dict)


class ContactRequest(BaseModel):
    user_email: str
    subject: str
    message: str
    category: str = "general"


class ChatbotMessageRequest(BaseModel):
    user_email: str
    message: str
    category: str = "chatbot"


class ExportDraftRequest(BaseModel):
    filename: str = "legal-draft"
    draft_markdown: str
    format: str


class ClassifyDocumentRequest(BaseModel):
    filename: str = "uploaded-document.txt"
    content: str


class ClassifyDocumentsRequest(BaseModel):
    documents: list[ClassifyDocumentRequest]


class LearnedDraftRequest(BaseModel):
    title: str
    document_type: str = "custom_legal_documents"
    content: str
    learn_mode: str = "add"
    source: str = "user_uploaded_draft"
    legal_country: str = "DE"


class FirmInviteRequest(BaseModel):
    email: str
    role: str = "junior_lawyer"
    message: str = ""


class MatterAssignmentRequest(BaseModel):
    matter_title: str
    assignee_email: str
    document_type: str
    due_date: str = ""
    instructions: str = ""


OFFICIAL_LEGAL_SOURCES: dict[str, list[str]] = {
    "DE": ["gesetze-im-internet.de", "bundesverfassungsgericht.de", "bundesgerichtshof.de", "bundesarbeitsgericht.de", "dejure.org"],
    "US": ["congress.gov", "law.cornell.edu", "supreme.justia.com", "uscourts.gov", "justice.gov"],
    "GB": ["legislation.gov.uk", "gov.uk", "supremecourt.uk", "judiciary.uk"],
    "FR": ["legifrance.gouv.fr", "conseil-constitutionnel.fr", "courdecassation.fr"],
    "ES": ["boe.es", "poderjudicial.es", "tribunalconstitucional.es"],
    "IT": ["normattiva.it", "cortecostituzionale.it", "cortedicassazione.it", "giustizia.it"],
}

DOCX_CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>"""

DOCX_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""


app = FastAPI(title="Legal Pattern Learning Agent API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
HISTORY_PATH = ROOT / "outputs" / "web_feedback_history.json"
SAMPLE_LIBRARY_PATH = ROOT / "reference_data" / "legal_document_sample_library.json"
RATE_LIMIT_BUCKET: dict[str, list[float]] = {}
REDIS_RATE_LIMITER = None


def _redis_rate_limiter():
    global REDIS_RATE_LIMITER
    if REDIS_RATE_LIMITER is not None:
        return REDIS_RATE_LIMITER
    redis_url = os.environ.get("REDIS_URL", "")
    if not redis_url or redis is None:
        return None
    REDIS_RATE_LIMITER = redis.Redis.from_url(redis_url, decode_responses=True)
    return REDIS_RATE_LIMITER


@app.middleware("http")
async def rate_limit_and_log(request: Request, call_next):
    client = request.client.host if request.client else "unknown"
    now = time.time()
    window_seconds = 60
    max_requests = int(os.environ.get("RATE_LIMIT_PER_MINUTE", "120"))
    limiter = _redis_rate_limiter()
    if limiter is not None:
        bucket_key = f"rate-limit:{client}:{int(now // window_seconds)}"
        hits = limiter.incr(bucket_key)
        if hits == 1:
            limiter.expire(bucket_key, window_seconds + 5)
        if hits > max_requests:
            return JSONResponse({"detail": "Rate limit exceeded."}, status_code=429)
    else:
        hits = [hit for hit in RATE_LIMIT_BUCKET.get(client, []) if now - hit < window_seconds]
        if len(hits) >= max_requests:
            return JSONResponse({"detail": "Rate limit exceeded."}, status_code=429)
        hits.append(now)
        RATE_LIMIT_BUCKET[client] = hits
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start) * 1000, 2)
    write_audit_log(
        actor_email=request.headers.get("x-user-email", ""),
        action=f"{request.method} {request.url.path}",
        resource_type="http_request",
        metadata={"status_code": response.status_code, "duration_ms": duration_ms},
    )
    response.headers["X-Process-Time-Ms"] = str(duration_ms)
    return response


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "database": "enabled" if is_database_enabled() else "json_fallback"}


@app.post("/api/auth/register")
def register(request: RegisterRequest) -> dict[str, Any]:
    _require_database()
    if request.account_type not in {"individual", "firm"}:
        raise HTTPException(status_code=400, detail="account_type must be individual or firm.")
    if request.role not in {"senior_lawyer", "junior_lawyer", "paralegal"}:
        raise HTTPException(status_code=400, detail="Unsupported role.")
    if get_user_by_email(request.email):
        raise HTTPException(status_code=409, detail="User already exists.")
    user = create_user_account(
        email=request.email,
        full_name=request.full_name,
        password_hash=hash_password(request.password),
        account_type=request.account_type,
        role=request.role,
        firm_name=request.firm_name,
    )
    raw_token, token_hash, expires_at = create_session_token()
    create_session(user_id=user["id"], token_hash=token_hash, expires_at=expires_at)
    write_audit_log(actor_email=request.email, action="auth.register", resource_type="user", resource_id=user["id"])
    return {
        "access_token": raw_token,
        "token_type": "bearer",
        "expires_at": expires_at.isoformat(),
        "user": _public_user(user),
        "email_verification_required": True,
    }


@app.post("/api/auth/login")
def login(request: LoginRequest) -> dict[str, Any]:
    _require_database()
    user = get_user_by_email(request.email)
    if not user or not verify_password(request.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    raw_token, token_hash, expires_at = create_session_token()
    create_session(user_id=user["id"], token_hash=token_hash, expires_at=expires_at)
    write_audit_log(actor_email=user["email"], action="auth.login", resource_type="user", resource_id=user["id"])
    return {"access_token": raw_token, "token_type": "bearer", "expires_at": expires_at.isoformat(), "user": _public_user(user)}


@app.get("/api/auth/me")
def me(request: Request) -> dict[str, Any]:
    _require_database()
    token = _bearer_token(request)
    user = get_user_by_session(hash_token(token))
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired session.")
    return {"user": _public_user(user)}


@app.patch("/api/profile")
def update_profile(request: Request, profile: ProfileUpdateRequest) -> dict[str, Any]:
    _require_database()
    user = _current_user(request)
    if profile.role not in {"senior_lawyer", "junior_lawyer", "paralegal"}:
        raise HTTPException(status_code=400, detail="Unsupported role.")
    if user["role"] != "senior_lawyer" and profile.role != user["role"]:
        raise HTTPException(status_code=403, detail="Only senior lawyers can change role metadata.")
    updated = update_user_profile(
        user_id=user["id"],
        full_name=profile.name,
        email=profile.email,
        account_type=profile.accountType,
        role=profile.role,
    )
    write_audit_log(actor_email=user["email"], action="profile.update", resource_type="user", resource_id=user["id"])
    return {"user": _public_user(updated)}


@app.post("/api/auth/request-email-verification")
def request_email_verification(request: EmailActionRequest) -> dict[str, Any]:
    result = send_email(
        to_email=request.email,
        subject="Verify your Legal AI Pattern Studio account",
        body="Use the secure verification link from the production account service to verify your email.",
    )
    write_audit_log(actor_email=request.email, action="auth.email_verification_requested", resource_type="user")
    return result


@app.post("/api/auth/request-password-reset")
def request_password_reset(request: EmailActionRequest) -> dict[str, Any]:
    result = send_email(
        to_email=request.email,
        subject="Confirm password change",
        body="Use the secure password-change link from the production account service to change your password.",
    )
    write_audit_log(actor_email=request.email, action="auth.password_reset_requested", resource_type="user")
    return result


@app.post("/api/provider-config")
def save_provider_settings(request: Request, config: ProviderConfigRequest) -> dict[str, Any]:
    _require_database()
    user = _current_user(request)
    encrypted_key = None
    if config.api_key:
        encrypted_key = encrypt_secret(config.api_key)
    saved = save_provider_config(
        user_id=user["id"],
        firm_id=user.get("firm_id") or "",
        provider=config.provider,
        model=config.model,
        base_url=config.base_url,
        encrypted_api_key=encrypted_key,
        legal_country=config.legal_country.upper(),
    )
    write_audit_log(actor_email=user["email"], action="provider_config.save", resource_type="provider_config", resource_id=saved["id"])
    return {"saved": True, "config": saved}


@app.get("/api/provider-config")
def provider_settings(request: Request) -> dict[str, Any]:
    _require_database()
    user = _current_user(request)
    return {"configs": get_provider_configs(user_id=user["id"], firm_id=user.get("firm_id") or "")}


@app.get("/api/subscription")
def subscription(request: Request) -> dict[str, Any]:
    _require_database()
    user = _current_user(request)
    return usage_snapshot(user_id=user["id"], firm_id=user.get("firm_id") or "", account_type=user["account_type"])


@app.post("/api/payments/webhook")
def payment_webhook(payload: PaymentWebhookRequest) -> dict[str, Any]:
    _require_database()
    subscription_record = create_or_update_subscription_from_payment(
        user_email=payload.user_email,
        plan_code=payload.plan_code,
        billing_interval=payload.billing_interval,
        status=payload.status,
        draft_limit=payload.draft_limit,
    )
    write_audit_log(actor_email=payload.user_email, action="payment.webhook", resource_type="subscription", metadata=subscription_record)
    return {"received": True, "subscription": subscription_record}


@app.get("/api/sample-library")
def sample_library() -> dict[str, Any]:
    if not SAMPLE_LIBRARY_PATH.exists():
        raise HTTPException(status_code=404, detail="Sample library has not been generated. Run scripts/build_sample_library.py.")
    return json.loads(SAMPLE_LIBRARY_PATH.read_text(encoding="utf-8"))


@app.get("/api/agents/status")
def agents_status() -> dict[str, Any]:
    return {
        "agents": [
            {"name": "PlanningAgent", "phase": "plan", "llm_connected": True, "purpose": "Create the tool-use plan."},
            {"name": "LLMPatternAgent", "phase": "analyze", "llm_connected": True, "purpose": "Interpret learned source patterns."},
            {"name": "RetrievalAgent", "phase": "observe", "llm_connected": False, "purpose": "Retrieve grounding chunks from source examples."},
            {"name": "GroundedDraftingAgent", "phase": "act", "llm_connected": True, "purpose": "Draft from template, facts, and retrieved chunks."},
            {"name": "CritiqueAgent", "phase": "analyze", "llm_connected": True, "purpose": "Critique QA findings and decide whether revision is required."},
            {"name": "RevisionAgent", "phase": "act", "llm_connected": True, "purpose": "Revise the draft when critique requires it."},
            {"name": "HumanReviewAgent", "phase": "observe", "llm_connected": False, "purpose": "Persist lawyer feedback and route history by account scope."},
            {"name": "BillingAgent", "phase": "act", "llm_connected": False, "purpose": "Enforce subscription and usage limits before generation."},
            {"name": "ToolPolicyAgent", "phase": "plan", "llm_connected": False, "purpose": "Approve or block MCP/tool calls before execution."},
            {"name": "SecurityAgent", "phase": "analyze", "llm_connected": False, "purpose": "Detect prompt injection, jailbreak, toxicity, bias, and unsafe legal instructions before/after LLM calls."},
            {"name": "SupportAgent", "phase": "act", "llm_connected": False, "purpose": "Guide users and create support tickets for complaints."},
        ],
        "llm_providers": ["mock", "ollama", "openai-compatible"],
        "orchestrators": [
            {"name": "custom", "available": True, "purpose": "Default dependency-light assessment/MVP orchestrator."},
            {"name": "langgraph", "available": _langgraph_available(), "purpose": "Optional production-style graph/state-machine orchestrator."},
        ],
        "classifier": {
            "external_command_configured": bool(os.environ.get("DOCUMENT_CLASSIFIER_COMMAND", "")),
            "adapter": "scripts/classify_with_docclassifier.py",
        },
        "mvp_agent_recommendation": "No extra agent is required for the current MVP. Production can add CitationAgent, RedlineAgent, AssignmentAgent, and Billing/CostAgent.",
    }


@app.post("/api/legal-verification")
def legal_verification(request: LegalVerificationRequest) -> dict[str, Any]:
    country = request.country.upper()
    official_domains = OFFICIAL_LEGAL_SOURCES.get(country, [])
    if not official_domains:
        raise HTTPException(status_code=400, detail=f"No official-source allowlist configured for country: {request.country}")

    checked_sources = []
    rejected_sources = []
    for url in request.source_urls:
        host = _host_from_url(url)
        if any(host == domain or host.endswith(f".{domain}") for domain in official_domains):
            checked_sources.append({"url": url, "host": host, "official": True})
        else:
            rejected_sources.append({"url": url, "host": host, "official": False})

    return {
        "country": country,
        "legal_question": request.legal_question,
        "official_only": True,
        "allowed_domains": official_domains,
        "checked_sources": checked_sources,
        "rejected_sources": rejected_sources,
        "verification_status": "ready_for_official_web_search" if not rejected_sources else "blocked_non_official_sources",
        "instruction": "Use only the allowed official domains for this country. Do not translate or infer another country's law into this jurisdiction.",
    }


@app.post("/api/legal-web-fetch")
def legal_web_fetch(request: OfficialFetchRequest) -> dict[str, Any]:
    country = request.country.upper()
    official_domains = OFFICIAL_LEGAL_SOURCES.get(country, [])
    if not official_domains:
        raise HTTPException(status_code=400, detail=f"No official-source allowlist configured for country: {request.country}")
    result = fetch_official_sources(request.source_urls, allowed_domains=official_domains)
    write_audit_log(
        actor_email="",
        action="official_sources.fetch",
        resource_type="legal_web_fetch",
        metadata={"country": country, "fetched": len(result["fetched"]), "rejected": len(result["rejected"])},
    )
    return {"country": country, "official_only": True, "allowed_domains": official_domains, **result}


@app.post("/api/rag/upload")
async def rag_upload(
    request: Request,
    file: UploadFile = File(...),
    firm_id: str = Form(default=""),
) -> dict[str, Any]:
    _require_database()
    user = _current_user(request)
    content = await file.read()
    text = content.decode("utf-8", errors="ignore")
    if not text.strip():
        raise HTTPException(status_code=400, detail="Only text-like files are supported by this production scaffold. Add PDF/DOCX/OCR workers next.")
    security = assess_text_security(text, source=f"rag_upload:{file.filename or 'uploaded.txt'}")
    if not security.allowed:
        write_audit_log(
            actor_email=user["email"],
            action="security.rag_upload_blocked",
            resource_type="document_asset",
            metadata=security.to_dict(),
        )
        raise HTTPException(status_code=400, detail={"message": "Uploaded document was blocked by security guardrails.", "security": security.to_dict()})
    chunks = _chunk_text_for_rag(text)
    saved = save_document_chunks(
        firm_id=firm_id or user.get("firm_id") or "",
        user_id=user["id"],
        filename=file.filename or "uploaded.txt",
        content_type=file.content_type or "text/plain",
        sha256=hashlib.sha256(content).hexdigest(),
        text=text,
        chunks=chunks,
    )
    write_audit_log(actor_email=user["email"], action="rag.upload", resource_type="document_asset", resource_id=saved["asset_id"])
    return saved


@app.post("/api/rag/search")
def rag_search(request: Request, query: RagSearchRequest) -> dict[str, Any]:
    _require_database()
    user = _current_user(request)
    terms = [term for term in query.query.split() if len(term) > 2][:12]
    rows = search_rag_chunks(firm_id=query.firm_id or user.get("firm_id") or "", query_terms=terms, limit=query.limit)
    write_audit_log(actor_email=user["email"], action="rag.search", resource_type="rag_chunks", metadata={"query": query.query, "results": len(rows)})
    return {"results": rows}


@app.post("/api/mcp/tool-call")
def mcp_tool_call(request: Request, tool_request: McpToolRequest) -> dict[str, Any]:
    _require_database()
    user = _current_user(request)
    country = tool_request.country.upper()
    security = evaluate_tool_policy(
        tool_name=tool_request.tool_name,
        payload=tool_request.payload,
        country=country,
        allowed_domains=OFFICIAL_LEGAL_SOURCES.get(country, []),
        actor_role=user.get("role", ""),
    )
    decision = "allowed" if security.allowed else "blocked"
    reason = "Tool call passed policy gate." if security.allowed else "Tool call blocked by security policy."
    audit = audit_mcp_tool(
        actor_email=user["email"],
        tool_name=tool_request.tool_name,
        policy_decision=decision,
        country=country,
        request_payload=tool_request.payload,
        response_summary={"reason": reason, "security": security.to_dict()},
    )
    return {"decision": decision, "reason": reason, "security": security.to_dict(), "audit": audit}


@app.post("/api/contact")
def contact(request: ContactRequest) -> dict[str, Any]:
    _require_database()
    assistant_message = _support_response(request.message, request.category)
    ticket = create_support_ticket(
        user_email=request.user_email,
        subject=request.subject,
        message=request.message,
        category=request.category,
        assistant_message=assistant_message,
    )
    write_audit_log(actor_email=request.user_email, action="support.ticket_created", resource_type="support_ticket", resource_id=ticket["id"])
    return {"ticket": ticket}


@app.post("/api/chatbot/message")
def chatbot_message(request: ChatbotMessageRequest) -> dict[str, Any]:
    _require_database()
    category = "complaint" if any(word in request.message.lower() for word in ["complaint", "bug", "issue", "problem", "wrong", "error"]) else request.category
    subject = "AI chatbot complaint" if category == "complaint" else "AI chatbot support request"
    assistant_message = _support_response(request.message, category)
    ticket = create_support_ticket(
        user_email=request.user_email,
        subject=subject,
        message=request.message,
        category=category,
        assistant_message=assistant_message,
    )
    return {"reply": assistant_message, "ticket_no": ticket["ticket_no"], "ticket": ticket}


@app.post("/api/classify-document")
def classify_document(request: ClassifyDocumentRequest) -> dict[str, Any]:
    classification = _classify_document_text(request.content, request.filename)
    write_audit_log(
        actor_email="",
        action="document.classify",
        resource_type="document_classifier",
        metadata={"filename": request.filename, **classification},
    )
    return classification


@app.post("/api/classify-documents")
def classify_documents(request: ClassifyDocumentsRequest) -> dict[str, Any]:
    if len(request.documents) > 25:
        raise HTTPException(status_code=400, detail="Classify up to 25 documents per request.")
    results = [
        {"index": index, **_classify_document_text(document.content, document.filename)}
        for index, document in enumerate(request.documents)
    ]
    write_audit_log(
        actor_email="",
        action="document.classify_batch",
        resource_type="document_classifier",
        metadata={"count": len(results), "labels": [result.get("raw_label") or result.get("topic") for result in results]},
    )
    return {
        "results": results,
        "coverage": {
            "platform_catalog_types": 73,
            "external_classifier_labels": 17,
            "direct_platform_mappings": 10,
            "note": "The classifier is currently strongest as a broad intake/router. Exact classification for every catalog type requires more labeled examples.",
        },
    }


@app.post("/api/learned-drafts")
def save_learned_draft(request: Request, draft: LearnedDraftRequest) -> dict[str, Any]:
    _require_database()
    user = _current_user(request)
    classification = _classify_document_text(draft.content, draft.title)
    document_type = draft.document_type if draft.document_type != "auto" else classification["document_type"]
    chunks = _chunk_text_for_rag(draft.content)
    for chunk in chunks:
        chunk.setdefault("metadata", {})
        chunk["metadata"].update(
            {
                "learned_draft": True,
                "learn_mode": draft.learn_mode,
                "document_type": document_type,
                "legal_country": draft.legal_country.upper(),
                "source": draft.source,
                "classification": classification,
            }
        )
    saved = save_document_chunks(
        firm_id=user.get("firm_id") or "",
        user_id=user["id"],
        filename=f"{_safe_name(draft.title) or 'learned_draft'}.md",
        content_type="text/markdown",
        sha256=hashlib.sha256(draft.content.encode("utf-8")).hexdigest(),
        text=draft.content,
        chunks=chunks,
    )
    write_audit_log(
        actor_email=user["email"],
        action=f"learned_draft.{draft.learn_mode}",
        resource_type="document_asset",
        resource_id=saved["asset_id"],
        metadata={"title": draft.title, "document_type": document_type, "classification": classification},
    )
    return {
        "saved": True,
        "asset_id": saved["asset_id"],
        "chunks_saved": saved["chunks_saved"],
        "document_type": document_type,
        "classification": classification,
        "message": "Draft learned and added to firm/user source examples for future generation.",
    }


@app.get("/api/learned-drafts")
def learned_drafts(request: Request, query: str = Query("", description="Optional search text")) -> dict[str, Any]:
    _require_database()
    user = _current_user(request)
    rows = (
        search_rag_chunks(firm_id=user.get("firm_id") or "", query_terms=query.split(), limit=20)
        if query.strip()
        else list_learned_draft_chunks(firm_id=user.get("firm_id") or "", limit=20)
    )
    drafts = [
        {
            "id": row.get("id"),
            "name": row.get("filename"),
            "heading": row.get("heading"),
            "content": row.get("text"),
            "score": row.get("score"),
        }
        for row in rows
    ]
    return {"drafts": drafts}


@app.post("/api/export/draft")
def export_draft(request: ExportDraftRequest) -> Response:
    export_format = request.format.lower().strip(".")
    safe_name = _safe_name(request.filename or "legal-draft") or "legal-draft"
    if export_format == "md":
        return Response(
            request.draft_markdown,
            media_type="text/markdown; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{safe_name}.md"'},
        )
    if export_format == "docx":
        return Response(
            _docx_from_markdown(request.draft_markdown),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="{safe_name}.docx"'},
        )
    if export_format == "pdf":
        return Response(
            _pdf_from_text(_markdown_to_plain_text(request.draft_markdown)),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{safe_name}.pdf"'},
        )
    raise HTTPException(status_code=400, detail="format must be one of: md, docx, pdf.")


@app.get("/api/firm-admin/overview")
def firm_admin_overview(request: Request) -> dict[str, Any]:
    user = _current_user(request)
    if user["account_type"] != "firm":
        raise HTTPException(status_code=403, detail="Firm admin screens require a firm account.")
    senior = user["role"] == "senior_lawyer"
    return {
        "can_manage": senior,
        "visibility_rule": "Senior lawyers can see junior assignments; juniors see only assigned matters.",
        "users": [
            {"name": user["full_name"], "email": user["email"], "role": user["role"], "visibility": "own_and_assigned"},
            {"name": "Junior Associate", "email": "junior.associate@example.com", "role": "junior_lawyer", "visibility": "assigned_only"},
        ],
        "review_queue": [
            {"matter": "DPS-2026-014", "owner": "Junior Associate", "document_type": "Dismissal Protection Suit", "status": "awaiting_senior_review"},
            {"matter": "CFD-2026-008", "owner": user["full_name"], "document_type": "Claim for Damages", "status": "senior_draft"},
        ],
        "assignments": [
            {"matter": "DPS-2026-014", "assignee": "junior.associate@example.com", "due_date": "2026-08-01", "visibility": "senior_and_assignee"},
        ],
    }


@app.post("/api/firm-admin/invite")
def firm_admin_invite(request: Request, invite: FirmInviteRequest) -> dict[str, Any]:
    user = _current_user(request)
    _require_senior_firm_user(user)
    write_audit_log(
        actor_email=user["email"],
        action="firm.invite_user",
        resource_type="firm_invitation",
        metadata=invite.model_dump(),
    )
    return {"sent": True, "invite": invite.model_dump(), "status": "pending_email_acceptance"}


@app.post("/api/firm-admin/assign")
def firm_admin_assign(request: Request, assignment: MatterAssignmentRequest) -> dict[str, Any]:
    user = _current_user(request)
    _require_senior_firm_user(user)
    write_audit_log(
        actor_email=user["email"],
        action="firm.assign_matter",
        resource_type="matter_assignment",
        metadata=assignment.model_dump(),
    )
    return {"assigned": True, "assignment": assignment.model_dump(), "visibility": "senior_and_assignee"}


@app.post("/generate")
def generate(request: Request, payload: GenerateRequest) -> dict[str, Any]:
    started_at = datetime.now(UTC)
    execution_log: list[dict[str, Any]] = []
    _record_execution_event(
        execution_log,
        agent="RequestGateway",
        phase="intake",
        status="completed",
        message="Received draft generation request and normalized request metadata.",
        details={
            "document_type": payload.doc_type,
            "llm_provider": payload.llm_provider,
            "model": payload.model,
            "legal_country": payload.legal_country,
            "output_language": payload.output_language,
            "source_document_count": len(payload.source_documents or []),
            "case_fact_count": len(payload.case_data),
        },
    )
    request_security = assess_generation_payload(
        doc_type=payload.doc_type,
        case_data=payload.case_data,
        source_documents=payload.source_documents,
    )
    _record_execution_event(
        execution_log,
        agent="SecurityAgent",
        phase="analyze",
        status="completed" if request_security.allowed else "blocked",
        message="Checked request, case facts, and uploaded source examples for prompt injection, jailbreak, toxicity, bias, and unsafe legal instructions.",
        details=request_security.to_dict(),
    )
    if not request_security.allowed:
        if is_database_enabled():
            write_audit_log(
                actor_email=payload.user_email,
                action="security.generate_request_blocked",
                resource_type="agent_run",
                metadata=request_security.to_dict(),
            )
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Draft generation blocked by security guardrails.",
                "execution_log": execution_log,
                "security": request_security.to_dict(),
            },
        )
    user = _current_user_optional(request)
    if user and is_database_enabled():
        _record_execution_event(
            execution_log,
            agent="BillingAgent",
            phase="plan",
            status="running",
            message="Checking subscription and monthly draft quota before generation.",
            details={"account_type": user["account_type"], "firm_id": user.get("firm_id") or ""},
        )
        reservation = reserve_draft_generation(
            user_id=user["id"],
            firm_id=user.get("firm_id") or "",
            account_type=user["account_type"],
        )
        if not reservation["allowed"]:
            _record_execution_event(
                execution_log,
                agent="BillingAgent",
                phase="plan",
                status="blocked",
                message="Draft generation blocked because the monthly quota has been reached.",
                details=reservation,
            )
            raise HTTPException(status_code=402, detail={"message": "Draft generation limit reached.", **reservation})
        _record_execution_event(
            execution_log,
            agent="BillingAgent",
            phase="plan",
            status="completed",
            message="Quota reserved successfully for this generation run.",
            details={
                "draft_generations": reservation["usage"].get("draft_generations"),
                "draft_limit": reservation["subscription"].get("draft_limit"),
            },
        )

    _record_execution_event(
        execution_log,
        agent="ProviderRouter",
        phase="plan",
        status="running",
        message="Selecting LLM provider and preparing structured-output client.",
        details={"provider": payload.llm_provider, "model": payload.model or "provider_default"},
    )
    llm = create_llm_client(payload.llm_provider, model=payload.model, api_key=payload.api_key, base_url=payload.base_url)
    _record_execution_event(
        execution_log,
        agent="ProviderRouter",
        phase="plan",
        status="completed",
        message="LLM client is ready for agent prompts.",
        details={"provider": payload.llm_provider},
    )

    if payload.source_documents:
        with tempfile.TemporaryDirectory(prefix="legal_pattern_sources_") as temp_dir:
            _record_execution_event(
                execution_log,
                agent="DocumentParserAgent",
                phase="observe",
                status="running",
                message="Writing uploaded source examples to a temporary workspace for parsing.",
                details={"source_document_count": len(payload.source_documents)},
            )
            document_dir = _write_source_documents(Path(temp_dir), payload.doc_type, payload.source_documents)
            _record_execution_event(
                execution_log,
                agent="DocumentParserAgent",
                phase="observe",
                status="completed",
                message="Source documents are staged and ready for pattern analysis.",
                details={"document_dir": str(document_dir)},
            )
            _record_execution_event(
                execution_log,
                agent="PlanningAgent",
                phase="plan",
                status="running",
                message="Starting agentic drafting workflow: planning, pattern recognition, RAG retrieval, drafting, critique, and revision.",
            )
            report = AgenticLegalPatternOrchestrator(llm=llm).run(
                document_dir=document_dir,
                case_data=_case_data_with_account(payload.case_data, payload),
                output_root=ROOT / "outputs",
            )
    else:
        document_dir = ROOT.parent / "sample_documents" / payload.doc_type
        if not document_dir.exists():
            raise HTTPException(status_code=404, detail=f"Unknown document type: {payload.doc_type}")
        _record_execution_event(
            execution_log,
            agent="DocumentParserAgent",
            phase="observe",
            status="completed",
            message="Using challenge-provided sample document folder for learning.",
            details={"document_dir": str(document_dir)},
        )
        _record_execution_event(
            execution_log,
            agent="PlanningAgent",
            phase="plan",
            status="running",
            message="Starting agentic drafting workflow: planning, pattern recognition, RAG retrieval, drafting, critique, and revision.",
        )
        report = AgenticLegalPatternOrchestrator(llm=llm).run(
            document_dir=document_dir,
            case_data=_case_data_with_account(payload.case_data, payload),
            output_root=ROOT / "outputs",
        )

    trace_path = Path(report.trace_dir) / "11_trace.json"
    trace = json.loads(trace_path.read_text(encoding="utf-8"))
    execution_log.extend(_execution_events_from_trace(trace))
    _record_execution_event(
        execution_log,
        agent="HumanReviewAgent",
        phase="observe",
        status="completed",
        message="Prepared lawyer-review packet and persisted trace artifacts.",
        details={"trace_dir": str(report.trace_dir)},
    )
    _record_execution_event(
        execution_log,
        agent="ResponseAssembler",
        phase="act",
        status="completed",
        message="Draft generation response is ready for the workspace UI.",
        details={"duration_ms": round((datetime.now(UTC) - started_at).total_seconds() * 1000, 2)},
    )
    execution_log = _normalize_execution_log(execution_log)
    (Path(report.trace_dir) / "13_execution_log.json").write_text(
        json.dumps(execution_log, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    trace["draft_markdown"] = _read_text_if_exists(Path(report.trace_dir) / "09_draft_v2.md")
    output_security = assess_llm_output(trace["draft_markdown"], source="generated_draft")
    _record_execution_event(
        execution_log,
        agent="SecurityAgent",
        phase="analyze",
        status="completed" if output_security.allowed else "blocked",
        message="Checked generated draft for jailbreak leakage, unsafe legal instructions, toxicity, and bias indicators.",
        details=output_security.to_dict(),
    )
    if not output_security.allowed:
        if is_database_enabled():
            write_audit_log(
                actor_email=payload.user_email,
                action="security.generated_draft_blocked",
                resource_type="agent_run",
                resource_id=trace.get("run_id", ""),
                metadata=output_security.to_dict(),
            )
        trace["draft_markdown"] = ""
        trace["security"] = output_security.to_dict()
        trace["execution_log"] = _normalize_execution_log(execution_log)
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Generated draft blocked by security guardrails.",
                "trace": trace,
                "security": output_security.to_dict(),
            },
        )
    trace["human_review"] = _read_json_if_exists(Path(report.trace_dir) / "12_human_review_packet.json")
    legal_validation = _validate_generated_citations(
        draft_markdown=trace["draft_markdown"],
        country=payload.legal_country,
        source_documents=payload.source_documents or [],
    )
    (Path(report.trace_dir) / "14_legal_citation_validation.json").write_text(
        json.dumps(legal_validation, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    trace["legal_validation"] = legal_validation
    trace["execution_log"] = execution_log
    return trace


@app.post("/human-review/{run_id}/decision")
def human_review_decision(run_id: str, decision: dict[str, Any]) -> dict[str, Any]:
    feedback = FeedbackRequest(
        run_id=run_id,
        sentiment=str(decision.get("sentiment", decision.get("decision", "positive"))),
        comment=str(decision.get("comment", "")),
        document_type=str(decision.get("document_type", "")),
        draft_markdown=str(decision.get("draft_markdown", "")),
        case_data=dict(decision.get("case_data", {})),
        qa_score=decision.get("qa_score"),
        reviewer=str(decision.get("reviewer", "guest")),
        account_scope=str(decision.get("account_scope", "guest")),
        firm_id=str(decision.get("firm_id", "guest-firm")),
        user_email=str(decision.get("user_email", decision.get("reviewer", "guest"))),
    )
    record = _append_feedback(feedback)
    return {
        "run_id": run_id,
        "decision_recorded": True,
        "decision": decision,
        "history_record": record,
        "note": "Prototype persists this to outputs/web_feedback_history.json. Production would store it in the review database and update template feedback metrics.",
    }


@app.post("/feedback")
def save_feedback(feedback: FeedbackRequest) -> dict[str, Any]:
    return {"saved": True, "record": _append_feedback(feedback)}


@app.post("/api/feedback")
def save_feedback_api(feedback: FeedbackRequest) -> dict[str, Any]:
    return save_feedback(feedback)


@app.get("/history")
def history(
    account_scope: str = Query(default="all"),
    firm_id: str = Query(default=""),
    user_email: str = Query(default=""),
) -> dict[str, Any]:
    records = _read_history()
    records = _filter_history(records, account_scope=account_scope, firm_id=firm_id, user_email=user_email)
    return {
        "positive": [record for record in records if record.get("sentiment") == "positive"],
        "negative": [record for record in records if record.get("sentiment") == "negative"],
        "all": records,
    }


@app.get("/api/history")
def history_api(
    account_scope: str = Query(default="all"),
    firm_id: str = Query(default=""),
    user_email: str = Query(default=""),
) -> dict[str, Any]:
    return history(account_scope=account_scope, firm_id=firm_id, user_email=user_email)


def _write_source_documents(root: Path, doc_type: str, source_documents: list[SourceDocument]) -> Path:
    document_dir = root / _safe_name(doc_type or "custom_legal_documents")
    document_dir.mkdir(parents=True, exist_ok=True)

    valid_documents = [doc for doc in source_documents if doc.content.strip()]
    if not valid_documents:
        raise HTTPException(status_code=400, detail="Provide at least one non-empty source document.")

    for index, document in enumerate(valid_documents, start=1):
        filename = _safe_name(document.name or f"source_{index}") or f"source_{index}"
        if not filename.endswith(".md"):
            filename = f"{filename}.md"
        (document_dir / filename).write_text(document.content.strip() + "\n", encoding="utf-8")

    return document_dir


def _safe_name(value: str) -> str:
    allowed = [character.lower() if character.isalnum() else "_" for character in value.strip()]
    collapsed = "_".join(part for part in "".join(allowed).split("_") if part)
    return collapsed[:80]


def _read_text_if_exists(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _read_json_if_exists(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _record_execution_event(
    events: list[dict[str, Any]],
    *,
    agent: str,
    phase: str,
    status: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> None:
    events.append(
        {
            "timestamp": datetime.now(UTC).isoformat(),
            "agent": agent,
            "phase": phase,
            "status": status,
            "message": message,
            "details": details or {},
        }
    )


def _execution_events_from_trace(trace: dict[str, Any]) -> list[dict[str, Any]]:
    phase_by_agent = {
        "PlanningAgent": "plan",
        "LLMPatternAgent": "analyze",
        "RetrievalAgent": "observe",
        "GroundedDraftingAgent": "act",
        "CritiqueAgent": "analyze",
        "RevisionAgent": "act",
    }
    events: list[dict[str, Any]] = []
    for step in trace.get("steps", []):
        agent = str(step.get("name", "Agent"))
        phase = phase_by_agent.get(agent, "act")
        _record_execution_event(
            events,
            agent=agent,
            phase=phase,
            status="completed",
            message=_friendly_step_message(agent, str(step.get("purpose", ""))),
            details={
                "input_summary": step.get("input_summary"),
                "output_summary": step.get("output_summary"),
                "artifact_path": step.get("artifact_path"),
            },
        )
    return events


def _normalize_execution_log(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    latest_terminal_by_agent: dict[tuple[str, str], int] = {}
    for index, event in enumerate(events):
        if event.get("status") in {"completed", "blocked", "failed"}:
            latest_terminal_by_agent[(str(event.get("agent", "")), str(event.get("phase", "")))] = index
    normalized = []
    for index, event in enumerate(events):
        next_event = dict(event)
        key = (str(event.get("agent", "")), str(event.get("phase", "")))
        terminal_index = latest_terminal_by_agent.get(key)
        if event.get("status") == "running" and terminal_index is not None and terminal_index > index:
            next_event["status"] = "completed"
            next_event["message"] = f"{event.get('message', '')} Completed."
        normalized.append(next_event)
    return normalized


def _friendly_step_message(agent: str, fallback: str) -> str:
    messages = {
        "PlanningAgent": "Request is in planning: the agent selected the tools and workflow steps.",
        "LLMPatternAgent": "Pattern recognition is complete: fixed legal language, variables, and required sections were analyzed.",
        "RetrievalAgent": "RAG retrieval is complete: grounding chunks were selected from learned source examples.",
        "GroundedDraftingAgent": "Drafting is complete: the LLM generated a grounded first version from template, facts, and retrieved chunks.",
        "CritiqueAgent": "Quality critique is complete: QA findings were reviewed and revision need was decided.",
        "RevisionAgent": "Reforming/revision is complete: the draft was improved using critique and QA feedback.",
    }
    return messages.get(agent, fallback or f"{agent} completed.")


def _case_data_with_account(case_data: dict[str, Any], request: GenerateRequest) -> dict[str, Any]:
    enriched = dict(case_data)
    enriched.setdefault("account_scope", request.account_scope)
    enriched.setdefault("firm_id", request.firm_id)
    enriched.setdefault("requested_by", request.user_email)
    enriched.setdefault("legal_country", request.legal_country.upper())
    enriched.setdefault("output_language", request.output_language.upper())
    enriched.setdefault(
        "jurisdiction_guardrail",
        f"Draft in {request.output_language.upper()} and keep legal verification within {request.legal_country.upper()} law unless a lawyer explicitly changes the country.",
    )
    return enriched


def _append_feedback(feedback: FeedbackRequest) -> dict[str, Any]:
    record = {
        "id": f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}_{feedback.run_id}",
        "created_at": datetime.now(UTC).isoformat(),
        "run_id": feedback.run_id,
        "sentiment": "negative" if feedback.sentiment.lower().startswith("neg") else "positive",
        "comment": feedback.comment,
        "document_type": feedback.document_type,
        "draft_markdown": feedback.draft_markdown,
        "case_data": feedback.case_data,
        "qa_score": feedback.qa_score,
        "reviewer": feedback.reviewer,
        "account_scope": _normalized_scope(feedback.account_scope),
        "firm_id": feedback.firm_id or "guest-firm",
        "user_email": feedback.user_email or feedback.reviewer,
    }
    if is_database_enabled():
        saved = save_feedback_record(record)
        write_audit_log(
            actor_email=saved.get("user_email", ""),
            action=f"feedback.{saved.get('sentiment')}",
            resource_type="review_feedback",
            resource_id=saved.get("id", ""),
            metadata={"run_id": saved.get("run_id"), "document_type": saved.get("document_type")},
        )
        return saved

    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    records = _read_history()
    records.insert(0, record)
    HISTORY_PATH.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
    return record


def _read_history() -> list[dict[str, Any]]:
    if is_database_enabled():
        return list_feedback_records(account_scope="all", firm_id="", user_email="")
    if not HISTORY_PATH.exists():
        return []
    try:
        value = json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if not isinstance(value, list):
        return []
    return [record for record in value if isinstance(record, dict)]


def _filter_history(
    records: list[dict[str, Any]],
    *,
    account_scope: str,
    firm_id: str,
    user_email: str,
) -> list[dict[str, Any]]:
    scope = _normalized_scope(account_scope)
    if scope == "all":
        return records
    if is_database_enabled():
        return list_feedback_records(account_scope=scope, firm_id=firm_id, user_email=user_email)
    if scope == "firm":
        return [record for record in records if record.get("account_scope") == "firm" and record.get("firm_id") == firm_id]
    if scope == "individual":
        return [
            record
            for record in records
            if record.get("account_scope") == "individual" and record.get("user_email") == user_email
        ]
    return records


def _normalized_scope(scope: str) -> str:
    normalized = (scope or "guest").lower()
    if normalized in {"firm", "individual", "all"}:
        return normalized
    return "guest"


def _host_from_url(url: str) -> str:
    value = url.strip().lower()
    value = value.removeprefix("https://").removeprefix("http://")
    return value.split("/", 1)[0].split(":", 1)[0]


def _require_database() -> None:
    if not is_database_enabled():
        raise HTTPException(status_code=503, detail="PostgreSQL is not configured. Install psycopg and set DATABASE_URL.")


def _bearer_token(request: Request) -> str:
    authorization = request.headers.get("authorization", "")
    prefix = "Bearer "
    if not authorization.startswith(prefix):
        raise HTTPException(status_code=401, detail="Missing bearer token.")
    return authorization[len(prefix) :].strip()


def _current_user(request: Request) -> dict[str, Any]:
    token = _bearer_token(request)
    user = get_user_by_session(hash_token(token))
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired session.")
    return user


def _current_user_optional(request: Request) -> dict[str, Any] | None:
    authorization = request.headers.get("authorization", "")
    if not authorization.startswith("Bearer "):
        return None
    try:
        return _current_user(request)
    except HTTPException:
        return None


def _require_senior_firm_user(user: dict[str, Any]) -> None:
    if user.get("account_type") != "firm" or user.get("role") != "senior_lawyer":
        raise HTTPException(status_code=403, detail="Only senior lawyers in firm accounts can manage invitations and assignments.")


def _langgraph_available() -> bool:
    try:
        import langgraph  # noqa: F401
    except ImportError:
        return False
    return True


def _public_user(user: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": user.get("id"),
        "firm_id": user.get("firm_id"),
        "email": user.get("email"),
        "name": user.get("full_name"),
        "accountType": user.get("account_type"),
        "role": user.get("role"),
        "email_verified": user.get("email_verified", False),
    }


def _classify_document_text(content: str, filename: str) -> dict[str, Any]:
    external_command = os.environ.get("DOCUMENT_CLASSIFIER_COMMAND", "")
    if external_command:
        security = assess_text_security(content, source=f"classifier_input:{filename}")
        if not security.allowed:
            return {
                "classifier": "security_blocked",
                "status": "blocked",
                "filename": filename,
                "security": security.to_dict(),
                **_heuristic_classification(content, filename),
            }
        try:
            completed = subprocess.run(
                classifier_command_args(external_command),
                input=json.dumps({"filename": filename, "content": content}, ensure_ascii=False),
                text=True,
                capture_output=True,
                timeout=30,
                check=False,
            )
            if completed.returncode == 0:
                parsed = json.loads(completed.stdout)
                if parsed.get("status") == "classified":
                    return parsed
                return {"classifier": "external_adapter_error", "status": "fallback", "external_error": parsed, **_heuristic_classification(content, filename)}
            return {
                "classifier": "external_adapter_error",
                "status": "fallback",
                "stderr": completed.stderr[-1000:],
                **_heuristic_classification(content, filename),
            }
        except Exception as exc:
            return {"classifier": "external_adapter_error", "status": "fallback", "error": str(exc), **_heuristic_classification(content, filename)}
    return {"classifier": "heuristic_fallback", "status": "classified", **_heuristic_classification(content, filename)}


def _heuristic_classification(content: str, filename: str) -> dict[str, Any]:
    text = f"{filename}\n{content}".lower()
    dismissal_score = sum(text.count(term) for term in ["dismissal", "termination", "employee", "employer", "labor court", "kündigung"])
    damages_score = sum(text.count(term) for term in ["damages", "breach", "loss", "compensation", "defendant", "schadensersatz"])
    if dismissal_score >= damages_score and dismissal_score > 0:
        return {
            "document_type": "dismissal_protection_suits",
            "practice_area": "Employment Law",
            "topic": "Dismissal Protection Suit",
            "pack_id": "challenge-dismissal",
            "confidence": min(0.95, 0.55 + dismissal_score / 20),
            "signals": ["employment relationship", "termination language", "labor dispute terms"],
        }
    if damages_score > 0:
        return {
            "document_type": "claims_for_damages",
            "practice_area": "Civil Law",
            "topic": "Claim for Damages",
            "pack_id": "challenge-damages",
            "confidence": min(0.95, 0.55 + damages_score / 20),
            "signals": ["damages claim", "breach/loss language", "civil dispute terms"],
        }
    return {
        "document_type": "custom_legal_documents",
        "practice_area": "Civil Law",
        "topic": "Custom legal document",
        "pack_id": "",
        "confidence": 0.35,
        "signals": ["fallback classification"],
    }


def _validate_generated_citations(*, draft_markdown: str, country: str, source_documents: list[SourceDocument]) -> dict[str, Any]:
    citations = sorted(set(re.findall(r"(?:§+\s*\d+[a-zA-Z]*|Art\.?\s*\d+[a-zA-Z]*|Article\s+\d+[a-zA-Z]*)", draft_markdown)))
    country_code = country.upper()
    allowed_domains = OFFICIAL_LEGAL_SOURCES.get(country_code, [])
    source_hosts = sorted({_host_from_url(match) for document in source_documents for match in re.findall(r"https?://[^\s)>\"]+", document.content)})
    official_source_hosts = [
        host for host in source_hosts if any(host == domain or host.endswith(f".{domain}") for domain in allowed_domains)
    ]
    status = "passed_with_official_sources" if citations and official_source_hosts else "needs_lawyer_review"
    if not citations:
        status = "needs_lawyer_review_no_citations_detected"
    return {
        "country": country_code,
        "status": status,
        "detected_citations": citations,
        "allowed_official_domains": allowed_domains,
        "official_source_hosts_seen": official_source_hosts,
        "instruction": "Citations are automatically surfaced and checked against the selected country's official-source allowlist. A lawyer must verify substantive correctness before filing.",
    }


def _markdown_to_plain_text(markdown: str) -> str:
    text = re.sub(r"`{1,3}", "", markdown)
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    return text.strip()


def _docx_from_markdown(markdown: str) -> bytes:
    paragraphs = [line.strip() for line in _markdown_to_plain_text(markdown).splitlines()]
    body = "".join(
        f"<w:p><w:r><w:t xml:space=\"preserve\">{html.escape(line)}</w:t></w:r></w:p>"
        for line in paragraphs
        if line
    )
    document_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body>{body}<w:sectPr/></w:body></w:document>"
    )
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", DOCX_CONTENT_TYPES)
        archive.writestr("_rels/.rels", DOCX_RELS)
        archive.writestr("word/document.xml", document_xml)
    return buffer.getvalue()


def _pdf_from_text(text: str) -> bytes:
    lines = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        while len(line) > 92:
            lines.append(line[:92])
            line = line[92:]
        lines.append(line)
    lines = lines[:54]
    content_lines = ["BT", "/F1 10 Tf", "50 780 Td"]
    for index, line in enumerate(lines):
        escaped = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        if index:
            content_lines.append("0 -14 Td")
        content_lines.append(f"({escaped}) Tj")
    content_lines.append("ET")
    stream = "\n".join(content_lines).encode("latin-1", errors="replace")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{index} 0 obj\n".encode("ascii"))
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")
    xref_start = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode("ascii"))
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    pdf.extend(f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_start}\n%%EOF".encode("ascii"))
    return bytes(pdf)


def _chunk_text_for_rag(text: str, *, chunk_words: int = 220) -> list[dict[str, Any]]:
    words = text.split()
    chunks = []
    for index in range(0, len(words), chunk_words):
        chunk_text = " ".join(words[index : index + chunk_words])
        if not chunk_text.strip():
            continue
        chunks.append(
            {
                "chunk_index": len(chunks),
                "heading": _first_heading(chunk_text),
                "text": chunk_text,
                "embedding_model": "hashing-128",
                "embedding_vector": _hash_embedding(chunk_text),
                "metadata": {"strategy": "word_window", "chunk_words": chunk_words},
            }
        )
    return chunks or [
        {
            "chunk_index": 0,
            "heading": "Document",
            "text": text[:4000],
            "embedding_model": "hashing-128",
            "embedding_vector": _hash_embedding(text),
            "metadata": {"strategy": "fallback"},
        }
    ]


def _first_heading(text: str) -> str:
    for line in text.splitlines():
        if line.strip().startswith("#"):
            return line.strip("# ").strip()[:160]
    return "Uploaded source"


def _hash_embedding(text: str, dimensions: int = 128) -> list[float]:
    vector = [0.0] * dimensions
    for token in text.lower().split():
        digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
        vector[int(digest[:8], 16) % dimensions] += 1.0
    length = sum(value * value for value in vector) ** 0.5 or 1.0
    return [round(value / length, 6) for value in vector]


def _support_response(message: str, category: str) -> str:
    if category == "complaint":
        return (
            "I recorded your complaint and created a ticket for the development team. "
            "Please keep the ticket number for follow-up; a representative can review the saved chat record."
        )
    if "how" in message.lower() or "use" in message.lower():
        return (
            "To use the app: choose a practice area and document type, fill required case facts, select provider/country, "
            "generate the draft, then review and save positive or negative feedback."
        )
    return "I created a support ticket and saved this chat for a representative to review."
