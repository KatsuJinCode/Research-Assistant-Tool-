"""
Unified Retrieval System for Advanced Graph RAG

Combines multiple retrieval strategies:
1. Semantic Similarity (sentence embeddings) - Current system
2. Knowledge Graph Embeddings (KGE) - Structural embeddings
3. Graph Context (relationship traversal) - Graph structure

Provides backward compatibility and retrieval mode selection.
"""

import logging
import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from backend.rag.semantic_similarity import SemanticSimilarity, SimilarityResult
from backend.rag.graph_context_builder import GraphContextBuilder
from backend.rag.kge_trainer import KGETrainer
from backend.rag.triple_extractor import TripleExtractor
from research_agent.graph_database import GraphDatabase

logger = logging.getLogger(__name__)


class RetrievalMode(Enum):
    """Retrieval strategies available."""
    BASIC = "basic"                    # Sentence embeddings only (current)
    KGE = "kge"                       # KGE embeddings only
    HYBRID = "hybrid"                 # Combine semantic + KGE
    GRAPH_CONTEXT = "graph_context"   # Graph traversal + semantic
    ADVANCED = "advanced"             # All strategies combined


@dataclass
class RetrievalResult:
    """Unified retrieval result."""
    claim_id: str
    claim_text: str
    score: float
    mode: str
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class UnifiedRetrieval:
    """
    Unified retrieval system combining multiple RAG strategies.

    Provides backward compatibility with existing SemanticSimilarity
    while enabling advanced KGE-based retrieval.
    """

    def __init__(
        self,
        db: GraphDatabase,
        mode: RetrievalMode = RetrievalMode.BASIC,
        kge_embedding_path: Optional[str] = None
    ):
        """
        Initialize unified retrieval system.

        Args:
            db: GraphDatabase instance
            mode: Retrieval mode (basic, kge, hybrid, advanced)
            kge_embedding_path: Path to KGE embeddings (optional)
        """
        self.db = db
        self.mode = mode

        # Initialize components based on mode
        self.semantic_similarity = SemanticSimilarity()
        self.graph_context = GraphContextBuilder()

        # KGE components (loaded on-demand)
        self.kge_trainer = None
        self.kge_embeddings = None
        self.kge_embedding_path = kge_embedding_path

        if mode in [RetrievalMode.KGE, RetrievalMode.HYBRID, RetrievalMode.ADVANCED]:
            self._load_kge_embeddings()

    def _load_kge_embeddings(self):
        """Load KGE embeddings if available."""
        if self.kge_embedding_path:
            try:
                self.kge_trainer = KGETrainer()
                self.kge_embeddings = self.kge_trainer.load_embeddings(self.kge_embedding_path)
                logger.info(f"Loaded KGE embeddings from {self.kge_embedding_path}")
            except Exception as e:
                logger.warning(f"Failed to load KGE embeddings: {e}. Falling back to basic mode.")
                self.mode = RetrievalMode.BASIC

    def retrieve(
        self,
        query_text: str,
        limit: int = 5,
        threshold: float = 0.70,
        custom_mode: Optional[RetrievalMode] = None
    ) -> List[RetrievalResult]:
        """
        Retrieve relevant claims using the configured strategy.

        Args:
            query_text: Query text
            limit: Maximum results
            threshold: Minimum similarity threshold
            custom_mode: Override default mode for this query

        Returns:
            List of RetrievalResult objects
        """
        mode = custom_mode or self.mode

        if mode == RetrievalMode.BASIC:
            return self._retrieve_basic(query_text, limit, threshold)
        elif mode == RetrievalMode.KGE:
            return self._retrieve_kge(query_text, limit, threshold)
        elif mode == RetrievalMode.HYBRID:
            return self._retrieve_hybrid(query_text, limit, threshold)
        elif mode == RetrievalMode.GRAPH_CONTEXT:
            return self._retrieve_graph_context(query_text, limit, threshold)
        elif mode == RetrievalMode.ADVANCED:
            return self._retrieve_advanced(query_text, limit, threshold)
        else:
            logger.warning(f"Unknown mode {mode}, falling back to basic")
            return self._retrieve_basic(query_text, limit, threshold)

    def _retrieve_basic(
        self,
        query_text: str,
        limit: int,
        threshold: float
    ) -> List[RetrievalResult]:
        """
        Basic retrieval using sentence embeddings (backward compatible).

        This is the current system behavior.
        """
        # Get all claims from database
        claims = self.db.find_nodes('Claim')

        # Convert to format expected by SemanticSimilarity
        candidates = [
            {
                'id': claim['id'],
                'text': claim.get('text', ''),
                'confidence': claim.get('confidence', 0.5)
            }
            for claim in claims
        ]

        # Use existing semantic similarity
        similar = self.semantic_similarity.find_similar(
            query_text=query_text,
            candidates=candidates,
            threshold=threshold,
            limit=limit
        )

        # Convert to unified format
        results = [
            RetrievalResult(
                claim_id=s.claim_id,
                claim_text=s.claim_text,
                score=s.similarity_score,
                mode="basic",
                metadata={'confidence': s.confidence}
            )
            for s in similar
        ]

        return results

    def _retrieve_kge(
        self,
        query_text: str,
        limit: int,
        threshold: float
    ) -> List[RetrievalResult]:
        """
        Retrieval using KGE embeddings.

        Uses structural knowledge from graph relationships.
        """
        if not self.kge_trainer or not self.kge_embeddings:
            logger.warning("KGE embeddings not loaded, falling back to basic")
            return self._retrieve_basic(query_text, limit, threshold)

        # Create a temporary claim node to get its embedding
        # (In practice, we'd encode the query using the same method as training)
        # For now, we'll use semantic similarity to find a proxy claim

        # Get all claims
        claims = self.db.find_nodes('Claim')

        # Find the most semantically similar claim to use as query anchor
        candidates = [
            {'id': c['id'], 'text': c.get('text', ''), 'confidence': c.get('confidence', 0.5)}
            for c in claims
        ]

        anchor_results = self.semantic_similarity.find_similar(
            query_text=query_text,
            candidates=candidates,
            threshold=0.5,  # Lower threshold for anchor
            limit=1
        )

        if not anchor_results:
            logger.warning("No anchor claim found for KGE retrieval")
            return []

        anchor_id = anchor_results[0].claim_id

        # Get KGE embedding for anchor
        try:
            anchor_emb = self.kge_trainer.get_entity_embedding(anchor_id)
        except Exception as e:
            logger.error(f"Failed to get KGE embedding for {anchor_id}: {e}")
            return []

        # Compute similarity to all other claims in KGE space
        results = []
        for claim in claims:
            claim_id = claim['id']
            if claim_id == anchor_id:
                continue

            try:
                claim_emb = self.kge_trainer.get_entity_embedding(claim_id)
                kge_similarity = self.kge_trainer.compute_similarity(anchor_id, claim_id)

                if kge_similarity >= threshold:
                    results.append(RetrievalResult(
                        claim_id=claim_id,
                        claim_text=claim.get('text', ''),
                        score=kge_similarity,
                        mode="kge",
                        metadata={
                            'anchor_id': anchor_id,
                            'kge_score': kge_similarity
                        }
                    ))
            except Exception as e:
                logger.debug(f"Skipping claim {claim_id}: {e}")
                continue

        # Sort by KGE similarity
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:limit]

    def _retrieve_hybrid(
        self,
        query_text: str,
        limit: int,
        threshold: float
    ) -> List[RetrievalResult]:
        """
        Hybrid retrieval combining semantic and KGE.

        Uses weighted combination of both approaches.
        """
        # Get results from both approaches
        semantic_results = self._retrieve_basic(query_text, limit * 2, threshold * 0.8)
        kge_results = self._retrieve_kge(query_text, limit * 2, threshold * 0.8)

        # Combine results with weighted scoring
        # Weights: 60% semantic, 40% KGE (tunable)
        semantic_weight = 0.6
        kge_weight = 0.4

        # Create score map
        combined_scores = {}
        claim_texts = {}

        # Add semantic scores
        for result in semantic_results:
            combined_scores[result.claim_id] = {
                'semantic': result.score,
                'kge': 0.0
            }
            claim_texts[result.claim_id] = result.claim_text

        # Add KGE scores
        for result in kge_results:
            if result.claim_id not in combined_scores:
                combined_scores[result.claim_id] = {
                    'semantic': 0.0,
                    'kge': result.score
                }
            else:
                combined_scores[result.claim_id]['kge'] = result.score

            if result.claim_id not in claim_texts:
                claim_texts[result.claim_id] = result.claim_text

        # Compute weighted scores
        hybrid_results = []
        for claim_id, scores in combined_scores.items():
            combined_score = (
                semantic_weight * scores['semantic'] +
                kge_weight * scores['kge']
            )

            hybrid_results.append(RetrievalResult(
                claim_id=claim_id,
                claim_text=claim_texts[claim_id],
                score=combined_score,
                mode="hybrid",
                metadata={
                    'semantic_score': scores['semantic'],
                    'kge_score': scores['kge'],
                    'weights': f"{semantic_weight}/{kge_weight}"
                }
            ))

        # Sort and filter by combined threshold
        hybrid_results.sort(key=lambda x: x.score, reverse=True)
        filtered = [r for r in hybrid_results if r.score >= threshold]

        return filtered[:limit]

    def _retrieve_graph_context(
        self,
        query_text: str,
        limit: int,
        threshold: float
    ) -> List[RetrievalResult]:
        """
        Retrieval using graph structure and context.

        Expands initial semantic results using graph relationships.
        """
        # Start with semantic search
        initial_results = self._retrieve_basic(query_text, limit=3, threshold=threshold)

        if not initial_results:
            return []

        # Expand using graph relationships
        expanded_claims = set()
        for result in initial_results:
            expanded_claims.add(result.claim_id)

            # Get related claims via graph edges
            relationships = self.db.get_relationships(result.claim_id, direction='both')

            for related_id, rel_data in relationships:
                rel_type = rel_data.get('type', '')

                # Only expand via semantic relationships
                if rel_type in ['SUPPORTS', 'CONTRADICTS', 'SIMILAR_TO', 'PARENT_OF']:
                    expanded_claims.add(related_id)

        # Get details for all expanded claims
        expanded_results = []
        for claim_id in expanded_claims:
            claim = self.db.get_node(claim_id)
            if claim:
                # Calculate distance-based score
                # Original results get full score, expanded get 0.8x
                is_original = any(r.claim_id == claim_id for r in initial_results)
                base_score = 1.0 if is_original else 0.8

                # If original, use its similarity score
                if is_original:
                    base_score = next(r.score for r in initial_results if r.claim_id == claim_id)

                expanded_results.append(RetrievalResult(
                    claim_id=claim_id,
                    claim_text=claim.get('text', ''),
                    score=base_score,
                    mode="graph_context",
                    metadata={
                        'is_original': is_original,
                        'expansion_hop': 0 if is_original else 1
                    }
                ))

        # Sort and limit
        expanded_results.sort(key=lambda x: x.score, reverse=True)
        return expanded_results[:limit]

    def _retrieve_advanced(
        self,
        query_text: str,
        limit: int,
        threshold: float
    ) -> List[RetrievalResult]:
        """
        Advanced retrieval combining all strategies.

        Pipeline:
        1. Semantic search (initial candidates)
        2. KGE re-ranking (structural relevance)
        3. Graph expansion (relationship context)
        4. Final scoring (weighted combination)
        """
        # Step 1: Get semantic candidates (cast wider net)
        semantic_results = self._retrieve_basic(
            query_text,
            limit=limit * 3,
            threshold=threshold * 0.7
        )

        if not semantic_results:
            return []

        # Step 2: Re-rank with KGE if available
        if self.kge_trainer and self.kge_embeddings:
            # Get KGE scores for semantic candidates
            for result in semantic_results:
                try:
                    # Find anchor (use query proxy)
                    kge_score = self.kge_trainer.compute_similarity(
                        semantic_results[0].claim_id,  # Use top semantic result as anchor
                        result.claim_id
                    )
                    result.metadata['kge_score'] = kge_score
                except Exception as e:
                    result.metadata['kge_score'] = 0.0

        # Step 3: Graph expansion
        expanded = set(r.claim_id for r in semantic_results)
        for result in semantic_results[:3]:  # Only expand top-3
            relationships = self.db.get_relationships(result.claim_id, direction='both')
            for related_id, rel_data in relationships:
                if rel_data.get('type') in ['SUPPORTS', 'CONTRADICTS']:
                    expanded.add(related_id)

        # Get details for expanded claims
        all_results = list(semantic_results)
        for claim_id in expanded:
            if claim_id not in [r.claim_id for r in semantic_results]:
                claim = self.db.get_node(claim_id)
                if claim:
                    all_results.append(RetrievalResult(
                        claim_id=claim_id,
                        claim_text=claim.get('text', ''),
                        score=threshold * 0.9,  # Expanded claims get lower score
                        mode="advanced",
                        metadata={'expanded': True}
                    ))

        # Step 4: Final scoring (weighted combination)
        for result in all_results:
            semantic_score = result.score
            kge_score = result.metadata.get('kge_score', 0.0)
            is_expanded = result.metadata.get('expanded', False)

            # Weights: 50% semantic, 30% KGE, 20% graph position
            final_score = (
                0.5 * semantic_score +
                0.3 * kge_score +
                0.2 * (0.8 if is_expanded else 1.0)
            )

            result.score = final_score
            result.metadata['final_score'] = final_score
            result.metadata['semantic_score'] = semantic_score

        # Sort and filter
        all_results.sort(key=lambda x: x.score, reverse=True)
        filtered = [r for r in all_results if r.score >= threshold]

        return filtered[:limit]

    def train_embeddings(
        self,
        output_path: str,
        embedding_dim: int = 256,
        epochs: int = 100,
        model_type: str = 'TransE'
    ) -> Dict[str, np.ndarray]:
        """
        Train KGE embeddings on the current graph.

        Args:
            output_path: Path to save embeddings
            embedding_dim: Embedding dimension
            epochs: Training epochs
            model_type: 'TransE', 'RotatE', or 'DistMult'

        Returns:
            Dictionary with embeddings
        """
        # Extract triples
        extractor = TripleExtractor(self.db)
        triples = extractor.extract_from_neo4j()

        logger.info(f"Extracted {len(triples)} triples for KGE training")

        # Train embeddings
        trainer = KGETrainer(embedding_dim=embedding_dim, model_type=model_type)
        embeddings = trainer.train_transe(triples, epochs=epochs)

        # Save embeddings
        trainer.save_embeddings(embeddings, output_path)
        logger.info(f"Saved KGE embeddings to {output_path}")

        # Update instance
        self.kge_trainer = trainer
        self.kge_embeddings = embeddings
        self.kge_embedding_path = output_path

        return embeddings

    def get_retrieval_statistics(self) -> Dict[str, any]:
        """Get statistics about the retrieval system."""
        stats = {
            'mode': self.mode.value,
            'kge_loaded': self.kge_embeddings is not None,
            'semantic_model': self.semantic_similarity.model_name,
        }

        if self.kge_embeddings:
            stats['kge_entities'] = len(self.kge_embeddings.get('entity_embeddings', []))
            stats['kge_relations'] = len(self.kge_embeddings.get('relation_embeddings', []))

        # Graph stats
        db_stats = self.db.stats()
        stats['graph_nodes'] = db_stats['total_nodes']
        stats['graph_edges'] = db_stats['total_relationships']

        return stats


# Singleton instance
_unified_retrieval = None


def get_unified_retrieval(
    db: GraphDatabase,
    mode: RetrievalMode = RetrievalMode.BASIC,
    kge_path: Optional[str] = None
) -> UnifiedRetrieval:
    """
    Get or create unified retrieval instance.

    Args:
        db: GraphDatabase instance
        mode: Retrieval mode
        kge_path: Path to KGE embeddings

    Returns:
        UnifiedRetrieval instance
    """
    global _unified_retrieval
    if _unified_retrieval is None:
        _unified_retrieval = UnifiedRetrieval(db, mode, kge_path)
    return _unified_retrieval
