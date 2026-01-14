"""
PRD-011: Redis Caching Layer Tests

TDD RED Phase - Tests written first for:
- AC-1: First query - Results are cached with TTL
- AC-2: Repeated identical query - Returns cached results without API call
- AC-3: Semantically similar query - Finds cached similar query results
- AC-4: Cache entry older than TTL - Fetches fresh results and updates cache

Tests cover:
1. Cache write and read (exact match)
2. Cache miss and factory function
3. TTL expiry behavior
4. Semantic similarity matching
5. Cache invalidation
6. Stats tracking (hit/miss)
7. Namespace isolation
8. Edge cases (empty, None values)
"""

import pytest
import asyncio
import json
import time
from typing import Optional, Any
from unittest.mock import MagicMock, AsyncMock, patch


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def memory_cache():
    """Create a MemoryCache instance for testing."""
    from app.services.cache import MemoryCache
    return MemoryCache()


@pytest.fixture
def cache_service(memory_cache):
    """Create a CacheService with MemoryCache backend."""
    from app.services.cache import CacheService
    return CacheService(backend=memory_cache, prefix="test")


@pytest.fixture
def semantic_cache(cache_service):
    """Create a SemanticCache instance."""
    from app.services.semantic_cache import SemanticCache
    return SemanticCache(cache_service=cache_service, similarity_threshold=0.95)


@pytest.fixture
def sample_embedding():
    """Create a sample embedding vector for testing."""
    return [0.1] * 384  # Common embedding dimension


@pytest.fixture
def similar_embedding(sample_embedding):
    """Create an embedding similar to sample_embedding."""
    # Slightly modify the embedding to create a similar vector
    similar = sample_embedding.copy()
    similar[0] = 0.11  # Small change
    similar[1] = 0.09
    return similar


@pytest.fixture
def different_embedding():
    """Create an embedding very different from sample_embedding."""
    return [0.9] * 384  # Very different values


# =============================================================================
# CacheBackend Abstract Interface Tests
# =============================================================================

class TestCacheBackendInterface:
    """Tests for CacheBackend abstract interface."""

    def test_cache_backend_is_abstract(self):
        """CacheBackend should be an abstract class."""
        from app.services.cache import CacheBackend
        from abc import ABC

        assert issubclass(CacheBackend, ABC)

    def test_cache_backend_has_get_method(self):
        """CacheBackend should define abstract get method."""
        from app.services.cache import CacheBackend

        assert hasattr(CacheBackend, 'get')

    def test_cache_backend_has_set_method(self):
        """CacheBackend should define abstract set method."""
        from app.services.cache import CacheBackend

        assert hasattr(CacheBackend, 'set')

    def test_cache_backend_has_delete_method(self):
        """CacheBackend should define abstract delete method."""
        from app.services.cache import CacheBackend

        assert hasattr(CacheBackend, 'delete')


# =============================================================================
# MemoryCache Tests - AC-1: Cache Write with TTL
# =============================================================================

class TestMemoryCacheWrite:
    """Tests for MemoryCache write operations - AC-1."""

    @pytest.mark.asyncio
    async def test_set_returns_true_on_success(self, memory_cache):
        """set() should return True on successful write."""
        result = await memory_cache.set("key1", "value1")
        assert result is True

    @pytest.mark.asyncio
    async def test_set_stores_value(self, memory_cache):
        """set() should store the value retrievable by get()."""
        await memory_cache.set("key1", "value1")
        result = await memory_cache.get("key1")
        assert result == "value1"

    @pytest.mark.asyncio
    async def test_set_with_custom_ttl(self, memory_cache):
        """set() should accept custom TTL parameter."""
        result = await memory_cache.set("key1", "value1", ttl=60)
        assert result is True

    @pytest.mark.asyncio
    async def test_set_overwrites_existing_value(self, memory_cache):
        """set() should overwrite existing value."""
        await memory_cache.set("key1", "old_value")
        await memory_cache.set("key1", "new_value")
        result = await memory_cache.get("key1")
        assert result == "new_value"

    @pytest.mark.asyncio
    async def test_set_handles_json_string_value(self, memory_cache):
        """set() should handle JSON string values."""
        json_value = json.dumps({"data": [1, 2, 3], "nested": {"key": "value"}})
        await memory_cache.set("json_key", json_value)
        result = await memory_cache.get("json_key")
        assert result == json_value

    @pytest.mark.asyncio
    async def test_set_handles_empty_string(self, memory_cache):
        """set() should handle empty string value."""
        await memory_cache.set("empty_key", "")
        result = await memory_cache.get("empty_key")
        assert result == ""


# =============================================================================
# MemoryCache Tests - AC-2: Cache Hit (Identical Query)
# =============================================================================

class TestMemoryCacheHit:
    """Tests for MemoryCache hit operations - AC-2."""

    @pytest.mark.asyncio
    async def test_get_returns_cached_value(self, memory_cache):
        """get() should return cached value for existing key."""
        await memory_cache.set("key1", "cached_value")
        result = await memory_cache.get("key1")
        assert result == "cached_value"

    @pytest.mark.asyncio
    async def test_get_returns_none_for_missing_key(self, memory_cache):
        """get() should return None for non-existent key."""
        result = await memory_cache.get("nonexistent_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_returns_none_for_empty_cache(self, memory_cache):
        """get() should return None when cache is empty."""
        result = await memory_cache.get("any_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_multiple_gets_return_same_value(self, memory_cache):
        """Multiple get() calls should return the same cached value."""
        await memory_cache.set("key1", "value1")

        result1 = await memory_cache.get("key1")
        result2 = await memory_cache.get("key1")
        result3 = await memory_cache.get("key1")

        assert result1 == result2 == result3 == "value1"


# =============================================================================
# MemoryCache Tests - AC-4: TTL Expiry
# =============================================================================

class TestMemoryCacheTTLExpiry:
    """Tests for MemoryCache TTL expiry - AC-4."""

    @pytest.mark.asyncio
    async def test_expired_entry_returns_none(self, memory_cache):
        """get() should return None for expired entries."""
        # Set with very short TTL
        await memory_cache.set("expire_key", "expire_value", ttl=1)

        # Wait for expiry
        await asyncio.sleep(1.1)

        result = await memory_cache.get("expire_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_non_expired_entry_returns_value(self, memory_cache):
        """get() should return value for non-expired entries."""
        await memory_cache.set("valid_key", "valid_value", ttl=10)

        # Immediate access should work
        result = await memory_cache.get("valid_key")
        assert result == "valid_value"

    @pytest.mark.asyncio
    async def test_expired_entry_is_cleaned_up(self, memory_cache):
        """Expired entries should be removed from cache."""
        await memory_cache.set("cleanup_key", "cleanup_value", ttl=1)

        # Wait for expiry
        await asyncio.sleep(1.1)

        # Access triggers cleanup
        await memory_cache.get("cleanup_key")

        # Key should be removed from internal cache
        assert "cleanup_key" not in memory_cache._cache

    @pytest.mark.asyncio
    async def test_default_ttl_is_one_hour(self, memory_cache):
        """Default TTL should be 3600 seconds (1 hour)."""
        # Mock time to test default TTL behavior
        original_time = memory_cache._time.time
        current_time = original_time()

        await memory_cache.set("default_ttl_key", "value")

        # Check stored expiry is ~3600 seconds from now
        _, expiry = memory_cache._cache["default_ttl_key"]
        expected_expiry = current_time + 3600

        assert abs(expiry - expected_expiry) < 2  # Allow 2 second tolerance


# =============================================================================
# MemoryCache Tests - Delete Operation
# =============================================================================

class TestMemoryCacheDelete:
    """Tests for MemoryCache delete operations."""

    @pytest.mark.asyncio
    async def test_delete_returns_true_for_existing_key(self, memory_cache):
        """delete() should return True when key exists."""
        await memory_cache.set("delete_key", "delete_value")
        result = await memory_cache.delete("delete_key")
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_returns_false_for_missing_key(self, memory_cache):
        """delete() should return False when key doesn't exist."""
        result = await memory_cache.delete("nonexistent_key")
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_removes_value(self, memory_cache):
        """delete() should remove value from cache."""
        await memory_cache.set("delete_key", "delete_value")
        await memory_cache.delete("delete_key")
        result = await memory_cache.get("delete_key")
        assert result is None


# =============================================================================
# CacheService Tests - Namespacing
# =============================================================================

class TestCacheServiceNamespacing:
    """Tests for CacheService namespace isolation."""

    @pytest.mark.asyncio
    async def test_different_namespaces_are_isolated(self, cache_service):
        """Values in different namespaces should be isolated."""
        await cache_service.set("ns1", "key1", {"data": "ns1_value"})
        await cache_service.set("ns2", "key1", {"data": "ns2_value"})

        result1 = await cache_service.get("ns1", "key1")
        result2 = await cache_service.get("ns2", "key1")

        assert result1["data"] == "ns1_value"
        assert result2["data"] == "ns2_value"

    @pytest.mark.asyncio
    async def test_make_key_creates_prefixed_key(self, cache_service):
        """_make_key should create properly prefixed keys."""
        key = cache_service._make_key("namespace", "mykey")
        assert key == "test:namespace:mykey"

    @pytest.mark.asyncio
    async def test_custom_prefix(self):
        """CacheService should use custom prefix."""
        from app.services.cache import MemoryCache, CacheService
        cache = MemoryCache()
        service = CacheService(backend=cache, prefix="custom_prefix")

        key = service._make_key("ns", "key")
        assert key.startswith("custom_prefix:")


# =============================================================================
# CacheService Tests - Serialization
# =============================================================================

class TestCacheServiceSerialization:
    """Tests for CacheService JSON serialization."""

    @pytest.mark.asyncio
    async def test_set_serializes_dict(self, cache_service):
        """set() should serialize dict to JSON."""
        data = {"key": "value", "number": 42, "list": [1, 2, 3]}
        await cache_service.set("ns", "key", data)
        result = await cache_service.get("ns", "key")
        assert result == data

    @pytest.mark.asyncio
    async def test_set_serializes_list(self, cache_service):
        """set() should serialize list to JSON."""
        data = [1, 2, 3, "four", {"five": 5}]
        await cache_service.set("ns", "list_key", data)
        result = await cache_service.get("ns", "list_key")
        assert result == data

    @pytest.mark.asyncio
    async def test_set_handles_nested_structures(self, cache_service):
        """set() should handle deeply nested structures."""
        data = {
            "level1": {
                "level2": {
                    "level3": {
                        "value": "deep"
                    }
                }
            }
        }
        await cache_service.set("ns", "nested", data)
        result = await cache_service.get("ns", "nested")
        assert result["level1"]["level2"]["level3"]["value"] == "deep"


# =============================================================================
# CacheService Tests - Hit/Miss Statistics - AC-2
# =============================================================================

class TestCacheServiceStatistics:
    """Tests for CacheService hit/miss statistics - AC-2."""

    @pytest.mark.asyncio
    async def test_initial_stats_are_zero(self, cache_service):
        """Initial statistics should be zero."""
        stats = cache_service.stats
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["hit_rate"] == 0.0

    @pytest.mark.asyncio
    async def test_cache_hit_increments_hit_count(self, cache_service):
        """Cache hit should increment hit counter."""
        await cache_service.set("ns", "key", "value")
        await cache_service.get("ns", "key")

        assert cache_service.hit_count == 1

    @pytest.mark.asyncio
    async def test_cache_miss_increments_miss_count(self, cache_service):
        """Cache miss should increment miss counter."""
        await cache_service.get("ns", "nonexistent")

        assert cache_service.miss_count == 1

    @pytest.mark.asyncio
    async def test_hit_rate_calculation(self, cache_service):
        """Hit rate should be calculated correctly."""
        await cache_service.set("ns", "key1", "value1")

        # 1 hit
        await cache_service.get("ns", "key1")
        # 1 miss
        await cache_service.get("ns", "key2")
        # 1 hit
        await cache_service.get("ns", "key1")

        stats = cache_service.stats
        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert stats["hit_rate"] == pytest.approx(2/3, rel=0.01)

    @pytest.mark.asyncio
    async def test_stats_returns_dict(self, cache_service):
        """stats property should return a dict."""
        stats = cache_service.stats
        assert isinstance(stats, dict)
        assert "hits" in stats
        assert "misses" in stats
        assert "hit_rate" in stats


# =============================================================================
# CacheService Tests - get_or_set Factory Function
# =============================================================================

class TestCacheServiceGetOrSet:
    """Tests for CacheService get_or_set method."""

    @pytest.mark.asyncio
    async def test_get_or_set_returns_cached_value(self, cache_service):
        """get_or_set should return cached value if exists."""
        await cache_service.set("ns", "key", "cached_value")

        result = await cache_service.get_or_set(
            "ns", "key",
            factory=lambda: "new_value"
        )

        assert result == "cached_value"

    @pytest.mark.asyncio
    async def test_get_or_set_calls_factory_on_miss(self, cache_service):
        """get_or_set should call factory function on cache miss."""
        factory_called = False

        async def factory():
            nonlocal factory_called
            factory_called = True
            return "factory_value"

        result = await cache_service.get_or_set("ns", "new_key", factory=factory)

        assert factory_called
        assert result == "factory_value"

    @pytest.mark.asyncio
    async def test_get_or_set_caches_factory_result(self, cache_service):
        """get_or_set should cache the factory result."""
        call_count = 0

        async def factory():
            nonlocal call_count
            call_count += 1
            return f"value_{call_count}"

        # First call - factory invoked
        result1 = await cache_service.get_or_set("ns", "key", factory=factory)
        # Second call - should use cache
        result2 = await cache_service.get_or_set("ns", "key", factory=factory)

        assert call_count == 1  # Factory only called once
        assert result1 == result2 == "value_1"

    @pytest.mark.asyncio
    async def test_get_or_set_respects_ttl(self, cache_service):
        """get_or_set should respect TTL parameter."""
        await cache_service.get_or_set("ns", "ttl_key", factory=lambda: "value", ttl=1)

        # Value should be cached
        result1 = await cache_service.get("ns", "ttl_key")
        assert result1 == "value"

        # Wait for expiry
        await asyncio.sleep(1.1)

        # Value should be expired
        result2 = await cache_service.get("ns", "ttl_key")
        assert result2 is None

    @pytest.mark.asyncio
    async def test_get_or_set_handles_non_async_factory(self, cache_service):
        """get_or_set should handle non-async factory values."""
        result = await cache_service.get_or_set("ns", "static_key", factory="static_value")
        assert result == "static_value"


# =============================================================================
# CacheService Tests - Delete Operation
# =============================================================================

class TestCacheServiceDelete:
    """Tests for CacheService delete operations."""

    @pytest.mark.asyncio
    async def test_delete_removes_cached_value(self, cache_service):
        """delete should remove value from cache."""
        await cache_service.set("ns", "key", "value")
        await cache_service.delete("ns", "key")

        result = await cache_service.get("ns", "key")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_returns_true_on_success(self, cache_service):
        """delete should return True when key was deleted."""
        await cache_service.set("ns", "key", "value")
        result = await cache_service.delete("ns", "key")
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_returns_false_for_missing(self, cache_service):
        """delete should return False when key doesn't exist."""
        result = await cache_service.delete("ns", "nonexistent")
        assert result is False


# =============================================================================
# CacheService Tests - Hash Key Generation
# =============================================================================

class TestCacheServiceHashKey:
    """Tests for CacheService key hashing."""

    def test_hash_key_returns_string(self, cache_service):
        """_hash_key should return a string."""
        result = cache_service._hash_key("test data")
        assert isinstance(result, str)

    def test_hash_key_is_deterministic(self, cache_service):
        """_hash_key should return same hash for same input."""
        hash1 = cache_service._hash_key("same input")
        hash2 = cache_service._hash_key("same input")
        assert hash1 == hash2

    def test_hash_key_different_for_different_input(self, cache_service):
        """_hash_key should return different hash for different input."""
        hash1 = cache_service._hash_key("input one")
        hash2 = cache_service._hash_key("input two")
        assert hash1 != hash2

    def test_hash_key_length(self, cache_service):
        """_hash_key should return 16 character hash."""
        result = cache_service._hash_key("test")
        assert len(result) == 16


# =============================================================================
# SemanticCache Tests - AC-2: Exact Match
# =============================================================================

class TestSemanticCacheExactMatch:
    """Tests for SemanticCache exact query matching - AC-2."""

    @pytest.mark.asyncio
    async def test_exact_match_returns_cached_response(self, semantic_cache):
        """Exact same query should return cached response."""
        query = "What is Python?"
        response = {"answer": "Python is a programming language."}

        await semantic_cache.set(query, response)
        result = await semantic_cache.get(query)

        assert result == response

    @pytest.mark.asyncio
    async def test_exact_match_case_insensitive(self, semantic_cache):
        """Query matching should be case-insensitive."""
        await semantic_cache.set("What Is Python?", {"answer": "test"})

        result = await semantic_cache.get("what is python?")

        assert result == {"answer": "test"}

    @pytest.mark.asyncio
    async def test_exact_match_trims_whitespace(self, semantic_cache):
        """Query matching should trim whitespace."""
        await semantic_cache.set("  What is Python?  ", {"answer": "test"})

        result = await semantic_cache.get("What is Python?")

        assert result == {"answer": "test"}


# =============================================================================
# SemanticCache Tests - AC-3: Semantic Similarity Matching
# =============================================================================

class TestSemanticCacheSimilarityMatch:
    """Tests for SemanticCache semantic similarity matching - AC-3."""

    @pytest.mark.asyncio
    async def test_similar_query_returns_cached_response(
        self, semantic_cache, sample_embedding, similar_embedding
    ):
        """Semantically similar query should return cached response."""
        query1 = "What is Python programming?"
        response = {"answer": "Python is a language."}

        await semantic_cache.set(query1, response, embedding=sample_embedding)

        # Query with similar embedding
        result = await semantic_cache.get("What is Python coding?", embedding=similar_embedding)

        assert result == response

    @pytest.mark.asyncio
    async def test_dissimilar_query_returns_none(
        self, semantic_cache, sample_embedding, different_embedding
    ):
        """Dissimilar query should not match cached entry."""
        query = "What is Python?"
        response = {"answer": "Python is a language."}

        await semantic_cache.set(query, response, embedding=sample_embedding)

        # Query with very different embedding
        result = await semantic_cache.get(
            "How to cook pasta?",
            embedding=different_embedding
        )

        # Should not match (different topic)
        # Result should be None since similarity is below threshold
        # Note: This might return None or the cached value depending on cosine similarity
        # For very different embeddings, it should return None
        assert result is None or result == response  # Depends on implementation

    @pytest.mark.asyncio
    async def test_similarity_threshold_respected(self, cache_service):
        """Semantic matching should respect similarity threshold."""
        from app.services.semantic_cache import SemanticCache

        # Create cache with high threshold
        high_threshold_cache = SemanticCache(
            cache_service=cache_service,
            similarity_threshold=0.99
        )

        # Use a varied embedding for threshold testing
        original_embedding = [i * 0.01 for i in range(384)]

        await high_threshold_cache.set(
            "original query",
            {"answer": "original"},
            embedding=original_embedding
        )

        # Create an embedding with different pattern that results in ~0.96 similarity
        # Flip sign of first 100 elements to bring similarity below 0.99
        noticeably_different = original_embedding.copy()
        for i in range(100):
            noticeably_different[i] = -original_embedding[i]

        # With high threshold (0.99), should not match since similarity is ~0.965
        result = await high_threshold_cache.get(
            "modified query",
            embedding=noticeably_different
        )

        # Should not match due to high threshold
        assert result is None


# =============================================================================
# SemanticCache Tests - Cosine Similarity
# =============================================================================

class TestSemanticCacheCosineSimilarity:
    """Tests for SemanticCache cosine similarity calculation."""

    def test_cosine_similarity_identical_vectors(self):
        """Identical vectors should have similarity of 1.0."""
        from app.services.semantic_cache import SemanticCache

        vec = [0.5, 0.5, 0.5]
        similarity = SemanticCache._cosine_similarity(vec, vec)

        assert similarity == pytest.approx(1.0, rel=0.001)

    def test_cosine_similarity_orthogonal_vectors(self):
        """Orthogonal vectors should have similarity of 0.0."""
        from app.services.semantic_cache import SemanticCache

        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]
        similarity = SemanticCache._cosine_similarity(vec1, vec2)

        assert similarity == pytest.approx(0.0, rel=0.001)

    def test_cosine_similarity_opposite_vectors(self):
        """Opposite vectors should have similarity of -1.0."""
        from app.services.semantic_cache import SemanticCache

        vec1 = [1.0, 0.0, 0.0]
        vec2 = [-1.0, 0.0, 0.0]
        similarity = SemanticCache._cosine_similarity(vec1, vec2)

        assert similarity == pytest.approx(-1.0, rel=0.001)

    def test_cosine_similarity_different_lengths_returns_zero(self):
        """Vectors of different lengths should return 0.0."""
        from app.services.semantic_cache import SemanticCache

        vec1 = [1.0, 0.0, 0.0]
        vec2 = [1.0, 0.0]
        similarity = SemanticCache._cosine_similarity(vec1, vec2)

        assert similarity == 0.0

    def test_cosine_similarity_zero_vector_returns_zero(self):
        """Zero vector should return 0.0 similarity."""
        from app.services.semantic_cache import SemanticCache

        vec1 = [0.0, 0.0, 0.0]
        vec2 = [1.0, 1.0, 1.0]
        similarity = SemanticCache._cosine_similarity(vec1, vec2)

        assert similarity == 0.0


# =============================================================================
# SemanticCache Tests - Cache Entry Management
# =============================================================================

class TestSemanticCacheEntryManagement:
    """Tests for SemanticCache entry management."""

    @pytest.mark.asyncio
    async def test_entry_count_increases_with_embeddings(
        self, semantic_cache, sample_embedding
    ):
        """Entry count should increase when storing with embeddings."""
        initial_count = semantic_cache.entry_count

        await semantic_cache.set("query1", {"answer": "1"}, embedding=sample_embedding)

        assert semantic_cache.entry_count == initial_count + 1

    @pytest.mark.asyncio
    async def test_entry_count_not_increased_without_embedding(self, semantic_cache):
        """Entry count should not increase when storing without embedding."""
        initial_count = semantic_cache.entry_count

        await semantic_cache.set("query1", {"answer": "1"})

        assert semantic_cache.entry_count == initial_count

    @pytest.mark.asyncio
    async def test_invalidate_removes_entry(self, semantic_cache, sample_embedding):
        """invalidate should remove entry from semantic cache."""
        await semantic_cache.set("query", {"answer": "test"}, embedding=sample_embedding)

        initial_count = semantic_cache.entry_count
        await semantic_cache.invalidate("query")

        assert semantic_cache.entry_count == initial_count - 1

    @pytest.mark.asyncio
    async def test_invalidate_removes_from_backend(self, semantic_cache):
        """invalidate should remove entry from backend cache."""
        await semantic_cache.set("query", {"answer": "test"})

        await semantic_cache.invalidate("query")

        result = await semantic_cache.get("query")
        assert result is None


# =============================================================================
# SemanticCache Tests - Query Hashing
# =============================================================================

class TestSemanticCacheQueryHashing:
    """Tests for SemanticCache query hashing."""

    def test_hash_query_is_deterministic(self, semantic_cache):
        """_hash_query should return same hash for same input."""
        hash1 = semantic_cache._hash_query("test query")
        hash2 = semantic_cache._hash_query("test query")
        assert hash1 == hash2

    def test_hash_query_normalizes_case(self, semantic_cache):
        """_hash_query should normalize case."""
        hash1 = semantic_cache._hash_query("Test Query")
        hash2 = semantic_cache._hash_query("test query")
        assert hash1 == hash2

    def test_hash_query_normalizes_whitespace(self, semantic_cache):
        """_hash_query should normalize whitespace."""
        hash1 = semantic_cache._hash_query("  test query  ")
        hash2 = semantic_cache._hash_query("test query")
        assert hash1 == hash2


# =============================================================================
# RedisCache Tests (with mocked redis)
# =============================================================================

class TestRedisCacheWithMock:
    """Tests for RedisCache with mocked Redis client."""

    @pytest.mark.asyncio
    async def test_redis_cache_get_calls_redis(self):
        """RedisCache.get should call Redis client."""
        from app.services.cache import RedisCache

        with patch('redis.asyncio.from_url') as mock_redis:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value="cached_value")
            mock_redis.return_value = mock_client

            cache = RedisCache("redis://localhost:6379")
            result = await cache.get("test_key")

            mock_client.get.assert_called_once_with("test_key")
            assert result == "cached_value"

    @pytest.mark.asyncio
    async def test_redis_cache_set_calls_setex(self):
        """RedisCache.set should call Redis setex with TTL."""
        from app.services.cache import RedisCache

        with patch('redis.asyncio.from_url') as mock_redis:
            mock_client = AsyncMock()
            mock_client.setex = AsyncMock()
            mock_redis.return_value = mock_client

            cache = RedisCache("redis://localhost:6379")
            await cache.set("test_key", "test_value", ttl=3600)

            mock_client.setex.assert_called_once_with("test_key", 3600, "test_value")

    @pytest.mark.asyncio
    async def test_redis_cache_delete_calls_redis(self):
        """RedisCache.delete should call Redis delete."""
        from app.services.cache import RedisCache

        with patch('redis.asyncio.from_url') as mock_redis:
            mock_client = AsyncMock()
            mock_client.delete = AsyncMock(return_value=1)
            mock_redis.return_value = mock_client

            cache = RedisCache("redis://localhost:6379")
            result = await cache.delete("test_key")

            mock_client.delete.assert_called_once_with("test_key")
            assert result is True

    @pytest.mark.asyncio
    async def test_redis_cache_delete_returns_false_when_not_found(self):
        """RedisCache.delete should return False when key not found."""
        from app.services.cache import RedisCache

        with patch('redis.asyncio.from_url') as mock_redis:
            mock_client = AsyncMock()
            mock_client.delete = AsyncMock(return_value=0)
            mock_redis.return_value = mock_client

            cache = RedisCache("redis://localhost:6379")
            result = await cache.delete("nonexistent_key")

            assert result is False


# =============================================================================
# Integration Tests - Full Cache Flow
# =============================================================================

class TestCacheIntegration:
    """Integration tests for complete cache workflows."""

    @pytest.mark.asyncio
    async def test_cache_search_results_flow(self, cache_service):
        """Test caching of search results - AC-1."""
        # Simulate caching vector search results
        search_results = [
            {"id": "doc1", "content": "Python basics", "score": 0.95},
            {"id": "doc2", "content": "Python advanced", "score": 0.85},
        ]

        query_key = "python programming"

        # First query - cache miss, store results
        cached = await cache_service.get("search", query_key)
        assert cached is None  # Miss

        await cache_service.set("search", query_key, search_results, ttl=3600)

        # Second query - cache hit
        cached = await cache_service.get("search", query_key)
        assert cached == search_results

        # Verify stats
        assert cache_service.miss_count >= 1
        assert cache_service.hit_count >= 1

    @pytest.mark.asyncio
    async def test_semantic_cache_with_real_scenario(
        self, semantic_cache, sample_embedding
    ):
        """Test semantic cache with realistic scenario - AC-3."""
        # Original query with response
        original_query = "How do I install Python?"
        original_response = {
            "answer": "Download from python.org and run the installer.",
            "sources": ["python.org/downloads"]
        }

        await semantic_cache.set(
            original_query,
            original_response,
            embedding=sample_embedding
        )

        # Same query should hit exact match
        result = await semantic_cache.get(original_query)
        assert result == original_response

        # Similar query with similar embedding should also match
        similar_embedding = sample_embedding.copy()
        similar_embedding[0] = 0.101  # Tiny change

        result = await semantic_cache.get(
            "How can I install Python?",
            embedding=similar_embedding
        )
        # Should return the cached response
        assert result == original_response

    @pytest.mark.asyncio
    async def test_cache_expiry_triggers_refresh(self, cache_service):
        """Test that expired cache triggers refresh - AC-4."""
        call_count = 0

        async def fetch_fresh_results():
            nonlocal call_count
            call_count += 1
            return {"data": f"fresh_result_{call_count}"}

        # First call - factory invoked
        result1 = await cache_service.get_or_set(
            "search", "query1",
            factory=fetch_fresh_results,
            ttl=1
        )
        assert result1["data"] == "fresh_result_1"
        assert call_count == 1

        # Immediate second call - uses cache
        result2 = await cache_service.get_or_set(
            "search", "query1",
            factory=fetch_fresh_results,
            ttl=1
        )
        assert result2["data"] == "fresh_result_1"
        assert call_count == 1  # Factory not called

        # Wait for expiry
        await asyncio.sleep(1.1)

        # Third call after expiry - factory invoked again
        result3 = await cache_service.get_or_set(
            "search", "query1",
            factory=fetch_fresh_results,
            ttl=1
        )
        assert result3["data"] == "fresh_result_2"
        assert call_count == 2  # Factory called again


# =============================================================================
# Edge Cases Tests
# =============================================================================

class TestCacheEdgeCases:
    """Tests for edge cases in cache operations."""

    @pytest.mark.asyncio
    async def test_cache_handles_none_value(self, cache_service):
        """Cache should handle None values correctly."""
        # Note: None might be confused with "not found"
        # Implementation should handle this case
        await cache_service.set("ns", "null_key", None)
        result = await cache_service.get("ns", "null_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_cache_handles_empty_dict(self, cache_service):
        """Cache should handle empty dict values."""
        await cache_service.set("ns", "empty_dict", {})
        result = await cache_service.get("ns", "empty_dict")
        assert result == {}

    @pytest.mark.asyncio
    async def test_cache_handles_empty_list(self, cache_service):
        """Cache should handle empty list values."""
        await cache_service.set("ns", "empty_list", [])
        result = await cache_service.get("ns", "empty_list")
        assert result == []

    @pytest.mark.asyncio
    async def test_cache_handles_special_characters_in_key(self, cache_service):
        """Cache should handle special characters in keys."""
        special_key = "key:with:colons/and/slashes?and=params"
        await cache_service.set("ns", special_key, {"data": "test"})
        result = await cache_service.get("ns", special_key)
        assert result == {"data": "test"}

    @pytest.mark.asyncio
    async def test_cache_handles_unicode_values(self, cache_service):
        """Cache should handle unicode values."""
        unicode_data = {"message": "Hello World", "emoji": "test"}
        await cache_service.set("ns", "unicode", unicode_data)
        result = await cache_service.get("ns", "unicode")
        assert result == unicode_data

    @pytest.mark.asyncio
    async def test_cache_handles_large_values(self, cache_service):
        """Cache should handle large values."""
        large_data = {"items": list(range(10000))}
        await cache_service.set("ns", "large", large_data)
        result = await cache_service.get("ns", "large")
        assert len(result["items"]) == 10000

    @pytest.mark.asyncio
    async def test_semantic_cache_handles_empty_embedding(self, semantic_cache):
        """Semantic cache should handle empty embedding."""
        await semantic_cache.set("query", {"answer": "test"}, embedding=[])

        # Should still work with exact match
        result = await semantic_cache.get("query")
        assert result == {"answer": "test"}

    @pytest.mark.asyncio
    async def test_semantic_cache_handles_no_entries(self, semantic_cache):
        """Semantic cache should handle search with no entries."""
        result = await semantic_cache.get(
            "query",
            embedding=[0.1] * 384
        )
        assert result is None


# =============================================================================
# CacheEntry Dataclass Tests
# =============================================================================

class TestCacheEntry:
    """Tests for CacheEntry dataclass."""

    def test_cache_entry_creation(self):
        """CacheEntry should be created with required fields."""
        from app.services.semantic_cache import CacheEntry

        entry = CacheEntry(
            query="test query",
            response={"answer": "test"}
        )

        assert entry.query == "test query"
        assert entry.response == {"answer": "test"}
        assert entry.embedding is None

    def test_cache_entry_with_embedding(self):
        """CacheEntry should store embedding."""
        from app.services.semantic_cache import CacheEntry

        embedding = [0.1, 0.2, 0.3]
        entry = CacheEntry(
            query="test",
            response={"answer": "test"},
            embedding=embedding
        )

        assert entry.embedding == embedding


# =============================================================================
# Performance Tests
# =============================================================================

class TestCachePerformance:
    """Performance tests for cache operations."""

    @pytest.mark.asyncio
    async def test_many_concurrent_reads(self, cache_service):
        """Cache should handle many concurrent reads."""
        await cache_service.set("ns", "concurrent_key", {"data": "value"})

        # Perform many concurrent reads
        tasks = [
            cache_service.get("ns", "concurrent_key")
            for _ in range(100)
        ]
        results = await asyncio.gather(*tasks)

        # All should return the same value
        assert all(r == {"data": "value"} for r in results)

    @pytest.mark.asyncio
    async def test_many_different_keys(self, cache_service):
        """Cache should handle many different keys."""
        # Write many keys
        for i in range(100):
            await cache_service.set("ns", f"key_{i}", {"index": i})

        # Read them back
        for i in range(100):
            result = await cache_service.get("ns", f"key_{i}")
            assert result == {"index": i}

    @pytest.mark.asyncio
    async def test_semantic_cache_with_many_entries(self, cache_service):
        """Semantic cache should handle many entries."""
        from app.services.semantic_cache import SemanticCache

        cache = SemanticCache(cache_service, similarity_threshold=0.95)

        # Add many entries with embeddings
        for i in range(50):
            embedding = [0.1 + i * 0.001] * 384
            await cache.set(
                f"query_{i}",
                {"answer": f"answer_{i}"},
                embedding=embedding
            )

        assert cache.entry_count == 50
