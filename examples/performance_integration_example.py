"""
Performance Optimization Integration Example

Shows how to integrate all 5 performance features into your application.
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask, jsonify, request
from backend.database.neo4j_client import Neo4jClient
from backend.database.query_optimizer import QueryOptimizer
from backend.cache.redis_cache import get_cache
from web_ui.performance_routes import init_performance_monitoring
import time


def create_app():
    """Create Flask app with performance optimizations."""
    app = Flask(__name__)

    # Initialize cache
    cache = get_cache()

    # Initialize performance monitoring
    init_performance_monitoring(app)

    @app.route('/api/graph', methods=['GET'])
    def get_graph():
        """
        Get graph with all optimizations applied.

        Query params:
            project_id: Optional project filter
            limit: Max nodes (default 1000)
            skip: Pagination offset (default 0)
            use_cache: Whether to use cache (default true)
        """
        project_id = request.args.get('project_id')
        limit = int(request.args.get('limit', 1000))
        skip = int(request.args.get('skip', 0))
        use_cache = request.args.get('use_cache', 'true').lower() == 'true'

        # Try cache first
        cache_key = f"{project_id}:{skip}:{limit}"
        if use_cache:
            cached_graph = cache.get_cached_graph(cache_key)
            if cached_graph:
                return jsonify({
                    'graph': cached_graph,
                    'cached': True,
                    'cache_key': cache_key
                })

        # Query database with optimizations
        client = Neo4jClient()
        start_time = time.time()

        with client.get_session() as session:
            optimizer = QueryOptimizer(session)

            # Use pagination for large result sets
            if skip > 0:
                graph = optimizer.get_paginated_graph(
                    skip=skip,
                    limit=limit,
                    project_id=project_id
                )
            else:
                graph = optimizer.get_full_graph(
                    project_id=project_id,
                    limit=limit
                )

        query_time = (time.time() - start_time) * 1000

        # Cache result
        if use_cache:
            cache.cache_graph(cache_key, graph)

        # Track performance
        track_query_performance(
            query="get_graph",
            duration=query_time,
            result_count=len(graph['nodes']),
            cached=False
        )

        return jsonify({
            'graph': graph,
            'cached': False,
            'query_time_ms': query_time,
            'node_count': len(graph['nodes']),
            'link_count': len(graph['links'])
        })

    @app.route('/api/search', methods=['GET'])
    def search():
        """
        Search with caching.

        Query params:
            q: Search query
            limit: Max results (default 50)
        """
        query = request.args.get('q', '')
        limit = int(request.args.get('limit', 50))

        if not query:
            return jsonify({'error': 'Query required'}), 400

        # Try cache
        cached_results = cache.get_cached_search(query)
        if cached_results:
            return jsonify({
                'results': cached_results,
                'cached': True,
                'count': len(cached_results)
            })

        # Search database
        client = Neo4jClient()
        start_time = time.time()

        with client.get_session() as session:
            optimizer = QueryOptimizer(session)
            results = optimizer.search_full_text(query, limit=limit)

        query_time = (time.time() - start_time) * 1000

        # Cache results
        cache.cache_search_results(query, results)

        # Track performance
        track_query_performance(
            query=f"search:{query}",
            duration=query_time,
            result_count=len(results),
            cached=False
        )

        return jsonify({
            'results': results,
            'cached': False,
            'query_time_ms': query_time,
            'count': len(results)
        })

    @app.route('/api/document/<doc_id>', methods=['GET'])
    def get_document(doc_id):
        """Get document with caching."""
        # Try cache
        cached_doc = cache.get_cached_document(doc_id)
        if cached_doc:
            return jsonify({
                'document': cached_doc,
                'cached': True
            })

        # Query database
        client = Neo4jClient()
        start_time = time.time()

        with client.get_session() as session:
            optimizer = QueryOptimizer(session)
            document = optimizer.get_document_with_claims(doc_id, limit=100)

        query_time = (time.time() - start_time) * 1000

        if not document:
            return jsonify({'error': 'Document not found'}), 404

        # Cache document
        cache.cache_document(doc_id, document)

        # Track performance
        track_query_performance(
            query=f"get_document:{doc_id}",
            duration=query_time,
            result_count=1,
            cached=False
        )

        return jsonify({
            'document': document,
            'cached': False,
            'query_time_ms': query_time
        })

    @app.route('/api/invalidate-cache', methods=['POST'])
    def invalidate_cache():
        """Invalidate cache after updates."""
        data = request.get_json() or {}
        cache_type = data.get('type', 'all')

        if cache_type == 'graph':
            project_id = data.get('project_id')
            cache.invalidate_graph(project_id)
        elif cache_type == 'search':
            cache.invalidate_search()
        elif cache_type == 'document':
            doc_id = data.get('document_id')
            cache.invalidate_document(doc_id)
        elif cache_type == 'all':
            cache.invalidate_all()
        else:
            return jsonify({'error': 'Invalid cache type'}), 400

        return jsonify({'status': 'invalidated', 'type': cache_type})

    return app


def track_query_performance(query: str, duration: float, result_count: int, cached: bool):
    """Track query performance (would send to monitoring endpoint)."""
    # In real implementation, this would POST to /api/performance/track/query
    print(f"[PERF] Query: {query}, Duration: {duration:.2f}ms, Results: {result_count}, Cached: {cached}")


def setup_indexes():
    """One-time setup of database indexes."""
    from backend.database.create_indexes import IndexManager

    print("Setting up database indexes...")

    client = Neo4jClient()
    with client.get_session() as session:
        manager = IndexManager(session)
        manager.create_all_indexes()

    print("✓ Indexes created")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--setup-indexes', action='store_true', help='Create database indexes')
    parser.add_argument('--port', type=int, default=5000, help='Port to run on')
    args = parser.parse_args()

    if args.setup_indexes:
        setup_indexes()
        sys.exit(0)

    app = create_app()
    app.run(debug=True, port=args.port)
