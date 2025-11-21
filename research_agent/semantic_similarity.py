"""
Semantic Similarity Module - Stage 1 Evidence Auto-Linking
===========================================================

Generates semantic embeddings for claims and evidence using sentence transformers.
Calculates cosine similarity to find potentially related claim-evidence pairs.

Based on: EVIDENCE_AUTO_LINKING_STRATEGY.md

Model Selection:
- Primary: all-mpnet-base-v2 (best quality, 768 dimensions)
- Fallback: all-MiniLM-L6-v2 (faster, 384 dimensions)

Similarity Threshold: >0.7 for candidate pairs
"""

import logging
import numpy as np
from typing import List, Dict, Tuple, Optional
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


class SemanticSimilarityEngine:
    """
    Manages embedding generation and similarity calculations for claims and evidence.
    """

    def __init__(self, model_name: str = 'all-mpnet-base-v2'):
        """
        Initialize the semantic similarity engine.

        Args:
            model_name: HuggingFace model name for sentence embeddings
                       Default: all-mpnet-base-v2 (best quality)
                       Alternative: all-MiniLM-L6-v2 (faster)
        """
        self.model_name = model_name
        self.model = None
        self.embedding_dim = None

        logger.info(f"[SemanticSimilarity] Initializing with model: {model_name}")

        try:
            self._load_model()
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            logger.info("Falling back to all-MiniLM-L6-v2")
            self.model_name = 'all-MiniLM-L6-v2'
            self._load_model()

    def _load_model(self):
        """Load the sentence transformer model."""
        self.model = SentenceTransformer(self.model_name)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        logger.info(f"[SemanticSimilarity] Model loaded. Embedding dimension: {self.embedding_dim}")

    def generate_embedding(self, text: str) -> np.ndarray:
        """
        Generate semantic embedding for a single text.

        Args:
            text: Text to embed (claim or evidence text)

        Returns:
            numpy array of embeddings (shape: [embedding_dim])
        """
        if not text or not text.strip():
            logger.warning("[SemanticSimilarity] Empty text provided, returning zero vector")
            return np.zeros(self.embedding_dim)

        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding
        except Exception as e:
            logger.error(f"[SemanticSimilarity] Error generating embedding: {e}")
            return np.zeros(self.embedding_dim)

    def generate_embeddings_batch(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for multiple texts efficiently.

        Args:
            texts: List of texts to embed

        Returns:
            numpy array of embeddings (shape: [num_texts, embedding_dim])
        """
        if not texts:
            return np.array([])

        try:
            embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=True)
            logger.info(f"[SemanticSimilarity] Generated {len(embeddings)} embeddings")
            return embeddings
        except Exception as e:
            logger.error(f"[SemanticSimilarity] Error in batch embedding: {e}")
            return np.array([])

    def calculate_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings.

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Similarity score (0.0 to 1.0)
        """
        try:
            # Reshape to 2D for sklearn
            emb1_2d = embedding1.reshape(1, -1)
            emb2_2d = embedding2.reshape(1, -1)

            similarity = cosine_similarity(emb1_2d, emb2_2d)[0][0]
            return float(similarity)
        except Exception as e:
            logger.error(f"[SemanticSimilarity] Error calculating similarity: {e}")
            return 0.0

    def find_similar_pairs(
        self,
        claim_texts: List[str],
        evidence_texts: List[str],
        threshold: float = 0.7
    ) -> List[Tuple[int, int, float]]:
        """
        Find claim-evidence pairs with similarity above threshold.

        Args:
            claim_texts: List of claim texts
            evidence_texts: List of evidence texts
            threshold: Minimum similarity score (default: 0.7)

        Returns:
            List of (claim_idx, evidence_idx, similarity_score) tuples
        """
        logger.info(f"[SemanticSimilarity] Finding similar pairs: {len(claim_texts)} claims, {len(evidence_texts)} evidence")

        # Generate embeddings
        claim_embeddings = self.generate_embeddings_batch(claim_texts)
        evidence_embeddings = self.generate_embeddings_batch(evidence_texts)

        if len(claim_embeddings) == 0 or len(evidence_embeddings) == 0:
            logger.warning("[SemanticSimilarity] No embeddings generated")
            return []

        # Calculate similarity matrix
        similarity_matrix = cosine_similarity(claim_embeddings, evidence_embeddings)

        # Find pairs above threshold
        pairs = []
        for claim_idx in range(len(claim_texts)):
            for evidence_idx in range(len(evidence_texts)):
                sim_score = similarity_matrix[claim_idx][evidence_idx]

                if sim_score >= threshold:
                    pairs.append((claim_idx, evidence_idx, float(sim_score)))

        # Sort by similarity (highest first)
        pairs.sort(key=lambda x: x[2], reverse=True)

        logger.info(f"[SemanticSimilarity] Found {len(pairs)} candidate pairs above threshold {threshold}")
        return pairs

    def embedding_to_list(self, embedding: np.ndarray) -> List[float]:
        """
        Convert numpy embedding to list for storage in Neo4j.

        Args:
            embedding: Numpy embedding array

        Returns:
            List of floats
        """
        return embedding.tolist()

    def list_to_embedding(self, embedding_list: List[float]) -> np.ndarray:
        """
        Convert list from Neo4j back to numpy array.

        Args:
            embedding_list: List of floats from database

        Returns:
            Numpy array
        """
        return np.array(embedding_list)


class EmbeddingManager:
    """
    Manages embedding storage and retrieval from Neo4j.
    """

    def __init__(self, db, similarity_engine: SemanticSimilarityEngine):
        """
        Initialize embedding manager.

        Args:
            db: GraphDatabase instance
            similarity_engine: SemanticSimilarityEngine instance
        """
        self.db = db
        self.engine = similarity_engine
        logger.info("[EmbeddingManager] Initialized")

    def store_claim_embedding(self, claim_id: str, claim_text: str) -> bool:
        """
        Generate and store embedding for a claim.

        Args:
            claim_id: Claim node ID
            claim_text: Claim text to embed

        Returns:
            True if successful
        """
        try:
            # Generate embedding
            embedding = self.engine.generate_embedding(claim_text)
            embedding_list = self.engine.embedding_to_list(embedding)

            # Store in Neo4j
            query = """
            MATCH (c:Claim {id: $claim_id})
            SET c.embedding = $embedding,
                c.embedding_model = $model_name,
                c.embedding_dim = $embedding_dim
            RETURN c.id as id
            """

            result = self.db.execute_query(query, {
                'claim_id': claim_id,
                'embedding': embedding_list,
                'model_name': self.engine.model_name,
                'embedding_dim': self.engine.embedding_dim
            })

            if result:
                logger.info(f"[EmbeddingManager] Stored embedding for claim {claim_id}")
                return True
            else:
                logger.warning(f"[EmbeddingManager] Failed to store embedding for claim {claim_id}")
                return False

        except Exception as e:
            logger.error(f"[EmbeddingManager] Error storing claim embedding: {e}")
            return False

    def store_evidence_embedding(self, evidence_id: str, evidence_text: str) -> bool:
        """
        Generate and store embedding for evidence.

        Args:
            evidence_id: Evidence node ID
            evidence_text: Evidence text to embed

        Returns:
            True if successful
        """
        try:
            # Generate embedding
            embedding = self.engine.generate_embedding(evidence_text)
            embedding_list = self.engine.embedding_to_list(embedding)

            # Store in Neo4j
            query = """
            MATCH (e:Evidence {id: $evidence_id})
            SET e.embedding = $embedding,
                e.embedding_model = $model_name,
                e.embedding_dim = $embedding_dim
            RETURN e.id as id
            """

            result = self.db.execute_query(query, {
                'evidence_id': evidence_id,
                'embedding': embedding_list,
                'model_name': self.engine.model_name,
                'embedding_dim': self.engine.embedding_dim
            })

            if result:
                logger.info(f"[EmbeddingManager] Stored embedding for evidence {evidence_id}")
                return True
            else:
                logger.warning(f"[EmbeddingManager] Failed to store embedding for evidence {evidence_id}")
                return False

        except Exception as e:
            logger.error(f"[EmbeddingManager] Error storing evidence embedding: {e}")
            return False

    def get_claim_embedding(self, claim_id: str) -> Optional[np.ndarray]:
        """
        Retrieve embedding for a claim.

        Args:
            claim_id: Claim node ID

        Returns:
            Numpy embedding array or None
        """
        try:
            query = """
            MATCH (c:Claim {id: $claim_id})
            RETURN c.embedding as embedding
            """

            result = self.db.execute_query(query, {'claim_id': claim_id})

            if result and len(result) > 0 and result[0]['embedding']:
                embedding_list = result[0]['embedding']
                return self.engine.list_to_embedding(embedding_list)
            else:
                return None

        except Exception as e:
            logger.error(f"[EmbeddingManager] Error retrieving claim embedding: {e}")
            return None

    def find_similar_evidence_for_claim(
        self,
        claim_id: str,
        threshold: float = 0.7,
        limit: int = 10
    ) -> List[Dict]:
        """
        Find evidence nodes similar to a claim.

        Args:
            claim_id: Claim node ID
            threshold: Minimum similarity score
            limit: Maximum number of results

        Returns:
            List of dicts with evidence_id, similarity, text
        """
        try:
            # Get claim embedding
            claim_embedding = self.get_claim_embedding(claim_id)

            if claim_embedding is None:
                logger.warning(f"[EmbeddingManager] No embedding found for claim {claim_id}")
                return []

            # Get all evidence nodes with embeddings
            query = """
            MATCH (e:Evidence)
            WHERE e.embedding IS NOT NULL
            RETURN e.id as id, e.text as text, e.embedding as embedding
            """

            evidence_nodes = self.db.execute_query(query)

            if not evidence_nodes:
                logger.info("[EmbeddingManager] No evidence nodes with embeddings found")
                return []

            # Calculate similarities
            similar_evidence = []

            for evidence in evidence_nodes:
                evidence_embedding = self.engine.list_to_embedding(evidence['embedding'])
                similarity = self.engine.calculate_similarity(claim_embedding, evidence_embedding)

                if similarity >= threshold:
                    similar_evidence.append({
                        'evidence_id': evidence['id'],
                        'similarity': similarity,
                        'text': evidence['text']
                    })

            # Sort by similarity and limit
            similar_evidence.sort(key=lambda x: x['similarity'], reverse=True)
            similar_evidence = similar_evidence[:limit]

            logger.info(f"[EmbeddingManager] Found {len(similar_evidence)} similar evidence for claim {claim_id}")
            return similar_evidence

        except Exception as e:
            logger.error(f"[EmbeddingManager] Error finding similar evidence: {e}")
            return []


# Global instances (initialized on first use, keyed by model name)
_similarity_engines = {}
_embedding_managers = {}


def get_similarity_engine(model_name: str = 'all-mpnet-base-v2') -> SemanticSimilarityEngine:
    """
    Get or create similarity engine instance for the specified model.

    Args:
        model_name: The sentence-transformer model to use.
                   Default: 'all-mpnet-base-v2' (768-dim, high quality)
                   Alternative: 'all-MiniLM-L6-v2' (384-dim, high speed)

    Returns:
        SemanticSimilarityEngine instance for the specified model.
    """
    global _similarity_engines
    if model_name not in _similarity_engines:
        _similarity_engines[model_name] = SemanticSimilarityEngine(model_name=model_name)
    return _similarity_engines[model_name]


def get_embedding_manager(db, model_name: str = 'all-mpnet-base-v2') -> EmbeddingManager:
    """
    Get or create embedding manager instance for the specified model.

    Args:
        db: Neo4j database instance
        model_name: The sentence-transformer model to use.
                   Default: 'all-mpnet-base-v2' (768-dim, high quality)
                   Alternative: 'all-MiniLM-L6-v2' (384-dim, high speed)

    Returns:
        EmbeddingManager instance for the specified model and database.
    """
    global _embedding_managers
    # Use model_name + db connection string as key (simplified to just model_name for now)
    manager_key = f"{model_name}_{id(db)}"
    if manager_key not in _embedding_managers:
        engine = get_similarity_engine(model_name=model_name)
        _embedding_managers[manager_key] = EmbeddingManager(db, engine)
    return _embedding_managers[manager_key]
