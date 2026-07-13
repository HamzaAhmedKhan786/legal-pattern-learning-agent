# QA Score Comparison

This note compares the earlier prototype QA behavior with the current final QA
behavior. It is useful for explaining the evaluation/iteration loop in the
walkthrough.

## How the QA Score Is Calculated

The QA score is a prototype quality-gate score. It is not a legal-validity score.

The scoring logic lives in:

```text
src/legal_pattern_system/agents/qa_agent.py
```

Calculation:

```text
score starts at 1.0

for each high-severity finding:
  subtract 0.25

for each medium-severity finding:
  subtract 0.10

final score is never below 0.0
```

Examples:

```text
1 medium finding:
1.0 - 0.10 = 0.90

1 high finding:
1.0 - 0.25 = 0.75

no findings:
1.0 = 1.00
```

## Earlier QA Result

Earlier in the prototype, both document families produced a QA score of `0.9`.

The exact old QA report preserved from the chat history was for
`dismissal_protection_suits`:

```json
{
  "document_type": "dismissal_protection_suits",
  "score": 0.9,
  "findings": [
    {
      "severity": "medium",
      "message": "Template citations not present in generated draft: Â§ 1 Abs. 3 KSchG, Â§ 622 BGB, Â§ 102 BetrVG",
      "agent": "qa_agent"
    }
  ]
}
```

Why it scored `0.9`:

```text
starting score: 1.0
1 medium finding: -0.10
final score: 0.90
```

The old `claims_for_damages` run was also observed at `0.9`, but the exact old
JSON report was not saved as a file. Based on the recorded run output, it had
the same score class: one medium-level QA issue and no high-severity issue.

## What Was Missing Before

The first version worked end to end, but the QA and generation were still basic.

Before:

- generated sections used representative source text,
- old case-specific text could leak into a new draft,
- citation checking expected too many source citations to appear,
- template metadata was thinner,
- QA did not check old source-case values,
- QA did not check section order,
- tests covered only the parser.

The key problem:

The system proved the pipeline, but the generated document still looked closer
to a copied prior case section than a clean reusable draft.

## Current QA Result

Current QA reports:

```json
{
  "document_type": "dismissal_protection_suits",
  "score": 1.0,
  "findings": []
}
```

```json
{
  "document_type": "claims_for_damages",
  "score": 1.0,
  "findings": []
}
```

Why they score `1.0`:

```text
starting score: 1.0
0 high findings: -0.00
0 medium findings: -0.00
final score: 1.00
```

## What Changed to Reach 1.0

### Generation Improvements

Before:

- used the longest representative section from source documents.

Now:

- generates cleaner canonical sections,
- preserves learned heading order and levels,
- fills fields from case-data JSON,
- avoids copying old source-case facts,
- includes learned citations in the legal-ground guidance.

### Template Improvements

Before:

- stored basic sections, fields, citations, and placeholders.

Now:

- also stores required sections,
- optional sections,
- variable fields,
- locked legal citations,
- template confidence,
- source examples.

### QA Improvements

Before:

- checked unresolved placeholders,
- missing required sections,
- missing expected citations,
- short draft length.

Now:

- checks unresolved placeholders,
- checks required Markdown headings more accurately,
- checks citation coverage more realistically,
- detects old source-case leakage,
- checks section order,
- flags short drafts,
- avoids false positives for acceptable reused court/venue names.

### Test Improvements

Before:

- parser test only.

Now:

- parser test,
- pattern learning test,
- placeholder creation test,
- generation from case data test,
- source-leakage QA test,
- unresolved-placeholder QA test.

## Short Explanation for Discussion

The first version scored `0.9` because QA found one medium citation issue. After
the final improvement pass, the generator became less copy-based and QA became
more targeted. The current outputs have no unresolved placeholders, no missing
required sections, learned citations are represented, section order is preserved,
and old source-case values are not leaking into the generated drafts. Therefore
the current prototype QA score is `1.0`.

