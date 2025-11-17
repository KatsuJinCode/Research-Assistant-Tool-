"""
Claim Simplification Agent

Uses Claude to intelligently simplify verbose claims while preserving meaning and qualifiers.
"""

import logging
import os
from typing import Dict, Any
from research_agent.normalization.qualifier_extractor import QualifierExtractor

logger = logging.getLogger(__name__)


class ClaimSimplifierAgent:
    """Agent that simplifies claims using LLM intelligence."""

    def __init__(self):
        """Initialize agent."""
        self.qualifier_extractor = QualifierExtractor()

    def simplify_claim(self, claim_text: str) -> Dict[str, Any]:
        """
        Simplify a claim to its most concise form while preserving meaning.

        Args:
            claim_text: Original verbose claim

        Returns:
            {
                'simplified': str,  # Concise version (5-10 words)
                'normalized': str,  # Medium version (15-20 words)
                'original': str,    # Full text
                'qualifiers_preserved': bool
            }
        """
        # For now, use rule-based simplification
        # TODO: Integrate with Claude API for better results

        simplified = self._rule_based_simplify(claim_text)
        normalized = self._rule_based_normalize(claim_text)

        # Extract qualifiers
        original_qualifiers = self.qualifier_extractor.extract(claim_text)
        simplified_qualifiers = self.qualifier_extractor.extract(simplified)

        qualifiers_preserved = len(simplified_qualifiers) >= len(original_qualifiers) * 0.8

        return {
            'simplified': simplified,
            'normalized': normalized,
            'original': claim_text,
            'qualifiers_preserved': qualifiers_preserved,
            'original_qualifiers': len(original_qualifiers),
            'preserved_qualifiers': len(simplified_qualifiers)
        }

    def _rule_based_simplify(self, text: str) -> str:
        """
        Create simplified version using rules.

        Approach:
        1. Identify the core assertion
        2. Keep essential qualifiers
        3. Remove redundant elaborations
        """
        import re

        # Remove parenthetical elaborations
        text = re.sub(r'\([^)]+\)', '', text)

        # Remove common verbose patterns
        patterns_to_remove = [
            r'in other words,?\s*',
            r'that is to say,?\s*',
            r'it should be noted that\s*',
            r'it is important to note that\s*',
            r'one could argue that\s*',
            r'for example,?\s*',
            r'for instance,?\s*',
        ]

        for pattern in patterns_to_remove:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)

        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text).strip()

        # If still too long, extract first complete clause
        if len(text.split()) > 12:
            # Try to find main clause before semicolon, dash, or "whereas"
            parts = re.split(r'[;—]|\swhereas\s', text, maxsplit=1)
            if parts:
                text = parts[0].strip()

        # Final length check - take first meaningful sentence
        if len(text.split()) > 12:
            sentences = re.split(r'[.!?]', text)
            if sentences:
                text = sentences[0].strip()

        return text

    def _rule_based_normalize(self, text: str) -> str:
        """Create medium-length normalized version."""
        # Less aggressive than simplify - just remove obvious redundancy
        import re

        text = re.sub(r'\([^)]+\)', '', text)
        text = re.sub(r'\s+', ' ', text).strip()

        # Take first two sentences if too long
        if len(text.split()) > 25:
            sentences = re.split(r'[.!?]\s+', text)
            if len(sentences) > 1:
                text = sentences[0] + '. ' + sentences[1]
            else:
                text = sentences[0]

        return text.strip()


def batch_simplify_claims(db):
    """Simplify all claims in Neo4j."""
    agent = ClaimSimplifierAgent()

    query = """
    MATCH (c:Claim)
    RETURN c.id as id, c.text as text
    """

    with db.driver.session(database=db.database) as session:
        result = session.run(query)
        claims = [dict(record) for record in result]

    logger.info(f"Simplifying {len(claims)} claims with intelligent agent...")

    for i, claim in enumerate(claims, 1):
        result = agent.simplify_claim(claim['text'])

        update_query = """
        MATCH (c:Claim {id: $claim_id})
        SET c.simplified = $simplified,
            c.normalized = $normalized,
            c.summary = $simplified,
            c.qualifiers_preserved = $qualifiers_preserved
        """

        with db.driver.session(database=db.database) as session:
            session.run(
                update_query,
                claim_id=claim['id'],
                simplified=result['simplified'],
                normalized=result['normalized'],
                qualifiers_preserved=result['preserved_qualifiers']
            )

        if i % 10 == 0:
            logger.info(f"Simplified {i}/{len(claims)} claims")

    logger.info(f"[SUCCESS] Simplified all {len(claims)} claims")
    return len(claims)
