"""
Real-time Document Processor with Live Updates

Processes documents incrementally, sending updates to clients via callback.
Uses Claude Code CLI agents for intelligent extraction and analysis.
"""

import logging
import json
import subprocess
from pathlib import Path
from typing import Callable, Dict, Any, List
from uuid import uuid4

from research_agent.document_processing.pdf_extractor import PDFExtractor
from research_agent.claim_analysis.claim_space_optimizer import ClaimSpaceOptimizer
from research_agent.neo4j_database import Neo4jDatabase

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

    def _invoke_agent(self, prompt: str, task_type: str) -> str:
        """
        Invoke Claude Code CLI agent to perform a task.

        Args:
            prompt: The task prompt for the agent
            task_type: Type of task (for logging)

        Returns:
            Agent's response as string
        """
        logger.info(f"Spawning Claude Code agent for {task_type}")

        try:
            # Create a prompt file
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
                f.write(prompt)
                prompt_file = f.name

            # Invoke Claude Code CLI
            # This runs: claude --prompt-file <file> --output-only
            result = subprocess.run(
                ['claude', '--prompt-file', prompt_file, '--output-only'],
                capture_output=True,
                text=True,
                timeout=120,  # 2 minute timeout
                encoding='utf-8'
            )

            # Clean up prompt file
            try:
                Path(prompt_file).unlink()
            except:
                pass

            if result.returncode != 0:
                logger.error(f"Agent failed with code {result.returncode}: {result.stderr}")
                raise RuntimeError(f"Agent process failed: {result.stderr}")

            response = result.stdout.strip()
            logger.info(f"Agent completed {task_type}")

            return response

        except subprocess.TimeoutExpired:
            logger.error(f"Agent timeout for {task_type}")
            raise RuntimeError("Agent timed out")
        except FileNotFoundError:
            logger.error("Claude Code CLI not found - is it installed?")
            raise RuntimeError("Claude Code CLI not available")
        except Exception as e:
            logger.error(f"Agent invocation failed: {e}")
            raise

    def _extract_claims_with_agent(self, text: str) -> List[Dict[str, Any]]:
        """
        Use Claude Code agent to extract claims from text.

        Returns list of claims with 'text', 'type', 'confidence' fields.
        """
        # Write text to temporary file for agent to process
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(text[:8000])  # Limit to 8000 chars
            temp_file = f.name

        try:
            # Spawn Claude Code agent to extract claims
            agent_prompt = f"""Extract all factual claims from the research document at: {temp_file}

Read the file, then extract claims. For each claim:
1. Extract the exact claim text (quote it precisely)
2. Classify the type (factual, methodological, causal, interpretive, etc.)
3. Assess extraction confidence (0.0-1.0)

Return ONLY a valid JSON array with this exact structure:
[
  {{"text": "exact claim text", "type": "factual", "confidence": 0.95}},
  ...
]

Important:
- Extract 10-30 claims maximum
- Be precise and preserve qualifiers (may, might, can, all, some, etc.)
- Return ONLY the JSON array, nothing else"""

            result = self._invoke_agent(agent_prompt, "claim-extraction")

            # Parse JSON response
            claims = json.loads(result)

            if not isinstance(claims, list):
                logger.error(f"Agent returned non-list: {type(claims)}")
                return self._fallback_claim_extraction(text)

            logger.info(f"Agent extracted {len(claims)} claims")
            return claims

        except Exception as e:
            logger.error(f"Agent extraction failed: {e}")
            return self._fallback_claim_extraction(text)
        finally:
            # Clean up temp file
            try:
                Path(temp_file).unlink()
            except:
                pass

    def _simplify_claim_with_agent(self, claim_text: str) -> Dict[str, str]:
        """
        Use Claude Code agent to simplify and normalize a claim.

        Returns dict with 'simplified', 'normalized' versions.
        """
        agent_prompt = f"""Simplify this research claim while preserving all qualifiers and meaning:

Original claim: "{claim_text}"

Provide:
1. simplified: A concise 5-10 word version that captures the core assertion
2. normalized: A medium 15-20 word version with key details

Return ONLY valid JSON with this exact structure:
{{"simplified": "...", "normalized": "..."}}

Important: Preserve qualifiers like may, might, can, could, all, some, etc."""

        try:
            result = self._invoke_agent(agent_prompt, "claim-simplification")

            # Parse JSON response
            simplification = json.loads(result)

            if 'simplified' not in simplification or 'normalized' not in simplification:
                logger.error(f"Agent returned incomplete response: {simplification}")
                return self._fallback_simplification(claim_text)

            return simplification

        except Exception as e:
            logger.error(f"Agent simplification failed: {e}")
            return self._fallback_simplification(claim_text)

    def _fallback_simplification(self, claim_text: str) -> Dict[str, str]:
        """Fallback simplification using rule-based agent."""
        try:
            from research_agent.claim_analysis.claim_simplifier_agent import ClaimSimplifierAgent
            simplifier = ClaimSimplifierAgent()
            return simplifier.simplify_claim(claim_text)
        except Exception as e:
            logger.error(f"Fallback simplification failed: {e}")
            return {'simplified': claim_text[:50], 'normalized': claim_text[:100]}

    def _fallback_claim_extraction(self, text: str) -> List[Dict[str, Any]]:
        """Simple fallback: extract claims as sentences."""
        import re
        sentences = re.split(r'[.!?]+\s+', text)
        claims = []
        for sent in sentences[:20]:  # Limit to 20 claims for now
            if len(sent.strip()) > 20:
                claims.append({
                    'text': sent.strip(),
                    'type': 'factual',
                    'confidence': 0.7
                })
        return claims

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

        claims = self._extract_claims_with_agent(text)

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
            simplification = self._simplify_claim_with_agent(claim_data['text'])

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
