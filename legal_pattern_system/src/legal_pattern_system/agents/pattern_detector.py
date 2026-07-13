from __future__ import annotations

import re
from collections import Counter, defaultdict

from legal_pattern_system.models import FieldPattern, LegalDocument, SectionPattern


CITATION_RE = re.compile(r"(?:\u00a7|Section)\s*\d+[a-zA-Z]*(?:\s+Abs\.\s*\d+)?\s+[A-Z][A-Za-z]+")


class PatternDetectorAgent:
    """Detect reusable patterns across multiple examples of one document type."""

    def detect_field_patterns(self, documents: list[LegalDocument]) -> tuple[list[FieldPattern], dict[str, list[FieldPattern]]]:
        # A field with one observed value across all examples is treated as fixed;
        # a field with multiple values is treated as a variable placeholder.
        metadata = self._field_patterns([doc.metadata for doc in documents])
        party_fields: dict[str, list[FieldPattern]] = {}
        preferred_order = ["plaintiff", "defendant"]
        observed = {party for doc in documents for party in doc.parties}
        party_names = [party for party in preferred_order if party in observed]
        party_names.extend(sorted(observed - set(party_names)))
        for party_name in party_names:
            party_fields[party_name] = self._field_patterns([doc.parties.get(party_name, {}) for doc in documents])
        return metadata, party_fields

    def detect_section_patterns(self, documents: list[LegalDocument]) -> list[SectionPattern]:
        # Section patterns preserve first-seen ordering from the source family so
        # generated drafts follow the firm's familiar document structure.
        by_heading: dict[str, list[str]] = defaultdict(list)
        levels: dict[str, int] = {}
        ordered_headings: list[str] = []
        for doc in documents:
            for section in doc.sections:
                if section.heading not in by_heading:
                    ordered_headings.append(section.heading)
                    levels[section.heading] = section.level
                by_heading[section.heading].append(section.content)

        patterns: list[SectionPattern] = []
        doc_count = len(documents)
        for heading in ordered_headings:
            contents = by_heading[heading]
            occurrence_rate = len(contents) / doc_count
            # The longest observed section is used as a representative body in
            # this prototype. Production would synthesize a cleaner canonical
            # clause from multiple source spans with lawyer approval.
            representative = max(contents, key=len)[:1200]
            variants = self._top_repeated_lines(contents)
            patterns.append(
                SectionPattern(
                    heading=heading,
                    level=levels[heading],
                    occurrence_rate=round(occurrence_rate, 2),
                    required=occurrence_rate >= 0.9,
                    variants=variants,
                    representative_content=representative,
                )
            )
        return patterns

    def detect_legal_citations(self, documents: list[LegalDocument]) -> list[str]:
        # Citations are surfaced for QA because legal references are high-risk:
        # generation should not silently lose or mutate them.
        citations: Counter[str] = Counter()
        for doc in documents:
            citations.update(CITATION_RE.findall(doc.raw_text))
        return [citation for citation, _ in citations.most_common()]

    def _field_patterns(self, field_sets: list[dict[str, str]]) -> list[FieldPattern]:
        """Summarize whether each observed field is fixed or variable."""
        labels = sorted({label for fields in field_sets for label in fields})
        patterns: list[FieldPattern] = []
        for label in labels:
            values = [fields[label] for fields in field_sets if label in fields]
            unique_values = sorted(set(values))
            stability = "fixed" if len(unique_values) == 1 else "variable"
            confidence = len(values) / max(len(field_sets), 1)
            patterns.append(
                FieldPattern(
                    label=label,
                    values=unique_values,
                    stability=stability,
                    confidence=round(confidence, 2),
                )
            )
        return patterns

    def _top_repeated_lines(self, contents: list[str]) -> list[str]:
        """Return repeated long lines that may represent stable legal language."""
        counter: Counter[str] = Counter()
        for content in contents:
            lines = [line.strip() for line in content.splitlines() if len(line.strip()) > 30]
            counter.update(lines)
        return [line for line, count in counter.most_common(5) if count > 1]
