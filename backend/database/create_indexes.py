"""
Neo4j Index and Constraint Management

Creates optimized indexes and constraints for:
- Fast text searches
- Efficient property lookups
- Uniqueness constraints
- Composite indexes

Run this script to set up optimal database performance.
"""

import logging
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.database.neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


class IndexManager:
    """
    Manages Neo4j database indexes and constraints.

    Provides methods to create, list, and drop indexes for optimal performance.
    """

    def __init__(self, session):
        """
        Initialize index manager.

        Args:
            session: Neo4j session object
        """
        self.session = session

    def create_all_indexes(self, drop_existing: bool = False):
        """
        Create all recommended indexes and constraints.

        Args:
            drop_existing: Whether to drop existing indexes first
        """
        logger.info("=" * 60)
        logger.info("Creating Neo4j Indexes and Constraints")
        logger.info("=" * 60)

        if drop_existing:
            logger.info("\n[1/6] Dropping existing indexes...")
            self.drop_all_indexes()

        logger.info("\n[2/6] Creating uniqueness constraints...")
        self.create_constraints()

        logger.info("\n[3/6] Creating property indexes...")
        self.create_property_indexes()

        logger.info("\n[4/6] Creating composite indexes...")
        self.create_composite_indexes()

        logger.info("\n[5/6] Creating full-text indexes...")
        self.create_fulltext_indexes()

        logger.info("\n[6/6] Verifying indexes...")
        self.list_indexes()

        logger.info("\n" + "=" * 60)
        logger.info("Index creation complete!")
        logger.info("=" * 60)

    # ===========================
    # UNIQUENESS CONSTRAINTS
    # ===========================

    def create_constraints(self):
        """Create uniqueness constraints for data integrity."""
        constraints = [
            # Claim text + project should be unique (prevent exact duplicates)
            {
                'name': 'claim_text_project_unique',
                'query': '''
                    CREATE CONSTRAINT claim_text_project_unique IF NOT EXISTS
                    FOR (c:Claim)
                    REQUIRE (c.text, c.project_id) IS UNIQUE
                '''
            },

            # Document title + project should be unique
            {
                'name': 'document_title_project_unique',
                'query': '''
                    CREATE CONSTRAINT document_title_project_unique IF NOT EXISTS
                    FOR (d:Document)
                    REQUIRE (d.title, d.project_id) IS UNIQUE
                '''
            },

            # Source URLs should be unique
            {
                'name': 'source_url_unique',
                'query': '''
                    CREATE CONSTRAINT source_url_unique IF NOT EXISTS
                    FOR (s:Source)
                    REQUIRE s.url IS UNIQUE
                '''
            },

            # Agent IDs should be unique
            {
                'name': 'agent_id_unique',
                'query': '''
                    CREATE CONSTRAINT agent_id_unique IF NOT EXISTS
                    FOR (a:Agent)
                    REQUIRE a.agent_id IS UNIQUE
                '''
            }
        ]

        for constraint in constraints:
            try:
                self.session.run(constraint['query'])
                logger.info(f"  ✓ Created constraint: {constraint['name']}")
            except Exception as e:
                # Constraint might already exist
                if "EquivalentSchemaRuleAlreadyExists" in str(e) or "already exists" in str(e).lower():
                    logger.info(f"  ⊙ Constraint already exists: {constraint['name']}")
                else:
                    logger.error(f"  ✗ Failed to create constraint {constraint['name']}: {e}")

    # ===========================
    # PROPERTY INDEXES
    # ===========================

    def create_property_indexes(self):
        """Create single-property indexes for fast lookups."""
        indexes = [
            # Claim indexes
            {
                'name': 'claim_text_idx',
                'query': '''
                    CREATE INDEX claim_text_idx IF NOT EXISTS
                    FOR (c:Claim)
                    ON (c.text)
                '''
            },
            {
                'name': 'claim_confidence_idx',
                'query': '''
                    CREATE INDEX claim_confidence_idx IF NOT EXISTS
                    FOR (c:Claim)
                    ON (c.confidence)
                '''
            },
            {
                'name': 'claim_created_idx',
                'query': '''
                    CREATE INDEX claim_created_idx IF NOT EXISTS
                    FOR (c:Claim)
                    ON (c.created_at)
                '''
            },
            {
                'name': 'claim_project_idx',
                'query': '''
                    CREATE INDEX claim_project_idx IF NOT EXISTS
                    FOR (c:Claim)
                    ON (c.project_id)
                '''
            },

            # Document indexes
            {
                'name': 'document_title_idx',
                'query': '''
                    CREATE INDEX document_title_idx IF NOT EXISTS
                    FOR (d:Document)
                    ON (d.title)
                '''
            },
            {
                'name': 'document_project_idx',
                'query': '''
                    CREATE INDEX document_project_idx IF NOT EXISTS
                    FOR (d:Document)
                    ON (d.project_id)
                '''
            },
            {
                'name': 'document_created_idx',
                'query': '''
                    CREATE INDEX document_created_idx IF NOT EXISTS
                    FOR (d:Document)
                    ON (d.created_at)
                '''
            },

            # Source indexes
            {
                'name': 'source_url_idx',
                'query': '''
                    CREATE INDEX source_url_idx IF NOT EXISTS
                    FOR (s:Source)
                    ON (s.url)
                '''
            },
            {
                'name': 'source_type_idx',
                'query': '''
                    CREATE INDEX source_type_idx IF NOT EXISTS
                    FOR (s:Source)
                    ON (s.type)
                '''
            },

            # Agent indexes
            {
                'name': 'agent_type_idx',
                'query': '''
                    CREATE INDEX agent_type_idx IF NOT EXISTS
                    FOR (a:Agent)
                    ON (a.type)
                '''
            },
            {
                'name': 'agent_created_idx',
                'query': '''
                    CREATE INDEX agent_created_idx IF NOT EXISTS
                    FOR (a:Agent)
                    ON (a.created_at)
                '''
            },

            # SuperClaim indexes
            {
                'name': 'superclaim_confidence_idx',
                'query': '''
                    CREATE INDEX superclaim_confidence_idx IF NOT EXISTS
                    FOR (sc:SuperClaim)
                    ON (sc.confidence)
                '''
            }
        ]

        for index in indexes:
            try:
                self.session.run(index['query'])
                logger.info(f"  ✓ Created index: {index['name']}")
            except Exception as e:
                if "EquivalentSchemaRuleAlreadyExists" in str(e) or "already exists" in str(e).lower():
                    logger.info(f"  ⊙ Index already exists: {index['name']}")
                else:
                    logger.error(f"  ✗ Failed to create index {index['name']}: {e}")

    # ===========================
    # COMPOSITE INDEXES
    # ===========================

    def create_composite_indexes(self):
        """Create composite indexes for multi-property queries."""
        indexes = [
            # Project + confidence for filtered queries
            {
                'name': 'claim_project_confidence_idx',
                'query': '''
                    CREATE INDEX claim_project_confidence_idx IF NOT EXISTS
                    FOR (c:Claim)
                    ON (c.project_id, c.confidence)
                '''
            },

            # Project + created_at for sorted listings
            {
                'name': 'document_project_created_idx',
                'query': '''
                    CREATE INDEX document_project_created_idx IF NOT EXISTS
                    FOR (d:Document)
                    ON (d.project_id, d.created_at)
                '''
            },

            # Type + created_at for agent queries
            {
                'name': 'agent_type_created_idx',
                'query': '''
                    CREATE INDEX agent_type_created_idx IF NOT EXISTS
                    FOR (a:Agent)
                    ON (a.type, a.created_at)
                '''
            }
        ]

        for index in indexes:
            try:
                self.session.run(index['query'])
                logger.info(f"  ✓ Created composite index: {index['name']}")
            except Exception as e:
                if "EquivalentSchemaRuleAlreadyExists" in str(e) or "already exists" in str(e).lower():
                    logger.info(f"  ⊙ Composite index already exists: {index['name']}")
                else:
                    logger.error(f"  ✗ Failed to create composite index {index['name']}: {e}")

    # ===========================
    # FULL-TEXT INDEXES
    # ===========================

    def create_fulltext_indexes(self):
        """Create full-text search indexes."""
        indexes = [
            # Full-text search on claim text
            {
                'name': 'claim_fulltext_idx',
                'query': '''
                    CREATE FULLTEXT INDEX claim_fulltext_idx IF NOT EXISTS
                    FOR (c:Claim)
                    ON EACH [c.text]
                '''
            },

            # Full-text search on document titles and content
            {
                'name': 'document_fulltext_idx',
                'query': '''
                    CREATE FULLTEXT INDEX document_fulltext_idx IF NOT EXISTS
                    FOR (d:Document)
                    ON EACH [d.title, d.content]
                '''
            },

            # Full-text search across multiple node types
            {
                'name': 'global_text_search_idx',
                'query': '''
                    CREATE FULLTEXT INDEX global_text_search_idx IF NOT EXISTS
                    FOR (n:Claim|Document|SuperClaim)
                    ON EACH [n.text, n.title, n.content]
                '''
            }
        ]

        for index in indexes:
            try:
                self.session.run(index['query'])
                logger.info(f"  ✓ Created full-text index: {index['name']}")
            except Exception as e:
                if "EquivalentSchemaRuleAlreadyExists" in str(e) or "already exists" in str(e).lower():
                    logger.info(f"  ⊙ Full-text index already exists: {index['name']}")
                else:
                    logger.error(f"  ✗ Failed to create full-text index {index['name']}: {e}")

    # ===========================
    # UTILITY METHODS
    # ===========================

    def list_indexes(self):
        """List all indexes and constraints."""
        logger.info("\nCurrent Indexes:")
        logger.info("-" * 60)

        # List indexes
        result = self.session.run("SHOW INDEXES")
        index_count = 0
        for record in result:
            index_count += 1
            name = record.get('name', 'Unknown')
            state = record.get('state', 'Unknown')
            index_type = record.get('type', 'Unknown')
            logger.info(f"  • {name} ({index_type}) - {state}")

        logger.info(f"\nTotal indexes: {index_count}")

        # List constraints
        logger.info("\nCurrent Constraints:")
        logger.info("-" * 60)

        result = self.session.run("SHOW CONSTRAINTS")
        constraint_count = 0
        for record in result:
            constraint_count += 1
            name = record.get('name', 'Unknown')
            constraint_type = record.get('type', 'Unknown')
            logger.info(f"  • {name} ({constraint_type})")

        logger.info(f"\nTotal constraints: {constraint_count}")

    def drop_all_indexes(self):
        """Drop all indexes (use with caution!)."""
        logger.warning("Dropping all indexes...")

        # Drop all indexes
        result = self.session.run("SHOW INDEXES")
        for record in result:
            index_name = record.get('name')
            if index_name:
                try:
                    self.session.run(f"DROP INDEX {index_name} IF EXISTS")
                    logger.info(f"  ✓ Dropped index: {index_name}")
                except Exception as e:
                    logger.error(f"  ✗ Failed to drop index {index_name}: {e}")

        # Drop all constraints
        result = self.session.run("SHOW CONSTRAINTS")
        for record in result:
            constraint_name = record.get('name')
            if constraint_name:
                try:
                    self.session.run(f"DROP CONSTRAINT {constraint_name} IF EXISTS")
                    logger.info(f"  ✓ Dropped constraint: {constraint_name}")
                except Exception as e:
                    logger.error(f"  ✗ Failed to drop constraint {constraint_name}: {e}")

    def analyze_query_performance(self, query: str, params: dict = None):
        """
        Analyze query performance using PROFILE.

        Args:
            query: Cypher query to analyze
            params: Query parameters

        Returns:
            Dict with performance metrics
        """
        profiled_query = f"PROFILE {query}"

        try:
            result = self.session.run(profiled_query, params or {})
            summary = result.consume()

            if hasattr(summary, 'profile'):
                profile = summary.profile
                return {
                    'db_hits': profile.get('dbHits', 0),
                    'rows': profile.get('rows', 0),
                    'time_ms': summary.result_available_after + summary.result_consumed_after
                }
        except Exception as e:
            logger.error(f"Query analysis failed: {e}")
            return None


def main():
    """Main execution function."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Create Neo4j indexes and constraints for optimal performance'
    )
    parser.add_argument(
        '--drop',
        action='store_true',
        help='Drop existing indexes before creating new ones'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List existing indexes and constraints only'
    )

    args = parser.parse_args()

    # Initialize Neo4j client
    client = Neo4jClient()

    with client.get_session() as session:
        manager = IndexManager(session)

        if args.list:
            # Just list existing indexes
            manager.list_indexes()
        else:
            # Create all indexes
            manager.create_all_indexes(drop_existing=args.drop)


if __name__ == '__main__':
    main()
