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

# Import MECE validator
try:
    import sys
    import os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from research_agent.claim_analysis.mece_validator import validate_mece_clustering
    MECE_VALIDATOR_AVAILABLE = True
    logger.info("✓ MECE validator available")
except ImportError as e:
    MECE_VALIDATOR_AVAILABLE = False
    logger.warning(f"✗ MECE validator NOT available: {e}")

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
    ) -> Tuple[List[ClusterResult], ClusteringMetrics, Optional[Dict[str, Any]]]:
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
        logger.info(f"  [1/4] Generating embeddings for {len(claims)} claims...")
        claim_texts = [c['text'] for c in claims]
        embeddings = self.model.encode(claim_texts, show_progress_bar=False)
        logger.info(f"  ✓ Generated embeddings: shape {embeddings.shape}")

        # 2. Find optimal number of clusters
        logger.info(f"  [2/4] Finding optimal number of clusters ({min_clusters}-{min(max_clusters, len(claims) - 1)})...")
        optimal_k, best_score = self._find_optimal_k(
            embeddings,
            min_k=min_clusters,
            max_k=min(max_clusters, len(claims) - 1)
        )
        logger.info(f"  ✓ Optimal K={optimal_k} (silhouette score: {best_score:.3f})")

        # 3. Perform clustering with optimal K
        logger.info(f"  [3/4] Running agglomerative clustering with K={optimal_k}...")
        clustering = AgglomerativeClustering(
            n_clusters=optimal_k,
            metric='cosine',
            linkage='average'
        )
        cluster_labels = clustering.fit_predict(embeddings)

        # 4. Calculate quality metrics
        logger.info(f"  [4/4] Calculating cluster quality metrics...")
        silhouette = silhouette_score(embeddings, cluster_labels, metric='cosine')
        davies_bouldin = davies_bouldin_score(embeddings, cluster_labels)

        metrics = ClusteringMetrics(
            silhouette_score=silhouette,
            davies_bouldin_score=davies_bouldin,
            n_clusters=optimal_k,
            method='semantic-embedding'
        )

        logger.info(f"  ✓ Clustering quality - Silhouette: {silhouette:.3f}, Davies-Bouldin: {davies_bouldin:.3f}")

        # 5. Create cluster results
        logger.info(f"  Generating super-claims for {optimal_k} clusters...")
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

        # MECE Validation (Phase 1 - added 2025-01)
        validation_results = None
        if MECE_VALIDATOR_AVAILABLE:
            try:
                logger.info(f"  [VALIDATION] Checking MECE compliance...")
                validation_results = validate_mece_clustering(
                    cluster_results,
                    claims,
                    embeddings,
                    cluster_labels
                )
                logger.info(f"  ✓ MECE Score: {validation_results['mece_score']:.3f} - {validation_results['grade']}")
            except Exception as e:
                logger.warning(f"  ✗ MECE validation failed: {e}")
                validation_results = None

        return cluster_results, metrics, validation_results

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


class SemanticDuplicateDetector:
    """
    Detects duplicate claims across documents using semantic similarity.

    Uses sentence embeddings to find claims that express the same idea
    even if worded differently.
    """

    def __init__(self, model_name: str = 'all-MiniLM-L6-v2', similarity_threshold: float = 0.85):
        """
        Initialize duplicate detector.

        Args:
            model_name: Sentence transformer model name
            similarity_threshold: Cosine similarity threshold for duplicates (0-1)
                                 0.85 = very similar, 0.70 = somewhat similar
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

        logger.info(f"Loading duplicate detector model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.similarity_threshold = similarity_threshold
        logger.info(f"✓ Duplicate detector ready (threshold: {similarity_threshold})")

    def find_duplicates(
        self,
        new_claims: List[Dict[str, Any]],
        existing_claims: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Find duplicates between new claims and existing claims.

        Args:
            new_claims: List of new claim dicts with 'id', 'text', 'summary'
            existing_claims: List of existing claim dicts with 'id', 'text', 'summary'

        Returns:
            List of duplicate matches:
            [
                {
                    'new_claim_id': str,
                    'existing_claim_id': str,
                    'similarity_score': float,
                    'new_text': str,
                    'existing_text': str,
                    'match_quality': str  # 'exact', 'very_high', 'high'
                }
            ]
        """
        if not new_claims or not existing_claims:
            return []

        logger.info(f"Checking {len(new_claims)} new claims against {len(existing_claims)} existing claims...")

        # Generate embeddings for new claims (use summary if available, else text)
        new_texts = [c.get('summary') or c.get('text', '') for c in new_claims]
        new_embeddings = self.model.encode(new_texts, show_progress_bar=False)

        # Generate embeddings for existing claims
        existing_texts = [c.get('summary') or c.get('text', '') for c in existing_claims]
        existing_embeddings = self.model.encode(existing_texts, show_progress_bar=False)

        # Calculate cosine similarity matrix
        from sklearn.metrics.pairwise import cosine_similarity
        similarity_matrix = cosine_similarity(new_embeddings, existing_embeddings)

        # Find matches above threshold
        duplicates = []
        for i, new_claim in enumerate(new_claims):
            for j, existing_claim in enumerate(existing_claims):
                similarity = similarity_matrix[i, j]

                if similarity >= self.similarity_threshold:
                    # Determine match quality
                    if similarity >= 0.95:
                        match_quality = 'exact'
                    elif similarity >= 0.90:
                        match_quality = 'very_high'
                    else:
                        match_quality = 'high'

                    duplicate = {
                        'new_claim_id': new_claim['id'],
                        'existing_claim_id': existing_claim['id'],
                        'similarity_score': float(similarity),
                        'new_text': new_claim.get('summary') or new_claim.get('text', ''),
                        'existing_text': existing_claim.get('summary') or existing_claim.get('text', ''),
                        'match_quality': match_quality,
                        'existing_doc_id': existing_claim.get('doc_id')
                    }
                    duplicates.append(duplicate)

                    logger.info(f"✓ Found {match_quality} duplicate: {similarity:.3f} similarity")
                    logger.debug(f"  New: {duplicate['new_text'][:60]}...")
                    logger.debug(f"  Existing: {duplicate['existing_text'][:60]}...")

        logger.info(f"✓ Found {len(duplicates)} duplicate claims")
        return duplicates

    def detect_duplicates_in_set(
        self,
        claims: List[Dict[str, Any]]
    ) -> List[Tuple[int, int, float]]:
        """
        Find duplicates within a single set of claims.

        Args:
            claims: List of claim dicts with 'text' or 'summary'

        Returns:
            List of (index_i, index_j, similarity_score) tuples
            where i < j and similarity >= threshold
        """
        if len(claims) < 2:
            return []

        # Generate embeddings
        texts = [c.get('summary') or c.get('text', '') for c in claims]
        embeddings = self.model.encode(texts, show_progress_bar=False)

        # Calculate similarity matrix
        from sklearn.metrics.pairwise import cosine_similarity
        similarity_matrix = cosine_similarity(embeddings)

        # Find pairs above threshold (only upper triangle to avoid duplicates)
        duplicates = []
        for i in range(len(claims)):
            for j in range(i + 1, len(claims)):
                similarity = similarity_matrix[i, j]
                if similarity >= self.similarity_threshold:
                    duplicates.append((i, j, float(similarity)))

        return duplicates
