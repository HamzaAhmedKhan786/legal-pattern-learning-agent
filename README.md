# Legal Document Pattern Learning System

## Solution

The implemented proof-of-concept is in:

```text
legal_pattern_system/
```

The written answers to the three additional challenge questions are in:

```text
legal_pattern_system/docs/additional_questions.md
```

Main solution documentation:

```text
legal_pattern_system/README.md
legal_pattern_system/RESULTS.md
legal_pattern_system/docs/architecture.md
legal_pattern_system/docs/design_decisions.md
legal_pattern_system/docs/qa_score_comparison.md
legal_pattern_system/docs/v2_agentic_corrections.md
legal_pattern_system/docs/production_web_plan.md
```

The runnable scripts are in:

```text
legal_pattern_system/scripts/
```

Run from the solution folder:

```bash
cd legal_pattern_system
```

Run the full learning/generation/QA pipeline:

```bash
python scripts\run_pipeline.py --doc-type dismissal_protection_suits
python scripts\run_pipeline.py --doc-type claims_for_damages
```

Run the corrected LLM-style agentic pipeline with planning, retrieval,
structured LLM outputs, critique/revision, and trace artifacts:

```bash
python scripts\run_agentic_pipeline.py --doc-type dismissal_protection_suits
python scripts\run_agentic_pipeline.py --doc-type claims_for_damages
```

Optional real LLM modes:

```bash
python scripts\run_agentic_pipeline.py --doc-type dismissal_protection_suits --llm ollama --model llama3.1
python scripts\run_agentic_pipeline.py --doc-type dismissal_protection_suits --llm openai-compatible --model gpt-4o-mini
```

Generate a draft from a saved template and example case-data JSON:

```bash
python scripts\generate_sample.py --template outputs\templates\dismissal_protection_suits_template.json --case-data examples\dismissal_case_data.json --output outputs\generated_documents\example_from_json.md
```

Evaluate an existing generated draft:

```bash
python scripts\evaluate_outputs.py --template outputs\templates\dismissal_protection_suits_template.json --draft outputs\generated_documents\example_from_json.md --output outputs\qa_reports\example_from_json_qa.json
```

Run checks:

```bash
python -m unittest discover -s tests
python -m compileall src scripts tests
```

Outputs are written to:

```text
legal_pattern_system/outputs/templates/
legal_pattern_system/outputs/generated_documents/
legal_pattern_system/outputs/qa_reports/
legal_pattern_system/outputs/runs/
```

## Overview

Welcome to our technical challenge for the AI Engineer position. This challenge is designed to evaluate your ability to design sophisticated AI systems, think through complex technical problems, and demonstrate deep understanding of modern AI approaches.

**Format**: This is a design and architecture challenge, not an implementation exercise. We want to see your thinking process, technical depth, and system design capabilities. See **Delivery and Discussion** at the end for more details.

## The Business Problem

Law firms generate hundreds of similar legal documents that follow specific patterns but vary in case-specific details. Currently, lawyers either:

- Manually draft each document from scratch (time-intensive, inconsistent)
- Use basic static templates (inflexible, requires manual adaptation)
- Copy-paste from previous cases (error-prone, may miss important updates)

This results in:

- **Inefficiency**: Senior lawyers spending hours on routine document drafting
- **Inconsistency**: Varying quality and structure across documents
- **Risk**: Potential errors or omissions in critical legal language
- **Scalability Issues**: Difficulty handling increased caseloads

## The Technical Challenge

### User Workflow Vision

Imagine this user experience:

1. **Document Upload**: A lawyer uploads 10 dismissal protection suits from their firm's past cases
2. **Pattern Learning**: The system automatically analyzes these documents to understand the firm's specific style, preferred legal language, and structural patterns. Since the lawyer uploads multiple documents of the same type, we need to make sure the patterns and templates are “learned” from these multiple documents, not just a single one.
3. **Template Generation**: The AI creates a flexible template that captures the firm's approach while identifying variable elements (names, dates, case-specific facts)
4. **New Case Generation**: When a new wrongful termination case arrives, the lawyer inputs basic case details (employee name, termination date, circumstances) and the system generates a complete, firm-specific legal document
5. **Quality Review**: The lawyer reviews, makes minor edits, and the system learns from these modifications

### Core Technical Challenge

Design an intelligent agentic system that can:

1. **Learn from Examples**: Analyze multiple similar legal documents to automatically detect structural and content patterns
2. **Extract Flexible Templates**: Create reusable templates that capture both fixed legal language and variable elements
3. **Generate New Documents**: Use learned patterns + new case details to draft high-quality legal documents
4. **Ensure Quality**: Validate generated content for consistency, completeness, and legal accuracy
5. **Adapt and Improve**: Learn from lawyer feedback and new document types

This system requires multiple specialized AI agents working together - document analysis, pattern detection, template generation, document creation, and quality assurance.

Design the multi-agent architecture, including agent responsibilities, communication patterns, and coordination mechanisms. How would you handle conflicts between agents and ensure system reliability?

**Consider**:

- What specific agents would you create and what would each be responsible for?
- How would agents communicate and share state/knowledge?
- What happens when agents disagree (e.g., pattern detection vs. quality assurance)?
- How would you handle agent failures and ensure system resilience?
- How would you orchestrate the overall workflow from document upload to final generation?
- What monitoring and debugging capabilities would you build in?

## Sample Data

We've provided sample legal documents in two categories:

- **Dismissal Protection Suits** (5 examples): Employment law cases challenging wrongful termination
- **Claims for Damages** (3 examples): Commercial disputes seeking monetary compensation

These documents are an extremely simplified example but the principles apply broadly to legal document generation.

## Additional Questions

## Question 1: Pattern Detection Architecture

**Scenario**: You need to automatically detect patterns in legal documents that vary significantly in length, structure, and complexity. Some documents are 2 pages, others are 20+ pages. Some follow strict templates, others are more free-form.

**Question**: Design a comprehensive approach for detecting both structural patterns (sections, hierarchies, formatting) and semantic patterns (legal arguments, clause types, language patterns) across diverse legal documents.

**Consider**:

- How would you handle documents of vastly different lengths and structures?
- What combination of traditional NLP and modern LLM techniques would you use?
- How would you represent and store discovered patterns for reuse?
- How would you validate that detected patterns are meaningful and legally sound?
- What would you do when documents don't fit discovered patterns?

---

## Question 2: Template Flexibility vs. Legal Accuracy

**Scenario**: Legal documents require extreme precision - a single word change can have significant legal implications. However, templates need flexibility to handle diverse cases and jurisdictions.

**Question**: How would you design a template system that balances maximum flexibility for case variations while maintaining strict legal accuracy and compliance requirements?

**Consider**:

- How do you represent "flexible" vs. "fixed" content in templates?
- What safeguards would prevent AI from modifying critical legal language?
- How would you handle conditional logic (e.g., "include this clause only for employment cases in California")?
- How would you validate that generated documents maintain legal validity?
- What role should human lawyers play in template creation and validation?

---

## Question 3: Handling Edge Cases and Ambiguity

**Scenario**: Real-world legal documents contain inconsistencies, errors, ambiguous language, and edge cases that don't fit standard patterns.

**Question**: How would your system handle documents that don't fit learned patterns, contain errors, or represent new legal scenarios not seen in training data?

**Consider**:

- What would you do with documents that are 80% similar to a known pattern but have significant differences?
- How would you detect and handle potential errors or inconsistencies in source documents?
- How would you identify when a new case requires legal research or precedent analysis beyond your training data?
- What confidence scoring and uncertainty quantification would you implement?
- How would you gracefully degrade when the system encounters scenarios it can't handle?
- What human-in-the-loop mechanisms would you design?

---
## Delivery and Discussion

### **Core Focus: Technical Assessment (Offline Homework)**

Your main task is to solve the **Core Technical Challenge** described above.

This is an **offline technical assessment** that you can complete as a short homework and then share back with us. Please send:

- **Your code** (repo or zipped project is fine), and  
- **A short video walkthrough** presenting your solution (tip: using **loom.com** is a great option).

This assessment is intended to be **quick and short nowadays with AI code assistants**.  
If you think you’ll need **more than one week** to complete it, please let us know.

Once you send it back, we’ll review your submission and get back to you with the next steps.  
**You will always receive feedback on your implementation, regardless of the outcome.**

---

### **What to Focus On**

To make your submission as effective as possible, please focus mostly on the **agentic part**:

- What each agent does
- Clear inputs and outputs for each component
- How each part is executed end-to-end
- Key limitations and how you address them (don’t treat LLMs as a magical black box)

A **simple prototype / proof-of-concept implementation** is strongly encouraged, as it helps us follow your reasoning and makes the discussion easier.
