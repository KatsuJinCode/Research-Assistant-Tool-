"""
Automatic Claim Classification

Classifies claims into categories automatically:
- Factual: Verifiable facts
- Opinion: Subjective opinions
- Hypothesis: Scientific hypotheses
- Prediction: Future predictions
- Definition: Definitions of terms

Features:
- AI-based classification with confidence scoring
- Batch classification
- Fine-tuning on user data (optional)
- Adds claim_category property to nodes
"""

import logging
import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ClaimCategory(Enum):
    """Claim category types"""
    FACTUAL = "factual"
    OPINION = "opinion"
    HYPOTHESIS = "hypothesis"
    PREDICTION = "prediction"
    DEFINITION = "definition"
    UNKNOWN = "unknown"


@dataclass
class ClassificationResult:
    """Result of claim classification"""
    claim_id: str
    claim_text: str
    category: ClaimCategory
    confidence: float
    reasoning: str
    subcategory: Optional[str] = None


class ClaimClassifier:
    """
    Automatic claim classifier using AI and rule-based methods.

    Categories:
    - Factual: Statements that can be verified with evidence
    - Opinion: Subjective statements expressing views/feelings
    - Hypothesis: Proposed explanations requiring testing
    - Prediction: Statements about future events
    - Definition: Statements defining terms or concepts
    """

    def __init__(self, ai_client: Any = None, use_ai: bool = True):
        """
        Initialize classifier.

        Args:
            ai_client: Optional AI client for AI-based classification
            use_ai: Whether to use AI (falls back to rules if False)
        """
        self.ai_client = ai_client
        self.use_ai = use_ai and ai_client is not None

        # Rule-based patterns
        self.patterns = {
            ClaimCategory.OPINION: [
                r'\b(think|believe|feel|seems?|appears?|probably|likely|maybe|perhaps|in my opinion)\b',
                r'\b(should|ought|must|better|worse|best|worst)\b',
                r'\b(beautiful|ugly|good|bad|amazing|terrible)\b'
            ],
            ClaimCategory.HYPOTHESIS: [
                r'\b(hypothesis|hypothesize|theory|theorize|propose|suggest|may|might|could)\b',
                r'\bif\b.*\bthen\b',
                r'\b(possibly|potentially|presumably)\b'
            ],
            ClaimCategory.PREDICTION: [
                r'\b(will|would|shall|going to|expect|predict|forecast)\b',
                r'\b(next|future|upcoming|soon|eventually)\b',
                r'\b(by \d{4}|in \d+ years?)\b'
            ],
            ClaimCategory.DEFINITION: [
                r'\bis defined as\b',
                r'\bmeans?\b',
                r'\brefers? to\b',
                r'\b(definition|terminology)\b',
                r'^[A-Z][a-z]+ is '
            ]
        }

    async def classify(
        self,
        claim_text: str,
        claim_id: Optional[str] = None
    ) -> ClassificationResult:
        """
        Classify a single claim.

        Args:
            claim_text: The claim text
            claim_id: Optional claim ID

        Returns:
            ClassificationResult
        """
        if self.use_ai:
            return await self._classify_with_ai(claim_text, claim_id)
        else:
            return self._classify_with_rules(claim_text, claim_id)

    async def classify_batch(
        self,
        claims: List[Dict[str, str]]
    ) -> List[ClassificationResult]:
        """
        Classify multiple claims.

        Args:
            claims: List of dicts with 'id' and 'text' keys

        Returns:
            List of ClassificationResult
        """
        results = []

        for claim in claims:
            result = await self.classify(
                claim.get('text', ''),
                claim.get('id')
            )
            results.append(result)

        return results

    async def _classify_with_ai(
        self,
        claim_text: str,
        claim_id: Optional[str] = None
    ) -> ClassificationResult:
        """Classify using AI"""
        prompt = f"""Classify this claim into one of these categories:
- factual: Verifiable facts that can be proven true or false
- opinion: Subjective statements expressing views, feelings, or judgments
- hypothesis: Proposed explanations that require testing/investigation
- prediction: Statements about future events or outcomes
- definition: Statements defining terms or concepts

Claim: "{claim_text}"

Return JSON:
{{
    "category": "factual|opinion|hypothesis|prediction|definition",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation",
    "subcategory": "optional subcategory"
}}"""

        try:
            import asyncio
            if asyncio.iscoroutinefunction(self.ai_client.generate):
                response = await self.ai_client.generate(
                    prompt,
                    temperature=0.1,
                    response_format='json'
                )
            else:
                response = self.ai_client.generate(prompt, temperature=0.1)

            import json
            result = json.loads(response)

            return ClassificationResult(
                claim_id=claim_id or "unknown",
                claim_text=claim_text,
                category=ClaimCategory(result['category']),
                confidence=result['confidence'],
                reasoning=result['reasoning'],
                subcategory=result.get('subcategory')
            )

        except Exception as e:
            logger.error(f"AI classification failed: {e}")
            # Fallback to rules
            return self._classify_with_rules(claim_text, claim_id)

    def _classify_with_rules(
        self,
        claim_text: str,
        claim_id: Optional[str] = None
    ) -> ClassificationResult:
        """Classify using rule-based patterns"""
        text_lower = claim_text.lower()

        # Check each category
        scores = {category: 0.0 for category in ClaimCategory}

        for category, patterns in self.patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    scores[category] += 1

        # Normalize scores
        max_score = max(scores.values()) if scores.values() else 0

        if max_score > 0:
            # Get highest scoring category
            best_category = max(scores, key=scores.get)
            confidence = min(scores[best_category] / (max_score + 2), 0.9)  # Cap at 0.9

            return ClassificationResult(
                claim_id=claim_id or "unknown",
                claim_text=claim_text,
                category=best_category,
                confidence=confidence,
                reasoning=f"Matched {int(scores[best_category])} pattern(s)"
            )
        else:
            # Default to factual if no patterns match
            return ClassificationResult(
                claim_id=claim_id or "unknown",
                claim_text=claim_text,
                category=ClaimCategory.FACTUAL,
                confidence=0.5,
                reasoning="No specific patterns detected, defaulting to factual"
            )

    def update_claim_categories(
        self,
        db: Any,
        claim_results: List[ClassificationResult]
    ):
        """
        Update claim categories in database.

        Args:
            db: Database connection
            claim_results: List of classification results
        """
        for result in claim_results:
            try:
                # Update claim node with category
                db.execute(
                    """
                    UPDATE claims
                    SET category = $1, category_confidence = $2
                    WHERE id = $3
                    """,
                    result.category.value,
                    result.confidence,
                    result.claim_id
                )
            except Exception as e:
                logger.error(f"Failed to update claim {result.claim_id}: {e}")

    def get_category_distribution(
        self,
        results: List[ClassificationResult]
    ) -> Dict[str, int]:
        """Get distribution of categories"""
        distribution = {cat.value: 0 for cat in ClaimCategory}

        for result in results:
            distribution[result.category.value] += 1

        return distribution

    def get_confidence_stats(
        self,
        results: List[ClassificationResult]
    ) -> Dict[str, float]:
        """Get confidence statistics"""
        if not results:
            return {
                'mean': 0.0,
                'min': 0.0,
                'max': 0.0,
                'median': 0.0
            }

        confidences = [r.confidence for r in results]
        confidences.sort()

        return {
            'mean': sum(confidences) / len(confidences),
            'min': confidences[0],
            'max': confidences[-1],
            'median': confidences[len(confidences) // 2]
        }

    def export_results(
        self,
        results: List[ClassificationResult],
        output_path: str
    ):
        """Export classification results to JSON"""
        import json

        export_data = {
            'summary': {
                'total_claims': len(results),
                'distribution': self.get_category_distribution(results),
                'confidence_stats': self.get_confidence_stats(results)
            },
            'results': [
                {
                    'claim_id': r.claim_id,
                    'claim_text': r.claim_text,
                    'category': r.category.value,
                    'confidence': r.confidence,
                    'reasoning': r.reasoning,
                    'subcategory': r.subcategory
                }
                for r in results
            ]
        }

        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)

        logger.info(f"Exported classification results to {output_path}")

    def train_on_user_data(
        self,
        training_data: List[Dict[str, Any]]
    ):
        """
        Fine-tune classifier on user-provided labels.

        Args:
            training_data: List of dicts with 'text' and 'category' keys

        Note: This is a placeholder for future implementation.
        Could use scikit-learn for traditional ML or fine-tune an LLM.
        """
        # TODO: Implement training
        # Options:
        # 1. Traditional ML: TF-IDF + Logistic Regression
        # 2. Fine-tune small transformer model
        # 3. Few-shot learning with GPT-4

        logger.warning("Training not yet implemented")
        pass


# Example usage
async def example_classification():
    """Example of using the classifier"""

    classifier = ClaimClassifier(use_ai=False)  # Using rules for demo

    claims = [
        {"id": "1", "text": "Water boils at 100°C at sea level"},
        {"id": "2", "text": "I think Python is the best programming language"},
        {"id": "3", "text": "We hypothesize that increased CO2 leads to warming"},
        {"id": "4", "text": "The global temperature will rise by 2°C by 2050"},
        {"id": "5", "text": "Photosynthesis is the process by which plants convert light to energy"}
    ]

    results = await classifier.classify_batch(claims)

    for result in results:
        print(f"\nClaim: {result.claim_text}")
        print(f"Category: {result.category.value}")
        print(f"Confidence: {result.confidence:.2f}")
        print(f"Reasoning: {result.reasoning}")

    # Get statistics
    print("\nDistribution:", classifier.get_category_distribution(results))
    print("Confidence Stats:", classifier.get_confidence_stats(results))
