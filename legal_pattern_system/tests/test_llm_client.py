import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from legal_pattern_system.llm_client import MockLlmClient, OllamaLlmClient, create_llm_client
from legal_pattern_system.schema_validation import SchemaValidationError, normalize_llm_response, validate_llm_response


class LlmClientTest(unittest.TestCase):
    def test_create_mock_provider(self) -> None:
        client = create_llm_client("mock")
        self.assertIsInstance(client, MockLlmClient)

    def test_create_ollama_provider(self) -> None:
        client = create_llm_client("ollama", model="llama3.1", base_url="http://localhost:11434")
        self.assertIsInstance(client, OllamaLlmClient)

    def test_mock_returns_structured_json(self) -> None:
        response = MockLlmClient().complete_json(
            purpose="plan",
            prompt="Return a plan.",
            context={"document_type": "claims_for_damages"},
        )
        self.assertIn("steps", response)
        self.assertIn("reasoning", response)

    def test_schema_validation_rejects_missing_fields(self) -> None:
        with self.assertRaises(SchemaValidationError):
            validate_llm_response("draft_document", {"draft_markdown": "# Draft"})

    def test_schema_validation_rejects_nested_shape_errors(self) -> None:
        with self.assertRaises(SchemaValidationError):
            validate_llm_response(
                "plan",
                {
                    "steps": [{"name": "parse_source_documents"}],
                    "reasoning": "Nested step objects are not accepted by the orchestration layer.",
                },
            )

    def test_normalizer_repairs_common_llm_list_shape(self) -> None:
        normalized = normalize_llm_response(
            "plan",
            {
                "steps": [{"name": "parse_source_documents"}],
                "reasoning": "Use tools in order.",
            },
        )

        self.assertEqual(normalized["steps"], ["parse_source_documents"])
        validate_llm_response("plan", normalized)


if __name__ == "__main__":
    unittest.main()
