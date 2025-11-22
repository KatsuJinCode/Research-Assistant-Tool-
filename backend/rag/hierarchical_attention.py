"""
Hierarchical Attention Mechanism for Tree-Structured Graph RAG

Implements multi-level attention over claim hierarchies to enable focused
retrieval based on query relevance at different levels of abstraction.

Hierarchy Structure:
    Document
    └── Super-Claim (high-level finding)
        ├── Sub-Claim 1 (supporting detail)
        │   ├── Evidence 1
        │   └── Evidence 2
        └── Sub-Claim 2 (supporting detail)
            └── Evidence 3

Attention Theory:
    At each level, compute attention scores using query-key similarity:

    attention_score = softmax(similarity(query, key))

    For hierarchical attention, cascade scores from parent to child:

    doc_attention = softmax(sim(query, document_embeddings))
    claim_attention = softmax(sim(query, claim_embeddings)) * doc_attention
    evidence_attention = softmax(sim(query, evidence_embeddings)) * claim_attention

This creates a "zoom in" effect where attention flows down the tree,
focusing on the most relevant branches at each level.

Performance Characteristics:
    - Tree Building: O(N) where N = number of nodes in tree
    - Attention Computation: O(N * D) where D = embedding dimension
    - Retrieval: O(N log N) for sorting results
    - Memory: O(N * D) for embedding cache
"""

import logging
import numpy as np
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, field
from collections import defaultdict

from backend.rag.semantic_similarity import SemanticSimilarity
from research_agent.graph_database import GraphDatabase

logger = logging.getLogger(__name__)


@dataclass
class TreeNode:
    """Node in the hierarchical tree structure."""
    node_id: str
    label: str  # Document, SuperClaim, Claim, Evidence
    text: str
    level: int
    embedding: Optional[np.ndarray] = None
    children: List['TreeNode'] = field(default_factory=list)
    parent_id: Optional[str] = None
    metadata: Dict = field(default_factory=dict)


@dataclass
class AttentionScore:
    """Attention score for a node."""
    node_id: str
    score: float
    level: int
    activated: bool  # Whether this branch was activated (score > threshold)
    parent_score: float = 1.0  # Attention from parent level
    local_score: float = 1.0  # Softmax score at current level


@dataclass
class AttentionPath:
    """Path through tree with attention scores at each level."""
    path: List[str]  # node_ids from root to target
    scores_per_level: List[float]
    final_score: float
    activated: bool
    reason: str


class HierarchicalAttention:
    """
    Hierarchical attention mechanism for tree-structured knowledge graphs.

    Computes attention scores at multiple levels of a claim hierarchy,
    enabling focused retrieval based on query relevance.

    Example Usage:
        >>> from research_agent.graph_database import GraphDatabase
        >>> from backend.rag.hierarchical_attention import HierarchicalAttention
        >>>
        >>> db = GraphDatabase()
        >>> # ... populate graph ...
        >>>
        >>> attention = HierarchicalAttention(db, temperature=0.8)
        >>> results = attention.retrieve_with_attention(
        ...     query_text="What are the effects of AI on employment?",
        ...     top_k_docs=3,
        ...     top_k_claims=5
        ... )
        >>>
        >>> for node_id, score, level in results[:5]:
        ...     node = db.get_node(node_id)
        ...     print(f"[L{level}] {node['text'][:50]}... ({score:.3f})")
    """

    # Relationship types that define the hierarchy
    HIERARCHY_RELATIONS = ['CONTAINS', 'PARENT_OF', 'HAS_EVIDENCE', 'MERGED_INTO']

    def __init__(
        self,
        db: GraphDatabase,
        embedding_model: Optional[SemanticSimilarity] = None,
        temperature: float = 1.0,
        activation_threshold: float = 0.1,
        cache_embeddings: bool = True
    ):
        """
        Initialize hierarchical attention.

        Args:
            db: GraphDatabase instance
            embedding_model: Optional SemanticSimilarity instance (uses default if None)
            temperature: Softmax temperature (< 1.0 = sharper, > 1.0 = softer)
            activation_threshold: Minimum attention score to activate a branch
            cache_embeddings: Whether to cache node embeddings for performance
        """
        self.db = db
        self.temperature = temperature
        self.activation_threshold = activation_threshold
        self.cache_embeddings = cache_embeddings

        # Initialize embedding model
        self.embedding_model = embedding_model or SemanticSimilarity()

        # Embedding cache: node_id -> embedding
        self._embedding_cache: Dict[str, np.ndarray] = {}

        # Tree cache: root_id -> TreeNode
        self._tree_cache: Dict[str, TreeNode] = {}

    def get_tree_structure(
        self,
        root_id: str,
        max_depth: int = 5,
        use_cache: bool = True
    ) -> Optional[TreeNode]:
        """
        Build tree structure from graph starting at root node.

        Args:
            root_id: Root node ID (document or super-claim)
            max_depth: Maximum depth to traverse
            use_cache: Use cached tree if available

        Returns:
            TreeNode representing root of tree, or None if node not found
        """
        # Check cache
        if use_cache and root_id in self._tree_cache:
            return self._tree_cache[root_id]

        # Get root node
        root_data = self.db.get_node(root_id)
        if not root_data:
            logger.warning(f"Root node {root_id} not found")
            return None

        # Build tree recursively
        tree = self._build_tree_recursive(root_id, level=0, max_depth=max_depth)

        # Cache tree
        if use_cache:
            self._tree_cache[root_id] = tree

        return tree

    def _build_tree_recursive(
        self,
        node_id: str,
        level: int,
        max_depth: int,
        visited: Optional[Set[str]] = None
    ) -> Optional[TreeNode]:
        """
        Recursively build tree structure.

        Args:
            node_id: Current node ID
            level: Current tree level
            max_depth: Maximum depth to traverse
            visited: Set of visited node IDs (to prevent cycles)

        Returns:
            TreeNode or None
        """
        if visited is None:
            visited = set()

        # Prevent cycles
        if node_id in visited:
            logger.debug(f"Cycle detected at {node_id}, skipping")
            return None

        visited.add(node_id)

        # Get node data
        node_data = self.db.get_node(node_id)
        if not node_data:
            return None

        # Create tree node
        tree_node = TreeNode(
            node_id=node_id,
            label=node_data.get('label', 'Unknown'),
            text=node_data.get('text', ''),
            level=level,
            metadata={k: v for k, v in node_data.items() if k not in ['id', 'label', 'text']}
        )

        # Get embedding (with caching)
        if self.cache_embeddings:
            if node_id not in self._embedding_cache:
                self._embedding_cache[node_id] = self.embedding_model.encode(tree_node.text)
            tree_node.embedding = self._embedding_cache[node_id]
        else:
            tree_node.embedding = self.embedding_model.encode(tree_node.text)

        # Recursively build children (if not at max depth)
        if level < max_depth:
            children = self._get_children(node_id)
            for child_id in children:
                child_node = self._build_tree_recursive(
                    child_id,
                    level=level + 1,
                    max_depth=max_depth,
                    visited=visited.copy()  # Copy to allow siblings
                )
                if child_node:
                    child_node.parent_id = node_id
                    tree_node.children.append(child_node)

        return tree_node

    def _get_children(self, node_id: str) -> List[str]:
        """
        Get child node IDs for a given node.

        Args:
            node_id: Parent node ID

        Returns:
            List of child node IDs
        """
        children = []

        # Get outgoing relationships
        relationships = self.db.get_relationships(node_id, direction='out')

        for target_id, rel_data in relationships:
            rel_type = rel_data.get('type', '')

            # Only follow hierarchy relationships
            if rel_type in self.HIERARCHY_RELATIONS:
                children.append(target_id)

        return children

    def compute_attention_scores(
        self,
        query_embedding: np.ndarray,
        tree_structure: TreeNode,
        parent_attention: float = 1.0
    ) -> Dict[str, AttentionScore]:
        """
        Compute hierarchical attention scores for all nodes in tree.

        Uses cascade multiplication: child_attention = softmax(similarity) * parent_attention

        Args:
            query_embedding: Query embedding vector
            tree_structure: TreeNode representing root of tree
            parent_attention: Attention from parent level (1.0 for root)

        Returns:
            Dict mapping node_id -> AttentionScore
        """
        attention_scores = {}

        # Compute attention recursively
        self._compute_attention_recursive(
            query_embedding,
            tree_structure,
            parent_attention,
            attention_scores
        )

        return attention_scores

    def _compute_attention_recursive(
        self,
        query_embedding: np.ndarray,
        node: TreeNode,
        parent_attention: float,
        attention_scores: Dict[str, AttentionScore]
    ):
        """
        Recursively compute attention scores.

        Args:
            query_embedding: Query embedding
            node: Current tree node
            parent_attention: Attention from parent
            attention_scores: Dict to populate with scores
        """
        # Compute similarity with query
        if node.embedding is not None:
            similarity = self.embedding_model.cosine_similarity(query_embedding, node.embedding)
        else:
            similarity = 0.0

        # If node has siblings, compute softmax over siblings
        # (For root or single child, local_score = similarity)
        local_score = similarity

        # Apply temperature to similarity before softmax
        # This happens at the sibling level (handled by parent)

        # Cascade: multiply parent attention by local score
        final_score = parent_attention * local_score

        # Check activation threshold
        activated = final_score >= self.activation_threshold

        # Store attention score
        attention_scores[node.node_id] = AttentionScore(
            node_id=node.node_id,
            score=final_score,
            level=node.level,
            activated=activated,
            parent_score=parent_attention,
            local_score=local_score
        )

        # Process children with softmax over siblings
        if node.children and activated:  # Only expand if activated
            # Compute similarities for all children
            child_similarities = []
            for child in node.children:
                if child.embedding is not None:
                    sim = self.embedding_model.cosine_similarity(query_embedding, child.embedding)
                    child_similarities.append(sim)
                else:
                    child_similarities.append(0.0)

            # Apply softmax with temperature
            child_attentions = self._softmax_with_temperature(
                np.array(child_similarities),
                self.temperature
            )

            # Recursively compute for each child
            for child, child_attention in zip(node.children, child_attentions):
                # Child's parent attention = current node's final score * child's softmax score
                child_parent_attention = final_score * child_attention

                self._compute_attention_recursive(
                    query_embedding,
                    child,
                    child_parent_attention,
                    attention_scores
                )

    @staticmethod
    def _softmax_with_temperature(scores: np.ndarray, temperature: float = 1.0) -> np.ndarray:
        """
        Compute softmax with temperature scaling.

        Temperature controls attention sharpness:
        - temperature = 1.0: Normal softmax
        - temperature < 1.0: Sharper (more focused)
        - temperature > 1.0: Softer (more distributed)

        Args:
            scores: Array of scores
            temperature: Temperature parameter

        Returns:
            Softmax probabilities
        """
        if len(scores) == 0:
            return np.array([])

        if len(scores) == 1:
            return np.array([1.0])

        # Apply temperature scaling
        scaled_scores = scores / temperature

        # Compute softmax with numerical stability
        exp_scores = np.exp(scaled_scores - np.max(scaled_scores))
        softmax_probs = exp_scores / np.sum(exp_scores)

        return softmax_probs

    def retrieve_with_attention(
        self,
        query_text: str,
        top_k_docs: int = 3,
        top_k_claims: int = 5,
        top_k_evidence: int = 10,
        expand_all_levels: bool = False
    ) -> List[Tuple[str, float, int]]:
        """
        Retrieve nodes using hierarchical attention.

        Pipeline:
        1. Find top-k documents by semantic similarity
        2. Build tree for each document
        3. Compute hierarchical attention
        4. Return top nodes across all levels

        Args:
            query_text: Query text
            top_k_docs: Top documents to consider
            top_k_claims: Top claims per document
            top_k_evidence: Top evidence per claim
            expand_all_levels: If True, expand all branches (ignore activation)

        Returns:
            List of (node_id, attention_score, level) sorted by score
        """
        # Generate query embedding
        query_embedding = self.embedding_model.encode(query_text)

        # Step 1: Find top documents
        documents = self.db.find_nodes('Document')

        if not documents:
            logger.warning("No documents found in database")
            return []

        # Compute document similarities
        doc_candidates = [
            {
                'id': doc['id'],
                'text': doc.get('text', doc.get('title', '')),
            }
            for doc in documents
        ]

        doc_results = self.embedding_model.find_similar(
            query_text=query_text,
            candidates=doc_candidates,
            threshold=0.0,  # No threshold for initial docs
            limit=top_k_docs
        )

        if not doc_results:
            logger.warning("No similar documents found")
            return []

        # Step 2: Build trees and compute attention for each document
        all_attention_scores = []

        for doc_result in doc_results:
            doc_id = doc_result.claim_id

            # Build tree from document
            tree = self.get_tree_structure(doc_id, max_depth=4)

            if not tree:
                continue

            # Temporarily override activation threshold if expand_all_levels
            original_threshold = self.activation_threshold
            if expand_all_levels:
                self.activation_threshold = 0.0

            # Compute attention scores
            attention_scores = self.compute_attention_scores(
                query_embedding,
                tree,
                parent_attention=doc_result.similarity_score  # Use doc similarity as initial attention
            )

            # Restore threshold
            if expand_all_levels:
                self.activation_threshold = original_threshold

            # Add to results
            for node_id, att_score in attention_scores.items():
                all_attention_scores.append((
                    node_id,
                    att_score.score,
                    att_score.level
                ))

        # Step 3: Sort by attention score and return top results
        all_attention_scores.sort(key=lambda x: x[1], reverse=True)

        # Limit results
        max_results = top_k_docs + top_k_claims + top_k_evidence
        return all_attention_scores[:max_results]

    def explain_attention(
        self,
        query_text: str,
        node_id: str,
        max_depth: int = 5
    ) -> Optional[AttentionPath]:
        """
        Explain why a node received its attention score.

        Shows the path from root to node with attention scores at each level.

        Args:
            query_text: Query text
            node_id: Node to explain
            max_depth: Maximum depth to search

        Returns:
            AttentionPath object with explanation, or None if node not found
        """
        # Generate query embedding
        query_embedding = self.embedding_model.encode(query_text)

        # Find root document containing this node
        root_id = self._find_root_document(node_id, max_depth)

        if not root_id:
            logger.warning(f"Could not find root document for {node_id}")
            return None

        # Build tree
        tree = self.get_tree_structure(root_id, max_depth=max_depth)

        if not tree:
            return None

        # Compute attention scores
        attention_scores = self.compute_attention_scores(query_embedding, tree)

        # Find path from root to target node
        path = self._find_path_to_node(tree, node_id)

        if not path:
            logger.warning(f"Node {node_id} not found in tree rooted at {root_id}")
            return None

        # Collect attention scores along path
        scores_per_level = []
        for path_node_id in path:
            if path_node_id in attention_scores:
                scores_per_level.append(attention_scores[path_node_id].score)
            else:
                scores_per_level.append(0.0)

        # Get final score
        final_score = attention_scores[node_id].score if node_id in attention_scores else 0.0
        activated = attention_scores[node_id].activated if node_id in attention_scores else False

        # Generate reason
        if final_score > 0.8:
            reason = "High semantic similarity at all levels"
        elif final_score > 0.5:
            reason = "Moderate semantic similarity, relevant to query"
        elif final_score > 0.2:
            reason = "Low-moderate similarity, partially relevant"
        else:
            reason = "Low similarity or pruned branch"

        return AttentionPath(
            path=path,
            scores_per_level=scores_per_level,
            final_score=final_score,
            activated=activated,
            reason=reason
        )

    def _find_root_document(self, node_id: str, max_depth: int = 5) -> Optional[str]:
        """
        Find root document containing a node by traversing parent relationships.

        Args:
            node_id: Node to find root for
            max_depth: Maximum depth to search

        Returns:
            Document ID or None
        """
        current_id = node_id
        visited = set()

        for _ in range(max_depth):
            if current_id in visited:
                break

            visited.add(current_id)

            # Check if current node is a document
            node = self.db.get_node(current_id)
            if node and node.get('label') == 'Document':
                return current_id

            # Find parent (incoming CONTAINS, PARENT_OF, etc.)
            relationships = self.db.get_relationships(current_id, direction='in')

            parent_id = None
            for source_id, rel_data in relationships:
                if rel_data.get('type') in self.HIERARCHY_RELATIONS:
                    parent_id = source_id
                    break

            if not parent_id:
                break

            current_id = parent_id

        return None

    def _find_path_to_node(
        self,
        tree: TreeNode,
        target_id: str,
        current_path: Optional[List[str]] = None
    ) -> Optional[List[str]]:
        """
        Find path from tree root to target node.

        Args:
            tree: Root of tree
            target_id: Target node ID
            current_path: Current path (for recursion)

        Returns:
            List of node IDs from root to target, or None if not found
        """
        if current_path is None:
            current_path = []

        # Add current node to path
        current_path = current_path + [tree.node_id]

        # Check if we found the target
        if tree.node_id == target_id:
            return current_path

        # Search children
        for child in tree.children:
            path = self._find_path_to_node(child, target_id, current_path)
            if path:
                return path

        return None

    def get_attention_statistics(self, query_text: str, top_k_docs: int = 3) -> Dict:
        """
        Get statistics about attention distribution for a query.

        Args:
            query_text: Query text
            top_k_docs: Number of top documents to analyze

        Returns:
            Dictionary with attention statistics
        """
        # Retrieve with attention
        results = self.retrieve_with_attention(
            query_text,
            top_k_docs=top_k_docs,
            expand_all_levels=True  # Get all nodes for stats
        )

        if not results:
            return {
                'total_nodes': 0,
                'activated_nodes': 0,
                'activation_rate': 0.0,
                'avg_attention': 0.0,
                'max_attention': 0.0,
                'min_attention': 0.0,
            }

        # Compute statistics
        scores = [score for _, score, _ in results]
        activated_count = sum(1 for score in scores if score >= self.activation_threshold)

        return {
            'total_nodes': len(results),
            'activated_nodes': activated_count,
            'activation_rate': activated_count / len(results) if results else 0.0,
            'avg_attention': np.mean(scores),
            'max_attention': np.max(scores),
            'min_attention': np.min(scores),
            'std_attention': np.std(scores),
            'attention_by_level': self._compute_level_statistics(results),
        }

    def _compute_level_statistics(
        self,
        results: List[Tuple[str, float, int]]
    ) -> Dict[int, Dict]:
        """Compute attention statistics per level."""
        level_stats = defaultdict(lambda: {'scores': [], 'count': 0})

        for node_id, score, level in results:
            level_stats[level]['scores'].append(score)
            level_stats[level]['count'] += 1

        # Compute summary per level
        summary = {}
        for level, data in level_stats.items():
            scores = data['scores']
            summary[level] = {
                'count': data['count'],
                'avg_score': np.mean(scores) if scores else 0.0,
                'max_score': np.max(scores) if scores else 0.0,
                'min_score': np.min(scores) if scores else 0.0,
            }

        return summary

    def clear_cache(self):
        """Clear embedding and tree caches."""
        self._embedding_cache.clear()
        self._tree_cache.clear()
        logger.info("Cleared hierarchical attention caches")

    def visualize_attention(
        self,
        query_text: str,
        root_id: str,
        max_depth: int = 3
    ) -> Dict:
        """
        Generate data for attention visualization.

        Returns tree structure with attention scores suitable for d3.js visualization.

        Args:
            query_text: Query text
            root_id: Root node ID
            max_depth: Maximum depth

        Returns:
            Dict with tree structure and attention scores
        """
        # Build tree
        tree = self.get_tree_structure(root_id, max_depth=max_depth)

        if not tree:
            return {}

        # Compute attention
        query_embedding = self.embedding_model.encode(query_text)
        attention_scores = self.compute_attention_scores(query_embedding, tree)

        # Convert to visualization format
        def tree_to_dict(node: TreeNode) -> Dict:
            node_dict = {
                'id': node.node_id,
                'text': node.text[:100],  # Truncate for display
                'level': node.level,
                'label': node.label,
                'attention': attention_scores[node.node_id].score if node.node_id in attention_scores else 0.0,
                'activated': attention_scores[node.node_id].activated if node.node_id in attention_scores else False,
                'children': [tree_to_dict(child) for child in node.children]
            }
            return node_dict

        return {
            'query': query_text,
            'root_id': root_id,
            'tree': tree_to_dict(tree),
            'temperature': self.temperature,
            'activation_threshold': self.activation_threshold,
        }
