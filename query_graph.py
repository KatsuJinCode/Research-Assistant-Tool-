"""
Quick script to query the Neo4j knowledge graph.
Shows what's stored in the database.
"""

from research_agent.neo4j_database import Neo4jDatabase

db = Neo4jDatabase()

print("=" * 80)
print("NEO4J KNOWLEDGE GRAPH CONTENTS")
print("=" * 80)

# Get overall stats
stats = db.stats()
print(f"\nDatabase Statistics:")
print(f"  Total Nodes: {stats['total_nodes']}")
print(f"  Total Relationships: {stats['total_relationships']}")

print(f"\nNodes by Type:")
for label, count in stats['node_labels'].items():
    print(f"  - {label}: {count}")

print(f"\nRelationships by Type:")
for rel_type, count in stats['relationship_types'].items():
    print(f"  - {rel_type}: {count}")

# Get document
print("\n" + "=" * 80)
print("DOCUMENT NODE")
print("=" * 80)
documents = db.find_nodes('Document')
if documents:
    doc = documents[0]
    print(f"\nTitle: {doc.get('title', 'Unknown')}")
    print(f"Author: {doc.get('author', 'Unknown')}")
    print(f"Pages: {doc.get('page_count', 'Unknown')}")
    print(f"Source: {doc.get('source_file', 'Unknown')}")

# Get sample claims
print("\n" + "=" * 80)
print("SAMPLE CLAIMS")
print("=" * 80)
claims = db.find_nodes('Claim')
print(f"\nTotal Claims: {len(claims)}")

print("\nFirst 5 Claims:")
for i, claim in enumerate(claims[:5], 1):
    print(f"\n{i}. {claim.get('text', '')[:150]}...")
    print(f"   Strength: {claim.get('strength', 'unknown')}")
    print(f"   Qualifiers: {claim.get('qualifier_count', 0)}")
    print(f"   Has temporal constraint: {claim.get('has_temporal', False)}")

# Get qualifiers
print("\n" + "=" * 80)
print("QUALIFIERS")
print("=" * 80)
qualifiers = db.find_nodes('Qualifier')
print(f"\nTotal Qualifiers: {len(qualifiers)}")

# Count by type
qual_types = {}
for q in qualifiers:
    qtype = q.get('type', 'unknown')
    qual_types[qtype] = qual_types.get(qtype, 0) + 1

print("\nQualifier Distribution:")
for qtype, count in sorted(qual_types.items(), key=lambda x: x[1], reverse=True):
    print(f"  {qtype}: {count}")

print("\nSample Qualifiers:")
for i, q in enumerate(qualifiers[:10], 1):
    print(f"  {i}. {q.get('type', 'unknown').upper()}: '{q.get('text', '')}' -> {q.get('impact', '')}")

db.close()

print("\n" + "=" * 80)
print("QUERY COMPLETE")
print("=" * 80)
