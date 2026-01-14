"""
PRD-011: Redis Caching Layer - Semantic Cache Service

Provides semantic similarity-based caching for queries:
- Exact match caching (hash-based)
- Semantic similarity matching using embeddings
- Configurable similarity threshold

This allows caching of semantically similar queries to reduce API costs
when users ask variations of the same question.
"""

from typing import Optional, Any, List
import hashlib
from dataclasses import dataclass, field


@dataclass
class CacheEntry:
    """
    A cache entry storing query, response, and optional embedding.

    Attributes:
        query: The original query text
        response: The cached response for this query
        embedding: Optional embedding vector for semantic matching
    """
    query: str
    response: Any
    embedding: List[float] = None


class SemanticCache:
    """
    Cache that matches semantically similar queries.

    Combines exact hash matching with embedding-based semantic similarity
    to maximize cache hits while maintaining accuracy.

    Features:
    - Exact match using normalized query hash
    - Semantic similarity using cosine similarity of embeddings
    - Configurable similarity threshold
    - Entry management and invalidation
    """

    def __init__(self, cache_service, similarity_threshold: float = 0.95):
        """
        Initialize semantic cache.

        Args:
            cache_service: The CacheService to use for backend storage
            similarity_threshold: Minimum cosine similarity for semantic match
                                 (default: 0.95 for high precision)
        """
        self.cache_service = cache_service
        self.similarity_threshold = similarity_threshold
        self._entries: dict[str, CacheEntry] = {}  # For similarity matching

    def _hash_query(self, query: str) -> str:
        """
        Create deterministic hash for exact match.

        Normalizes the query by lowercasing and stripping whitespace
        to improve exact match hit rate.

        Args:
            query: The query string to hash

        Returns:
            16-character hex hash string
        """
        normalized = query.lower().strip()
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]

    async def get(self, query: str, embedding: List[float] = None) -> Optional[Any]:
        """
        Get cached response for query, using semantic matching if available.

        Matching strategy:
        1. First try exact match using query hash
        2. If no exact match and embedding provided, try semantic similarity

        Args:
            query: The query string to look up
            embedding: Optional embedding vector for semantic matching

        Returns:
            Cached response if found, None otherwise
        """
        # Try exact match first (most efficient)
        key = self._hash_query(query)
        cached = await self.cache_service.get("semantic", key)
        if cached is not None:
            return cached

        # Try semantic similarity if embedding provided
        if embedding and self._entries:
            similar = self._find_similar(embedding)
            if similar:
                return similar.response

        return None

    async def set(
        self,
        query: str,
        response: Any,
        embedding: List[float] = None,
        ttl: int = 3600
    ) -> bool:
        """
        Cache response with optional embedding for semantic matching.

        Args:
            query: The query string
            response: The response to cache
            embedding: Optional embedding vector for future semantic matching
            ttl: Time-to-live in seconds (default: 1 hour)

        Returns:
            True if successfully cached
        """
        key = self._hash_query(query)

        # Store in cache backend for exact matches
        result = await self.cache_service.set("semantic", key, response, ttl)

        # Store embedding for similarity matching
        if embedding:
            self._entries[key] = CacheEntry(
                query=query,
                response=response,
                embedding=embedding
            )

        return result

    def _find_similar(self, embedding: List[float]) -> Optional[CacheEntry]:
        """
        Find entry with similar embedding above threshold.

        Iterates through all cached entries with embeddings and finds
        the one with the highest cosine similarity above the threshold.

        Args:
            embedding: The query embedding to match against

        Returns:
            The best matching CacheEntry, or None if no match above threshold
        """
        best_match = None
        best_score = 0.0

        for entry in self._entries.values():
            if entry.embedding:
                score = self._cosine_similarity(embedding, entry.embedding)
                if score > best_score and score >= self.similarity_threshold:
                    best_score = score
                    best_match = entry

        return best_match

    @staticmethod
    def _cosine_similarity(a: List[float], b: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.

        Cosine similarity = (A . B) / (||A|| * ||B||)

        Args:
            a: First vector
            b: Second vector

        Returns:
            Cosine similarity between -1.0 and 1.0
            Returns 0.0 for vectors of different lengths or zero vectors
        """
        if len(a) != len(b):
            return 0.0

        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)

    async def invalidate(self, query: str) -> bool:
        """
        Invalidate cache entry for query.

        Removes both the backend cache entry and the in-memory
        embedding entry.

        Args:
            query: The query string to invalidate

        Returns:
            True if entry was deleted from backend
        """
        key = self._hash_query(query)
        if key in self._entries:
            del self._entries[key]
        return await self.cache_service.delete("semantic", key)

    @property
    def entry_count(self) -> int:
        """
        Get the number of entries with embeddings for semantic matching.

        Returns:
            Count of entries in the semantic matching index
        """
        return len(self._entries)
