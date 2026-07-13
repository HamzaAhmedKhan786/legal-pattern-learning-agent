import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from legal_pattern_system.agents.document_parser import MarkdownDocumentParser


class MarkdownParserTest(unittest.TestCase):
    def test_markdown_parser_extracts_core_fields(self) -> None:
        sample = ROOT.parent / "sample_documents" / "dismissal_protection_suits" / "dps_001.md"
        document = MarkdownDocumentParser().parse(sample)

        self.assertEqual(document.title, "DISMISSAL PROTECTION SUIT")
        self.assertEqual(document.metadata["Case No."], "DPS-2024-001")
        self.assertIn("plaintiff", document.parties)
        self.assertIn("STATEMENT OF CLAIM", document.top_level_headings())


if __name__ == "__main__":
    unittest.main()
