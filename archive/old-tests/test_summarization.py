"""
Unit test for claim summarization - shows side-by-side comparison
"""

import sys
import io
from pathlib import Path
from web_ui.document_processor import LiveDocumentProcessor
from research_agent.neo4j_database import Neo4jDatabase

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_summarization():
    """Test claim summarization by showing original vs summarized text."""

    print("=" * 80)
    print("SUMMARIZATION UNIT TEST")
    print("=" * 80)
    print()

    # Initialize components
    print("Initializing database connection...")
    db = Neo4jDatabase()

    print("Initializing document processor...")
    processor = LiveDocumentProcessor(progress_callback=None)

    print()
    print("=" * 80)
    print("FETCHING CLAIMS FROM DATABASE")
    print("=" * 80)
    print()

    # Fetch all claims from database using driver directly
    query = """
    MATCH (c:Claim)
    RETURN c.id as id, c.text as text, c.summary as summary, c.normalized as normalized
    ORDER BY c.id
    LIMIT 10
    """

    with db.driver.session(database=db.database) as session:
        result = session.run(query)
        results = [record.data() for record in result]

    if not results:
        print("❌ NO CLAIMS FOUND IN DATABASE")
        print()
        print("Possible reasons:")
        print("1. No documents have been processed yet")
        print("2. Database connection failed")
        print("3. Claims were not saved to database")
        print()
        return

    print(f"✓ Found {len(results)} claims in database")
    print()

    # Display side-by-side comparison
    for i, record in enumerate(results, 1):
        claim_id = record['id']
        original = record['text']
        simplified = record['summary']
        normalized = record['normalized']

        print("=" * 80)
        print(f"CLAIM #{i}: {claim_id}")
        print("=" * 80)
        print()

        print("📄 ORIGINAL TEXT:")
        print("-" * 80)
        print(original)
        print()
        print(f"   Length: {len(original.split())} words")
        print()

        print("✂️  SIMPLIFIED (5-12 words):")
        print("-" * 80)
        if simplified:
            print(simplified)
            print()
            print(f"   Length: {len(simplified.split())} words")

            # Check for qualifiers
            qualifiers = ['may', 'might', 'can', 'could', 'should', 'would', 'must',
                         'all', 'some', 'few', 'many', 'most', 'likely', 'possibly',
                         'probably', 'suggests', 'indicates', 'appears']

            orig_qualifiers = [q for q in qualifiers if q in original.lower()]
            simp_qualifiers = [q for q in qualifiers if q in simplified.lower()]

            if orig_qualifiers:
                print(f"   Qualifiers in original: {', '.join(orig_qualifiers)}")
                print(f"   Qualifiers in simplified: {', '.join(simp_qualifiers)}")

                missing = set(orig_qualifiers) - set(simp_qualifiers)
                if missing:
                    print(f"   ⚠️  MISSING QUALIFIERS: {', '.join(missing)}")
        else:
            print("❌ NO SIMPLIFIED VERSION")
        print()

        print("📋 NORMALIZED (15-25 words):")
        print("-" * 80)
        if normalized:
            print(normalized)
            print()
            print(f"   Length: {len(normalized.split())} words")
        else:
            print("❌ NO NORMALIZED VERSION")
        print()
        print()

    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total claims tested: {len(results)}")

    claims_with_summary = sum(1 for r in results if r['summary'])
    claims_with_normalized = sum(1 for r in results if r['normalized'])

    print(f"Claims with simplified summary: {claims_with_summary}/{len(results)}")
    print(f"Claims with normalized summary: {claims_with_normalized}/{len(results)}")

    if claims_with_summary == 0:
        print()
        print("❌ CRITICAL: NO SUMMARIES FOUND")
        print("   This means _simplify_claim_with_agent() is NOT being called")
        print("   or summaries are not being saved to the database")

    print()

if __name__ == '__main__':
    test_summarization()
