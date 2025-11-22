"""
Test suite for Knowledge Graph Triple Extractor

Tests the extraction of (head, relation, tail) triples from the graph database
for PyKEEN embedding training.
"""

import os
import sys
import tempfile
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from research_agent.graph_database import GraphDatabase
from backend.rag.triple_extractor import TripleExtractor


def create_test_graph() -> GraphDatabase:
    """
    Create a small test graph with various node types and relationships.

    Graph structure:
    - 1 Document containing 3 Claims
    - Claims have SUPPORTS/CONTRADICTS relationships
    - 1 SuperClaim merging 2 claims
    - 1 Qualifier attached to a claim
    - Hierarchical PARENT_OF relationship
    """
    db = GraphDatabase()

    # Create document
    doc_id = db.create_node('Document', {
        'title': 'Test Paper',
        'arxiv_id': 'test.123',
    })

    # Create claims
    claim1_id = db.create_node('Claim', {
        'text': 'Climate change affects ecosystems',
        'confidence': 0.9,
    })

    claim2_id = db.create_node('Claim', {
        'text': 'Ecosystems are resilient to climate change',
        'confidence': 0.7,
    })

    claim3_id = db.create_node('Claim', {
        'text': 'Temperature increases harm biodiversity',
        'confidence': 0.85,
    })

    # Create superclaim
    super_claim_id = db.create_node('SuperClaim', {
        'text': 'Climate change impacts ecosystems',
        'confidence': 0.95,
        'member_count': 2,
    })

    # Create qualifier
    qualifier_id = db.create_node('Qualifier', {
        'type': 'modal',
        'value': 'may',
    })

    # Create relationships - Document contains claims
    db.create_relationship(doc_id, claim1_id, 'CONTAINS')
    db.create_relationship(doc_id, claim2_id, 'CONTAINS')
    db.create_relationship(doc_id, claim3_id, 'CONTAINS')

    # Semantic relationships
    db.create_relationship(claim1_id, claim3_id, 'SUPPORTS', {'confidence': 0.8})
    db.create_relationship(claim2_id, claim1_id, 'CONTRADICTS', {'confidence': 0.75})

    # Similarity relationship
    db.create_relationship(claim1_id, claim3_id, 'SIMILAR_TO', {'score': 0.82})

    # Merge relationships
    db.create_relationship(claim1_id, super_claim_id, 'MERGED_INTO')
    db.create_relationship(claim3_id, super_claim_id, 'MERGED_INTO')

    # Qualifier relationship
    db.create_relationship(claim2_id, qualifier_id, 'HAS_QUALIFIER')

    # Hierarchical relationship
    db.create_relationship(claim1_id, claim3_id, 'PARENT_OF')

    return db


def test_basic_extraction():
    """Test basic triple extraction functionality."""
    print("\n" + "="*60)
    print("TEST: Basic Triple Extraction")
    print("="*60)

    db = create_test_graph()
    extractor = TripleExtractor(db)

    # Extract all triples
    triples = extractor.extract_from_neo4j()

    print(f"\nExtracted {len(triples)} triples:")
    for i, (head, relation, tail) in enumerate(triples[:5], 1):
        print(f"  {i}. ({head[:12]}..., {relation}, {tail[:12]}...)")

    # Verify format
    assert all(isinstance(triple, tuple) for triple in triples), "All triples should be tuples"
    assert all(len(triple) == 3 for triple in triples), "All triples should have 3 elements"
    assert all(
        all(isinstance(elem, str) for elem in triple)
        for triple in triples
    ), "All triple elements should be strings"

    print("\n[PASS] Triple format validation passed")

    # Verify we got expected relationships
    relations = [triple[1] for triple in triples]
    expected_relations = ['CONTAINS', 'SUPPORTS', 'CONTRADICTS', 'SIMILAR_TO',
                         'MERGED_INTO', 'HAS_QUALIFIER', 'PARENT_OF']

    for rel in expected_relations:
        assert rel in relations, f"Missing expected relation: {rel}"

    print(f"[PASS] All expected relation types found")

    return True


def test_relation_filtering():
    """Test filtering triples by relation type."""
    print("\n" + "="*60)
    print("TEST: Relation Type Filtering")
    print("="*60)

    db = create_test_graph()
    extractor = TripleExtractor(db)

    # Test semantic relationships only
    semantic_triples = extractor.extract_by_relation_type(['SUPPORTS', 'CONTRADICTS'])
    print(f"\nSemantic triples: {len(semantic_triples)}")
    for head, relation, tail in semantic_triples:
        print(f"  ({head[:12]}..., {relation}, {tail[:12]}...)")

    assert all(
        triple[1] in ['SUPPORTS', 'CONTRADICTS']
        for triple in semantic_triples
    ), "Filtered triples should only contain requested relations"

    print("[PASS] Relation filtering works correctly")

    # Test hierarchical relationships
    hierarchical_triples = extractor.extract_by_relation_type(['PARENT_OF', 'CONTAINS'])
    print(f"\nHierarchical triples: {len(hierarchical_triples)}")

    assert len(hierarchical_triples) > 0, "Should have hierarchical relationships"
    print("[PASS] Multiple filter types work")

    return True


def test_statistics():
    """Test statistics generation."""
    print("\n" + "="*60)
    print("TEST: Statistics Generation")
    print("="*60)

    db = create_test_graph()
    extractor = TripleExtractor(db)

    stats = extractor.get_statistics()

    print("\nGraph Statistics:")
    print(f"  Total triples: {stats['total_triples']}")
    print(f"  Unique entities: {stats['unique_entities']}")
    print(f"  Unique relations: {stats['unique_relations']}")
    print(f"  Average degree: {stats['avg_degree']:.2f}")

    print("\n  Relation counts:")
    for relation, count in stats['relation_counts'].items():
        print(f"    {relation}: {count}")

    print("\n  Node label counts:")
    for label, count in stats['node_label_counts'].items():
        print(f"    {label}: {count}")

    # Validate statistics
    assert stats['total_triples'] > 0, "Should have triples"
    assert stats['unique_entities'] > 0, "Should have entities"
    assert stats['unique_relations'] > 0, "Should have relations"
    assert isinstance(stats['relation_counts'], dict), "Relation counts should be dict"
    assert isinstance(stats['node_label_counts'], dict), "Label counts should be dict"

    print("\n[PASS] Statistics generation passed")

    return True


def test_semantic_vs_hierarchical():
    """Test specialized extraction methods."""
    print("\n" + "="*60)
    print("TEST: Semantic vs Hierarchical Extraction")
    print("="*60)

    db = create_test_graph()
    extractor = TripleExtractor(db)

    # Get semantic triples
    semantic = extractor.get_semantic_triples()
    print(f"\nSemantic triples (reasoning): {len(semantic)}")
    semantic_relations = set(triple[1] for triple in semantic)
    print(f"  Relations: {semantic_relations}")

    assert all(
        rel in ['SUPPORTS', 'CONTRADICTS', 'SIMILAR_TO']
        for rel in semantic_relations
    ), "Semantic triples should only contain reasoning relations"

    # Get hierarchical triples
    hierarchical = extractor.get_hierarchical_triples()
    print(f"\nHierarchical triples (structure): {len(hierarchical)}")
    hierarchical_relations = set(triple[1] for triple in hierarchical)
    print(f"  Relations: {hierarchical_relations}")

    assert all(
        rel in ['PARENT_OF', 'CONTAINS', 'MERGED_INTO']
        for rel in hierarchical_relations
    ), "Hierarchical triples should only contain structure relations"

    print("\n[PASS] Specialized extraction methods work correctly")

    return True


def test_pykeen_export():
    """Test export to PyKEEN TSV format."""
    print("\n" + "="*60)
    print("TEST: PyKEEN TSV Export")
    print("="*60)

    db = create_test_graph()
    extractor = TripleExtractor(db)

    # Export to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tsv', delete=False) as f:
        temp_file = f.name

    try:
        count = extractor.export_to_pykeen_format(temp_file)
        print(f"\nExported {count} triples to {temp_file}")

        # Read and verify format
        with open(temp_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        print("\nSample lines:")
        for i, line in enumerate(lines[:3], 1):
            parts = line.strip().split('\t')
            print(f"  {i}. {parts[0][:12]}...\t{parts[1]}\t{parts[2][:12]}...")

            # Verify TSV format
            assert len(parts) == 3, "Each line should have 3 tab-separated values"

        print("\n[PASS] PyKEEN export format is correct")

    finally:
        # Cleanup
        if os.path.exists(temp_file):
            os.remove(temp_file)

    return True


def test_entity_types():
    """Test entity type mapping extraction."""
    print("\n" + "="*60)
    print("TEST: Entity Type Mapping")
    print("="*60)

    db = create_test_graph()
    extractor = TripleExtractor(db)

    entity_types = extractor.get_entity_types()

    print(f"\nEntity type mapping: {len(entity_types)} entities")

    # Count by type
    type_counts = {}
    for entity_id, label in entity_types.items():
        type_counts[label] = type_counts.get(label, 0) + 1

    print("\nType distribution:")
    for label, count in type_counts.items():
        print(f"  {label}: {count}")

    # Verify types
    expected_types = {'Document', 'Claim', 'SuperClaim', 'Qualifier'}
    actual_types = set(type_counts.keys())

    assert expected_types == actual_types, f"Expected {expected_types}, got {actual_types}"

    print("\n[PASS] Entity type mapping is correct")

    return True


def test_cache_invalidation():
    """Test cache invalidation mechanism."""
    print("\n" + "="*60)
    print("TEST: Cache Invalidation")
    print("="*60)

    db = create_test_graph()
    extractor = TripleExtractor(db)

    # First extraction
    triples1 = extractor.extract_from_neo4j()
    count1 = len(triples1)
    print(f"\nInitial extraction: {count1} triples")

    # Add new relationship
    claim_ids = db.find_nodes('Claim')
    if len(claim_ids) >= 2:
        db.create_relationship(claim_ids[0]['id'], claim_ids[1]['id'], 'TEST_RELATION')

    # Without invalidation, should get cached result
    triples2 = extractor.extract_from_neo4j()
    count2 = len(triples2)
    print(f"Cached extraction: {count2} triples (should be same)")
    assert count2 == count1, "Should return cached result"

    # Invalidate cache
    extractor.invalidate_cache()

    # Now should get updated result
    triples3 = extractor.extract_from_neo4j()
    count3 = len(triples3)
    print(f"After invalidation: {count3} triples (should be +1)")
    assert count3 == count1 + 1, "Should include new relationship after cache invalidation"

    print("\n[PASS] Cache invalidation works correctly")

    return True


def run_all_tests():
    """Run all test cases."""
    print("\n" + "="*70)
    print("KNOWLEDGE GRAPH TRIPLE EXTRACTOR - TEST SUITE")
    print("="*70)

    tests = [
        ("Basic Extraction", test_basic_extraction),
        ("Relation Filtering", test_relation_filtering),
        ("Statistics", test_statistics),
        ("Semantic vs Hierarchical", test_semantic_vs_hierarchical),
        ("PyKEEN Export", test_pykeen_export),
        ("Entity Types", test_entity_types),
        ("Cache Invalidation", test_cache_invalidation),
    ]

    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success, None))
        except Exception as e:
            results.append((name, False, str(e)))

    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    passed = 0
    failed = 0

    for name, success, error in results:
        status = "[PASS] PASSED" if success else "[FAIL] FAILED"
        print(f"{status}: {name}")
        if error:
            print(f"  Error: {error}")

        if success:
            passed += 1
        else:
            failed += 1

    print(f"\n{passed}/{len(tests)} tests passed")

    if failed > 0:
        print(f"\n[WARN] {failed} test(s) failed")
        return False
    else:
        print("\n[PASS] All tests passed!")
        return True


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
