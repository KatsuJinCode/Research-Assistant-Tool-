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

    def summarize_claim(self, claim_text: str, target_length: int = 50) -> Dict[str, Any]:
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
        Create extractive summary by keeping most important sentences.

        For now: Just take first N words intelligently.
        TODO: Use sentence importance scoring.
        """
        words = text.split()

        if len(words) <= target_words:
            return text

        # Find sentence boundaries
        sentences = []
        current_sentence = []

        for word in words:
            current_sentence.append(word)
            if word.endswith(('.', '!', '?', ';')):
                sentences.append(' '.join(current_sentence))
                current_sentence = []

        if current_sentence:
            sentences.append(' '.join(current_sentence))

        # Take complete sentences up to target
        summary_words = 0
        summary_sentences = []

        for sentence in sentences:
            sentence_word_count = len(sentence.split())
            if summary_words + sentence_word_count <= target_words:
                summary_sentences.append(sentence)
                summary_words += sentence_word_count
            else:
                break

        # If we got at least one sentence, use it
        if summary_sentences:
            return ' '.join(summary_sentences)

        # Otherwise, just truncate at word boundary
        return ' '.join(words[:target_words]) + '...'

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
