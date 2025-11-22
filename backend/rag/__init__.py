"""
RAG (Retrieval-Augmented Generation) Module

Provides graph-aware context for intelligent agent operations.

Components:
- SemanticSimilarity: Sentence embedding similarity (baseline)
- GraphContextBuilder: Graph traversal and context
- TripleExtractor: Extract KG triples for embeddings
- KGETrainer: Train knowledge graph embeddings
- KGERetrieval: Path-based retrieval with KGE embeddings
- UnifiedRetrieval: Multi-strategy retrieval system
- HierarchicalAttention: Multi-level attention for tree-structured graphs
"""

from .semantic_similarity import SemanticSimilarity
from .graph_context_builder import GraphContextBuilder
from .config import RAGConfig, RAGThresholds, get_rag_config
from .claim_deduplicator import ClaimDeduplicator, ClaimDeduplicationResult
from .triple_extractor import TripleExtractor
from .kge_trainer import KGETrainer, train_embeddings_from_graph
from .kge_retrieval import KGERetrieval, PathResult, LinkPrediction, get_kge_retrieval
from .unified_retrieval import UnifiedRetrieval, RetrievalMode, RetrievalResult, get_unified_retrieval
from .hierarchical_attention import HierarchicalAttention, TreeNode, AttentionScore, AttentionPath

__all__ = [
    'SemanticSimilarity',
    'GraphContextBuilder',
    'RAGConfig',
    'RAGThresholds',
    'get_rag_config',
    'ClaimDeduplicator',
    'ClaimDeduplicationResult',
    'TripleExtractor',
    'KGETrainer',
    'train_embeddings_from_graph',
    'KGERetrieval',
    'PathResult',
    'LinkPrediction',
    'get_kge_retrieval',
    'UnifiedRetrieval',
    'RetrievalMode',
    'RetrievalResult',
    'get_unified_retrieval',
    'HierarchicalAttention',
    'TreeNode',
    'AttentionScore',
    'AttentionPath',
]
