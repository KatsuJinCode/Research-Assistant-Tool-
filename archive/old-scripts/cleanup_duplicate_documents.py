"""
Cleanup Duplicate Document Processing

Removes duplicate document processing runs, keeping only the most recent
version of each document along with its claims and qualifiers.
"""

from research_agent.neo4j_database import Neo4jDatabase
from collections import defaultdict


def find_duplicate_documents(db: Neo4jDatabase):
    """Find documents that have been processed multiple times."""
    query = """
    MATCH (d:Document)
    RETURN d.source_file as file,
           d.processed_at as timestamp,
           d.id as id
    ORDER BY d.source_file, d.processed_at
    """

    with db.driver.session(database=db.database) as session:
        result = session.run(query)

        # Group by filename
        docs_by_file = defaultdict(list)
        for record in result:
            docs_by_file[record['file']].append({
                'id': record['id'],
                'timestamp': record['timestamp']
            })

        return docs_by_file


def remove_duplicate_documents(db: Neo4jDatabase, docs_by_file):
    """
    Remove duplicate document processing runs.

    Keeps the most recent version of each document.
    """
    print("\n" + "=" * 80)
    print("REMOVING DUPLICATE DOCUMENT PROCESSING".center(80))
    print("=" * 80 + "\n")

    total_removed = 0

    for filename, docs in docs_by_file.items():
        if len(docs) <= 1:
            print(f"{filename}: No duplicates")
            continue

        print(f"\n{filename}: Found {len(docs)} versions")

        # Sort by timestamp (most recent last)
        docs.sort(key=lambda d: d['timestamp'])

        # Keep the most recent, remove others
        to_keep = docs[-1]
        to_remove = docs[:-1]

        print(f"  Keeping: {to_keep['timestamp']}")
        print(f"  Removing: {len(to_remove)} older versions")

        for doc in to_remove:
            # Delete document and all connected nodes
            query = """
            MATCH (d:Document {id: $doc_id})
            OPTIONAL MATCH (d)-[:CONTAINS_CLAIM]->(c:Claim)
            OPTIONAL MATCH (c)-[:HAS_QUALIFIER]->(q:Qualifier)
            DETACH DELETE d, c, q
            """

            with db.driver.session(database=db.database) as session:
                session.run(query, doc_id=doc['id'])

            total_removed += 1

    print(f"\n{total_removed} duplicate document(s) removed")
    return total_removed


def main():
    """Run duplicate document cleanup."""
    db = Neo4jDatabase()

    try:
        # Find duplicates
        print("Scanning for duplicate documents...")
        docs_by_file = find_duplicate_documents(db)

        if not docs_by_file:
            print("No documents found in database")
            return

        # Remove duplicates
        removed = remove_duplicate_documents(db, docs_by_file)

        # Show final stats
        stats = db.stats()
        print("\n" + "=" * 80)
        print("FINAL DATABASE STATE".center(80))
        print("=" * 80 + "\n")
        print(f"Total nodes: {stats['total_nodes']}")
        print(f"Total relationships: {stats['total_relationships']}")
        print("\nNode types:")
        for label, count in stats['node_labels'].items():
            print(f"  {label}: {count}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
