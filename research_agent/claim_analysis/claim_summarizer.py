"""
Claim Summarizer with Qualifier Preservation

Creates concise summaries of claims for UI display while preserving critical qualifiers.
Tracks what was changed and verifies no semantic loss.
"""

import re
import logging
from typing import Dict, List, Tuple, Any
from research_agent.normalization.qualifier_extractor import QualifierExtractor

logger = logging.getLogger(__name__)


class ClaimSummarizer:
    """Summarize claims while preserving qualifiers and semantic meaning."""

    def __init__(self):
        """Initialize summarizer."""
        self.qualifier_extractor = QualifierExtractor()

    def summarize(self, claim_text: str, max_length: int = 100) -> Dict[str, Any]:
        """
        Create a concise summary of a claim.

        Args:
            claim_text: Full claim text
            max_length: Maximum summary length

        Returns:
            {
                'summary': str,
                'original': str,
                'preserved_qualifiers': list,
                'compression_ratio': float,
                'changes_made': list,
                'semantic_verified': bool
            }
        """
        original = claim_text
        summary = claim_text

        # If already short enough, return as-is
        if len(claim_text) <= max_length:
            return {
                'summary': claim_text.strip(),
                'original': original,
                'preserved_qualifiers': [],
                'lost_qualifiers': [],
                'compression_ratio': 1.0,
                'changes_made': [],
                'semantic_verified': True
            }

        # Extract qualifiers BEFORE summarization
        original_qualifiers = self.qualifier_extractor.extract(claim_text)
        changes_made = []

        # 1. Remove redundant phrases
        summary, removed = self._remove_redundancy(summary)
        if removed:
            changes_made.append(f"Removed redundancy: {removed}")

        # 2. Condense verbose constructions
        summary, condensed = self._condense_verbose(summary)
        if condensed:
            changes_made.extend(condensed)

        # 3. Keep only core assertion + qualifiers
        summary = self._extract_core_assertion(summary, original_qualifiers)

        # 4. Smart truncation: Try to break at sentence boundary
        if len(summary) > max_length:
            # Try to find first complete sentence within limit
            sentences = re.split(r'([.!?])\s+', summary)
            truncated = ""
            for i in range(0, len(sentences), 2):
                sent = sentences[i] + (sentences[i+1] if i+1 < len(sentences) else '')
                if len(truncated + sent) <= max_length - 3:
                    truncated += sent
                else:
                    break

            # If we got at least one sentence, use it
            if truncated and len(truncated) > max_length * 0.5:
                summary = truncated.strip()
                changes_made.append(f"Truncated at sentence boundary")
            else:
                # Fall back to word boundary
                summary = summary[:max_length].rsplit(' ', 1)[0] + "..."
                changes_made.append(f"Truncated at word boundary")

        # Verify qualifiers preserved
        summary_qualifiers = self.qualifier_extractor.extract(summary)
        preserved_qualifiers = self._verify_qualifiers_preserved(
            original_qualifiers,
            summary_qualifiers
        )

        semantic_verified = len(preserved_qualifiers) == len(original_qualifiers)

        compression_ratio = len(summary) / len(original) if original else 1.0

        return {
            'summary': summary.strip(),
            'original': original,
            'preserved_qualifiers': preserved_qualifiers,
            'lost_qualifiers': [q for q in original_qualifiers if q not in preserved_qualifiers],
            'compression_ratio': compression_ratio,
            'changes_made': changes_made,
            'semantic_verified': semantic_verified
        }

    def _remove_redundancy(self, text: str) -> Tuple[str, List[str]]:
        """Remove redundant phrases."""
        removed = []

        redundant_patterns = [
            (r'\s+in other words,?\s+', ' '),
            (r'\s+that is to say,?\s+', ' '),
            (r'\s+specifically,?\s+', ' '),
            (r'\s+for example,?\s+', ' '),
            (r'\s+such as\s+', ' '),
        ]

        for pattern, replacement in redundant_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                removed.append(re.search(pattern, text, re.IGNORECASE).group(0))
                text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        return text, removed

    def _condense_verbose(self, text: str) -> Tuple[str, List[str]]:
        """Condense verbose constructions."""
        condensed = []

        condensations = [
            (r'it is (important|necessary|crucial) to note that', ''),
            (r'it should be (noted|mentioned|observed) that', ''),
            (r'one (can|could|may|might) argue that', ''),
            (r'there (is|are|exists?)', ''),
            (r'in the case of', 'for'),
            (r'with regard to', 'regarding'),
            (r'in relation to', 'regarding'),
        ]

        for pattern, replacement in condensations:
            if re.search(pattern, text, re.IGNORECASE):
                condensed.append(f"'{pattern}' → '{replacement}'")
                text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        return text, condensed

    def _extract_core_assertion(
        self,
        text: str,
        qualifiers: List[Dict]
    ) -> str:
        """Extract core assertion with qualifiers."""
        # Find the main clause (subject-verb-object)
        # Keep qualifiers at the beginning

        # Preserve modal qualifiers at start
        modal_prefix = ""
        for qual in qualifiers:
            if qual['type'] == 'modal' and text.lower().startswith(qual['text'].lower()):
                modal_prefix = qual['text'] + " "
                break

        # Remove leading "the fact that", "the notion that", etc.
        text = re.sub(r'^the (fact|notion|idea|concept) that\s+', '', text, flags=re.IGNORECASE)

        return modal_prefix + text

    def _verify_qualifiers_preserved(
        self,
        original_qualifiers: List[Dict],
        summary_qualifiers: List[Dict]
    ) -> List[Dict]:
        """Verify which qualifiers were preserved."""
        preserved = []

        for orig_qual in original_qualifiers:
            # Check if this qualifier appears in summary
            for summ_qual in summary_qualifiers:
                if (summ_qual['text'].lower() == orig_qual['text'].lower() and
                    summ_qual['type'] == orig_qual['type']):
                    preserved.append(orig_qual)
                    break

        return preserved

    def create_hierarchical_summary(
        self,
        parent_claim: str,
        child_claims: List[str]
    ) -> Dict[str, Any]:
        """
        Create summaries for a parent and its children, ensuring non-overlapping.

        Args:
            parent_claim: Parent claim text
            child_claims: List of child claim texts

        Returns:
            {
                'parent_summary': dict,
                'child_summaries': list of dicts,
                'coverage_verified': bool
            }
        """
        # Summarize parent
        parent_summary = self.summarize(parent_claim, max_length=80)

        # Summarize children
        child_summaries = []
        for child in child_claims:
            child_sum = self.summarize(child, max_length=60)
            child_summaries.append(child_sum)

        # Verify coverage (children should not duplicate parent)
        coverage_verified = self._verify_non_overlapping(
            parent_summary['summary'],
            [c['summary'] for c in child_summaries]
        )

        return {
            'parent_summary': parent_summary,
            'child_summaries': child_summaries,
            'coverage_verified': coverage_verified
        }

    def _verify_non_overlapping(
        self,
        parent: str,
        children: List[str]
    ) -> bool:
        """Verify children don't duplicate parent content."""
        parent_words = set(parent.lower().split())

        for child in children:
            child_words = set(child.lower().split())
            overlap = len(parent_words & child_words) / len(child_words) if child_words else 0

            # If >70% overlap, they're duplicative
            if overlap > 0.7:
                return False

        return True


def add_summaries_to_neo4j(db):
    """Add summary properties to all claims in Neo4j."""
    summarizer = ClaimSummarizer()

    # Get all claims
    claims = db.find_nodes('Claim')

    updated_count = 0

    for claim in claims:
        # Create summary
        result = summarizer.summarize(claim['text'], max_length=100)

        # Update claim node with summary
        query = """
        MATCH (c:Claim {id: $claim_id})
        SET c.summary = $summary,
            c.compression_ratio = $compression_ratio,
            c.qualifiers_preserved = $qualifiers_preserved
        """

        with db.driver.session(database=db.database) as session:
            session.run(
                query,
                claim_id=claim['id'],
                summary=result['summary'],
                compression_ratio=result['compression_ratio'],
                qualifiers_preserved=len(result['preserved_qualifiers'])
            )

        updated_count += 1

    logger.info(f"Added summaries to {updated_count} claims")
    return updated_count
