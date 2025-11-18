"""
Unit tests for semantic embedding-based claim clustering.

Tests the PRIMARY method for hierarchical claim categorization.
"""

import pytest
from web_ui.semantic_clustering import (
    SemanticClaimClusterer,
    check_embedding_availability,
    ClusterResult,
    ClusteringMetrics
)


# Sample test claims - small dataset for fast testing
SAMPLE_CLAIMS = [
    {"text": "Mental illness is not a biological disease", "type": "interpretive", "confidence": 0.9},
    {"text": "Psychiatric diagnosis lacks objective criteria", "type": "methodological", "confidence": 0.8},
    {"text": "The concept of mental illness is a social construct", "type": "interpretive", "confidence": 0.85},

    {"text": "Hysteria patients exhibit conversion symptoms", "type": "factual", "confidence": 0.7},
    {"text": "Psychosomatic symptoms can mimic organic disease", "type": "causal", "confidence": 0.75},
    {"text": "Conversion disorder involves unconscious mechanisms", "type": "interpretive", "confidence": 0.65},

    {"text": "Medical practice operates within social context", "type": "factual", "confidence": 0.9},
    {"text": "Physician-patient relationships involve power dynamics", "type": "interpretive", "confidence": 0.8},
    {"text": "Cultural norms influence disease categorization", "type": "causal", "confidence": 0.85},
]


@pytest.fixture
def clusterer():
    """Create clusterer instance if embeddings are available."""
    if not check_embedding_availability():
        pytest.skip("Semantic embeddings not available - install sentence-transformers and scikit-learn")
    return SemanticClaimClusterer()


def test_embedding_availability():
    """Test that we can detect embedding availability."""
    available = check_embedding_availability()
    assert isinstance(available, bool)


def test_clusterer_initialization(clusterer):
    """Test that clusterer initializes successfully."""
    assert clusterer is not None
    assert clusterer.model is not None


def test_cluster_claims_basic(clusterer):
    """Test basic clustering with sample claims."""
    clusters, metrics = clusterer.cluster_claims(
        SAMPLE_CLAIMS,
        min_clusters=2,
        max_clusters=4
    )

    # Check clusters returned
    assert isinstance(clusters, list)
    assert len(clusters) >= 2
    assert len(clusters) <= 4

    # Check metrics
    assert isinstance(metrics, ClusteringMetrics)
    assert metrics.method == 'semantic-embedding'
    assert metrics.n_clusters == len(clusters)
    assert -1.0 <= metrics.silhouette_score <= 1.0
    assert metrics.davies_bouldin_score >= 0

    # Check each cluster
    for cluster in clusters:
        assert isinstance(cluster, ClusterResult)
        assert cluster.super_claim_text
        assert cluster.super_claim_description
        assert isinstance(cluster.sub_claims, list)
        assert len(cluster.sub_claims) > 0
        assert 0.0 <= cluster.quality_score <= 1.0

        # Check sub-claims have expected fields
        for claim in cluster.sub_claims:
            assert 'text' in claim
            assert 'type' in claim
            assert 'confidence' in claim


def test_optimal_k_finding(clusterer):
    """Test that optimal K is found within range."""
    clusters, metrics = clusterer.cluster_claims(
        SAMPLE_CLAIMS,
        min_clusters=2,
        max_clusters=4
    )

    # Optimal K should be in specified range
    assert 2 <= metrics.n_clusters <= 4


def test_quality_metrics(clusterer):
    """Test that quality metrics are reasonable."""
    clusters, metrics = clusterer.cluster_claims(
        SAMPLE_CLAIMS,
        min_clusters=2,
        max_clusters=3
    )

    # Silhouette score should be reasonable (>0 is good, >0.5 is very good)
    # For this small, well-separated dataset, we expect decent scores
    assert metrics.silhouette_score > 0, "Silhouette score should be positive"

    # Davies-Bouldin should be reasonable (lower is better, <1 is good)
    assert metrics.davies_bouldin_score >= 0


def test_all_claims_assigned(clusterer):
    """Test that all claims are assigned to exactly one cluster."""
    clusters, metrics = clusterer.cluster_claims(
        SAMPLE_CLAIMS,
        min_clusters=2,
        max_clusters=3
    )

    # Count total claims across all clusters
    total_claims = sum(len(c.sub_claims) for c in clusters)
    assert total_claims == len(SAMPLE_CLAIMS), "All claims must be assigned to exactly one cluster"


def test_no_overlapping_clusters(clusterer):
    """Test that clusters are non-overlapping (exhaustive partitioning)."""
    clusters, metrics = clusterer.cluster_claims(
        SAMPLE_CLAIMS,
        min_clusters=2,
        max_clusters=3
    )

    # Collect all claim texts from all clusters
    all_claim_texts = []
    for cluster in clusters:
        for claim in cluster.sub_claims:
            all_claim_texts.append(claim['text'])

    # Check no duplicates (non-overlapping)
    assert len(all_claim_texts) == len(set(all_claim_texts)), "Clusters must not overlap"


def test_minimum_clusters_respected(clusterer):
    """Test that minimum cluster count is respected."""
    min_k = 3
    clusters, metrics = clusterer.cluster_claims(
        SAMPLE_CLAIMS,
        min_clusters=min_k,
        max_clusters=5
    )

    assert len(clusters) >= min_k


def test_insufficient_claims_error():
    """Test that error is raised if too few claims for requested clusters."""
    clusterer = SemanticClaimClusterer()

    few_claims = SAMPLE_CLAIMS[:2]  # Only 2 claims

    with pytest.raises(ValueError, match="Need at least"):
        clusterer.cluster_claims(few_claims, min_clusters=3, max_clusters=5)


def test_cluster_centroid_embeddings(clusterer):
    """Test that cluster centroids are computed."""
    clusters, metrics = clusterer.cluster_claims(
        SAMPLE_CLAIMS,
        min_clusters=2,
        max_clusters=3
    )

    for cluster in clusters:
        # Check centroid embedding exists and has correct shape
        assert cluster.centroid_embedding is not None
        assert len(cluster.centroid_embedding.shape) == 1  # 1D vector
        assert cluster.centroid_embedding.shape[0] > 0  # Non-empty


@pytest.mark.slow
def test_large_dataset_performance():
    """Test clustering with larger dataset (performance test)."""
    if not check_embedding_availability():
        pytest.skip("Embeddings not available")

    # Create 50 claims by repeating and varying sample claims
    large_claims = []
    for i in range(5):
        for claim in SAMPLE_CLAIMS:
            varied_claim = claim.copy()
            varied_claim['text'] = f"{claim['text']} (variant {i})"
            large_claims.append(varied_claim)

    clusterer = SemanticClaimClusterer()

    import time
    start = time.time()
    clusters, metrics = clusterer.cluster_claims(
        large_claims,
        min_clusters=3,
        max_clusters=8
    )
    duration = time.time() - start

    # Should complete in reasonable time (< 30 seconds for 50 claims)
    assert duration < 30, f"Clustering took too long: {duration:.2f}s"

    # Should produce valid clusters
    assert len(clusters) >= 3
    assert len(clusters) <= 8


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
