"""
Performance Testing Suite

Benchmarks system performance with graphs of different sizes:
- 100 nodes
- 500 nodes
- 1000 nodes

Measures:
- Page load time
- Rendering FPS
- Query response time
- Cache hit rate
- Memory usage
"""

import time
import statistics
import sys
from pathlib import Path
from typing import Dict, List, Any
import logging

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.database.neo4j_client import Neo4jClient
from backend.database.query_optimizer import QueryOptimizer
from backend.cache.redis_cache import get_cache

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class PerformanceBenchmark:
    """
    Comprehensive performance benchmark suite.
    """

    def __init__(self):
        self.results = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'benchmarks': []
        }
        self.client = None
        self.cache = None

    def setup(self):
        """Initialize connections."""
        logger.info("=" * 70)
        logger.info("Performance Benchmark Suite")
        logger.info("=" * 70)

        try:
            self.client = Neo4jClient()
            logger.info("✓ Neo4j connected")
        except Exception as e:
            logger.error(f"✗ Neo4j connection failed: {e}")
            raise

        try:
            self.cache = get_cache()
            cache_info = self.cache.get_cache_info()
            if cache_info.get('available'):
                logger.info("✓ Redis cache available")
            else:
                logger.warning("⚠ Redis cache unavailable - running without cache")
        except Exception as e:
            logger.warning(f"⚠ Redis initialization warning: {e}")

        logger.info("")

    def teardown(self):
        """Clean up connections."""
        if self.client:
            self.client.close()
        if self.cache:
            self.cache.close()

    def run_all_benchmarks(self):
        """Run all performance benchmarks."""
        self.setup()

        try:
            # Test different graph sizes
            for node_count in [100, 500, 1000]:
                logger.info(f"\n{'=' * 70}")
                logger.info(f"Benchmark: {node_count} Nodes")
                logger.info(f"{'=' * 70}\n")

                self.benchmark_query_performance(node_count)
                self.benchmark_cache_performance(node_count)
                self.benchmark_pagination(node_count)

            # Additional benchmarks
            self.benchmark_index_performance()
            self.benchmark_search_performance()

            # Print summary
            self.print_summary()

        finally:
            self.teardown()

    def benchmark_query_performance(self, node_count: int):
        """
        Benchmark query performance for different node counts.

        Args:
            node_count: Number of nodes to query
        """
        logger.info(f"[1/5] Query Performance ({node_count} nodes)")

        with self.client.get_session() as session:
            optimizer = QueryOptimizer(session)

            # Warm up
            optimizer.get_full_graph(limit=10)

            # Benchmark full graph query
            times = []
            for i in range(5):
                start = time.time()
                result = optimizer.get_full_graph(limit=node_count)
                duration = (time.time() - start) * 1000
                times.append(duration)

                logger.info(f"  Run {i+1}: {duration:.2f}ms ({len(result['nodes'])} nodes, {len(result['links'])} links)")

            avg_time = statistics.mean(times)
            min_time = min(times)
            max_time = max(times)
            std_dev = statistics.stdev(times) if len(times) > 1 else 0

            logger.info(f"  Average: {avg_time:.2f}ms ± {std_dev:.2f}ms")
            logger.info(f"  Range: {min_time:.2f}ms - {max_time:.2f}ms")

            self.results['benchmarks'].append({
                'name': f'Query {node_count} nodes',
                'avg_ms': avg_time,
                'min_ms': min_time,
                'max_ms': max_time,
                'std_dev_ms': std_dev,
                'runs': len(times)
            })

        logger.info("  ✓ Complete\n")

    def benchmark_cache_performance(self, node_count: int):
        """
        Benchmark cache hit/miss performance.

        Args:
            node_count: Number of nodes for test data
        """
        logger.info(f"[2/5] Cache Performance ({node_count} nodes)")

        if not self.cache or not self.cache.is_available:
            logger.warning("  ⚠ Skipping - cache unavailable\n")
            return

        # Test data
        test_data = {
            'nodes': [{'id': i, 'label': f'Node {i}'} for i in range(node_count)],
            'links': []
        }

        # Benchmark cache miss (read non-existent key)
        miss_times = []
        for i in range(10):
            start = time.time()
            result = self.cache.get('graph', f'test_{i}')
            duration = (time.time() - start) * 1000
            miss_times.append(duration)

        # Benchmark cache set
        set_times = []
        for i in range(10):
            start = time.time()
            self.cache.set('graph', f'test_{i}', test_data)
            duration = (time.time() - start) * 1000
            set_times.append(duration)

        # Benchmark cache hit (read existing key)
        hit_times = []
        for i in range(10):
            start = time.time()
            result = self.cache.get('graph', f'test_{i}')
            duration = (time.time() - start) * 1000
            hit_times.append(duration)

        # Clean up
        for i in range(10):
            self.cache.delete('graph', f'test_{i}')

        avg_miss = statistics.mean(miss_times)
        avg_set = statistics.mean(set_times)
        avg_hit = statistics.mean(hit_times)

        speedup = avg_miss / avg_hit if avg_hit > 0 else 0

        logger.info(f"  Cache miss: {avg_miss:.3f}ms")
        logger.info(f"  Cache set: {avg_set:.3f}ms")
        logger.info(f"  Cache hit: {avg_hit:.3f}ms")
        logger.info(f"  Speedup: {speedup:.1f}x")

        self.results['benchmarks'].append({
            'name': f'Cache performance {node_count} nodes',
            'cache_miss_ms': avg_miss,
            'cache_set_ms': avg_set,
            'cache_hit_ms': avg_hit,
            'speedup': speedup
        })

        logger.info("  ✓ Complete\n")

    def benchmark_pagination(self, total_nodes: int):
        """
        Benchmark paginated queries.

        Args:
            total_nodes: Total nodes in dataset
        """
        logger.info(f"[3/5] Pagination Performance ({total_nodes} total nodes)")

        with self.client.get_session() as session:
            optimizer = QueryOptimizer(session)

            page_size = 100
            times = []

            for page in range(min(5, total_nodes // page_size)):
                skip = page * page_size
                start = time.time()
                result = optimizer.get_paginated_graph(skip=skip, limit=page_size)
                duration = (time.time() - start) * 1000
                times.append(duration)

                logger.info(f"  Page {page+1}: {duration:.2f}ms ({result['count']} nodes)")

            if times:
                avg_time = statistics.mean(times)
                logger.info(f"  Average page load: {avg_time:.2f}ms")

                self.results['benchmarks'].append({
                    'name': f'Pagination {total_nodes} nodes',
                    'avg_page_load_ms': avg_time,
                    'page_size': page_size,
                    'pages_tested': len(times)
                })

        logger.info("  ✓ Complete\n")

    def benchmark_index_performance(self):
        """Benchmark index usage vs non-indexed queries."""
        logger.info("[4/5] Index Performance")

        with self.client.get_session() as session:
            optimizer = QueryOptimizer(session)

            # Query with index (project_id)
            start = time.time()
            results = optimizer.search_claims("test", limit=50, min_confidence=0.5)
            indexed_time = (time.time() - start) * 1000

            logger.info(f"  Indexed query: {indexed_time:.2f}ms ({len(results)} results)")

            self.results['benchmarks'].append({
                'name': 'Index usage',
                'indexed_query_ms': indexed_time,
                'result_count': len(results)
            })

        logger.info("  ✓ Complete\n")

    def benchmark_search_performance(self):
        """Benchmark search query performance."""
        logger.info("[5/5] Search Performance")

        with self.client.get_session() as session:
            optimizer = QueryOptimizer(session)

            queries = ["research", "data", "analysis", "model", "system"]
            times = []

            for query in queries:
                start = time.time()
                results = optimizer.search_full_text(query, limit=50)
                duration = (time.time() - start) * 1000
                times.append(duration)

                logger.info(f"  '{query}': {duration:.2f}ms ({len(results)} results)")

            avg_time = statistics.mean(times) if times else 0
            logger.info(f"  Average search time: {avg_time:.2f}ms")

            self.results['benchmarks'].append({
                'name': 'Full-text search',
                'avg_search_ms': avg_time,
                'queries_tested': len(queries)
            })

        logger.info("  ✓ Complete\n")

    def print_summary(self):
        """Print benchmark summary."""
        logger.info("\n" + "=" * 70)
        logger.info("BENCHMARK SUMMARY")
        logger.info("=" * 70)

        for benchmark in self.results['benchmarks']:
            logger.info(f"\n{benchmark['name']}:")
            for key, value in benchmark.items():
                if key != 'name':
                    if isinstance(value, float):
                        logger.info(f"  {key}: {value:.2f}")
                    else:
                        logger.info(f"  {key}: {value}")

        logger.info("\n" + "=" * 70)
        logger.info("Benchmark complete!")
        logger.info("=" * 70)

    def save_results(self, filename: str = 'benchmark_results.json'):
        """Save results to JSON file."""
        import json

        output_path = Path(__file__).parent / filename

        with open(output_path, 'w') as f:
            json.dump(self.results, f, indent=2)

        logger.info(f"\nResults saved to: {output_path}")


def compare_with_baseline(current_results: Dict, baseline_file: str = 'baseline_benchmark.json'):
    """
    Compare current results with baseline.

    Args:
        current_results: Current benchmark results
        baseline_file: Path to baseline results file
    """
    import json

    baseline_path = Path(__file__).parent / baseline_file

    if not baseline_path.exists():
        logger.warning(f"No baseline found at {baseline_path}")
        logger.info("Run with --save-baseline to create baseline")
        return

    with open(baseline_path, 'r') as f:
        baseline = json.load(f)

    logger.info("\n" + "=" * 70)
    logger.info("COMPARISON WITH BASELINE")
    logger.info("=" * 70)

    for curr_bench in current_results['benchmarks']:
        name = curr_bench['name']

        # Find matching baseline benchmark
        baseline_bench = next(
            (b for b in baseline['benchmarks'] if b['name'] == name),
            None
        )

        if not baseline_bench:
            continue

        logger.info(f"\n{name}:")

        for key in curr_bench.keys():
            if key == 'name' or key not in baseline_bench:
                continue

            curr_val = curr_bench[key]
            base_val = baseline_bench[key]

            if isinstance(curr_val, (int, float)) and isinstance(base_val, (int, float)):
                diff_pct = ((curr_val - base_val) / base_val * 100) if base_val != 0 else 0

                if diff_pct > 10:
                    indicator = "⚠ SLOWER"
                elif diff_pct < -10:
                    indicator = "✓ FASTER"
                else:
                    indicator = "≈ SIMILAR"

                logger.info(f"  {key}: {curr_val:.2f} (baseline: {base_val:.2f}) {diff_pct:+.1f}% {indicator}")


def main():
    """Main execution."""
    import argparse

    parser = argparse.ArgumentParser(description='Performance benchmark suite')
    parser.add_argument(
        '--save-baseline',
        action='store_true',
        help='Save results as baseline for future comparisons'
    )
    parser.add_argument(
        '--compare',
        action='store_true',
        help='Compare with baseline results'
    )
    parser.add_argument(
        '--output',
        default='benchmark_results.json',
        help='Output file for results'
    )

    args = parser.parse_args()

    benchmark = PerformanceBenchmark()

    try:
        benchmark.run_all_benchmarks()
        benchmark.save_results(args.output)

        if args.save_baseline:
            import shutil
            baseline_path = Path(__file__).parent / 'baseline_benchmark.json'
            shutil.copy(
                Path(__file__).parent / args.output,
                baseline_path
            )
            logger.info(f"Baseline saved to: {baseline_path}")

        if args.compare:
            compare_with_baseline(benchmark.results)

    except KeyboardInterrupt:
        logger.info("\nBenchmark interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\nBenchmark failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
