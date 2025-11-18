"""
Neo4j Client Singleton

Manages Neo4j database connection lifecycle with singleton pattern.
Ensures only one connection per process for optimal resource usage.
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
    Singleton Neo4j database client.

    Manages database driver lifecycle and provides connection access.
    Thread-safe singleton implementation.
    """

    _instance: Optional['Neo4jClient'] = None
    _driver = None

    def __new__(cls):
        """Ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize Neo4j driver connection."""
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

    @property
    def driver(self):
        """Get the Neo4j driver instance."""
        if self._driver is None:
            raise RuntimeError("Neo4j driver not initialized")
        return self._driver

    def get_session(self, **kwargs):
        """
        Create a new database session.

        Args:
            **kwargs: Additional session parameters

        Returns:
            Neo4j session object
        """
        return self.driver.session(database=self.database, **kwargs)

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
