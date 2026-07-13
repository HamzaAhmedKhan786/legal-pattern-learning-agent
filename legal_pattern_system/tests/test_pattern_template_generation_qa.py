import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from legal_pattern_system.agents.document_generator import DocumentGeneratorAgent
from legal_pattern_system.agents.document_parser import MarkdownDocumentParser
from legal_pattern_system.agents.orchestrator import LegalPatternOrchestrator
from legal_pattern_system.agents.qa_agent import QaAgent
from legal_pattern_system.models import GeneratedDocument


class PatternTemplateGenerationQaTest(unittest.TestCase):
    def setUp(self) -> None:
        self.sample_dir = ROOT.parent / "sample_documents" / "dismissal_protection_suits"
        self.template, self.documents = LegalPatternOrchestrator().learn_template(self.sample_dir)

    def test_pattern_learning_creates_variable_placeholders(self) -> None:
        self.assertIn("case_no", self.template.placeholders)
        self.assertIn("plaintiff_name", self.template.placeholders)
        self.assertIn("I. FACTUAL BACKGROUND", self.template.required_sections)
        self.assertGreaterEqual(self.template.confidence, 0.8)

    def test_generator_uses_case_data_and_avoids_old_case_name(self) -> None:
        case_data = {
            "case_no": "DPS-2024-999",
            "court": "Labor Court Berlin",
            "date_filed": "June 20, 2024",
            "plaintiff_name": "New Employee",
            "plaintiff_address": "New Street 1, 10115 Berlin, Germany",
            "plaintiff_employee_id": "EMP-2024-0999",
            "plaintiff_position": "Senior Product Manager",
            "plaintiff_department": "Product",
            "plaintiff_hire_date": "May 1, 2020",
            "defendant_company": "New Employer GmbH",
            "defendant_address": "Employer Avenue 10, 10117 Berlin, Germany",
            "defendant_legal_representative": "Dr. Example Counsel",
            "defendant_hr_contact": "Example HR Director",
        }
        generated = DocumentGeneratorAgent().generate(self.template, case_data)

        self.assertIn("New Employee", generated.content)
        self.assertIn("New Employer GmbH", generated.content)
        self.assertNotIn("Maria Schmidt", generated.content)
        self.assertEqual(generated.unresolved_placeholders, [])

    def test_qa_catches_unresolved_placeholders_and_source_leakage(self) -> None:
        generated = GeneratedDocument(
            document_type=self.template.document_type,
            content="# DISMISSAL PROTECTION SUIT\n\n**Case No.:** {{case_no}}\n\n## PLAINTIFF\nMaria Schmidt\n",
            used_placeholders=[],
            unresolved_placeholders=["case_no"],
        )
        report = QaAgent().evaluate(self.template, generated)

        messages = " ".join(finding.message for finding in report.findings)
        self.assertLess(report.score, 1.0)
        self.assertIn("Unresolved placeholders", messages)
        self.assertIn("source-case values", messages)


class ParserTest(unittest.TestCase):
    def test_parser_keeps_document_type_from_folder(self) -> None:
        sample = ROOT.parent / "sample_documents" / "claims_for_damages" / "cfd_001.md"
        document = MarkdownDocumentParser().parse(sample)
        self.assertEqual(document.document_type, "claims_for_damages")


if __name__ == "__main__":
    unittest.main()
