"""
Database Migration: Add Project Support
Adds project_id property to all nodes and creates default project.
"""

from neo4j import GraphDatabase
import os
from datetime import datetime
import sys

# Set UTF-8 encoding for Windows compatibility
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def run_migration(uri="bolt://localhost:7687", user="neo4j", password="password"):
    """
    Run the migration to add project support to the database.

    Steps:
    1. Create Project node type
    2. Add project_id property to all existing nodes
    3. Create default project
    4. Create indexes for efficient querying
    """

    driver = GraphDatabase.driver(uri, auth=(user, password))

    try:
        with driver.session() as session:
            print("=" * 60)
            print("STARTING PROJECT SUPPORT MIGRATION")
            print("=" * 60)

            # Step 1: Create default project if it doesn't exist
            print("\n[1/4] Creating default project...")
            result = session.run("""
                MERGE (p:Project {id: 'default'})
                ON CREATE SET
                    p.name = 'Default Project',
                    p.description = 'Default research project',
                    p.color = '#2196F3',
                    p.created_at = datetime(),
                    p.updated_at = datetime(),
                    p.is_active = true
                RETURN p
            """)

            project = result.single()
            if project:
                print("✅ Default project created/verified")

            # Step 2: Add project_id to all existing nodes without one
            print("\n[2/4] Adding project_id to existing nodes...")
            result = session.run("""
                MATCH (n)
                WHERE n.project_id IS NULL AND NOT n:Project
                SET n.project_id = 'default'
                RETURN count(n) as updated_count
            """)

            record = result.single()
            count = record['updated_count'] if record else 0
            print(f"✅ Updated {count} nodes with default project_id")

            # Step 3: Create indexes for efficient project queries
            print("\n[3/4] Creating indexes for project queries...")

            try:
                session.run("CREATE INDEX project_id_index IF NOT EXISTS FOR (n:Claim) ON (n.project_id)")
                print("✅ Index created for Claim.project_id")
            except Exception as e:
                print(f"⚠️ Index creation info: {e}")

            try:
                session.run("CREATE INDEX document_project_index IF NOT EXISTS FOR (n:Document) ON (n.project_id)")
                print("✅ Index created for Document.project_id")
            except Exception as e:
                print(f"⚠️ Index creation info: {e}")

            # Step 4: Verify migration
            print("\n[4/4] Verifying migration...")
            result = session.run("""
                MATCH (p:Project {id: 'default'})
                RETURN p.name as name, p.id as id
            """)

            project = result.single()
            if project:
                print(f"✅ Default project verified: {project['name']} (ID: {project['id']})")

            result = session.run("""
                MATCH (n)
                WHERE NOT n:Project
                WITH count(n) as total_nodes,
                     count(CASE WHEN n.project_id = 'default' THEN 1 END) as nodes_with_project
                RETURN total_nodes, nodes_with_project
            """)

            stats = result.single()
            if stats:
                print(f"✅ Total nodes: {stats['total_nodes']}, With project_id: {stats['nodes_with_project']}")

            print("\n" + "=" * 60)
            print("MIGRATION COMPLETED SUCCESSFULLY ✅")
            print("=" * 60)

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        raise

    finally:
        driver.close()


def rollback_migration(uri="bolt://localhost:7687", user="neo4j", password="password"):
    """
    Rollback the migration (for testing purposes).
    WARNING: This removes all project_id properties and Project nodes.
    """

    driver = GraphDatabase.driver(uri, auth=(user, password))

    try:
        with driver.session() as session:
            print("=" * 60)
            print("ROLLING BACK PROJECT SUPPORT MIGRATION")
            print("=" * 60)

            # Remove project_id from all nodes
            print("\n[1/3] Removing project_id from nodes...")
            result = session.run("""
                MATCH (n)
                WHERE n.project_id IS NOT NULL
                REMOVE n.project_id
                RETURN count(n) as removed_count
            """)

            record = result.single()
            count = record['removed_count'] if record else 0
            print(f"✅ Removed project_id from {count} nodes")

            # Delete all Project nodes
            print("\n[2/3] Deleting Project nodes...")
            result = session.run("""
                MATCH (p:Project)
                DELETE p
                RETURN count(p) as deleted_count
            """)

            record = result.single()
            count = record['deleted_count'] if record else 0
            print(f"✅ Deleted {count} Project nodes")

            # Drop indexes
            print("\n[3/3] Dropping project indexes...")
            try:
                session.run("DROP INDEX project_id_index IF EXISTS")
                session.run("DROP INDEX document_project_index IF EXISTS")
                print("✅ Indexes dropped")
            except Exception as e:
                print(f"⚠️ Index drop info: {e}")

            print("\n" + "=" * 60)
            print("ROLLBACK COMPLETED ✅")
            print("=" * 60)

    except Exception as e:
        print(f"\n❌ Rollback failed: {e}")
        raise

    finally:
        driver.close()


if __name__ == "__main__":
    import sys

    # Get Neo4j credentials from environment or use defaults
    uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
    user = os.getenv('NEO4J_USER', 'neo4j')
    password = os.getenv('NEO4J_PASSWORD', 'password')

    # Check for rollback flag
    if len(sys.argv) > 1 and sys.argv[1] == '--rollback':
        print("\n⚠️  WARNING: This will remove all project data!")
        response = input("Are you sure you want to rollback? (yes/no): ")
        if response.lower() == 'yes':
            rollback_migration(uri, user, password)
        else:
            print("Rollback cancelled.")
    else:
        run_migration(uri, user, password)
