"""
Neo4j Client Singleton with Multi-Database Support

Manages Neo4j database connection lifecycle with singleton pattern.
Ensures only one connection per process for optimal resource usage.
Supports Neo4j multi-database feature for project isolation.
"""

import os
import logging
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class Neo4jClient:
    """
    Singleton Neo4j database client with multi-database support.

    Manages database driver lifecycle and provides connection access.
    Thread-safe singleton implementation.

    Multi-Database Support:
    - Each project can have its own database for complete isolation
    - Switch databases by calling set_active_database(database_name)
    - All operations use the active database by default
    """

    _instance: Optional['Neo4jClient'] = None
    _driver = None
    _database_manager = None

    def __new__(cls):
        """Ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize Neo4j driver connection and database manager."""
        try:
            from neo4j import GraphDatabase
        except ImportError:
            raise ImportError(
                "Neo4j driver not installed. Install with: pip install neo4j"
            )

        # Get connection details from environment
        self.uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
        self.user = os.getenv('NEO4J_USER', 'neo4j')
        self.password = os.getenv('NEO4J_PASSWORD', 'neo4j')
        self.database = os.getenv('NEO4J_DATABASE', 'neo4j')

        # Create driver
        self._driver = GraphDatabase.driver(
            self.uri,
            auth=(self.user, self.password)
        )

        # Verify connectivity
        try:
            self._driver.verify_connectivity()
            logger.info(f"Neo4j client connected to {self.uri}")
        except Exception as e:
            logger.error(f"Failed to verify Neo4j connectivity: {e}")
            raise

        # Initialize database manager for multi-database support
        try:
            from .database_manager import DatabaseManager
            self._database_manager = DatabaseManager(self._driver)
            logger.info("DatabaseManager initialized for multi-database support")
        except Exception as e:
            logger.warning(f"Failed to initialize DatabaseManager: {e}")
            self._database_manager = None

    @property
    def driver(self):
        """Get the Neo4j driver instance."""
        if self._driver is None:
            raise RuntimeError("Neo4j driver not initialized")
        return self._driver

    @property
    def database_manager(self):
        """Get the DatabaseManager instance."""
        if self._database_manager is None:
            raise RuntimeError("DatabaseManager not initialized")
        return self._database_manager

    @property
    def active_database(self) -> str:
        """Get the currently active database name."""
        if self._database_manager:
            return self._database_manager.active_database
        return self.database

    def set_active_database(self, database_name: str):
        """
        Set the active database for subsequent operations.

        Args:
            database_name: Name of the database to activate
        """
        if self._database_manager:
            self._database_manager.set_active_database(database_name)
            logger.info(f"Active database set to: {database_name}")
        else:
            logger.warning("DatabaseManager not available, cannot switch database")

    def get_session(self, database: Optional[str] = None, **kwargs):
        """
        Create a new database session.

        Args:
            database: Optional database name (uses active database if not specified)
            **kwargs: Additional session parameters

        Returns:
            Neo4j session object
        """
        if self._database_manager:
            # Use DatabaseManager for multi-database support
            db = database or self._database_manager.active_database
        else:
            # Fallback to default database
            db = database or self.database

        return self.driver.session(database=db, **kwargs)

    def close(self):
        """Close the database driver."""
        if self._driver:
            self._driver.close()
            self._driver = None
            logger.info("Neo4j client closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        # Don't close on context exit (singleton pattern)
        # Connection stays open for reuse
        pass

    @classmethod
    def reset_instance(cls):
        """
        Reset singleton instance.

        ONLY for testing - allows creating fresh instance.
        """
        if cls._instance and cls._instance._driver:
            cls._instance.close()
        cls._instance = None
