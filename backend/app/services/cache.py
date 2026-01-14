"""
PRD-011: Redis Caching Layer - Cache Service

Provides caching backends and a high-level cache service for:
- Vector search results caching
- Query caching with TTL
- Hit/miss statistics tracking

Supports:
- MemoryCache: In-memory cache for testing and development
- RedisCache: Redis-based cache for production
- CacheService: High-level interface with namespacing and serialization
"""

import json
import hashlib
import time
from typing import Optional, Any
from abc import ABC, abstractmethod


class CacheBackend(ABC):
    """Abstract base class for cache backends."""

    @abstractmethod
    async def get(self, key: str) -> Optional[str]:
        """
        Get a value from the cache.

        Args:
            key: The cache key

        Returns:
            The cached value as a string, or None if not found/expired
        """
        pass

    @abstractmethod
    async def set(self, key: str, value: str, ttl: int = 3600) -> bool:
        """
        Set a value in the cache with TTL.

        Args:
            key: The cache key
            value: The value to cache (as string)
            ttl: Time-to-live in seconds (default: 1 hour)

        Returns:
            True if successfully stored
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """
        Delete a value from the cache.

        Args:
            key: The cache key

        Returns:
            True if the key was deleted, False if it didn't exist
        """
        pass


class MemoryCache(CacheBackend):
    """
    In-memory cache for testing and development.

    Stores values in a dictionary with expiry timestamps.
    Automatically cleans up expired entries on access.
    """

    def __init__(self):
        self._cache: dict[str, tuple[str, float]] = {}  # key -> (value, expiry_time)
        self._time = time  # Allow mocking in tests

    async def get(self, key: str) -> Optional[str]:
        """Get value from memory cache, checking expiry."""
        if key in self._cache:
            value, expiry = self._cache[key]
            if expiry > self._time.time():
                return value
            # Entry has expired, clean it up
            del self._cache[key]
        return None

    async def set(self, key: str, value: str, ttl: int = 3600) -> bool:
        """Set value in memory cache with expiry time."""
        self._cache[key] = (value, self._time.time() + ttl)
        return True

    async def delete(self, key: str) -> bool:
        """Delete value from memory cache."""
        if key in self._cache:
            del self._cache[key]
            return True
        return False


class RedisCache(CacheBackend):
    """
    Redis cache for production use.

    Connects to Redis and provides async cache operations.
    Uses lazy connection initialization.
    """

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        """
        Initialize Redis cache.

        Args:
            redis_url: Redis connection URL
        """
        self._redis_url = redis_url
        self._redis = None

    async def _get_client(self):
        """Get or create Redis client (lazy initialization)."""
        if self._redis is None:
            import redis.asyncio as redis
            self._redis = redis.from_url(self._redis_url)
        return self._redis

    async def get(self, key: str) -> Optional[str]:
        """Get value from Redis cache."""
        client = await self._get_client()
        value = await client.get(key)
        if value is not None and isinstance(value, bytes):
            return value.decode('utf-8')
        return value

    async def set(self, key: str, value: str, ttl: int = 3600) -> bool:
        """Set value in Redis cache with TTL using SETEX."""
        client = await self._get_client()
        await client.setex(key, ttl, value)
        return True

    async def delete(self, key: str) -> bool:
        """Delete value from Redis cache."""
        client = await self._get_client()
        result = await client.delete(key)
        return result > 0


class CacheService:
    """
    High-level cache service with namespacing and serialization.

    Provides:
    - Namespace-based key organization
    - Automatic JSON serialization/deserialization
    - Hit/miss statistics tracking
    - Factory function support for cache-aside pattern
    """

    def __init__(self, backend: CacheBackend, prefix: str = "strong_mvp"):
        """
        Initialize cache service.

        Args:
            backend: The cache backend to use (MemoryCache or RedisCache)
            prefix: Prefix for all cache keys (default: "strong_mvp")
        """
        self.backend = backend
        self.prefix = prefix
        self.hit_count = 0
        self.miss_count = 0

    def _make_key(self, namespace: str, key: str) -> str:
        """
        Create a fully qualified cache key with prefix and namespace.

        Args:
            namespace: The namespace for this key
            key: The base key

        Returns:
            Formatted key: "{prefix}:{namespace}:{key}"
        """
        return f"{self.prefix}:{namespace}:{key}"

    def _hash_key(self, data: str) -> str:
        """
        Create a deterministic hash of the input data.

        Args:
            data: The data to hash

        Returns:
            16-character hex hash string
        """
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    async def get(self, namespace: str, key: str) -> Optional[Any]:
        """
        Get a value from the cache.

        Args:
            namespace: The namespace for this key
            key: The cache key

        Returns:
            The deserialized cached value, or None if not found
        """
        full_key = self._make_key(namespace, key)
        value = await self.backend.get(full_key)
        if value is not None:
            self.hit_count += 1
            return json.loads(value)
        self.miss_count += 1
        return None

    async def set(self, namespace: str, key: str, value: Any, ttl: int = 3600) -> bool:
        """
        Set a value in the cache.

        Args:
            namespace: The namespace for this key
            key: The cache key
            value: The value to cache (will be JSON serialized)
            ttl: Time-to-live in seconds (default: 1 hour)

        Returns:
            True if successfully stored
        """
        full_key = self._make_key(namespace, key)
        return await self.backend.set(full_key, json.dumps(value), ttl)

    async def delete(self, namespace: str, key: str) -> bool:
        """
        Delete a value from the cache.

        Args:
            namespace: The namespace for this key
            key: The cache key

        Returns:
            True if the key was deleted, False if it didn't exist
        """
        full_key = self._make_key(namespace, key)
        return await self.backend.delete(full_key)

    async def get_or_set(
        self,
        namespace: str,
        key: str,
        factory,
        ttl: int = 3600
    ) -> Any:
        """
        Get from cache or call factory to create and cache value.

        Implements the cache-aside pattern:
        1. Try to get from cache
        2. If not found, call factory function
        3. Cache the result
        4. Return the value

        Args:
            namespace: The namespace for this key
            key: The cache key
            factory: A callable that returns the value to cache,
                    or a static value to cache
            ttl: Time-to-live in seconds (default: 1 hour)

        Returns:
            The cached or freshly computed value
        """
        cached = await self.get(namespace, key)
        if cached is not None:
            return cached

        # Call factory if it's callable, otherwise use the value directly
        if callable(factory):
            import asyncio
            if asyncio.iscoroutinefunction(factory):
                value = await factory()
            else:
                value = factory()
        else:
            value = factory

        await self.set(namespace, key, value, ttl)
        return value

    @property
    def stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dict with hits, misses, and hit_rate
        """
        total = self.hit_count + self.miss_count
        return {
            "hits": self.hit_count,
            "misses": self.miss_count,
            "hit_rate": self.hit_count / total if total > 0 else 0.0
        }
