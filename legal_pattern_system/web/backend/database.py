from __future__ import annotations

import json
import os
from datetime import date
from uuid import UUID
from pathlib import Path
from typing import Any

try:
    import psycopg
    from psycopg.rows import dict_row
except ImportError:  # pragma: no cover - optional production dependency
    psycopg = None
    dict_row = None


DEFAULT_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/legal_pattern_system"


def database_url() -> str:
    return os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)


def is_database_enabled() -> bool:
    return psycopg is not None and bool(os.environ.get("DATABASE_URL"))


def connection():
    if psycopg is None:
        raise RuntimeError("Install psycopg with: pip install -r requirements-web.txt")
    return psycopg.connect(database_url(), row_factory=dict_row)


def init_database() -> None:
    schema_path = Path(__file__).with_name("schema.sql")
    with connection() as conn:
      with conn.cursor() as cur:
          cur.execute(schema_path.read_text(encoding="utf-8"))
      conn.commit()


def create_user_account(
    *,
    email: str,
    full_name: str,
    password_hash: str,
    account_type: str,
    role: str,
    firm_name: str = "",
) -> dict[str, Any]:
    with connection() as conn:
        with conn.cursor() as cur:
            firm_id = None
            if account_type == "firm":
                cur.execute(
                    """
                    INSERT INTO firms (name)
                    VALUES (%s)
                    RETURNING id::text;
                    """,
                    (firm_name or f"{full_name} Firm",),
                )
                row = cur.fetchone()
                firm_id = row["id"]
            cur.execute(
                """
                INSERT INTO users (firm_id, email, full_name, password_hash, account_type, role)
                VALUES (NULLIF(%(firm_id)s, '')::uuid, %(email)s, %(full_name)s, %(password_hash)s, %(account_type)s, %(role)s)
                RETURNING id::text, firm_id::text, email, full_name, account_type, role, email_verified;
                """,
                {
                    "firm_id": firm_id or "",
                    "email": email.lower(),
                    "full_name": full_name,
                    "password_hash": password_hash,
                    "account_type": account_type,
                    "role": role,
                },
            )
            user = cur.fetchone()
        conn.commit()
    return user


def get_user_by_email(email: str) -> dict[str, Any] | None:
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id::text, firm_id::text, email, full_name, password_hash, account_type, role, email_verified
                FROM users
                WHERE email = %s;
                """,
                (email.lower(),),
            )
            return cur.fetchone()


def create_session(*, user_id: str, token_hash: str, expires_at: Any) -> None:
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO user_sessions (user_id, token_hash, expires_at) VALUES (%s::uuid, %s, %s);",
                (user_id, token_hash, expires_at),
            )
        conn.commit()


def get_user_by_session(token_hash: str) -> dict[str, Any] | None:
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT u.id::text, u.firm_id::text, u.email, u.full_name, u.account_type, u.role, u.email_verified
                FROM user_sessions s
                JOIN users u ON u.id = s.user_id
                WHERE s.token_hash = %s
                  AND s.revoked_at IS NULL
                  AND s.expires_at > now();
                """,
                (token_hash,),
            )
            return cur.fetchone()


def update_user_profile(*, user_id: str, full_name: str, email: str, account_type: str, role: str) -> dict[str, Any]:
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE users
                SET full_name = %s, email = %s, account_type = %s, role = %s, updated_at = now()
                WHERE id = %s::uuid
                RETURNING id::text, firm_id::text, email, full_name, account_type, role, email_verified;
                """,
                (full_name, email.lower(), account_type, role, user_id),
            )
            user = cur.fetchone()
        conn.commit()
    return user


def save_provider_config(
    *,
    user_id: str,
    firm_id: str,
    provider: str,
    model: str,
    base_url: str,
    encrypted_api_key: bytes | None,
    legal_country: str,
) -> dict[str, Any]:
    scope_field = "firm_id" if firm_id else "user_id"
    scope_value = firm_id or user_id
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                DELETE FROM provider_configs
                WHERE {scope_field} = %s::uuid AND provider = %s;
                """,
                (scope_value, provider),
            )
            cur.execute(
                """
                INSERT INTO provider_configs (firm_id, user_id, provider, model, base_url, encrypted_api_key, legal_country)
                VALUES (NULLIF(%(firm_id)s, '')::uuid, NULLIF(%(user_id)s, '')::uuid, %(provider)s, %(model)s, %(base_url)s, %(encrypted_api_key)s, %(legal_country)s)
                RETURNING id::text, provider, model, base_url, legal_country, encrypted_api_key IS NOT NULL AS has_api_key;
                """,
                {
                    "firm_id": firm_id,
                    "user_id": "" if firm_id else user_id,
                    "provider": provider,
                    "model": model,
                    "base_url": base_url,
                    "encrypted_api_key": encrypted_api_key,
                    "legal_country": legal_country,
                },
            )
            config = cur.fetchone()
        conn.commit()
    return config


def get_provider_configs(*, user_id: str, firm_id: str) -> list[dict[str, Any]]:
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id::text, provider, model, base_url, legal_country, encrypted_api_key IS NOT NULL AS has_api_key
                FROM provider_configs
                WHERE (firm_id = NULLIF(%(firm_id)s, '')::uuid)
                   OR (user_id = %(user_id)s::uuid)
                ORDER BY updated_at DESC;
                """,
                {"firm_id": firm_id, "user_id": user_id},
            )
            return cur.fetchall()


def get_or_create_subscription(*, user_id: str, firm_id: str, account_type: str) -> dict[str, Any]:
    owner_column = "firm_id" if account_type == "firm" and firm_id else "user_id"
    owner_value = firm_id if owner_column == "firm_id" else user_id
    default_limit = 50 if owner_column == "firm_id" else 20
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT * FROM subscriptions WHERE {owner_column} = %s::uuid AND status = 'active' LIMIT 1;", (owner_value,))
            subscription = cur.fetchone()
            if not subscription:
                cur.execute(
                    f"""
                    INSERT INTO subscriptions ({owner_column}, plan_code, draft_limit)
                    VALUES (%s::uuid, %s, %s)
                    RETURNING *;
                    """,
                    (owner_value, "firm_free" if owner_column == "firm_id" else "free", default_limit),
                )
                subscription = cur.fetchone()
        conn.commit()
    return _row_dates(subscription)


def usage_snapshot(*, user_id: str, firm_id: str, account_type: str) -> dict[str, Any]:
    subscription = get_or_create_subscription(user_id=user_id, firm_id=firm_id, account_type=account_type)
    owner_column = "firm_id" if account_type == "firm" and firm_id else "user_id"
    owner_value = firm_id if owner_column == "firm_id" else user_id
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT * FROM usage_counters
                WHERE {owner_column} = %s::uuid
                  AND period_start = %s
                  AND period_end = %s
                LIMIT 1;
                """,
                (owner_value, subscription["current_period_start"], subscription["current_period_end"]),
            )
            usage = cur.fetchone()
            if not usage:
                cur.execute(
                    f"""
                    INSERT INTO usage_counters ({owner_column}, period_start, period_end)
                    VALUES (%s::uuid, %s, %s)
                    RETURNING *;
                    """,
                    (owner_value, subscription["current_period_start"], subscription["current_period_end"]),
                )
                usage = cur.fetchone()
        conn.commit()
    return {"subscription": subscription, "usage": _row_dates(usage)}


def reserve_draft_generation(*, user_id: str, firm_id: str, account_type: str) -> dict[str, Any]:
    snapshot = usage_snapshot(user_id=user_id, firm_id=firm_id, account_type=account_type)
    subscription = snapshot["subscription"]
    usage = snapshot["usage"]
    if usage["draft_generations"] >= subscription["draft_limit"]:
        return {"allowed": False, "subscription": subscription, "usage": usage}
    owner_column = "firm_id" if account_type == "firm" and firm_id else "user_id"
    owner_value = firm_id if owner_column == "firm_id" else user_id
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                UPDATE usage_counters
                SET draft_generations = draft_generations + 1, updated_at = now()
                WHERE {owner_column} = %s::uuid
                  AND period_start = %s
                  AND period_end = %s
                RETURNING *;
                """,
                (owner_value, subscription["current_period_start"], subscription["current_period_end"]),
            )
            updated = cur.fetchone()
        conn.commit()
    return {"allowed": True, "subscription": subscription, "usage": _row_dates(updated)}


def create_or_update_subscription_from_payment(*, user_email: str, plan_code: str, billing_interval: str, status: str, draft_limit: int) -> dict[str, Any]:
    user = get_user_by_email(user_email)
    if not user:
        raise ValueError("Unknown user for subscription webhook.")
    owner_column = "firm_id" if user["account_type"] == "firm" and user.get("firm_id") else "user_id"
    owner_value = user["firm_id"] if owner_column == "firm_id" else user["id"]
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute(f"DELETE FROM subscriptions WHERE {owner_column} = %s::uuid;", (owner_value,))
            cur.execute(
                f"""
                INSERT INTO subscriptions ({owner_column}, plan_code, billing_interval, status, draft_limit)
                VALUES (%s::uuid, %s, %s, %s, %s)
                RETURNING *;
                """,
                (owner_value, plan_code, billing_interval, status, draft_limit),
            )
            subscription = cur.fetchone()
        conn.commit()
    return _row_dates(subscription)


def save_document_chunks(*, firm_id: str, user_id: str, filename: str, content_type: str, sha256: str, text: str, chunks: list[dict[str, Any]]) -> dict[str, Any]:
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO document_assets (firm_id, uploaded_by, filename, content_type, storage_uri, sha256, pii_classification)
                VALUES (NULLIF(%(firm_id)s, '')::uuid, %(user_id)s::uuid, %(filename)s, %(content_type)s, %(storage_uri)s, %(sha256)s, 'needs_review')
                RETURNING id::text;
                """,
                {
                    "firm_id": firm_id,
                    "user_id": user_id,
                    "filename": filename,
                    "content_type": content_type,
                    "storage_uri": f"postgres://document_assets/{sha256}",
                    "sha256": sha256,
                },
            )
            asset_id = cur.fetchone()["id"]
            for chunk in chunks:
                cur.execute(
                    """
                    INSERT INTO rag_chunks (document_asset_id, firm_id, chunk_index, heading, text, token_count, embedding_model, embedding_vector, metadata)
                    VALUES (%s::uuid, NULLIF(%s, '')::uuid, %s, %s, %s, %s, %s, %s, %s::jsonb);
                    """,
                    (
                        asset_id,
                        firm_id,
                        chunk["chunk_index"],
                        chunk.get("heading", ""),
                        chunk["text"],
                        len(chunk["text"].split()),
                        chunk.get("embedding_model", "hashing-128"),
                        chunk.get("embedding_vector", []),
                        json.dumps(chunk.get("metadata", {}), ensure_ascii=False),
                    ),
                )
        conn.commit()
    return {"asset_id": asset_id, "chunks_saved": len(chunks)}


def search_rag_chunks(*, firm_id: str, query_terms: list[str], limit: int = 6) -> list[dict[str, Any]]:
    pattern = " | ".join(query_terms) if query_terms else ""
    with connection() as conn:
        with conn.cursor() as cur:
            if pattern:
                cur.execute(
                    """
                    SELECT id::text, heading, text, filename, ts_rank_cd(to_tsvector('simple', text), plainto_tsquery('simple', %s)) AS score
                    FROM rag_chunks
                    JOIN document_assets ON document_assets.id = rag_chunks.document_asset_id
                    WHERE (rag_chunks.firm_id = NULLIF(%s, '')::uuid OR %s = '')
                      AND to_tsvector('simple', text) @@ plainto_tsquery('simple', %s)
                    ORDER BY score DESC
                    LIMIT %s;
                    """,
                    (" ".join(query_terms), firm_id, firm_id, " ".join(query_terms), limit),
                )
            else:
                cur.execute(
                    """
                    SELECT id::text, heading, text, filename, 0.0 AS score
                    FROM rag_chunks
                    JOIN document_assets ON document_assets.id = rag_chunks.document_asset_id
                    WHERE (rag_chunks.firm_id = NULLIF(%s, '')::uuid OR %s = '')
                    ORDER BY rag_chunks.created_at DESC
                    LIMIT %s;
                    """,
                    (firm_id, firm_id, limit),
                )
            return cur.fetchall()


def list_learned_draft_chunks(*, firm_id: str, limit: int = 20) -> list[dict[str, Any]]:
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT rag_chunks.id::text, rag_chunks.heading, rag_chunks.text, document_assets.filename,
                       rag_chunks.metadata, rag_chunks.created_at
                FROM rag_chunks
                JOIN document_assets ON document_assets.id = rag_chunks.document_asset_id
                WHERE (rag_chunks.firm_id = NULLIF(%s, '')::uuid OR %s = '')
                  AND rag_chunks.metadata @> '{"learned_draft": true}'::jsonb
                ORDER BY rag_chunks.created_at DESC
                LIMIT %s;
                """,
                (firm_id, firm_id, limit),
            )
            return cur.fetchall()


def audit_mcp_tool(*, actor_email: str, tool_name: str, policy_decision: str, country: str, request_payload: dict[str, Any], response_summary: dict[str, Any]) -> dict[str, Any]:
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO mcp_tool_audits (actor_email, tool_name, policy_decision, country, request_payload, response_summary)
                VALUES (%s, %s, %s, %s, %s::jsonb, %s::jsonb)
                RETURNING id::text, created_at;
                """,
                (
                    actor_email,
                    tool_name,
                    policy_decision,
                    country,
                    json.dumps(request_payload, ensure_ascii=False),
                    json.dumps(response_summary, ensure_ascii=False),
                ),
            )
            row = cur.fetchone()
        conn.commit()
    return {"id": row["id"], "created_at": row["created_at"].isoformat()}


def create_support_ticket(*, user_email: str, subject: str, message: str, category: str, assistant_message: str) -> dict[str, Any]:
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 'TCK-' || to_char(now(), 'YYYYMMDD') || '-' || lpad((count(1) + 1)::text, 4, '0') AS ticket_no FROM support_tickets;")
            ticket_no = cur.fetchone()["ticket_no"]
            cur.execute(
                """
                INSERT INTO support_tickets (ticket_no, user_email, subject, message, category)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id::text, ticket_no, status, created_at;
                """,
                (ticket_no, user_email, subject, message, category),
            )
            ticket = cur.fetchone()
            cur.execute(
                """
                INSERT INTO chat_messages (ticket_id, user_email, role, message)
                VALUES (%s::uuid, %s, 'user', %s), (%s::uuid, %s, 'assistant', %s);
                """,
                (ticket["id"], user_email, message, ticket["id"], user_email, assistant_message),
            )
        conn.commit()
    return {**ticket, "created_at": ticket["created_at"].isoformat(), "assistant_message": assistant_message}


def save_feedback_record(record: dict[str, Any]) -> dict[str, Any]:
    firm_id = _uuid_or_empty(str(record.get("firm_id", "")))
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO review_feedback (
                    run_id, firm_id, user_email, account_scope, sentiment, document_type,
                    comment, draft_markdown, case_data, qa_score, reviewer
                )
                VALUES (
                    %(run_id)s, NULLIF(%(firm_id)s, '')::uuid, %(user_email)s, %(account_scope)s,
                    %(sentiment)s, %(document_type)s, %(comment)s, %(draft_markdown)s,
                    %(case_data)s::jsonb, %(qa_score)s, %(reviewer)s
                )
                RETURNING id::text, created_at;
                """,
                {**record, "firm_id": firm_id, "case_data": json.dumps(record.get("case_data", {}), ensure_ascii=False)},
            )
            saved = cur.fetchone()
        conn.commit()
    return {**record, "id": saved["id"], "created_at": saved["created_at"].isoformat()}


def list_feedback_records(*, account_scope: str, firm_id: str, user_email: str) -> list[dict[str, Any]]:
    where = ""
    params: dict[str, Any] = {}
    if account_scope == "firm":
        where = "WHERE account_scope = 'firm' AND firm_id = %(firm_id)s::uuid"
        params["firm_id"] = firm_id
    elif account_scope == "individual":
        where = "WHERE account_scope = 'individual' AND user_email = %(user_email)s"
        params["user_email"] = user_email

    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT id::text, created_at, run_id, sentiment, comment, document_type,
                       draft_markdown, case_data, qa_score, reviewer, account_scope,
                       COALESCE(firm_id::text, '') AS firm_id, user_email
                FROM review_feedback
                {where}
                ORDER BY created_at DESC
                LIMIT 200;
                """,
                params,
            )
            rows = cur.fetchall()
    return [
        {
            **row,
            "created_at": row["created_at"].isoformat(),
            "case_data": row.get("case_data") or {},
        }
        for row in rows
    ]


def write_audit_log(*, actor_email: str, action: str, resource_type: str, resource_id: str = "", metadata: dict[str, Any] | None = None) -> None:
    if not is_database_enabled():
        return
    try:
        with connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO audit_logs (actor_email, action, resource_type, resource_id, metadata)
                    VALUES (%s, %s, %s, %s, %s::jsonb);
                    """,
                    (actor_email, action, resource_type, resource_id, json.dumps(metadata or {}, ensure_ascii=False)),
                )
            conn.commit()
    except Exception:
        return


def _uuid_or_empty(value: str) -> str:
    try:
        return str(UUID(value))
    except ValueError:
        return ""


def _row_dates(row: dict[str, Any]) -> dict[str, Any]:
    result = dict(row)
    for key, value in list(result.items()):
        if hasattr(value, "isoformat"):
            result[key] = value.isoformat()
    return result
