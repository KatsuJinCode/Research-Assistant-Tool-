"""
Investigation Value Prediction

Predicts how valuable investigating a claim would be.

Scoring factors:
- Novelty: How unique/novel the claim is
- Evidence gap: How much evidence is missing
- Controversy: Presence of conflicting claims
- Recency: How recent the topic is
- Impact: Potential importance/impact

Returns score 0-100 with explanation.
"""

import logging
import math
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class ValuePrediction:
    """Investigation value prediction result"""
    claim_id: str
    claim_text: str
    value_score: float  # 0-100
    factors: Dict[str, float]  # Individual factor scores
    explanation: str
    recommendation: str  # high/medium/low priority


class InvestigationValuePredictor:
    """
    Predicts the value of investigating a claim.

    Uses multiple factors to compute an investigation value score:
    1. Novelty (0-100): How unique the claim is
    2. Evidence Gap (0-100): How much evidence is missing
    3. Controversy (0-100): Level of conflicting claims
    4. Recency (0-100): How recent/timely the topic is
    5. Impact (0-100): Potential importance

    Final score is weighted average of these factors.
    """

    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None,
        ai_client: Any = None
    ):
        """
        Initialize value predictor.

        Args:
            weights: Custom weights for factors (defaults to equal weights)
            ai_client: Optional AI client for enhanced predictions
        """
        self.weights = weights or {
            'novelty': 0.25,
            'evidence_gap': 0.25,
            'controversy': 0.20,
            'recency': 0.15,
            'impact': 0.15
        }

        # Normalize weights to sum to 1.0
        total = sum(self.weights.values())
        self.weights = {k: v/total for k, v in self.weights.items()}

        self.ai_client = ai_client

    async def predict(
        self,
        claim: Dict[str, Any],
        related_claims: Optional[List[Dict[str, Any]]] = None,
        existing_evidence: Optional[List[Dict[str, Any]]] = None
    ) -> ValuePrediction:
        """
        Predict investigation value for a claim.

        Args:
            claim: Claim dict with 'id', 'text', 'created_at', etc.
            related_claims: Related/similar claims
            existing_evidence: Existing evidence for the claim

        Returns:
            ValuePrediction
        """
        claim_id = claim.get('id', 'unknown')
        claim_text = claim.get('text', '')

        # Calculate individual factors
        novelty_score = self._calculate_novelty(claim, related_claims or [])
        evidence_gap_score = self._calculate_evidence_gap(claim, existing_evidence or [])
        controversy_score = self._calculate_controversy(claim, related_claims or [])
        recency_score = self._calculate_recency(claim)
        impact_score = await self._calculate_impact(claim)

        factors = {
            'novelty': novelty_score,
            'evidence_gap': evidence_gap_score,
            'controversy': controversy_score,
            'recency': recency_score,
            'impact': impact_score
        }

        # Calculate weighted final score
        final_score = sum(
            factors[factor] * weight
            for factor, weight in self.weights.items()
        )

        # Generate explanation
        explanation = self._generate_explanation(factors)

        # Recommendation
        if final_score >= 75:
            recommendation = "high"
        elif final_score >= 50:
            recommendation = "medium"
        else:
            recommendation = "low"

        return ValuePrediction(
            claim_id=claim_id,
            claim_text=claim_text,
            value_score=final_score,
            factors=factors,
            explanation=explanation,
            recommendation=recommendation
        )

    def _calculate_novelty(
        self,
        claim: Dict[str, Any],
        related_claims: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate novelty score.

        Novel claims have fewer similar claims in the system.
        """
        if not related_claims:
            return 90.0  # Very novel if no related claims

        # Count very similar claims
        similar_count = len([
            c for c in related_claims
            if c.get('similarity', 0) > 0.8
        ])

        if similar_count == 0:
            return 85.0
        elif similar_count <= 2:
            return 70.0
        elif similar_count <= 5:
            return 50.0
        else:
            return 30.0

    def _calculate_evidence_gap(
        self,
        claim: Dict[str, Any],
        existing_evidence: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate evidence gap score.

        Higher score means more need for evidence.
        """
        evidence_count = len(existing_evidence)

        # Quality-weighted evidence count
        weighted_count = sum(
            e.get('relevance_score', 0.5) * e.get('credibility_score', 0.5)
            for e in existing_evidence
        )

        if weighted_count == 0:
            return 100.0  # Complete gap
        elif weighted_count < 2:
            return 80.0
        elif weighted_count < 5:
            return 60.0
        elif weighted_count < 10:
            return 40.0
        else:
            return 20.0

    def _calculate_controversy(
        self,
        claim: Dict[str, Any],
        related_claims: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate controversy score.

        Higher score if there are conflicting claims.
        """
        if not related_claims:
            return 10.0  # Low controversy if isolated

        # Count supporting vs challenging claims
        supporting = len([
            c for c in related_claims
            if c.get('relationship') == 'supports'
        ])
        challenging = len([
            c for c in related_claims
            if c.get('relationship') == 'challenges'
        ])

        total = supporting + challenging
        if total == 0:
            return 10.0

        # High controversy if roughly equal support/challenge
        balance = min(supporting, challenging) / max(supporting, challenging, 1)

        if balance > 0.7:
            return 90.0  # Very controversial
        elif balance > 0.4:
            return 70.0
        elif balance > 0.2:
            return 50.0
        else:
            return 30.0

    def _calculate_recency(self, claim: Dict[str, Any]) -> float:
        """
        Calculate recency score.

        Recent claims score higher.
        """
        created_at = claim.get('created_at')
        if not created_at:
            return 50.0  # Unknown, assume moderate

        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            except:
                return 50.0

        age_days = (datetime.now() - created_at).days

        if age_days < 7:
            return 95.0  # Very recent
        elif age_days < 30:
            return 80.0
        elif age_days < 90:
            return 60.0
        elif age_days < 365:
            return 40.0
        else:
            return 20.0

    async def _calculate_impact(self, claim: Dict[str, Any]) -> float:
        """
        Calculate potential impact score.

        Uses AI to assess importance if available, otherwise uses heuristics.
        """
        if self.ai_client:
            return await self._calculate_impact_ai(claim)
        else:
            return self._calculate_impact_heuristic(claim)

    async def _calculate_impact_ai(self, claim: Dict[str, Any]) -> float:
        """Calculate impact using AI"""
        prompt = f"""Rate the potential importance/impact of investigating this claim on a scale of 0-100:

Claim: "{claim.get('text', '')}"

Consider:
- How many people it affects
- Importance to science/society
- Potential for new insights

Return just a number 0-100."""

        try:
            import asyncio
            if asyncio.iscoroutinefunction(self.ai_client.generate):
                response = await self.ai_client.generate(prompt, temperature=0.3)
            else:
                response = self.ai_client.generate(prompt)

            # Extract number
            import re
            match = re.search(r'\b(\d+(?:\.\d+)?)\b', response)
            if match:
                score = float(match.group(1))
                return min(max(score, 0), 100)
            else:
                return 50.0

        except Exception as e:
            logger.error(f"AI impact calculation failed: {e}")
            return self._calculate_impact_heuristic(claim)

    def _calculate_impact_heuristic(self, claim: Dict[str, Any]) -> float:
        """Calculate impact using heuristics"""
        text = claim.get('text', '').lower()

        # High-impact keywords
        high_impact_keywords = [
            'global', 'climate', 'health', 'pandemic', 'cancer',
            'breakthrough', 'revolutionary', 'crisis', 'emergency'
        ]

        # Count high-impact keywords
        impact_count = sum(1 for keyword in high_impact_keywords if keyword in text)

        if impact_count >= 3:
            return 90.0
        elif impact_count == 2:
            return 75.0
        elif impact_count == 1:
            return 60.0
        else:
            return 40.0

    def _generate_explanation(self, factors: Dict[str, float]) -> str:
        """Generate human-readable explanation"""
        explanations = []

        for factor, score in factors.items():
            level = "high" if score >= 70 else "moderate" if score >= 40 else "low"
            explanations.append(f"{factor}: {level} ({score:.0f}/100)")

        return "; ".join(explanations)

    async def predict_batch(
        self,
        claims: List[Dict[str, Any]],
        claim_relationships: Optional[Dict[str, List[Dict[str, Any]]]] = None,
        claim_evidence: Optional[Dict[str, List[Dict[str, Any]]]] = None
    ) -> List[ValuePrediction]:
        """
        Predict investigation value for multiple claims.

        Args:
            claims: List of claim dicts
            claim_relationships: Dict mapping claim IDs to related claims
            claim_evidence: Dict mapping claim IDs to evidence

        Returns:
            List of ValuePrediction
        """
        results = []

        for claim in claims:
            claim_id = claim.get('id', 'unknown')

            related = claim_relationships.get(claim_id, []) if claim_relationships else []
            evidence = claim_evidence.get(claim_id, []) if claim_evidence else []

            prediction = await self.predict(claim, related, evidence)
            results.append(prediction)

        return results

    def update_investigation_values(
        self,
        db: Any,
        predictions: List[ValuePrediction]
    ):
        """
        Update investigation values in database.

        Args:
            db: Database connection
            predictions: List of value predictions
        """
        for pred in predictions:
            try:
                db.execute(
                    """
                    UPDATE claims
                    SET investigation_value = $1,
                        value_factors = $2,
                        value_explanation = $3,
                        priority = $4
                    WHERE id = $5
                    """,
                    pred.value_score,
                    pred.factors,  # Store as JSON
                    pred.explanation,
                    pred.recommendation,
                    pred.claim_id
                )
            except Exception as e:
                logger.error(f"Failed to update claim {pred.claim_id}: {e}")

    def get_priority_queue(
        self,
        predictions: List[ValuePrediction],
        limit: int = 10
    ) -> List[ValuePrediction]:
        """
        Get top priority claims for investigation.

        Args:
            predictions: All value predictions
            limit: Maximum number to return

        Returns:
            Top N highest-value claims
        """
        sorted_predictions = sorted(
            predictions,
            key=lambda p: p.value_score,
            reverse=True
        )

        return sorted_predictions[:limit]

    def export_predictions(
        self,
        predictions: List[ValuePrediction],
        output_path: str
    ):
        """Export predictions to JSON"""
        import json

        export_data = {
            'summary': {
                'total_claims': len(predictions),
                'high_priority': len([p for p in predictions if p.recommendation == 'high']),
                'medium_priority': len([p for p in predictions if p.recommendation == 'medium']),
                'low_priority': len([p for p in predictions if p.recommendation == 'low']),
                'avg_score': sum(p.value_score for p in predictions) / len(predictions) if predictions else 0
            },
            'predictions': [
                {
                    'claim_id': p.claim_id,
                    'claim_text': p.claim_text,
                    'value_score': p.value_score,
                    'factors': p.factors,
                    'explanation': p.explanation,
                    'recommendation': p.recommendation
                }
                for p in predictions
            ]
        }

        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)

        logger.info(f"Exported value predictions to {output_path}")
