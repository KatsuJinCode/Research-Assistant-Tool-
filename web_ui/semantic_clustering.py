"""
Semantic Embedding-Based Claim Clustering

Creates optimal, exhaustive, non-overlapping hierarchical claim structure using:
- Sentence embeddings (semantic similarity)
- Hierarchical clustering (mathematical optimization)
- Quality metrics (silhouette score, Davies-Bouldin index)

This is the PRIMARY method for claim categorization.
LLM-based categorization should only be used as a fallback.
"""

import logging
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Try to import sentence-transformers
try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
    logger.info("✓ Sentence-transformers available - using semantic clustering")
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    logger.warning("✗ Sentence-transformers NOT available - will fall back to LLM-based categorization")

# Try to import sklearn
try:
    from sklearn.cluster import AgglomerativeClustering
    from sklearn.metrics import silhouette_score, davies_bouldin_score
    from sklearn.metrics.pairwise import cosine_distances
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("✗ Scikit-learn NOT available - clustering will not work")


@dataclass
class ClusterResult:
    """Result of semantic clustering"""
    cluster_id: int
    super_claim_text: str
    super_claim_description: str
    sub_claims: List[Dict[str, Any]]
    quality_score: float  # Silhouette score for this cluster
    centroid_embedding: np.ndarray


@dataclass
class ClusteringMetrics:
    """Quality metrics for entire clustering"""
    silhouette_score: float  # -1 to 1 (higher is better, >0.5 is good)
    davies_bouldin_score: float  # Lower is better
    n_clusters: int
    method: str  # 'semantic-embedding' or 'llm-fallback'


class SemanticClaimClusterer:
    """
    Creates hierarchical claim structure using semantic embeddings.

    This is the PRIMARY method - mathematically rigorous and optimal.
    """

    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize semantic clusterer.

        Args:
            model_name: Sentence transformer model name
                       'all-MiniLM-L6-v2' - Fast, lightweight (22M params)
                       'all-mpnet-base-v2' - Higher quality (110M params)
        """
        if not EMBEDDINGS_AVAILABLE:
            raise ImportError(
                "sentence-transformers not installed. Install with: "
                "pip install sentence-transformers"
            )

        if not SKLEARN_AVAILABLE:
            raise ImportError(
                "scikit-learn not installed. Install with: "
                "pip install scikit-learn"
            )

        logger.info(f"Loading sentence transformer model: {model_name}")
        self.model = SentenceTransformer(model_name)
        logger.info(f"✓ Model loaded: {model_name}")

    def cluster_claims(
        self,
        claims: List[Dict[str, Any]],
        min_clusters: int = 3,
        max_clusters: int = 10
    ) -> Tuple[List[ClusterResult], ClusteringMetrics]:
        """
        Cluster claims using semantic embeddings.

        Args:
            claims: List of claim dicts with 'text', 'type', 'confidence'
            min_clusters: Minimum number of categories to create
            max_clusters: Maximum number of categories to create

        Returns:
            (clusters, metrics)
        """
        if len(claims) < min_clusters:
            raise ValueError(f"Need at least {min_clusters} claims, got {len(claims)}")

        logger.info(f"Clustering {len(claims)} claims using semantic embeddings...")

        # 1. Generate embeddings
        claim_texts = [c['text'] for c in claims]
        embeddings = self.model.encode(claim_texts, show_progress_bar=False)
        logger.info(f"✓ Generated embeddings: shape {embeddings.shape}")

        # 2. Find optimal number of clusters
        optimal_k, best_score = self._find_optimal_k(
            embeddings,
            min_k=min_clusters,
            max_k=min(max_clusters, len(claims) - 1)
        )
        logger.info(f"✓ Optimal K={optimal_k} (silhouette score: {best_score:.3f})")

        # 3. Perform clustering with optimal K
        clustering = AgglomerativeClustering(
            n_clusters=optimal_k,
            metric='cosine',
            linkage='average'
        )
        cluster_labels = clustering.fit_predict(embeddings)

        # 4. Calculate quality metrics
        silhouette = silhouette_score(embeddings, cluster_labels, metric='cosine')
        davies_bouldin = davies_bouldin_score(embeddings, cluster_labels)

        metrics = ClusteringMetrics(
            silhouette_score=silhouette,
            davies_bouldin_score=davies_bouldin,
            n_clusters=optimal_k,
            method='semantic-embedding'
        )

        logger.info(f"✓ Clustering quality - Silhouette: {silhouette:.3f}, Davies-Bouldin: {davies_bouldin:.3f}")

        # 5. Create cluster results
        cluster_results = []
        for cluster_id in range(optimal_k):
            cluster_mask = cluster_labels == cluster_id
            cluster_claims = [c for i, c in enumerate(claims) if cluster_mask[i]]
            cluster_embeddings = embeddings[cluster_mask]

            # Find centroid and generate super-claim
            centroid = np.mean(cluster_embeddings, axis=0)

            # Find claim closest to centroid as super-claim representative
            distances = cosine_distances([centroid], cluster_embeddings)[0]
            closest_idx = np.argmin(distances)
            representative_claim = cluster_claims[closest_idx]

            # Generate super-claim text (generalized from representative)
            super_claim_text = self._generalize_claim(
                representative_claim['text'],
                cluster_claims
            )

            # Calculate cluster quality (silhouette for this cluster only)
            cluster_quality = self._calculate_cluster_silhouette(
                embeddings,
                cluster_labels,
                cluster_id
            )

            cluster_result = ClusterResult(
                cluster_id=cluster_id,
                super_claim_text=super_claim_text,
                super_claim_description=f"Cluster {cluster_id+1}/{optimal_k} (quality: {cluster_quality:.2f})",
                sub_claims=cluster_claims,
                quality_score=cluster_quality,
                centroid_embedding=centroid
            )
            cluster_results.append(cluster_result)

        logger.info(f"✓ Created {len(cluster_results)} semantic clusters")
        return cluster_results, metrics

    def _find_optimal_k(
        self,
        embeddings: np.ndarray,
        min_k: int,
        max_k: int
    ) -> Tuple[int, float]:
        """
        Find optimal number of clusters using silhouette score.

        Returns:
            (optimal_k, best_score)
        """
        best_k = min_k
        best_score = -1

        for k in range(min_k, max_k + 1):
            clustering = AgglomerativeClustering(
                n_clusters=k,
                metric='cosine',
                linkage='average'
            )
            labels = clustering.fit_predict(embeddings)
            score = silhouette_score(embeddings, labels, metric='cosine')

            logger.debug(f"K={k}: silhouette={score:.3f}")

            if score > best_score:
                best_score = score
                best_k = k

        return best_k, best_score

    def _calculate_cluster_silhouette(
        self,
        all_embeddings: np.ndarray,
        all_labels: np.ndarray,
        cluster_id: int
    ) -> float:
        """
        Calculate silhouette score for a specific cluster.

        Returns:
            Average silhouette for points in this cluster (0 to 1)
        """
        cluster_mask = all_labels == cluster_id
        cluster_embeddings = all_embeddings[cluster_mask]

        if len(cluster_embeddings) < 2:
            return 0.0

        # Calculate silhouette for each point in cluster
        from sklearn.metrics import silhouette_samples
        samples = silhouette_samples(all_embeddings, all_labels, metric='cosine')
        cluster_samples = samples[cluster_mask]

        return float(np.mean(cluster_samples))

    def _generalize_claim(
        self,
        representative_text: str,
        cluster_claims: List[Dict[str, Any]]
    ) -> str:
        """
        Generate generalized super-claim from representative claim.

        For now, uses first 50 chars of representative claim.
        TODO: Use LLM to generate proper generalization.

        Args:
            representative_text: Text of claim closest to centroid
            cluster_claims: All claims in this cluster

        Returns:
            Generalized super-claim text (10-15 words)
        """
        # Simple heuristic: truncate representative claim
        # TODO: Call LLM to generate proper generalization
        words = representative_text.split()
        if len(words) <= 12:
            return representative_text
        else:
            return ' '.join(words[:12]) + '...'


def check_embedding_availability() -> bool:
    """
    Check if semantic embedding pipeline is available.

    Returns:
        True if both sentence-transformers and sklearn are installed
    """
    return EMBEDDINGS_AVAILABLE and SKLEARN_AVAILABLE


def get_clustering_method_status() -> Dict[str, Any]:
    """
    Get status of clustering methods.

    Returns:
        Dict with availability and recommendations
    """
    return {
        'semantic_embedding_available': EMBEDDINGS_AVAILABLE and SKLEARN_AVAILABLE,
        'sentence_transformers': EMBEDDINGS_AVAILABLE,
        'sklearn': SKLEARN_AVAILABLE,
        'recommended_method': 'semantic-embedding' if (EMBEDDINGS_AVAILABLE and SKLEARN_AVAILABLE) else 'llm-fallback',
        'install_instructions': {
            'sentence_transformers': 'pip install sentence-transformers',
            'sklearn': 'pip install scikit-learn'
        }
    }
