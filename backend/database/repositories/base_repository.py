"""
Base Repository

Abstract base class for all repositories.
Provides common database operations and error handling.
"""

from abc import ABC
from typing import Dict, List, Any, Optional
from uuid import uuid4
from datetime import datetime
import logging

from backend.database.neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)


class BaseRepository(ABC):
    """
    Abstract base repository for Neo4j operations.

    Provides common CRUD operations and query helpers.
    Subclasses define entity-specific queries.
    """

    def __init__(self, client: Optional[Neo4jClient] = None):
        """
        Initialize repository.

        Args:
            client: Neo4jClient instance (defaults to singleton)
        """
        self.client = client or Neo4jClient()

    def execute_query(self, query: str, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Execute a Cypher query and return results.

        Args:
            query: Cypher query string
            parameters: Query parameters

        Returns:
            List of result dictionaries

        Raises:
            Exception: If query execution fails
        """
        parameters = parameters or {}

        try:
            with self.client.get_session() as session:
                result = session.run(query, parameters)
                return [record.data() for record in result]
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Parameters: {parameters}")
            raise

    def execute_write(self, query: str, parameters: Dict[str, Any] = None) -> Any:
        """
        Execute a write query and return single result.

        Args:
            query: Cypher query string
            parameters: Query parameters

        Returns:
            Single result value or None

        Raises:
            Exception: If query execution fails
        """
        parameters = parameters or {}

        try:
            with self.client.get_session() as session:
                result = session.run(query, parameters)
                record = result.single()
                return record[0] if record else None
        except Exception as e:
            logger.error(f"Write query execution failed: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Parameters: {parameters}")
            raise

    def create_node(self, label: str, properties: Dict[str, Any]) -> str:
        """
        Create a node with auto-generated ID and timestamp.

        Args:
            label: Node label
            properties: Node properties

        Returns:
            Node ID (UUID)
        """
        # Ensure ID and timestamp
        node_id = properties.get('id', str(uuid4()))
        properties['id'] = node_id
        properties['created_at'] = properties.get(
            'created_at',
            datetime.utcnow().isoformat()
        )

        query = f"""
        CREATE (n:{label} $props)
        RETURN n.id as id
        """

        result = self.execute_write(query, {'props': properties})
        logger.info(f"Created {label} node: {result}")
        return result

    def get_node_by_id(self, label: str, node_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a node by ID.

        Args:
            label: Node label
            node_id: Node ID

        Returns:
            Node properties as dict, or None if not found
        """
        query = f"""
        MATCH (n:{label} {{id: $id}})
        RETURN n
        """

        results = self.execute_query(query, {'id': node_id})
        return results[0]['n'] if results else None

    def update_node(self, label: str, node_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update node properties.

        Args:
            label: Node label
            node_id: Node ID
            updates: Properties to update

        Returns:
            True if node was updated, False if not found
        """
        # Add updated_at timestamp
        updates['updated_at'] = datetime.utcnow().isoformat()

        query = f"""
        MATCH (n:{label} {{id: $id}})
        SET n += $updates
        RETURN n.id as id
        """

        result = self.execute_write(query, {'id': node_id, 'updates': updates})
        if result:
            logger.info(f"Updated {label} node: {node_id}")
            return True
        return False

    def delete_node(self, label: str, node_id: str) -> bool:
        """
        Delete a node and its relationships.

        Args:
            label: Node label
            node_id: Node ID

        Returns:
            True if node was deleted, False if not found
        """
        query = f"""
        MATCH (n:{label} {{id: $id}})
        DETACH DELETE n
        RETURN count(n) as deleted
        """

        result = self.execute_write(query, {'id': node_id})
        if result and result > 0:
            logger.info(f"Deleted {label} node: {node_id}")
            return True
        return False

    def find_nodes(self, label: str, filters: Dict[str, Any], limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Find nodes matching filters.

        Args:
            label: Node label
            filters: Property filters (exact match)
            limit: Maximum results to return

        Returns:
            List of matching nodes
        """
        # Build WHERE clauses
        where_clauses = [f"n.{key} = ${key}" for key in filters.keys()]
        where_str = " AND ".join(where_clauses) if where_clauses else "true"

        limit_str = f"LIMIT {limit}" if limit else ""

        query = f"""
        MATCH (n:{label})
        WHERE {where_str}
        RETURN n
        {limit_str}
        """

        results = self.execute_query(query, filters)
        return [r['n'] for r in results]

    def create_relationship(
        self,
        from_id: str,
        to_id: str,
        relationship_type: str,
        properties: Dict[str, Any] = None
    ) -> bool:
        """
        Create a relationship between two nodes.

        Args:
            from_id: Source node ID
            to_id: Target node ID
            relationship_type: Relationship type
            properties: Relationship properties

        Returns:
            True if relationship created
        """
        properties = properties or {}

        query = f"""
        MATCH (a {{id: $from_id}}), (b {{id: $to_id}})
        CREATE (a)-[r:{relationship_type} $props]->(b)
        RETURN id(r) as rel_id
        """

        result = self.execute_write(query, {
            'from_id': from_id,
            'to_id': to_id,
            'props': properties
        })

        if result:
            logger.info(f"Created {relationship_type} relationship: {from_id} -> {to_id}")
            return True
        return False
