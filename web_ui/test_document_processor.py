"""
Unit tests for LiveDocumentProcessor

Tests agent invocation, tool calling, claim extraction, and error handling.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import tempfile

from web_ui.document_processor import LiveDocumentProcessor


class TestLiveDocumentProcessor(unittest.TestCase):
    """Test suite for LiveDocumentProcessor"""

    def setUp(self):
        """Set up test fixtures"""
        self.progress_callback = Mock()
        self.processor = LiveDocumentProcessor(self.progress_callback)

    def test_init(self):
        """Test processor initialization"""
        self.assertIsNotNone(self.processor.db)
        self.assertEqual(self.processor.progress_callback, self.progress_callback)

    def test_emit_progress(self):
        """Test progress callback emission"""
        self.processor._emit("Test message", 50, {"event": "test"})
        self.progress_callback.assert_called_once_with(
            "Test message", 50, {"event": "test"}
        )

    @patch('document_processor.subprocess.run')
    def test_invoke_agent_with_tool_success(self, mock_run):
        """Test successful agent invocation with tool"""
        # Mock successful tool response
        tool_response = {
            "content": [{
                "type": "tool_use",
                "input": {
                    "simplified": "Test claim",
                    "normalized": "This is a test claim for validation"
                }
            }]
        }

        mock_run.return_value = Mock(
            returncode=0,
            stdout=json.dumps(tool_response),
            stderr=""
        )

        tool_schema = {
            "name": "submit_simplified_claim",
            "input_schema": {
                "type": "object",
                "properties": {
                    "simplified": {"type": "string"},
                    "normalized": {"type": "string"}
                },
                "required": ["simplified", "normalized"]
            }
        }

        result = self.processor._invoke_agent_with_tool(
            "Test prompt",
            tool_schema,
            "test-task"
        )

        self.assertEqual(result["simplified"], "Test claim")
        self.assertEqual(result["normalized"], "This is a test claim for validation")

    @patch('document_processor.subprocess.run')
    def test_invoke_agent_with_tool_no_tool_use(self, mock_run):
        """Test agent response with no tool use"""
        # Mock response without tool use
        mock_run.return_value = Mock(
            returncode=0,
            stdout=json.dumps({"content": [{"type": "text", "text": "No tool"}]}),
            stderr=""
        )

        tool_schema = {
            "name": "test_tool",
            "input_schema": {"type": "object", "properties": {}}
        }

        with self.assertRaises(RuntimeError) as context:
            self.processor._invoke_agent_with_tool(
                "Test prompt",
                tool_schema,
                "test-task"
            )

        self.assertIn("did not call the required tool", str(context.exception))

    @patch('document_processor.subprocess.run')
    def test_invoke_agent_with_tool_process_failure(self, mock_run):
        """Test agent process failure"""
        mock_run.return_value = Mock(
            returncode=1,
            stdout="",
            stderr="Error: Command failed"
        )

        tool_schema = {
            "name": "test_tool",
            "input_schema": {"type": "object", "properties": {}}
        }

        with self.assertRaises(RuntimeError) as context:
            self.processor._invoke_agent_with_tool(
                "Test prompt",
                tool_schema,
                "test-task"
            )

        self.assertIn("Agent process failed", str(context.exception))

    @patch.object(LiveDocumentProcessor, '_invoke_agent_with_tool')
    def test_extract_claims_with_agent_success(self, mock_invoke):
        """Test successful claim extraction"""
        # Mock tool response
        mock_invoke.return_value = {
            "claims": [
                {"text": "Claim 1", "type": "factual", "confidence": 0.9},
                {"text": "Claim 2", "type": "methodological", "confidence": 0.85}
            ]
        }

        claims = self.processor._extract_claims_with_agent("Test text")

        self.assertEqual(len(claims), 2)
        self.assertEqual(claims[0]["text"], "Claim 1")
        self.assertEqual(claims[1]["type"], "methodological")

    @patch.object(LiveDocumentProcessor, '_invoke_agent_with_tool')
    def test_extract_claims_with_agent_invalid_response(self, mock_invoke):
        """Test claim extraction with invalid response"""
        # Mock invalid response (not a list)
        mock_invoke.return_value = {
            "claims": "not a list"
        }

        with self.assertRaises(RuntimeError) as context:
            self.processor._extract_claims_with_agent("Test text")

        self.assertIn("invalid data type", str(context.exception))

    @patch.object(LiveDocumentProcessor, '_invoke_agent_with_tool')
    def test_simplify_claim_with_agent_success(self, mock_invoke):
        """Test successful claim simplification"""
        mock_invoke.return_value = {
            "simplified": "Short claim",
            "normalized": "This is a normalized claim version"
        }

        result = self.processor._simplify_claim_with_agent("Long verbose claim text")

        self.assertEqual(result["simplified"], "Short claim")
        self.assertEqual(result["normalized"], "This is a normalized claim version")

    @patch.object(LiveDocumentProcessor, '_invoke_agent_with_tool')
    def test_simplify_claim_with_agent_missing_fields(self, mock_invoke):
        """Test claim simplification with missing required fields"""
        mock_invoke.return_value = {
            "simplified": "Short claim"
            # Missing 'normalized' field
        }

        with self.assertRaises(RuntimeError) as context:
            self.processor._simplify_claim_with_agent("Test claim")

        self.assertIn("missing", str(context.exception).lower())

    def test_default_callback(self):
        """Test default progress callback"""
        processor = LiveDocumentProcessor()
        # Should not raise any errors
        processor._default_callback("Test", 50, {})


class TestToolSchemaGeneration(unittest.TestCase):
    """Test tool schema definitions"""

    def test_claim_extraction_schema(self):
        """Test claim extraction tool schema is valid"""
        schema = {
            "name": "submit_extracted_claims",
            "description": "Submit the list of extracted research claims",
            "input_schema": {
                "type": "object",
                "properties": {
                    "claims": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "text": {"type": "string"},
                                "type": {"type": "string", "enum": ["factual", "methodological", "causal", "interpretive"]},
                                "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0}
                            },
                            "required": ["text", "type", "confidence"]
                        }
                    }
                },
                "required": ["claims"]
            }
        }

        # Validate schema structure
        self.assertEqual(schema["name"], "submit_extracted_claims")
        self.assertIn("claims", schema["input_schema"]["properties"])
        self.assertEqual(schema["input_schema"]["properties"]["claims"]["type"], "array")

    def test_simplification_schema(self):
        """Test claim simplification tool schema is valid"""
        schema = {
            "name": "submit_simplified_claim",
            "description": "Submit the simplified and normalized versions of the claim",
            "input_schema": {
                "type": "object",
                "properties": {
                    "simplified": {"type": "string"},
                    "normalized": {"type": "string"}
                },
                "required": ["simplified", "normalized"]
            }
        }

        # Validate schema structure
        self.assertEqual(schema["name"], "submit_simplified_claim")
        self.assertIn("simplified", schema["input_schema"]["properties"])
        self.assertIn("normalized", schema["input_schema"]["properties"])


if __name__ == '__main__':
    unittest.main()
