"""
Claim Contradiction Detection Module.

Automatically detects contradicting claims in the graph using AI analysis.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json

from .base_nlp import BaseNLPProcessor

logger = logging.getLogger(__name__)


class ContradictionType(Enum):
    """Types of contradictions."""
    DIRECT = "direct"  # Directly opposing claims
    IMPLICIT = "implicit"  # Implicit contradiction
    SEMANTIC = "semantic"  # Semantic contradiction
    NONE = "none"  # No contradiction


@dataclass
class ContradictionResult:
    """Result of contradiction detection."""
    claim1_id: str
    claim2_id: str
    claim1_text: str
    claim2_text: str
    is_contradiction: bool
    contradiction_type: ContradictionType
    confidence: float  # 0-100%
    explanation: str
    keywords: List[str]


class ContradictionDetector(BaseNLPProcessor):
    """
    Detects contradicting claims in the knowledge graph.

    Uses AI to analyze claim pairs for contradictions.
    """

    def __init__(self, **kwargs):
        """Initialize contradiction detector."""
        super().__init__(**kwargs)
        self.similarity_threshold = 0.15  # Minimum similarity to consider

    async def detect_contradiction(
        self,
        claim1: Dict[str, Any],
        claim2: Dict[str, Any]
    ) -> ContradictionResult:
        """
        Detect if two claims contradict each other.

        Args:
            claim1: First claim dict with 'id' and 'text'
            claim2: Second claim dict with 'id' and 'text'

        Returns:
            ContradictionResult object
        """
        claim1_id = claim1.get('id', 'unknown')
        claim2_id = claim2.get('id', 'unknown')
        claim1_text = claim1.get('text', claim1.get('original_text', ''))
        claim2_text = claim2.get('text', claim2.get('original_text', ''))

        # Check textual similarity first
        similarity = self.calculate_text_similarity(claim1_text, claim2_text)

        # If too dissimilar, skip AI analysis
        if similarity < self.similarity_threshold:
            return ContradictionResult(
                claim1_id=claim1_id,
                claim2_id=claim2_id,
                claim1_text=claim1_text,
                claim2_text=claim2_text,
                is_contradiction=False,
                contradiction_type=ContradictionType.NONE,
                confidence=0.0,
                explanation="Claims are too dissimilar to contradict.",
                keywords=[]
            )

        # Use AI to analyze contradiction
        prompt = f"""Analyze these two claims for contradiction:

Claim 1: "{claim1_text}"
Claim 2: "{claim2_text}"

Determine if these claims contradict each other. Consider:
1. Direct contradictions (opposite statements)
2. Implicit contradictions (logically incompatible)
3. Semantic contradictions (different meanings that conflict)

Analyze carefully and respond with your assessment."""

        schema = {
            "is_contradiction": "boolean - true if claims contradict",
            "contradiction_type": "string - one of: direct, implicit, semantic, none",
            "confidence": "number - confidence score from 0-100",
            "explanation": "string - brief explanation of the contradiction or lack thereof",
            "keywords": "array of strings - key terms involved in the contradiction"
        }

        try:
            result = await self.analyze_with_schema(prompt, schema, temperature=0.2)

            contradiction_type = ContradictionType.NONE
            type_str = result.get('contradiction_type', 'none').lower()
            for ct in ContradictionType:
                if ct.value == type_str:
                    contradiction_type = ct
                    break

            return ContradictionResult(
                claim1_id=claim1_id,
                claim2_id=claim2_id,
                claim1_text=claim1_text,
                claim2_text=claim2_text,
                is_contradiction=result.get('is_contradiction', False),
                contradiction_type=contradiction_type,
                confidence=float(result.get('confidence', 0.0)),
                explanation=result.get('explanation', ''),
                keywords=result.get('keywords', [])
            )

        except Exception as e:
            logger.error(f"Contradiction detection failed: {e}")
            # Return non-contradiction on error
            return ContradictionResult(
                claim1_id=claim1_id,
                claim2_id=claim2_id,
                claim1_text=claim1_text,
                claim2_text=claim2_text,
                is_contradiction=False,
                contradiction_type=ContradictionType.NONE,
                confidence=0.0,
                explanation=f"Analysis failed: {str(e)}",
                keywords=[]
            )

    async def detect_contradictions_batch(
        self,
        claims: List[Dict[str, Any]],
        min_confidence: float = 70.0
    ) -> List[ContradictionResult]:
        """
        Detect contradictions among a batch of claims.

        Args:
            claims: List of claim dicts
            min_confidence: Minimum confidence to include (0-100)

        Returns:
            List of contradiction results above confidence threshold
        """
        contradictions = []

        # Pairwise comparison
        for i in range(len(claims)):
            for j in range(i + 1, len(claims)):
                result = await self.detect_contradiction(claims[i], claims[j])

                if result.is_contradiction and result.confidence >= min_confidence:
                    contradictions.append(result)
                    logger.info(
                        f"Found contradiction: {result.contradiction_type.value} "
                        f"(confidence: {result.confidence:.1f}%)"
                    )

        return contradictions

    async def create_contradiction_relationships(
        self,
        graph_db,
        contradictions: List[ContradictionResult]
    ) -> int:
        """
        Create CONTRADICTS relationships in the graph database.

        Args:
            graph_db: GraphDatabase instance
            contradictions: List of contradiction results

        Returns:
            Number of relationships created
        """
        count = 0

        for contradiction in contradictions:
            # Create bidirectional CONTRADICTS relationship
            graph_db.create_relationship(
                from_node=contradiction.claim1_id,
                to_node=contradiction.claim2_id,
                rel_type='CONTRADICTS',
                properties={
                    'contradiction_type': contradiction.contradiction_type.value,
                    'confidence': contradiction.confidence,
                    'explanation': contradiction.explanation,
                    'keywords': json.dumps(contradiction.keywords)
                }
            )

            # Add reverse relationship
            graph_db.create_relationship(
                from_node=contradiction.claim2_id,
                to_node=contradiction.claim1_id,
                rel_type='CONTRADICTS',
                properties={
                    'contradiction_type': contradiction.contradiction_type.value,
                    'confidence': contradiction.confidence,
                    'explanation': contradiction.explanation,
                    'keywords': json.dumps(contradiction.keywords)
                }
            )

            count += 2

        logger.info(f"Created {count} CONTRADICTS relationships")
        return count

    def get_contradictions_for_claim(
        self,
        graph_db,
        claim_id: str,
        min_confidence: float = 70.0
    ) -> List[Dict[str, Any]]:
        """
        Get all contradictions for a specific claim.

        Args:
            graph_db: GraphDatabase instance
            claim_id: Claim ID to check
            min_confidence: Minimum confidence threshold

        Returns:
            List of contradicting claims with metadata
        """
        contradictions = []

        # Get CONTRADICTS relationships
        relationships = graph_db.get_relationships(claim_id, 'CONTRADICTS', 'both')

        for target_id, rel_data in relationships:
            confidence = rel_data.get('confidence', 0.0)

            if confidence >= min_confidence:
                target_claim = graph_db.get_node(target_id)
                contradictions.append({
                    'claim_id': target_id,
                    'claim_text': target_claim.get('text', ''),
                    'contradiction_type': rel_data.get('contradiction_type', 'unknown'),
                    'confidence': confidence,
                    'explanation': rel_data.get('explanation', ''),
                    'keywords': json.loads(rel_data.get('keywords', '[]'))
                })

        return sorted(contradictions, key=lambda x: x['confidence'], reverse=True)
