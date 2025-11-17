#!/usr/bin/env python3
"""
Demonstrate claim normalization process (simulated without API).
Shows how claims would be analyzed and normalized.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from research_agent.normalization.qualifier_extractor import QualifierExtractor


def simulate_normalization(original, proposed_normalized, extractor):
    """Simulate the normalization process with qualifier verification."""

    print(f"ORIGINAL CLAIM:")
    print(f'  "{original}"')
    print()

    # Extract qualifiers from original
    original_qualifiers = extractor.extract(original)

    if original_qualifiers:
        print(f"Original qualifiers: {len(original_qualifiers)}")
        for q in original_qualifiers:
            print(f"  • {q['type']}: '{q['text']}' ({q['impact']})")
    else:
        print("Original qualifiers: None (absolute statement)")
    print()

    print(f"PROPOSED NORMALIZED:")
    print(f'  "{proposed_normalized}"')
    print()

    # Verify preservation
    verification = extractor.verify_preservation(original, proposed_normalized)

    if verification['preserved']:
        print("✅ QUALIFIER PRESERVATION: PASSED")
        print("   All qualifiers maintained in normalized version")
        confidence = 0.95
    else:
        print("❌ QUALIFIER PRESERVATION: FAILED")
        print(f"   Missing qualifiers: {verification['missing']}")
        print("   Result: AUTO-FAIL - Normalization REJECTED")
        confidence = 0.0

    print(f"\nConfidence score: {confidence:.2f}")
    print(f"Needs human review: {'No' if confidence >= 0.95 else 'Yes'}")

    return verification['preserved'], confidence


def main():
    print("=" * 80)
    print("CLAIM NORMALIZATION DEMONSTRATION")
    print("=" * 80)
    print()

    extractor = QualifierExtractor()

    # Example 1: Claim with qualifier - GOOD normalization
    print("EXAMPLE 1: Successful Normalization (Preserves Qualifier)")
    print("=" * 80)
    print()

    original = "Mental illness can exist only in the same sort of way in which other theoretical concepts exist"
    normalized = "Mental illness can only exist in the same way as other theoretical concepts"

    passed, confidence = simulate_normalization(original, normalized, extractor)

    print()
    print("Analysis: Normalization simplified language while preserving the modal")
    print("          qualifier 'can', maintaining the tentative nature of the claim.")
    print()
    print("-" * 80)
    print()

    # Example 2: Claim with qualifier - BAD normalization
    print("EXAMPLE 2: Failed Normalization (Loses Qualifier)")
    print("=" * 80)
    print()

    original = "Mental illness can exist only in the same sort of way in which other theoretical concepts exist"
    bad_normalized = "Mental illness exists in the same way as other theoretical concepts"

    passed, confidence = simulate_normalization(original, bad_normalized, extractor)

    print()
    print("Analysis: This normalization LOSES the modal 'can', changing the claim")
    print("          from a possibility to a definite statement. This fundamentally")
    print("          alters the meaning and is automatically rejected.")
    print()
    print("-" * 80)
    print()

    # Example 3: Absolute statement - normalization ok
    print("EXAMPLE 3: Absolute Statement Normalization")
    print("=" * 80)
    print()

    original = "Mental illness is not literally a 'thing' — or physical object"
    normalized = "Mental illness is not a physical object"

    passed, confidence = simulate_normalization(original, normalized, extractor)

    print()
    print("Analysis: No qualifiers in original, so simplified normalization is safe.")
    print("          The core claim (mental illness ≠ physical object) is preserved.")
    print()
    print("-" * 80)
    print()

    # Example 4: Complex qualifier statement
    print("EXAMPLE 4: Complex Claim with Multiple Considerations")
    print("=" * 80)
    print()

    original = "The notion of mental illness is extremely widely used nowadays"
    normalized = "The concept of mental illness is widely used today"

    passed, confidence = simulate_normalization(original, normalized, extractor)

    print()
    print("Analysis: While 'extremely' and 'widely' might seem like qualifiers,")
    print("          the qualifier extractor focuses on modal/epistemic qualifiers")
    print("          that affect truth conditions. Intensity adverbs like 'extremely'")
    print("          are tracked separately in normalization validation.")
    print()
    print("-" * 80)
    print()

    print("=" * 80)
    print("NORMALIZATION WORKFLOW")
    print("=" * 80)
    print()
    print("The complete normalization process:")
    print()
    print("1. EXTRACT original qualifiers")
    print("   → Identify all modal, frequency, and quantity qualifiers")
    print()
    print("2. GENERATE normalized version (AI)")
    print("   → Simplify language, standardize phrasing")
    print("   → AI is instructed to preserve ALL qualifiers")
    print()
    print("3. VERIFY qualifier preservation")
    print("   → Extract qualifiers from normalized version")
    print("   → Compare with original qualifier set")
    print("   → AUTO-FAIL if ANY qualifier is missing")
    print()
    print("4. CALCULATE confidence")
    print("   → High (0.95+): Qualifiers preserved, minimal changes")
    print("   → Medium (0.60-0.94): Preserved but significant rewording")
    print("   → Low (<0.60): Failed preservation or high uncertainty")
    print()
    print("5. HUMAN-IN-THE-LOOP review")
    print("   → Required for confidence < 0.95")
    print("   → Human can accept, reject, or manually edit")
    print("   → System learns from human corrections")
    print()
    print("=" * 80)
    print("CRITICAL SAFEGUARD")
    print("=" * 80)
    print()
    print("The auto-fail mechanism ensures:")
    print()
    print("  ✓ Modal qualifiers (can, may, might, etc.) are NEVER lost")
    print("  ✓ Frequency qualifiers (always, never, often, etc.) are preserved")
    print("  ✓ Quantity qualifiers (all, some, most, etc.) remain intact")
    print()
    print("This prevents catastrophic meaning changes like:")
    print("  ✗ 'X may cause Y' → 'X causes Y'")
    print("  ✗ 'Some evidence suggests' → 'Evidence shows'")
    print("  ✗ 'Often associated with' → 'Associated with'")
    print()
    print("=" * 80)


if __name__ == '__main__':
    main()
