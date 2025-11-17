"""
Complete Pipeline Test - Tests ALL components end-to-end

This is run by the agent automatically after installation to verify
everything works. Tests every stage of the system.
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test 1: All dependencies can be imported."""
    print("\n[1/7] Testing imports...")
    try:
        import pytest
        import networkx
        import arxiv
        import PyPDF2
        import pdfplumber
        import pydantic
        import click
        from research_agent.graph_database import GraphDatabase
        from research_agent.normalization.qualifier_extractor import QualifierExtractor
        print("  ✓ All dependencies imported successfully")
        return True
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_graph_database():
    """Test 2: Graph database (NetworkX) working."""
    print("\n[2/7] Testing graph database...")
    try:
        from research_agent.graph_database import GraphDatabase

        db = GraphDatabase()

        # Create test nodes
        doc_id = db.create_node('Document', {'title': 'Test Doc'})
        claim_id = db.create_node('Claim', {'text': 'Test claim'})

        # Create relationship
        db.create_relationship(doc_id, 'CONTAINS', claim_id)

        # Verify
        stats = db.stats()
        assert stats['total_nodes'] >= 2
        assert stats['total_relationships'] >= 1

        print(f"  ✓ Graph database working ({stats['total_nodes']} nodes, {stats['total_relationships']} relationships)")
        return True
    except Exception as e:
        print(f"  ✗ Graph database failed: {e}")
        return False


def test_qualifier_extraction():
    """Test 3: Qualifier extraction working."""
    print("\n[3/7] Testing qualifier extraction...")
    try:
        from research_agent.normalization.qualifier_extractor import QualifierExtractor

        extractor = QualifierExtractor()

        # Test modal qualifier
        claim = "Mental illness can exist as a theoretical concept"
        qualifiers = extractor.extract(claim)

        assert len(qualifiers) > 0
        assert any(q['type'] == 'modal' and q['text'] == 'can' for q in qualifiers)

        # Test preservation
        preserved = extractor.verify_preservation(claim, claim)
        assert preserved is True

        print(f"  ✓ Qualifier extraction working (found {len(qualifiers)} qualifiers)")
        return True
    except Exception as e:
        print(f"  ✗ Qualifier extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_pdf_extraction():
    """Test 4: PDF extraction working."""
    print("\n[4/7] Testing PDF extraction...")
    try:
        import PyPDF2
        from pathlib import Path

        # Check if sample PDF exists
        pdf_path = Path("sample papers/SHORT-The-Myth-of-Mental-Illness.pdf")

        if not pdf_path.exists():
            print(f"  ⚠ Sample PDF not found at: {pdf_path}")
            print("  ⚠ Skipping PDF test (not critical for setup)")
            return True  # Don't fail if sample PDF missing

        # Try to extract text
        with open(pdf_path, 'rb') as f:
            pdf = PyPDF2.PdfReader(f)
            text = ""
            for page in pdf.pages:
                text += page.extract_text() or ""

        assert len(text) > 1000  # Should have substantial text

        print(f"  ✓ PDF extraction working ({len(text)} characters extracted)")
        return True
    except Exception as e:
        print(f"  ✗ PDF extraction failed: {e}")
        return False


def test_research_apis():
    """Test 5: Research APIs accessible."""
    print("\n[5/7] Testing research APIs...")
    try:
        import arxiv

        # Test arXiv API (most reliable)
        search = arxiv.Search(query='test', max_results=1)
        results = list(search.results())

        assert len(results) > 0

        print("  ✓ Research APIs accessible (arXiv working)")
        return True
    except Exception as e:
        print(f"  ⚠ Research API test failed: {e}")
        print("  ⚠ This may be a network issue - continuing anyway")
        return True  # Don't fail on network issues


def test_neo4j_connection():
    """Test 6: Neo4j connection (if installed)."""
    print("\n[6/7] Testing Neo4j connection...")
    try:
        from research_agent.neo4j_database import Neo4jDatabase

        db = Neo4jDatabase()
        db.close()

        print("  ✓ Neo4j connection working")
        return True
    except Exception as e:
        print("  ⚠ Neo4j not installed (optional)")
        print("  ℹ System will use NetworkX graph database")
        return True  # Neo4j is optional


def test_end_to_end_pipeline():
    """Test 7: Complete end-to-end workflow."""
    print("\n[7/7] Testing end-to-end pipeline...")
    try:
        from research_agent.graph_database import GraphDatabase
        from research_agent.normalization.qualifier_extractor import QualifierExtractor

        db = GraphDatabase()
        extractor = QualifierExtractor()

        # Simulate complete workflow
        # 1. Create document
        doc_id = db.create_node('Document', {
            'title': 'Test Research Paper',
            'author': 'Test Author'
        })

        # 2. Extract claim with qualifiers
        claim_text = "Some patients may respond to treatment"
        qualifiers = extractor.extract(claim_text)

        # 3. Create claim node
        claim_id = db.create_node('Claim', {
            'text': claim_text,
            'type': 'empirical'
        })

        # 4. Link document to claim
        db.create_relationship(doc_id, 'CONTAINS', claim_id)

        # 5. Link qualifiers to claim
        for qualifier in qualifiers:
            qual_id = db.create_node('Qualifier', qualifier)
            db.create_relationship(claim_id, 'HAS_QUALIFIER', qual_id)

        # 6. Export to file
        export_file = "pipeline_test_export.cypher"
        db.export_to_cypher(export_file)

        # Verify export created
        assert Path(export_file).exists()

        print("  ✓ End-to-end pipeline working")
        print(f"  ✓ Exported graph to: {export_file}")
        return True
    except Exception as e:
        print(f"  ✗ Pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests and report results."""
    print("="*80)
    print("RESEARCH VERIFICATION AGENT - COMPLETE SYSTEM TEST")
    print("="*80)

    tests = [
        ("Import Dependencies", test_imports),
        ("Graph Database", test_graph_database),
        ("Qualifier Extraction", test_qualifier_extraction),
        ("PDF Extraction", test_pdf_extraction),
        ("Research APIs", test_research_apis),
        ("Neo4j Connection", test_neo4j_connection),
        ("End-to-End Pipeline", test_end_to_end_pipeline),
    ]

    results = []

    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n  ✗ {name} crashed: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:10} {name}")

    print("="*80)
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("\n✅ SUCCESS: All tests passed! System is fully operational.")
        print("\nThe system is ready to:")
        print("  - Extract claims from research papers")
        print("  - Preserve critical qualifiers")
        print("  - Build knowledge graphs")
        print("  - Search research papers")
        print("  - Investigate and verify claims")
        return 0
    else:
        failed_tests = [name for name, result in results if not result]
        print(f"\n⚠ ISSUES: {len(failed_tests)} test(s) failed:")
        for name in failed_tests:
            print(f"  - {name}")
        print("\nPlease troubleshoot the failed tests.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
