"""
Unit Tests for Strict JSON Schema Validation

Tests that we FAIL LOUDLY when:
1. Agent doesn't return valid JSON
2. JSON is missing required fields
3. JSON has wrong field types
4. JSON is wrapped in code blocks (should fail, no fallback)
"""

import unittest
import json
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from web_ui.document_processor import LiveDocumentProcessor


class TestStrictSchemaValidation(unittest.TestCase):
    """Test that schema validation fails loudly without fallbacks"""

    def setUp(self):
        """Set up test processor"""
        self.processor = LiveDocumentProcessor()

    def test_validate_json_schema_success(self):
        """Test successful validation with correct schema"""
        schema = {
            "type": "object",
            "properties": {
                "claims": {"type": "array"},
                "count": {"type": "number"}
            },
            "required": ["claims"]
        }

        data = {
            "claims": [{"text": "Test claim"}],
            "count": 1
        }

        # Should not raise
        self.processor._validate_json_schema(data, schema, "test")

    def test_validate_json_schema_missing_required_field(self):
        """Test that missing required fields cause failure"""
        schema = {
            "type": "object",
            "properties": {
                "claims": {"type": "array"}
            },
            "required": ["claims"]
        }

        data = {"other_field": "value"}

        with self.assertRaises(RuntimeError) as context:
            self.processor._validate_json_schema(data, schema, "test")

        self.assertIn("missing required fields", str(context.exception).lower())
        self.assertIn("claims", str(context.exception))

    def test_validate_json_schema_wrong_type_array(self):
        """Test that wrong field type (expecting array) causes failure"""
        schema = {
            "type": "object",
            "properties": {
                "claims": {"type": "array"}
            },
            "required": ["claims"]
        }

        data = {"claims": "not an array"}

        with self.assertRaises(RuntimeError) as context:
            self.processor._validate_json_schema(data, schema, "test")

        self.assertIn("should be array", str(context.exception))

    def test_validate_json_schema_wrong_type_string(self):
        """Test that wrong field type (expecting string) causes failure"""
        schema = {
            "type": "object",
            "properties": {
                "simplified": {"type": "string"}
            },
            "required": ["simplified"]
        }

        data = {"simplified": 123}

        with self.assertRaises(RuntimeError) as context:
            self.processor._validate_json_schema(data, schema, "test")

        self.assertIn("should be string", str(context.exception))

    def test_validate_json_schema_wrong_type_number(self):
        """Test that wrong field type (expecting number) causes failure"""
        schema = {
            "type": "object",
            "properties": {
                "confidence": {"type": "number"}
            },
            "required": ["confidence"]
        }

        data = {"confidence": "not a number"}

        with self.assertRaises(RuntimeError) as context:
            self.processor._validate_json_schema(data, schema, "test")

        self.assertIn("should be number", str(context.exception))

    def test_validate_json_schema_not_object(self):
        """Test that non-object data causes failure"""
        schema = {
            "type": "object",
            "properties": {},
            "required": []
        }

        data = ["not", "an", "object"]

        with self.assertRaises(RuntimeError) as context:
            self.processor._validate_json_schema(data, schema, "test")

        self.assertIn("expected object", str(context.exception).lower())


class TestStructuredOutputNoFallbacks(unittest.TestCase):
    """Test that structured output FAILS without fallbacks"""

    def setUp(self):
        """Set up test processor"""
        self.processor = LiveDocumentProcessor()

    @patch('web_ui.document_processor.get_agent_adapter')
    def test_agent_returns_non_json(self, mock_get_adapter):
        """Test that non-JSON response causes failure (no fallback)"""
        # Mock adapter returns plain text
        mock_adapter = Mock()
        mock_adapter.invoke.return_value = json.dumps({
            "type": "result",
            "result": "This is just plain text, not JSON"
        })
        mock_get_adapter.return_value = mock_adapter

        schema = {
            "type": "object",
            "properties": {"answer": {"type": "string"}},
            "required": ["answer"]
        }

        with self.assertRaises(RuntimeError) as context:
            self.processor._invoke_agent_with_structured_output(
                "Test prompt",
                schema,
                "test-task"
            )

        error_msg = str(context.exception)
        # Check for clear error message
        self.assertIn("Could not extract valid JSON", error_msg)
        self.assertIn("Parse error", error_msg)
        self.assertIn("Agent returned", error_msg)

    @patch('web_ui.document_processor.get_agent_adapter')
    def test_agent_returns_json_embedded_in_text(self, mock_get_adapter):
        """Test extraction of JSON embedded in explanatory text"""
        # Mock adapter returns JSON embedded in conversational response
        mock_adapter = Mock()
        mock_adapter.invoke.return_value = json.dumps({
            "type": "result",
            "result": "Sure! Here's the answer you requested: {\"answer\": \"42\", \"confidence\": 0.95} Hope that helps!"
        })
        mock_get_adapter.return_value = mock_adapter

        schema = {
            "type": "object",
            "properties": {
                "answer": {"type": "string"},
                "confidence": {"type": "number"}
            },
            "required": ["answer", "confidence"]
        }

        # Should SUCCEED - robust extraction finds embedded JSON
        result = self.processor._invoke_agent_with_structured_output(
            "Test prompt",
            schema,
            "test-task"
        )

        self.assertEqual(result["answer"], "42")
        self.assertEqual(result["confidence"], 0.95)

    @patch('web_ui.document_processor.get_agent_adapter')
    def test_agent_returns_json_in_code_block_extracted_successfully(self, mock_get_adapter):
        """Test that JSON in code blocks is extracted (robust extraction)"""
        # Mock adapter returns JSON wrapped in markdown code block
        mock_adapter = Mock()
        mock_adapter.invoke.return_value = json.dumps({
            "type": "result",
            "result": "Here's the JSON:\n```json\n{\"answer\": \"42\"}\n```"
        })
        mock_get_adapter.return_value = mock_adapter

        schema = {
            "type": "object",
            "properties": {"answer": {"type": "string"}},
            "required": ["answer"]
        }

        # Should SUCCEED - robust extraction finds JSON in code block
        result = self.processor._invoke_agent_with_structured_output(
            "Test prompt",
            schema,
            "test-task"
        )

        self.assertEqual(result["answer"], "42")

    @patch('web_ui.document_processor.get_agent_adapter')
    def test_agent_returns_triple_backticks_extracted_successfully(self, mock_get_adapter):
        """Test the EXACT scenario from user screenshot - now FIXED with robust extraction"""
        # Mock adapter returns JSON with triple backticks at start (like user saw)
        mock_adapter = Mock()
        mock_adapter.invoke.return_value = json.dumps({
            "type": "result",
            "result": '```json\n{\n  "claims": [\n    {\n      "text": "During certain historical periods...",\n      "type": "factual",\n      "confidence": 0.9\n    }\n  ]\n}\n```'
        })
        mock_get_adapter.return_value = mock_adapter

        schema = {
            "type": "object",
            "properties": {
                "claims": {"type": "array"}
            },
            "required": ["claims"]
        }

        # Should SUCCEED - robust extraction handles code blocks
        result = self.processor._invoke_agent_with_structured_output(
            "Test prompt",
            schema,
            "claim-extraction"
        )

        # Verify we got the data
        self.assertIn("claims", result)
        self.assertEqual(len(result["claims"]), 1)
        self.assertEqual(result["claims"][0]["text"], "During certain historical periods...")

    @patch('web_ui.document_processor.get_agent_adapter')
    def test_agent_returns_valid_json(self, mock_get_adapter):
        """Test that valid raw JSON succeeds"""
        # Mock adapter returns valid JSON
        mock_adapter = Mock()
        mock_adapter.invoke.return_value = json.dumps({
            "type": "result",
            "result": json.dumps({"answer": "42"})
        })
        mock_get_adapter.return_value = mock_adapter

        schema = {
            "type": "object",
            "properties": {"answer": {"type": "string"}},
            "required": ["answer"]
        }

        result = self.processor._invoke_agent_with_structured_output(
            "Test prompt",
            schema,
            "test-task"
        )

        self.assertEqual(result["answer"], "42")

    @patch('web_ui.document_processor.get_agent_adapter')
    def test_agent_returns_json_missing_required_field(self, mock_get_adapter):
        """Test that JSON missing required fields causes failure"""
        # Mock adapter returns JSON without required field
        mock_adapter = Mock()
        mock_adapter.invoke.return_value = json.dumps({
            "type": "result",
            "result": json.dumps({"wrong_field": "value"})
        })
        mock_get_adapter.return_value = mock_adapter

        schema = {
            "type": "object",
            "properties": {"answer": {"type": "string"}},
            "required": ["answer"]
        }

        with self.assertRaises(RuntimeError) as context:
            self.processor._invoke_agent_with_structured_output(
                "Test prompt",
                schema,
                "test-task"
            )

        error_msg = str(context.exception).lower()
        self.assertIn("missing required fields", error_msg)

    @patch('web_ui.document_processor.get_agent_adapter')
    def test_agent_returns_json_wrong_type(self, mock_get_adapter):
        """Test that JSON with wrong field types causes failure"""
        # Mock adapter returns JSON with wrong type
        mock_adapter = Mock()
        mock_adapter.invoke.return_value = json.dumps({
            "type": "result",
            "result": json.dumps({"claims": "should be array not string"})
        })
        mock_get_adapter.return_value = mock_adapter

        schema = {
            "type": "object",
            "properties": {
                "claims": {"type": "array"}
            },
            "required": ["claims"]
        }

        with self.assertRaises(RuntimeError) as context:
            self.processor._invoke_agent_with_structured_output(
                "Test prompt",
                schema,
                "test-task"
            )

        error_msg = str(context.exception).lower()
        self.assertIn("should be array", error_msg)


class TestClaimExtractionValidation(unittest.TestCase):
    """Test claim extraction with strict validation"""

    def setUp(self):
        """Set up test processor"""
        self.processor = LiveDocumentProcessor()

    @patch('web_ui.document_processor.get_agent_adapter')
    def test_extract_claims_success(self, mock_get_adapter):
        """Test successful claim extraction with valid schema"""
        mock_adapter = Mock()
        mock_adapter.invoke.return_value = json.dumps({
            "type": "result",
            "result": json.dumps({
                "claims": [
                    {
                        "text": "Test claim",
                        "type": "factual",
                        "confidence": 0.9
                    }
                ]
            })
        })
        mock_get_adapter.return_value = mock_adapter

        claims = self.processor._extract_claims_with_agent("Test text")

        self.assertEqual(len(claims), 1)
        self.assertEqual(claims[0]["text"], "Test claim")
        self.assertEqual(claims[0]["type"], "factual")
        self.assertEqual(claims[0]["confidence"], 0.9)

    @patch('web_ui.document_processor.get_agent_adapter')
    def test_extract_claims_non_array(self, mock_get_adapter):
        """Test that non-array claims field causes failure"""
        mock_adapter = Mock()
        mock_adapter.invoke.return_value = json.dumps({
            "type": "result",
            "result": json.dumps({
                "claims": "not an array"
            })
        })
        mock_get_adapter.return_value = mock_adapter

        with self.assertRaises(RuntimeError) as context:
            self.processor._extract_claims_with_agent("Test text")

        self.assertIn("should be array", str(context.exception))


class TestClaimSimplificationValidation(unittest.TestCase):
    """Test claim simplification with strict validation"""

    def setUp(self):
        """Set up test processor"""
        self.processor = LiveDocumentProcessor()

    @patch('web_ui.document_processor.get_agent_adapter')
    def test_simplify_claim_success(self, mock_get_adapter):
        """Test successful claim simplification"""
        mock_adapter = Mock()
        mock_adapter.invoke.return_value = json.dumps({
            "type": "result",
            "result": json.dumps({
                "simplified": "Short version",
                "normalized": "Longer normalized version"
            })
        })
        mock_get_adapter.return_value = mock_adapter

        result = self.processor._simplify_claim_with_agent("Original claim text")

        self.assertEqual(result["simplified"], "Short version")
        self.assertEqual(result["normalized"], "Longer normalized version")

    @patch('web_ui.document_processor.get_agent_adapter')
    def test_simplify_claim_missing_field(self, mock_get_adapter):
        """Test that missing required field causes failure"""
        mock_adapter = Mock()
        mock_adapter.invoke.return_value = json.dumps({
            "type": "result",
            "result": json.dumps({
                "simplified": "Short version"
                # Missing "normalized"
            })
        })
        mock_get_adapter.return_value = mock_adapter

        with self.assertRaises(RuntimeError) as context:
            self.processor._simplify_claim_with_agent("Original claim text")

        self.assertIn("missing required fields", str(context.exception).lower())
        self.assertIn("normalized", str(context.exception))


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
