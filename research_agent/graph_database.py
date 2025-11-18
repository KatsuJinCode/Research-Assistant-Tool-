"""
Graph Database Layer using NetworkX (Neo4j-compatible design)

This module provides a graph database interface that mirrors Neo4j's design
but uses NetworkX for prototyping. Can be migrated to Neo4j later.

Node Types:
- Document: Research papers
- Claim: Individual claims from papers
- SuperClaim: Normalized merged claims
- Qualifier: Modal/frequency/quantity qualifiers
- Evidence: Supporting/contradicting evidence
- Source: External sources

Relationship Types:
- CONTAINS: Document -> Claim
- SIMILAR_TO: Claim -> Claim (with similarity score)
- MERGED_INTO: Claim -> SuperClaim
- HAS_QUALIFIER: Claim -> Qualifier
- PARENT_OF: Claim -> Claim (hierarchical)
- SUPPORTS: Claim -> Claim
- CONTRADICTS: Claim -> Claim
"""

import networkx as nx
from typing import Dict, List, Any, Optional, Tuple
from uuid import uuid4
from datetime import datetime
import json


class GraphDatabase:
    """
    Graph database for research claim verification.

    Uses NetworkX MultiDiGraph to support multiple relationships between nodes.
    Designed to mirror Neo4j's labeled property graph model.
    """

    def __init__(self):
        """Initialize the graph database."""
        self.graph = nx.MultiDiGraph()
        self._node_labels = {}  # node_id -> label (Document, Claim, etc.)

    def create_node(self, label: str, properties: Dict[str, Any]) -> str:
        """
        Create a node with a label and properties.

        Args:
            label: Node type (Document, Claim, SuperClaim, etc.)
            properties: Node properties as dict

        Returns:
            node_id: UUID of created node
        """
        node_id = properties.get('id', str(uuid4()))
        properties['id'] = node_id
        properties['created_at'] = properties.get('created_at', datetime.utcnow().isoformat())

        self.graph.add_node(node_id, label=label, **properties)
        self._node_labels[node_id] = label

        return node_id

    def create_relationship(self, from_node: str, to_node: str,
                          rel_type: str, properties: Dict[str, Any] = None) -> int:
        """
        Create a relationship between two nodes.

        Args:
            from_node: Source node ID
            to_node: Target node ID
            rel_type: Relationship type (CONTAINS, SIMILAR_TO, etc.)
            properties: Optional relationship properties

        Returns:
            edge_key: Key of created edge
        """
        props = properties or {}
        props['type'] = rel_type
        props['created_at'] = props.get('created_at', datetime.utcnow().isoformat())

        edge_key = self.graph.add_edge(from_node, to_node, **props)
        return edge_key

    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get node properties by ID."""
        if node_id not in self.graph:
            return None

        data = dict(self.graph.nodes[node_id])
        data['id'] = node_id
        return data

    def find_nodes(self, label: str, properties: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Find nodes by label and optional property filters.

        Args:
            label: Node label to filter by
            properties: Optional property filters

        Returns:
            List of matching nodes with their properties
        """
        results = []

        for node_id, data in self.graph.nodes(data=True):
            if data.get('label') != label:
                continue

            # Check property filters
            if properties:
                match = all(data.get(k) == v for k, v in properties.items())
                if not match:
                    continue

            node_data = dict(data)
            node_data['id'] = node_id
            results.append(node_data)

        return results

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
        results = []

        if direction in ['out', 'both']:
            for target, edges in self.graph[node_id].items():
                for edge_key, edge_data in edges.items():
                    if rel_type and edge_data.get('type') != rel_type:
                        continue
                    results.append((target, dict(edge_data)))

        if direction in ['in', 'both']:
            for source in self.graph.predecessors(node_id):
                for edge_key, edge_data in self.graph[source][node_id].items():
                    if rel_type and edge_data.get('type') != rel_type:
                        continue
                    results.append((source, dict(edge_data)))

        return results

    def find_similar_claims(self, claim_id: str, min_score: float = 0.7) -> List[Dict[str, Any]]:
        """
        Find claims similar to the given claim.

        Args:
            claim_id: Source claim ID
            min_score: Minimum similarity score (0.0-1.0)

        Returns:
            List of similar claims with similarity scores
        """
        results = []

        for target, rel_data in self.get_relationships(claim_id, 'SIMILAR_TO', 'both'):
            score = rel_data.get('score', 0.0)
            if score >= min_score:
                claim_data = self.get_node(target)
                claim_data['similarity_score'] = score
                results.append(claim_data)

        return sorted(results, key=lambda x: x['similarity_score'], reverse=True)

    def find_claim_cluster(self, claim_id: str, min_score: float = 0.7) -> List[str]:
        """
        Find all claims in the same cluster (connected by SIMILAR_TO).

        Uses graph traversal to find all connected similar claims.

        Args:
            claim_id: Starting claim ID
            min_score: Minimum similarity score

        Returns:
            List of claim IDs in the cluster
        """
        # Create subgraph of similarity relationships above threshold
        similar_edges = []
        for u, v, data in self.graph.edges(data=True):
            if data.get('type') == 'SIMILAR_TO' and data.get('score', 0) >= min_score:
                similar_edges.append((u, v))

        subgraph = nx.Graph(similar_edges)  # Undirected for clustering

        if claim_id not in subgraph:
            return [claim_id]  # Single node cluster

        # Find connected component containing this claim
        for component in nx.connected_components(subgraph):
            if claim_id in component:
                return list(component)

        return [claim_id]

    def create_super_claim(self, claim_ids: List[str], normalized_text: str,
                          confidence: float = 1.0) -> str:
        """
        Create a super-claim from a cluster of similar claims.

        Args:
            claim_ids: List of claim IDs to merge
            normalized_text: Normalized text for the super-claim
            confidence: Confidence score for the super-claim

        Returns:
            super_claim_id: ID of created super-claim
        """
        # Create super-claim node
        super_claim_id = self.create_node('SuperClaim', {
            'text': normalized_text,
            'confidence': confidence,
            'member_count': len(claim_ids)
        })

        # Link all claims to super-claim
        for claim_id in claim_ids:
            claim_data = self.get_node(claim_id)
            if claim_data:
                self.create_relationship(claim_id, super_claim_id, 'MERGED_INTO', {
                    'verbatim': claim_data.get('text', ''),
                    'original_confidence': claim_data.get('confidence', 0.0)
                })

        return super_claim_id

    def get_claim_hierarchy(self, claim_id: str, max_depth: int = 5) -> Dict[str, Any]:
        """
        Get hierarchical tree of claims (parent/child relationships).

        Args:
            claim_id: Root claim ID
            max_depth: Maximum depth to traverse

        Returns:
            Hierarchical dict with claim and its children
        """
        claim = self.get_node(claim_id)
        if not claim:
            return None

        result = dict(claim)

        if max_depth > 0:
            # Get child claims
            children = []
            for child_id, _ in self.get_relationships(claim_id, 'PARENT_OF', 'out'):
                child_hierarchy = self.get_claim_hierarchy(child_id, max_depth - 1)
                if child_hierarchy:
                    children.append(child_hierarchy)

            if children:
                result['children'] = children

        return result

    def export_to_cypher(self, output_file: str):
        """
        Export graph to Cypher statements for Neo4j import.

        Args:
            output_file: Path to output .cypher file
        """
        statements = []

        # Create nodes
        for node_id, data in self.graph.nodes(data=True):
            label = data.get('label', 'Node')
            props = {k: v for k, v in data.items() if k != 'label'}
            props['id'] = node_id

            # Format properties for Cypher
            prop_str = ', '.join(f'{k}: {json.dumps(v)}' for k, v in props.items())
            statements.append(f"CREATE (n:{label} {{{prop_str}}})")

        # Create relationships
        for u, v, data in self.graph.edges(data=True):
            rel_type = data.get('type', 'RELATED_TO')
            props = {k: v for k, v in data.items() if k != 'type'}

            prop_str = ', '.join(f'{k}: {json.dumps(v)}' for k, v in props.items())
            prop_clause = f' {{{prop_str}}}' if prop_str else ''

            statements.append(
                f"MATCH (a {{id: {json.dumps(u)}}}), (b {{id: {json.dumps(v)}}})\n"
                f"CREATE (a)-[:{rel_type}{prop_clause}]->(b)"
            )

        with open(output_file, 'w') as f:
            f.write('// Graph export for Neo4j\n')
            f.write('// Generated: ' + datetime.utcnow().isoformat() + '\n\n')
            f.write('\n\n'.join(statements))

        return len(statements)

    def stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        label_counts = {}
        for node_id in self.graph.nodes():
            label = self._node_labels.get(node_id, 'Unknown')
            label_counts[label] = label_counts.get(label, 0) + 1

        rel_type_counts = {}
        for u, v, data in self.graph.edges(data=True):
            rel_type = data.get('type', 'Unknown')
            rel_type_counts[rel_type] = rel_type_counts.get(rel_type, 0) + 1

        return {
            'total_nodes': self.graph.number_of_nodes(),
            'total_relationships': self.graph.number_of_edges(),
            'node_labels': label_counts,
            'relationship_types': rel_type_counts
        }
