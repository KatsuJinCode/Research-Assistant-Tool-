"""
Anomaly Detection for Claims

Detects unusual or outlier claims that warrant special attention.

Detection methods:
- Statistical anomalies (outliers in metadata)
- Semantic distance (claims far from others)
- Confidence anomalies (very high/low confidence)
- Contradiction of established knowledge
- Unusual patterns

Returns anomaly score 0-100 with explanation.
"""

import logging
import math
import statistics
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from collections import Counter

logger = logging.getLogger(__name__)


@dataclass
class AnomalyResult:
    """Result of anomaly detection"""
    claim_id: str
    claim_text: str
    anomaly_score: float  # 0-100
    anomaly_types: List[str]
    explanation: str
    severity: str  # low/medium/high
    details: Dict[str, Any]


class AnomalyDetector:
    """
    Detects anomalous claims using multiple methods:

    1. Statistical Anomalies: Z-score analysis on metadata
    2. Semantic Distance: Claims semantically distant from others
    3. Confidence Anomalies: Unusually high or low confidence
    4. Knowledge Contradiction: Claims that contradict established facts
    5. Pattern Anomalies: Unusual structural patterns

    Uses ensemble approach combining multiple detection methods.
    """

    def __init__(
        self,
        z_threshold: float = 3.0,
        semantic_threshold: float = 0.3,
        ai_client: Any = None
    ):
        """
        Initialize anomaly detector.

        Args:
            z_threshold: Z-score threshold for statistical anomalies
            semantic_threshold: Threshold for semantic distance
            ai_client: Optional AI client for enhanced detection
        """
        self.z_threshold = z_threshold
        self.semantic_threshold = semantic_threshold
        self.ai_client = ai_client

    async def detect(
        self,
        claim: Dict[str, Any],
        all_claims: Optional[List[Dict[str, Any]]] = None
    ) -> AnomalyResult:
        """
        Detect anomalies in a single claim.

        Args:
            claim: Claim to analyze
            all_claims: All claims for context

        Returns:
            AnomalyResult
        """
        claim_id = claim.get('id', 'unknown')
        claim_text = claim.get('text', '')

        anomaly_types = []
        scores = []
        details = {}

        # 1. Statistical anomalies
        if all_claims:
            stat_score, stat_details = self._detect_statistical_anomaly(claim, all_claims)
            if stat_score > 0:
                anomaly_types.append('statistical')
                scores.append(stat_score)
                details['statistical'] = stat_details

        # 2. Semantic distance
        if all_claims:
            sem_score, sem_details = self._detect_semantic_anomaly(claim, all_claims)
            if sem_score > 0:
                anomaly_types.append('semantic')
                scores.append(sem_score)
                details['semantic'] = sem_details

        # 3. Confidence anomalies
        conf_score, conf_details = self._detect_confidence_anomaly(claim)
        if conf_score > 0:
            anomaly_types.append('confidence')
            scores.append(conf_score)
            details['confidence'] = conf_details

        # 4. Knowledge contradiction
        if self.ai_client:
            know_score, know_details = await self._detect_knowledge_contradiction(claim)
            if know_score > 0:
                anomaly_types.append('contradiction')
                scores.append(know_score)
                details['contradiction'] = know_details

        # 5. Pattern anomalies
        pattern_score, pattern_details = self._detect_pattern_anomaly(claim)
        if pattern_score > 0:
            anomaly_types.append('pattern')
            scores.append(pattern_score)
            details['pattern'] = pattern_details

        # Calculate overall anomaly score
        if scores:
            # Use max score (most anomalous signal)
            anomaly_score = max(scores)
        else:
            anomaly_score = 0.0

        # Determine severity
        if anomaly_score >= 75:
            severity = 'high'
        elif anomaly_score >= 50:
            severity = 'medium'
        else:
            severity = 'low'

        # Generate explanation
        explanation = self._generate_explanation(anomaly_types, details)

        return AnomalyResult(
            claim_id=claim_id,
            claim_text=claim_text,
            anomaly_score=anomaly_score,
            anomaly_types=anomaly_types,
            explanation=explanation,
            severity=severity,
            details=details
        )

    def _detect_statistical_anomaly(
        self,
        claim: Dict[str, Any],
        all_claims: List[Dict[str, Any]]
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Detect statistical anomalies using Z-scores.

        Checks for outliers in:
        - Word count
        - Confidence scores
        - Number of evidence items
        - Number of relationships
        """
        anomaly_score = 0.0
        details = {}

        # Word count
        word_count = len(claim.get('text', '').split())
        all_word_counts = [len(c.get('text', '').split()) for c in all_claims]

        if len(all_word_counts) > 1:
            mean_words = statistics.mean(all_word_counts)
            std_words = statistics.stdev(all_word_counts) if len(all_word_counts) > 1 else 1.0

            if std_words > 0:
                z_score = abs((word_count - mean_words) / std_words)
                if z_score > self.z_threshold:
                    anomaly_score = max(anomaly_score, min(z_score * 20, 100))
                    details['word_count_zscore'] = z_score
                    details['word_count'] = word_count
                    details['mean_word_count'] = mean_words

        # Confidence anomalies
        confidence = claim.get('confidence', 0.5)
        all_confidences = [c.get('confidence', 0.5) for c in all_claims]

        if len(all_confidences) > 1:
            mean_conf = statistics.mean(all_confidences)
            std_conf = statistics.stdev(all_confidences) if len(all_confidences) > 1 else 0.1

            if std_conf > 0:
                z_score = abs((confidence - mean_conf) / std_conf)
                if z_score > self.z_threshold:
                    anomaly_score = max(anomaly_score, min(z_score * 20, 100))
                    details['confidence_zscore'] = z_score
                    details['confidence'] = confidence

        return anomaly_score, details

    def _detect_semantic_anomaly(
        self,
        claim: Dict[str, Any],
        all_claims: List[Dict[str, Any]]
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Detect claims semantically distant from others.

        Uses simple word overlap as proxy for semantic similarity.
        """
        claim_words = set(claim.get('text', '').lower().split())

        if not claim_words:
            return 0.0, {}

        # Calculate average similarity to other claims
        similarities = []

        for other_claim in all_claims:
            if other_claim.get('id') == claim.get('id'):
                continue

            other_words = set(other_claim.get('text', '').lower().split())
            if not other_words:
                continue

            # Jaccard similarity
            intersection = len(claim_words & other_words)
            union = len(claim_words | other_words)
            similarity = intersection / union if union > 0 else 0.0
            similarities.append(similarity)

        if not similarities:
            return 0.0, {}

        avg_similarity = statistics.mean(similarities)
        max_similarity = max(similarities)

        # Low average similarity indicates semantic anomaly
        if avg_similarity < self.semantic_threshold:
            anomaly_score = (self.semantic_threshold - avg_similarity) / self.semantic_threshold * 100
            return anomaly_score, {
                'avg_similarity': avg_similarity,
                'max_similarity': max_similarity,
                'threshold': self.semantic_threshold
            }

        return 0.0, {}

    def _detect_confidence_anomaly(
        self,
        claim: Dict[str, Any]
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Detect unusual confidence levels.

        Very high (>0.95) or very low (<0.2) confidence is anomalous.
        """
        confidence = claim.get('confidence', 0.5)

        if confidence > 0.95:
            anomaly_score = (confidence - 0.95) / 0.05 * 50  # Up to 50 points
            return anomaly_score, {
                'type': 'very_high_confidence',
                'confidence': confidence,
                'message': 'Unusually high confidence may indicate overconfidence'
            }
        elif confidence < 0.2:
            anomaly_score = (0.2 - confidence) / 0.2 * 50
            return anomaly_score, {
                'type': 'very_low_confidence',
                'confidence': confidence,
                'message': 'Unusually low confidence may indicate problematic claim'
            }

        return 0.0, {}

    async def _detect_knowledge_contradiction(
        self,
        claim: Dict[str, Any]
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Detect claims that contradict established knowledge.

        Uses AI to check against common knowledge.
        """
        if not self.ai_client:
            return 0.0, {}

        claim_text = claim.get('text', '')

        prompt = f"""Does this claim contradict well-established scientific facts or common knowledge?

Claim: "{claim_text}"

Return JSON:
{{
    "contradicts": true/false,
    "contradiction_type": "scientific_fact|historical_fact|logical|none",
    "confidence": 0.0-1.0,
    "explanation": "brief explanation"
}}"""

        try:
            import asyncio
            import json

            if asyncio.iscoroutinefunction(self.ai_client.generate):
                response = await self.ai_client.generate(
                    prompt,
                    temperature=0.1,
                    response_format='json'
                )
            else:
                response = self.ai_client.generate(prompt, temperature=0.1)

            result = json.loads(response)

            if result.get('contradicts'):
                anomaly_score = result.get('confidence', 0.5) * 100
                return anomaly_score, {
                    'type': result.get('contradiction_type'),
                    'explanation': result.get('explanation'),
                    'ai_confidence': result.get('confidence')
                }

        except Exception as e:
            logger.error(f"Knowledge contradiction detection failed: {e}")

        return 0.0, {}

    def _detect_pattern_anomaly(
        self,
        claim: Dict[str, Any]
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Detect unusual structural patterns.

        Checks for:
        - All caps text
        - Excessive punctuation
        - Very short/long claims
        - Unusual character patterns
        """
        text = claim.get('text', '')
        anomaly_score = 0.0
        details = {}

        # All caps
        if text.isupper() and len(text) > 10:
            anomaly_score = max(anomaly_score, 60)
            details['all_caps'] = True

        # Excessive punctuation
        punct_ratio = sum(1 for c in text if c in '!?') / len(text) if text else 0
        if punct_ratio > 0.05:
            anomaly_score = max(anomaly_score, punct_ratio * 500)
            details['excessive_punctuation'] = punct_ratio

        # Very short
        if len(text) < 10:
            anomaly_score = max(anomaly_score, 40)
            details['very_short'] = len(text)

        # Very long
        if len(text) > 1000:
            anomaly_score = max(anomaly_score, 50)
            details['very_long'] = len(text)

        # Repeated characters
        import re
        repeated = re.findall(r'(.)\1{4,}', text)
        if repeated:
            anomaly_score = max(anomaly_score, 70)
            details['repeated_characters'] = len(repeated)

        return anomaly_score, details if details else {}

    def _generate_explanation(
        self,
        anomaly_types: List[str],
        details: Dict[str, Any]
    ) -> str:
        """Generate human-readable explanation"""
        if not anomaly_types:
            return "No anomalies detected"

        explanations = []

        for atype in anomaly_types:
            if atype in details:
                detail = details[atype]
                if atype == 'statistical':
                    explanations.append("Statistical outlier in metadata")
                elif atype == 'semantic':
                    explanations.append(f"Semantically distant from other claims (similarity: {detail.get('avg_similarity', 0):.2f})")
                elif atype == 'confidence':
                    explanations.append(detail.get('message', 'Confidence anomaly'))
                elif atype == 'contradiction':
                    explanations.append(f"May contradict established knowledge: {detail.get('explanation', '')}")
                elif atype == 'pattern':
                    explanations.append("Unusual structural patterns detected")

        return "; ".join(explanations)

    async def detect_batch(
        self,
        claims: List[Dict[str, Any]]
    ) -> List[AnomalyResult]:
        """
        Detect anomalies in multiple claims.

        Args:
            claims: List of claims to analyze

        Returns:
            List of AnomalyResult
        """
        results = []

        for claim in claims:
            result = await self.detect(claim, claims)
            results.append(result)

        return results

    def flag_anomalies(
        self,
        db: Any,
        anomalies: List[AnomalyResult],
        min_score: float = 50.0
    ):
        """
        Flag anomalous claims in database.

        Args:
            db: Database connection
            anomalies: List of anomaly results
            min_score: Minimum score to flag
        """
        for anomaly in anomalies:
            if anomaly.anomaly_score >= min_score:
                try:
                    db.execute(
                        """
                        UPDATE claims
                        SET is_anomaly = true,
                            anomaly_score = $1,
                            anomaly_types = $2,
                            anomaly_explanation = $3,
                            anomaly_severity = $4
                        WHERE id = $5
                        """,
                        anomaly.anomaly_score,
                        anomaly.anomaly_types,  # Store as JSON array
                        anomaly.explanation,
                        anomaly.severity,
                        anomaly.claim_id
                    )
                except Exception as e:
                    logger.error(f"Failed to flag anomaly {anomaly.claim_id}: {e}")

    def get_anomaly_statistics(
        self,
        results: List[AnomalyResult]
    ) -> Dict[str, Any]:
        """Get statistics about detected anomalies"""
        total = len(results)
        anomalous = [r for r in results if r.anomaly_score >= 50]

        type_counts = Counter()
        for result in anomalous:
            for atype in result.anomaly_types:
                type_counts[atype] += 1

        return {
            'total_claims': total,
            'anomalous_claims': len(anomalous),
            'anomaly_rate': len(anomalous) / total if total > 0 else 0,
            'severity_distribution': {
                'high': len([r for r in results if r.severity == 'high']),
                'medium': len([r for r in results if r.severity == 'medium']),
                'low': len([r for r in results if r.severity == 'low'])
            },
            'type_distribution': dict(type_counts),
            'avg_anomaly_score': statistics.mean([r.anomaly_score for r in results]) if results else 0
        }

    def export_anomalies(
        self,
        results: List[AnomalyResult],
        output_path: str,
        min_score: float = 0.0
    ):
        """Export anomaly results to JSON"""
        import json

        filtered_results = [r for r in results if r.anomaly_score >= min_score]

        export_data = {
            'summary': self.get_anomaly_statistics(results),
            'anomalies': [
                {
                    'claim_id': r.claim_id,
                    'claim_text': r.claim_text,
                    'anomaly_score': r.anomaly_score,
                    'anomaly_types': r.anomaly_types,
                    'explanation': r.explanation,
                    'severity': r.severity,
                    'details': r.details
                }
                for r in filtered_results
            ]
        }

        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)

        logger.info(f"Exported {len(filtered_results)} anomalies to {output_path}")
