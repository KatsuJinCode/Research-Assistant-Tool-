"""
Semantic Similarity Engine

Calculates semantic similarity between claims using sentence embeddings.
Supports duplicate detection and claim clustering.
"""

import logging
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SimilarityResult:
    """Result of similarity comparison."""
    claim_id: str
    claim_text: str
    similarity_score: float
    confidence: Optional[float] = None


@dataclass
class ClaimCluster:
    """Group of similar claims."""
    claims: List[Dict]
    max_similarity: float
    avg_similarity: float


class SemanticSimilarity:
    """
    Calculate semantic similarity between claims using sentence embeddings.

    Uses sentence-transformers for generating embeddings and cosine
    similarity for comparing them.

    Similarity Thresholds:
    - >= 0.95: Almost identical (auto-merge candidate)
    - 0.85 - 0.94: Very similar (suggest merge to user)
    - 0.70 - 0.84: Related (show as related claims)
    - < 0.70: Different claims
    """

    # Similarity thresholds
    THRESHOLD_IDENTICAL = 0.95
    THRESHOLD_VERY_SIMILAR = 0.85
    THRESHOLD_RELATED = 0.70

    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize semantic similarity engine.

        Args:
            model_name: Sentence transformer model name
        """
        self.model_name = model_name
        self._model = None
        self._load_model()

    def _load_model(self):
        """Load sentence transformer model (lazy loading)."""
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
            logger.info(f"Loaded sentence transformer model: {self.model_name}")
        except ImportError:
            logger.error("sentence-transformers not installed. Install with: pip install sentence-transformers")
            self._model = None
        except Exception as e:
            logger.error(f"Failed to load sentence transformer model: {e}")
            self._model = None

    @property
    def model(self):
        """Get model instance (with lazy loading)."""
        if self._model is None:
            self._load_model()
        return self._model

    def encode(self, text: str) -> np.ndarray:
        """
        Generate embedding for text.

        Args:
            text: Text to encode

        Returns:
            Embedding vector as numpy array
        """
        if self.model is None:
            raise RuntimeError("Sentence transformer model not available")

        # Handle empty text
        if not text or not text.strip():
            # Return zero vector for empty text
            return np.zeros(self.model.get_sentence_embedding_dimension())

        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding
        except Exception as e:
            logger.error(f"Error encoding text: {e}")
            return np.zeros(self.model.get_sentence_embedding_dimension())

    def encode_batch(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for multiple texts (faster than encoding individually).

        Args:
            texts: List of texts to encode

        Returns:
            Matrix of embeddings (num_texts × embedding_dim)
        """
        if self.model is None:
            raise RuntimeError("Sentence transformer model not available")

        if not texts:
            return np.array([])

        try:
            embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=len(texts) > 100)
            return embeddings
        except Exception as e:
            logger.error(f"Error encoding batch: {e}")
            # Return zero vectors
            dim = self.model.get_sentence_embedding_dimension()
            return np.zeros((len(texts), dim))

    @staticmethod
    def cosine_similarity(embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings.

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Similarity score between 0 and 1
        """
        # Handle zero vectors
        if np.all(embedding1 == 0) or np.all(embedding2 == 0):
            return 0.0

        # Calculate cosine similarity
        dot_product = np.dot(embedding1, embedding2)
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        similarity = dot_product / (norm1 * norm2)

        # Clamp to [0, 1] range
        return float(np.clip(similarity, 0.0, 1.0))

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate semantic similarity between two texts.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score between 0 and 1
        """
        # Handle identical texts
        if text1 == text2:
            return 1.0

        # Generate embeddings
        embedding1 = self.encode(text1)
        embedding2 = self.encode(text2)

        # Calculate similarity
        return self.cosine_similarity(embedding1, embedding2)

    def find_similar(
        self,
        query_text: str,
        candidates: List[Dict],
        threshold: float = THRESHOLD_RELATED,
        limit: int = 5
    ) -> List[SimilarityResult]:
        """
        Find similar claims from a list of candidates.

        Args:
            query_text: Text to compare against
            candidates: List of candidate claims (dicts with 'id', 'text', optional 'confidence')
            threshold: Minimum similarity threshold
            limit: Maximum number of results to return

        Returns:
            List of SimilarityResult objects, sorted by similarity (descending)
        """
        if not candidates:
            return []

        # Generate query embedding
        query_embedding = self.encode(query_text)

        # Generate candidate embeddings
        candidate_texts = [c.get('text', '') for c in candidates]
        candidate_embeddings = self.encode_batch(candidate_texts)

        # Calculate similarities
        results = []
        for i, (candidate, embedding) in enumerate(zip(candidates, candidate_embeddings)):
            similarity = self.cosine_similarity(query_embedding, embedding)

            if similarity >= threshold:
                results.append(SimilarityResult(
                    claim_id=candidate.get('id', ''),
                    claim_text=candidate.get('text', ''),
                    similarity_score=similarity,
                    confidence=candidate.get('confidence')
                ))

        # Sort by similarity (descending) and limit
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        return results[:limit]

    def find_duplicates(
        self,
        claims: List[Dict],
        threshold: float = THRESHOLD_VERY_SIMILAR
    ) -> List[Tuple[str, str, float]]:
        """
        Find duplicate claim pairs above similarity threshold.

        Args:
            claims: List of claim dicts with 'id' and 'text'
            threshold: Minimum similarity to consider duplicates

        Returns:
            List of tuples (claim_id1, claim_id2, similarity_score)
        """
        if len(claims) < 2:
            return []

        duplicates = []

        # Generate all embeddings
        texts = [c.get('text', '') for c in claims]
        embeddings = self.encode_batch(texts)

        # Compare all pairs
        for i in range(len(claims)):
            for j in range(i + 1, len(claims)):
                similarity = self.cosine_similarity(embeddings[i], embeddings[j])

                if similarity >= threshold:
                    duplicates.append((
                        claims[i].get('id', ''),
                        claims[j].get('id', ''),
                        similarity
                    ))

        # Sort by similarity (descending)
        duplicates.sort(key=lambda x: x[2], reverse=True)
        return duplicates

    def cluster_similar_claims(
        self,
        claims: List[Dict],
        threshold: float = THRESHOLD_VERY_SIMILAR
    ) -> List[ClaimCluster]:
        """
        Group similar claims into clusters using single-linkage clustering.

        Args:
            claims: List of claim dicts with 'id' and 'text'
            threshold: Minimum similarity for clustering

        Returns:
            List of ClaimCluster objects
        """
        if not claims:
            return []

        # Find all duplicate pairs
        duplicate_pairs = self.find_duplicates(claims, threshold)

        if not duplicate_pairs:
            # No duplicates found - each claim is its own cluster
            return [
                ClaimCluster(
                    claims=[claim],
                    max_similarity=1.0,
                    avg_similarity=1.0
                )
                for claim in claims
            ]

        # Build adjacency list for clustering
        from collections import defaultdict
        adjacency = defaultdict(set)

        for claim1_id, claim2_id, similarity in duplicate_pairs:
            adjacency[claim1_id].add(claim2_id)
            adjacency[claim2_id].add(claim1_id)

        # Find connected components (clusters)
        visited = set()
        clusters = []

        def dfs(claim_id, cluster_ids):
            """Depth-first search to find connected component."""
            if claim_id in visited:
                return
            visited.add(claim_id)
            cluster_ids.add(claim_id)

            for neighbor in adjacency[claim_id]:
                dfs(neighbor, cluster_ids)

        # Build claim ID to claim dict mapping
        claim_map = {c.get('id', ''): c for c in claims}

        # Find all clusters
        for claim in claims:
            claim_id = claim.get('id', '')
            if claim_id not in visited:
                cluster_ids = set()
                dfs(claim_id, cluster_ids)

                if cluster_ids:
                    cluster_claims = [claim_map[cid] for cid in cluster_ids if cid in claim_map]

                    # Calculate cluster statistics
                    if len(cluster_claims) > 1:
                        # Find max and avg similarity within cluster
                        similarities = [
                            sim for id1, id2, sim in duplicate_pairs
                            if id1 in cluster_ids and id2 in cluster_ids
                        ]
                        max_sim = max(similarities) if similarities else 1.0
                        avg_sim = sum(similarities) / len(similarities) if similarities else 1.0
                    else:
                        max_sim = avg_sim = 1.0

                    clusters.append(ClaimCluster(
                        claims=cluster_claims,
                        max_similarity=max_sim,
                        avg_similarity=avg_sim
                    ))

        # Sort clusters by size (largest first)
        clusters.sort(key=lambda c: len(c.claims), reverse=True)
        return clusters

    def get_similarity_category(self, score: float) -> str:
        """
        Get human-readable category for similarity score.

        Args:
            score: Similarity score (0-1)

        Returns:
            Category string
        """
        if score >= self.THRESHOLD_IDENTICAL:
            return "identical"
        elif score >= self.THRESHOLD_VERY_SIMILAR:
            return "very_similar"
        elif score >= self.THRESHOLD_RELATED:
            return "related"
        else:
            return "different"


# Singleton instance
_similarity_engine = None


def get_similarity_engine() -> SemanticSimilarity:
    """Get or create singleton SemanticSimilarity instance."""
    global _similarity_engine
    if _similarity_engine is None:
        _similarity_engine = SemanticSimilarity()
    return _similarity_engine
