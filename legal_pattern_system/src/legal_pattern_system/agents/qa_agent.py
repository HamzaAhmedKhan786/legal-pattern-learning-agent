from __future__ import annotations

import re

from legal_pattern_system.models import GeneratedDocument, LearnedTemplate, QaFinding, QaReport


class QaAgent:
    """Run deterministic quality checks before a draft reaches lawyer review."""

    def evaluate(self, template: LearnedTemplate, generated: GeneratedDocument) -> QaReport:
        findings: list[QaFinding] = []

        # Missing data should be explicit. A legal draft with unresolved fields
        # must be corrected before use.
        if generated.unresolved_placeholders:
            findings.append(
                QaFinding(
                    severity="high",
                    message=f"Unresolved placeholders remain: {', '.join(generated.unresolved_placeholders)}",
                )
            )

        # Required sections are learned from occurrence across source examples.
        # If a generated draft drops one, it is a structural completeness issue.
        required_headings = [section.heading for section in template.sections if section.required]
        missing_headings = [heading for heading in required_headings if not self._has_heading(generated.content, heading)]
        if missing_headings:
            findings.append(QaFinding(severity="high", message=f"Missing required sections: {', '.join(missing_headings)}"))

        # Citation checks are intentionally conservative. Different source
        # examples may contain different citations, so the prototype checks that
        # at least some learned citations survive into the legal grounds.
        present_citations = [citation for citation in template.legal_citations if citation in generated.content]
        if template.legal_citations and not present_citations:
            findings.append(
                QaFinding(
                    severity="medium",
                    message="No learned legal citations are present in the generated draft.",
                )
            )

        leaked_values = self._source_value_leaks(template, generated.content)
        if leaked_values:
            findings.append(
                QaFinding(
                    severity="high",
                    message=f"Generated draft appears to contain source-case values: {', '.join(leaked_values[:5])}",
                )
            )

        if not self._section_order_is_preserved(template, generated.content):
            findings.append(QaFinding(severity="medium", message="Generated section order differs from the learned template order."))

        # A very short draft often indicates failed generation or bad input data.
        if len(generated.content.split()) < 250:
            findings.append(QaFinding(severity="medium", message="Generated draft is unusually short for this document family."))

        # Simple score for the prototype. Production scoring would combine parser
        # confidence, retrieval coverage, lawyer edits, and policy checks.
        score = 1.0
        for finding in findings:
            score -= 0.25 if finding.severity == "high" else 0.1
        return QaReport(document_type=template.document_type, score=round(max(score, 0.0), 2), findings=findings)

    def _has_heading(self, content: str, heading: str) -> bool:
        """Match Markdown headings regardless of whether they are level 2 or 3."""
        pattern = re.compile(rf"^#{{2,6}}\s+{re.escape(heading)}\s*$", re.MULTILINE)
        return bool(pattern.search(content))

    def _source_value_leaks(self, template: LearnedTemplate, content: str) -> list[str]:
        """Find old variable values copied from source documents into the new draft."""
        leaked: list[str] = []
        for field in template.metadata_fields:
            if field.label.lower() in {"court"}:
                continue
            if field.stability == "variable":
                leaked.extend(value for value in field.values if self._looks_like_case_specific_value(value) and value in content)
        for fields in template.party_fields.values():
            for field in fields:
                if field.stability == "variable":
                    leaked.extend(value for value in field.values if self._looks_like_case_specific_value(value) and value in content)
        return sorted(set(leaked))

    def _looks_like_case_specific_value(self, value: str) -> bool:
        """Avoid flagging broad repeated labels while catching names, dates, IDs, and addresses."""
        if len(value) < 4:
            return False
        patterns = [
            r"^[A-Z][a-z]+ [A-Z][a-z]+",
            r"\d{4}",
            r"\d{5}",
            r"EMP-",
            r"HRB",
            r"GmbH|AG",
            r"Street|Straße|Strasse|Avenue|Platz|Linden",
        ]
        return any(re.search(pattern, value) for pattern in patterns)

    def _section_order_is_preserved(self, template: LearnedTemplate, content: str) -> bool:
        """Check that required learned sections appear in their learned order."""
        positions: list[int] = []
        for heading in template.required_sections:
            match = re.search(rf"^#{{2,6}}\s+{re.escape(heading)}\s*$", content, re.MULTILINE)
            if match:
                positions.append(match.start())
        return positions == sorted(positions)
