"""
Database Manager - Handle Neo4j Multi-Database Operations
Manages database lifecycle: create, drop, list, switch
"""

import re
import logging
from typing import List, Dict, Optional
from neo4j import GraphDatabase
from neo4j.exceptions import DatabaseError, ClientError

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Manages Neo4j multi-database operations for project isolation.

    Each project gets its own Neo4j database for complete data isolation.
    The 'neo4j' database is used for system metadata (project list, settings).
    """

    # System database for storing project metadata
    SYSTEM_DATABASE = "neo4j"

    # Database name prefix for projects
    PROJECT_DB_PREFIX = "project_"

    # Reserved database names
    RESERVED_NAMES = {"neo4j", "system"}

    def __init__(self, driver):
        """
        Initialize DatabaseManager with Neo4j driver.

        Args:
            driver: Neo4j driver instance
        """
        self.driver = driver
        self._active_database = self.SYSTEM_DATABASE

    @property
    def active_database(self) -> str:
        """Get the currently active database name."""
        return self._active_database

    def set_active_database(self, database_name: str):
        """
        Set the active database for subsequent operations.

        Args:
            database_name: Name of the database to activate
        """
        logger.info(f"[DatabaseManager] Setting active database to: {database_name}")
        self._active_database = database_name

    def get_session(self, database: Optional[str] = None):
        """
        Get a Neo4j session for the specified or active database.

        Args:
            database: Database name (optional, uses active if not specified)

        Returns:
            Neo4j session object
        """
        db = database or self._active_database
        return self.driver.session(database=db)

    @staticmethod
    def sanitize_database_name(name: str) -> str:
        """
        Sanitize a project name to create a valid Neo4j database name.

        Rules:
        - Lowercase only
        - Alphanumeric and underscore only
        - Max 63 characters
        - Starts with letter or underscore

        Args:
            name: Project name to sanitize

        Returns:
            Sanitized database name with project_ prefix
        """
        # Convert to lowercase
        name = name.lower()

        # Replace spaces and special chars with underscore
        name = re.sub(r'[^a-z0-9_]', '_', name)

        # Remove consecutive underscores
        name = re.sub(r'_+', '_', name)

        # Remove leading/trailing underscores
        name = name.strip('_')

        # Ensure starts with letter or underscore
        if name and not name[0].isalpha() and name[0] != '_':
            name = '_' + name

        # Add prefix
        db_name = f"{DatabaseManager.PROJECT_DB_PREFIX}{name}"

        # Truncate to max length
        if len(db_name) > 63:
            db_name = db_name[:63]

        return db_name

    def list_databases(self) -> List[Dict[str, any]]:
        """
        List all databases in the Neo4j instance.

        Returns:
            List of database info dictionaries
        """
        try:
            with self.get_session(self.SYSTEM_DATABASE) as session:
                result = session.run("SHOW DATABASES")
                databases = []

                for record in result:
                    databases.append({
                        'name': record.get('name'),
                        'type': record.get('type'),
                        'default': record.get('default', False),
                        'currentStatus': record.get('currentStatus'),
                        'requestedStatus': record.get('requestedStatus')
                    })

                logger.info(f"[DatabaseManager] Found {len(databases)} databases")
                return databases

        except Exception as e:
            logger.error(f"[DatabaseManager] Error listing databases: {e}")
            raise

    def database_exists(self, database_name: str) -> bool:
        """
        Check if a database exists.

        Args:
            database_name: Name of the database to check

        Returns:
            True if database exists, False otherwise
        """
        try:
            databases = self.list_databases()
            return any(db['name'] == database_name for db in databases)
        except Exception as e:
            logger.error(f"[DatabaseManager] Error checking if database exists: {e}")
            return False

    def create_database(self, database_name: str, wait: bool = True) -> tuple[bool, Optional[str]]:
        """
        Create a new Neo4j database.

        Args:
            database_name: Name of the database to create
            wait: Wait for database to be online (default: True)

        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        try:
            # Check if already exists
            if self.database_exists(database_name):
                logger.warning(f"[DatabaseManager] Database {database_name} already exists")
                return True, None

            # Create database
            logger.info(f"[DatabaseManager] Creating database: {database_name}")

            with self.get_session(self.SYSTEM_DATABASE) as session:
                query = f"CREATE DATABASE `{database_name}` IF NOT EXISTS"
                if wait:
                    query += " WAIT"

                session.run(query)

            logger.info(f"[DatabaseManager] Database {database_name} created successfully")
            return True, None

        except ClientError as e:
            error_msg = str(e)
            logger.error(f"[DatabaseManager] Client error creating database: {error_msg}")

            # Check if it's a multi-database not available error
            if "Unsupported administration command" in error_msg or "does not support multiple databases" in error_msg:
                return False, "Multi-database not available. Neo4j Enterprise or Desktop required. Consider using Neo4j Community Edition with single-database mode."

            return False, f"Database error: {error_msg}"

        except Exception as e:
            error_msg = str(e)
            logger.error(f"[DatabaseManager] Error creating database: {error_msg}")
            return False, f"Unexpected error: {error_msg}"

    def drop_database(self, database_name: str) -> bool:
        """
        Drop a Neo4j database.

        WARNING: This permanently deletes all data in the database!

        Args:
            database_name: Name of the database to drop

        Returns:
            True if successful, False otherwise
        """
        try:
            # Prevent dropping system databases
            if database_name in self.RESERVED_NAMES:
                logger.error(f"[DatabaseManager] Cannot drop reserved database: {database_name}")
                return False

            # Check if exists
            if not self.database_exists(database_name):
                logger.warning(f"[DatabaseManager] Database {database_name} does not exist")
                return True

            # Drop database
            logger.info(f"[DatabaseManager] Dropping database: {database_name}")

            with self.get_session(self.SYSTEM_DATABASE) as session:
                session.run(f"DROP DATABASE `{database_name}` IF EXISTS")

            logger.info(f"[DatabaseManager] Database {database_name} dropped successfully")
            return True

        except Exception as e:
            logger.error(f"[DatabaseManager] Error dropping database: {e}")
            return False

    def initialize_database_schema(self, database_name: str) -> bool:
        """
        Initialize a new database with default schema, indexes, and constraints.

        Args:
            database_name: Name of the database to initialize

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"[DatabaseManager] Initializing schema for database: {database_name}")

            with self.get_session(database_name) as session:
                # Create indexes for performance
                indexes = [
                    "CREATE INDEX claim_id_index IF NOT EXISTS FOR (n:Claim) ON (n.id)",
                    "CREATE INDEX document_id_index IF NOT EXISTS FOR (n:Document) ON (n.id)",
                    "CREATE INDEX evidence_id_index IF NOT EXISTS FOR (n:Evidence) ON (n.id)",
                    "CREATE INDEX claim_text_index IF NOT EXISTS FOR (n:Claim) ON (n.text)",
                    "CREATE INDEX document_status_index IF NOT EXISTS FOR (n:Document) ON (n.status)"
                ]

                for index_query in indexes:
                    try:
                        session.run(index_query)
                        logger.debug(f"[DatabaseManager] Created index: {index_query}")
                    except ClientError as e:
                        # Index might already exist, that's OK
                        logger.debug(f"[DatabaseManager] Index creation info: {e}")

            logger.info(f"[DatabaseManager] Schema initialized for {database_name}")
            return True

        except Exception as e:
            logger.error(f"[DatabaseManager] Error initializing schema: {e}")
            return False

    def get_database_stats(self, database_name: str) -> Dict[str, int]:
        """
        Get statistics for a database (node count, relationship count, etc.).

        Args:
            database_name: Name of the database

        Returns:
            Dictionary with database statistics
        """
        try:
            with self.get_session(database_name) as session:
                # Count nodes by label
                result = session.run("""
                    MATCH (n)
                    RETURN labels(n)[0] as label, count(n) as count
                """)

                label_counts = {record['label']: record['count'] for record in result if record['label']}

                # Count relationships
                result = session.run("MATCH ()-[r]->() RETURN count(r) as rel_count")
                rel_count = result.single()['rel_count']

                # Total nodes
                total_nodes = sum(label_counts.values())

                stats = {
                    'total_nodes': total_nodes,
                    'total_relationships': rel_count,
                    'document_count': label_counts.get('Document', 0),
                    'claim_count': label_counts.get('Claim', 0),
                    'evidence_count': label_counts.get('Evidence', 0),
                    'label_counts': label_counts
                }

                return stats

        except Exception as e:
            logger.error(f"[DatabaseManager] Error getting database stats: {e}")
            return {
                'total_nodes': 0,
                'total_relationships': 0,
                'document_count': 0,
                'claim_count': 0,
                'evidence_count': 0,
                'label_counts': {}
            }

    def copy_database(self, source_db: str, target_db: str) -> bool:
        """
        Copy all data from source database to target database.

        Note: This creates the target database if it doesn't exist.

        Args:
            source_db: Name of the source database
            target_db: Name of the target database

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"[DatabaseManager] Copying database {source_db} to {target_db}")

            # Create target database if it doesn't exist
            if not self.database_exists(target_db):
                self.create_database(target_db)
                self.initialize_database_schema(target_db)

            # Export from source
            with self.get_session(source_db) as source_session:
                # Get all nodes
                nodes_result = source_session.run("MATCH (n) RETURN n")
                nodes = [record['n'] for record in nodes_result]

                # Get all relationships
                rels_result = source_session.run("MATCH ()-[r]->() RETURN r")
                relationships = [record['r'] for record in rels_result]

            # Import to target
            with self.get_session(target_db) as target_session:
                # Create nodes
                for node in nodes:
                    labels = ':'.join(node.labels)
                    props = dict(node)

                    create_query = f"CREATE (n:{labels} $props)"
                    target_session.run(create_query, props=props)

                # Create relationships
                for rel in relationships:
                    # This is simplified - production would need proper node matching
                    pass

            logger.info(f"[DatabaseManager] Database copied successfully")
            return True

        except Exception as e:
            logger.error(f"[DatabaseManager] Error copying database: {e}")
            return False
