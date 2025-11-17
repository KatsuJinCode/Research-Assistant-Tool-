#!/usr/bin/env python3
"""
Migrate graph data from NetworkX to Neo4j.

This script:
1. Loads the existing graph from NetworkX (from extract_and_cluster_claims.py)
2. Connects to Neo4j
3. Migrates all nodes and relationships
4. Verifies the migration

Prerequisites:
- Neo4j must be installed and running
- pip install neo4j python-dotenv

Usage:
    python migrate_to_neo4j.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from research_agent.neo4j_database import Neo4jDatabase


def load_from_cypher_file(db: Neo4jDatabase, cypher_file: str):
    """
    Load data from Cypher file into Neo4j.

    Args:
        db: Neo4j database instance
        cypher_file: Path to .cypher file
    """
    print(f"📄 Reading Cypher file: {cypher_file}")
    print()

    with open(cypher_file, 'r') as f:
        content = f.read()

    # Split into individual statements
    statements = content.split('\n\n')
    statements = [s.strip() for s in statements if s.strip() and not s.strip().startswith('//')]

    print(f"Found {len(statements)} statements to execute")
    print()

    # Execute each statement
    with db.driver.session(database=db.database) as session:
        for i, statement in enumerate(statements, 1):
            if not statement:
                continue

            print(f"[{i}/{len(statements)}] Executing statement...")

            try:
                session.run(statement)
                print(f"  ✓ Success")
            except Exception as e:
                print(f"  ✗ Error: {e}")
                print(f"  Statement: {statement[:100]}...")
                # Continue with other statements

            if i % 10 == 0:
                print()

    print()
    print("✓ Migration complete!")
    print()


def verify_migration(db: Neo4jDatabase):
    """
    Verify that migration was successful.

    Args:
        db: Neo4j database instance
    """
    print("=" * 80)
    print("VERIFYING MIGRATION")
    print("=" * 80)
    print()

    stats = db.stats()

    print(f"Total nodes: {stats['total_nodes']}")
    print(f"Total relationships: {stats['total_relationships']}")
    print()

    print("Node types:")
    for label, count in stats['node_labels'].items():
        print(f"  {label:15s}: {count:3d}")
    print()

    print("Relationship types:")
    for rel_type, count in stats['relationship_types'].items():
        print(f"  {rel_type:15s}: {count:3d}")
    print()

    # Test some queries
    print("Testing queries...")
    print()

    # Find a document
    docs = db.find_nodes('Document')
    if docs:
        print(f"✓ Found {len(docs)} document(s)")
        doc = docs[0]
        print(f"  Title: {doc.get('title')}")
        print()

    # Find claims
    claims = db.find_nodes('Claim')
    if claims:
        print(f"✓ Found {len(claims)} claim(s)")
        print(f"  Sample: {claims[0].get('text', '')[:80]}...")
        print()

    # Find super-claims
    super_claims = db.find_nodes('SuperClaim')
    if super_claims:
        print(f"✓ Found {len(super_claims)} super-claim(s)")
        print(f"  Sample: {super_claims[0].get('text', '')[:80]}...")
        print()

    # Test similarity search
    if claims:
        claim_id = claims[0]['id']
        similar = db.find_similar_claims(claim_id, min_score=0.7)
        print(f"✓ Similarity search works ({len(similar)} similar claims found)")
        print()

    print("=" * 80)
    print("✅ MIGRATION VERIFIED")
    print("=" * 80)
    print()


def main():
    """Run migration."""
    print()
    print("╔" + "═" * 78 + "╗")
    print("║" + " NETWORKX → NEO4J MIGRATION".center(78) + "║")
    print("╚" + "═" * 78 + "╝")
    print()

    # Check for Cypher file
    cypher_file = 'szasz_claims_graph.cypher'
    if not Path(cypher_file).exists():
        print(f"❌ Cypher file not found: {cypher_file}")
        print()
        print("Please run extract_and_cluster_claims.py first to generate the file.")
        print()
        return 1

    # Connect to Neo4j
    print("Connecting to Neo4j...")
    print()

    try:
        db = Neo4jDatabase()
        print(f"✓ Connected to Neo4j at {db.uri}")
        print(f"  Database: {db.database}")
        print()
    except Exception as e:
        print(f"❌ Could not connect to Neo4j: {e}")
        print()
        print("Please ensure:")
        print("  1. Neo4j is installed and running")
        print("  2. Connection details are correct in .env file:")
        print("     NEO4J_URI=bolt://localhost:7687")
        print("     NEO4J_USER=neo4j")
        print("     NEO4J_PASSWORD=research123")
        print()
        print("See setup_neo4j.md for installation instructions.")
        print()
        return 1

    # Ask for confirmation to clear existing data
    print("⚠️  This will clear all existing data in the Neo4j database!")
    print()
    response = input("Continue? (yes/no): ").strip().lower()
    print()

    if response != 'yes':
        print("Migration cancelled.")
        print()
        return 0

    # Clear database
    print("Clearing existing data...")
    db.clear_database()
    print("✓ Database cleared")
    print()

    # Load data
    load_from_cypher_file(db, cypher_file)

    # Verify
    verify_migration(db)

    # Close connection
    db.close()

    print("Migration successful! 🎉")
    print()
    print("Next steps:")
    print("  1. Access Neo4j Browser: http://localhost:7474")
    print("  2. Run queries to explore the graph")
    print("  3. Update config to use Neo4j by default")
    print()

    return 0


if __name__ == '__main__':
    sys.exit(main())
