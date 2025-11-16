#!/usr/bin/env python3
"""
Simple test script to demonstrate the Research Verification Agent System pipeline
without requiring full database setup.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from research_agent.document_processing.pdf_extractor import PDFExtractor
from research_agent.document_processing.claim_extractor import ClaimExtractor
from research_agent.normalization.qualifier_extractor import QualifierExtractor
from research_agent.normalization.normalizer import ClaimNormalizer
from research_agent.utils.ai_client import AIClient


async def test_pipeline(pdf_path: str):
    """Test the pipeline with a PDF file."""

    print("=" * 80)
    print("RESEARCH VERIFICATION AGENT SYSTEM - PIPELINE TEST")
    print("=" * 80)
    print()

    # Step 1: Extract PDF
    print("📄 Step 1: Extracting PDF...")
    print("-" * 80)

    extractor = PDFExtractor()
    pdf_result = extractor.extract(Path(pdf_path))

    print(f"✓ Title: {pdf_result['metadata'].get('title', 'N/A')}")
    print(f"✓ Pages: {pdf_result['page_count']}")
    print(f"✓ Total characters: {pdf_result['total_chars']:,}")
    print()

    # Show first 500 characters
    print("Preview (first 500 chars):")
    print(pdf_result['full_text'][:500])
    print("...\n")

    # Step 2: Extract claims (requires AI - skip if no API key)
    print("🔍 Step 2: Extracting Claims (requires AI API key)...")
    print("-" * 80)

    # Check for API key in environment
    import os
    api_key = os.getenv('ANTHROPIC_API_KEY') or os.getenv('OPENAI_API_KEY')

    if not api_key:
        print("⚠️  No API key found in environment variables")
        print("   Set ANTHROPIC_API_KEY or OPENAI_API_KEY to test claim extraction")
        print()
        print("Skipping AI-dependent steps...")
        return

    # Use Anthropic if available, otherwise OpenAI
    provider = 'anthropic' if os.getenv('ANTHROPIC_API_KEY') else 'openai'
    model = 'claude-3-5-sonnet-20241022' if provider == 'anthropic' else 'gpt-4-turbo'

    ai_client = AIClient(
        provider=provider,
        api_key=api_key,
        model=model,
        temperature=0.5
    )

    claim_extractor = ClaimExtractor(ai_client)
    claims = await claim_extractor.extract_claims(pdf_result['full_text'], max_length=4000)

    print(f"✓ Extracted {len(claims)} claims")
    print()

    # Display claims
    for i, claim in enumerate(claims[:5], 1):  # Show first 5
        print(f"Claim {i}:")
        print(f"  Text: {claim['text'][:100]}...")
        print(f"  Type: {claim.get('type', 'unknown')}")
        print(f"  Confidence: {claim.get('confidence', 0):.2f}")
        print()

    if len(claims) > 5:
        print(f"... and {len(claims) - 5} more claims")
        print()

    # Step 3: Analyze qualifiers
    print("🔬 Step 3: Analyzing Qualifiers...")
    print("-" * 80)

    qualifier_extractor = QualifierExtractor()

    for i, claim in enumerate(claims[:3], 1):  # Analyze first 3
        print(f"Claim {i}: {claim['text'][:80]}...")
        qualifiers = qualifier_extractor.extract(claim['text'])

        if qualifiers:
            print(f"  Qualifiers found: {len(qualifiers)}")
            for q in qualifiers:
                print(f"    - {q['type']}: '{q['text']}' ({q['impact']})")
        else:
            print("  No qualifiers found")
        print()

    # Step 4: Normalize first claim
    if claims:
        print("✨ Step 4: Normalizing First Claim...")
        print("-" * 80)

        first_claim = claims[0]['text']
        print(f"Original: {first_claim}")
        print()

        normalizer = ClaimNormalizer(ai_client)
        result = await normalizer.normalize(first_claim)

        print(f"Normalized: {result['normalized_text']}")
        print(f"Qualifiers preserved: {'✓' if result['qualifiers_preserved'] else '✗ FAILED'}")
        print(f"Confidence: {result['confidence']:.2f}")
        print(f"Needs human review: {'Yes' if result['needs_human_review'] else 'No'}")

        if result['qualifiers']:
            print(f"\nPreserved qualifiers:")
            for q in result['qualifiers']:
                print(f"  - {q['text']}")
        print()

    print("=" * 80)
    print("✓ PIPELINE TEST COMPLETE")
    print("=" * 80)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python test_pipeline.py <pdf_path>")
        sys.exit(1)

    pdf_path = sys.argv[1]

    if not Path(pdf_path).exists():
        print(f"Error: PDF file not found: {pdf_path}")
        sys.exit(1)

    asyncio.run(test_pipeline(pdf_path))
