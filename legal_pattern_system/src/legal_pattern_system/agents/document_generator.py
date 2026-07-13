from __future__ import annotations

import re
from typing import Any

from legal_pattern_system.models import GeneratedDocument, LearnedTemplate


PLACEHOLDER_RE = re.compile(r"\{\{([a-zA-Z0-9_]+)\}\}")


class DocumentGeneratorAgent:
    """Render a new Markdown draft from a learned template and case data."""

    def generate(self, template: LearnedTemplate, case_data: dict[str, Any]) -> GeneratedDocument:
        lines: list[str] = [f"# {template.title}", ""]

        # Metadata fields are filled from case_data when provided. Otherwise the
        # placeholder remains visible for QA/human review.
        for field in template.metadata_fields:
            key = self._key(field.label)
            value = case_data.get(key, f"{{{{{key}}}}}" if field.stability == "variable" else self._fallback(field.values, key))
            lines.append(f"**{field.label}:** {value}  ")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Parties are dynamic: whatever party fields were learned from the source
        # documents are rendered here, not a fixed schema hardcoded in the script.
        for party_name, fields in template.party_fields.items():
            lines.append(f"## {party_name.upper()}")
            for field in fields:
                key = f"{party_name}_{self._key(field.label)}"
                fallback = f"{{{{{key}}}}}" if field.stability == "variable" else self._fallback(field.values, key)
                lines.append(f"**{field.label}:** {case_data.get(key, fallback)}  ")
            lines.append("")

        # Learned section order and heading levels are preserved. Party sections
        # are skipped because they were rendered as structured party blocks above.
        rendered_evidence_block = False
        for section in template.sections:
            if section.heading in {"PLAINTIFF", "DEFENDANT"}:
                continue
            if section.heading in {"DOCUMENTS ATTACHED", "WITNESS LIST", "EXPERT WITNESSES"} and rendered_evidence_block:
                continue
            heading_marker = "#" * max(section.level, 2)
            lines.append(f"{heading_marker} {section.heading}")
            body = case_data.get(f"section_{self._key(section.heading)}", self._canonical_body(template, section.heading, case_data))
            lines.append(self._adapt_body(body, case_data))
            lines.append("")
            if section.heading == "SUPPORTING EVIDENCE":
                rendered_evidence_block = True

        content = "\n".join(lines).strip() + "\n"
        # Unresolved placeholders stay visible and are reported to QA instead of
        # being removed. This is safer for legal drafting workflows.
        unresolved = sorted(set(PLACEHOLDER_RE.findall(content)))
        used = sorted(set(template.placeholders) - set(unresolved))
        return GeneratedDocument(
            document_type=template.document_type,
            content=content,
            used_placeholders=used,
            unresolved_placeholders=unresolved,
        )

    def _adapt_body(self, body: str, case_data: dict[str, Any]) -> str:
        """Replace explicit {{placeholder}} tokens if a section body contains them."""
        rendered = body
        for key, value in case_data.items():
            rendered = rendered.replace(f"{{{{{key}}}}}", str(value))
        return rendered

    def _canonical_body(self, template: LearnedTemplate, heading: str, case_data: dict[str, Any]) -> str:
        """Create clean section text from learned structure without copying old facts."""
        citations = ", ".join(template.locked_legal_citations[:3])
        plaintiff = self._party_value(case_data, "plaintiff", "name", "the Plaintiff")
        defendant = (
            self._party_value(case_data, "defendant", "company", "")
            or self._party_value(case_data, "defendant", "name", "the Defendant")
        )
        amount = case_data.get("total_damages", "{{total_damages}}")

        if heading == "STATEMENT OF CLAIM":
            return "The Plaintiff submits this statement of claim based on the facts, legal grounds, and relief set out below."
        if heading == "I. FACTUAL BACKGROUND":
            return "\n".join(
                [
                    "1. **Relationship Between the Parties**",
                    f"   - {plaintiff} and {defendant} had a legally relevant relationship giving rise to this claim.",
                    "   - The case-specific dates, role details, contract terms, and communications should be verified against the matter file.",
                    "",
                    "2. **Events Giving Rise to the Claim**",
                    "   - The relevant events are summarized from the new case intake and supporting evidence.",
                    "   - Any disputed facts should remain clearly separated from confirmed documentary evidence.",
                    "",
                    "3. **Resulting Harm or Legal Consequence**",
                    "   - The facts described above caused the legal harm addressed in the requested relief.",
                ]
            )
        if heading == "II. LEGAL GROUNDS":
            citation_text = f" The learned template highlights these citations for lawyer review: {citations}." if citations else ""
            return "\n".join(
                [
                    "1. **Applicable Legal Standard**",
                    f"   - The claim should be assessed under the applicable statutory and contractual framework.{citation_text}",
                    "",
                    "2. **Application to the Facts**",
                    "   - The facts alleged in the matter file should be mapped to each required legal element.",
                    "   - The final legal analysis must be reviewed by a qualified lawyer before filing.",
                ]
            )
        if heading == "III. DAMAGES CLAIMED":
            return "\n".join(
                [
                    "1. **Direct Damages:**",
                    f"   - Total claimed direct damages: {amount}",
                    "   - Supporting calculations should be attached as evidence.",
                    "",
                    "2. **Consequential Damages and Costs:**",
                    "   - Any consequential damages, interest, expert fees, and court costs should be itemized from the case file.",
                ]
            )
        if heading in {"III. RELIEF SOUGHT", "IV. RELIEF SOUGHT"}:
            return "\n".join(
                [
                    "The Plaintiff respectfully requests that this Honorable Court:",
                    "",
                    "1. grant the primary relief supported by the facts and applicable law;",
                    "2. award any monetary compensation, interest, fees, and costs proven by the evidence;",
                    "3. grant such other relief as the Court deems just and proper.",
                ]
            )
        if heading in {"SUPPORTING EVIDENCE", "DOCUMENTS ATTACHED", "WITNESS LIST", "EXPERT WITNESSES"}:
            return "\n".join(
                [
                    "### DOCUMENTS ATTACHED",
                    "- A. Primary agreement, employment contract, or other governing document",
                    "- B. Notices, correspondence, and relevant communications",
                    "- C. Financial, employment, or damages records",
                    "- D. Additional matter-specific evidence",
                    "",
                    "### WITNESS LIST",
                    "1. Matter-specific witness or expert to be confirmed by counsel",
                ]
            )
        if heading == "CONCLUSION":
            return (
                f"For the reasons set out above, {plaintiff} requests relief against {defendant}. "
                "This draft is generated from learned firm patterns and must be reviewed for legal accuracy, "
                "jurisdiction-specific requirements, and factual completeness before use."
            )
        return "This section should be completed with matter-specific facts and lawyer-approved language."

    def _fallback(self, values: list[str], key: str) -> str:
        return values[0] if values else f"{{{{{key}}}}}"

    def _party_value(self, case_data: dict[str, Any], party: str, label: str, default: str) -> str:
        value = case_data.get(f"{party}_{label}")
        return str(value) if value else default

    def _key(self, label: str) -> str:
        """Normalize field labels so case_data can use predictable snake_case keys."""
        return label.lower().replace(" ", "_").replace(".", "").replace(":", "")
