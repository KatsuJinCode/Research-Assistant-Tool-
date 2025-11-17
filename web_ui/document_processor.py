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

    def _invoke_agent_with_structured_output(self, prompt: str, expected_schema: Dict, task_type: str) -> Dict[str, Any]:
        """
        Invoke AI agent CLI and request structured JSON output.

        Since Claude Code CLI --tools flag doesn't force tool use, we use prompt-based
        JSON extraction instead.

        Args:
            prompt: The task prompt
            expected_schema: JSON schema describing expected output structure
            task_type: Description of task (for logging)

        Returns:
            Parsed JSON output as dict

        Raises:
            RuntimeError: If agent fails or doesn't return valid JSON
        """
        adapter = get_agent_adapter()
        logger.info(f"Spawning {adapter.__class__.__name__} for {task_type}")

        # Add JSON formatting instructions to prompt (emphasize backend system requirement)
        schema_str = json.dumps(expected_schema, indent=2)
        enhanced_prompt = f"""{prompt}

CRITICAL: This is for a backend system that directly parses your response.
You MUST respond with ONLY raw JSON. No explanations, no markdown, no code blocks.

Required JSON schema:
{schema_str}

Output ONLY the JSON object. Nothing before it, nothing after it.
Your response will be parsed by json.loads() - it must be valid JSON."""

        # Retry loop: Try up to 3 times with re-prompting if validation fails
        max_retries = 3
        last_error = None
        last_response_text = None

        for attempt in range(max_retries):
            try:
                # For retries, add correction prompt
                if attempt > 0:
                    retry_prompt = f"""RETRY {attempt}/{max_retries-1}: Your previous response had errors.

Previous response that failed validation:
{last_response_text[:500]}

Error encountered:
{last_error}

Required JSON schema:
{schema_str}

Please fix the response. Output ONLY valid JSON matching the schema exactly.
No explanations, no markdown, no code blocks. Just raw JSON."""
                    logger.info(f"{task_type}: Retry attempt {attempt} - re-prompting agent to fix response")
                    current_prompt = retry_prompt
                else:
                    current_prompt = enhanced_prompt

                # Invoke agent
                response = adapter.invoke(current_prompt, tools=None, timeout=120)
                logger.info(f"Agent completed {task_type} (attempt {attempt+1}): {len(response)} chars")

                # Parse response - handle CLI wrapper format
                response_data = json.loads(response)

                # Extract actual result from CLI wrapper if present
                if isinstance(response_data, dict) and 'result' in response_data:
                    result_text = response_data['result']
                else:
                    result_text = response

                last_response_text = result_text  # Save for retry prompt

                # Robust JSON extraction - try multiple strategies
                parsed_json = self._extract_json_from_response(result_text, task_type)
                logger.info(f"✓ Agent returned valid JSON (attempt {attempt+1})")

                # Validate against schema - check required fields STRICTLY
                self._validate_json_schema(parsed_json, expected_schema, task_type)

                if attempt > 0:
                    logger.info(f"✓ {task_type}: Validation succeeded after {attempt+1} attempts")

                return parsed_json

            except (json.JSONDecodeError, RuntimeError) as e:
                last_error = str(e)
                logger.warning(f"{task_type}: Attempt {attempt+1} failed: {e}")

                # If this was the last attempt, raise the error
                if attempt == max_retries - 1:
                    error_msg = (
                        f"❌ AGENT ERROR ({task_type}): Failed after {max_retries} attempts.\n\n"
                        f"Final error: {last_error}\n\n"
                        f"Last response:\n{last_response_text[:300] if last_response_text else 'No response'}...\n\n"
                        f"The agent could not produce valid JSON matching the schema after multiple retries."
                    )
                    logger.error(error_msg)
                    raise RuntimeError(error_msg)

                # Otherwise, continue to next retry
                continue

    def _extract_json_from_response(self, text: str, task_type: str) -> Dict[str, Any]:
        """
        Robust JSON extraction - tries multiple strategies to find JSON in response.

        Strategy order:
        1. Try parsing as raw JSON (Claude followed instructions)
        2. Extract from markdown code blocks (```json or ```)
        3. Find first { ... } or [ ... ] structure in text
        4. Fail with clear error

        Args:
            text: Raw response text from agent
            task_type: Description for logging

        Returns:
            Parsed JSON dict

        Raises:
            json.JSONDecodeError: If no valid JSON found
        """
        import re

        # Strategy 1: Try raw JSON (best case)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Strategy 2: Extract from code blocks
        # Match ```json\n{...}\n``` or ```\n{...}\n```
        code_block_pattern = r'```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```'
        match = re.search(code_block_pattern, text, re.DOTALL)
        if match:
            logger.info(f"{task_type}: Extracted JSON from markdown code block")
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # Strategy 3: Find first JSON object or array in text
        # Look for standalone { ... } or [ ... ]
        json_obj_pattern = r'\{(?:[^{}]|(?R))*\}'  # Matches balanced braces
        # Simpler approach: find first { and matching }
        brace_start = text.find('{')
        bracket_start = text.find('[')

        # Try object first if it appears before array
        if brace_start != -1 and (bracket_start == -1 or brace_start < bracket_start):
            depth = 0
            for i in range(brace_start, len(text)):
                if text[i] == '{':
                    depth += 1
                elif text[i] == '}':
                    depth -= 1
                    if depth == 0:
                        candidate = text[brace_start:i+1]
                        try:
                            logger.info(f"{task_type}: Extracted JSON object from embedded text")
                            return json.loads(candidate)
                        except json.JSONDecodeError:
                            break

        # Try array
        if bracket_start != -1:
            depth = 0
            for i in range(bracket_start, len(text)):
                if text[i] == '[':
                    depth += 1
                elif text[i] == ']':
                    depth -= 1
                    if depth == 0:
                        candidate = text[bracket_start:i+1]
                        try:
                            logger.info(f"{task_type}: Extracted JSON array from embedded text")
                            return json.loads(candidate)
                        except json.JSONDecodeError:
                            break

        # Strategy 4: All failed
        raise json.JSONDecodeError("No valid JSON found in response", text, 0)

    def _validate_json_schema(self, data: Dict, schema: Dict, task_type: str):
        """
        Validate JSON data against schema - check required fields exist.

        Args:
            data: Parsed JSON data
            schema: Expected JSON schema
            task_type: Description for error messages

        Raises:
            RuntimeError: If validation fails
        """
        if not isinstance(data, dict):
            raise RuntimeError(f"{task_type}: Expected object, got {type(data).__name__}")

        # Check required fields at root level
        required_fields = schema.get('required', [])
        missing_fields = [field for field in required_fields if field not in data]

        if missing_fields:
            raise RuntimeError(
                f"{task_type}: JSON missing required fields: {missing_fields}. "
                f"Got fields: {list(data.keys())}"
            )

        # Validate field types if specified
        properties = schema.get('properties', {})
        for field_name, field_schema in properties.items():
            if field_name in data:
                expected_type = field_schema.get('type')
                actual_value = data[field_name]

                # Type checking
                if expected_type == 'array' and not isinstance(actual_value, list):
                    raise RuntimeError(
                        f"{task_type}: Field '{field_name}' should be array, got {type(actual_value).__name__}"
                    )
                elif expected_type == 'object' and not isinstance(actual_value, dict):
                    raise RuntimeError(
                        f"{task_type}: Field '{field_name}' should be object, got {type(actual_value).__name__}"
                    )
                elif expected_type == 'string' and not isinstance(actual_value, str):
                    raise RuntimeError(
                        f"{task_type}: Field '{field_name}' should be string, got {type(actual_value).__name__}"
                    )
                elif expected_type == 'number' and not isinstance(actual_value, (int, float)):
                    raise RuntimeError(
                        f"{task_type}: Field '{field_name}' should be number, got {type(actual_value).__name__}"
                    )

        logger.info(f"✓ JSON schema validation passed for {task_type}")

    def _extract_claims_with_agent(self, text: str) -> List[Dict[str, Any]]:
        """
        Use AI agent to extract claims from text with structured JSON output.

        Returns list of claims with 'text', 'type', 'confidence' fields.

        Raises:
            RuntimeError: If agent fails or returns invalid data
        """
        # Define expected JSON schema
        expected_schema = {
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

        # Prompt for claim extraction
        agent_prompt = f"""Extract factual research claims from this text. Ignore copyright notices, publication info, and page headers/footers.

TEXT:
{text[:8000]}

For each ACTUAL RESEARCH CLAIM (not metadata):
1. Extract the exact claim text
2. Classify type (factual, methodological, causal, interpretive)
3. Rate confidence (0.0-1.0)

Extract 10-20 claims. Preserve qualifiers (may, might, can, all, some). ONLY research claims, not metadata."""

        result = self._invoke_agent_with_structured_output(agent_prompt, expected_schema, "claim-extraction")

        # Extract claims from response
        claims = result.get('claims', [])

        if not isinstance(claims, list):
            logger.error(f"Response returned non-list: {type(claims)}")
            raise RuntimeError(f"Response returned invalid data type: {type(claims)}")

        logger.info(f"✓ AI agent extracted {len(claims)} claims via structured JSON")
        return claims

    def _simplify_claim_with_agent(self, claim_text: str) -> Dict[str, str]:
        """
        Use AI agent to simplify and normalize a claim with structured JSON output.

        Returns dict with 'simplified', 'normalized' versions.

        Raises:
            RuntimeError: If agent fails or returns invalid data
        """
        # Define expected JSON schema
        expected_schema = {
            "type": "object",
            "properties": {
                "simplified": {"type": "string", "description": "5-10 word core assertion"},
                "normalized": {"type": "string", "description": "15-20 word normalized version"}
            },
            "required": ["simplified", "normalized"]
        }

        agent_prompt = f"""Simplify this claim, preserving all qualifiers (may, might, can, all, some, etc.):

"{claim_text}"

Create:
1. simplified: 5-10 word core assertion
2. normalized: 15-20 word version"""

        result = self._invoke_agent_with_structured_output(agent_prompt, expected_schema, "claim-simplification")

        if 'simplified' not in result or 'normalized' not in result:
            logger.error(f"Response missing required fields: {result.keys()}")
            raise RuntimeError("Response missing 'simplified' or 'normalized' fields")

        logger.info(f"✓ AI agent simplified claim via structured JSON")
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
