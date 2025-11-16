"""
Confidence score calculations.

Provides confidence scoring at multiple levels:
- Normalization confidence
- Finding confidence
- Overall claim confidence
"""

import logging
from typing import List, Dict, Any
from research_agent.database import Database


logger = logging.getLogger(__name__)


class ConfidenceCalculator:
    """Calculate confidence scores for claims and findings."""

    def __init__(self, db: Database):
        """
        Initialize confidence calculator.

        Args:
            db: Database instance
        """
        self.db = db

    async def calculate_claim_confidence(self, claim_id) -> float:
        """
        Calculate overall confidence for a claim based on all evidence.

        Uses database function for calculation.

        Args:
            claim_id: Claim ID

        Returns:
            Confidence score (0.0-1.0)
        """
        return await self.db.update_claim_confidence(claim_id)

    def calculate_finding_confidence(
        self,
        evidence_list: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate confidence for a finding based on evidence quality.

        Args:
            evidence_list: List of evidence dicts

        Returns:
            Confidence score (0.0-1.0)
        """
        if not evidence_list:
            return 0.0

        total = 0.0
        for evidence in evidence_list:
            relevance = evidence.get('relevance_score', 0.5)
            credibility = evidence.get('credibility_score', 0.5)
            # Average relevance and credibility
            total += (relevance + credibility) / 2

        confidence = total / len(evidence_list)
        return round(confidence, 2)

    def get_confidence_label(self, confidence: float) -> str:
        """
        Get confidence label.

        Args:
            confidence: Confidence score

        Returns:
            Label string
        """
        if confidence >= 0.85:
            return "HIGH"
        elif confidence >= 0.60:
            return "MEDIUM"
        else:
            return "LOW"

    def get_confidence_stars(self, confidence: float) -> str:
        """
        Get visual confidence indicator.

        Args:
            confidence: Confidence score

        Returns:
            Star rating string
        """
        stars = int(confidence * 5)
        return "⭐" * stars + "☆" * (5 - stars)

    def should_trigger_additional_investigation(
        self,
        confidence: float,
        threshold: float = 0.60
    ) -> bool:
        """
        Check if low confidence should trigger more investigation.

        Args:
            confidence: Confidence score
            threshold: Low confidence threshold

        Returns:
            True if more investigation needed
        """
        return confidence < threshold

    async def get_claim_confidence_breakdown(
        self,
        claim_id
    ) -> Dict[str, Any]:
        """
        Get detailed confidence breakdown for a claim.

        Args:
            claim_id: Claim ID

        Returns:
            Dict with confidence details
        """
        # Get all findings
        findings = await self.db.get_findings_for_claim(claim_id)

        # Calculate per-finding-type confidence
        support_findings = [f for f in findings if f['finding_type'] == 'support']
        challenge_findings = [f for f in findings if f['finding_type'] == 'challenge']
        neutral_findings = [
            f for f in findings
            if f['finding_type'] in ['neutral', 'clarification']
        ]

        support_confidence = (
            sum(f['confidence'] or 0 for f in support_findings) / len(support_findings)
            if support_findings else 0.0
        )

        challenge_confidence = (
            sum(f['confidence'] or 0 for f in challenge_findings) / len(challenge_findings)
            if challenge_findings else 0.0
        )

        neutral_confidence = (
            sum(f['confidence'] or 0 for f in neutral_findings) / len(neutral_findings)
            if neutral_findings else 0.0
        )

        # Get overall confidence from database
        overall = await self.calculate_claim_confidence(claim_id)

        return {
            'overall_confidence': overall,
            'overall_label': self.get_confidence_label(overall),
            'overall_stars': self.get_confidence_stars(overall),
            'support_confidence': round(support_confidence, 2),
            'support_count': len(support_findings),
            'challenge_confidence': round(challenge_confidence, 2),
            'challenge_count': len(challenge_findings),
            'neutral_confidence': round(neutral_confidence, 2),
            'neutral_count': len(neutral_findings),
            'needs_more_investigation': self.should_trigger_additional_investigation(overall)
        }
