"""
Performance Profiling Script

Profiles application performance and generates reports.
Tracks:
- API endpoint response times
- Database query performance
- Memory usage
- CPU usage
- Graph rendering performance

Usage:
    python scripts/performance_profiler.py
    python scripts/performance_profiler.py --endpoint /api/claims
    python scripts/performance_profiler.py --benchmark
"""

import os
import sys
import time
import argparse
import statistics
import psutil
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.core.logging_config import setup_logging

logger = setup_logging("performance_profiler", log_level="INFO")


class PerformanceProfiler:
    """Performance profiling and benchmarking"""

    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.results = []
        self.process = psutil.Process()

    def profile_endpoint(self, endpoint: str, method: str = "GET", data: Dict = None, runs: int = 10) -> Dict[str, Any]:
        """
        Profile an API endpoint's performance.

        Args:
            endpoint: API endpoint path
            method: HTTP method
            data: Request data for POST/PUT
            runs: Number of test runs

        Returns:
            Performance metrics
        """
        logger.info(f"Profiling {method} {endpoint} ({runs} runs)")

        response_times = []
        status_codes = []
        memory_usage = []
        cpu_usage = []

        url = f"{self.base_url}{endpoint}"

        for i in range(runs):
            # Record initial state
            mem_before = self.process.memory_info().rss / 1024 / 1024  # MB
            cpu_before = self.process.cpu_percent(interval=0.1)

            # Make request
            start_time = time.time()
            try:
                if method == "GET":
                    response = requests.get(url, timeout=30)
                elif method == "POST":
                    response = requests.post(url, json=data, timeout=30)
                elif method == "PUT":
                    response = requests.put(url, json=data, timeout=30)
                else:
                    raise ValueError(f"Unsupported method: {method}")

                response_time = (time.time() - start_time) * 1000  # ms
                response_times.append(response_time)
                status_codes.append(response.status_code)

            except Exception as e:
                logger.error(f"Request failed: {str(e)}")
                response_times.append(-1)
                status_codes.append(0)

            # Record final state
            mem_after = self.process.memory_info().rss / 1024 / 1024  # MB
            cpu_after = self.process.cpu_percent(interval=0.1)

            memory_usage.append(mem_after - mem_before)
            cpu_usage.append(cpu_after - cpu_before)

            # Brief delay between requests
            time.sleep(0.1)

        # Calculate statistics
        valid_times = [t for t in response_times if t > 0]

        if not valid_times:
            logger.error("No successful requests")
            return {
                "endpoint": endpoint,
                "method": method,
                "success": False,
                "error": "All requests failed"
            }

        result = {
            "endpoint": endpoint,
            "method": method,
            "success": True,
            "runs": runs,
            "response_time": {
                "min": min(valid_times),
                "max": max(valid_times),
                "mean": statistics.mean(valid_times),
                "median": statistics.median(valid_times),
                "stdev": statistics.stdev(valid_times) if len(valid_times) > 1 else 0,
                "p95": sorted(valid_times)[int(len(valid_times) * 0.95)],
                "p99": sorted(valid_times)[int(len(valid_times) * 0.99)]
            },
            "memory_delta_mb": {
                "min": min(memory_usage),
                "max": max(memory_usage),
                "mean": statistics.mean(memory_usage)
            },
            "cpu_percent": {
                "min": min(cpu_usage),
                "max": max(cpu_usage),
                "mean": statistics.mean(cpu_usage)
            },
            "status_codes": {
                code: status_codes.count(code)
                for code in set(status_codes)
            },
            "timestamp": datetime.now().isoformat()
        }

        logger.info(f"Mean response time: {result['response_time']['mean']:.2f} ms")
        logger.info(f"P95 response time: {result['response_time']['p95']:.2f} ms")

        self.results.append(result)

        return result

    def benchmark_all_endpoints(self) -> List[Dict]:
        """Benchmark all major API endpoints"""
        logger.info("Running comprehensive benchmark")

        endpoints = [
            ("/health", "GET"),
            ("/api/projects", "GET"),
            ("/api/documents", "GET"),
            ("/api/claims", "GET"),
            ("/api/search?q=test", "GET"),
            ("/api/graph", "GET"),
            ("/api/stats", "GET")
        ]

        results = []

        for endpoint, method in endpoints:
            try:
                result = self.profile_endpoint(endpoint, method, runs=20)
                results.append(result)

                # Brief delay between endpoint tests
                time.sleep(1)

            except Exception as e:
                logger.error(f"Benchmark failed for {endpoint}: {str(e)}")

        return results

    def profile_database_queries(self) -> Dict[str, Any]:
        """Profile database query performance"""
        logger.info("Profiling database queries")

        queries = [
            "MATCH (c:Claim) RETURN count(c)",
            "MATCH (d:Document) RETURN count(d)",
            "MATCH (c:Claim)-[r:SUPPORTS]->() RETURN count(r)",
            "MATCH (c:Claim) WHERE c.confidence > 0.8 RETURN c LIMIT 100"
        ]

        query_results = []

        # This would require direct Neo4j access
        # For now, return mock structure

        return {
            "queries_profiled": len(queries),
            "timestamp": datetime.now().isoformat()
        }

    def generate_report(self, output_file: str = "performance_report.json"):
        """
        Generate performance report.

        Args:
            output_file: Output file path
        """
        logger.info(f"Generating performance report: {output_file}")

        report = {
            "generated_at": datetime.now().isoformat(),
            "total_tests": len(self.results),
            "results": self.results,
            "summary": {
                "total_requests": sum(r.get("runs", 0) for r in self.results),
                "successful_tests": sum(1 for r in self.results if r.get("success", False)),
                "failed_tests": sum(1 for r in self.results if not r.get("success", True))
            }
        }

        # Calculate overall statistics
        all_response_times = []
        for result in self.results:
            if result.get("success") and "response_time" in result:
                all_response_times.append(result["response_time"]["mean"])

        if all_response_times:
            report["overall_performance"] = {
                "mean_response_time": statistics.mean(all_response_times),
                "fastest_endpoint": min((r for r in self.results if r.get("success")), key=lambda x: x["response_time"]["mean"])["endpoint"],
                "slowest_endpoint": max((r for r in self.results if r.get("success")), key=lambda x: x["response_time"]["mean"])["endpoint"]
            }

        # Save report
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)

        logger.info(f"Report saved to {output_path}")

        # Print summary
        self.print_summary(report)

    def print_summary(self, report: Dict):
        """Print performance summary to console"""
        print("\n" + "=" * 60)
        print("PERFORMANCE PROFILING SUMMARY")
        print("=" * 60)

        print(f"\nTotal Tests: {report['summary']['total_tests']}")
        print(f"Successful: {report['summary']['successful_tests']}")
        print(f"Failed: {report['summary']['failed_tests']}")

        if "overall_performance" in report:
            overall = report["overall_performance"]
            print(f"\nOverall Mean Response Time: {overall['mean_response_time']:.2f} ms")
            print(f"Fastest Endpoint: {overall['fastest_endpoint']}")
            print(f"Slowest Endpoint: {overall['slowest_endpoint']}")

        print("\n" + "=" * 60)
        print("INDIVIDUAL ENDPOINT RESULTS")
        print("=" * 60)

        for result in report["results"]:
            if result.get("success"):
                rt = result["response_time"]
                print(f"\n{result['method']} {result['endpoint']}")
                print(f"  Mean: {rt['mean']:.2f} ms")
                print(f"  P95:  {rt['p95']:.2f} ms")
                print(f"  P99:  {rt['p99']:.2f} ms")

        print("\n" + "=" * 60)


def main():
    """Main profiling script"""
    parser = argparse.ArgumentParser(description="Performance profiling utility")
    parser.add_argument(
        "--endpoint",
        type=str,
        help="Profile specific endpoint"
    )
    parser.add_argument(
        "--method",
        type=str,
        default="GET",
        help="HTTP method (default: GET)"
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=10,
        help="Number of test runs (default: 10)"
    )
    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="Run full benchmark suite"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="performance_report.json",
        help="Output file (default: performance_report.json)"
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default="http://localhost:5000",
        help="Base URL (default: http://localhost:5000)"
    )

    args = parser.parse_args()

    profiler = PerformanceProfiler(base_url=args.base_url)

    try:
        if args.benchmark:
            # Run full benchmark
            profiler.benchmark_all_endpoints()

        elif args.endpoint:
            # Profile specific endpoint
            profiler.profile_endpoint(
                args.endpoint,
                method=args.method,
                runs=args.runs
            )

        else:
            logger.error("Please specify --endpoint or --benchmark")
            sys.exit(1)

        # Generate report
        profiler.generate_report(args.output)

        logger.info("Profiling completed successfully")
        sys.exit(0)

    except Exception as e:
        logger.error(f"Profiling failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
