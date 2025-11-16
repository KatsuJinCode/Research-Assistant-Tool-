"""
Claim normalizer with CRITICAL qualifier preservation.

Normalizes claims while ensuring all qualifier terms are preserved.
Auto-fails normalization if qualifiers are lost.
"""

import logging
from typing import Dict, Any, Optional
from research_agent.utils.ai_client import AIClient
from research_agent.normalization.qualifier_extractor import QualifierExtractor


logger = logging.getLogger(__name__)


class ClaimNormalizer:
    """
    Normalize claims while preserving qualifiers.

    CRITICAL REQUIREMENT: Qualifier preservation is mandatory.
    Any normalization that loses qualifiers is automatically failed.
    """

    def __init__(self, ai_client: AIClient):
        """
        Initialize claim normalizer.

        Args:
            ai_client: AI client instance
        """
        self.ai = ai_client
        self.qualifier_extractor = QualifierExtractor()

    async def normalize(
        self,
        claim_text: str,
        max_retries: int = 2
    ) -> Dict[str, Any]:
        """
        Normalize claim while preserving qualifiers.

        Args:
            claim_text: Original claim text
            max_retries: Max retries if qualifiers lost

        Returns:
            Dict with:
                - normalized_text: Normalized claim
                - qualifiers: List of qualifiers
                - qualifiers_preserved: bool
                - confidence: Normalization confidence
                - needs_human_review: bool
        """
        # Step 1: Extract qualifiers FIRST
        qualifiers = self.qualifier_extractor.extract(claim_text)
        logger.info(
            f"Extracted {len(qualifiers)} qualifiers from claim: "
            f"{[q['text'] for q in qualifiers]}"
        )

        # Step 2: Generate normalized version
        normalized_text = None
        qualifiers_preserved = False

        for attempt in range(max_retries + 1):
            if attempt == 0:
                # First attempt: normal normalization
                normalized_text = await self._generate_normalized(claim_text, qualifiers)
            else:
                # Retry with stricter prompt
                logger.warning(
                    f"Retry {attempt}/{max_retries}: Qualifiers lost, "
                    f"using stricter prompt"
                )
                normalized_text = await self._generate_normalized_strict(
                    claim_text, qualifiers
                )

            # Step 3: VERIFY qualifiers preserved
            verification = self.qualifier_extractor.verify_preservation(
                claim_text,
                normalized_text
            )
            qualifiers_preserved = verification['preserved']

            if qualifiers_preserved:
                logger.info("✓ Qualifiers preserved successfully")
                break
            else:
                logger.error(
                    f"✗ Qualifiers lost: {verification['missing']}"
                )

        # Step 4: Calculate confidence
        confidence = await self._calculate_confidence(
            claim_text,
            normalized_text,
            qualifiers_preserved
        )

        # Step 5: Determine if human review needed
        needs_human_review = (
            confidence < 0.95 or
            not qualifiers_preserved or
            len(qualifiers) > 3  # Complex claims need review
        )

        result = {
            'normalized_text': normalized_text,
            'qualifiers': qualifiers,
            'qualifiers_preserved': qualifiers_preserved,
            'confidence': confidence,
            'needs_human_review': needs_human_review,
            'original_text': claim_text
        }

        if not qualifiers_preserved:
            result['failure_reason'] = 'qualifiers_lost'
            result['missing_qualifiers'] = verification['missing']

        return result

    async def _generate_normalized(
        self,
        claim_text: str,
        qualifiers: list
    ) -> str:
        """
        Generate normalized claim.

        Args:
            claim_text: Original claim
            qualifiers: Extracted qualifiers

        Returns:
            Normalized claim text
        """
        qualifier_list = ", ".join([q['text'] for q in qualifiers])

        prompt = f"""Simplify this claim to its core assertion while preserving:
1. ALL qualifier words: {qualifier_list}
2. ALL numbers and percentages
3. ALL temporal markers (years, dates)
4. The exact meaning

Original claim: "{claim_text}"

Rules:
- Remove unnecessary phrases and redundancy
- Keep the claim concise but complete
- MUST include all qualifiers: {qualifier_list}
- Do not change the meaning
- Do not add information not in the original

Return only the simplified claim, no explanation."""

        response = await self.ai.generate(prompt, temperature=0.1)
        return response.strip().strip('"')

    async def _generate_normalized_strict(
        self,
        claim_text: str,
        qualifiers: list
    ) -> str:
        """
        Generate normalized claim with STRICT qualifier preservation.

        Used on retry when qualifiers were lost.

        Args:
            claim_text: Original claim
            qualifiers: Extracted qualifiers

        Returns:
            Normalized claim text
        """
        qualifier_list = ", ".join([q['text'] for q in qualifiers])

        prompt = f"""❗ CRITICAL: You MUST include these exact words in your response: {qualifier_list}

Simplify this claim while INCLUDING ALL OF THESE WORDS: {qualifier_list}

Original claim: "{claim_text}"

REQUIREMENTS:
1. Include EVERY word from this list: {qualifier_list}
2. Simplify the phrasing but keep all qualifiers
3. Do not change the meaning
4. Keep it concise

If you cannot include all qualifier words, return the original claim unchanged.

Return only the simplified claim:"""

        response = await self.ai.generate(prompt, temperature=0.0)
        normalized = response.strip().strip('"')

        # If still missing qualifiers, return original
        verification = self.qualifier_extractor.verify_preservation(
            claim_text,
            normalized
        )
        if not verification['preserved']:
            logger.warning("Even strict prompt failed, returning original")
            return claim_text

        return normalized

    async def _calculate_confidence(
        self,
        original: str,
        normalized: str,
        qualifiers_preserved: bool
    ) -> float:
        """
        Calculate normalization confidence.

        Args:
            original: Original claim
            normalized: Normalized claim
            qualifiers_preserved: Whether qualifiers preserved

        Returns:
            Confidence score (0.0-1.0)
        """
        # Auto-fail if qualifiers lost
        if not qualifiers_preserved:
            return 0.0

        # Ask LLM: "Are these semantically equivalent?"
        prompt = f"""Do these two claims mean exactly the same thing?

Original: "{original}"
Normalized: "{normalized}"

Answer with a confidence score (0.0-1.0) where:
- 1.0 = Identical meaning, all details preserved
- 0.9 = Nearly identical, minor simplification only
- 0.7 = Same core meaning, some detail simplified
- 0.5 = Similar but some information changed
- 0.3 = Meaning shifted
- 0.0 = Different meaning

Return only the number (e.g., 0.9):"""

        try:
            response = await self.ai.generate(prompt, temperature=0.0)
            confidence = float(response.strip())
            confidence = max(0.0, min(1.0, confidence))  # Clamp to [0, 1]
            return confidence
        except ValueError:
            logger.error(f"Invalid confidence response: {response}")
            return 0.5  # Default to medium confidence

    async def validate_normalization(
        self,
        original: str,
        normalized: str
    ) -> Dict[str, Any]:
        """
        Validate a normalization.

        Args:
            original: Original claim
            normalized: Normalized claim

        Returns:
            Validation results
        """
        verification = self.qualifier_extractor.verify_preservation(
            original,
            normalized
        )

        confidence = await self._calculate_confidence(
            original,
            normalized,
            verification['preserved']
        )

        return {
            'valid': verification['preserved'] and confidence >= 0.7,
            'qualifiers_preserved': verification['preserved'],
            'missing_qualifiers': verification['missing'],
            'confidence': confidence,
            'recommendation': self._get_recommendation(
                verification['preserved'],
                confidence
            )
        }

    def _get_recommendation(
        self,
        qualifiers_preserved: bool,
        confidence: float
    ) -> str:
        """Get recommendation for normalization."""
        if not qualifiers_preserved:
            return "REJECT - Qualifiers lost"
        elif confidence >= 0.95:
            return "AUTO-APPROVE - High confidence"
        elif confidence >= 0.85:
            return "APPROVE - Good confidence"
        elif confidence >= 0.70:
            return "REVIEW - Medium confidence, human review recommended"
        else:
            return "REJECT - Low confidence"

    async def generate_alternatives(
        self,
        claim_text: str,
        count: int = 3
    ) -> list:
        """
        Generate multiple normalization candidates.

        Args:
            claim_text: Original claim
            count: Number of alternatives

        Returns:
            List of normalization results
        """
        qualifiers = self.qualifier_extractor.extract(claim_text)
        alternatives = []

        for i in range(count):
            # Use slightly different temperatures for variety
            temp = 0.1 + (i * 0.1)

            normalized = await self._generate_normalized(claim_text, qualifiers)
            verification = self.qualifier_extractor.verify_preservation(
                claim_text,
                normalized
            )
            confidence = await self._calculate_confidence(
                claim_text,
                normalized,
                verification['preserved']
            )

            alternatives.append({
                'normalized_text': normalized,
                'qualifiers_preserved': verification['preserved'],
                'confidence': confidence,
                'rank': i + 1
            })

        # Sort by confidence
        alternatives.sort(key=lambda x: x['confidence'], reverse=True)

        # Re-rank
        for i, alt in enumerate(alternatives):
            alt['rank'] = i + 1

        return alternatives
