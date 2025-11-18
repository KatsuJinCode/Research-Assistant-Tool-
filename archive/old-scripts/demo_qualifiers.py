#!/usr/bin/env python3
"""
Demonstrate qualifier extraction and preservation on Szasz claims.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from research_agent.normalization.qualifier_extractor import QualifierExtractor

# Sample claims extracted from Szasz's "The Myth of Mental Illness"
SAMPLE_CLAIMS = [
    "Mental illness is not literally a 'thing' — or physical object",
    "There is no such thing as mental illness",
    "Mental illness can exist only in the same sort of way in which other theoretical concepts exist",
    "Familiar theories are in the habit of posing as 'objective truths'",
    "The notion of mental illness is extremely widely used nowadays",
]

def demonstrate_qualifier_extraction():
    """Demonstrate the CRITICAL qualifier extraction system."""

    print("=" * 80)
    print("QUALIFIER EXTRACTION DEMONSTRATION")
    print("From: Thomas Szasz - The Myth of Mental Illness")
    print("=" * 80)
    print()

    extractor = QualifierExtractor()

    for i, claim in enumerate(SAMPLE_CLAIMS, 1):
        print(f"Claim {i}:")
        print(f'  "{claim}"')
        print()

        # Extract qualifiers
        qualifiers = extractor.extract(claim)

        if qualifiers:
            print(f"  [OK] Found {len(qualifiers)} qualifier(s):")
            for q in qualifiers:
                print(f"    • Type: {q['type']}")
                print(f"      Text: '{q['text']}'")
                print(f"      Impact: {q['impact']}")
            print()

            # Analyze claim strength
            analysis = extractor.analyze_claim_strength(claim)
            print(f"  Claim Strength Analysis:")
            print(f"    - Overall strength: {analysis['strength']}")
            print(f"    - Total qualifiers: {analysis['total_qualifiers']}")
            print(f"    - Has temporal constraint: {analysis['has_temporal_constraint']}")
            print()
        else:
            print("  [INFO] No qualifiers found (absolute statement)")
            print()

        print("-" * 80)
        print()

    # Demonstrate verification
    print("=" * 80)
    print("QUALIFIER PRESERVATION VERIFICATION")
    print("=" * 80)
    print()

    original = "Mental illness can exist only in the same sort of way"

    # Good normalization (preserves qualifiers)
    good_normalized = "Mental illness can only exist in the same way"

    # Bad normalization (loses qualifiers)
    bad_normalized = "Mental illness exists in the same way"

    print(f'Original: "{original}"')
    print()

    print(f'[OK] GOOD normalization: "{good_normalized}"')
    result = extractor.verify_preservation(original, good_normalized)
    print(f"  Qualifiers preserved: {result['preserved']}")
    print()

    print(f'[X] BAD normalization: "{bad_normalized}"')
    result = extractor.verify_preservation(original, bad_normalized)
    print(f"  Qualifiers preserved: {result['preserved']}")
    if result['missing']:
        print(f"  Missing qualifiers: {result['missing']}")
        print("  [FAIL] AUTO-FAIL - Normalization rejected!")
    print()

    print("=" * 80)
    print("This demonstrates the CRITICAL qualifier preservation system")
    print("that prevents loss of meaning during claim normalization.")
    print("=" * 80)

if __name__ == '__main__':
    demonstrate_qualifier_extraction()
