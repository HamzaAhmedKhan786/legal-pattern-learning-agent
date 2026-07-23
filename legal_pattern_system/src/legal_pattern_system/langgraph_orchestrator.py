from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TypedDict

from legal_pattern_system.agentic_orchestrator import AgenticLegalPatternOrchestrator
from legal_pattern_system.agents.qa_agent import QaAgent
from legal_pattern_system.llm_client import LlmClient, MockLlmClient
from legal_pattern_system.models import AgentRunReport, AgentStep, GeneratedDocument


class LegalDraftGraphState(TypedDict, total=False):
    document_dir: Path
    case_data: dict[str, Any]
    output_root: Path
    run_id: str
    trace_dir: Path
    steps: list[AgentStep]
    plan: dict[str, Any]
    template: Any
    documents: list[Any]
    pattern_response: dict[str, Any]
    retrieved: list[Any]
    retrieval_coverage: float
    generation_response: dict[str, Any]
    draft_v1: GeneratedDocument
    qa_v1: Any
    critique: dict[str, Any]
    draft_v2: GeneratedDocument
    qa_v2: Any
    report: AgentRunReport


class LangGraphLegalPatternOrchestrator(AgenticLegalPatternOrchestrator):
    """Optional LangGraph workflow preserving the existing agentic trace contract.

    The project keeps the custom orchestrator as the default so the assessment
    remains runnable without extra dependencies. This class is the production
    path: each agent step is an explicit graph node, and future versions can add
    conditional retries, interrupts, streaming progress, and resumable state.
    """

    def __init__(self, llm: LlmClient | None = None) -> None:
        super().__init__(llm=llm or MockLlmClient())
        try:
            from langgraph.graph import END, StateGraph
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "LangGraph is not installed. Install optional dependencies with: "
                "pip install langgraph langchain-core"
            ) from exc
        self._end = END
        self._state_graph = StateGraph

    def run(self, *, document_dir: Path, case_data: dict[str, Any], output_root: Path) -> AgentRunReport:
        graph = self._build_graph()
        initial_state: LegalDraftGraphState = {
            "document_dir": document_dir,
            "case_data": case_data,
            "output_root": output_root,
            "steps": [],
        }
        final_state = graph.invoke(initial_state)
        return final_state["report"]

    def _build_graph(self) -> Any:
        workflow = self._state_graph(LegalDraftGraphState)
        workflow.add_node("initialize", self._initialize)
        workflow.add_node("plan", self._plan)
        workflow.add_node("learn_template", self._learn_template)
        workflow.add_node("extract_patterns", self._extract_patterns)
        workflow.add_node("retrieve", self._retrieve)
        workflow.add_node("draft", self._draft)
        workflow.add_node("critique", self._critique)
        workflow.add_node("revise", self._revise)
        workflow.add_node("finalize", self._finalize)

        workflow.set_entry_point("initialize")
        workflow.add_edge("initialize", "plan")
        workflow.add_edge("plan", "learn_template")
        workflow.add_edge("learn_template", "extract_patterns")
        workflow.add_edge("extract_patterns", "retrieve")
        workflow.add_edge("retrieve", "draft")
        workflow.add_edge("draft", "critique")
        workflow.add_edge("critique", "revise")
        workflow.add_edge("revise", "finalize")
        workflow.add_edge("finalize", self._end)
        return workflow.compile()

    def _initialize(self, state: LegalDraftGraphState) -> LegalDraftGraphState:
        run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        trace_dir = state["output_root"] / "runs" / f"{state['document_dir'].name}_{run_id}_langgraph"
        trace_dir.mkdir(parents=True, exist_ok=True)
        self._write_json(trace_dir / "00_prompt_manifest.json", self._prompt_manifest())
        state["run_id"] = run_id
        state["trace_dir"] = trace_dir
        return state

    def _plan(self, state: LegalDraftGraphState) -> LegalDraftGraphState:
        plan = self.llm.complete_json(
            purpose="plan",
            prompt=self._prompt("planning.md"),
            context={"document_type": state["document_dir"].name, "case_data_keys": sorted(state["case_data"])},
        )
        self._write_json(state["trace_dir"] / "01_plan.json", plan)
        state["plan"] = plan
        state["steps"].append(
            AgentStep("PlanningAgent", "Create tool-use plan", state["document_dir"].name, ", ".join(plan["steps"]), "01_plan.json")
        )
        return state

    def _learn_template(self, state: LegalDraftGraphState) -> LegalDraftGraphState:
        template, documents = self.base.learn_template(state["document_dir"])
        self._write_json(state["trace_dir"] / "02_template.json", template.to_dict())
        state["template"] = template
        state["documents"] = documents
        state["steps"].append(
            AgentStep(
                "LLMPatternAgent",
                "Learn source-document patterns and produce template schema",
                f"{len(documents)} source documents",
                f"{len(template.required_sections)} required sections, confidence {template.confidence}",
                "02_template.json",
            )
        )
        return state

    def _extract_patterns(self, state: LegalDraftGraphState) -> LegalDraftGraphState:
        template = state["template"]
        pattern_response = self.llm.complete_json(
            purpose="pattern_extraction",
            prompt=self._prompt("pattern_extraction.md"),
            context={"template_confidence": template.confidence, "required_sections": template.required_sections},
        )
        self._write_json(state["trace_dir"] / "03_pattern_llm_response.json", pattern_response)
        state["pattern_response"] = pattern_response
        return state

    def _retrieve(self, state: LegalDraftGraphState) -> LegalDraftGraphState:
        retrieved = self.retriever.retrieve(state["documents"], state["case_data"], top_k=6)
        retrieval_coverage = self.retriever.coverage(retrieved, state["template"].required_sections)
        self._write_json(state["trace_dir"] / "04_retrieval.json", [self._chunk_dict(chunk) for chunk in retrieved])
        state["retrieved"] = retrieved
        state["retrieval_coverage"] = retrieval_coverage
        state["steps"].append(
            AgentStep(
                "RetrievalAgent",
                "Retrieve source clauses for grounding",
                f"{len(state['documents'])} parsed docs",
                f"{len(retrieved)} chunks, coverage {retrieval_coverage}",
                "04_retrieval.json",
            )
        )
        return state

    def _draft(self, state: LegalDraftGraphState) -> LegalDraftGraphState:
        generation_response = self.llm.complete_json(
            purpose="grounded_generation",
            prompt=self._prompt("grounded_generation.md"),
            context={"retrieved_chunks": self._llm_chunks(state["retrieved"]), "case_data": state["case_data"]},
        )
        self._write_json(state["trace_dir"] / "05_generation_llm_response.json", generation_response)
        draft_response = self.llm.complete_json(
            purpose="draft_document",
            prompt=self._prompt("draft_document.md"),
            context={
                "template": self._llm_template(state["template"]),
                "case_data": state["case_data"],
                "retrieved_chunks": self._llm_chunks(state["retrieved"]),
                "drafting_strategy": generation_response,
            },
        )
        self._write_json(state["trace_dir"] / "06_draft_llm_response.json", draft_response)
        draft_v1 = GeneratedDocument(
            document_type=state["template"].document_type,
            content=draft_response["draft_markdown"],
            used_placeholders=[],
            unresolved_placeholders=[],
        )
        qa_v1 = QaAgent().evaluate(state["template"], draft_v1)
        (state["trace_dir"] / "06_draft_v1.md").write_text(draft_v1.content, encoding="utf-8")
        self._write_json(state["trace_dir"] / "07_qa_v1.json", qa_v1.to_dict())
        state["generation_response"] = generation_response
        state["draft_v1"] = draft_v1
        state["qa_v1"] = qa_v1
        state["steps"].append(
            AgentStep(
                "GroundedDraftingAgent",
                "Generate LLM draft using template plus retrieved grounding",
                f"chunks={generation_response['grounding_chunk_ids']}",
                f"draft words={len(draft_v1.content.split())}, QA={qa_v1.score}",
                "06_draft_v1.md",
            )
        )
        return state

    def _critique(self, state: LegalDraftGraphState) -> LegalDraftGraphState:
        critique = self.llm.complete_json(
            purpose="qa_critique",
            prompt=self._prompt("qa_critique.md"),
            context={"qa_findings": [finding.message for finding in state["qa_v1"].findings], "qa_score": state["qa_v1"].score},
        )
        self._write_json(state["trace_dir"] / "08_critique.json", critique)
        state["critique"] = critique
        state["steps"].append(
            AgentStep(
                "CritiqueAgent",
                "Critique draft and decide whether revision is needed",
                f"QA score {state['qa_v1'].score}",
                f"decision={critique['decision']}, risk={critique['legal_risk']}",
                "08_critique.json",
            )
        )
        return state

    def _revise(self, state: LegalDraftGraphState) -> LegalDraftGraphState:
        draft_v2, qa_v2 = self._revise_if_needed(
            template_document=state["draft_v1"],
            qa_report=state["qa_v1"],
            critique=state["critique"],
            template=state["template"],
            case_data=state["case_data"],
            retrieved_chunks=[self._chunk_dict(chunk) for chunk in state["retrieved"]],
            trace_dir=state["trace_dir"],
        )
        (state["trace_dir"] / "09_draft_v2.md").write_text(draft_v2.content, encoding="utf-8")
        self._write_json(state["trace_dir"] / "10_qa_v2.json", qa_v2.to_dict())
        self._write_human_review_packet(state["trace_dir"], draft_v2, qa_v2, state["retrieved"], state["template"].to_dict())
        state["draft_v2"] = draft_v2
        state["qa_v2"] = qa_v2
        state["steps"].append(
            AgentStep(
                "RevisionAgent",
                "Revise draft when critique finds issues",
                f"decision={state['critique']['decision']}",
                f"final QA={qa_v2.score}",
                "09_draft_v2.md",
            )
        )
        return state

    def _finalize(self, state: LegalDraftGraphState) -> LegalDraftGraphState:
        report = AgentRunReport(
            run_id=state["run_id"],
            document_type=state["document_dir"].name,
            steps=state["steps"],
            retrieval_coverage=state["retrieval_coverage"],
            initial_qa_score=state["qa_v1"].score,
            final_qa_score=state["qa_v2"].score,
            trace_dir=str(state["trace_dir"]),
        )
        self._write_json(state["trace_dir"] / "11_trace.json", report.to_dict())
        state["report"] = report
        return state
