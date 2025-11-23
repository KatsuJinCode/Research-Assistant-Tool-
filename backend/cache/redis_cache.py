"""
Redis Caching Layer for Performance Optimization

Provides caching for:
- Graph data (TTL: 5 minutes)
- Search results (TTL: 1 minute)
- User sessions
- Statistics
- Query results

Features:
- Automatic TTL management
- Cache invalidation on updates
- Fallback to direct DB if Redis unavailable
- JSON serialization for complex objects
"""

import redis
import json
import logging
import hashlib
from typing import Any, Optional, Callable, Dict, List
from datetime import timedelta
from functools import wraps
import os

logger = logging.getLogger(__name__)


class RedisCache:
    """
    Redis-based caching system with automatic fallback.

    Provides transparent caching layer with TTL management
    and automatic invalidation.
    """

    def __init__(self, redis_url: str = None, enabled: bool = True):
        """
        Initialize Redis cache.

        Args:
            redis_url: Redis connection URL (defaults to env var REDIS_URL)
            enabled: Whether caching is enabled
        """
        self.enabled = enabled
        self.redis_url = redis_url or os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        self.client = None
        self.is_available = False

        # TTL settings (in seconds)
        self.ttls = {
            'graph': 300,        # 5 minutes
            'search': 60,        # 1 minute
            'session': 3600,     # 1 hour
            'stats': 300,        # 5 minutes
            'query': 180,        # 3 minutes
            'document': 600      # 10 minutes
        }

        # Cache key prefixes
        self.prefixes = {
            'graph': 'graph:',
            'search': 'search:',
            'session': 'session:',
            'stats': 'stats:',
            'query': 'query:',
            'document': 'doc:'
        }

        if self.enabled:
            self._connect()

    def _connect(self):
        """Establish Redis connection with fallback."""
        try:
            self.client = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2
            )
            # Test connection
            self.client.ping()
            self.is_available = True
            logger.info(f"Redis cache connected: {self.redis_url}")
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.warning(f"Redis cache unavailable: {e}. Running without cache.")
            self.is_available = False
            self.client = None
        except Exception as e:
            logger.error(f"Unexpected Redis error: {e}")
            self.is_available = False
            self.client = None

    def _make_key(self, category: str, identifier: str) -> str:
        """
        Generate cache key.

        Args:
            category: Cache category (graph, search, etc.)
            identifier: Unique identifier

        Returns:
            Full cache key
        """
        prefix = self.prefixes.get(category, '')
        return f"{prefix}{identifier}"

    def _serialize(self, value: Any) -> str:
        """Serialize value to JSON string."""
        try:
            return json.dumps(value, default=str)
        except (TypeError, ValueError) as e:
            logger.error(f"Serialization error: {e}")
            return None

    def _deserialize(self, value: str) -> Any:
        """Deserialize JSON string to value."""
        if value is None:
            return None
        try:
            return json.loads(value)
        except (TypeError, ValueError) as e:
            logger.error(f"Deserialization error: {e}")
            return None

    # ===========================
    # BASIC CACHE OPERATIONS
    # ===========================

    def get(self, category: str, identifier: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            category: Cache category
            identifier: Unique identifier

        Returns:
            Cached value or None if not found/unavailable
        """
        if not self.is_available:
            return None

        try:
            key = self._make_key(category, identifier)
            value = self.client.get(key)
            if value:
                logger.debug(f"Cache hit: {key}")
                return self._deserialize(value)
            logger.debug(f"Cache miss: {key}")
            return None
        except redis.RedisError as e:
            logger.warning(f"Cache get error: {e}")
            return None

    def set(self, category: str, identifier: str, value: Any,
            ttl: int = None) -> bool:
        """
        Set value in cache with TTL.

        Args:
            category: Cache category
            identifier: Unique identifier
            value: Value to cache
            ttl: Time-to-live in seconds (uses category default if not specified)

        Returns:
            True if successful, False otherwise
        """
        if not self.is_available:
            return False

        try:
            key = self._make_key(category, identifier)
            serialized = self._serialize(value)

            if serialized is None:
                return False

            ttl_value = ttl or self.ttls.get(category, 300)

            self.client.setex(key, ttl_value, serialized)
            logger.debug(f"Cache set: {key} (TTL: {ttl_value}s)")
            return True
        except redis.RedisError as e:
            logger.warning(f"Cache set error: {e}")
            return False

    def delete(self, category: str, identifier: str) -> bool:
        """
        Delete value from cache.

        Args:
            category: Cache category
            identifier: Unique identifier

        Returns:
            True if successful, False otherwise
        """
        if not self.is_available:
            return False

        try:
            key = self._make_key(category, identifier)
            self.client.delete(key)
            logger.debug(f"Cache delete: {key}")
            return True
        except redis.RedisError as e:
            logger.warning(f"Cache delete error: {e}")
            return False

    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching pattern.

        Args:
            pattern: Redis key pattern (e.g., "graph:*")

        Returns:
            Number of keys deleted
        """
        if not self.is_available:
            return 0

        try:
            keys = self.client.keys(pattern)
            if keys:
                deleted = self.client.delete(*keys)
                logger.info(f"Cache invalidated: {deleted} keys matching '{pattern}'")
                return deleted
            return 0
        except redis.RedisError as e:
            logger.warning(f"Cache invalidate error: {e}")
            return 0

    # ===========================
    # SPECIALIZED CACHE METHODS
    # ===========================

    def cache_graph(self, project_id: str, graph_data: Dict) -> bool:
        """
        Cache full graph data.

        Args:
            project_id: Project ID
            graph_data: Graph data dict with nodes and links

        Returns:
            True if cached successfully
        """
        identifier = f"full:{project_id}" if project_id else "full:global"
        return self.set('graph', identifier, graph_data)

    def get_cached_graph(self, project_id: str = None) -> Optional[Dict]:
        """
        Get cached graph data.

        Args:
            project_id: Project ID

        Returns:
            Cached graph data or None
        """
        identifier = f"full:{project_id}" if project_id else "full:global"
        return self.get('graph', identifier)

    def cache_search_results(self, query: str, results: List[Dict],
                            filters: Dict = None) -> bool:
        """
        Cache search results.

        Args:
            query: Search query
            results: Search results
            filters: Optional filters applied

        Returns:
            True if cached successfully
        """
        # Create hash of query + filters for unique key
        filter_str = json.dumps(filters or {}, sort_keys=True)
        identifier = hashlib.md5(f"{query}:{filter_str}".encode()).hexdigest()
        return self.set('search', identifier, results)

    def get_cached_search(self, query: str, filters: Dict = None) -> Optional[List[Dict]]:
        """
        Get cached search results.

        Args:
            query: Search query
            filters: Optional filters

        Returns:
            Cached results or None
        """
        filter_str = json.dumps(filters or {}, sort_keys=True)
        identifier = hashlib.md5(f"{query}:{filter_str}".encode()).hexdigest()
        return self.get('search', identifier)

    def cache_document(self, document_id: str, document_data: Dict) -> bool:
        """
        Cache document data.

        Args:
            document_id: Document ID
            document_data: Document data

        Returns:
            True if cached successfully
        """
        return self.set('document', document_id, document_data)

    def get_cached_document(self, document_id: str) -> Optional[Dict]:
        """
        Get cached document.

        Args:
            document_id: Document ID

        Returns:
            Cached document or None
        """
        return self.get('document', document_id)

    def cache_stats(self, stats_type: str, data: Dict) -> bool:
        """
        Cache statistics.

        Args:
            stats_type: Type of stats (e.g., 'graph', 'project', 'user')
            data: Statistics data

        Returns:
            True if cached successfully
        """
        return self.set('stats', stats_type, data)

    def get_cached_stats(self, stats_type: str) -> Optional[Dict]:
        """
        Get cached statistics.

        Args:
            stats_type: Type of stats

        Returns:
            Cached stats or None
        """
        return self.get('stats', stats_type)

    # ===========================
    # CACHE INVALIDATION
    # ===========================

    def invalidate_graph(self, project_id: str = None):
        """
        Invalidate graph cache.

        Args:
            project_id: Optional project ID (invalidates all graphs if None)
        """
        if project_id:
            pattern = f"graph:*{project_id}*"
        else:
            pattern = "graph:*"

        self.invalidate_pattern(pattern)

    def invalidate_search(self):
        """Invalidate all search caches."""
        self.invalidate_pattern("search:*")

    def invalidate_document(self, document_id: str = None):
        """
        Invalidate document cache.

        Args:
            document_id: Optional document ID (invalidates all if None)
        """
        if document_id:
            self.delete('document', document_id)
        else:
            self.invalidate_pattern("doc:*")

    def invalidate_all(self):
        """Invalidate entire cache."""
        if self.is_available:
            try:
                self.client.flushdb()
                logger.info("Cache completely invalidated")
            except redis.RedisError as e:
                logger.warning(f"Cache flush error: {e}")

    # ===========================
    # DECORATOR FOR AUTO-CACHING
    # ===========================

    def cached(self, category: str, ttl: int = None,
               key_func: Callable = None):
        """
        Decorator for automatic caching of function results.

        Args:
            category: Cache category
            ttl: Optional TTL override
            key_func: Function to generate cache key from args (defaults to str(args))

        Usage:
            @cache.cached('query', ttl=60)
            def expensive_query(param1, param2):
                return result
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    # Default: hash of function name + args
                    key_parts = [func.__name__] + [str(arg) for arg in args]
                    key_parts += [f"{k}={v}" for k, v in sorted(kwargs.items())]
                    cache_key = hashlib.md5(":".join(key_parts).encode()).hexdigest()

                # Try to get from cache
                cached_result = self.get(category, cache_key)
                if cached_result is not None:
                    return cached_result

                # Execute function
                result = func(*args, **kwargs)

                # Cache result
                self.set(category, cache_key, result, ttl=ttl)

                return result

            return wrapper
        return decorator

    # ===========================
    # CACHE STATISTICS
    # ===========================

    def get_cache_info(self) -> Dict[str, Any]:
        """
        Get cache statistics and info.

        Returns:
            Dict with cache statistics
        """
        if not self.is_available:
            return {
                'enabled': self.enabled,
                'available': False,
                'reason': 'Redis unavailable'
            }

        try:
            info = self.client.info('stats')
            keyspace = self.client.info('keyspace')

            db_info = keyspace.get('db0', {})

            return {
                'enabled': self.enabled,
                'available': True,
                'total_keys': db_info.get('keys', 0),
                'hits': info.get('keyspace_hits', 0),
                'misses': info.get('keyspace_misses', 0),
                'hit_rate': self._calculate_hit_rate(
                    info.get('keyspace_hits', 0),
                    info.get('keyspace_misses', 0)
                ),
                'memory_used': info.get('used_memory_human', 'N/A')
            }
        except redis.RedisError as e:
            logger.warning(f"Error getting cache info: {e}")
            return {
                'enabled': self.enabled,
                'available': False,
                'error': str(e)
            }

    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """Calculate cache hit rate percentage."""
        total = hits + misses
        if total == 0:
            return 0.0
        return (hits / total) * 100

    def close(self):
        """Close Redis connection."""
        if self.client:
            try:
                self.client.close()
                logger.info("Redis cache connection closed")
            except Exception as e:
                logger.warning(f"Error closing Redis connection: {e}")


# Global cache instance
_cache_instance = None


def get_cache(redis_url: str = None) -> RedisCache:
    """
    Get global cache instance (singleton pattern).

    Args:
        redis_url: Optional Redis URL

    Returns:
        RedisCache instance
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = RedisCache(redis_url=redis_url)
    return _cache_instance
