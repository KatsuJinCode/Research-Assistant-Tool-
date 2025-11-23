"""
Performance Monitoring Routes

Provides endpoints for monitoring system performance:
- Query performance metrics
- Cache statistics
- Graph rendering metrics
- Database performance
"""

from flask import Blueprint, jsonify, request
import time
import psutil
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Create blueprint
performance_bp = Blueprint('performance', __name__, url_prefix='/api/performance')

# Performance metrics storage
performance_metrics = {
    'queries': [],
    'renders': [],
    'cache_hits': 0,
    'cache_misses': 0,
    'start_time': datetime.utcnow()
}


@performance_bp.route('/metrics', methods=['GET'])
def get_metrics():
    """
    Get current performance metrics.

    Returns:
        JSON with comprehensive performance data
    """
    try:
        from backend.cache.redis_cache import get_cache

        cache = get_cache()
        cache_info = cache.get_cache_info()

        # System metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        # Calculate uptime
        uptime = datetime.utcnow() - performance_metrics['start_time']

        # Calculate averages
        query_times = [m['duration'] for m in performance_metrics['queries'][-100:]]
        avg_query_time = sum(query_times) / len(query_times) if query_times else 0

        render_times = [m['duration'] for m in performance_metrics['renders'][-100:]]
        avg_render_time = sum(render_times) / len(render_times) if render_times else 0

        metrics = {
            'timestamp': datetime.utcnow().isoformat(),
            'uptime_seconds': uptime.total_seconds(),

            # System metrics
            'system': {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_mb': memory.available / (1024 * 1024),
                'disk_percent': disk.percent,
                'disk_free_gb': disk.free / (1024 * 1024 * 1024)
            },

            # Query performance
            'queries': {
                'total_count': len(performance_metrics['queries']),
                'recent_count': len(performance_metrics['queries'][-100:]),
                'avg_time_ms': avg_query_time,
                'slowest_recent': max(query_times) if query_times else 0,
                'fastest_recent': min(query_times) if query_times else 0
            },

            # Render performance
            'renders': {
                'total_count': len(performance_metrics['renders']),
                'recent_count': len(performance_metrics['renders'][-100:]),
                'avg_time_ms': avg_render_time,
                'slowest_recent': max(render_times) if render_times else 0,
                'fastest_recent': min(render_times) if render_times else 0
            },

            # Cache performance
            'cache': cache_info
        }

        return jsonify(metrics)

    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        return jsonify({'error': str(e)}), 500


@performance_bp.route('/queries', methods=['GET'])
def get_query_performance():
    """
    Get detailed query performance metrics.

    Query params:
        limit: Number of recent queries to return (default 50)
        slow_only: Only return slow queries (>100ms)
    """
    try:
        limit = int(request.args.get('limit', 50))
        slow_only = request.args.get('slow_only', 'false').lower() == 'true'

        queries = performance_metrics['queries']

        if slow_only:
            queries = [q for q in queries if q['duration'] > 100]

        recent_queries = queries[-limit:]

        return jsonify({
            'queries': recent_queries,
            'count': len(recent_queries),
            'total_count': len(performance_metrics['queries'])
        })

    except Exception as e:
        logger.error(f"Error getting query performance: {e}")
        return jsonify({'error': str(e)}), 500


@performance_bp.route('/renders', methods=['GET'])
def get_render_performance():
    """
    Get graph rendering performance metrics.

    Query params:
        limit: Number of recent renders to return (default 50)
    """
    try:
        limit = int(request.args.get('limit', 50))

        recent_renders = performance_metrics['renders'][-limit:]

        return jsonify({
            'renders': recent_renders,
            'count': len(recent_renders),
            'total_count': len(performance_metrics['renders'])
        })

    except Exception as e:
        logger.error(f"Error getting render performance: {e}")
        return jsonify({'error': str(e)}), 500


@performance_bp.route('/track/query', methods=['POST'])
def track_query():
    """
    Track a query execution.

    Expected JSON:
        {
            "query": "MATCH (n) RETURN n",
            "duration": 123.45,
            "result_count": 100,
            "cached": false
        }
    """
    try:
        data = request.get_json()

        metric = {
            'timestamp': datetime.utcnow().isoformat(),
            'query': data.get('query', 'Unknown'),
            'duration': data.get('duration', 0),
            'result_count': data.get('result_count', 0),
            'cached': data.get('cached', False)
        }

        performance_metrics['queries'].append(metric)

        # Update cache stats
        if data.get('cached'):
            performance_metrics['cache_hits'] += 1
        else:
            performance_metrics['cache_misses'] += 1

        # Keep only last 1000 queries
        if len(performance_metrics['queries']) > 1000:
            performance_metrics['queries'] = performance_metrics['queries'][-1000:]

        return jsonify({'status': 'tracked'})

    except Exception as e:
        logger.error(f"Error tracking query: {e}")
        return jsonify({'error': str(e)}), 500


@performance_bp.route('/track/render', methods=['POST'])
def track_render():
    """
    Track a graph render.

    Expected JSON:
        {
            "node_count": 100,
            "link_count": 150,
            "duration": 234.56,
            "lod_level": "high"
        }
    """
    try:
        data = request.get_json()

        metric = {
            'timestamp': datetime.utcnow().isoformat(),
            'node_count': data.get('node_count', 0),
            'link_count': data.get('link_count', 0),
            'duration': data.get('duration', 0),
            'lod_level': data.get('lod_level', 'unknown')
        }

        performance_metrics['renders'].append(metric)

        # Keep only last 500 renders
        if len(performance_metrics['renders']) > 500:
            performance_metrics['renders'] = performance_metrics['renders'][-500:]

        return jsonify({'status': 'tracked'})

    except Exception as e:
        logger.error(f"Error tracking render: {e}")
        return jsonify({'error': str(e)}), 500


@performance_bp.route('/benchmark', methods=['POST'])
def run_benchmark():
    """
    Run performance benchmark.

    Tests:
        - Query performance with different node counts
        - Cache hit rate
        - Rendering performance

    Returns benchmark results.
    """
    try:
        from backend.database.neo4j_client import Neo4jClient
        from backend.database.query_optimizer import QueryOptimizer
        from backend.cache.redis_cache import get_cache

        results = {
            'timestamp': datetime.utcnow().isoformat(),
            'tests': []
        }

        client = Neo4jClient()
        cache = get_cache()

        with client.get_session() as session:
            optimizer = QueryOptimizer(session)

            # Test 1: Query performance with different limits
            for limit in [10, 50, 100, 500, 1000]:
                start = time.time()
                graph = optimizer.get_full_graph(limit=limit)
                duration = (time.time() - start) * 1000

                results['tests'].append({
                    'name': f'Query {limit} nodes',
                    'duration_ms': duration,
                    'node_count': len(graph['nodes'])
                })

            # Test 2: Cache performance
            cache_key_test = 'benchmark_test'

            # Uncached
            start = time.time()
            cached_val = cache.get('query', cache_key_test)
            uncached_duration = (time.time() - start) * 1000

            # Set cache
            cache.set('query', cache_key_test, {'test': 'data'})

            # Cached
            start = time.time()
            cached_val = cache.get('query', cache_key_test)
            cached_duration = (time.time() - start) * 1000

            results['tests'].append({
                'name': 'Cache miss',
                'duration_ms': uncached_duration
            })

            results['tests'].append({
                'name': 'Cache hit',
                'duration_ms': cached_duration,
                'speedup': uncached_duration / cached_duration if cached_duration > 0 else 0
            })

            # Clean up
            cache.delete('query', cache_key_test)

        return jsonify(results)

    except Exception as e:
        logger.error(f"Error running benchmark: {e}")
        return jsonify({'error': str(e)}), 500


@performance_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint.

    Returns system health status.
    """
    try:
        from backend.database.neo4j_client import Neo4jClient
        from backend.cache.redis_cache import get_cache

        health = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'components': {}
        }

        # Check Neo4j
        try:
            client = Neo4jClient()
            with client.get_session() as session:
                result = session.run("RETURN 1 as test")
                result.single()
            health['components']['neo4j'] = {'status': 'healthy'}
        except Exception as e:
            health['components']['neo4j'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health['status'] = 'degraded'

        # Check Redis
        try:
            cache = get_cache()
            cache_info = cache.get_cache_info()
            if cache_info.get('available'):
                health['components']['redis'] = {'status': 'healthy'}
            else:
                health['components']['redis'] = {
                    'status': 'unavailable',
                    'reason': cache_info.get('reason', 'Unknown')
                }
        except Exception as e:
            health['components']['redis'] = {
                'status': 'unhealthy',
                'error': str(e)
            }

        # Check system resources
        cpu = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()

        if cpu > 90 or memory.percent > 90:
            health['status'] = 'degraded'
            health['components']['system'] = {
                'status': 'degraded',
                'cpu_percent': cpu,
                'memory_percent': memory.percent
            }
        else:
            health['components']['system'] = {
                'status': 'healthy',
                'cpu_percent': cpu,
                'memory_percent': memory.percent
            }

        return jsonify(health)

    except Exception as e:
        logger.error(f"Error in health check: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500


@performance_bp.route('/stats/reset', methods=['POST'])
def reset_stats():
    """
    Reset performance statistics.

    Useful for testing and benchmarking.
    """
    try:
        performance_metrics['queries'] = []
        performance_metrics['renders'] = []
        performance_metrics['cache_hits'] = 0
        performance_metrics['cache_misses'] = 0
        performance_metrics['start_time'] = datetime.utcnow()

        return jsonify({'status': 'reset'})

    except Exception as e:
        logger.error(f"Error resetting stats: {e}")
        return jsonify({'error': str(e)}), 500


def init_performance_monitoring(app):
    """
    Initialize performance monitoring.

    Call this from main app.py to register the blueprint.

    Args:
        app: Flask application instance
    """
    app.register_blueprint(performance_bp)
    logger.info("Performance monitoring initialized")
