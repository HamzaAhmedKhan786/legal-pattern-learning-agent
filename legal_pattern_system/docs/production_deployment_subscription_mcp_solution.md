# Production Deployment, Subscription, Data Scale, and MCP Solution

## Product Tiers

Initial commercial model:

- Free user: 20 draft generations per month.
- Firm user: 50 draft generations per month.
- Monthly subscription: EUR 6.99.
- Yearly subscription: EUR 4.99 x 12 = EUR 59.88 per year.

Recommended improvement:

- Keep the free tier useful but controlled.
- Count a "draft generation" only when the user receives a generated draft, not when validation fails.
- Add separate limits for:
  - draft generations,
  - legal verification web fetches,
  - uploaded documents,
  - stored matters,
  - team members.

Suggested production tiers:

| Tier | Users | Drafts/month | Storage | Notes |
|---|---:|---:|---:|---|
| Free | 1 | 20 | small | Trial and personal testing |
| Individual Pro | 1 | 50 | medium | EUR 6.99/month or EUR 59.88/year |
| Firm Starter | 3-5 | 150 pooled | medium | Senior/junior workflow |
| Firm Pro | 10+ | custom pooled | larger | audit, assignments, SSO later |

## Data Growth Strategy

Do not keep everything forever in the primary database.

Use three storage layers:

1. PostgreSQL for structured records.
2. Object storage for large files and generated exports.
3. Vector index for retrieval chunks and embeddings.

PostgreSQL should store:

- users,
- firms,
- subscriptions,
- usage counters,
- matters,
- draft metadata,
- feedback summaries,
- audit logs,
- pointers to object storage,
- retrieval metadata.

Object storage should store:

- uploaded PDF/DOCX/TXT files,
- OCR outputs,
- generated DOCX/PDF exports,
- full agent trace bundles,
- long draft versions.

Vector database should store:

- chunk embeddings,
- chunk IDs,
- tenant/matter/document filters,
- source type: firm precedent, public official law, user upload.

## Feedback Retention

Your idea is right: keep only the most useful positive and negative examples for learning.

Recommended retention:

- Keep all feedback metadata.
- Keep full draft text for recent records only.
- Keep selected positive/negative examples as "training candidates".
- Archive older full drafts to object storage.
- Delete or anonymize old drafts based on firm retention settings.

Recommended defaults:

- Free users:
  - keep latest 20 drafts,
  - keep latest 10 positive feedback records,
  - keep latest 10 negative feedback records.
- Individual paid users:
  - keep latest 200 drafts,
  - keep latest 100 positive and 100 negative records.
- Firm users:
  - keep metadata for all runs,
  - keep full drafts for 12 months by default,
  - keep approved template candidates indefinitely until admin deletes them,
  - archive older raw content to object storage.

Database tables to add:

- `subscriptions`
- `usage_counters`
- `retention_policies`
- `training_candidates`
- `billing_events`

Example usage table:

```sql
CREATE TABLE usage_counters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    firm_id UUID REFERENCES firms(id),
    user_id UUID REFERENCES users(id),
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    draft_generations INTEGER NOT NULL DEFAULT 0,
    legal_verifications INTEGER NOT NULL DEFAULT 0,
    uploads INTEGER NOT NULL DEFAULT 0,
    UNIQUE (firm_id, user_id, period_start)
);
```

## Limit Enforcement

Draft generation flow:

1. User requests draft.
2. Backend authenticates session.
3. Backend loads subscription.
4. Backend checks usage counter.
5. If limit reached, return upgrade/payment response.
6. If allowed, reserve one generation.
7. Run agent pipeline.
8. If generation succeeds, finalize usage.
9. If generation fails before draft output, release or mark failed.

This must be enforced server-side, not frontend-side.

## Model Hosting

For a hosted SaaS, "free local model on cloud" means you still pay cloud compute.

Good initial options:

### Option A: One GPU Server

Use one rented GPU VM running:

- FastAPI backend,
- frontend static build,
- PostgreSQL,
- Ollama or vLLM,
- Redis,
- background worker.

Best for MVP launch.

Pros:

- simple,
- cheap,
- easy to debug,
- one deployment target.

Cons:

- limited scaling,
- database and model compete for resources,
- riskier reliability.

### Option B: Split App and Model

Use:

- small CPU server for frontend/backend/PostgreSQL,
- separate GPU server for LLM inference,
- object storage,
- managed PostgreSQL if possible.

Best for early production.

Pros:

- better reliability,
- GPU can scale separately,
- easier backups,
- safer database.

Cons:

- slightly more DevOps work.

### Option C: Distributed Production

Use:

- frontend on CDN/static hosting,
- API backend containers,
- worker containers,
- managed PostgreSQL,
- Redis,
- object storage,
- vector database,
- GPU inference service,
- observability stack.

Best after real users arrive.

## Recommended Deployment Path

Start with Option B.

Initial production layout:

```text
User Browser
  |
  v
Frontend Hosting / Nginx
  |
  v
FastAPI Backend
  |
  +--> PostgreSQL
  +--> Redis
  +--> Object Storage
  +--> Vector DB / pgvector
  +--> LLM Server (Ollama or vLLM)
  +--> SMTP Provider
  +--> Payment Provider
```

For the first launch, use:

- FastAPI backend in Docker.
- React frontend as static build.
- PostgreSQL.
- Redis.
- MinIO or S3-compatible object storage.
- Ollama for easiest local/cloud model serving, or vLLM for better throughput.
- Nginx reverse proxy with TLS.

## LLM Choice

For MVP cloud inference:

- Start with `llama3.1:8b` or `qwen2.5:14b-instruct` if GPU memory allows.
- For better structured output, Qwen-style instruct models are often strong.
- For German legal drafting, test multilingual quality carefully.

Recommended production model stack:

- small/cheap model for classification, extraction, routing;
- stronger model for drafting and revision;
- embeddings model for RAG;
- reranker model for retrieval quality.

Do not fine-tune immediately. Improve RAG and prompts first.

Fine-tune later only on:

- lawyer-approved drafts,
- redline edits,
- rejected draft examples,
- official-source citation examples,
- jurisdiction-specific style examples.

## Agentic RAG Architecture

Agents/services:

1. `AuthAgent`
   - session validation,
   - role loading,
   - account scope.

2. `BillingAgent`
   - checks subscription,
   - enforces draft limits,
   - records usage.

3. `IngestionAgent`
   - receives files,
   - stores raw file in object storage,
   - extracts text,
   - OCR if needed,
   - detects PII.

4. `ChunkingAgent`
   - sections documents,
   - creates chunks,
   - stores chunk metadata.

5. `EmbeddingAgent`
   - generates embeddings,
   - writes to vector DB.

6. `RetrievalAgent`
   - retrieves firm precedent chunks,
   - retrieves official legal chunks,
   - filters by country, firm, matter, role.

7. `OfficialLawAgent`
   - only searches/fetches official domains,
   - writes audit records,
   - blocks country mismatch.

8. `DraftingAgent`
   - creates draft from case facts + retrieved chunks.

9. `CitationAgent`
   - checks citations against official sources.

10. `CritiqueAgent`
   - detects missing fields, contradictions, weak grounding.

11. `RevisionAgent`
   - revises draft based on critique.

12. `HumanReviewAgent`
   - collects approval/rejection/redlines.

13. `RetentionAgent`
   - archives/deletes old raw content based on retention policy.

## MCP Server Integration

MCP is useful when agents need tools:

- legal source search,
- document storage,
- firm case management,
- email/calendar,
- billing,
- document export,
- knowledge base.

Recommended MCP architecture:

```text
FastAPI Orchestrator
  |
  +--> MCP Client Layer
        |
        +--> Official Legal Search MCP
        +--> Document Storage MCP
        +--> Email MCP
        +--> Billing MCP
        +--> Firm DMS / CRM MCP
```

Important rule:

- Do not let the LLM call MCP tools directly without policy checks.
- The orchestrator should approve tool calls.
- Every MCP call should be logged in `audit_logs`.
- Official legal search MCP must enforce country/domain allowlists.

MCP tool-call flow:

1. Agent proposes tool call.
2. Policy layer checks tenant, role, country, allowed domain, data sensitivity.
3. MCP client executes call.
4. Result is sanitized and stored.
5. Agent receives only allowed result.
6. Audit log records request, source, user, matter, and result hash.

Do we need agents for MCP?

Yes, but use service agents, not too many autonomous agents:

- `ToolPolicyAgent`
- `OfficialLawAgent`
- `DocumentStorageAgent`
- `NotificationAgent`
- `BillingAgent`

These should be deterministic/policy-driven around the LLM, because legal-tech needs auditability.

## Payment and Subscription

Use Stripe or Paddle.

Tables:

- `plans`
- `subscriptions`
- `billing_events`
- `usage_counters`

Payment flow:

1. User selects plan.
2. Payment provider checkout.
3. Webhook updates subscription table.
4. Backend uses subscription status in limit checks.

Never trust frontend subscription state.

## Monitoring

Add:

- structured JSON logs,
- request IDs,
- Sentry or OpenTelemetry errors,
- Prometheus metrics,
- model latency,
- cost per draft,
- tokens per draft,
- retrieval coverage,
- legal verification failures,
- rejected source count,
- user limit failures,
- generation success rate.

Important dashboards:

- Draft generation latency.
- LLM/provider errors.
- RAG retrieval quality.
- User growth and limit usage.
- Positive vs negative feedback rate.
- Jurisdiction mismatch attempts.
- Storage growth.

## Production Milestones

### Milestone 1: Single-server MVP

- Docker Compose.
- PostgreSQL.
- Backend + frontend.
- Ollama/vLLM.
- Redis.
- Nginx TLS.
- Basic subscriptions.

### Milestone 2: Early SaaS

- Managed PostgreSQL.
- Object storage.
- Worker queue.
- Stripe/Paddle.
- SMTP.
- Backups.
- Sentry/logging.

### Milestone 3: Scaled SaaS

- Separate GPU inference.
- Vector DB.
- Kubernetes or managed containers.
- SSO for firms.
- Advanced RBAC.
- Data retention policies.
- Fine-tuned model after enough lawyer-reviewed data.
