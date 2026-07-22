from __future__ import annotations

import re
from collections import Counter

from legal_pattern_system.models import LegalDocument, RetrievalChunk


TOKEN_RE = re.compile(r"[A-Za-z0-9§]+")


class SimpleRetriever:
    """Small lexical retriever over parsed legal document sections.

    This is intentionally lightweight, but it implements the missing retrieval
    idea: generation and QA can inspect which source sections were used for
    grounding instead of operating from the template alone.
    """

    def build_chunks(self, documents: list[LegalDocument]) -> list[RetrievalChunk]:
        chunks: list[RetrievalChunk] = []
        for doc_index, document in enumerate(documents):
            for section_index, section in enumerate(document.sections):
                if not section.content.strip():
                    continue
                chunk_id = f"{document.document_type}:{doc_index}:{section_index}"
                chunks.append(
                    RetrievalChunk(
                        chunk_id=chunk_id,
                        source_path=str(document.source_path.name),
                        heading=section.heading,
                        text=section.content[:1600],
                        score=0.0,
                    )
                )
        return chunks

    def retrieve(self, documents: list[LegalDocument], case_data: dict[str, object], *, top_k: int = 5) -> list[RetrievalChunk]:
        chunks = self.build_chunks(documents)
        query = " ".join(str(value) for value in case_data.values())
        query_terms = self._tokens(query)
        if not query_terms:
            return chunks[:top_k]

        scored: list[RetrievalChunk] = []
        for chunk in chunks:
            chunk_terms = self._tokens(f"{chunk.heading} {chunk.text}")
            overlap = sum((query_terms & chunk_terms).values())
            citation_bonus = 2 if "§" in chunk.text else 0
            heading_bonus = 4 if chunk.heading == "II. LEGAL GROUNDS" else 1 if chunk.heading == "SUPPORTING EVIDENCE" else 0
            score = float(overlap + citation_bonus + heading_bonus)
            scored.append(
                RetrievalChunk(
                    chunk_id=chunk.chunk_id,
                    source_path=chunk.source_path,
                    heading=chunk.heading,
                    text=chunk.text,
                    score=score,
                )
            )

        return sorted(scored, key=lambda chunk: chunk.score, reverse=True)[:top_k]

    def coverage(self, retrieved_chunks: list[RetrievalChunk], required_headings: list[str]) -> float:
        if not required_headings:
            return 1.0
        retrieved_headings = {chunk.heading for chunk in retrieved_chunks}
        covered = sum(1 for heading in required_headings if heading in retrieved_headings)
        return round(covered / len(required_headings), 2)

    def _tokens(self, text: str) -> Counter[str]:
        return Counter(token.lower() for token in TOKEN_RE.findall(text))
