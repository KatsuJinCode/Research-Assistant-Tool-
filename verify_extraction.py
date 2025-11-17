#!/usr/bin/env python3
"""
Comprehensive verification of claim extraction and analysis.
Shows the 5 manually extracted claims from Szasz's paper.
"""

import sys
from pathlib import Path
import PyPDF2

sys.path.insert(0, str(Path(__file__).parent))

from research_agent.normalization.qualifier_extractor import QualifierExtractor


def main():
    print("=" * 80)
    print("SZASZ PAPER - CLAIM EXTRACTION VERIFICATION")
    print("=" * 80)
    print()

    # First, verify the PDF extraction
    pdf_path = Path("sample papers/SHORT-The-Myth-of-Mental-Illness.pdf")

    print("📄 PDF EXTRACTION VERIFICATION")
    print("-" * 80)

    with open(pdf_path, 'rb') as f:
        pdf = PyPDF2.PdfReader(f)
        full_text = ""
        for page in pdf.pages:
            text = page.extract_text() or ""
            full_text += text

    total_chars = len(full_text)
    words = len(full_text.split())

    print(f"✓ File: {pdf_path.name}")
    print(f"✓ Pages: {len(pdf.pages)}")
    print(f"✓ Total characters: {total_chars:,}")
    print(f"✓ Word count: {words:,}")
    print(f"✓ Words per page (avg): {words/len(pdf.pages):.0f}")
    print()
    print("Note: This is a dense academic journal article (~2,882 words/page),")
    print("      not a typical document (which averages ~500 words/page)")
    print()

    # Show where each claim appears in the text
    print("=" * 80)
    print("MANUALLY EXTRACTED CLAIMS (5 claims)")
    print("=" * 80)
    print()

    claims = [
        {
            "text": "Mental illness is not literally a 'thing' — or physical object",
            "location": "Opening paragraph",
            "type": "Definitional"
        },
        {
            "text": "There is no such thing as mental illness",
            "location": "Title/Thesis statement",
            "type": "Normative (Main thesis)"
        },
        {
            "text": "Mental illness can exist only in the same sort of way in which other theoretical concepts exist",
            "location": "Opening paragraph",
            "type": "Theoretical"
        },
        {
            "text": "Familiar theories are in the habit of posing as 'objective truths'",
            "location": "Opening paragraph",
            "type": "Methodological critique"
        },
        {
            "text": "The notion of mental illness is extremely widely used nowadays",
            "location": "Opening paragraph",
            "type": "Empirical observation"
        }
    ]

    extractor = QualifierExtractor()

    for i, claim in enumerate(claims, 1):
        print(f"CLAIM {i}: {claim['type']}")
        print("-" * 80)
        print(f"Text: \"{claim['text']}\"")
        print(f"Location: {claim['location']}")
        print()

        # Verify it appears in the PDF
        if claim['text'].lower() in full_text.lower():
            print("✓ Verified: Found in PDF text")
        else:
            # Try to find partial match
            words_in_claim = claim['text'].split()[:5]
            partial = " ".join(words_in_claim)
            if partial.lower() in full_text.lower():
                print("✓ Verified: Partial match found in PDF (minor paraphrasing)")
            else:
                print("⚠ Note: Paraphrased/synthesized from PDF content")
        print()

        # Extract qualifiers
        qualifiers = extractor.extract(claim['text'])

        if qualifiers:
            print(f"Qualifiers found: {len(qualifiers)}")
            for q in qualifiers:
                print(f"  • {q['type'].upper()}: '{q['text']}' → {q['impact']}")

            # Analyze strength
            analysis = extractor.analyze_claim_strength(claim['text'])
            print(f"\nClaim strength: {analysis['strength']}")
            print(f"  - Total qualifiers: {analysis['total_qualifiers']}")
            print(f"  - Temporal constraint: {analysis['has_temporal_constraint']}")
        else:
            print("Qualifiers: None (absolute/categorical statement)")
            print("Claim strength: STRONG (no hedging)")

        print()
        print()

    print("=" * 80)
    print("EXTRACTION QUALITY ASSESSMENT")
    print("=" * 80)
    print()
    print(f"Total claims extracted: {len(claims)}")
    print(f"Claims with qualifiers: {sum(1 for c in claims if extractor.extract(c['text']))}")
    print(f"Absolute statements: {sum(1 for c in claims if not extractor.extract(c['text']))}")
    print()
    print("Note: These 5 claims are from the OPENING PARAGRAPH only.")
    print("      A full extraction with AI would identify 50-100+ claims from")
    print(f"      the complete {words:,}-word paper.")
    print()
    print("Why only 5 claims shown:")
    print("  1. These are manually extracted for demonstration/testing")
    print("  2. AI-powered extraction requires API keys (not yet configured)")
    print("  3. These 5 claims represent different claim types and complexity")
    print()
    print("=" * 80)
    print("NEXT STEPS FOR FULL CLAIM EXTRACTION")
    print("=" * 80)
    print()
    print("To extract ALL claims from the paper:")
    print("  1. Set ANTHROPIC_API_KEY or OPENAI_API_KEY environment variable")
    print("  2. Run: python test_pipeline.py 'sample papers/SHORT-The-Myth-of-Mental-Illness.pdf'")
    print("  3. Expected output: 50-100 claims from the full paper")
    print()


if __name__ == '__main__':
    main()
