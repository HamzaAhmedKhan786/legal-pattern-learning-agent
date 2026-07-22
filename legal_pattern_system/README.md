# Legal Pattern Learning Prototype

This is a proof-of-concept submission for the legal document pattern learning
challenge. It is intentionally small, dependency-free, and easy to inspect. The
main goal is to demonstrate the agentic architecture and the end-to-end workflow,
not to build a production legal drafting system.

## What This Solves

The challenge asks for a system that can learn from multiple past legal
documents, separate stable legal structure from variable case details, generate a
new firm-specific draft, and validate the output before lawyer review.

This prototype:

- parses the provided Markdown legal documents into normalized document objects,
- compares multiple examples from the same document family,
- learns stable sections, variable fields, legal citations, and repeated patterns,
- builds a reusable JSON template,
- generates a new Markdown draft from sample case details,
- runs a QA pass over the generated draft,
- documents the production architecture, tradeoffs, and answers to the three
  additional challenge questions.

## Current Scope vs. Production

Current prototype:

- uses Markdown because the provided files are Markdown,
- uses deterministic Python agents so behavior is reproducible,
- uses only the Python standard library,
- writes learned templates, generated drafts, and QA reports to disk.

Production version:

- would add PDF/DOCX/OCR parser adapters,
- would add retrieval over approved firm documents and legal knowledge,
- would use LLMs through structured-output interfaces,
- would include clause locking, redline comparison, template versioning, lawyer
  approval workflows, and observability.

## Do We Need a Frontend?

No frontend is needed for this assessment. The email explicitly says Django or
FastAPI is not required and asks for Python code plus notes. A CLI prototype is
the clearest fit.

If this were productized, a frontend would be useful for lawyer upload, template
review, redline comparison, and approval workflows. For the take-home, a frontend
would add surface area without proving the core architecture.

## Agents

The system uses software agents. They are deterministic agents in this prototype,
not autonomous LLM agents. That is deliberate: the reviewers can run the project
without API keys and inspect every decision.

- `DocumentParserAgent`: turns source files into normalized `LegalDocument`
  objects.
- `PatternDetectorAgent`: detects variable fields, required sections, repeated
  language, and legal citations across multiple examples.
- `TemplateBuilderAgent`: builds a reusable `LearnedTemplate`.
- `DocumentGeneratorAgent`: creates a new draft from the learned template and
  case data.
- `QaAgent`: checks unresolved placeholders, missing required sections, missing
  citations, and suspiciously short drafts.
- `LegalPatternOrchestrator`: coordinates the full workflow.

## Dependencies

No external libraries are required.

The project uses:

- `argparse` for CLI arguments,
- `dataclasses` for typed models,
- `json` for output artifacts,
- `pathlib` for filesystem paths,
- `re` for Markdown/field/citation extraction,
- `unittest` for tests.

This keeps setup simple. In production I would add selected dependencies such as
Pydantic, PyMuPDF/pdfplumber, python-docx, an embeddings/vector database layer,
and an LLM client with schema validation.

## What Is Dynamic?

Dynamically handled:

- number of Markdown files in a document family,
- metadata fields found in source documents,
- plaintiff/defendant fields found in source documents,
- section headings and heading levels,
- required vs. optional sections based on occurrence rate,
- legal citations found in source text,
- generated output paths by document type,
- QA findings based on generated content.

Hardcoded only for prototype/demo convenience:

- the two sample document family names used by the challenge,
- small sample case data inside `scripts/run_pipeline.py`,
- QA thresholds such as required section occurrence rate and short-document word
  count.

Those hardcoded items are isolated and easy to replace with CLI JSON input,
configuration, or a database in a production version.

## Folder Structure

```text
legal_pattern_system/
  README.md
  pyproject.toml
  src/legal_pattern_system/
    models.py
    agents/
      document_parser.py
      pattern_detector.py
      template_builder.py
      document_generator.py
      qa_agent.py
      orchestrator.py
    utils/
      section_parser.py
      text_cleaning.py
  scripts/
    run_pipeline.py
    generate_sample.py
    evaluate_outputs.py
  docs/
    architecture.md
    design_decisions.md
    additional_questions.md
    loom_script.md
  outputs/
    templates/
    generated_documents/
    qa_reports/
  tests/
    test_parser.py
```

## How To Run

Open a terminal in this folder:

```bash
cd C:\Users\DELL\Documents\Tasks\JUPUS\ai-challenge\legal_pattern_system
```

Run the full pipeline for dismissal protection suits:

```bash
python scripts\run_pipeline.py --doc-type dismissal_protection_suits
```

Run the full pipeline for claims for damages:

```bash
python scripts\run_pipeline.py --doc-type claims_for_damages
```

Run the corrected LLM-style agentic pipeline:

```bash
python scripts\run_agentic_pipeline.py --doc-type dismissal_protection_suits
python scripts\run_agentic_pipeline.py --doc-type claims_for_damages
```

This agentic path adds the missing AI-engineering layer:

- planning step,
- prompt templates in `prompts/`,
- retrieval grounding over parsed source sections,
- structured mock-LLM outputs,
- draft critique,
- revision decision,
- run traces in `outputs/runs/`.

Run tests:

```bash
python -m unittest discover -s tests
```

Compile-check the code:

```bash
python -m compileall src scripts tests
```

## Inputs

The full pipeline reads source examples from:

```text
../sample_documents/dismissal_protection_suits/*.md
../sample_documents/claims_for_damages/*.md
```

The demo case data is currently inside `scripts/run_pipeline.py` under
`SAMPLE_CASES`.

To generate from a saved template and your own case-data JSON:

```bash
python scripts\generate_sample.py --template outputs\templates\dismissal_protection_suits_template.json --case-data examples\dismissal_case_data.json --output outputs\generated_documents\my_generated.md
```

Example case-data files are included:

- `examples/dismissal_case_data.json`
- `examples/damages_case_data.json`

Example structure:

```json
{
  "case_no": "DPS-2024-999",
  "court": "Labor Court Berlin",
  "date_filed": "June 20, 2024",
  "plaintiff_name": "Example Employee",
  "plaintiff_address": "Example Street 1, 10115 Berlin, Germany",
  "defendant_company": "Example Employer GmbH",
  "defendant_address": "Employer Avenue 10, 10117 Berlin, Germany"
}
```

## Outputs

The pipeline writes:

- `outputs/templates/<doc_type>_template.json`
- `outputs/generated_documents/<doc_type>_generated.md`
- `outputs/qa_reports/<doc_type>_qa.json`
- `outputs/runs/<doc_type>_<run_id>/`

## Design Notes

See:

- `docs/architecture.md`
- `docs/design_decisions.md`
- `docs/additional_questions.md`
- `docs/loom_script.md`
- `docs/qa_score_comparison.md`
- `docs/v2_agentic_corrections.md`
- `RESULTS.md`

## Future Production Suggestions

For production, I would keep this prototype's agent boundaries but replace the
lightweight internals with more robust services and review workflows.

My next production improvements would be:

- Add PDF, DOCX, and OCR ingestion adapters so the same downstream agents can
  work with real law-firm documents, not only Markdown samples.
- Add retrieval over approved firm templates, prior filings, and clause libraries
  so generation is grounded in reviewed source material.
- Introduce LLMs through structured-output contracts for semantic clause
  classification, template-variable suggestions, and controlled draft
  generation.
- Add locked clauses and redline comparison so critical legal language cannot be
  silently rewritten.
- Add a lawyer approval workflow for templates, generated drafts, low-confidence
  sections, and agent disagreements.
- Track lawyer edits after review and use that feedback as an evaluation signal
  for future template improvements.
- Add jurisdiction-specific rule checks, citation validation, PII controls,
  audit logs, and tenant isolation.
- Add observability for latency, cost, parser confidence, template confidence,
  QA findings, and post-review edit distance.

My production direction would be to treat the AI as a drafting and pattern
learning assistant, while keeping lawyers in control of legal judgment,
template approval, and final filing decisions.
