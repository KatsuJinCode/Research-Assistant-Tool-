"""
Example: Using TripleExtractor for Knowledge Graph Embeddings

This example demonstrates how to extract triples from the research graph
for training PyKEEN embeddings (TransE, RotatE, etc.).
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from research_agent.graph_database import GraphDatabase
from backend.rag.triple_extractor import TripleExtractor


def example_basic_extraction():
    """Example: Basic triple extraction."""
    print("\n" + "="*60)
    print("Example 1: Basic Triple Extraction")
    print("="*60)

    # Initialize graph database
    db = GraphDatabase()

    # Create some sample data
    doc_id = db.create_node('Document', {
        'title': 'Climate Change Impact Study',
        'arxiv_id': '2401.12345',
    })

    claim1 = db.create_node('Claim', {
        'text': 'Global temperatures are rising',
        'confidence': 0.95,
    })

    claim2 = db.create_node('Claim', {
        'text': 'Ice sheets are melting faster',
        'confidence': 0.90,
    })

    db.create_relationship(doc_id, claim1, 'CONTAINS')
    db.create_relationship(doc_id, claim2, 'CONTAINS')
    db.create_relationship(claim1, claim2, 'SUPPORTS', {'confidence': 0.85})

    # Extract triples
    extractor = TripleExtractor(db)
    triples = extractor.extract_from_neo4j()

    print(f"\nExtracted {len(triples)} triples:")
    for head, relation, tail in triples:
        print(f"  ({head[:20]}..., {relation}, {tail[:20]}...)")

    return extractor


def example_filtered_extraction():
    """Example: Extract only reasoning relationships."""
    print("\n" + "="*60)
    print("Example 2: Filtered Triple Extraction")
    print("="*60)

    # Initialize graph database
    db = GraphDatabase()

    # Create claims with various relationships
    claims = []
    for i in range(5):
        claim_id = db.create_node('Claim', {
            'text': f'Claim {i}',
            'confidence': 0.8 + i * 0.02,
        })
        claims.append(claim_id)

    # Add different types of relationships
    db.create_relationship(claims[0], claims[1], 'SUPPORTS')
    db.create_relationship(claims[1], claims[2], 'CONTRADICTS')
    db.create_relationship(claims[0], claims[2], 'PARENT_OF')
    db.create_relationship(claims[3], claims[4], 'SIMILAR_TO', {'score': 0.92})

    # Extract only semantic relationships (reasoning)
    extractor = TripleExtractor(db)
    semantic_triples = extractor.get_semantic_triples()

    print(f"\nSemantic triples (reasoning only): {len(semantic_triples)}")
    for head, relation, tail in semantic_triples:
        print(f"  {relation}: {head[:20]}... -> {tail[:20]}...")

    # Extract only hierarchical relationships
    hierarchical_triples = extractor.get_hierarchical_triples()

    print(f"\nHierarchical triples (structure): {len(hierarchical_triples)}")
    for head, relation, tail in hierarchical_triples:
        print(f"  {relation}: {head[:20]}... -> {tail[:20]}...")


def example_statistics():
    """Example: Get graph statistics."""
    print("\n" + "="*60)
    print("Example 3: Graph Statistics")
    print("="*60)

    # Initialize graph database
    db = GraphDatabase()

    # Create a small research graph
    doc = db.create_node('Document', {'title': 'Research Paper'})
    claims = [db.create_node('Claim', {'text': f'Claim {i}'}) for i in range(3)]
    super_claim = db.create_node('SuperClaim', {'text': 'Merged claim'})

    # Add relationships
    for claim in claims:
        db.create_relationship(doc, claim, 'CONTAINS')

    db.create_relationship(claims[0], claims[1], 'SUPPORTS')
    db.create_relationship(claims[1], super_claim, 'MERGED_INTO')

    # Get statistics
    extractor = TripleExtractor(db)
    stats = extractor.get_statistics()

    print("\nGraph Statistics:")
    print(f"  Total triples: {stats['total_triples']}")
    print(f"  Unique entities: {stats['unique_entities']}")
    print(f"  Unique relations: {stats['unique_relations']}")
    print(f"  Average degree: {stats['avg_degree']:.2f}")

    print("\n  Relation distribution:")
    for relation, count in stats['relation_counts'].items():
        percentage = (count / stats['total_triples']) * 100
        print(f"    {relation}: {count} ({percentage:.1f}%)")

    print("\n  Node type distribution:")
    for label, count in stats['node_label_counts'].items():
        print(f"    {label}: {count}")


def example_pykeen_export():
    """Example: Export triples for PyKEEN training."""
    print("\n" + "="*60)
    print("Example 4: Export for PyKEEN")
    print("="*60)

    # Initialize graph database
    db = GraphDatabase()

    # Create sample graph
    claims = [db.create_node('Claim', {'text': f'Claim {i}'}) for i in range(4)]

    db.create_relationship(claims[0], claims[1], 'SUPPORTS')
    db.create_relationship(claims[1], claims[2], 'SUPPORTS')
    db.create_relationship(claims[2], claims[3], 'CONTRADICTS')

    # Export to PyKEEN format
    extractor = TripleExtractor(db)
    output_file = 'triples_for_pykeen.tsv'
    count = extractor.export_to_pykeen_format(output_file)

    print(f"\nExported {count} triples to {output_file}")
    print("Format: head_entity<TAB>relation<TAB>tail_entity")

    # Show sample lines
    with open(output_file, 'r') as f:
        lines = f.readlines()[:3]

    print("\nSample lines:")
    for i, line in enumerate(lines, 1):
        parts = line.strip().split('\t')
        print(f"  {i}. {parts[0][:20]:<20} {parts[1]:<15} {parts[2][:20]}")

    print(f"\nThis file can now be used with PyKEEN for training:")
    print("  from pykeen.triples import TriplesFactory")
    print(f"  triples = TriplesFactory.from_path('{output_file}')")
    print("  # Train TransE, RotatE, or other embeddings...")

    # Cleanup
    import os
    os.remove(output_file)


def example_entity_types():
    """Example: Get entity type information."""
    print("\n" + "="*60)
    print("Example 5: Entity Type Mapping")
    print("="*60)

    # Initialize graph database
    db = GraphDatabase()

    # Create diverse node types
    doc = db.create_node('Document', {'title': 'Paper'})
    claim = db.create_node('Claim', {'text': 'Claim text'})
    super_claim = db.create_node('SuperClaim', {'text': 'Merged'})
    qualifier = db.create_node('Qualifier', {'type': 'modal', 'value': 'may'})

    db.create_relationship(doc, claim, 'CONTAINS')
    db.create_relationship(claim, qualifier, 'HAS_QUALIFIER')

    # Get entity types
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

    print("\nThis mapping can be used for:")
    print("  - Typed knowledge graph embeddings")
    print("  - Entity-specific learning rates")
    print("  - Filtering by entity type")


if __name__ == '__main__':
    print("\n" + "="*70)
    print("KNOWLEDGE GRAPH TRIPLE EXTRACTION - USAGE EXAMPLES")
    print("="*70)

    example_basic_extraction()
    example_filtered_extraction()
    example_statistics()
    example_pykeen_export()
    example_entity_types()

    print("\n" + "="*70)
    print("Examples completed successfully!")
    print("="*70)
    print("\nNext steps:")
    print("  1. Use TripleExtractor to export your research graph")
    print("  2. Train PyKEEN embeddings (TransE, RotatE, etc.)")
    print("  3. Use embeddings for advanced Graph RAG:")
    print("     - Semantic similarity in embedding space")
    print("     - Link prediction for claim verification")
    print("     - Claim clustering based on embeddings")
    print("="*70 + "\n")
