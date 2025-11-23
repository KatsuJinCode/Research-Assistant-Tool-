"""
Backend Cache Module

Provides Redis-based caching for performance optimization.
"""

from .redis_cache import RedisCache, get_cache

__all__ = ['RedisCache', 'get_cache']
