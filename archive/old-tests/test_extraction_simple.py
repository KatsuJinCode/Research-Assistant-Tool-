"""
Simple test of extraction pipeline without Unicode output issues.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from research_agent.graph_database import GraphDatabase
from research_agent.normalization.qualifier_extractor import QualifierExtractor

def main():
    print("Testing extraction pipeline...")

    # Initialize
    db = GraphDatabase()
    extractor = QualifierExtractor()

    # Create test document
    doc_id = db.create_node('Document', {
        'title': 'Test Document',
        'author': 'Test Author'
    })
    print(f"Created document node: {doc_id}")

    # Create test claim with qualifier
    claim_text = "Mental illness can only exist as a theoretical concept"

    # Extract qualifiers
    qualifiers = extractor.extract(claim_text)
    print(f"Extracted {len(qualifiers)} qualifiers")
    for q in qualifiers:
        print(f"  - {q['type']}: {q['text']}")

    # Create claim node
    claim_id = db.create_node('Claim', {
        'text': claim_text,
        'type': 'theoretical'
    })
    print(f"Created claim node: {claim_id}")

    # Link qualifiers
    for qualifier in qualifiers:
        qual_id = db.create_node('Qualifier', qualifier)
        db.create_relationship(claim_id, 'HAS_QUALIFIER', qual_id)

    # Get stats
    stats = db.stats()
    print(f"\nDatabase stats:")
    print(f"  Nodes: {stats['total_nodes']}")
    print(f"  Relationships: {stats['total_relationships']}")

    # Export
    export_file = "test_graph_export.cypher"
    db.export_to_cypher(export_file)
    print(f"\nExported to: {export_file}")

    print("\nSUCCESS: Extraction pipeline is working!")
    return True

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
