"""
RAG (Retrieval-Augmented Generation) Module

Provides graph-aware context for intelligent agent operations.
"""

from .semantic_similarity import SemanticSimilarity
from .graph_context_builder import GraphContextBuilder
from .config import RAGConfig, RAGThresholds, get_rag_config
from .claim_deduplicator import ClaimDeduplicator, ClaimDeduplicationResult

__all__ = [
    'SemanticSimilarity',
    'GraphContextBuilder',
    'RAGConfig',
    'RAGThresholds',
    'get_rag_config',
    'ClaimDeduplicator',
    'ClaimDeduplicationResult',
]
