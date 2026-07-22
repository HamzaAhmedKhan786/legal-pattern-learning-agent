from __future__ import annotations

import json
import hashlib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from legal_pattern_system.agents.orchestrator import LegalPatternOrchestrator
from legal_pattern_system.agents.qa_agent import QaAgent
from legal_pattern_system.llm_client import LlmClient, MockLlmClient
from legal_pattern_system.models import AgentRunReport, AgentStep, GeneratedDocument, LearnedTemplate, QaReport, RetrievalChunk
from legal_pattern_system.retrieval import SimpleRetriever


class AgenticLegalPatternOrchestrator:
    """LLM-style agent loop with planning, retrieval, critique, revision, traces."""

    def __init__(self, llm: LlmClient | None = None) -> None:
        self.base = LegalPatternOrchestrator()
        self.retriever = SimpleRetriever()
        self.llm = llm or MockLlmClient()

    def run(self, *, document_dir: Path, case_data: dict[str, Any], output_root: Path) -> AgentRunReport:
        run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        trace_dir = output_root / "runs" / f"{document_dir.name}_{run_id}"
        trace_dir.mkdir(parents=True, exist_ok=True)
        steps: list[AgentStep] = []
        self._write_json(trace_dir / "00_prompt_manifest.json", self._prompt_manifest())

        plan = self.llm.complete_json(
            purpose="plan",
            prompt=self._prompt("planning.md"),
            context={"document_type": document_dir.name, "case_data_keys": sorted(case_data)},
        )
        self._write_json(trace_dir / "01_plan.json", plan)
        steps.append(AgentStep("PlanningAgent", "Create tool-use plan", document_dir.name, ", ".join(plan["steps"]), "01_plan.json"))

        template, documents = self.base.learn_template(document_dir)
        self._write_json(trace_dir / "02_template.json", template.to_dict())
        steps.append(
            AgentStep(
                "LLMPatternAgent",
                "Learn source-document patterns and produce template schema",
                f"{len(documents)} source documents",
                f"{len(template.required_sections)} required sections, confidence {template.confidence}",
                "02_template.json",
            )
        )

        pattern_response = self.llm.complete_json(
            purpose="pattern_extraction",
            prompt=self._prompt("pattern_extraction.md"),
            context={"template_confidence": template.confidence, "required_sections": template.required_sections},
        )
        self._write_json(trace_dir / "03_pattern_llm_response.json", pattern_response)

        retrieved = self.retriever.retrieve(documents, case_data, top_k=6)
        retrieval_coverage = self.retriever.coverage(retrieved, template.required_sections)
        self._write_json(trace_dir / "04_retrieval.json", [self._chunk_dict(chunk) for chunk in retrieved])
        steps.append(
            AgentStep(
                "RetrievalAgent",
                "Retrieve source clauses for grounding",
                f"{len(documents)} parsed docs",
                f"{len(retrieved)} chunks, coverage {retrieval_coverage}",
                "04_retrieval.json",
            )
        )

        generation_response = self.llm.complete_json(
            purpose="grounded_generation",
            prompt=self._prompt("grounded_generation.md"),
            context={"retrieved_chunks": self._llm_chunks(retrieved), "case_data": case_data},
        )
        self._write_json(trace_dir / "05_generation_llm_response.json", generation_response)

        draft_response = self.llm.complete_json(
            purpose="draft_document",
            prompt=self._prompt("draft_document.md"),
            context={
                "template": self._llm_template(template),
                "case_data": case_data,
                "retrieved_chunks": self._llm_chunks(retrieved),
                "drafting_strategy": generation_response,
            },
        )
        self._write_json(trace_dir / "06_draft_llm_response.json", draft_response)
        draft_v1 = GeneratedDocument(
            document_type=template.document_type,
            content=draft_response["draft_markdown"],
            used_placeholders=[],
            unresolved_placeholders=[],
        )
        qa_v1 = QaAgent().evaluate(template, draft_v1)
        (trace_dir / "06_draft_v1.md").write_text(draft_v1.content, encoding="utf-8")
        self._write_json(trace_dir / "07_qa_v1.json", qa_v1.to_dict())
        steps.append(
            AgentStep(
                "GroundedDraftingAgent",
                "Generate LLM draft using template plus retrieved grounding",
                f"chunks={generation_response['grounding_chunk_ids']}",
                f"draft words={len(draft_v1.content.split())}, QA={qa_v1.score}",
                "06_draft_v1.md",
            )
        )

        critique = self.llm.complete_json(
            purpose="qa_critique",
            prompt=self._prompt("qa_critique.md"),
            context={"qa_findings": [finding.message for finding in qa_v1.findings], "qa_score": qa_v1.score},
        )
        self._write_json(trace_dir / "08_critique.json", critique)
        steps.append(
            AgentStep(
                "CritiqueAgent",
                "Critique draft and decide whether revision is needed",
                f"QA score {qa_v1.score}",
                f"decision={critique['decision']}, risk={critique['legal_risk']}",
                "08_critique.json",
            )
        )

        draft_v2, qa_v2 = self._revise_if_needed(
            template_document=draft_v1,
            qa_report=qa_v1,
            critique=critique,
            template=template,
            case_data=case_data,
            retrieved_chunks=[self._chunk_dict(chunk) for chunk in retrieved],
            trace_dir=trace_dir,
        )
        (trace_dir / "09_draft_v2.md").write_text(draft_v2.content, encoding="utf-8")
        self._write_json(trace_dir / "10_qa_v2.json", qa_v2.to_dict())
        self._write_human_review_packet(trace_dir, draft_v2, qa_v2, retrieved, template.to_dict())
        steps.append(
            AgentStep(
                "RevisionAgent",
                "Revise draft when critique finds issues",
                f"decision={critique['decision']}",
                f"final QA={qa_v2.score}",
                "09_draft_v2.md",
            )
        )

        report = AgentRunReport(
            run_id=run_id,
            document_type=document_dir.name,
            steps=steps,
            retrieval_coverage=retrieval_coverage,
            initial_qa_score=qa_v1.score,
            final_qa_score=qa_v2.score,
            trace_dir=str(trace_dir),
        )
        self._write_json(trace_dir / "11_trace.json", report.to_dict())
        return report

    def _revise_if_needed(
        self,
        *,
        template_document: GeneratedDocument,
        qa_report: QaReport,
        critique: dict[str, Any],
        template: LearnedTemplate,
        case_data: dict[str, Any],
        retrieved_chunks: list[dict[str, Any]],
        trace_dir: Path,
    ) -> tuple[GeneratedDocument, QaReport]:
        if not qa_report.findings:
            return template_document, qa_report
        if critique.get("decision") != "revise":
            return template_document, qa_report

        revision_response = self.llm.complete_json(
            purpose="revision",
            prompt=self._prompt("revision.md"),
            context={
                "draft_markdown": template_document.content,
                "qa_findings": [finding.message for finding in qa_report.findings],
                "critique": critique,
                "template": self._llm_template(template),
                "case_data": case_data,
                "retrieved_chunks": self._compact_chunk_dicts(retrieved_chunks),
            },
        )
        self._write_json(trace_dir / "08b_revision_llm_response.json", revision_response)
        revised = GeneratedDocument(
            document_type=template_document.document_type,
            content=revision_response["draft_markdown"],
            used_placeholders=template_document.used_placeholders,
            unresolved_placeholders=template_document.unresolved_placeholders,
        )
        revised_qa = QaAgent().evaluate(template, revised)
        if revised_qa.score > qa_report.score:
            return revised, revised_qa

        fallback = self.base.generator.generate(template, case_data)
        fallback_qa = QaAgent().evaluate(template, fallback)
        self._write_json(
            trace_dir / "08c_revision_guardrail.json",
            {
                "reason": "LLM revision did not improve deterministic QA score.",
                "llm_revision_score": revised_qa.score,
                "fallback_score": fallback_qa.score,
                "action": "used_template_safe_assembly_for_final_draft",
            },
        )
        return fallback, fallback_qa

    def _prompt(self, filename: str) -> str:
        prompt_path = Path(__file__).resolve().parents[2] / "prompts" / filename
        return prompt_path.read_text(encoding="utf-8")

    def _prompt_manifest(self) -> dict[str, Any]:
        prompt_dir = Path(__file__).resolve().parents[2] / "prompts"
        manifest: dict[str, Any] = {"version": "2026-07-22", "prompts": []}
        for prompt_file in sorted(prompt_dir.glob("*.md")):
            content = prompt_file.read_text(encoding="utf-8")
            manifest["prompts"].append(
                {
                    "name": prompt_file.name,
                    "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
                }
            )
        return manifest

    def _write_json(self, path: Path, data: Any) -> None:
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def _write_human_review_packet(
        self,
        trace_dir: Path,
        final_draft: GeneratedDocument,
        qa_report: QaReport,
        retrieved_chunks: list[RetrievalChunk],
        template: dict[str, Any],
    ) -> None:
        packet = {
            "status": "pending_lawyer_review",
            "review_required": True,
            "review_reasons": [
                "LLM-generated legal draft",
                "Template requires lawyer approval before use",
                "Retrieved grounding chunks should be checked against matter facts",
            ],
            "qa_score": qa_report.score,
            "qa_findings": [finding.message for finding in qa_report.findings],
            "template_confidence": template.get("confidence"),
            "grounding_sources": [self._chunk_dict(chunk) for chunk in retrieved_chunks],
            "feedback_capture": {
                "lawyer_decision": "approve | request_changes | reject",
                "redline_notes": [],
                "final_filing_ready": False,
            },
            "draft_preview": final_draft.content[:2000],
        }
        self._write_json(trace_dir / "12_human_review_packet.json", packet)

    def _chunk_dict(self, chunk: RetrievalChunk) -> dict[str, Any]:
        return {
            "chunk_id": chunk.chunk_id,
            "source_path": chunk.source_path,
            "heading": chunk.heading,
            "score": chunk.score,
            "text": chunk.text,
        }

    def _llm_template(self, template: LearnedTemplate) -> dict[str, Any]:
        """Expose only the template fields needed for LLM drafting."""

        return {
            "document_type": template.document_type,
            "title": template.title,
            "required_sections": template.required_sections,
            "locked_legal_citations": template.locked_legal_citations,
            "variable_fields": template.variable_fields,
            "confidence": template.confidence,
        }

    def _llm_chunks(self, chunks: list[RetrievalChunk]) -> list[dict[str, Any]]:
        """Send compact grounding excerpts to LLMs while preserving full traces on disk."""

        return [
            {
                "chunk_id": chunk.chunk_id,
                "source_path": chunk.source_path,
                "heading": chunk.heading,
                "score": round(chunk.score, 3),
                "excerpt": self._truncate(chunk.text, 900),
            }
            for chunk in chunks[:4]
        ]

    def _compact_chunk_dicts(self, chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "chunk_id": chunk.get("chunk_id"),
                "source_path": chunk.get("source_path"),
                "heading": chunk.get("heading"),
                "score": chunk.get("score"),
                "excerpt": self._truncate(str(chunk.get("text", "")), 900),
            }
            for chunk in chunks[:4]
        ]

    def _truncate(self, text: str, limit: int) -> str:
        if len(text) <= limit:
            return text
        return text[: limit - 3].rstrip() + "..."
