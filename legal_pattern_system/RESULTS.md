# Results and Evaluation

## What Was Evaluated

The prototype was evaluated on both sample document families provided in the
challenge:

- `dismissal_protection_suits` with 5 source documents
- `claims_for_damages` with 3 source documents

For each family, the system:

1. parsed all source Markdown documents,
2. learned common structure and variable fields,
3. built a reusable template JSON artifact,
4. generated a new draft from sample case data,
5. ran deterministic QA checks,
6. wrote the generated artifacts to `outputs/`.

## Commands Run

```bash
python scripts\run_pipeline.py --doc-type dismissal_protection_suits
python scripts\run_pipeline.py --doc-type claims_for_damages
python scripts\generate_sample.py --template outputs\templates\dismissal_protection_suits_template.json --case-data examples\dismissal_case_data.json --output outputs\generated_documents\example_from_json.md
python -m unittest discover -s tests
python -m compileall src scripts tests
```

## Current Output Artifacts

- `outputs/templates/dismissal_protection_suits_template.json`
- `outputs/templates/claims_for_damages_template.json`
- `outputs/generated_documents/dismissal_protection_suits_generated.md`
- `outputs/generated_documents/claims_for_damages_generated.md`
- `outputs/generated_documents/example_from_json.md`
- `outputs/qa_reports/dismissal_protection_suits_qa.json`
- `outputs/qa_reports/claims_for_damages_qa.json`

## QA Score

The QA score is a prototype quality-gate score, not a legal-validity score.

It starts at `1.0` and subtracts:

- `0.25` for each high-severity finding,
- `0.10` for each medium-severity finding.

Current scores:

| Document family | Score | Findings |
| --- | ---: | --- |
| dismissal protection suits | 1.0 | none |
| claims for damages | 1.0 | none |

See `docs/qa_score_comparison.md` for a detailed comparison between the earlier
`0.9` prototype score and the current `1.0` score.

## What Failed Earlier

The first implementation scored `0.9` because the QA agent warned that not all
learned legal citations were present in the generated draft.

The generated draft also used representative source sections. That was useful
for proving the pipeline, but it risked copying old case-specific facts into a
new matter.

## What Changed

The final pass improved five areas:

1. **Generation quality**
   - Replaced copied representative sections with canonical section bodies.
   - Preserved learned heading order and heading levels.
   - Inserted learned legal citations into legal-ground guidance.

2. **Template structure**
   - Added required sections, optional sections, variable fields, locked legal
     citations, template confidence, and source examples.

3. **QA**
   - Added Markdown-heading-aware required-section checks.
   - Added source-case leakage detection for copied names, IDs, dates,
     registrations, addresses, and company values.
   - Added section-order validation.
   - Changed citation QA to require learned citation coverage without assuming
     every citation from every source variant must appear in every draft.

4. **Tests**
   - Added tests for pattern learning, placeholder creation, generation from case
     data, old-case leakage, unresolved placeholders, and parser behavior.

5. **Documentation**
   - Added architecture diagrams, detailed README instructions, status notes, and
     this results/evaluation file.

## Current Limitations

- The default provider is still `mock` so reviewers can run the project without
  credentials, but the same agentic path can use Ollama or an OpenAI-compatible
  API provider.
- Generated legal language is intentionally conservative and requires lawyer
  review.
- Official-law validation currently uses country allowlist and audit scaffolding;
  deeper live legal retrieval and citation-text matching still need production
  integration.
- PDF, DOCX, and scanned-document ingestion are planned production adapters.
- QA is a prototype quality gate, not a legal-validity guarantee.

## Production Improvements

For a production version, I would add:

- layout-aware PDF/DOCX/OCR ingestion,
- retrieval over approved firm templates and clauses,
- structured LLM outputs with JSON schema validation,
- clause locking and redline comparison,
- template versioning and lawyer approval workflows,
- PII controls and tenant isolation,
- evaluation against lawyer edit distance and approval/rejection outcomes,
- observability for cost, latency, confidence, and failure modes.

## V2 Agentic Correction After Feedback

After feedback that the first submission was too deterministic, I added a
separate LLM-style agentic path:

```bash
python scripts\run_agentic_pipeline.py --doc-type dismissal_protection_suits
python scripts\run_agentic_pipeline.py --doc-type claims_for_damages
```

This corrected path adds:

- prompt templates in `prompts/`,
- an `LlmClient` protocol and mock structured-output provider,
- optional local Llama/Ollama and OpenAI-compatible API providers,
- retrieval grounding over parsed source sections,
- a planning step,
- draft critique and revision decision,
- per-run trace artifacts under `outputs/runs/`,
- tests for retrieval and trace generation.

This still runs without external API keys in mock mode, but can also use local
Llama through Ollama or an API-key based OpenAI-compatible provider. The control
flow now mirrors a real LLM-agent system more closely.

The web application extends this into a product-style flow with auth, profile
settings, firm admin screens, provider configuration, language selection, export
buttons, live agent status, positive/negative history, support tickets, and
production scaffolding for PostgreSQL, Redis, SMTP, payments, MCP, and official
law validation.

See:

- `docs/architecture.md`
- `docs/system_design.md`
- `docs/application_flow.md`
- `docs/production_integration_guide.md`
