# MECE Implementation Guide for Research Assistant Tool

## Overview

This guide provides actionable steps to implement MECE (Mutually Exclusive, Comprehensively Exhaustive) clustering in the Research Assistant Tool based on comprehensive research findings.

**Status**: Your codebase already has strong foundations in place. This guide focuses on refinements and validation enhancements.

---

## Current State Analysis

### ✓ Already Implemented

1. **Semantic Embeddings** (`web_ui/semantic_clustering.py`)
   - Using sentence-transformers (all-MiniLM-L6-v2)
   - Hierarchical agglomerative clustering
   - Silhouette score optimization for k selection
   - Hard clustering (ensures mutual exclusivity)

2. **Claim Space Optimization** (`research_agent/claim_analysis/claim_space_optimizer.py`)
   - Subsumption detection
   - Redundancy removal
   - Hierarchical structure building
   - Information content analysis

3. **MECE Architecture** (`MECE_ARCHITECTURE.md`)
   - Graph-based community detection design
   - Leiden algorithm integration plan
   - Large context window strategy (500K chars)

### ⚠️ Needs Enhancement

1. **MECE Validation Metrics** - No comprehensive validation
2. **Coverage Metrics** - No exhaustiveness validation
3. **Exclusivity Metrics** - No overlap detection (even for hard clustering validation)
4. **Combined MECE Score** - No single quality metric
5. **Graph-Based Clustering** - Leiden algorithm not implemented yet

---

## Implementation Roadmap

### Phase 1: Add MECE Validation (2-3 hours)

**Goal**: Validate existing clustering meets MECE requirements

**File**: Create `research_agent/claim_analysis/mece_validator.py`

```python
"""
MECE Validation Module

Provides comprehensive validation for MECE compliance:
- Mutual Exclusivity metrics
- Comprehensiveness (coverage) metrics
- Combined MECE score with grading
"""

import numpy as np
from typing import List, Dict, Any, Tuple
from sklearn.metrics import silhouette_score, davies_bouldin_score
from sklearn.metrics.pairwise import cosine_similarity, cosine_distances


class MECEValidator:
    """
    Validates clustering results for MECE compliance.
    """

    def __init__(self):
        pass

    def validate_mece(
        self,
        clusters: List[Dict[str, Any]],
        all_claims: List[Dict[str, Any]],
        embeddings: np.ndarray,
        labels: np.ndarray
    ) -> Dict[str, Any]:
        """
        Comprehensive MECE validation.

        Args:
            clusters: List of cluster dicts from SemanticClaimClusterer
            all_claims: Complete list of claims
            embeddings: Claim embeddings (n_claims, embedding_dim)
            labels: Cluster labels (n_claims,)

        Returns:
            {
                'mutual_exclusivity': {
                    'overlap_ratio': float,
                    'inter_cluster_similarity': float,
                    'partition_coefficient': float
                },
                'comprehensiveness': {
                    'coverage_ratio': float,
                    'semantic_coverage': float,
                    'missing_claims': List[str]
                },
                'cluster_quality': {
                    'silhouette_score': float,
                    'davies_bouldin_index': float,
                    'avg_cohesion': float
                },
                'mece_score': float,
                'grade': str,
                'passed': bool
            }
        """
        # 1. Validate Mutual Exclusivity
        exclusivity = self._validate_mutual_exclusivity(clusters)

        # 2. Validate Comprehensiveness
        comprehensiveness = self._validate_comprehensiveness(
            clusters, all_claims, embeddings
        )

        # 3. Cluster Quality Metrics
        quality = self._validate_cluster_quality(
            embeddings, labels, clusters
        )

        # 4. Calculate Combined MECE Score
        mece_score = self._calculate_mece_score(
            exclusivity, comprehensiveness, quality
        )

        # 5. Assign Grade
        grade = self._assign_grade(mece_score)

        # 6. Overall pass/fail
        passed = mece_score >= 0.6  # Threshold for acceptable MECE

        return {
            'mutual_exclusivity': exclusivity,
            'comprehensiveness': comprehensiveness,
            'cluster_quality': quality,
            'mece_score': mece_score,
            'grade': grade,
            'passed': passed,
            'summary': self._generate_summary(
                mece_score, grade, passed, exclusivity, comprehensiveness, quality
            )
        }

    def _validate_mutual_exclusivity(
        self,
        clusters: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        Validate mutual exclusivity property.

        For hard clustering, overlap should always be 0.
        This validates implementation correctness.
        """
        # Check for overlaps (should be 0 for hard clustering)
        all_claim_ids = set()
        total_claims = 0

        for cluster in clusters:
            cluster_ids = {c['id'] for c in cluster.sub_claims}
            overlap = all_claim_ids & cluster_ids
            if overlap:
                print(f"WARNING: Found {len(overlap)} overlapping claims!")

            all_claim_ids.update(cluster_ids)
            total_claims += len(cluster.sub_claims)

        overlap_ratio = (total_claims - len(all_claim_ids)) / total_claims if total_claims > 0 else 0

        # Calculate inter-cluster similarity
        centroids = np.array([c.centroid_embedding for c in clusters])
        if len(centroids) > 1:
            sim_matrix = cosine_similarity(centroids)
            # Get upper triangle (exclude diagonal)
            n = len(clusters)
            upper_triangle = sim_matrix[np.triu_indices(n, k=1)]
            inter_cluster_sim = float(np.mean(upper_triangle))
        else:
            inter_cluster_sim = 0.0

        # Partition coefficient (should be 1.0 for hard clustering)
        partition_coefficient = 1.0  # Hard clustering by definition

        return {
            'overlap_ratio': overlap_ratio,  # Should be 0.0
            'inter_cluster_similarity': inter_cluster_sim,  # Should be < 0.6
            'partition_coefficient': partition_coefficient  # Should be 1.0
        }

    def _validate_comprehensiveness(
        self,
        clusters: List[Dict[str, Any]],
        all_claims: List[Dict[str, Any]],
        embeddings: np.ndarray
    ) -> Dict[str, Any]:
        """
        Validate comprehensiveness (coverage) property.
        """
        # 1. Coverage ratio (simple count)
        clustered_ids = set()
        for cluster in clusters:
            clustered_ids.update(c['id'] for c in cluster.sub_claims)

        all_ids = {c['id'] for c in all_claims}
        coverage_ratio = len(clustered_ids) / len(all_ids) if len(all_ids) > 0 else 0

        missing_ids = all_ids - clustered_ids
        missing_claims = [c for c in all_claims if c['id'] in missing_ids]

        # 2. Semantic coverage (embedding space coverage)
        centroids = np.array([c.centroid_embedding for c in clusters])
        if len(centroids) > 0:
            # Distance from each claim to nearest centroid
            distances = cosine_distances(embeddings, centroids)
            min_distances = np.min(distances, axis=1)

            # Coverage: % of claims with distance < threshold to a centroid
            threshold = 0.3  # Max acceptable distance
            semantic_coverage = float(np.mean(min_distances < threshold))
        else:
            semantic_coverage = 0.0

        return {
            'coverage_ratio': coverage_ratio,  # Should be ≥ 0.95
            'semantic_coverage': semantic_coverage,  # Should be > 0.8
            'missing_claims': [c['text'][:50] for c in missing_claims[:5]],  # First 5
            'num_missing': len(missing_claims)
        }

    def _validate_cluster_quality(
        self,
        embeddings: np.ndarray,
        labels: np.ndarray,
        clusters: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        Validate overall cluster quality.
        """
        # Silhouette score
        if len(set(labels)) > 1:
            silhouette = float(silhouette_score(embeddings, labels, metric='cosine'))
        else:
            silhouette = 0.0

        # Davies-Bouldin index (lower is better)
        if len(set(labels)) > 1:
            davies_bouldin = float(davies_bouldin_score(embeddings, labels))
        else:
            davies_bouldin = float('inf')

        # Average cluster cohesion
        cohesions = [c.quality_score for c in clusters]
        avg_cohesion = float(np.mean(cohesions)) if cohesions else 0.0

        return {
            'silhouette_score': silhouette,  # Should be > 0.5
            'davies_bouldin_index': davies_bouldin,  # Should be < 1.0
            'avg_cohesion': avg_cohesion  # Should be > 0.5
        }

    def _calculate_mece_score(
        self,
        exclusivity: Dict[str, float],
        comprehensiveness: Dict[str, float],
        quality: Dict[str, float]
    ) -> float:
        """
        Calculate combined MECE score (0-1).

        Weights:
        - 40% Mutual Exclusivity
        - 30% Comprehensiveness
        - 30% Cluster Quality
        """
        # Exclusivity component (higher is better)
        exclusivity_score = (
            0.5 * (1 - exclusivity['overlap_ratio']) +  # No overlaps
            0.3 * (1 - exclusivity['inter_cluster_similarity']) +  # Low inter-cluster sim
            0.2 * exclusivity['partition_coefficient']  # Hard clustering
        )

        # Comprehensiveness component (higher is better)
        comprehensiveness_score = (
            0.6 * comprehensiveness['coverage_ratio'] +  # High coverage
            0.4 * comprehensiveness['semantic_coverage']  # Semantic coverage
        )

        # Quality component (higher is better)
        # Normalize silhouette from [-1,1] to [0,1]
        normalized_silhouette = (quality['silhouette_score'] + 1) / 2

        quality_score = (
            0.5 * normalized_silhouette +  # Good separation
            0.3 * quality['avg_cohesion'] +  # High cohesion
            0.2 * (1 / (1 + quality['davies_bouldin_index']))  # Low DB index
        )

        # Combined MECE score
        mece_score = (
            0.4 * exclusivity_score +
            0.3 * comprehensiveness_score +
            0.3 * quality_score
        )

        return float(mece_score)

    def _assign_grade(self, score: float) -> str:
        """Assign letter grade to MECE score."""
        if score >= 0.8:
            return 'A - Excellent MECE compliance'
        elif score >= 0.7:
            return 'B - Good MECE compliance'
        elif score >= 0.6:
            return 'C - Acceptable MECE compliance'
        elif score >= 0.5:
            return 'D - Poor MECE compliance (needs refinement)'
        else:
            return 'F - Failed MECE compliance (major issues)'

    def _generate_summary(
        self,
        score: float,
        grade: str,
        passed: bool,
        exclusivity: Dict,
        comprehensiveness: Dict,
        quality: Dict
    ) -> str:
        """Generate human-readable summary."""
        status = "PASSED" if passed else "FAILED"

        summary = f"""
MECE Validation Summary
{'='*50}
Overall Score: {score:.3f} / 1.0
Grade: {grade}
Status: {status}

Mutual Exclusivity: {'✓' if exclusivity['overlap_ratio'] == 0 else '✗'}
  - Overlap ratio: {exclusivity['overlap_ratio']:.3f} (target: 0.0)
  - Inter-cluster similarity: {exclusivity['inter_cluster_similarity']:.3f} (target: < 0.6)

Comprehensiveness: {'✓' if comprehensiveness['coverage_ratio'] >= 0.95 else '✗'}
  - Coverage ratio: {comprehensiveness['coverage_ratio']:.3f} (target: ≥ 0.95)
  - Semantic coverage: {comprehensiveness['semantic_coverage']:.3f} (target: > 0.8)
  - Missing claims: {comprehensiveness['num_missing']}

Cluster Quality: {'✓' if quality['silhouette_score'] > 0.5 else '○'}
  - Silhouette score: {quality['silhouette_score']:.3f} (target: > 0.5)
  - Davies-Bouldin index: {quality['davies_bouldin_index']:.3f} (target: < 1.0)
  - Average cohesion: {quality['avg_cohesion']:.3f} (target: > 0.5)

{'='*50}
"""
        return summary


def validate_mece_clustering(
    cluster_results: List[Any],
    all_claims: List[Dict[str, Any]],
    embeddings: np.ndarray,
    labels: np.ndarray
) -> Dict[str, Any]:
    """
    Convenience function for MECE validation.

    Args:
        cluster_results: Output from SemanticClaimClusterer.cluster_claims()
        all_claims: Complete list of claims
        embeddings: Claim embeddings
        labels: Cluster labels

    Returns:
        Validation results dict
    """
    validator = MECEValidator()
    results = validator.validate_mece(cluster_results, all_claims, embeddings, labels)

    # Print summary
    print(results['summary'])

    return results
```

**Integration with Existing Code**:

Update `web_ui/semantic_clustering.py`:

```python
# Add import
from research_agent.claim_analysis.mece_validator import validate_mece_clustering

# In SemanticClaimClusterer.cluster_claims(), after line 192:
logger.info(f"✓ Created {len(cluster_results)} semantic clusters")

# ADD VALIDATION:
logger.info(f"  [VALIDATION] Checking MECE compliance...")
validation_results = validate_mece_clustering(
    cluster_results,
    claims,
    embeddings,
    cluster_labels
)

# Add to return value
return cluster_results, metrics, validation_results  # <-- Add validation_results
```

---

### Phase 2: Enhance Coverage Detection (1 hour)

**Goal**: Ensure no claims are lost during clustering

**File**: Update `research_agent/claim_analysis/claim_space_optimizer.py`

Add method to `ClaimSpaceOptimizer` class:

```python
def validate_coverage(self) -> Dict[str, Any]:
    """
    Validate that optimization doesn't lose claims.

    Returns:
        {
            'total_claims': int,
            'covered_claims': int,
            'missing_claims': List[str],
            'coverage_ratio': float,
            'passed': bool
        }
    """
    all_claim_ids = set(self.claims.keys())
    covered_claim_ids = set()

    # Claims in optimal set
    optimal_set = self.compute_optimal_spanning_set()
    covered_claim_ids.update(optimal_set)

    # Claims subsumed by others (still covered, just redundant)
    for claim_id, node in self.claims.items():
        if node.is_redundant and node.subsumed_by:
            covered_claim_ids.add(claim_id)  # Count as covered

    missing_ids = all_claim_ids - covered_claim_ids
    missing_claims = [self.claims[cid].text[:50] for cid in missing_ids]

    coverage_ratio = len(covered_claim_ids) / len(all_claim_ids)
    passed = coverage_ratio >= 0.95

    return {
        'total_claims': len(all_claim_ids),
        'covered_claims': len(covered_claim_ids),
        'missing_claims': missing_claims,
        'coverage_ratio': coverage_ratio,
        'passed': passed
    }
```

Update the `optimize()` method to include coverage validation:

```python
# In optimize() method, after line 461 (building hierarchy):
print("Step 5: Validating coverage...")
coverage_validation = self.validate_coverage()

if not coverage_validation['passed']:
    print(f"  WARNING: Low coverage ratio: {coverage_validation['coverage_ratio']:.2%}")
    print(f"  Missing {len(coverage_validation['missing_claims'])} claims")

# Add to stats dict:
stats['coverage_validation'] = coverage_validation
```

---

### Phase 3: Implement Leiden Algorithm (3-4 hours)

**Goal**: Replace arbitrary thresholds with graph-based community detection

**File**: Create `research_agent/claim_analysis/graph_mece_clusterer.py`

```python
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
from typing import List, Dict, Any, Optional
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
    ) -> tuple[List[GraphClusterResult], Dict[str, Any]]:
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
    ) -> tuple[ig.Graph, List[float]]:
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
            'avg_cluster_size': float(np.mean(cluster_sizes)),
            'cluster_size_std': float(np.std(cluster_sizes)),
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
```

**Installation**:

```bash
pip install leidenalg python-igraph
```

---

### Phase 4: Add MECE Dashboard (2 hours)

**Goal**: Visual dashboard for MECE quality monitoring

**File**: Create `web_ui/mece_dashboard.py`

```python
"""
MECE Quality Dashboard

Provides visualization and monitoring of MECE clustering quality.
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from typing import Dict, Any, List


def create_mece_dashboard(validation_results: Dict[str, Any]) -> go.Figure:
    """
    Create comprehensive MECE quality dashboard.

    Args:
        validation_results: Output from MECEValidator.validate_mece()

    Returns:
        Plotly figure with 4 subplots
    """
    # Create 2x2 subplot grid
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            'MECE Score Breakdown',
            'Mutual Exclusivity Metrics',
            'Comprehensiveness Metrics',
            'Cluster Quality Metrics'
        ),
        specs=[
            [{'type': 'indicator'}, {'type': 'bar'}],
            [{'type': 'bar'}, {'type': 'bar'}]
        ]
    )

    # 1. Overall MECE Score (gauge)
    mece_score = validation_results['mece_score']
    grade = validation_results['grade'].split(' - ')[0]  # Extract letter grade

    fig.add_trace(
        go.Indicator(
            mode="gauge+number+delta",
            value=mece_score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': f"MECE Score<br><span style='font-size:0.8em'>Grade: {grade}</span>"},
            delta={'reference': 0.7, 'increasing': {'color': 'green'}},
            gauge={
                'axis': {'range': [None, 1]},
                'bar': {'color': get_score_color(mece_score)},
                'steps': [
                    {'range': [0, 0.5], 'color': 'lightgray'},
                    {'range': [0.5, 0.7], 'color': 'lightyellow'},
                    {'range': [0.7, 1], 'color': 'lightgreen'}
                ],
                'threshold': {
                    'line': {'color': 'red', 'width': 4},
                    'thickness': 0.75,
                    'value': 0.6
                }
            }
        ),
        row=1, col=1
    )

    # 2. Mutual Exclusivity Metrics
    exclusivity = validation_results['mutual_exclusivity']
    fig.add_trace(
        go.Bar(
            x=['Overlap Ratio', 'Inter-Cluster Sim', 'Partition Coef'],
            y=[
                exclusivity['overlap_ratio'],
                exclusivity['inter_cluster_similarity'],
                1 - exclusivity['partition_coefficient']  # Invert so lower is better
            ],
            marker_color=['red' if exclusivity['overlap_ratio'] > 0 else 'green',
                         'red' if exclusivity['inter_cluster_similarity'] > 0.6 else 'green',
                         'green'],
            text=[f"{v:.3f}" for v in [
                exclusivity['overlap_ratio'],
                exclusivity['inter_cluster_similarity'],
                1 - exclusivity['partition_coefficient']
            ]],
            textposition='auto'
        ),
        row=1, col=2
    )

    # 3. Comprehensiveness Metrics
    comprehensiveness = validation_results['comprehensiveness']
    fig.add_trace(
        go.Bar(
            x=['Coverage Ratio', 'Semantic Coverage'],
            y=[
                comprehensiveness['coverage_ratio'],
                comprehensiveness['semantic_coverage']
            ],
            marker_color=[
                'green' if comprehensiveness['coverage_ratio'] >= 0.95 else 'orange',
                'green' if comprehensiveness['semantic_coverage'] > 0.8 else 'orange'
            ],
            text=[f"{v:.3f}" for v in [
                comprehensiveness['coverage_ratio'],
                comprehensiveness['semantic_coverage']
            ]],
            textposition='auto'
        ),
        row=2, col=1
    )

    # 4. Cluster Quality Metrics
    quality = validation_results['cluster_quality']
    fig.add_trace(
        go.Bar(
            x=['Silhouette', 'Cohesion', 'DB Index (inv)'],
            y=[
                quality['silhouette_score'],
                quality['avg_cohesion'],
                1 / (1 + quality['davies_bouldin_index'])  # Normalize
            ],
            marker_color=[
                'green' if quality['silhouette_score'] > 0.5 else 'orange',
                'green' if quality['avg_cohesion'] > 0.5 else 'orange',
                'green'
            ],
            text=[
                f"{quality['silhouette_score']:.3f}",
                f"{quality['avg_cohesion']:.3f}",
                f"DB: {quality['davies_bouldin_index']:.3f}"
            ],
            textposition='auto'
        ),
        row=2, col=2
    )

    # Update layout
    fig.update_layout(
        title_text=f"MECE Quality Dashboard - {validation_results['grade']}",
        showlegend=False,
        height=700
    )

    # Add reference lines
    fig.add_hline(y=0.95, line_dash="dash", line_color="green", row=2, col=1, annotation_text="Target: 0.95")
    fig.add_hline(y=0.6, line_dash="dash", line_color="orange", row=1, col=2, annotation_text="Threshold: 0.6")

    return fig


def get_score_color(score: float) -> str:
    """Get color based on MECE score."""
    if score >= 0.8:
        return 'green'
    elif score >= 0.7:
        return 'lightgreen'
    elif score >= 0.6:
        return 'orange'
    elif score >= 0.5:
        return 'darkorange'
    else:
        return 'red'
```

---

## Testing and Validation

### Test Script

Create `tests/test_mece_validation.py`:

```python
"""
Tests for MECE validation functionality.
"""

import pytest
import numpy as np
from research_agent.claim_analysis.mece_validator import MECEValidator


def test_mece_validator_perfect_case():
    """Test with perfect MECE clustering."""
    # Create mock clusters
    clusters = [
        {
            'cluster_id': 0,
            'sub_claims': [{'id': '1', 'text': 'Claim 1'}, {'id': '2', 'text': 'Claim 2'}],
            'centroid_embedding': np.array([1, 0, 0]),
            'quality_score': 0.8
        },
        {
            'cluster_id': 1,
            'sub_claims': [{'id': '3', 'text': 'Claim 3'}, {'id': '4', 'text': 'Claim 4'}],
            'centroid_embedding': np.array([0, 1, 0]),
            'quality_score': 0.9
        }
    ]

    all_claims = [
        {'id': '1', 'text': 'Claim 1'},
        {'id': '2', 'text': 'Claim 2'},
        {'id': '3', 'text': 'Claim 3'},
        {'id': '4', 'text': 'Claim 4'}
    ]

    embeddings = np.array([
        [1, 0, 0],
        [0.9, 0.1, 0],
        [0, 1, 0],
        [0, 0.9, 0.1]
    ])

    labels = np.array([0, 0, 1, 1])

    validator = MECEValidator()
    results = validator.validate_mece(clusters, all_claims, embeddings, labels)

    # Check mutual exclusivity
    assert results['mutual_exclusivity']['overlap_ratio'] == 0.0
    assert results['comprehensiveness']['coverage_ratio'] == 1.0
    assert results['passed'] is True
    assert results['mece_score'] > 0.6


def test_mece_validator_missing_claims():
    """Test with missing claims (low coverage)."""
    clusters = [
        {
            'cluster_id': 0,
            'sub_claims': [{'id': '1', 'text': 'Claim 1'}],
            'centroid_embedding': np.array([1, 0, 0]),
            'quality_score': 0.8
        }
    ]

    all_claims = [
        {'id': '1', 'text': 'Claim 1'},
        {'id': '2', 'text': 'Claim 2'},  # Missing from clusters
        {'id': '3', 'text': 'Claim 3'}   # Missing from clusters
    ]

    embeddings = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
    labels = np.array([0, 0, 0])

    validator = MECEValidator()
    results = validator.validate_mece(clusters, all_claims, embeddings, labels)

    # Should detect low coverage
    assert results['comprehensiveness']['coverage_ratio'] < 0.95
    assert results['comprehensiveness']['num_missing'] == 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
```

Run tests:

```bash
pytest tests/test_mece_validation.py -v
```

---

## Summary of Changes

### New Files Created

1. `research_agent/claim_analysis/mece_validator.py` - MECE validation module
2. `research_agent/claim_analysis/graph_mece_clusterer.py` - Leiden algorithm implementation
3. `web_ui/mece_dashboard.py` - Visual quality dashboard
4. `tests/test_mece_validation.py` - Unit tests

### Modified Files

1. `web_ui/semantic_clustering.py` - Add validation call
2. `research_agent/claim_analysis/claim_space_optimizer.py` - Add coverage validation

### New Dependencies

```bash
pip install leidenalg python-igraph plotly
```

---

## Next Steps

1. **Implement Phase 1** (MECE validation) - Highest priority
2. **Test validation** with existing clustering results
3. **Add dashboard** to web UI
4. **Implement Leiden algorithm** as alternative clustering method
5. **Compare results** between hierarchical and graph-based clustering
6. **Tune parameters** based on validation metrics

---

## Quick Start

```python
# Example: Validate existing clustering

from research_agent.claim_analysis.mece_validator import validate_mece_clustering
from web_ui.semantic_clustering import SemanticClaimClusterer

# Cluster claims
clusterer = SemanticClaimClusterer()
cluster_results, metrics = clusterer.cluster_claims(claims, min_clusters=3, max_clusters=10)

# Validate MECE compliance
validation = validate_mece_clustering(
    cluster_results,
    all_claims,
    embeddings,
    labels
)

# Check results
print(f"MECE Score: {validation['mece_score']:.3f}")
print(f"Grade: {validation['grade']}")
print(f"Passed: {validation['passed']}")

# View detailed metrics
print(validation['summary'])
```

---

*End of Implementation Guide*
