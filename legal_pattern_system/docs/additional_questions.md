# Additional Questions

## 1. Pattern Detection Architecture

I would use a layered approach that separates layout structure from legal
semantics.

For structure, the system should extract headings, hierarchy, section order,
numbered lists, party blocks, signature blocks, tables, and formatting cues. For
Markdown this is simple; for PDFs and DOCX files the ingestion layer should
preserve layout coordinates, font styles, page breaks, and numbering. Long
documents should be chunked by logical section rather than arbitrary token
windows.

For semantics, I would combine deterministic NLP, embeddings, and LLM structured
outputs. Deterministic rules identify obvious fields, citations, dates, money
amounts, parties, and headings. Embeddings cluster semantically similar clauses
even when wording differs. LLMs classify clause roles, summarize factual
patterns, and propose variable slots, but their output should be schema-validated
and traceable to source spans.

Patterns should be stored as versioned template objects with source references:
required sections, optional sections, locked clauses, variable fields,
conditional rules, examples, confidence scores, and lawyer approval state.

Validation should combine automated checks and human review. Automated checks
measure consistency across examples, section coverage, citation preservation,
and similarity to approved clauses. A lawyer should approve templates before
they are used for real drafting.

When documents do not fit known patterns, the system should not force them into
the nearest template. It should flag low similarity, create a candidate variant,
and route it to review.

## 2. Template Flexibility vs. Legal Accuracy

I would represent templates as structured documents, not as one long prompt.
Each block would have a type:

- locked legal language,
- variable field,
- conditional clause,
- generated factual narrative,
- lawyer-approved optional clause.

Locked content cannot be rewritten by the generator. Variable fields can be
filled from case data. Conditional clauses run only when jurisdiction, claim
type, fact pattern, or lawyer selection requires them.

Safeguards:

- schema validation for required data,
- clause-level permissions,
- redline diff against approved language,
- citation checks,
- jurisdiction checks,
- QA gate before lawyer review,
- audit log for every generated draft.

For example, a California employment clause should require both a jurisdiction
condition and an approved clause source. If those are missing, the system should
ask for legal review rather than invent language.

Lawyers should approve initial templates, approve changes to locked clauses,
resolve low-confidence cases, and provide feedback after reviewing drafts. Their
edits become evaluation data and candidate improvements, not automatic silent
training updates.

## 3. Handling Edge Cases and Ambiguity

The system should treat ambiguity as a first-class state.

For a document that is 80% similar to a known pattern but significantly
different, I would produce a similarity report showing matched sections, missing
sections, new clauses, and legal-risk differences. The system can create a draft
candidate, but it should mark the template match as partial and require review.

Potential source errors can be detected through cross-document comparison,
schema checks, date consistency checks, citation checks, and outlier detection.
For example, if all dismissal suits include a works council issue except one,
the system should ask whether that is a real case difference or a missing
section.

The system should identify cases requiring legal research by looking for new
jurisdictions, unfamiliar statutes, unseen claim types, unusual remedies, missing
precedent support, or low retrieval coverage. In those cases, generation should
degrade into an assisted research/review workflow.

Confidence scoring should combine:

- parser confidence,
- template similarity,
- field completeness,
- retrieval coverage,
- generation constraints passed,
- QA score,
- historical lawyer edit distance for that template.

Graceful degradation means producing less automation when risk rises:

- high confidence: generate full draft with QA report,
- medium confidence: generate draft with warnings,
- low confidence: create outline and issue list,
- critical uncertainty: block generation and request lawyer input.

Human-in-the-loop controls should include approval queues, inline comments,
redline review, reason-coded rejections, and feedback capture for future
template versions.

