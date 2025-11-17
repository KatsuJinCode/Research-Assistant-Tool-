"""
Real-time Document Processor with Live Updates

Processes documents incrementally, sending updates to clients via callback.
Uses configurable AI agent CLIs for intelligent extraction and analysis.
Supports: Claude Code, OpenAI Codex, Gemini Code, and custom adapters.
"""

import logging
import json
from pathlib import Path
from typing import Callable, Dict, Any, List
from uuid import uuid4

from research_agent.document_processing.pdf_extractor import PDFExtractor
from research_agent.claim_analysis.claim_space_optimizer import ClaimSpaceOptimizer
from research_agent.neo4j_database import Neo4jDatabase
from web_ui.agent_config import get_agent_adapter

logger = logging.getLogger(__name__)


class LiveDocumentProcessor:
    """Process documents with real-time progress updates."""

    def __init__(self, progress_callback: Callable[[str, float, Dict], None] = None):
        """
        Initialize processor.

        Args:
            progress_callback: Function called with (status_message, progress_percent, data)
        """
        self.progress_callback = progress_callback or self._default_callback
        self.db = Neo4jDatabase()

    def _default_callback(self, message: str, progress: float, data: Dict[str, Any]):
        """Default callback - just log."""
        logger.info(f"[{progress:.0f}%] {message}")

    def _emit(self, message: str, progress: float, data: Dict[str, Any] = None):
        """Emit progress update."""
        self.progress_callback(message, progress, data or {})

    def _invoke_agent_with_tool(self, prompt: str, tool_schema: Dict, task_type: str) -> Dict[str, Any]:
        """
        Invoke AI agent CLI with a tool definition to get structured output.
        Uses the configured agent adapter (Claude, OpenAI, Gemini, or custom).

        Args:
            prompt: The task prompt for the agent
            tool_schema: Tool definition with input_schema
            task_type: Type of task (for logging)

        Returns:
            Parsed tool input (the structured data)
        """
        adapter = get_agent_adapter()
        logger.info(f"Spawning {adapter.__class__.__name__} for {task_type}")

        try:
            # Invoke agent through adapter
            response = adapter.invoke(prompt, tools=[tool_schema], timeout=120)
            logger.info(f"Agent completed {task_type}: {len(response)} chars")

            # Parse tool response through adapter
            tool_input = adapter.parse_tool_response(response)
            logger.info(f"✓ Extracted structured data from tool use")
            return tool_input

        except Exception as e:
            logger.error(f"Agent invocation failed: {e}")
            raise

    def _extract_claims_with_agent(self, text: str) -> List[Dict[str, Any]]:
        """
        Use Claude Code agent to extract claims from text using tool calling.

        Returns list of claims with 'text', 'type', 'confidence' fields.

        Raises:
            RuntimeError: If agent fails or returns invalid data
        """
        # Define tool schema for structured output
        tool_schema = {
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
                                "text": {"type": "string", "description": "Exact claim text from document"},
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

        # Spawn Claude Code agent with tool definition
        agent_prompt = f"""Extract factual research claims from this text. Ignore copyright notices, publication info, and page headers/footers.

TEXT:
{text[:8000]}

For each ACTUAL RESEARCH CLAIM (not metadata):
1. Extract the exact claim text
2. Classify type (factual, methodological, causal, interpretive)
3. Rate confidence (0.0-1.0)

Extract 10-20 claims. Preserve qualifiers (may, might, can, all, some). ONLY research claims, not metadata.

IMPORTANT: You MUST call the submit_extracted_claims tool with your results."""

        result = self._invoke_agent_with_tool(agent_prompt, tool_schema, "claim-extraction")

        # Extract claims from tool call
        claims = result.get('claims', [])

        if not isinstance(claims, list):
            logger.error(f"Tool returned non-list: {type(claims)}")
            raise RuntimeError(f"Tool returned invalid data type: {type(claims)}")

        logger.info(f"✓ Claude Code agent extracted {len(claims)} claims via tool use")
        return claims

    def _simplify_claim_with_agent(self, claim_text: str) -> Dict[str, str]:
        """
        Use Claude Code agent to simplify and normalize a claim using tool calling.

        Returns dict with 'simplified', 'normalized' versions.

        Raises:
            RuntimeError: If agent fails or returns invalid data
        """
        # Define tool schema for structured output
        tool_schema = {
            "name": "submit_simplified_claim",
            "description": "Submit the simplified and normalized versions of the claim",
            "input_schema": {
                "type": "object",
                "properties": {
                    "simplified": {"type": "string", "description": "5-10 word core assertion"},
                    "normalized": {"type": "string", "description": "15-20 word normalized version"}
                },
                "required": ["simplified", "normalized"]
            }
        }

        agent_prompt = f"""Simplify this claim, preserving all qualifiers (may, might, can, all, some, etc.):

"{claim_text}"

Create:
1. simplified: 5-10 word core assertion
2. normalized: 15-20 word version

IMPORTANT: You MUST call the submit_simplified_claim tool with your results."""

        result = self._invoke_agent_with_tool(agent_prompt, tool_schema, "claim-simplification")

        if 'simplified' not in result or 'normalized' not in result:
            logger.error(f"Tool returned incomplete response: missing required fields")
            raise RuntimeError("Tool response missing 'simplified' or 'normalized' fields")

        logger.info(f"✓ Claude Code agent simplified claim via tool use")
        return result

    def process_document(self, file_path: str, doc_id: str = None) -> str:
        """
        Process document with live updates.

        Args:
            file_path: Path to PDF file
            doc_id: Optional document ID (generated if not provided)

        Returns:
            document_id
        """
        if not doc_id:
            doc_id = str(uuid4())

        # 1. Create document node
        self._emit("Creating document node...", 5, {
            'event': 'document_created',
            'doc_id': doc_id,
            'file_path': file_path
        })

        doc_node = {
            'id': doc_id,
            'title': Path(file_path).name,
            'source_file': file_path,
            'status': 'processing'
        }
        self.db.create_node('Document', doc_node)

        # 2. Extract text
        self._emit("Extracting text from PDF...", 10, {
            'event': 'text_extraction_started',
            'doc_id': doc_id
        })

        extractor = PDFExtractor(column_aware=True, postprocess=True)
        extraction_result = extractor.extract(Path(file_path))
        text = extraction_result['full_text']

        self._emit(f"Extracted {len(text)} characters", 20, {
            'event': 'text_extracted',
            'doc_id': doc_id,
            'char_count': len(text)
        })

        # 3. Extract claims using Claude Code agent
        self._emit("Extracting claims with AI...", 30, {
            'event': 'claim_extraction_started',
            'doc_id': doc_id
        })

        try:
            claims = self._extract_claims_with_agent(text)
        except Exception as e:
            error_msg = f"Claude Code agent failed to extract claims: {str(e)}"
            logger.error(error_msg)
            self._emit(f"ERROR: {error_msg}", 30, {
                'event': 'claim_extraction_failed',
                'doc_id': doc_id,
                'error': str(e)
            })
            # Mark document as failed
            self.db.driver.session(database=self.db.database).run(
                "MATCH (d:Document {id: $doc_id}) SET d.status = 'failed', d.error = $error",
                doc_id=doc_id,
                error=error_msg
            )
            raise

        self._emit(f"Extracted {len(claims)} claims", 50, {
            'event': 'claims_extracted',
            'doc_id': doc_id,
            'claim_count': len(claims)
        })

        # 4. Add claims to graph incrementally with live updates
        for i, claim_data in enumerate(claims):
            progress = 50 + (i / len(claims)) * 30  # 50% to 80%

            # Create claim node
            claim_id = str(uuid4())

            # Simplify using agent
            try:
                simplification = self._simplify_claim_with_agent(claim_data['text'])
            except Exception as e:
                error_msg = f"Claude Code agent failed to simplify claim {i+1}: {str(e)}"
                logger.error(error_msg)
                self._emit(f"ERROR: {error_msg}", progress, {
                    'event': 'claim_simplification_failed',
                    'doc_id': doc_id,
                    'claim_index': i + 1,
                    'error': str(e)
                })
                # Mark document as failed
                self.db.driver.session(database=self.db.database).run(
                    "MATCH (d:Document {id: $doc_id}) SET d.status = 'failed', d.error = $error",
                    doc_id=doc_id,
                    error=error_msg
                )
                raise

            claim_node = {
                'id': claim_id,
                'text': claim_data['text'],
                'summary': simplification['simplified'],
                'simplified': simplification['simplified'],
                'normalized': simplification['normalized'],
                'is_optimal': True  # Will be updated by optimizer
            }

            self.db.create_node('Claim', claim_node)
            self.db.create_relationship(doc_id, claim_id, 'CONTAINS_CLAIM', {})

            # Emit live update for each claim
            self._emit(f"Added claim {i+1}/{len(claims)}", progress, {
                'event': 'claim_added',
                'doc_id': doc_id,
                'claim_id': claim_id,
                'claim_summary': simplification['simplified'],
                'total_claims': len(claims),
                'current_claim': i + 1
            })

        # 5. Skip optimization for now (too slow for web interface)
        self._emit("Skipping claim hierarchy analysis (can run later)", 90, {
            'event': 'optimization_skipped',
            'doc_id': doc_id
        })

        # TODO: Run optimization in background or on-demand
        # optimizer = ClaimSpaceOptimizer()
        # optimizer.optimize_claim_space(self.db)

        # 6. Mark document as complete
        self.db.driver.session(database=self.db.database).run(
            "MATCH (d:Document {id: $doc_id}) SET d.status = 'complete'",
            doc_id=doc_id
        )

        self._emit("Document processing complete!", 100, {
            'event': 'processing_complete',
            'doc_id': doc_id
        })

        return doc_id
