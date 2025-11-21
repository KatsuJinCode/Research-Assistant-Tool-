"""
Neo4j Graph Database Layer

Production-ready graph database using Neo4j.
Requires Neo4j to be installed and running.

Installation:
    pip install neo4j python-dotenv

Configuration (.env file):
    NEO4J_URI=bolt://localhost:7687
    NEO4J_USER=neo4j
    NEO4J_PASSWORD=research123
    NEO4J_DATABASE=neo4j
"""

import os
from typing import Dict, List, Any, Optional, Tuple
from uuid import uuid4
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Neo4jDatabase:
    """
    Neo4j-based graph database for research claim verification.

    Provides the same interface as GraphDatabase but uses real Neo4j.
    """

    def __init__(self, uri: str = None, user: str = None,
                 password: str = None, database: str = "neo4j"):
        """
        Initialize Neo4j database connection.

        Args:
            uri: Neo4j URI (e.g., "bolt://localhost:7687")
            user: Neo4j username
            password: Neo4j password
            database: Database name (default: "neo4j")

        Uses environment variables if parameters not provided:
            - NEO4J_URI
            - NEO4J_USER
            - NEO4J_PASSWORD
            - NEO4J_DATABASE
        """
        try:
            from neo4j import GraphDatabase as Neo4jDriver
        except ImportError:
            raise ImportError(
                "Neo4j driver not installed. Install with: pip install neo4j"
            )

        # Get connection details from env or parameters
        self.uri = uri or os.getenv('NEO4J_URI', 'bolt://localhost:7687')
        self.user = user or os.getenv('NEO4J_USER', 'neo4j')
        self.password = password or os.getenv('NEO4J_PASSWORD', 'neo4j')
        self.database = database or os.getenv('NEO4J_DATABASE', 'neo4j')

        # Create driver
        self.driver = Neo4jDriver.driver(
            self.uri,
            auth=(self.user, self.password)
        )

        # Verify connection
        self.driver.verify_connectivity()

    def close(self):
        """Close database connection."""
        if self.driver:
            self.driver.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def create_node(self, label: str, properties: Dict[str, Any]) -> str:
        """
        Create a node with a label and properties.

        Args:
            label: Node label (Document, Claim, etc.)
            properties: Node properties as dict

        Returns:
            node_id: UUID of created node
        """
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

        with self.driver.session(database=self.database) as session:
            result = session.run(query, props=properties)
            record = result.single()
            return record['id'] if record else node_id

    def create_relationship(self, from_node: str, to_node: str,
                          rel_type: str, properties: Dict[str, Any] = None) -> str:
        """
        Create a relationship between two nodes.

        Args:
            from_node: Source node ID
            to_node: Target node ID
            rel_type: Relationship type
            properties: Optional relationship properties

        Returns:
            Relationship ID
        """
        props = properties or {}
        props['created_at'] = props.get('created_at', datetime.utcnow().isoformat())

        query = f"""
        MATCH (a {{id: $from_id}}), (b {{id: $to_id}})
        CREATE (a)-[r:{rel_type} $props]->(b)
        RETURN id(r) as rel_id
        """

        with self.driver.session(database=self.database) as session:
            result = session.run(
                query,
                from_id=from_node,
                to_id=to_node,
                props=props
            )
            record = result.single()
            return str(record['rel_id']) if record else str(uuid4())

    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get node properties by ID."""
        query = """
        MATCH (n {id: $node_id})
        RETURN n
        """

        with self.driver.session(database=self.database) as session:
            result = session.run(query, node_id=node_id)
            record = result.single()
            if record:
                node = dict(record['n'])
                node['id'] = node_id
                return node
            return None

    def update_node_properties(self, node_id: str, properties: Dict[str, Any]) -> None:
        """
        Update properties of an existing node.

        Args:
            node_id: ID of the node to update
            properties: Dictionary of properties to set/update
        """
        # Build SET clause for all properties
        set_clauses = []
        params = {'node_id': node_id}

        for key, value in properties.items():
            param_name = f'prop_{key}'
            set_clauses.append(f'n.{key} = ${param_name}')
            params[param_name] = value

        query = f"""
        MATCH (n {{id: $node_id}})
        SET {', '.join(set_clauses)}
        RETURN n
        """

        with self.driver.session(database=self.database) as session:
            session.run(query, **params)

    def find_nodes(self, label: str, properties: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Find nodes by label and optional property filters.

        Args:
            label: Node label to filter by
            properties: Optional property filters

        Returns:
            List of matching nodes
        """
        if properties:
            # Build WHERE clause
            where_parts = [f"n.{k} = ${k}" for k in properties.keys()]
            where_clause = " AND ".join(where_parts)
            query = f"""
            MATCH (n:{label})
            WHERE {where_clause}
            RETURN n
            """
            params = properties
        else:
            query = f"""
            MATCH (n:{label})
            RETURN n
            """
            params = {}

        with self.driver.session(database=self.database) as session:
            result = session.run(query, **params)
            nodes = []
            for record in result:
                node = dict(record['n'])
                nodes.append(node)
            return nodes

    def get_relationships(self, node_id: str, rel_type: str = None,
                         direction: str = 'out') -> List[Tuple[str, Dict]]:
        """
        Get relationships from a node.

        Args:
            node_id: Node to get relationships from
            rel_type: Optional relationship type filter
            direction: 'out' (outgoing), 'in' (incoming), or 'both'

        Returns:
            List of (target_node_id, relationship_properties) tuples
        """
        if direction == 'out':
            rel_pattern = f"-[r{':' + rel_type if rel_type else ''}]->"
            other_node = "other"
        elif direction == 'in':
            rel_pattern = f"<-[r{':' + rel_type if rel_type else ''}]-"
            other_node = "other"
        else:  # both
            rel_pattern = f"-[r{':' + rel_type if rel_type else ''}]-"
            other_node = "other"

        query = f"""
        MATCH (n {{id: $node_id}}){rel_pattern}({other_node})
        RETURN other.id as target_id, properties(r) as rel_props
        """

        with self.driver.session(database=self.database) as session:
            result = session.run(query, node_id=node_id)
            relationships = []
            for record in result:
                relationships.append((
                    record['target_id'],
                    dict(record['rel_props'])
                ))
            return relationships

    def find_similar_claims(self, claim_id: str, min_score: float = 0.7) -> List[Dict[str, Any]]:
        """
        Find claims similar to the given claim.

        Args:
            claim_id: Source claim ID
            min_score: Minimum similarity score

        Returns:
            List of similar claims with scores
        """
        query = """
        MATCH (c1:Claim {id: $claim_id})-[s:SIMILAR_TO]-(c2:Claim)
        WHERE s.score >= $min_score
        RETURN c2, s.score as similarity_score
        ORDER BY s.score DESC
        """

        with self.driver.session(database=self.database) as session:
            result = session.run(query, claim_id=claim_id, min_score=min_score)
            claims = []
            for record in result:
                claim = dict(record['c2'])
                claim['similarity_score'] = record['similarity_score']
                claims.append(claim)
            return claims

    def find_claim_cluster(self, claim_id: str, min_score: float = 0.7) -> List[str]:
        """
        Find all claims in the same cluster.

        Uses graph algorithms to find connected components.

        Args:
            claim_id: Starting claim ID
            min_score: Minimum similarity score

        Returns:
            List of claim IDs in the cluster
        """
        query = """
        MATCH path = (start:Claim {id: $claim_id})-[:SIMILAR_TO*..10]-(connected:Claim)
        WHERE ALL(r IN relationships(path) WHERE r.score >= $min_score)
        RETURN DISTINCT connected.id as claim_id
        UNION
        RETURN $claim_id as claim_id
        """

        with self.driver.session(database=self.database) as session:
            result = session.run(query, claim_id=claim_id, min_score=min_score)
            claim_ids = [record['claim_id'] for record in result]
            return claim_ids

    def create_super_claim(self, claim_ids: List[str], normalized_text: str,
                          confidence: float = 1.0) -> str:
        """
        Create a super-claim from a cluster of similar claims.

        Args:
            claim_ids: List of claim IDs to merge
            normalized_text: Normalized text for super-claim
            confidence: Confidence score

        Returns:
            super_claim_id: ID of created super-claim
        """
        super_claim_id = str(uuid4())

        query = """
        CREATE (sc:SuperClaim {
            id: $super_id,
            text: $text,
            confidence: $confidence,
            member_count: $count,
            created_at: $created_at
        })
        WITH sc
        UNWIND $claim_ids as claim_id
        MATCH (c:Claim {id: claim_id})
        CREATE (c)-[:MERGED_INTO {
            verbatim: c.text,
            original_confidence: c.confidence,
            created_at: $created_at
        }]->(sc)
        RETURN sc.id as id
        """

        with self.driver.session(database=self.database) as session:
            result = session.run(
                query,
                super_id=super_claim_id,
                text=normalized_text,
                confidence=confidence,
                count=len(claim_ids),
                claim_ids=claim_ids,
                created_at=datetime.utcnow().isoformat()
            )
            record = result.single()
            return record['id'] if record else super_claim_id

    def get_claim_hierarchy(self, claim_id: str, max_depth: int = 5) -> Dict[str, Any]:
        """
        Get hierarchical tree of claims.

        Args:
            claim_id: Root claim ID
            max_depth: Maximum depth to traverse

        Returns:
            Hierarchical dict
        """
        query = """
        MATCH path = (root:Claim {id: $claim_id})-[:PARENT_OF*0..{max_depth}]->(child:Claim)
        RETURN path
        """.replace('{max_depth}', str(max_depth))

        with self.driver.session(database=self.database) as session:
            result = session.run(query, claim_id=claim_id)

            # Build tree structure
            # This is simplified; real implementation would be more complex
            claim = self.get_node(claim_id)
            if not claim:
                return None

            children = []
            child_rels = self.get_relationships(claim_id, 'PARENT_OF', 'out')
            for child_id, _ in child_rels:
                child_hierarchy = self.get_claim_hierarchy(child_id, max_depth - 1)
                if child_hierarchy:
                    children.append(child_hierarchy)

            result = dict(claim)
            if children:
                result['children'] = children

            return result

    def stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        query = """
        // Count nodes by label
        CALL db.labels() YIELD label
        CALL apoc.cypher.run('MATCH (n:' + label + ') RETURN count(n) as count', {})
        YIELD value
        RETURN label, value.count as count

        UNION ALL

        // Count relationships by type
        CALL db.relationshipTypes() YIELD relationshipType
        CALL apoc.cypher.run('MATCH ()-[r:' + relationshipType + ']->() RETURN count(r) as count', {})
        YIELD value
        RETURN relationshipType as label, value.count as count
        """

        # Simplified version without APOC
        simple_query = """
        MATCH (n)
        RETURN labels(n)[0] as label, count(n) as count
        """

        node_counts = {}
        rel_counts = {}

        with self.driver.session(database=self.database) as session:
            # Count nodes
            result = session.run(simple_query)
            for record in result:
                node_counts[record['label']] = record['count']

            # Count relationships
            rel_query = """
            MATCH ()-[r]->()
            RETURN type(r) as rel_type, count(r) as count
            """
            result = session.run(rel_query)
            for record in result:
                rel_counts[record['rel_type']] = record['count']

            # Total counts
            total_nodes_query = "MATCH (n) RETURN count(n) as count"
            total_rels_query = "MATCH ()-[r]->() RETURN count(r) as count"

            total_nodes = session.run(total_nodes_query).single()['count']
            total_rels = session.run(total_rels_query).single()['count']

        return {
            'total_nodes': total_nodes,
            'total_relationships': total_rels,
            'node_labels': node_counts,
            'relationship_types': rel_counts
        }

    def clear_database(self):
        """[WARNING]  Clear all data from database (use with caution!)."""
        query = "MATCH (n) DETACH DELETE n"

        with self.driver.session(database=self.database) as session:
            session.run(query)
