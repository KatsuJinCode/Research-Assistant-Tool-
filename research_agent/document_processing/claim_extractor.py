"""
Claim extraction from research documents using LLM.
"""

import json
import logging
from typing import List, Dict, Any
from research_agent.utils.ai_client import AIClient


logger = logging.getLogger(__name__)


class ClaimExtractor:
    """
    Extract claims from document text using LLM.

    MVP approach: Simple LLM-based extraction with structured output.
    """

    def __init__(self, ai_client: AIClient):
        """
        Initialize claim extractor.

        Args:
            ai_client: AI client instance
        """
        self.ai = ai_client

    async def extract_claims(
        self,
        document_text: str,
        max_length: int = 8000
    ) -> List[Dict[str, Any]]:
        """
        Extract claims from document using LLM.

        Args:
            document_text: Full document text
            max_length: Maximum text length to process

        Returns:
            List of claim dicts with:
                - text: Exact claim text
                - type: Claim type
                - confidence: Extraction confidence
        """
        # Truncate if needed (MVP limitation)
        if len(document_text) > max_length:
            logger.warning(
                f"Document truncated from {len(document_text)} to {max_length} chars"
            )
            document_text = document_text[:max_length]

        prompt = self._build_extraction_prompt(document_text)

        try:
            response = await self.ai.generate(
                prompt,
                temperature=0.3,
                response_format='json'
            )

            claims = json.loads(response)

            # Validate response structure
            if not isinstance(claims, list):
                logger.error(f"Invalid response format: expected list, got {type(claims)}")
                return []

            logger.info(f"Extracted {len(claims)} claims from document")
            return claims

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response from AI: {e}")
            return []
        except Exception as e:
            logger.error(f"Error extracting claims: {e}")
            return []

    def _build_extraction_prompt(self, document_text: str) -> str:
        """Build prompt for claim extraction."""
        return f"""You are a research claim extractor. Identify all factual claims,
hypotheses, and conclusions in this research document.

A claim is:
- A statement that asserts something as true or likely
- A hypothesis being tested
- A conclusion from results
- A prediction or recommendation
- A normative statement (should/ought)

NOT a claim:
- Background information or definitions
- Methodology descriptions (unless making a claim about the method)
- Acknowledgments or citations
- Questions or uncertainties

IMPORTANT: Preserve ALL qualifier words like:
- Modals: can, could, may, might, will, would, should, must
- Frequency: always, never, often, rarely, sometimes, usually, mostly
- Quantity: all, every, each, some, most, many, few, several
- Certainty: probably, possibly, likely, perhaps
- Temporal: by 2030, until, before, after

Document:
{document_text}

Return JSON array:
[
  {{
    "text": "exact claim text from document with all qualifiers preserved",
    "type": "empirical" | "theoretical" | "predictive" | "normative" | "definitional",
    "confidence": 0.0-1.0
  }}
]

Return ONLY the JSON array, no other text."""

    async def extract_claims_with_context(
        self,
        document_text: str,
        max_length: int = 8000
    ) -> List[Dict[str, Any]]:
        """
        Extract claims with surrounding context.

        Args:
            document_text: Full document text
            max_length: Maximum text length to process

        Returns:
            List of claim dicts with context
        """
        # For MVP, use simple extraction
        # TODO: Add context extraction in post-MVP
        claims = await self.extract_claims(document_text, max_length)

        # Add simple context (surrounding sentences)
        for claim in claims:
            claim['context'] = self._extract_context(document_text, claim['text'])

        return claims

    def _extract_context(
        self,
        full_text: str,
        claim_text: str,
        context_chars: int = 500
    ) -> str:
        """
        Extract context around a claim.

        Args:
            full_text: Full document text
            claim_text: Claim text to find
            context_chars: Characters to include before/after

        Returns:
            Context string
        """
        # Find claim in text
        index = full_text.find(claim_text)

        if index == -1:
            # Claim not found verbatim, return empty context
            return ""

        # Get context before and after
        start = max(0, index - context_chars)
        end = min(len(full_text), index + len(claim_text) + context_chars)

        context = full_text[start:end]

        # Add ellipsis if truncated
        if start > 0:
            context = "..." + context
        if end < len(full_text):
            context = context + "..."

        return context

    async def validate_claim(self, claim_text: str) -> Dict[str, Any]:
        """
        Validate that a text is indeed a claim.

        Args:
            claim_text: Text to validate

        Returns:
            Dict with is_valid (bool) and reason (str)
        """
        prompt = f"""Is this text a valid research claim?

Text: "{claim_text}"

A valid claim:
- Asserts something as true or likely
- Makes a testable prediction
- States a conclusion from research
- Makes a normative statement

Respond with JSON:
{{
  "is_valid": true/false,
  "reason": "brief explanation",
  "suggested_type": "empirical/theoretical/predictive/normative/definitional"
}}"""

        try:
            response = await self.ai.generate(
                prompt,
                temperature=0.0,
                response_format='json'
            )
            return json.loads(response)
        except Exception as e:
            logger.error(f"Error validating claim: {e}")
            return {
                "is_valid": False,
                "reason": f"Validation error: {e}",
                "suggested_type": None
            }
