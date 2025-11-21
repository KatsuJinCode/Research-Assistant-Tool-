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
            # Handle both object and dict structures
            if hasattr(cluster, 'sub_claims'):
                cluster_claims = cluster.sub_claims
            else:
                cluster_claims = cluster.get('sub_claims', [])

            cluster_ids = {c['id'] if isinstance(c, dict) else c.id for c in cluster_claims}
            overlap = all_claim_ids & cluster_ids
            if overlap:
                print(f"WARNING: Found {len(overlap)} overlapping claims!")

            all_claim_ids.update(cluster_ids)
            total_claims += len(cluster_claims)

        overlap_ratio = (total_claims - len(all_claim_ids)) / total_claims if total_claims > 0 else 0

        # Calculate inter-cluster similarity
        centroids = []
        for c in clusters:
            if hasattr(c, 'centroid_embedding'):
                centroids.append(c.centroid_embedding)
            elif 'centroid_embedding' in c:
                centroids.append(c['centroid_embedding'])

        centroids = np.array(centroids)

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
            # Handle both object and dict structures
            if hasattr(cluster, 'sub_claims'):
                cluster_claims = cluster.sub_claims
            else:
                cluster_claims = cluster.get('sub_claims', [])

            clustered_ids.update(
                c['id'] if isinstance(c, dict) else c.id
                for c in cluster_claims
            )

        all_ids = {c['id'] for c in all_claims}
        coverage_ratio = len(clustered_ids) / len(all_ids) if len(all_ids) > 0 else 0

        missing_ids = all_ids - clustered_ids
        missing_claims = [c for c in all_claims if c['id'] in missing_ids]

        # 2. Semantic coverage (embedding space coverage)
        centroids = []
        for c in clusters:
            if hasattr(c, 'centroid_embedding'):
                centroids.append(c.centroid_embedding)
            elif 'centroid_embedding' in c:
                centroids.append(c['centroid_embedding'])

        centroids = np.array(centroids)

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
        cohesions = []
        for c in clusters:
            if hasattr(c, 'quality_score'):
                cohesions.append(c.quality_score)
            elif 'quality_score' in c:
                cohesions.append(c['quality_score'])

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
