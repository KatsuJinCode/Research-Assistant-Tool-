"""
Knowledge Graph Embedding (KGE) Triple Extractor

Extracts (head, relation, tail) triples from the NetworkX-based graph database
for training PyKEEN embeddings (TransE, RotatE, etc.).

This module provides the foundation for advanced Graph RAG by converting
the research claim graph into a format suitable for knowledge graph embedding.
"""

from typing import List, Tuple, Dict, Any, Optional, Set
from research_agent.graph_database import GraphDatabase


class TripleExtractor:
    """Extract knowledge graph triples for embedding training."""

    # Metadata relationships to exclude from embeddings
    # These are system-level relationships that don't add semantic value
    EXCLUDED_RELATIONS = {
        'CREATED',  # Agent provenance - not semantic
    }

    def __init__(self, db: GraphDatabase):
        """
        Initialize extractor with graph database.

        Args:
            db: GraphDatabase instance
        """
        self.db = db
        self._cache_valid = False
        self._cached_triples: Optional[List[Tuple[str, str, str]]] = None

    def extract_from_neo4j(self) -> List[Tuple[str, str, str]]:
        """
        Extract all triples from the graph database.

        Returns:
            List of (head, relation, tail) triples as strings

        Example:
            >>> extractor = TripleExtractor(db)
            >>> triples = extractor.extract_from_neo4j()
            >>> print(triples[0])
            ('claim_123', 'SUPPORTS', 'claim_456')
        """
        # Return cached triples if valid
        if self._cache_valid and self._cached_triples is not None:
            return self._cached_triples.copy()

        triples = []

        # Extract edges from NetworkX MultiDiGraph
        for u, v, data in self.db.graph.edges(data=True):
            # Get relationship type
            rel_type = data.get('type')

            # Skip invalid triples
            if not self._is_valid_triple(u, v, rel_type):
                continue

            # Create triple: (head, relation, tail)
            triple = (str(u), str(rel_type), str(v))
            triples.append(triple)

        # Cache results
        self._cached_triples = triples
        self._cache_valid = True

        return triples.copy()

    def extract_by_relation_type(self, relation_types: List[str]) -> List[Tuple[str, str, str]]:
        """
        Extract triples filtered by relationship types.

        Args:
            relation_types: List of relation types to include
                          (e.g., ['SUPPORTS', 'CONTRADICTS'])

        Returns:
            Filtered list of triples

        Example:
            >>> triples = extractor.extract_by_relation_type(['SUPPORTS', 'CONTRADICTS'])
            >>> # Only reasoning relationships
        """
        relation_set = set(relation_types)
        all_triples = self.extract_from_neo4j()

        # Filter by relation type (index 1 in tuple)
        filtered = [
            triple for triple in all_triples
            if triple[1] in relation_set
        ]

        return filtered

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about extracted triples.

        Returns:
            Dict with counts by relation type, unique entities, etc.

        Example:
            >>> stats = extractor.get_statistics()
            >>> print(stats['total_triples'])
            1523
            >>> print(stats['relation_counts'])
            {'SUPPORTS': 345, 'CONTRADICTS': 123, ...}
        """
        triples = self.extract_from_neo4j()

        # Count by relation type
        relation_counts: Dict[str, int] = {}
        unique_entities: Set[str] = set()

        for head, relation, tail in triples:
            # Count relations
            relation_counts[relation] = relation_counts.get(relation, 0) + 1

            # Track unique entities
            unique_entities.add(head)
            unique_entities.add(tail)

        # Count unique relations
        unique_relations = set(relation_counts.keys())

        # Get node label distribution
        node_label_counts = self._get_node_label_counts()

        return {
            'total_triples': len(triples),
            'unique_entities': len(unique_entities),
            'unique_relations': len(unique_relations),
            'relation_counts': relation_counts,
            'node_label_counts': node_label_counts,
            'avg_triples_per_relation': (
                len(triples) / len(unique_relations) if unique_relations else 0
            ),
            'avg_degree': (
                (2 * len(triples)) / len(unique_entities) if unique_entities else 0
            ),
        }

    def get_semantic_triples(self) -> List[Tuple[str, str, str]]:
        """
        Extract only semantic relationships (reasoning relationships).

        Includes: SUPPORTS, CONTRADICTS, SIMILAR_TO
        Excludes: Structural relationships like CONTAINS, MERGED_INTO

        Returns:
            List of semantic triples
        """
        semantic_relations = ['SUPPORTS', 'CONTRADICTS', 'SIMILAR_TO']
        return self.extract_by_relation_type(semantic_relations)

    def get_hierarchical_triples(self) -> List[Tuple[str, str, str]]:
        """
        Extract only hierarchical relationships.

        Includes: PARENT_OF, CONTAINS, MERGED_INTO

        Returns:
            List of hierarchical triples
        """
        hierarchical_relations = ['PARENT_OF', 'CONTAINS', 'MERGED_INTO']
        return self.extract_by_relation_type(hierarchical_relations)

    def invalidate_cache(self):
        """
        Invalidate the triple cache.

        Call this when the graph database is modified to ensure
        fresh triples are extracted on next call.
        """
        self._cache_valid = False
        self._cached_triples = None

    def _is_valid_triple(self, head: str, tail: str, relation: Optional[str]) -> bool:
        """
        Check if a triple is valid for extraction.

        Args:
            head: Head entity ID
            tail: Tail entity ID
            relation: Relation type

        Returns:
            True if triple should be included
        """
        # Check nodes exist
        if head not in self.db.graph or tail not in self.db.graph:
            return False

        # Check relation is valid
        if not relation or relation == '':
            return False

        # Exclude metadata relationships
        if relation in self.EXCLUDED_RELATIONS:
            return False

        return True

    def _get_node_label_counts(self) -> Dict[str, int]:
        """
        Get count of nodes by label.

        Returns:
            Dict mapping label to count
        """
        label_counts: Dict[str, int] = {}

        for node_id, data in self.db.graph.nodes(data=True):
            label = data.get('label', 'Unknown')
            label_counts[label] = label_counts.get(label, 0) + 1

        return label_counts

    def export_to_pykeen_format(self, output_file: str, relation_filter: Optional[List[str]] = None):
        """
        Export triples to PyKEEN-compatible TSV format.

        PyKEEN expects a tab-separated file with format:
        head_entity<TAB>relation<TAB>tail_entity

        Args:
            output_file: Path to output TSV file
            relation_filter: Optional list of relations to include

        Example:
            >>> extractor.export_to_pykeen_format('triples.tsv')
            >>> # Creates: claim_123    SUPPORTS    claim_456
        """
        if relation_filter:
            triples = self.extract_by_relation_type(relation_filter)
        else:
            triples = self.extract_from_neo4j()

        with open(output_file, 'w', encoding='utf-8') as f:
            for head, relation, tail in triples:
                f.write(f"{head}\t{relation}\t{tail}\n")

        return len(triples)

    def get_entity_types(self) -> Dict[str, str]:
        """
        Get mapping of entity IDs to their types (labels).

        Useful for typed knowledge graph embeddings.

        Returns:
            Dict mapping entity_id -> label

        Example:
            >>> entity_types = extractor.get_entity_types()
            >>> print(entity_types['claim_123'])
            'Claim'
        """
        entity_types = {}

        for node_id, data in self.db.graph.nodes(data=True):
            label = data.get('label', 'Unknown')
            entity_types[node_id] = label

        return entity_types
