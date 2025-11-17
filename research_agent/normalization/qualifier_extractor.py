"""
Qualifier extraction - CRITICAL component for claim normalization.

Extracts and preserves qualifier terms (modals, quantifiers, frequency adverbs, etc.)
that MUST be preserved during normalization.
"""

import re
import logging
from typing import List, Dict, Set


logger = logging.getLogger(__name__)


class QualifierExtractor:
    """
    Extract qualifier terms that MUST be preserved.

    Qualifiers include:
    - Modals: can, could, may, might, will, would, shall, should, must
    - Frequency: always, never, often, rarely, sometimes, usually, mostly, typically
    - Quantity: all, every, each, some, most, many, few, several, none, any
    - Certainty: certainly, probably, possibly, likely, unlikely, perhaps, maybe
    - Temporal: by 2030, until 2025, before 2040, after 2020, etc.
    """

    # Comprehensive qualifier lists (case-insensitive matching)
    MODALS = [
        'can', 'could', 'may', 'might', 'will', 'would',
        'shall', 'should', 'must', 'ought'
    ]

    FREQUENCY = [
        'always', 'never', 'often', 'rarely', 'sometimes', 'usually',
        'generally', 'frequently', 'occasionally', 'seldom', 'mostly',
        'typically', 'commonly', 'regularly', 'constantly', 'continually'
    ]

    QUANTITY = [
        'all', 'every', 'each', 'some', 'most', 'many', 'few',
        'several', 'none', 'any', 'multiple', 'numerous', 'countless',
        'various', 'certain', 'particular'
    ]

    CERTAINTY = [
        'certainly', 'probably', 'possibly', 'likely', 'unlikely',
        'perhaps', 'maybe', 'definitely', 'surely', 'potentially',
        'presumably', 'apparently', 'evidently', 'arguably'
    ]

    def extract(self, claim_text: str) -> List[Dict[str, str]]:
        """
        Extract all qualifiers from claim text.

        Args:
            claim_text: Claim text to analyze

        Returns:
            List of qualifier dicts with:
                - type: Qualifier type
                - text: Qualifier word/phrase
                - impact: Semantic impact description
        """
        qualifiers = []

        # Extract modals
        for modal in self.MODALS:
            if re.search(rf'\b{modal}\b', claim_text, re.I):
                qualifiers.append({
                    'type': 'modal',
                    'text': modal,
                    'impact': self._modal_impact(modal)
                })

        # Extract frequency adverbs
        for freq in self.FREQUENCY:
            if re.search(rf'\b{freq}\b', claim_text, re.I):
                qualifiers.append({
                    'type': 'frequency',
                    'text': freq,
                    'impact': f'indicates_{freq}_occurrence'
                })

        # Extract quantity markers
        for quant in self.QUANTITY:
            if re.search(rf'\b{quant}\b', claim_text, re.I):
                qualifiers.append({
                    'type': 'quantity',
                    'text': quant,
                    'impact': self._quantity_impact(quant)
                })

        # Extract certainty markers
        for cert in self.CERTAINTY:
            if re.search(rf'\b{cert}\b', claim_text, re.I):
                qualifiers.append({
                    'type': 'certainty',
                    'text': cert,
                    'impact': f'indicates_{cert}_level'
                })

        # Extract percentages
        percentages = re.findall(
            r'\b(\d+(?:\.\d+)?)\s*(?:%|percent)\b',
            claim_text,
            re.I
        )
        for pct in percentages:
            qualifiers.append({
                'type': 'quantity',
                'text': f'{pct}%',
                'impact': f'indicates_{pct}_percent'
            })

        # Extract temporal markers (years)
        temporal_patterns = [
            r'\b(by|until|before|after|in|during)\s+(\d{4})\b',
            r'\b(by|until|before|after|in|during)\s+(early|mid|late)\s+(\d{4})s?\b',
        ]

        for pattern in temporal_patterns:
            matches = re.findall(pattern, claim_text, re.I)
            for match in matches:
                if len(match) == 2:  # Simple: "by 2030"
                    prep, year = match
                    text = f'{prep} {year}'
                else:  # Complex: "by mid 2030s"
                    prep, period, year = match
                    text = f'{prep} {period} {year}s'

                qualifiers.append({
                    'type': 'temporal',
                    'text': text,
                    'impact': f'time_constraint_{text.replace(" ", "_")}'
                })

        logger.debug(f"Extracted {len(qualifiers)} qualifiers from: {claim_text[:100]}...")
        return qualifiers

    def _modal_impact(self, modal: str) -> str:
        """Get semantic impact description for modal."""
        impacts = {
            'can': 'indicates_possibility',
            'could': 'indicates_conditional_possibility',
            'may': 'indicates_permission_or_possibility',
            'might': 'indicates_low_probability',
            'will': 'indicates_future_certainty',
            'would': 'indicates_conditional_certainty',
            'shall': 'indicates_obligation',
            'should': 'indicates_obligation_or_expectation',
            'must': 'indicates_necessity',
            'ought': 'indicates_moral_obligation'
        }
        return impacts.get(modal.lower(), 'indicates_modality')

    def _quantity_impact(self, quantity: str) -> str:
        """Get semantic impact description for quantity."""
        impacts = {
            'all': 'universal_quantification',
            'every': 'universal_quantification',
            'each': 'individual_universal_quantification',
            'some': 'existential_quantification',
            'most': 'majority_quantification',
            'many': 'large_quantity',
            'few': 'small_quantity',
            'several': 'moderate_quantity',
            'none': 'negation',
            'any': 'unrestricted_quantification'
        }
        return impacts.get(quantity.lower(), 'quantity_modifier')

    def verify_preservation(self, original: str, normalized: str) -> Dict[str, any]:
        """
        Verify all qualifiers from original appear in normalized.

        CRITICAL: Auto-fail normalization if any qualifier lost.

        Args:
            original: Original claim text
            normalized: Normalized claim text

        Returns:
            Dict with:
                - preserved: bool (True if all qualifiers present)
                - missing: List of missing qualifiers
                - original_qualifiers: List of original qualifiers
                - normalized_qualifiers: List of normalized qualifiers
        """
        original_qualifiers = self.extract(original)
        normalized_qualifiers = self.extract(normalized)

        # Create sets of qualifier texts (case-insensitive)
        original_texts = {q['text'].lower() for q in original_qualifiers}
        normalized_texts = {q['text'].lower() for q in normalized_qualifiers}

        # Find missing qualifiers
        missing = original_texts - normalized_texts

        preserved = len(missing) == 0

        if not preserved:
            logger.error(
                f"[FAIL] QUALIFIER LOSS DETECTED\n"
                f"Original: {original}\n"
                f"Normalized: {normalized}\n"
                f"Missing qualifiers: {missing}"
            )
        else:
            logger.info(
                f"[OK] All qualifiers preserved in normalization"
            )

        return {
            'preserved': preserved,
            'missing': list(missing),
            'original_qualifiers': original_qualifiers,
            'normalized_qualifiers': normalized_qualifiers
        }

    def get_qualifier_texts(self, claim_text: str) -> List[str]:
        """
        Get list of qualifier words from text.

        Args:
            claim_text: Claim text

        Returns:
            List of qualifier words
        """
        qualifiers = self.extract(claim_text)
        return [q['text'] for q in qualifiers]

    def count_qualifiers(self, claim_text: str) -> Dict[str, int]:
        """
        Count qualifiers by type.

        Args:
            claim_text: Claim text

        Returns:
            Dict mapping type -> count
        """
        qualifiers = self.extract(claim_text)
        counts = {}
        for q in qualifiers:
            qtype = q['type']
            counts[qtype] = counts.get(qtype, 0) + 1
        return counts

    def has_strong_modals(self, claim_text: str) -> bool:
        """
        Check if claim has strong modals (will, must, shall).

        Args:
            claim_text: Claim text

        Returns:
            True if strong modals present
        """
        strong_modals = ['will', 'must', 'shall']
        qualifiers = self.extract(claim_text)
        return any(
            q['type'] == 'modal' and q['text'] in strong_modals
            for q in qualifiers
        )

    def has_weak_modals(self, claim_text: str) -> bool:
        """
        Check if claim has weak modals (may, might, could).

        Args:
            claim_text: Claim text

        Returns:
            True if weak modals present
        """
        weak_modals = ['may', 'might', 'could', 'possibly']
        qualifiers = self.extract(claim_text)
        return any(
            q['type'] in ['modal', 'certainty'] and q['text'] in weak_modals
            for q in qualifiers
        )

    def analyze_claim_strength(self, claim_text: str) -> Dict[str, any]:
        """
        Analyze claim strength based on qualifiers.

        Args:
            claim_text: Claim text

        Returns:
            Dict with strength analysis
        """
        qualifiers = self.extract(claim_text)
        counts = self.count_qualifiers(claim_text)

        # Determine claim strength
        has_strong = self.has_strong_modals(claim_text)
        has_weak = self.has_weak_modals(claim_text)

        if has_strong and not has_weak:
            strength = 'strong'
        elif has_weak and not has_strong:
            strength = 'weak'
        elif has_strong and has_weak:
            strength = 'mixed'
        else:
            strength = 'neutral'

        return {
            'strength': strength,
            'total_qualifiers': len(qualifiers),
            'counts_by_type': counts,
            'has_temporal_constraint': 'temporal' in counts,
            'has_percentage': any(
                '%' in q['text'] for q in qualifiers
            )
        }
