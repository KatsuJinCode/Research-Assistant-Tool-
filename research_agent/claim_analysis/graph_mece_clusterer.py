"""
Graph-Based MECE Clustering using Leiden Algorithm

This module implements the recommended graph-based approach from MECE_ARCHITECTURE.md
using the Leiden algorithm for community detection.

Advantages over threshold-based clustering:
- No arbitrary similarity thresholds
- Mathematically optimal partitions (maximizes modularity)
- Natural MECE structure emerges from data
- Scales better to large datasets
"""

import numpy as np
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Check for required libraries
try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    logger.warning("sentence-transformers or sklearn not available")

try:
    import leidenalg
    import igraph as ig
    LEIDEN_AVAILABLE = True
except ImportError:
    LEIDEN_AVAILABLE = False
    logger.warning("leidenalg or python-igraph not available. Install with: pip install leidenalg python-igraph")


@dataclass
class GraphClusterResult:
    """Result from graph-based clustering"""
    cluster_id: int
    claims: List[Dict[str, Any]]
    centroid_embedding: np.ndarray
    modularity_contribution: float  # How much this cluster contributes to overall modularity
    internal_density: float  # Edge density within cluster
    external_connections: int  # Number of edges to other clusters


class GraphMECEClusterer:
    """
    MECE clustering using Leiden algorithm on similarity graph.

    No need to specify number of clusters - algorithm finds optimal partition.
    """

    def __init__(self, model_name: str = 'all-mpnet-base-v2'):
        """
        Initialize graph-based clusterer.

        Args:
            model_name: Sentence transformer model for embeddings
        """
        if not EMBEDDINGS_AVAILABLE:
            raise ImportError(
                "sentence-transformers and sklearn required. "
                "Install with: pip install sentence-transformers scikit-learn"
            )

        if not LEIDEN_AVAILABLE:
            raise ImportError(
                "leidenalg and python-igraph required. "
                "Install with: pip install leidenalg python-igraph"
            )

        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        logger.info("✓ Graph-based MECE clusterer ready")

    def cluster_claims(
        self,
        claims: List[Dict[str, Any]],
        similarity_threshold: float = 0.5,
        min_cluster_size: int = 2
    ) -> Tuple[List[GraphClusterResult], Dict[str, Any]]:
        """
        Cluster claims using graph-based community detection.

        Args:
            claims: List of claim dicts with 'text', 'id', etc.
            similarity_threshold: Minimum similarity to create edge (default: 0.5)
                                 Lower = more edges, larger clusters
                                 Higher = fewer edges, smaller clusters
            min_cluster_size: Minimum claims per cluster (singletons discarded)

        Returns:
            (clusters, metrics)
        """
        if len(claims) < 2:
            raise ValueError("Need at least 2 claims for clustering")

        logger.info(f"Graph-based clustering of {len(claims)} claims...")

        # 1. Generate embeddings
        logger.info("  [1/5] Generating embeddings...")
        claim_texts = [c['text'] for c in claims]
        embeddings = self.model.encode(claim_texts, show_progress_bar=False)
        logger.info(f"  ✓ Embeddings: {embeddings.shape}")

        # 2. Build similarity graph
        logger.info("  [2/5] Building similarity graph...")
        graph, edge_weights = self._build_similarity_graph(
            embeddings, similarity_threshold
        )
        n_edges = len(graph.es)
        logger.info(f"  ✓ Graph: {len(graph.vs)} nodes, {n_edges} edges")

        # 3. Detect communities with Leiden algorithm
        logger.info("  [3/5] Running Leiden algorithm...")
        partition = leidenalg.find_partition(
            graph,
            leidenalg.ModularityVertexPartition,
            weights=edge_weights,
            n_iterations=-1  # Iterate until stable
        )
        modularity = partition.modularity
        logger.info(f"  ✓ Found {len(partition)} communities (modularity: {modularity:.3f})")

        # 4. Build cluster results
        logger.info("  [4/5] Building clusters...")
        clusters = self._build_cluster_results(
            claims, embeddings, partition, graph, min_cluster_size
        )
        logger.info(f"  ✓ {len(clusters)} clusters (after filtering small clusters)")

        # 5. Calculate metrics
        logger.info("  [5/5] Calculating metrics...")
        metrics = self._calculate_metrics(clusters, embeddings, modularity, partition)

        logger.info(f"✓ Graph-based clustering complete!")
        logger.info(f"  Modularity: {modularity:.3f}")
        logger.info(f"  Avg cluster size: {metrics['avg_cluster_size']:.1f}")

        return clusters, metrics

    def _build_similarity_graph(
        self,
        embeddings: np.ndarray,
        threshold: float
    ) -> Tuple[ig.Graph, List[float]]:
        """
        Build weighted similarity graph.

        Args:
            embeddings: Claim embeddings (n_claims, embedding_dim)
            threshold: Minimum similarity for edge

        Returns:
            (igraph.Graph, edge_weights)
        """
        n_claims = len(embeddings)

        # Calculate pairwise similarities
        similarities = cosine_similarity(embeddings)

        # Build edge list (only include edges above threshold)
        edges = []
        weights = []

        for i in range(n_claims):
            for j in range(i + 1, n_claims):
                sim = similarities[i, j]
                if sim >= threshold:
                    edges.append((i, j))
                    weights.append(float(sim))

        # Create igraph
        graph = ig.Graph()
        graph.add_vertices(n_claims)
        graph.add_edges(edges)

        logger.debug(f"  Graph density: {len(edges) / (n_claims * (n_claims - 1) / 2):.3f}")

        return graph, weights

    def _build_cluster_results(
        self,
        claims: List[Dict[str, Any]],
        embeddings: np.ndarray,
        partition: leidenalg.VertexPartition,
        graph: ig.Graph,
        min_size: int
    ) -> List[GraphClusterResult]:
        """Build cluster result objects."""
        clusters = []

        for cluster_id, community in enumerate(partition):
            # Get claims in this cluster
            indices = list(community)

            # Filter small clusters
            if len(indices) < min_size:
                logger.debug(f"  Skipping cluster {cluster_id} (size {len(indices)} < {min_size})")
                continue

            cluster_claims = [claims[i] for i in indices]
            cluster_embeddings = embeddings[indices]

            # Calculate centroid
            centroid = np.mean(cluster_embeddings, axis=0)

            # Calculate internal density (edge density within cluster)
            if len(indices) > 1:
                # Count internal edges
                internal_edges = 0
                for i, idx_i in enumerate(indices):
                    for idx_j in indices[i+1:]:
                        if graph.are_connected(idx_i, idx_j):
                            internal_edges += 1

                max_internal_edges = len(indices) * (len(indices) - 1) / 2
                internal_density = internal_edges / max_internal_edges if max_internal_edges > 0 else 0
            else:
                internal_density = 1.0

            # Count external connections
            external_connections = 0
            for idx in indices:
                neighbors = graph.neighbors(idx)
                external_neighbors = [n for n in neighbors if n not in indices]
                external_connections += len(external_neighbors)

            # Modularity contribution (approximate)
            modularity_contribution = internal_density - (len(indices) / len(claims)) ** 2

            clusters.append(GraphClusterResult(
                cluster_id=cluster_id,
                claims=cluster_claims,
                centroid_embedding=centroid,
                modularity_contribution=modularity_contribution,
                internal_density=internal_density,
                external_connections=external_connections
            ))

        return clusters

    def _calculate_metrics(
        self,
        clusters: List[GraphClusterResult],
        embeddings: np.ndarray,
        modularity: float,
        partition: leidenalg.VertexPartition
    ) -> Dict[str, Any]:
        """Calculate quality metrics."""
        cluster_sizes = [len(c.claims) for c in clusters]

        metrics = {
            'method': 'graph-leiden',
            'n_clusters': len(clusters),
            'modularity': modularity,
            'avg_cluster_size': float(np.mean(cluster_sizes)) if cluster_sizes else 0,
            'cluster_size_std': float(np.std(cluster_sizes)) if cluster_sizes else 0,
            'min_cluster_size': min(cluster_sizes) if cluster_sizes else 0,
            'max_cluster_size': max(cluster_sizes) if cluster_sizes else 0,
            'avg_internal_density': float(np.mean([c.internal_density for c in clusters])),
            'total_external_connections': sum(c.external_connections for c in clusters)
        }

        return metrics


def check_leiden_availability() -> bool:
    """Check if Leiden algorithm is available."""
    return LEIDEN_AVAILABLE and EMBEDDINGS_AVAILABLE


def get_installation_instructions() -> str:
    """Get installation instructions for missing dependencies."""
    instructions = []

    if not EMBEDDINGS_AVAILABLE:
        instructions.append("pip install sentence-transformers scikit-learn")

    if not LEIDEN_AVAILABLE:
        instructions.append("pip install leidenalg python-igraph")

    if instructions:
        return "Install missing dependencies:\n" + "\n".join(instructions)
    else:
        return "All dependencies installed!"
