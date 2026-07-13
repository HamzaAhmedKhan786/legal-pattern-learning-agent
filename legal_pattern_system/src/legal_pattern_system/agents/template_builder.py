from __future__ import annotations

from legal_pattern_system.models import FieldPattern, LearnedTemplate, LegalDocument, SectionPattern


class TemplateBuilderAgent:
    """Create a reusable template object from detected patterns."""

    def build(
        self,
        documents: list[LegalDocument],
        metadata_fields: list[FieldPattern],
        party_fields: dict[str, list[FieldPattern]],
        sections: list[SectionPattern],
        legal_citations: list[str],
    ) -> LearnedTemplate:
        if not documents:
            raise ValueError("Cannot build a template without source documents.")

        # Placeholders are derived from fields that vary across examples. This is
        # the core "fixed vs flexible" separation requested in the challenge.
        placeholders = self._placeholders(metadata_fields, party_fields)
        required_sections = [section.heading for section in sections if section.required]
        optional_sections = [section.heading for section in sections if not section.required]
        variable_fields = placeholders[:]
        confidence = self._confidence(sections, metadata_fields, party_fields)
        notes = [
            "Prototype learns structure from Markdown samples; production ingestion can swap parser adapters.",
            "Fields observed with multiple values are treated as variable placeholders.",
            "Critical legal citations are surfaced for lawyer review before template approval.",
            "Generation uses canonical section guidance instead of copying whole source sections.",
        ]

        return LearnedTemplate(
            document_type=documents[0].document_type,
            source_count=len(documents),
            title=documents[0].title,
            metadata_fields=metadata_fields,
            party_fields=party_fields,
            sections=sections,
            legal_citations=legal_citations,
            placeholders=placeholders,
            required_sections=required_sections,
            optional_sections=optional_sections,
            variable_fields=variable_fields,
            locked_legal_citations=legal_citations,
            confidence=confidence,
            source_examples=[str(document.source_path.name) for document in documents],
            notes=notes,
        )

    def _placeholders(self, metadata_fields: list[FieldPattern], party_fields: dict[str, list[FieldPattern]]) -> list[str]:
        """Create stable placeholder names for variable metadata and party fields."""
        placeholders = [self._placeholder(field.label) for field in metadata_fields if field.stability == "variable"]
        for party_name, fields in party_fields.items():
            for field in fields:
                if field.stability == "variable":
                    placeholders.append(f"{party_name}_{self._placeholder(field.label)}")
        return sorted(set(placeholders))

    def _placeholder(self, label: str) -> str:
        """Normalize human field labels into JSON/template-friendly keys."""
        return label.lower().replace(" ", "_").replace(".", "")

    def _confidence(
        self,
        sections: list[SectionPattern],
        metadata_fields: list[FieldPattern],
        party_fields: dict[str, list[FieldPattern]],
    ) -> float:
        """Estimate template confidence from field and required-section coverage."""
        field_confidences = [field.confidence for field in metadata_fields]
        for fields in party_fields.values():
            field_confidences.extend(field.confidence for field in fields)
        section_confidence = sum(section.occurrence_rate for section in sections) / max(len(sections), 1)
        field_confidence = sum(field_confidences) / max(len(field_confidences), 1)
        return round((section_confidence + field_confidence) / 2, 2)
