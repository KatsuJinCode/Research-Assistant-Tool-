"""
Real-time Document Processor with Live Updates

Processes documents incrementally, sending updates to clients via callback.
Uses configurable AI agent CLIs for intelligent extraction and analysis.
Supports: Claude Code, OpenAI Codex, Gemini Code, and custom adapters.

PRIMARY METHOD: Semantic embedding-based clustering (optimal, non-overlapping)
FALLBACK METHOD: LLM-based categorization (logged transparently when used)
"""

import logging
import json
import time
from pathlib import Path
from typing import Callable, Dict, Any, List, Tuple
from uuid import uuid4

from research_agent.document_processing.pdf_extractor import PDFExtractor
from research_agent.claim_analysis.claim_space_optimizer import ClaimSpaceOptimizer
# Intelligent summarization handled by _simplify_claim_with_agent() using Claude Code CLI
from research_agent.neo4j_database import Neo4jDatabase
from web_ui.agent_config import get_agent_adapter

# Import semantic clustering (PRIMARY method)
try:
    from web_ui.semantic_clustering import (
        SemanticClaimClusterer,
        check_embedding_availability,
        get_clustering_method_status,
        ClusteringMetrics
    )
    SEMANTIC_CLUSTERING_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Semantic clustering not available: {e}")
    SEMANTIC_CLUSTERING_AVAILABLE = False

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
        self.db = Neo4jDatabase()  # Keep for backward compatibility during migration

        # Repository pattern for new code
        from backend.database.repositories import DocumentRepository, ClaimRepository
        self.doc_repo = DocumentRepository()
        self.claim_repo = ClaimRepository()
        # Summarization uses _simplify_claim_with_agent() - AI-powered via Claude Code CLI

    def _default_callback(self, message: str, progress: float, data: Dict[str, Any]):
        """Default callback - just log."""
        if progress is not None:
            logger.info(f"[{progress:.0f}%] {message}")
        else:
            logger.info(message)

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

    def _extract_and_cluster_claims(self, text: str) -> Tuple[Dict[str, Any], ClusteringMetrics]:
        """
        Extract claims and organize hierarchically.

        PRIMARY: Use semantic embedding clustering (optimal, non-overlapping)
        FALLBACK: Use LLM-based categorization (with transparent logging)

        Returns:
            (hierarchical_structure, metrics)
        """
        # Step 1: Extract flat list of claims using agent
        self._emit("Extracting flat claims...", 30, {'event': 'flat_extraction_started'})

        try:
            flat_claims = self._extract_flat_claims_with_agent(text)
        except Exception as e:
            logger.error(f"Flat claim extraction failed: {e}")
            raise

        self._emit(f"Extracted {len(flat_claims)} claims", 40, {
            'event': 'flat_claims_extracted',
            'claim_count': len(flat_claims)
        })

        # Step 2: Cluster claims using PRIMARY or FALLBACK method
        if SEMANTIC_CLUSTERING_AVAILABLE and check_embedding_availability():
            # PRIMARY METHOD: Semantic embedding clustering
            logger.info("=" * 80)
            logger.info("Using PRIMARY method: Semantic embedding-based clustering")
            logger.info("=" * 80)

            self._emit("Organizing hierarchically using embedding models...", 50, {
                'event': 'semantic_clustering_started',
                'method': 'PRIMARY'
            })

            try:
                clusterer = SemanticClaimClusterer()
                cluster_results, metrics = clusterer.cluster_claims(flat_claims)

                # Convert to hierarchical structure
                categories = []
                for cluster in cluster_results:
                    categories.append({
                        'super_claim': cluster.super_claim_text,
                        'category_description': cluster.super_claim_description,
                        'sub_claims': cluster.sub_claims,
                        'quality_score': cluster.quality_score
                    })

                hierarchical_structure = {'categories': categories}

                logger.info(f"✓ Semantic clustering succeeded - {metrics.n_clusters} optimal clusters")
                logger.info(f"  Silhouette score: {metrics.silhouette_score:.3f} (>0.5 is good)")
                logger.info(f"  Davies-Bouldin score: {metrics.davies_bouldin_score:.3f} (lower is better)")

                return hierarchical_structure, metrics

            except Exception as e:
                logger.warning(f"Semantic clustering failed: {e}")
                logger.warning("Falling back to LLM-based categorization...")
                # Fall through to fallback

        # FALLBACK METHOD: LLM-based categorization
        logger.warning("=" * 80)
        logger.warning("Using FALLBACK method: LLM-based categorization")
        logger.warning("Reason: Semantic clustering not available or failed")
        logger.warning("=" * 80)

        self._emit("Organizing hierarchically using LLM categorization (FALLBACK)...", 50, {
            'event': 'llm_clustering_started',
            'method': 'FALLBACK',
            'reason': 'semantic_clustering_unavailable'
        })

        hierarchical_structure = self._extract_hierarchical_claims_with_agent_llm(text)

        # Create fallback metrics
        fallback_metrics = ClusteringMetrics(
            silhouette_score=-999.0,  # Invalid sentinel value
            davies_bouldin_score=-999.0,
            n_clusters=len(hierarchical_structure.get('categories', [])),
            method='llm-fallback'
        )

        logger.warning(f"LLM categorization created {fallback_metrics.n_clusters} categories")
        logger.warning("⚠️  Note: This method is NOT mathematically optimal")

        return hierarchical_structure, fallback_metrics

    def _extract_flat_claims_with_agent(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract flat list of claims (no categorization yet).

        This is step 1 - gets raw claims for later clustering.
        """
        expected_schema = {
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

        agent_prompt = f"""Extract research claims from this text. Ignore copyright, metadata, headers/footers.

TEXT:
{text[:8000]}

For each ACTUAL RESEARCH CLAIM (not metadata):
1. Extract exact claim text
2. Classify type (factual, methodological, causal, interpretive)
3. Rate confidence (0.0-1.0)

Extract 10-20 claims. Preserve qualifiers (may, might, can, all, some). ONLY research claims."""

        result = self._invoke_agent_with_structured_output(agent_prompt, expected_schema, "flat-claim-extraction")
        claims = result.get('claims', [])

        if not isinstance(claims, list):
            raise RuntimeError(f"Expected list, got {type(claims)}")

        logger.info(f"✓ Extracted {len(claims)} flat claims for clustering")
        return claims

    def _extract_hierarchical_claims_with_agent_llm(self, text: str) -> Dict[str, Any]:
        """
        Use AI agent to extract HIERARCHICAL claims (categories + specific claims).

        Returns dict with 'categories', each containing 'super_claim' and 'sub_claims'.

        Raises:
            RuntimeError: If agent fails or returns invalid data
        """
        # Define expected JSON schema for hierarchical structure
        expected_schema = {
            "type": "object",
            "properties": {
                "categories": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "super_claim": {
                                "type": "string",
                                "description": "Generalized category claim (e.g., 'Mental illness is not a medical condition')"
                            },
                            "category_description": {
                                "type": "string",
                                "description": "Brief explanation of this claim category"
                            },
                            "sub_claims": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "text": {"type": "string", "description": "Specific claim text"},
                                        "type": {"type": "string", "enum": ["factual", "methodological", "causal", "interpretive"]},
                                        "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0}
                                    },
                                    "required": ["text", "type", "confidence"]
                                }
                            }
                        },
                        "required": ["super_claim", "sub_claims"]
                    }
                }
            },
            "required": ["categories"]
        }

        # Prompt for hierarchical claim extraction
        agent_prompt = f"""Extract research claims from this text in a HIERARCHICAL structure. Ignore copyright, metadata, headers/footers.

TEXT:
{text[:8000]}

Group related claims into CATEGORIES. For each category:
1. super_claim: A generalized claim that summarizes the category (10-15 words)
2. category_description: Brief explanation of this theme
3. sub_claims: 2-5 specific claims that fall under this super-claim

Extract 3-6 categories total. Each sub-claim should have:
- text: Exact claim from document
- type: factual, methodological, causal, or interpretive
- confidence: 0.0-1.0

Preserve qualifiers (may, might, can, all, some). Structure spreads claims across TWO levels (categories → specifics)."""

        result = self._invoke_agent_with_structured_output(agent_prompt, expected_schema, "hierarchical-claim-extraction")

        # Validate structure
        categories = result.get('categories', [])
        if not isinstance(categories, list):
            logger.error(f"Response returned non-list for categories: {type(categories)}")
            raise RuntimeError(f"Response returned invalid data type: {type(categories)}")

        total_claims = sum(len(cat.get('sub_claims', [])) for cat in categories)
        logger.info(f"✓ AI agent extracted {len(categories)} categories with {total_claims} specific claims")
        return result

    def _extract_claims_with_agent(self, text: str) -> List[Dict[str, Any]]:
        """
        Use AI agent to extract claims from text with structured JSON output.

        DEPRECATED: Use _extract_hierarchical_claims_with_agent() for better organization.

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

    def _simplify_claim_with_agent(self, claim_text: str, claim_id: str = None, doc_id: str = None, claim_index: int = None, total_claims: int = None, max_retries: int = 2) -> dict:
        """
        Full 4-stage claim processing pipeline: Analysis → Clarification → Simplification → Validation

        Emits real-time SocketIO events for live frontend updates.
        Returns dict with all processing stages for complete transparency.
        """
        result = {
            'text': claim_text,
            'analysis': None,
            'clarified': None,
            'candidate_1': None,
            'candidate_2': None,
            'candidate_3': None,
            'score_1': 0,
            'score_2': 0,
            'score_3': 0,
            'fidelity_reason': None,
            'quality_score': 0,
            'quality_reason': None,
            'disposition': None,
            'recommendation': None,
            'selected_candidate': None,
            'summary': None,
            'processing_stage': 'created',
            'duration_analysis_ms': 0,
            'duration_clarification_ms': 0,
            'duration_simplification_ms': 0,
            'duration_validation_ms': 0,
            'duration_total_ms': 0
        }

        pipeline_start_time = time.time()

        try:
            # STAGE 1: ANALYSIS - Deep understanding
            start_time = time.time()

            # Create claim preview for UI (truncate to 50 chars)
            claim_preview = claim_text[:50] + '...' if len(claim_text) > 50 else claim_text

            self._emit(f"Analyzing claim for deep understanding...", None, {
                'event': 'claim_stage_update',
                'doc_id': doc_id,
                'claim_id': claim_id,
                'claim_index': claim_index,  # NEW FIELD (1-based)
                'total_claims': total_claims,  # NEW FIELD
                'claim_preview': claim_preview,  # NEW FIELD
                'stage': 'analysis',
                'status': 'in_progress',
                'message': 'Analyzing claim for deep understanding...',
                'data': {
                    'original_text': claim_text,
                    'word_count': len(claim_text.split())
                }
            })

            result['analysis'] = self._analyze_claim(claim_text)
            result['duration_analysis_ms'] = (time.time() - start_time) * 1000
            result['processing_stage'] = 'analyzed'

            self._emit(f"✓ Analysis complete", None, {
                'event': 'claim_stage_update',
                'doc_id': doc_id,
                'claim_id': claim_id,
                'claim_index': claim_index,  # NEW FIELD
                'total_claims': total_claims,  # NEW FIELD
                'claim_preview': claim_preview,  # NEW FIELD
                'stage': 'analysis',
                'status': 'complete',
                'data': {
                    'analysis': result['analysis'],
                    'word_count': len(result['analysis'].split()),
                    'duration_ms': result['duration_analysis_ms']
                }
            })

            # STAGE 2: CLARIFICATION - Make implicit meaning explicit
            start_time = time.time()
            self._emit(f"Clarifying claim meaning...", None, {
                'event': 'claim_stage_update',
                'doc_id': doc_id,
                'claim_id': claim_id,
                'claim_index': claim_index,  # NEW FIELD
                'total_claims': total_claims,  # NEW FIELD
                'claim_preview': claim_preview,  # NEW FIELD
                'stage': 'clarification',
                'status': 'in_progress',
                'message': 'Making implicit meaning explicit...'
            })

            result['clarified'] = self._clarify_claim(claim_text, result['analysis'])
            result['duration_clarification_ms'] = (time.time() - start_time) * 1000
            result['processing_stage'] = 'clarified'

            self._emit(f"✓ Clarification complete", None, {
                'event': 'claim_stage_update',
                'doc_id': doc_id,
                'claim_id': claim_id,
                'claim_index': claim_index,  # NEW FIELD
                'total_claims': total_claims,  # NEW FIELD
                'claim_preview': claim_preview,  # NEW FIELD
                'stage': 'clarification',
                'status': 'complete',
                'data': {
                    'clarified': result['clarified'],
                    'word_count': len(result['clarified'].split()),
                    'duration_ms': result['duration_clarification_ms']
                }
            })

            # STAGE 3: SIMPLIFICATION - Generate 3 optimal candidates
            start_time = time.time()
            self._emit(f"Generating simplified candidates...", None, {
                'event': 'claim_stage_update',
                'doc_id': doc_id,
                'claim_id': claim_id,
                'claim_index': claim_index,  # NEW FIELD
                'total_claims': total_claims,  # NEW FIELD
                'claim_preview': claim_preview,  # NEW FIELD
                'stage': 'simplification',
                'status': 'in_progress',
                'message': 'Generating 3 simplified candidates...'
            })

            candidates = self._simplify_claim_candidates(result['clarified'])
            result['candidate_1'] = candidates['candidate_1']
            result['candidate_2'] = candidates['candidate_2']
            result['candidate_3'] = candidates['candidate_3']
            result['duration_simplification_ms'] = (time.time() - start_time) * 1000
            result['processing_stage'] = 'simplified'

            self._emit(f"✓ Simplification complete", None, {
                'event': 'claim_stage_update',
                'doc_id': doc_id,
                'claim_id': claim_id,
                'claim_index': claim_index,  # NEW FIELD
                'total_claims': total_claims,  # NEW FIELD
                'claim_preview': claim_preview,  # NEW FIELD
                'stage': 'simplification',
                'status': 'complete',
                'data': {
                    'candidate_1': result['candidate_1'],
                    'candidate_2': result['candidate_2'],
                    'candidate_3': result['candidate_3'],
                    'duration_ms': result['duration_simplification_ms']
                }
            })

            # STAGE 4: VALIDATION - Fidelity + Quality scoring
            start_time = time.time()
            self._emit(f"Validating candidates and assessing quality...", None, {
                'event': 'claim_stage_update',
                'doc_id': doc_id,
                'claim_id': claim_id,
                'claim_index': claim_index,  # NEW FIELD
                'total_claims': total_claims,  # NEW FIELD
                'claim_preview': claim_preview,  # NEW FIELD
                'stage': 'validation',
                'status': 'in_progress',
                'message': 'Validating fidelity and assessing quality...'
            })

            validation = self._validate_final(claim_text, result['analysis'], result['clarified'], candidates)
            result['score_1'] = validation.get('score_1', 0)
            result['score_2'] = validation.get('score_2', 0)
            result['score_3'] = validation.get('score_3', 0)
            result['fidelity_reason'] = validation.get('fidelity_reason', '')
            result['quality_score'] = validation.get('quality_score', 0)
            result['quality_reason'] = validation.get('quality_reason', '')
            result['disposition'] = validation.get('disposition', 'review')
            result['recommendation'] = validation.get('recommendation', '')
            result['selected_candidate'] = validation['best_candidate']
            result['duration_validation_ms'] = (time.time() - start_time) * 1000
            result['duration_total_ms'] = (time.time() - pipeline_start_time) * 1000

            if validation['best_candidate'] != 'none':
                # Success!
                selected_num = int(validation['best_candidate'])
                result['summary'] = candidates[f'candidate_{selected_num}']
                result['processing_stage'] = 'validated'

                self._emit(f"✓ Validation complete", None, {
                    'event': 'claim_stage_update',
                    'doc_id': doc_id,
                    'claim_id': claim_id,
                    'claim_index': claim_index,  # NEW FIELD
                    'total_claims': total_claims,  # NEW FIELD
                    'claim_preview': claim_preview,  # NEW FIELD
                    'stage': 'validation',
                    'status': 'complete',
                    'data': {
                        'fidelity_scores': {
                            'score_1': result['score_1'],
                            'score_2': result['score_2'],
                            'score_3': result['score_3']
                        },
                        'best_candidate': selected_num,
                        'fidelity_reason': result['fidelity_reason'],
                        'quality_score': result['quality_score'],
                        'quality_reason': result['quality_reason'],
                        'disposition': result['disposition'],
                        'recommendation': result['recommendation'],
                        'duration_ms': result['duration_validation_ms']
                    }
                })

                # FINAL: Emit completion event
                self._emit(f"✓ Claim processing complete", None, {
                    'event': 'claim_complete',
                    'doc_id': doc_id,
                    'claim_id': claim_id,
                    'final_text': result['summary'],
                    'quality_score': result['quality_score'],
                    'disposition': result['disposition'],
                    'total_duration_ms': result['duration_total_ms']
                })

                logger.info(f"✓ Claim processed successfully (candidate {selected_num}, quality: {result['quality_score']:.2f}, disposition: {result['disposition']})")
                return result

            # No valid candidate found
            logger.error(f"No valid candidates found, using original")
            result['summary'] = claim_text[:50] + "..." if len(claim_text) > 50 else claim_text
            result['processing_stage'] = 'failed'
            return result

        except Exception as e:
            logger.error(f"Claim processing error: {e}", exc_info=True)
            result['summary'] = claim_text[:50] + "..." if len(claim_text) > 50 else claim_text
            result['processing_stage'] = 'error'
            result['duration_total_ms'] = (time.time() - pipeline_start_time) * 1000
            return result

    def _analyze_claim(self, claim_text: str) -> str:
        """
        STAGE 1: Deep analysis - verbose paragraph(s) fully understanding the claim.
        This can be 1-2 paragraphs expanding on all context and implications.
        """
        schema = {
            "type": "object",
            "properties": {
                "analysis": {"type": "string"}
            },
            "required": ["analysis"]
        }

        prompt = f"""Provide a deep analysis of this claim. Write 1-2 paragraphs that fully unpack:
- What is the claim actually saying?
- What are the implicit assumptions?
- What is evidence vs stated fact?
- What is correlation vs causation?
- What are the qualifiers and conditions?
- What context is needed to understand this properly?

ORIGINAL CLAIM:
"{claim_text}"

OUTPUT: 1-2 paragraphs of analysis (verbose is OK - we need full understanding)

EXAMPLE:
Original: "Mental illness derives its main support from syphilis of the brain"
Analysis: "This claim is stating that the concept or theory of mental illness as a disease entity derives its primary evidential support from the case of neurosyphilis (syphilis infection of the brain). The key word is 'support' - not that mental illness IS caused by brain disease, but that the THEORY of mental illness as brain disease gains its justification by pointing to neurosyphilis as an analogous case. In neurosyphilis, observable mental symptoms are caused by a known physical brain disease. Proponents use this as evidence that other mental illnesses must likewise have brain disease causes, even when no such disease can be identified. The claim is about epistemological support for a theory, not an assertion of causation."
"""

        result = self._invoke_agent_with_structured_output(prompt, schema, "analyze-claim")
        return result['analysis']

    def _clarify_claim(self, claim_text: str, analysis: str) -> str:
        """
        STAGE 2: Clarification - reword the original claim to be fully explicit.
        Should be similar length to original, just with implicit meaning made explicit.
        """
        schema = {
            "type": "object",
            "properties": {
                "clarified": {"type": "string"}
            },
            "required": ["clarified"]
        }

        prompt = f"""Reword this claim to make all implicit meaning EXPLICIT.
Should be roughly the SAME LENGTH as original - just clearer.
Do NOT add supporting sentences - just clarify the original phrasing.

ORIGINAL CLAIM:
"{claim_text}"

ANALYSIS (for context):
"{analysis}"

OUTPUT: The claim reworded with implicit meaning made explicit (similar length to original)

EXAMPLES:

Original: "Mental illness derives support from brain syphilis"
Clarified: "The theory of mental illness as brain disease derives evidential support from neurosyphilis as an analogous case"

Original: "This suggests users might improve"
Clarified: "The study's findings suggest some users might experience performance improvements"

Original: "It cannot be explained by defects"
Clarified: "A person's belief cannot be explained by nervous system defects or disease"
"""

        result = self._invoke_agent_with_structured_output(prompt, schema, "clarify-claim")
        return result['clarified']

    def _simplify_claim_candidates(self, clarified_text: str) -> dict:
        """
        STAGE 3: Generate 3 simplified candidates using SAME optimization goal.
        All 3 use identical prompt - they're just different attempts (random seeds).
        Goal: Find the mathematically optimal simplification.
        """
        schema = {
            "type": "object",
            "properties": {
                "candidate_1": {"type": "string"},
                "candidate_2": {"type": "string"},
                "candidate_3": {"type": "string"}
            },
            "required": ["candidate_1", "candidate_2", "candidate_3"]
        }

        prompt = f"""Simplify this clarified claim to its OPTIMAL shortest form.

CLARIFIED CLAIM:
"{clarified_text}"

GOAL: Mathematical optimization - find the absolute simplest way to state this while:
1. Preserving ALL qualifiers (may/might/can/must/some/all/possibly/likely/etc)
2. Preserving exact meaning from clarified version
3. Keeping causation vs correlation distinction
4. Keeping "supports/evidence" vs "causes/is" distinction
5. Removing ALL redundancy

Generate 3 independent attempts at this optimization (they should be similar but may differ slightly):

EXAMPLE:
Clarified: "The theory of mental illness as brain disease derives evidential support from neurosyphilis as an analogous case"
Optimal candidates (all attempting same goal):
- candidate_1: "Mental illness theory derives support from neurosyphilis analogy"
- candidate_2: "Brain disease theory gains evidential support from neurosyphilis case"
- candidate_3: "Mental illness concept supported by neurosyphilis as analogous example"
"""

        result = self._invoke_agent_with_structured_output(prompt, schema, "simplify-candidates")
        return result

    def _validate_final(self, original: str, analysis: str, clarified: str, candidates: dict) -> dict:
        """
        STAGE 4: Final validation - check candidates against ALL previous stages.
        Returns fidelity scores, quality score, and disposition.
        """
        schema = {
            "type": "object",
            "properties": {
                "score_1": {"type": "number"},
                "score_2": {"type": "number"},
                "score_3": {"type": "number"},
                "best_candidate": {"type": "string", "enum": ["1", "2", "3", "none"]},
                "fidelity_reason": {"type": "string"},
                "quality_score": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "quality_reason": {"type": "string"},
                "disposition": {"type": "string", "enum": ["central", "child", "review", "discard"]},
                "recommendation": {"type": "string"}
            },
            "required": ["score_1", "score_2", "score_3", "best_candidate", "fidelity_reason",
                        "quality_score", "quality_reason", "disposition", "recommendation"]
        }

        prompt = f"""Final validation: Check these simplified candidates against the full processing chain.

ORIGINAL SOURCE:
"{original}"

ANALYSIS (deep understanding):
"{analysis}"

CLARIFIED (explicit rewording):
"{clarified}"

SIMPLIFIED CANDIDATES:
1. "{candidates['candidate_1']}"
2. "{candidates['candidate_2']}"
3. "{candidates['candidate_3']}"

PART 1 - FIDELITY SCORING:
Score each candidate (0.0-1.0) on how well it preserves meaning:
- Preserves meaning from ANALYSIS? (0.3 points)
- Preserves meaning from CLARIFIED? (0.3 points)
- Preserves qualifiers from ORIGINAL? (0.2 points)
- No reversed meaning (evidence→cause, correlation→causation)? (0.15 points)
- Optimal simplification (no redundancy)? (0.05 points)

SELECT best_candidate (1/2/3) with highest score, OR "none" if ALL score < 0.7.
Provide fidelity_reason for selection.

PART 2 - QUALITY SCORING:
After selecting the best simplified version, evaluate the OVERALL CLAIM QUALITY (0.0-1.0):

HIGH QUALITY (0.7-1.0) - Disposition: "central"
- Makes a specific, testable assertion
- Contains meaningful qualifiers that add nuance (not just hedging)
- Provides actionable information worth investigating
- Should be a central/trunk node in knowledge graph

MEDIUM QUALITY (0.4-0.69) - Disposition: "child"
- Too vague or heavily hedged to be a central claim
- Derivative of more fundamental claims
- Should be attached as child to related superclaim
- Provides context but not primary focus

LOW QUALITY (0.0-0.39) - Disposition: "review" or "discard"
- Essentially meaningless (too many qualifiers, no substance)
- Circular reasoning or tautology
- Too vague to verify or investigate
- Flag for user review - likely not worth adding to database

Provide:
- quality_score: Overall claim quality (0.0-1.0)
- quality_reason: Why this score? Is claim specific and testable, or vague and meaningless?
- disposition: "central" / "child" / "review" / "discard"
- recommendation: What should be done with this claim in the knowledge graph?

EXAMPLE - LOW QUALITY CLAIM:
"The study suggests that some users who regularly utilize the system might experience improved performance metrics"
→ Quality: 0.35 (LOW)
→ Reason: "While simplification correctly preserves all qualifiers, the claim is too heavily hedged to provide meaningful information. It essentially says 'maybe something happens sometimes for some people under some conditions.' This provides no actionable research direction."
→ Disposition: "child"
→ Recommendation: "Attach as supporting detail to more specific claim about system effectiveness, or flag for review. Consider discarding if isolated."
"""

        result = self._invoke_agent_with_structured_output(prompt, schema, "validate-final")
        return result

    def _extract_document_title(self, text: str) -> str:
        """
        Extract the actual document title from the text.

        Uses AI agent to find the title in the first ~1000 characters.
        Falls back to "Untitled Document" if extraction fails.
        """
        expected_schema = {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "The document title"}
            },
            "required": ["title"]
        }

        agent_prompt = f"""Extract the document title from this text.

TEXT (first 1000 chars):
{text[:1000]}

Find the main title/heading at the top of the document. Return just the title text, no authors or metadata."""

        try:
            result = self._invoke_agent_with_structured_output(agent_prompt, expected_schema, "title-extraction")
            title = result.get('title', '').strip()

            if not title or len(title) < 3:
                raise RuntimeError("Title too short or empty")

            return title
        except Exception as e:
            logger.warning(f"Title extraction failed: {e}")
            return "Untitled Document"

    def _preprocess_text(self, text: str) -> str:
        """
        Clean and preprocess extracted text before sending to agent.

        Removes:
        - Copyright notices and legal boilerplate
        - ISBN numbers and publication metadata
        - Page headers/footers
        - Excessive whitespace and formatting artifacts

        Returns:
            Cleaned text suitable for claim extraction
        """
        import re

        logger.info("Preprocessing extracted text to remove metadata and artifacts...")

        # Split into lines for processing
        lines = text.split('\n')
        cleaned_lines = []

        # Patterns to identify metadata/boilerplate
        copyright_patterns = [
            r'(?i)copyright\s*©?\s*\d{4}',
            r'(?i)all rights reserved',
            r'(?i)no part of this.*may be reproduced',
            r'(?i)published (by|simultaneously)',
            r'ISBN\s*[\d-]+',
            r'(?i)printed in the',
            r'(?i)harper\s*&\s*row',
            r'(?i)perennial\s*library',
        ]

        # Page number patterns
        page_num_patterns = [
            r'^\s*\d+\s*$',  # Standalone page numbers
            r'^\s*[ivxlcdm]+\s*$',  # Roman numerals alone
        ]

        for line in lines:
            line = line.strip()

            # Skip empty lines
            if not line:
                continue

            # Skip copyright/metadata lines
            is_metadata = any(re.search(pattern, line) for pattern in copyright_patterns)
            if is_metadata:
                continue

            # Skip page numbers
            is_page_num = any(re.match(pattern, line) for pattern in page_num_patterns)
            if is_page_num:
                continue

            # Skip very short lines (likely artifacts) unless they end with punctuation
            if len(line) < 20 and not re.search(r'[.!?]$', line):
                continue

            cleaned_lines.append(line)

        # Rejoin into paragraphs (join lines until we hit a break)
        cleaned_text = ' '.join(cleaned_lines)

        # Remove null bytes (can break JSON parsing)
        if '\x00' in cleaned_text:
            logger.warning("Text contains null bytes - removing them")
            cleaned_text = cleaned_text.replace('\x00', '')

        # Normalize whitespace
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text)

        # Limit to first 50,000 characters (reasonable size for processing)
        if len(cleaned_text) > 50000:
            logger.info(f"Text too long ({len(cleaned_text)} chars), truncating to 50,000")
            cleaned_text = cleaned_text[:50000]

        logger.info(f"✓ Text preprocessed: {len(text)} → {len(cleaned_text)} chars")
        return cleaned_text

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
        doc_node = {
            'id': doc_id,
            'title': Path(file_path).name,
            'source_file': file_path,
            'status': 'processing'
        }

        self._emit("Creating document node...", 5, {
            'event': 'document_created',
            'doc_id': doc_id,
            'file_path': file_path,
            'node_data': doc_node  # Full node data for immediate rendering
        })

        # Use repository instead of direct DB call
        self.doc_repo.create_document(
            title=doc_node['title'],
            source_file=str(file_path),
            status='processing',
            **{k: v for k, v in doc_node.items() if k not in ['id', 'title', 'source_file', 'status', 'created_at']}
        )

        # 2. Extract text
        self._emit("Extracting text from PDF...", 10, {
            'event': 'text_extraction_started',
            'doc_id': doc_id
        })

        extractor = PDFExtractor(column_aware=True, postprocess=True)
        extraction_result = extractor.extract(Path(file_path))
        raw_text = extraction_result['full_text']

        self._emit(f"Extracted {len(raw_text)} characters", 15, {
            'event': 'text_extracted',
            'doc_id': doc_id,
            'char_count': len(raw_text)
        })

        # 2.1. Preprocess text to remove metadata and artifacts
        self._emit("Cleaning extracted text...", 18, {
            'event': 'text_preprocessing_started',
            'doc_id': doc_id
        })

        text = self._preprocess_text(raw_text)

        self._emit(f"Preprocessed {len(text)} characters", 20, {
            'event': 'text_preprocessed',
            'doc_id': doc_id,
            'char_count': len(text)
        })

        # 2.5. Extract actual document title
        self._emit("Extracting document title...", 25, {
            'event': 'title_extraction_started',
            'doc_id': doc_id
        })

        try:
            actual_title = self._extract_document_title(text)
            logger.info(f"✓ Extracted document title: {actual_title}")
        except Exception as e:
            logger.warning(f"Failed to extract document title: {e}")
            actual_title = Path(file_path).stem  # Fallback to filename

        # Update document node with actual title using repository
        self.doc_repo.update_document(doc_id, {'title': actual_title})

        self._emit(f"Document title: {actual_title}", 28, {
            'event': 'title_extracted',
            'doc_id': doc_id,
            'title': actual_title,
            'node_update': {  # FIX: Tell frontend to update the document node label
                'node_id': doc_id,
                'node_type': 'document',
                'updates': {'title': actual_title}
            }
        })

        # 3. Extract claims with AI (FLAT structure for MVP - clustering happens later via community detection)
        self._emit("Extracting claims with AI...", 30, {
            'event': 'claim_extraction_started',
            'doc_id': doc_id
        })

        try:
            # Extract flat list of claims (no hierarchy/clustering yet)
            claims_list = self._extract_flat_claims_with_agent(text)
            logger.info(f"✓ Extracted {len(claims_list)} claims (flat structure)")
        except Exception as e:
            error_msg = f"Claude Code agent failed to extract claims: {str(e)}"
            logger.error(error_msg)
            self._emit(f"ERROR: {error_msg}", 30, {
                'event': 'claim_extraction_failed',
                'doc_id': doc_id,
                'error': str(e)
            })
            # Mark document as failed using repository
            self.doc_repo.mark_document_failed(doc_id, error_msg)
            raise

        total_claims = len(claims_list)

        # Build claim previews for progress tracking UI
        claim_previews = []
        for claim_text in claims_list:
            preview = claim_text[:50] + '...' if len(claim_text) > 50 else claim_text
            claim_previews.append({
                'id': None,  # Will be set when claim is created
                'preview': preview
            })

        self._emit(f"Extracted {total_claims} claims", 50, {
            'event': 'claims_extracted',
            'doc_id': doc_id,
            'total_claims': total_claims,
            'claim_previews': claim_previews
        })

        # 4. Create skeleton claim nodes IMMEDIATELY for real-time visualization
        logger.info(f"Creating {total_claims} skeleton claim nodes for immediate rendering...")

        claim_ids = []  # Store IDs for processing loop

        for idx, claim_dict in enumerate(claims_list):
            claim_id = str(uuid4())
            claim_ids.append(claim_id)

            # Extract text from claim dictionary
            claim_text = claim_dict.get('text', str(claim_dict))  # Fallback to string representation if no 'text' key

            # Create minimal "skeleton" node with raw claim text using repository
            # Note: create_claim automatically creates the CONTAINS_CLAIM relationship
            created_claim_id = self.claim_repo.create_claim(
                text=claim_text,  # Raw text (will be updated with summary later)
                original_text=claim_text,
                doc_id=doc_id,
                claim_type=claim_dict.get('type', 'extracted'),  # Preserve type from extraction
                confidence=claim_dict.get('confidence', 0.0),  # Preserve initial confidence
                status='processing',
                processing_stage='pending',
                word_count_original=len(claim_text.split())
            )

            # Skeleton node data for event emission (reconstructed for backward compatibility)
            skeleton_node = {
                'id': claim_id,
                'text': claim_text,
                'original_text': claim_text,
                'status': 'processing',
                'processing_stage': 'pending',
                'claim_type': claim_dict.get('type', 'extracted'),
                'confidence': claim_dict.get('confidence', 0.0),
                'word_count_original': len(claim_text.split())
            }

            # Emit IMMEDIATELY so user sees claim appear in graph
            progress = 35 + (idx / total_claims) * 15  # 35% to 50%
            self._emit(f"Extracted claim {idx+1}/{total_claims}", progress, {
                'event': 'claim_added',
                'doc_id': doc_id,
                'claim_id': claim_id,
                'node_data': skeleton_node,
                'parent_id': doc_id,
                'is_skeleton': True  # Flag for frontend to render with "processing" appearance
            })

        logger.info(f"✓ Created {total_claims} skeleton nodes - user can see claims now!")

        # 5. Now process each claim through 4-stage pipeline and UPDATE existing nodes
        logger.info(f"Processing {total_claims} claims through 4-stage pipeline...")

        for idx, (claim_id, claim_dict) in enumerate(zip(claim_ids, claims_list)):
            progress = 50 + ((idx + 1) / total_claims) * 40  # 50% to 90%

            # Extract text from claim dictionary
            claim_text = claim_dict.get('text', str(claim_dict))

            logger.info(f"Processing claim {idx + 1}/{total_claims}: {claim_text[:60]}...")

            # Emit processing started event for this specific claim
            self._emit(f"Processing claim {idx+1}/{total_claims}", progress, {
                'event': 'claim_processing_started',
                'claim_id': claim_id,
                'doc_id': doc_id,
                'processing_stage': 'analysis'
            })

            # Process claim through 4-stage pipeline (analyze → clarify → simplify → validate)
            simplification_result = self._simplify_claim_with_agent(
                claim_text,
                claim_id=claim_id,
                doc_id=doc_id,
                claim_index=idx + 1,  # 1-based for UI display
                total_claims=total_claims
            )

            # UPDATE existing skeleton node with all processed data
            processed_data = {
                # Display text (what user sees in graph) - UPDATED from raw text
                'text': simplification_result['summary'],
                'summary': simplification_result['summary'],

                # Status - mark as complete
                'status': 'complete',
                'processing_stage': 'complete',

                # Complete processing chain (for details view)
                'analysis': simplification_result['analysis'],
                'clarified': simplification_result['clarified'],

                # All 3 candidates
                'candidate_1': simplification_result['candidate_1'],
                'candidate_2': simplification_result['candidate_2'],
                'candidate_3': simplification_result['candidate_3'],

                # Fidelity scores (how well candidates preserve meaning)
                'score_1': simplification_result['score_1'],
                'score_2': simplification_result['score_2'],
                'score_3': simplification_result['score_3'],
                'fidelity_reason': simplification_result['fidelity_reason'],
                'selected_candidate': simplification_result['selected_candidate'],

                # Quality assessment (overall claim value)
                'quality_score': simplification_result['quality_score'],
                'quality_reason': simplification_result['quality_reason'],
                'disposition': simplification_result['disposition'],  # central/child/review/discard
                'recommendation': simplification_result['recommendation'],

                # Timing data (milliseconds)
                'duration_analysis_ms': simplification_result['duration_analysis_ms'],
                'duration_clarification_ms': simplification_result['duration_clarification_ms'],
                'duration_simplification_ms': simplification_result['duration_simplification_ms'],
                'duration_validation_ms': simplification_result['duration_validation_ms'],
                'duration_total_ms': simplification_result['duration_total_ms'],

                # Word counts (for analytics)
                'word_count_final': len(simplification_result['summary'].split()),

                # Metadata - MVP flat structure (no super-claims yet)
                'claim_type': 'extracted',  # Will be refined by community detection later
                'confidence': simplification_result['quality_score'],  # Use quality as confidence
                'is_optimal': True  # Will be updated by optimizer later
            }

            # UPDATE Neo4j node using repository (not create - node already exists from skeleton)
            self.claim_repo.update_claim(claim_id, processed_data)
            logger.info(f"✓ Updated claim node with processed data: {claim_id}")

            # Emit claim_updated event for frontend to update appearance
            self._emit(f"Processed claim {idx+1}/{total_claims}", progress, {
                'event': 'claim_updated',
                'doc_id': doc_id,
                'claim_id': claim_id,
                'updates': processed_data  # Send updated fields for frontend to apply
            })
            logger.info(f"✓ Emitted claim_updated event")

        # 5. Skip optimization for now (too slow for web interface)
        self._emit("Skipping claim hierarchy analysis (can run later)", 90, {
            'event': 'optimization_skipped',
            'doc_id': doc_id
        })

        # TODO: Run optimization in background or on-demand
        # optimizer = ClaimSpaceOptimizer()
        # optimizer.optimize_claim_space(self.db)

        # 6. Mark document as complete using repository
        self.doc_repo.mark_document_complete(doc_id)

        self._emit("Document processing complete!", 100, {
            'event': 'processing_complete',
            'doc_id': doc_id
        })

        return doc_id
