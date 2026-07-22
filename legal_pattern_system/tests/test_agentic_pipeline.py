import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from legal_pattern_system.agentic_orchestrator import AgenticLegalPatternOrchestrator
from legal_pattern_system.agents.orchestrator import LegalPatternOrchestrator
from legal_pattern_system.retrieval import SimpleRetriever


class AgenticPipelineTest(unittest.TestCase):
    def test_retriever_returns_grounding_chunks(self) -> None:
        document_dir = ROOT.parent / "sample_documents" / "claims_for_damages"
        template, documents = LegalPatternOrchestrator().learn_template(document_dir)
        case_data = json.loads((ROOT / "examples" / "damages_case_data.json").read_text(encoding="utf-8"))

        retrieved = SimpleRetriever().retrieve(documents, case_data, top_k=3)

        self.assertEqual(len(retrieved), 3)
        self.assertTrue(any(chunk.heading == "II. LEGAL GROUNDS" for chunk in retrieved))
        self.assertGreaterEqual(SimpleRetriever().coverage(retrieved, template.required_sections), 0.0)

    def test_agentic_pipeline_writes_trace(self) -> None:
        document_dir = ROOT.parent / "sample_documents" / "dismissal_protection_suits"
        case_data = json.loads((ROOT / "examples" / "dismissal_case_data.json").read_text(encoding="utf-8"))

        with tempfile.TemporaryDirectory() as temp_dir:
            report = AgenticLegalPatternOrchestrator().run(
                document_dir=document_dir,
                case_data=case_data,
                output_root=Path(temp_dir),
            )

            trace_dir = Path(report.trace_dir)
            self.assertTrue((trace_dir / "01_plan.json").exists())
            self.assertTrue((trace_dir / "04_retrieval.json").exists())
            self.assertTrue((trace_dir / "08_critique.json").exists())
            self.assertTrue((trace_dir / "11_trace.json").exists())
            self.assertGreaterEqual(report.final_qa_score, report.initial_qa_score)


if __name__ == "__main__":
    unittest.main()
