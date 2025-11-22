"""
RAG Retrieval Benchmark Suite

Comprehensive benchmarking system for evaluating retrieval quality improvements.

Metrics:
- Precision@k: Precision at top-k results
- Recall@k: Recall at top-k results
- MRR (Mean Reciprocal Rank): Average 1/rank of first relevant result
- NDCG (Normalized Discounted Cumulative Gain): Ranking quality
- Latency: Query response time
- Throughput: Queries per second

Comparisons:
- Baseline (semantic only) vs KGE vs Hybrid vs Advanced
- Different embedding dimensions
- Temperature effects on hierarchical attention
"""

import time
import logging
import numpy as np
from typing import List, Dict, Tuple, Set, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import json

from research_agent.graph_database import GraphDatabase
from backend.rag import (
    SemanticSimilarity,
    TripleExtractor,
    KGETrainer,
    HierarchicalAttention,
    KGERetrieval,
    UnifiedRetrieval,
    RetrievalMode
)

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkQuery:
    """Test query with ground truth relevant claims."""
    query_text: str
    relevant_claim_ids: Set[str]  # Ground truth relevant claims
    category: str = "general"  # Query category for analysis


@dataclass
class RetrievalMetrics:
    """Metrics for a single retrieval result."""
    precision_at_5: float = 0.0
    precision_at_10: float = 0.0
    recall_at_5: float = 0.0
    recall_at_10: float = 0.0
    mrr: float = 0.0  # Mean Reciprocal Rank
    ndcg_at_5: float = 0.0
    ndcg_at_10: float = 0.0
    latency_ms: float = 0.0
    retrieved_count: int = 0


@dataclass
class BenchmarkResults:
    """Aggregated benchmark results."""
    mode: str
    queries: int = 0
    avg_precision_at_5: float = 0.0
    avg_precision_at_10: float = 0.0
    avg_recall_at_5: float = 0.0
    avg_recall_at_10: float = 0.0
    avg_mrr: float = 0.0
    avg_ndcg_at_5: float = 0.0
    avg_ndcg_at_10: float = 0.0
    avg_latency_ms: float = 0.0
    throughput_qps: float = 0.0
    per_query_metrics: List[RetrievalMetrics] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'mode': self.mode,
            'queries': self.queries,
            'precision@5': round(self.avg_precision_at_5, 4),
            'precision@10': round(self.avg_precision_at_10, 4),
            'recall@5': round(self.avg_recall_at_5, 4),
            'recall@10': round(self.avg_recall_at_10, 4),
            'mrr': round(self.avg_mrr, 4),
            'ndcg@5': round(self.avg_ndcg_at_5, 4),
            'ndcg@10': round(self.avg_ndcg_at_10, 4),
            'latency_ms': round(self.avg_latency_ms, 2),
            'throughput_qps': round(self.throughput_qps, 2)
        }


class RAGBenchmark:
    """
    Comprehensive benchmark suite for RAG retrieval systems.

    Tests all retrieval modes and measures performance improvements.
    """

    def __init__(self, db: GraphDatabase):
        """
        Initialize benchmark suite.

        Args:
            db: GraphDatabase instance with test data
        """
        self.db = db
        self.queries: List[BenchmarkQuery] = []
        self.results: Dict[str, BenchmarkResults] = {}

    def add_query(self, query_text: str, relevant_claim_ids: List[str], category: str = "general"):
        """
        Add a benchmark query.

        Args:
            query_text: Query text
            relevant_claim_ids: List of ground truth relevant claim IDs
            category: Query category
        """
        self.queries.append(BenchmarkQuery(
            query_text=query_text,
            relevant_claim_ids=set(relevant_claim_ids),
            category=category
        ))

    def generate_synthetic_queries(self, num_queries: int = 20):
        """
        Generate synthetic queries from existing claims.

        Args:
            num_queries: Number of queries to generate
        """
        claims = self.db.find_nodes('Claim')

        if len(claims) < num_queries:
            logger.warning(f"Only {len(claims)} claims available, generating {len(claims)} queries")
            num_queries = len(claims)

        # Sample claims
        import random
        sampled_claims = random.sample(claims, num_queries)

        for claim in sampled_claims:
            claim_id = claim['id']
            claim_text = claim.get('text', '')

            # Use claim text as query
            # Ground truth: The claim itself + similar claims
            relevant_ids = {claim_id}

            # Find connected claims (via SUPPORTS, CONTRADICTS, etc.)
            relationships = self.db.get_relationships(claim_id, direction='both')
            for related_id, rel_data in relationships:
                rel_type = rel_data.get('type', '')
                if rel_type in ['SUPPORTS', 'CONTRADICTS', 'SIMILAR_TO']:
                    relevant_ids.add(related_id)

            # Determine category based on relationships
            has_support = any(r[1].get('type') == 'SUPPORTS' for r in relationships)
            has_contradiction = any(r[1].get('type') == 'CONTRADICTS' for r in relationships)

            if has_support and has_contradiction:
                category = "controversial"
            elif has_support:
                category = "supported"
            elif has_contradiction:
                category = "contradicted"
            else:
                category = "isolated"

            self.add_query(claim_text, list(relevant_ids), category)

        logger.info(f"Generated {num_queries} synthetic queries")

    def calculate_precision_at_k(
        self,
        retrieved: List[str],
        relevant: Set[str],
        k: int
    ) -> float:
        """
        Calculate Precision@k.

        Args:
            retrieved: List of retrieved claim IDs
            relevant: Set of relevant claim IDs
            k: Top-k to consider

        Returns:
            Precision@k score
        """
        top_k = retrieved[:k]
        relevant_in_top_k = len([r for r in top_k if r in relevant])
        return relevant_in_top_k / k if k > 0 else 0.0

    def calculate_recall_at_k(
        self,
        retrieved: List[str],
        relevant: Set[str],
        k: int
    ) -> float:
        """
        Calculate Recall@k.

        Args:
            retrieved: List of retrieved claim IDs
            relevant: Set of relevant claim IDs
            k: Top-k to consider

        Returns:
            Recall@k score
        """
        if not relevant:
            return 0.0

        top_k = retrieved[:k]
        relevant_in_top_k = len([r for r in top_k if r in relevant])
        return relevant_in_top_k / len(relevant)

    def calculate_mrr(self, retrieved: List[str], relevant: Set[str]) -> float:
        """
        Calculate Mean Reciprocal Rank.

        Args:
            retrieved: List of retrieved claim IDs
            relevant: Set of relevant claim IDs

        Returns:
            MRR score
        """
        for i, claim_id in enumerate(retrieved):
            if claim_id in relevant:
                return 1.0 / (i + 1)
        return 0.0

    def calculate_ndcg_at_k(
        self,
        retrieved: List[str],
        relevant: Set[str],
        k: int
    ) -> float:
        """
        Calculate Normalized Discounted Cumulative Gain@k.

        Args:
            retrieved: List of retrieved claim IDs
            relevant: Set of relevant claim IDs
            k: Top-k to consider

        Returns:
            NDCG@k score
        """
        top_k = retrieved[:k]

        # DCG: sum(rel_i / log2(i+1))
        dcg = 0.0
        for i, claim_id in enumerate(top_k):
            relevance = 1.0 if claim_id in relevant else 0.0
            dcg += relevance / np.log2(i + 2)  # i+2 because i is 0-indexed

        # IDCG: DCG of perfect ranking
        ideal_ranking = [1.0] * min(len(relevant), k) + [0.0] * (k - len(relevant))
        idcg = sum(rel / np.log2(i + 2) for i, rel in enumerate(ideal_ranking))

        return dcg / idcg if idcg > 0 else 0.0

    def benchmark_mode(
        self,
        mode: RetrievalMode,
        kge_path: Optional[str] = None,
        limit: int = 10,
        threshold: float = 0.5
    ) -> BenchmarkResults:
        """
        Benchmark a specific retrieval mode.

        Args:
            mode: RetrievalMode to test
            kge_path: Path to KGE embeddings (if applicable)
            limit: Max results to retrieve
            threshold: Similarity threshold

        Returns:
            BenchmarkResults for this mode
        """
        logger.info(f"Benchmarking mode: {mode.value}")

        # Initialize retrieval system
        retrieval = UnifiedRetrieval(self.db, mode=mode, kge_embedding_path=kge_path)

        results = BenchmarkResults(mode=mode.value)
        total_latency = 0.0

        for query in self.queries:
            start_time = time.time()

            # Retrieve
            retrieved_results = retrieval.retrieve(
                query_text=query.query_text,
                limit=limit,
                threshold=threshold
            )

            latency_ms = (time.time() - start_time) * 1000
            total_latency += latency_ms

            # Extract claim IDs
            retrieved_ids = [r.claim_id for r in retrieved_results]

            # Calculate metrics
            metrics = RetrievalMetrics(
                precision_at_5=self.calculate_precision_at_k(retrieved_ids, query.relevant_claim_ids, 5),
                precision_at_10=self.calculate_precision_at_k(retrieved_ids, query.relevant_claim_ids, 10),
                recall_at_5=self.calculate_recall_at_k(retrieved_ids, query.relevant_claim_ids, 5),
                recall_at_10=self.calculate_recall_at_k(retrieved_ids, query.relevant_claim_ids, 10),
                mrr=self.calculate_mrr(retrieved_ids, query.relevant_claim_ids),
                ndcg_at_5=self.calculate_ndcg_at_k(retrieved_ids, query.relevant_claim_ids, 5),
                ndcg_at_10=self.calculate_ndcg_at_k(retrieved_ids, query.relevant_claim_ids, 10),
                latency_ms=latency_ms,
                retrieved_count=len(retrieved_ids)
            )

            results.per_query_metrics.append(metrics)

        # Aggregate metrics
        results.queries = len(self.queries)
        results.avg_precision_at_5 = np.mean([m.precision_at_5 for m in results.per_query_metrics])
        results.avg_precision_at_10 = np.mean([m.precision_at_10 for m in results.per_query_metrics])
        results.avg_recall_at_5 = np.mean([m.recall_at_5 for m in results.per_query_metrics])
        results.avg_recall_at_10 = np.mean([m.recall_at_10 for m in results.per_query_metrics])
        results.avg_mrr = np.mean([m.mrr for m in results.per_query_metrics])
        results.avg_ndcg_at_5 = np.mean([m.ndcg_at_5 for m in results.per_query_metrics])
        results.avg_ndcg_at_10 = np.mean([m.ndcg_at_10 for m in results.per_query_metrics])
        results.avg_latency_ms = np.mean([m.latency_ms for m in results.per_query_metrics])
        results.throughput_qps = 1000 / results.avg_latency_ms if results.avg_latency_ms > 0 else 0.0

        self.results[mode.value] = results

        logger.info(f"Mode {mode.value}: Precision@5={results.avg_precision_at_5:.3f}, "
                   f"MRR={results.avg_mrr:.3f}, Latency={results.avg_latency_ms:.1f}ms")

        return results

    def run_full_benchmark(
        self,
        kge_path: Optional[str] = None,
        modes: Optional[List[RetrievalMode]] = None
    ) -> Dict[str, BenchmarkResults]:
        """
        Run full benchmark across all modes.

        Args:
            kge_path: Path to KGE embeddings
            modes: List of modes to test (default: all modes)

        Returns:
            Dict mapping mode name to results
        """
        if modes is None:
            modes = [
                RetrievalMode.BASIC,
                RetrievalMode.KGE,
                RetrievalMode.HYBRID,
                RetrievalMode.GRAPH_CONTEXT,
                RetrievalMode.ADVANCED
            ]

        logger.info(f"Running full benchmark with {len(self.queries)} queries across {len(modes)} modes")

        for mode in modes:
            try:
                self.benchmark_mode(mode, kge_path=kge_path)
            except Exception as e:
                logger.error(f"Error benchmarking mode {mode.value}: {e}")
                continue

        return self.results

    def compare_modes(self) -> Dict:
        """
        Compare all benchmarked modes.

        Returns:
            Comparison report
        """
        if not self.results:
            logger.warning("No benchmark results available")
            return {}

        comparison = {
            'modes': list(self.results.keys()),
            'metrics': {}
        }

        # Extract baseline (BASIC mode)
        baseline = self.results.get('basic')

        for metric_name in ['precision@5', 'precision@10', 'recall@5', 'recall@10', 'mrr', 'ndcg@5', 'ndcg@10']:
            comparison['metrics'][metric_name] = {}

            for mode_name, results in self.results.items():
                result_dict = results.to_dict()
                value = result_dict.get(metric_name, 0.0)
                comparison['metrics'][metric_name][mode_name] = value

                # Calculate improvement over baseline
                if baseline and mode_name != 'basic':
                    baseline_value = baseline.to_dict().get(metric_name, 0.0)
                    if baseline_value > 0:
                        improvement = ((value - baseline_value) / baseline_value) * 100
                        comparison['metrics'][metric_name][f'{mode_name}_vs_baseline'] = f"+{improvement:.1f}%"

        # Latency comparison
        comparison['latency_ms'] = {
            mode_name: results.to_dict()['latency_ms']
            for mode_name, results in self.results.items()
        }

        return comparison

    def generate_report(self, output_path: Optional[str] = None) -> str:
        """
        Generate human-readable benchmark report.

        Args:
            output_path: Optional path to save report

        Returns:
            Report text
        """
        lines = []
        lines.append("=" * 80)
        lines.append("RAG RETRIEVAL BENCHMARK REPORT")
        lines.append("=" * 80)
        lines.append(f"Queries: {len(self.queries)}")
        lines.append("")

        # Per-mode results
        for mode_name, results in self.results.items():
            lines.append(f"\n{'='*80}")
            lines.append(f"MODE: {mode_name.upper()}")
            lines.append(f"{'='*80}")

            result_dict = results.to_dict()
            lines.append(f"  Precision@5:  {result_dict['precision@5']:.4f}")
            lines.append(f"  Precision@10: {result_dict['precision@10']:.4f}")
            lines.append(f"  Recall@5:     {result_dict['recall@5']:.4f}")
            lines.append(f"  Recall@10:    {result_dict['recall@10']:.4f}")
            lines.append(f"  MRR:          {result_dict['mrr']:.4f}")
            lines.append(f"  NDCG@5:       {result_dict['ndcg@5']:.4f}")
            lines.append(f"  NDCG@10:      {result_dict['ndcg@10']:.4f}")
            lines.append(f"  Latency:      {result_dict['latency_ms']:.2f}ms")
            lines.append(f"  Throughput:   {result_dict['throughput_qps']:.2f} QPS")

        # Comparison
        lines.append(f"\n{'='*80}")
        lines.append("COMPARISON vs BASELINE (BASIC)")
        lines.append(f"{'='*80}")

        comparison = self.compare_modes()
        baseline = self.results.get('basic')

        if baseline:
            for mode_name, results in self.results.items():
                if mode_name == 'basic':
                    continue

                lines.append(f"\n{mode_name.upper()} vs BASIC:")
                result_dict = results.to_dict()
                baseline_dict = baseline.to_dict()

                for metric in ['precision@5', 'recall@5', 'mrr', 'ndcg@5']:
                    value = result_dict[metric]
                    baseline_value = baseline_dict[metric]
                    if baseline_value > 0:
                        improvement = ((value - baseline_value) / baseline_value) * 100
                        sign = "+" if improvement >= 0 else ""
                        lines.append(f"  {metric:15s}: {value:.4f} ({sign}{improvement:.1f}%)")

        report = "\n".join(lines)

        if output_path:
            with open(output_path, 'w') as f:
                f.write(report)
            logger.info(f"Saved report to {output_path}")

        return report

    def save_results(self, output_path: str):
        """
        Save benchmark results to JSON.

        Args:
            output_path: Path to save JSON file
        """
        data = {
            'queries': len(self.queries),
            'modes': {
                mode_name: results.to_dict()
                for mode_name, results in self.results.items()
            },
            'comparison': self.compare_modes()
        }

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Saved results to {output_path}")


def create_test_graph() -> GraphDatabase:
    """
    Create a test graph for benchmarking.

    Returns:
        GraphDatabase with test data
    """
    db = GraphDatabase()

    # Create test claims with relationships
    claims = []

    # AI & Employment topic
    c1 = db.create_node('Claim', {
        'text': 'AI automation will displace factory workers in manufacturing',
        'confidence': 0.8
    })
    c2 = db.create_node('Claim', {
        'text': 'Factory automation has historically increased productivity',
        'confidence': 0.9
    })
    c3 = db.create_node('Claim', {
        'text': 'Workers can be retrained for AI-adjacent roles',
        'confidence': 0.7
    })

    # Healthcare topic
    c4 = db.create_node('Claim', {
        'text': 'AI improves diagnostic accuracy in medical imaging',
        'confidence': 0.85
    })
    c5 = db.create_node('Claim', {
        'text': 'Radiologists use AI tools to enhance workflow efficiency',
        'confidence': 0.8
    })

    # Create relationships
    db.create_relationship(c2, c1, 'SUPPORTS')
    db.create_relationship(c3, c1, 'CONTRADICTS')
    db.create_relationship(c5, c4, 'SUPPORTS')
    db.create_relationship(c1, c2, 'SIMILAR_TO', {'score': 0.75})

    claims.extend([c1, c2, c3, c4, c5])

    logger.info(f"Created test graph with {len(claims)} claims")
    return db


if __name__ == "__main__":
    # Example benchmark run
    logging.basicConfig(level=logging.INFO)

    # Create test graph
    db = create_test_graph()

    # Initialize benchmark
    benchmark = RAGBenchmark(db)

    # Generate synthetic queries
    benchmark.generate_synthetic_queries(num_queries=5)

    # Run benchmark (basic mode only for quick test)
    benchmark.run_full_benchmark(modes=[RetrievalMode.BASIC])

    # Generate report
    report = benchmark.generate_report()
    print(report)
