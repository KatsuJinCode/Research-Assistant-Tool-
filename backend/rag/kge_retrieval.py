"""
Knowledge Graph Embedding (KGE) Retrieval System

Provides path-based retrieval using knowledge graph embeddings.
Enables semantic path queries, multi-hop reasoning, and link prediction.

Key Capabilities:
- Path queries: Find SUPPORTS/CONTRADICTS chains
- Multi-hop reasoning: Discover indirect relationships
- Link prediction: Predict missing relationships
- Relation arithmetic: Combine relation embeddings
"""

import logging
import numpy as np
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass
from collections import defaultdict

from backend.rag.kge_trainer import KGETrainer
from backend.rag.triple_extractor import TripleExtractor
from research_agent.graph_database import GraphDatabase

logger = logging.getLogger(__name__)


@dataclass
class PathResult:
    """Result of a path query."""
    path: List[str]  # List of node IDs in path
    relations: List[str]  # Relations between nodes
    score: float  # Path score
    length: int  # Path length (number of hops)


@dataclass
class LinkPrediction:
    """Predicted link between entities."""
    head: str  # Head entity ID
    relation: str  # Predicted relation type
    tail: str  # Tail entity ID
    score: float  # Prediction confidence


class KGERetrieval:
    """
    KGE-based retrieval system for graph path queries.

    Uses knowledge graph embeddings to:
    - Find reasoning chains (A→B→C)
    - Predict missing links
    - Combine relations via vector arithmetic
    - Score path plausibility
    """

    def __init__(
        self,
        db: GraphDatabase,
        kge_trainer: Optional[KGETrainer] = None,
        embedding_path: Optional[str] = None
    ):
        """
        Initialize KGE retrieval system.

        Args:
            db: GraphDatabase instance
            kge_trainer: Trained KGETrainer instance
            embedding_path: Path to load embeddings from
        """
        self.db = db
        self.kge_trainer = kge_trainer

        # Load embeddings if path provided
        if embedding_path and not kge_trainer:
            self.kge_trainer = KGETrainer()
            self.kge_trainer.load_embeddings(embedding_path)
            logger.info(f"Loaded KGE embeddings from {embedding_path}")

        # Build adjacency lists for fast path queries
        self._adjacency = None
        self._reverse_adjacency = None
        self._relation_map = None
        self._build_adjacency()

    def _build_adjacency(self):
        """Build adjacency lists from graph for fast traversal."""
        self._adjacency = defaultdict(list)  # node_id -> [(target, relation)]
        self._reverse_adjacency = defaultdict(list)  # node_id -> [(source, relation)]
        self._relation_map = defaultdict(set)  # relation -> {(head, tail)}

        # Iterate over all edges
        for u, v, data in self.db.graph.edges(data=True):
            rel_type = data.get('type', 'UNKNOWN')

            # Forward adjacency
            self._adjacency[u].append((v, rel_type))

            # Reverse adjacency
            self._reverse_adjacency[v].append((u, rel_type))

            # Relation map
            self._relation_map[rel_type].add((u, v))

        logger.info(f"Built adjacency lists: {len(self._adjacency)} nodes, {len(self._relation_map)} relation types")

    def find_paths(
        self,
        start_id: str,
        end_id: str,
        max_length: int = 3,
        relation_filter: Optional[List[str]] = None
    ) -> List[PathResult]:
        """
        Find all paths between two nodes.

        Args:
            start_id: Starting node ID
            end_id: Target node ID
            max_length: Maximum path length (number of hops)
            relation_filter: Only use these relation types

        Returns:
            List of PathResult objects sorted by score
        """
        if not self._adjacency:
            self._build_adjacency()

        paths = []
        visited = set()

        def dfs(current, target, path, relations, depth):
            """Depth-first search for paths."""
            if depth > max_length:
                return

            if current == target and depth > 0:
                # Found a path, compute score
                score = self._score_path(path, relations)
                paths.append(PathResult(
                    path=list(path),
                    relations=list(relations),
                    score=score,
                    length=len(path) - 1
                ))
                return

            if current in visited:
                return

            visited.add(current)

            # Explore neighbors
            for neighbor, relation in self._adjacency.get(current, []):
                # Filter by relation if specified
                if relation_filter and relation not in relation_filter:
                    continue

                path.append(neighbor)
                relations.append(relation)
                dfs(neighbor, target, path, relations, depth + 1)
                path.pop()
                relations.pop()

            visited.remove(current)

        # Start DFS
        dfs(start_id, end_id, [start_id], [], 0)

        # Sort by score
        paths.sort(key=lambda p: p.score, reverse=True)
        return paths

    def _score_path(self, path: List[str], relations: List[str]) -> float:
        """
        Score a path using KGE embeddings.

        For TransE: score = -sum(||h + r - t||) for each hop
        Higher score = more plausible path

        Args:
            path: List of node IDs
            relations: List of relations between nodes

        Returns:
            Path score (higher = better)
        """
        if not self.kge_trainer:
            # No KGE available, use uniform score
            return 1.0 / len(relations) if relations else 1.0

        try:
            total_score = 0.0

            for i in range(len(relations)):
                head = path[i]
                relation = relations[i]
                tail = path[i + 1]

                # Get embeddings
                h_emb = self.kge_trainer.get_entity_embedding(head)
                r_emb = self.kge_trainer.get_relation_embedding(relation)
                t_emb = self.kge_trainer.get_entity_embedding(tail)

                # TransE scoring: h + r ≈ t
                # Score = -||h + r - t||
                predicted = h_emb + r_emb
                distance = np.linalg.norm(predicted - t_emb)
                score = -distance  # Lower distance = higher score

                total_score += score

            # Average score over hops
            return total_score / len(relations) if relations else 0.0

        except Exception as e:
            logger.warning(f"Error scoring path: {e}")
            return 0.0

    def find_supporting_chains(
        self,
        claim_id: str,
        max_length: int = 3,
        min_score: float = -10.0,
        limit: int = 10
    ) -> List[PathResult]:
        """
        Find chains of supporting claims (A→B→C where → is SUPPORTS).

        Args:
            claim_id: Starting claim ID
            max_length: Maximum chain length
            min_score: Minimum path score
            limit: Maximum results

        Returns:
            List of support chains
        """
        # Find all paths using SUPPORTS relation
        all_chains = []

        # Get all claims in graph
        claims = self.db.find_nodes('Claim')

        for claim in claims:
            target_id = claim['id']
            if target_id == claim_id:
                continue

            # Find paths
            paths = self.find_paths(
                start_id=claim_id,
                end_id=target_id,
                max_length=max_length,
                relation_filter=['SUPPORTS']
            )

            all_chains.extend(paths)

        # Filter by score and limit
        filtered = [p for p in all_chains if p.score >= min_score]
        filtered.sort(key=lambda p: p.score, reverse=True)

        return filtered[:limit]

    def find_contradicting_chains(
        self,
        claim_id: str,
        max_length: int = 3,
        min_score: float = -10.0,
        limit: int = 10
    ) -> List[PathResult]:
        """
        Find chains of contradicting claims.

        Args:
            claim_id: Starting claim ID
            max_length: Maximum chain length
            min_score: Minimum path score
            limit: Maximum results

        Returns:
            List of contradiction chains
        """
        all_chains = []
        claims = self.db.find_nodes('Claim')

        for claim in claims:
            target_id = claim['id']
            if target_id == claim_id:
                continue

            paths = self.find_paths(
                start_id=claim_id,
                end_id=target_id,
                max_length=max_length,
                relation_filter=['CONTRADICTS']
            )

            all_chains.extend(paths)

        filtered = [p for p in all_chains if p.score >= min_score]
        filtered.sort(key=lambda p: p.score, reverse=True)

        return filtered[:limit]

    def find_multi_hop_reasoning(
        self,
        start_id: str,
        relation_sequence: List[str],
        top_k: int = 5
    ) -> List[Tuple[str, float]]:
        """
        Find entities reachable via a sequence of relations.

        Example: Find evidence for claims that support a given claim
        relation_sequence = ['SUPPORTS', 'HAS_EVIDENCE']

        Args:
            start_id: Starting entity
            relation_sequence: Sequence of relations to follow
            top_k: Top results to return

        Returns:
            List of (entity_id, score) tuples
        """
        # Start with the initial entity
        current_entities = {start_id: 1.0}  # entity_id -> cumulative_score

        for relation in relation_sequence:
            next_entities = {}

            for entity_id, current_score in current_entities.items():
                # Find neighbors via this relation
                for neighbor, rel_type in self._adjacency.get(entity_id, []):
                    if rel_type != relation:
                        continue

                    # Score this hop using KGE
                    hop_score = self._score_single_hop(entity_id, relation, neighbor)

                    # Accumulate score (multiply for path confidence)
                    accumulated_score = current_score * np.exp(hop_score)

                    # Track best score for this neighbor
                    if neighbor not in next_entities or accumulated_score > next_entities[neighbor]:
                        next_entities[neighbor] = accumulated_score

            current_entities = next_entities

            if not current_entities:
                break  # No entities found via this relation

        # Sort by score
        results = sorted(current_entities.items(), key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def _score_single_hop(self, head: str, relation: str, tail: str) -> float:
        """Score a single hop using KGE."""
        if not self.kge_trainer:
            return 0.0

        try:
            h_emb = self.kge_trainer.get_entity_embedding(head)
            r_emb = self.kge_trainer.get_relation_embedding(relation)
            t_emb = self.kge_trainer.get_entity_embedding(tail)

            # TransE: h + r ≈ t
            predicted = h_emb + r_emb
            distance = np.linalg.norm(predicted - t_emb)

            return -distance  # Lower distance = higher score

        except Exception as e:
            logger.debug(f"Error scoring hop: {e}")
            return 0.0

    def predict_missing_links(
        self,
        head: str,
        relation: str,
        top_k: int = 10,
        exclude_existing: bool = True
    ) -> List[LinkPrediction]:
        """
        Predict which entities are likely to be tails for (head, relation, ?).

        Args:
            head: Head entity ID
            relation: Relation type
            top_k: Number of predictions
            exclude_existing: Exclude existing links in graph

        Returns:
            List of LinkPrediction objects
        """
        if not self.kge_trainer:
            logger.warning("KGE trainer not available for link prediction")
            return []

        try:
            # Get embeddings
            h_emb = self.kge_trainer.get_entity_embedding(head)
            r_emb = self.kge_trainer.get_relation_embedding(relation)

            # Predict: t ≈ h + r
            predicted_tail = h_emb + r_emb

            # Get existing links to exclude
            existing_tails = set()
            if exclude_existing:
                for neighbor, rel_type in self._adjacency.get(head, []):
                    if rel_type == relation:
                        existing_tails.add(neighbor)

            # Score all entities
            predictions = []
            all_nodes = list(self.db.graph.nodes())

            for node_id in all_nodes:
                if node_id == head:
                    continue
                if exclude_existing and node_id in existing_tails:
                    continue

                try:
                    tail_emb = self.kge_trainer.get_entity_embedding(node_id)
                    distance = np.linalg.norm(predicted_tail - tail_emb)
                    score = -distance  # Lower distance = higher score

                    predictions.append(LinkPrediction(
                        head=head,
                        relation=relation,
                        tail=node_id,
                        score=score
                    ))

                except Exception as e:
                    logger.debug(f"Skipping node {node_id}: {e}")
                    continue

            # Sort and return top-k
            predictions.sort(key=lambda p: p.score, reverse=True)
            return predictions[:top_k]

        except Exception as e:
            logger.error(f"Error in link prediction: {e}")
            return []

    def find_analogous_relations(
        self,
        source_pair: Tuple[str, str],
        target_head: str,
        top_k: int = 5
    ) -> List[Tuple[str, float]]:
        """
        Find analogous relations using relation arithmetic.

        Example: If (A, SUPPORTS, B), find C where (target, ?, C) has similar relation
        Uses: r ≈ t_emb(B) - h_emb(A)

        Args:
            source_pair: (head, tail) tuple defining the relation
            target_head: Head entity for analogous relation
            top_k: Number of results

        Returns:
            List of (tail_entity, score) tuples
        """
        if not self.kge_trainer:
            return []

        try:
            # Compute relation vector from source pair
            source_head, source_tail = source_pair
            h_emb = self.kge_trainer.get_entity_embedding(source_head)
            t_emb = self.kge_trainer.get_entity_embedding(source_tail)
            relation_vector = t_emb - h_emb

            # Apply to target head
            target_h_emb = self.kge_trainer.get_entity_embedding(target_head)
            predicted_tail = target_h_emb + relation_vector

            # Find closest entities
            results = []
            for node_id in self.db.graph.nodes():
                if node_id == target_head:
                    continue

                try:
                    node_emb = self.kge_trainer.get_entity_embedding(node_id)
                    distance = np.linalg.norm(predicted_tail - node_emb)
                    score = -distance

                    results.append((node_id, score))

                except Exception:
                    continue

            results.sort(key=lambda x: x[1], reverse=True)
            return results[:top_k]

        except Exception as e:
            logger.error(f"Error finding analogous relations: {e}")
            return []

    def get_path_statistics(self) -> Dict:
        """Get statistics about the graph structure."""
        stats = {
            'total_nodes': len(self._adjacency) if self._adjacency else 0,
            'relation_types': len(self._relation_map) if self._relation_map else 0,
        }

        if self._relation_map:
            stats['edges_per_relation'] = {
                rel: len(pairs) for rel, pairs in self._relation_map.items()
            }

        if self._adjacency:
            out_degrees = [len(neighbors) for neighbors in self._adjacency.values()]
            stats['avg_out_degree'] = np.mean(out_degrees) if out_degrees else 0
            stats['max_out_degree'] = max(out_degrees) if out_degrees else 0

        return stats

    def explain_path(self, path: PathResult) -> Dict:
        """
        Generate human-readable explanation of a path.

        Args:
            path: PathResult to explain

        Returns:
            Explanation dict with formatted text
        """
        explanation = {
            'path_length': path.length,
            'overall_score': path.score,
            'hops': []
        }

        for i in range(len(path.relations)):
            head_id = path.path[i]
            tail_id = path.path[i + 1]
            relation = path.relations[i]

            # Get node details
            head_node = self.db.get_node(head_id)
            tail_node = self.db.get_node(tail_id)

            hop_score = self._score_single_hop(head_id, relation, tail_id)

            hop_info = {
                'from': head_node.get('text', head_id)[:50] if head_node else head_id,
                'relation': relation,
                'to': tail_node.get('text', tail_id)[:50] if tail_node else tail_id,
                'score': hop_score
            }

            explanation['hops'].append(hop_info)

        return explanation


# Singleton instance
_kge_retrieval = None


def get_kge_retrieval(
    db: GraphDatabase,
    kge_trainer: Optional[KGETrainer] = None,
    embedding_path: Optional[str] = None
) -> KGERetrieval:
    """
    Get or create KGE retrieval instance.

    Args:
        db: GraphDatabase instance
        kge_trainer: KGETrainer instance
        embedding_path: Path to embeddings

    Returns:
        KGERetrieval instance
    """
    global _kge_retrieval
    if _kge_retrieval is None:
        _kge_retrieval = KGERetrieval(db, kge_trainer, embedding_path)
    return _kge_retrieval
