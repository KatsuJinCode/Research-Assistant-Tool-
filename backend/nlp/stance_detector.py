"""
Stance Detection Module.

Determines author stance toward claims (support, oppose, neutral, unclear).
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json

from .base_nlp import BaseNLPProcessor

logger = logging.getLogger(__name__)


class Stance(Enum):
    """Author stance types."""
    SUPPORT = "support"  # Author supports the claim
    OPPOSE = "oppose"  # Author opposes the claim
    NEUTRAL = "neutral"  # Author is neutral
    UNCLEAR = "unclear"  # Stance is unclear


@dataclass
class StanceResult:
    """Result of stance detection."""
    claim_id: str
    claim_text: str
    doc_id: str
    doc_title: Optional[str]
    stance: Stance
    confidence: float  # 0-100
    supporting_quotes: List[str]
    explanation: str
    sentiment_score: Optional[float] = None  # -1 to 1 (negative to positive)


@dataclass
class StanceShift:
    """Represents a shift in stance across documents."""
    claim_id: str
    claim_text: str
    from_doc_id: str
    to_doc_id: str
    from_stance: Stance
    to_stance: Stance
    shift_magnitude: float
    explanation: str


class StanceDetector(BaseNLPProcessor):
    """
    Detects author stance toward claims.

    Analyzes text to determine if author supports, opposes, or is neutral
    toward specific claims.
    """

    def __init__(self, **kwargs):
        """Initialize stance detector."""
        super().__init__(**kwargs)

    async def detect_stance(
        self,
        claim: Dict[str, Any],
        document: Dict[str, Any],
        context: Optional[str] = None
    ) -> StanceResult:
        """
        Detect author stance toward a claim in a document.

        Args:
            claim: Claim dict with 'id' and 'text'
            document: Document dict with 'id', 'title', and 'content'
            context: Optional context text around the claim

        Returns:
            StanceResult object
        """
        claim_id = claim.get('id', 'unknown')
        claim_text = claim.get('text', claim.get('original_text', ''))
        doc_id = document.get('id', 'unknown')
        doc_title = document.get('title', 'Untitled')
        doc_content = document.get('content', '')

        # If context not provided, use full document (chunked if needed)
        if context is None:
            context = doc_content[:2000]  # Use first 2000 chars

        # Use AI to detect stance
        prompt = f"""Analyze the author's stance toward this claim in the given text:

Claim: "{claim_text}"

Text context:
{context}

Determine:
1. The author's stance: support, oppose, neutral, or unclear
2. Confidence level (0-100)
3. Supporting quotes from the text that indicate the stance
4. Brief explanation of the stance

Consider the language, tone, and arguments used by the author."""

        schema = {
            "stance": "string - support, oppose, neutral, or unclear",
            "confidence": "number - 0-100",
            "supporting_quotes": ["array of strings - relevant quotes from text"],
            "explanation": "string - brief explanation of the stance",
            "sentiment_score": "number - -1.0 to 1.0 (negative to positive)"
        }

        try:
            result = await self.analyze_with_schema(prompt, schema, temperature=0.3)

            # Parse stance
            stance_str = result.get('stance', 'unclear').lower()
            stance = Stance.UNCLEAR
            for s in Stance:
                if s.value == stance_str:
                    stance = s
                    break

            return StanceResult(
                claim_id=claim_id,
                claim_text=claim_text,
                doc_id=doc_id,
                doc_title=doc_title,
                stance=stance,
                confidence=float(result.get('confidence', 0.0)),
                supporting_quotes=result.get('supporting_quotes', []),
                explanation=result.get('explanation', ''),
                sentiment_score=float(result.get('sentiment_score', 0.0))
            )

        except Exception as e:
            logger.error(f"Stance detection failed: {e}")
            # Return unclear stance on error
            return StanceResult(
                claim_id=claim_id,
                claim_text=claim_text,
                doc_id=doc_id,
                doc_title=doc_title,
                stance=Stance.UNCLEAR,
                confidence=0.0,
                supporting_quotes=[],
                explanation=f"Analysis failed: {str(e)}",
                sentiment_score=None
            )

    async def detect_stances_batch(
        self,
        claim: Dict[str, Any],
        documents: List[Dict[str, Any]]
    ) -> List[StanceResult]:
        """
        Detect stances for a claim across multiple documents.

        Args:
            claim: Claim dict
            documents: List of document dicts

        Returns:
            List of stance results
        """
        results = []

        for doc in documents:
            result = await self.detect_stance(claim, doc)
            results.append(result)
            logger.info(
                f"Stance in '{doc.get('title', 'Unknown')}': "
                f"{result.stance.value} (confidence: {result.confidence:.1f}%)"
            )

        return results

    async def detect_stance_shifts(
        self,
        claim: Dict[str, Any],
        documents: List[Dict[str, Any]]
    ) -> List[StanceShift]:
        """
        Detect shifts in stance across documents.

        Args:
            claim: Claim dict
            documents: List of document dicts (should be ordered chronologically)

        Returns:
            List of detected stance shifts
        """
        # First detect all stances
        stances = await self.detect_stances_batch(claim, documents)

        shifts = []

        # Look for shifts between consecutive documents
        for i in range(len(stances) - 1):
            current = stances[i]
            next_stance = stances[i + 1]

            # Check if stance changed
            if current.stance != next_stance.stance:
                # Calculate shift magnitude
                stance_values = {
                    Stance.OPPOSE: -1.0,
                    Stance.NEUTRAL: 0.0,
                    Stance.SUPPORT: 1.0,
                    Stance.UNCLEAR: 0.0
                }

                magnitude = abs(
                    stance_values.get(next_stance.stance, 0.0) -
                    stance_values.get(current.stance, 0.0)
                )

                shifts.append(StanceShift(
                    claim_id=current.claim_id,
                    claim_text=current.claim_text,
                    from_doc_id=current.doc_id,
                    to_doc_id=next_stance.doc_id,
                    from_stance=current.stance,
                    to_stance=next_stance.stance,
                    shift_magnitude=magnitude,
                    explanation=f"Stance shifted from {current.stance.value} "
                               f"to {next_stance.stance.value}"
                ))

        logger.info(f"Detected {len(shifts)} stance shifts")
        return shifts

    def add_stance_to_graph(
        self,
        graph_db,
        stance_results: List[StanceResult]
    ) -> int:
        """
        Add stance information to graph nodes.

        Args:
            graph_db: GraphDatabase instance
            stance_results: List of stance results

        Returns:
            Number of nodes updated
        """
        count = 0

        for result in stance_results:
            # Get the claim node
            claim_node = graph_db.get_node(result.claim_id)

            if claim_node:
                # Add or update stance property
                claim_node['stance'] = result.stance.value
                claim_node['stance_confidence'] = result.confidence
                claim_node['stance_explanation'] = result.explanation
                count += 1

            # Create relationship between document and claim with stance info
            graph_db.create_relationship(
                from_node=result.doc_id,
                to_node=result.claim_id,
                rel_type='HAS_STANCE',
                properties={
                    'stance': result.stance.value,
                    'confidence': result.confidence,
                    'supporting_quotes': json.dumps(result.supporting_quotes),
                    'explanation': result.explanation,
                    'sentiment_score': result.sentiment_score
                }
            )

        logger.info(f"Added stance info to {count} claim nodes")
        return count

    def get_stance_distribution(
        self,
        stance_results: List[StanceResult]
    ) -> Dict[str, Any]:
        """
        Get distribution of stances.

        Args:
            stance_results: List of stance results

        Returns:
            Dict with stance distribution stats
        """
        distribution = {
            'support': 0,
            'oppose': 0,
            'neutral': 0,
            'unclear': 0
        }

        total_confidence = 0.0

        for result in stance_results:
            distribution[result.stance.value] += 1
            total_confidence += result.confidence

        avg_confidence = total_confidence / len(stance_results) if stance_results else 0.0

        return {
            'distribution': distribution,
            'total_documents': len(stance_results),
            'average_confidence': avg_confidence,
            'support_percentage': (distribution['support'] / len(stance_results) * 100)
                                 if stance_results else 0.0,
            'oppose_percentage': (distribution['oppose'] / len(stance_results) * 100)
                                if stance_results else 0.0,
            'neutral_percentage': (distribution['neutral'] / len(stance_results) * 100)
                                 if stance_results else 0.0,
            'unclear_percentage': (distribution['unclear'] / len(stance_results) * 100)
                                 if stance_results else 0.0
        }

    async def visualize_stance_timeline(
        self,
        claim: Dict[str, Any],
        documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Create timeline visualization data for stance changes.

        Args:
            claim: Claim dict
            documents: Chronologically ordered document dicts

        Returns:
            Visualization data dict
        """
        stances = await self.detect_stances_batch(claim, documents)

        timeline = []
        for stance_result in stances:
            timeline.append({
                'doc_id': stance_result.doc_id,
                'doc_title': stance_result.doc_title,
                'stance': stance_result.stance.value,
                'confidence': stance_result.confidence,
                'sentiment': stance_result.sentiment_score
            })

        return {
            'claim_id': claim.get('id'),
            'claim_text': claim.get('text'),
            'timeline': timeline,
            'distribution': self.get_stance_distribution(stances)
        }
