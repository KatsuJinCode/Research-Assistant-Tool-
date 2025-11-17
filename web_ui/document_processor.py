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

    def _extract_claims_with_agent(self, text: str) -> List[Dict[str, Any]]:
        """
        Use Claude Code agent to extract claims from text.

        Returns list of claims with 'text', 'type', 'confidence' fields.
        """
        prompt = f"""Extract all factual claims from this research document text.

For each claim, provide:
1. The exact claim text (quote it precisely)
2. The type of claim (factual, methodological, causal, interpretive, etc.)
3. Your confidence in the extraction (0.0-1.0)

Return ONLY a valid JSON array of claim objects with this structure:
[
  {{"text": "exact claim text", "type": "factual", "confidence": 0.95}},
  ...
]

Document text:
{text[:8000]}

Return the JSON array:"""

        try:
            # This would be where we invoke a Claude Code agent
            # For now, use a simple sentence-based extraction as fallback
            logger.warning("Claude Code agent integration pending - using fallback extraction")
            return self._fallback_claim_extraction(text)
        except Exception as e:
            logger.error(f"Agent extraction failed: {e}")
            return self._fallback_claim_extraction(text)

    def _simplify_claim_with_agent(self, claim_text: str) -> Dict[str, str]:
        """
        Use Claude Code agent to simplify and normalize a claim.

        Returns dict with 'simplified', 'normalized' versions.
        """
        prompt = f"""Simplify this research claim while preserving all qualifiers and meaning:

Original claim: "{claim_text}"

Provide:
1. simplified: A concise 5-10 word version
2. normalized: A medium 15-20 word version

Return ONLY valid JSON:
{{"simplified": "...", "normalized": "..."}}"""

        try:
            # This would invoke a Claude Code agent
            logger.warning("Claude Code agent integration pending - using rule-based simplification")
            # For now, use the existing simplifier
            from research_agent.claim_analysis.claim_simplifier_agent import ClaimSimplifierAgent
            simplifier = ClaimSimplifierAgent()
            return simplifier.simplify_claim(claim_text)
        except Exception as e:
            logger.error(f"Agent simplification failed: {e}")
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

        # 5. Optimize claim space (find hierarchies)
        self._emit("Analyzing claim relationships...", 80, {
            'event': 'optimization_started',
            'doc_id': doc_id
        })

        optimizer = ClaimSpaceOptimizer()
        optimizer.optimize_claim_space(self.db)

        self._emit("Optimization complete", 90, {
            'event': 'optimization_complete',
            'doc_id': doc_id
        })

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
