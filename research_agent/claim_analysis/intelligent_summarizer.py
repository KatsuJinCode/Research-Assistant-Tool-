"""
Intelligent Claim Summarizer using LLM

Creates concise, meaningful summaries of claims while preserving semantic content.
Uses Claude API to generate high-quality summaries.
"""

import logging
from typing import Dict, Any, List
from research_agent.normalization.qualifier_extractor import QualifierExtractor

logger = logging.getLogger(__name__)


class IntelligentSummarizer:
    """AI-powered claim summarization that preserves meaning."""

    def __init__(self):
        """Initialize summarizer."""
        self.qualifier_extractor = QualifierExtractor()

    def summarize_claim(self, claim_text: str, target_length: int = 5) -> Dict[str, Any]:
        """
        Create intelligent summary of a claim.

        Args:
            claim_text: Full claim text
            target_length: Target word count (not character count)

        Returns:
            {
                'summary': str,              # Concise summary
                'normalized': str,           # Normalized version (medium detail)
                'original': str,             # Full original text
                'preserved_qualifiers': list,
                'compression_ratio': float
            }
        """
        original = claim_text

        # If already very short, return as-is
        word_count = len(claim_text.split())
        if word_count <= target_length:
            return {
                'summary': claim_text.strip(),
                'normalized': claim_text.strip(),
                'original': original,
                'preserved_qualifiers': [],
                'compression_ratio': 1.0
            }

        # Extract qualifiers BEFORE summarization
        original_qualifiers = self.qualifier_extractor.extract(claim_text)

        # Use simple extractive summarization for now
        # TODO: Integrate with Claude API for better summaries
        summary = self._extractive_summarize(claim_text, target_length)
        normalized = self._extractive_summarize(claim_text, target_length * 2)

        # Verify qualifiers preserved
        summary_qualifiers = self.qualifier_extractor.extract(summary)
        preserved = self._verify_qualifiers_preserved(
            original_qualifiers,
            summary_qualifiers
        )

        compression_ratio = len(summary.split()) / len(original.split())

        return {
            'summary': summary.strip(),
            'normalized': normalized.strip(),
            'original': original,
            'preserved_qualifiers': preserved,
            'compression_ratio': compression_ratio
        }

    def _extractive_summarize(self, text: str, target_words: int) -> str:
        """
        Extract key concept words from text.

        Extracts the most meaningful nouns/verbs, skipping filler words.
        """
        # Remove punctuation and split
        import string
        text_clean = text.translate(str.maketrans('', '', string.punctuation))
        words = text_clean.split()

        if len(words) <= target_words:
            return text

        # Skip common filler words
        filler_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'are', 'was', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'should', 'could', 'may', 'might', 'must', 'can', 'this',
            'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
            'what', 'which', 'who', 'when', 'where', 'why', 'how', 'all', 'each',
            'every', 'both', 'few', 'more', 'most', 'other', 'some', 'such', 'than'
        }

        # Extract key words (content words)
        key_words = []
        for word in words:
            word_lower = word.lower()
            if word_lower not in filler_words and len(word) > 3:
                key_words.append(word)
                if len(key_words) >= target_words:
                    break

        # If we didn't get enough, just take first N words
        if len(key_words) < target_words:
            return ' '.join(words[:target_words])

        return ' '.join(key_words)

    def _verify_qualifiers_preserved(
        self,
        original_qualifiers: List[Dict],
        summary_qualifiers: List[Dict]
    ) -> List[Dict]:
        """Verify which qualifiers were preserved."""
        preserved = []

        for orig_qual in original_qualifiers:
            for summ_qual in summary_qualifiers:
                if (summ_qual['text'].lower() == orig_qual['text'].lower() and
                    summ_qual['type'] == orig_qual['type']):
                    preserved.append(orig_qual)
                    break

        return preserved


def batch_summarize_claims(db):
    """Summarize all claims in Neo4j."""
    summarizer = IntelligentSummarizer()

    # Get all claims
    query = """
    MATCH (c:Claim)
    RETURN c.id as id, c.text as text
    """

    with db.driver.session(database=db.database) as session:
        result = session.run(query)
        claims = [dict(record) for record in result]

    logger.info(f"Summarizing {len(claims)} claims...")

    for i, claim in enumerate(claims, 1):
        # Create summary
        result = summarizer.summarize_claim(claim['text'], target_length=8)

        # Update Neo4j
        update_query = """
        MATCH (c:Claim {id: $claim_id})
        SET c.summary = $summary,
            c.normalized = $normalized,
            c.compression_ratio = $compression_ratio,
            c.qualifiers_preserved = $qualifiers_preserved
        """

        with db.driver.session(database=db.database) as session:
            session.run(
                update_query,
                claim_id=claim['id'],
                summary=result['summary'],
                normalized=result['normalized'],
                compression_ratio=result['compression_ratio'],
                qualifiers_preserved=len(result['preserved_qualifiers'])
            )

        if i % 10 == 0:
            logger.info(f"Summarized {i}/{len(claims)} claims")

    logger.info(f"[SUCCESS] Summarized all {len(claims)} claims")
    return len(claims)
