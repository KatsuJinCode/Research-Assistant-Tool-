"""
End-to-End Test for Document Upload Flow

This test catches ALL the issues we've been debugging manually:
1. File upload API endpoint
2. Document processor initialization
3. PDF text extraction
4. AI agent claim extraction
5. Database storage
6. WebSocket progress updates

Run this BEFORE manual testing to catch errors early.
"""

import sys
import time
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from research_agent.neo4j_database import Neo4jDatabase
from web_ui.document_processor import LiveDocumentProcessor


def test_document_upload_flow():
    """Test the complete document upload and processing flow."""

    print("=" * 80)
    print("TESTING DOCUMENT UPLOAD FLOW")
    print("=" * 80)

    # Test 1: Database connection
    print("\n[1/6] Testing database connection...")
    try:
        db = Neo4jDatabase()
        stats = db.stats()
        print(f"✓ Database connected: {stats['total_nodes']} nodes")
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False

    # Test 2: Document processor initialization
    print("\n[2/6] Testing document processor initialization...")
    try:
        updates = []

        def progress_callback(message, progress, data):
            updates.append((message, progress, data))
            print(f"  [{progress:.0f}%] {message}")

        processor = LiveDocumentProcessor(progress_callback)
        print(f"✓ Processor initialized")
    except Exception as e:
        print(f"✗ Processor initialization failed: {e}")
        return False

    # Test 3: Check for test PDF
    print("\n[3/6] Checking for test PDF...")
    test_pdf = Path(__file__).parent / "uploads" / "SHORT-The-Myth-of-Mental-Illness - 2-page excerpt.pdf"

    if not test_pdf.exists():
        print(f"✗ Test PDF not found: {test_pdf}")
        print("  Please upload a test PDF first")
        return False

    print(f"✓ Found test PDF: {test_pdf.name}")

    # Test 4: PDF text extraction
    print("\n[4/6] Testing PDF text extraction...")
    try:
        from research_agent.document_processing.pdf_extractor import PDFExtractor
        extractor = PDFExtractor(column_aware=True, postprocess=True)
        extraction_result = extractor.extract(test_pdf)
        text = extraction_result['full_text']

        # Check for null bytes
        if '\x00' in text:
            print(f"✗ PDF text contains null bytes (will break JSON)")
            print(f"  Cleaning null bytes...")
            text = text.replace('\x00', '')
            print(f"✓ Null bytes removed")

        print(f"✓ Extracted {len(text)} characters from PDF")
    except Exception as e:
        print(f"✗ PDF extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test 5: Document processing
    print("\n[5/6] Testing full document processing...")
    print("  This will:")
    print("    - Extract text from PDF")
    print("    - Call AI agent to extract claims")
    print("    - Add claims to database")
    print("    - Emit progress updates via WebSocket")
    print()

    try:
        doc_id = processor.process_document(str(test_pdf))
        print(f"\n✓ Document processed successfully: {doc_id}")
    except Exception as e:
        print(f"\n✗ Document processing failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test 6: Verify database storage
    print("\n[6/6] Verifying database storage...")
    try:
        with db.driver.session(database=db.database) as session:
            # Check document
            doc_result = session.run(
                "MATCH (d:Document {id: $doc_id}) RETURN d.status as status, d.title as title",
                doc_id=doc_id
            ).single()

            if not doc_result:
                print(f"✗ Document not found in database")
                return False

            print(f"✓ Document stored: {doc_result['title']}")
            print(f"  Status: {doc_result['status']}")

            # Check claims
            claim_count = session.run(
                "MATCH (d:Document {id: $doc_id})-[:CONTAINS_CLAIM]->(c:Claim) RETURN count(c) as count",
                doc_id=doc_id
            ).single()['count']

            if claim_count == 0:
                print(f"✗ No claims found for document")
                return False

            print(f"✓ Found {claim_count} claims")

            # Check hierarchical structure
            super_claims = session.run(
                "MATCH (d:Document {id: $doc_id})-[:CONTAINS_CLAIM]->(c:Claim) WHERE c.is_super_claim = true RETURN count(c) as count",
                doc_id=doc_id
            ).single()['count']

            print(f"✓ Found {super_claims} super-claims (categories)")

    except Exception as e:
        print(f"✗ Database verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test 7: Progress updates
    print("\n[7/7] Checking progress updates...")
    if len(updates) == 0:
        print(f"✗ No progress updates received")
        return False

    print(f"✓ Received {len(updates)} progress updates:")
    for i, (msg, prog, data) in enumerate(updates[:5]):
        print(f"    {i+1}. [{prog:.0f}%] {msg}")
    if len(updates) > 5:
        print(f"    ... and {len(updates) - 5} more")

    print("\n" + "=" * 80)
    print("✓ ALL TESTS PASSED")
    print("=" * 80)
    print("\nThe upload flow is working correctly!")
    print("You can now test via the web UI.")

    return True


if __name__ == '__main__':
    success = test_document_upload_flow()
    sys.exit(0 if success else 1)
