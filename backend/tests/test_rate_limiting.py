"""
Comprehensive tests for rate limiting functionality.
Tests cover:
- Rate limit configuration
- Memory-based rate limit backend
- Sliding window rate limit backend
- Rate limiter
- Rate limit middleware
- Per-user and per-IP limiting
- Window expiration and reset
- Different endpoint limits
- Edge cases
"""

import pytest
import time
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import FastAPI, Request, HTTPException
from fastapi.testclient import TestClient
from starlette.testclient import TestClient as StarletteTestClient


# Import rate limiting components
from app.config.rate_limits import (
    RateLimitConfig,
    DEFAULT_LIMITS,
    ENDPOINT_LIMITS,
    get_limit,
    get_limit_by_name,
)
from app.middleware.rate_limit import (
    RateLimitResult,
    RateLimitBackend,
    MemoryRateLimitBackend,
    SlidingWindowRateLimitBackend,
    RateLimiter,
    RateLimitMiddleware,
    rate_limit,
    rate_limiter,
)


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def rate_limit_config():
    """Create a test rate limit configuration."""
    return RateLimitConfig(requests=10, window_seconds=60)


@pytest.fixture
def memory_backend():
    """Create a fresh memory backend for each test."""
    return MemoryRateLimitBackend()


@pytest.fixture
def sliding_window_backend():
    """Create a fresh sliding window backend for each test."""
    return SlidingWindowRateLimitBackend()


@pytest.fixture
def rate_limiter_instance(memory_backend):
    """Create a rate limiter with memory backend."""
    return RateLimiter(backend=memory_backend)


@pytest.fixture
def mock_request():
    """Create a mock FastAPI request."""
    request = MagicMock(spec=Request)
    request.url.path = "/test"
    request.client.host = "127.0.0.1"
    request.headers = {}
    return request


@pytest.fixture
def test_app(rate_limiter_instance):
    """Create a test FastAPI app with rate limiting middleware."""
    app = FastAPI()

    @app.get("/test")
    async def test_endpoint():
        return {"message": "success"}

    @app.get("/health")
    async def health_endpoint():
        return {"status": "healthy"}

    @app.post("/chat")
    async def chat_endpoint():
        return {"response": "Hello"}

    app.add_middleware(RateLimitMiddleware, rate_limiter=rate_limiter_instance)
    return app


@pytest.fixture
def client(test_app):
    """Create a test client for the app."""
    return TestClient(test_app)


# =============================================================================
# Test RateLimitConfig
# =============================================================================

class TestRateLimitConfig:
    """Tests for RateLimitConfig dataclass."""

    def test_rate_limit_config_creation(self):
        """Test basic configuration creation."""
        config = RateLimitConfig(requests=100, window_seconds=60)
        assert config.requests == 100
        assert config.window_seconds == 60

    def test_rate_limit_config_window_minutes(self):
        """Test window_minutes property calculation."""
        config = RateLimitConfig(requests=100, window_seconds=60)
        assert config.window_minutes == 1.0

        config2 = RateLimitConfig(requests=100, window_seconds=120)
        assert config2.window_minutes == 2.0

        config3 = RateLimitConfig(requests=100, window_seconds=30)
        assert config3.window_minutes == 0.5

    def test_rate_limit_config_validation_negative_requests(self):
        """Test that negative requests raises ValueError."""
        with pytest.raises(ValueError, match="requests must be positive"):
            RateLimitConfig(requests=-1, window_seconds=60)

    def test_rate_limit_config_validation_zero_requests(self):
        """Test that zero requests raises ValueError."""
        with pytest.raises(ValueError, match="requests must be positive"):
            RateLimitConfig(requests=0, window_seconds=60)

    def test_rate_limit_config_validation_negative_window(self):
        """Test that negative window raises ValueError."""
        with pytest.raises(ValueError, match="window_seconds must be positive"):
            RateLimitConfig(requests=100, window_seconds=-1)

    def test_rate_limit_config_validation_zero_window(self):
        """Test that zero window raises ValueError."""
        with pytest.raises(ValueError, match="window_seconds must be positive"):
            RateLimitConfig(requests=100, window_seconds=0)


class TestDefaultLimits:
    """Tests for default rate limit configurations."""

    def test_default_limits_contains_authenticated(self):
        """Test that authenticated limit exists."""
        assert "authenticated" in DEFAULT_LIMITS
        assert DEFAULT_LIMITS["authenticated"].requests == 100
        assert DEFAULT_LIMITS["authenticated"].window_seconds == 60

    def test_default_limits_contains_anonymous(self):
        """Test that anonymous limit exists."""
        assert "anonymous" in DEFAULT_LIMITS
        assert DEFAULT_LIMITS["anonymous"].requests == 20
        assert DEFAULT_LIMITS["anonymous"].window_seconds == 60

    def test_default_limits_contains_chat(self):
        """Test that chat limit exists."""
        assert "chat" in DEFAULT_LIMITS
        assert DEFAULT_LIMITS["chat"].requests == 30

    def test_default_limits_contains_upload(self):
        """Test that upload limit exists."""
        assert "upload" in DEFAULT_LIMITS
        assert DEFAULT_LIMITS["upload"].requests == 10

    def test_default_limits_contains_health(self):
        """Test that health limit exists."""
        assert "health" in DEFAULT_LIMITS
        assert DEFAULT_LIMITS["health"].requests == 300

    def test_authenticated_higher_than_anonymous(self):
        """Test that authenticated users have higher limits than anonymous."""
        assert DEFAULT_LIMITS["authenticated"].requests > DEFAULT_LIMITS["anonymous"].requests


class TestGetLimit:
    """Tests for get_limit function."""

    def test_get_limit_for_chat_endpoint(self):
        """Test getting limit for /chat endpoint."""
        config = get_limit("/chat", authenticated=False)
        assert config.requests == 30  # Chat limit

    def test_get_limit_for_upload_endpoint(self):
        """Test getting limit for /upload/content endpoint."""
        config = get_limit("/upload/content", authenticated=False)
        assert config.requests == 10  # Upload limit

    def test_get_limit_for_health_endpoint(self):
        """Test getting limit for /health endpoint."""
        config = get_limit("/health", authenticated=False)
        assert config.requests == 300  # Health limit

    def test_get_limit_for_unknown_endpoint_authenticated(self):
        """Test getting limit for unknown endpoint when authenticated."""
        config = get_limit("/unknown", authenticated=True)
        assert config.requests == 100  # Authenticated default

    def test_get_limit_for_unknown_endpoint_anonymous(self):
        """Test getting limit for unknown endpoint when anonymous."""
        config = get_limit("/unknown", authenticated=False)
        assert config.requests == 20  # Anonymous default

    def test_get_limit_by_name_valid(self):
        """Test getting limit by name."""
        config = get_limit_by_name("chat")
        assert config is not None
        assert config.requests == 30

    def test_get_limit_by_name_invalid(self):
        """Test getting limit by invalid name."""
        config = get_limit_by_name("nonexistent")
        assert config is None


# =============================================================================
# Test RateLimitResult
# =============================================================================

class TestRateLimitResult:
    """Tests for RateLimitResult dataclass."""

    def test_rate_limit_result_creation(self):
        """Test basic result creation."""
        result = RateLimitResult(
            allowed=True,
            remaining=9,
            reset_at=time.time() + 60,
            limit=10
        )
        assert result.allowed is True
        assert result.remaining == 9
        assert result.limit == 10

    def test_rate_limit_result_retry_after_positive(self):
        """Test retry_after when reset is in future."""
        future_time = time.time() + 30
        result = RateLimitResult(
            allowed=False,
            remaining=0,
            reset_at=future_time,
            limit=10
        )
        assert result.retry_after > 0
        assert result.retry_after <= 30

    def test_rate_limit_result_retry_after_past(self):
        """Test retry_after when reset is in past."""
        past_time = time.time() - 10
        result = RateLimitResult(
            allowed=False,
            remaining=0,
            reset_at=past_time,
            limit=10
        )
        assert result.retry_after == 0

    def test_rate_limit_result_retry_after_zero(self):
        """Test retry_after at exact reset time."""
        result = RateLimitResult(
            allowed=False,
            remaining=0,
            reset_at=time.time(),
            limit=10
        )
        assert result.retry_after == 0


# =============================================================================
# Test MemoryRateLimitBackend
# =============================================================================

class TestMemoryRateLimitBackend:
    """Tests for MemoryRateLimitBackend."""

    @pytest.mark.asyncio
    async def test_first_request_allowed(self, memory_backend):
        """Test that first request is always allowed."""
        result = await memory_backend.is_allowed("test_key", limit=10, window=60)
        assert result.allowed is True
        assert result.remaining == 9
        assert result.limit == 10

    @pytest.mark.asyncio
    async def test_requests_within_limit(self, memory_backend):
        """Test that requests within limit are allowed."""
        for i in range(5):
            result = await memory_backend.is_allowed("test_key", limit=10, window=60)
            assert result.allowed is True
            assert result.remaining == 9 - i

    @pytest.mark.asyncio
    async def test_requests_at_limit(self, memory_backend):
        """Test that request exactly at limit is allowed."""
        for i in range(10):
            result = await memory_backend.is_allowed("test_key", limit=10, window=60)
            assert result.allowed is True

        # 10th request should have 0 remaining
        assert result.remaining == 0

    @pytest.mark.asyncio
    async def test_requests_exceed_limit(self, memory_backend):
        """Test that requests exceeding limit are rejected."""
        # Make 10 requests (reach limit)
        for _ in range(10):
            await memory_backend.is_allowed("test_key", limit=10, window=60)

        # 11th request should be rejected
        result = await memory_backend.is_allowed("test_key", limit=10, window=60)
        assert result.allowed is False
        assert result.remaining == 0

    @pytest.mark.asyncio
    async def test_different_keys_independent(self, memory_backend):
        """Test that different keys have independent counters."""
        # Exhaust limit for key1
        for _ in range(10):
            await memory_backend.is_allowed("key1", limit=10, window=60)

        # key1 should be blocked
        result1 = await memory_backend.is_allowed("key1", limit=10, window=60)
        assert result1.allowed is False

        # key2 should still work
        result2 = await memory_backend.is_allowed("key2", limit=10, window=60)
        assert result2.allowed is True

    @pytest.mark.asyncio
    async def test_window_reset(self, memory_backend):
        """Test that counter resets after window expires."""
        # Set up a counter that's already at limit with old timestamp
        old_time = time.time() - 70  # 70 seconds ago
        memory_backend.set_counter("test_key", 10, old_time)

        # Next request should reset the window
        result = await memory_backend.is_allowed("test_key", limit=10, window=60)
        assert result.allowed is True
        assert result.remaining == 9

    @pytest.mark.asyncio
    async def test_reset_specific_key(self, memory_backend):
        """Test resetting a specific key."""
        await memory_backend.is_allowed("key1", limit=10, window=60)
        await memory_backend.is_allowed("key2", limit=10, window=60)

        memory_backend.reset("key1")

        assert memory_backend.get_counter("key1") is None
        assert memory_backend.get_counter("key2") is not None

    @pytest.mark.asyncio
    async def test_reset_all_keys(self, memory_backend):
        """Test resetting all keys."""
        await memory_backend.is_allowed("key1", limit=10, window=60)
        await memory_backend.is_allowed("key2", limit=10, window=60)

        memory_backend.reset()

        assert memory_backend.get_counter("key1") is None
        assert memory_backend.get_counter("key2") is None

    @pytest.mark.asyncio
    async def test_reset_at_time_in_future(self, memory_backend):
        """Test that reset_at is in the future."""
        result = await memory_backend.is_allowed("test_key", limit=10, window=60)
        assert result.reset_at > time.time()
        assert result.reset_at <= time.time() + 60


# =============================================================================
# Test SlidingWindowRateLimitBackend
# =============================================================================

class TestSlidingWindowRateLimitBackend:
    """Tests for SlidingWindowRateLimitBackend."""

    @pytest.mark.asyncio
    async def test_first_request_allowed(self, sliding_window_backend):
        """Test that first request is allowed."""
        result = await sliding_window_backend.is_allowed("test_key", limit=10, window=60)
        assert result.allowed is True
        assert result.remaining == 9

    @pytest.mark.asyncio
    async def test_requests_within_limit(self, sliding_window_backend):
        """Test requests within limit are allowed."""
        for i in range(5):
            result = await sliding_window_backend.is_allowed("test_key", limit=10, window=60)
            assert result.allowed is True
            assert result.remaining == 9 - i

    @pytest.mark.asyncio
    async def test_requests_exceed_limit(self, sliding_window_backend):
        """Test requests exceeding limit are rejected."""
        for _ in range(10):
            await sliding_window_backend.is_allowed("test_key", limit=10, window=60)

        result = await sliding_window_backend.is_allowed("test_key", limit=10, window=60)
        assert result.allowed is False
        assert result.remaining == 0

    @pytest.mark.asyncio
    async def test_sliding_window_expired_requests(self, sliding_window_backend):
        """Test that old requests expire from sliding window."""
        # Add some requests
        for _ in range(5):
            await sliding_window_backend.is_allowed("test_key", limit=10, window=60)

        # Manually expire old requests by manipulating internal state
        now = time.time()
        sliding_window_backend._request_logs["test_key"] = [
            now - 70,  # Expired
            now - 65,  # Expired
            now - 10,  # Valid
            now - 5,   # Valid
            now,       # Valid
        ]

        # Next request should only count valid ones
        result = await sliding_window_backend.is_allowed("test_key", limit=10, window=60)
        assert result.allowed is True
        # 3 valid requests + 1 new = 4, so remaining = 10 - 4 = 6
        assert result.remaining == 6

    @pytest.mark.asyncio
    async def test_reset_specific_key(self, sliding_window_backend):
        """Test resetting a specific key."""
        await sliding_window_backend.is_allowed("key1", limit=10, window=60)
        await sliding_window_backend.is_allowed("key2", limit=10, window=60)

        sliding_window_backend.reset("key1")

        assert sliding_window_backend.get_request_count("key1") == 0
        assert sliding_window_backend.get_request_count("key2") == 1

    @pytest.mark.asyncio
    async def test_reset_all_keys(self, sliding_window_backend):
        """Test resetting all keys."""
        await sliding_window_backend.is_allowed("key1", limit=10, window=60)
        await sliding_window_backend.is_allowed("key2", limit=10, window=60)

        sliding_window_backend.reset()

        assert sliding_window_backend.get_request_count("key1") == 0
        assert sliding_window_backend.get_request_count("key2") == 0


# =============================================================================
# Test RateLimiter
# =============================================================================

class TestRateLimiter:
    """Tests for RateLimiter class."""

    def test_rate_limiter_default_backend(self):
        """Test that RateLimiter creates default backend."""
        limiter = RateLimiter()
        assert isinstance(limiter.backend, MemoryRateLimitBackend)

    def test_rate_limiter_custom_backend(self, sliding_window_backend):
        """Test that RateLimiter accepts custom backend."""
        limiter = RateLimiter(backend=sliding_window_backend)
        assert limiter.backend is sliding_window_backend

    @pytest.mark.asyncio
    async def test_check_with_user_id(self, rate_limiter_instance, mock_request):
        """Test rate limiting with user ID."""
        result = await rate_limiter_instance.check(mock_request, user_id="user123")
        assert result.allowed is True

    @pytest.mark.asyncio
    async def test_check_without_user_id_uses_ip(self, rate_limiter_instance, mock_request):
        """Test rate limiting falls back to IP when no user ID."""
        result = await rate_limiter_instance.check(mock_request, user_id=None)
        assert result.allowed is True

    @pytest.mark.asyncio
    async def test_check_with_custom_config(self, rate_limiter_instance, mock_request):
        """Test rate limiting with custom configuration."""
        custom_config = RateLimitConfig(requests=5, window_seconds=30)
        result = await rate_limiter_instance.check(mock_request, config=custom_config)
        assert result.limit == 5

    @pytest.mark.asyncio
    async def test_different_users_independent(self, rate_limiter_instance, mock_request):
        """Test that different users have independent rate limits."""
        config = RateLimitConfig(requests=2, window_seconds=60)

        # Exhaust limit for user1
        await rate_limiter_instance.check(mock_request, user_id="user1", config=config)
        await rate_limiter_instance.check(mock_request, user_id="user1", config=config)

        result1 = await rate_limiter_instance.check(mock_request, user_id="user1", config=config)
        assert result1.allowed is False

        # user2 should still have full limit
        result2 = await rate_limiter_instance.check(mock_request, user_id="user2", config=config)
        assert result2.allowed is True
        assert result2.remaining == 1

    @pytest.mark.asyncio
    async def test_check_with_key(self, rate_limiter_instance):
        """Test check_with_key method."""
        config = RateLimitConfig(requests=5, window_seconds=60)
        result = await rate_limiter_instance.check_with_key("custom:key", config)
        assert result.allowed is True
        assert result.limit == 5

    def test_reset_limiter(self, rate_limiter_instance):
        """Test resetting the rate limiter."""
        rate_limiter_instance.reset()
        # Should not raise any errors

    def test_get_client_ip_direct(self, rate_limiter_instance, mock_request):
        """Test getting client IP from direct connection."""
        mock_request.headers = {}
        ip = rate_limiter_instance._get_client_ip(mock_request)
        assert ip == "127.0.0.1"

    def test_get_client_ip_x_forwarded_for(self, rate_limiter_instance, mock_request):
        """Test getting client IP from X-Forwarded-For header."""
        mock_request.headers = {"X-Forwarded-For": "10.0.0.1, 192.168.1.1"}
        ip = rate_limiter_instance._get_client_ip(mock_request)
        assert ip == "10.0.0.1"

    def test_get_client_ip_x_real_ip(self, rate_limiter_instance, mock_request):
        """Test getting client IP from X-Real-IP header."""
        mock_request.headers = {"X-Real-IP": "10.0.0.2"}
        ip = rate_limiter_instance._get_client_ip(mock_request)
        assert ip == "10.0.0.2"

    def test_get_client_ip_no_client(self, rate_limiter_instance, mock_request):
        """Test getting client IP when no client info available."""
        mock_request.headers = {}
        mock_request.client = None
        ip = rate_limiter_instance._get_client_ip(mock_request)
        assert ip == "unknown"


# =============================================================================
# Test RateLimitMiddleware
# =============================================================================

class TestRateLimitMiddleware:
    """Tests for RateLimitMiddleware."""

    def test_middleware_allows_within_limit(self, client, rate_limiter_instance):
        """Test that requests within limit are allowed."""
        response = client.get("/test")
        assert response.status_code == 200
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers

    def test_middleware_returns_rate_limit_headers(self, client):
        """Test that rate limit headers are returned."""
        response = client.get("/test")
        assert response.status_code == 200

        assert int(response.headers["X-RateLimit-Limit"]) > 0
        assert int(response.headers["X-RateLimit-Remaining"]) >= 0
        assert int(response.headers["X-RateLimit-Reset"]) > 0

    def test_middleware_blocks_exceeded_limit(self, rate_limiter_instance):
        """Test that requests exceeding limit are blocked with 429."""
        app = FastAPI()

        @app.get("/test")
        async def test_endpoint():
            return {"message": "success"}

        # Use a very low limit
        config = RateLimitConfig(requests=2, window_seconds=60)

        async def get_config(*args, **kwargs):
            return config

        # Patch get_limit to use our low limit
        with patch('app.middleware.rate_limit.get_limit', return_value=config):
            app.add_middleware(RateLimitMiddleware, rate_limiter=rate_limiter_instance)
            client = TestClient(app)

            # First two requests should succeed
            response1 = client.get("/test")
            assert response1.status_code == 200

            response2 = client.get("/test")
            assert response2.status_code == 200

            # Third request should be rate limited
            response3 = client.get("/test")
            assert response3.status_code == 429

    def test_middleware_429_includes_retry_after(self, rate_limiter_instance):
        """Test that 429 response includes Retry-After header."""
        app = FastAPI()

        @app.get("/test")
        async def test_endpoint():
            return {"message": "success"}

        config = RateLimitConfig(requests=1, window_seconds=60)

        with patch('app.middleware.rate_limit.get_limit', return_value=config):
            app.add_middleware(RateLimitMiddleware, rate_limiter=rate_limiter_instance)
            client = TestClient(app)

            # First request succeeds
            client.get("/test")

            # Second request should be rate limited
            response = client.get("/test")
            assert response.status_code == 429
            assert "Retry-After" in response.headers
            assert int(response.headers["Retry-After"]) > 0

    def test_middleware_excluded_paths(self, rate_limiter_instance):
        """Test that excluded paths are not rate limited."""
        app = FastAPI()

        @app.get("/excluded/test")
        async def excluded_endpoint():
            return {"message": "success"}

        config = RateLimitConfig(requests=1, window_seconds=60)

        with patch('app.middleware.rate_limit.get_limit', return_value=config):
            app.add_middleware(
                RateLimitMiddleware,
                rate_limiter=rate_limiter_instance,
                excluded_paths=["/excluded"]
            )
            client = TestClient(app)

            # Multiple requests to excluded path should all succeed
            for _ in range(5):
                response = client.get("/excluded/test")
                assert response.status_code == 200

    def test_middleware_with_user_id_extractor(self, rate_limiter_instance):
        """Test middleware with custom user ID extractor."""
        app = FastAPI()

        @app.get("/test")
        async def test_endpoint():
            return {"message": "success"}

        async def get_user_id(request):
            return request.headers.get("X-User-ID")

        app.add_middleware(
            RateLimitMiddleware,
            rate_limiter=rate_limiter_instance,
            get_user_id=get_user_id
        )
        client = TestClient(app)

        # Request with user ID header
        response = client.get("/test", headers={"X-User-ID": "user123"})
        assert response.status_code == 200


# =============================================================================
# Test IP-Based Rate Limiting
# =============================================================================

class TestIPBasedRateLimiting:
    """Tests for IP-based rate limiting for anonymous users."""

    @pytest.mark.asyncio
    async def test_ip_rate_limit_key_generation(self, rate_limiter_instance, mock_request):
        """Test that IP-based key is generated for anonymous users."""
        key = rate_limiter_instance._get_key(mock_request, user_id=None)
        assert key.startswith("rate:ip:")
        assert "127.0.0.1" in key

    @pytest.mark.asyncio
    async def test_user_rate_limit_key_generation(self, rate_limiter_instance, mock_request):
        """Test that user-based key is generated for authenticated users."""
        key = rate_limiter_instance._get_key(mock_request, user_id="user123")
        assert key == "rate:user:user123"

    @pytest.mark.asyncio
    async def test_same_ip_shares_limit(self, rate_limiter_instance, mock_request):
        """Test that same IP shares rate limit."""
        config = RateLimitConfig(requests=2, window_seconds=60)

        await rate_limiter_instance.check(mock_request, user_id=None, config=config)
        await rate_limiter_instance.check(mock_request, user_id=None, config=config)

        result = await rate_limiter_instance.check(mock_request, user_id=None, config=config)
        assert result.allowed is False

    @pytest.mark.asyncio
    async def test_different_ips_independent(self, rate_limiter_instance):
        """Test that different IPs have independent limits."""
        config = RateLimitConfig(requests=1, window_seconds=60)

        request1 = MagicMock(spec=Request)
        request1.url.path = "/test"
        request1.client.host = "192.168.1.1"
        request1.headers = {}

        request2 = MagicMock(spec=Request)
        request2.url.path = "/test"
        request2.client.host = "192.168.1.2"
        request2.headers = {}

        # Exhaust limit for IP1
        await rate_limiter_instance.check(request1, user_id=None, config=config)
        result1 = await rate_limiter_instance.check(request1, user_id=None, config=config)
        assert result1.allowed is False

        # IP2 should still have full limit
        result2 = await rate_limiter_instance.check(request2, user_id=None, config=config)
        assert result2.allowed is True


# =============================================================================
# Test Window Expiration
# =============================================================================

class TestWindowExpiration:
    """Tests for rate limit window expiration and reset."""

    @pytest.mark.asyncio
    async def test_window_expires_counter_resets(self, memory_backend):
        """Test that counter resets after window expires."""
        # Make requests to exhaust limit
        for _ in range(5):
            await memory_backend.is_allowed("test_key", limit=5, window=60)

        result = await memory_backend.is_allowed("test_key", limit=5, window=60)
        assert result.allowed is False

        # Simulate window expiration by manipulating timestamp
        count, window_start = memory_backend.get_counter("test_key")
        memory_backend.set_counter("test_key", count, window_start - 70)

        # Now request should succeed
        result = await memory_backend.is_allowed("test_key", limit=5, window=60)
        assert result.allowed is True
        assert result.remaining == 4

    @pytest.mark.asyncio
    async def test_remaining_count_accurate_after_reset(self, memory_backend):
        """Test that remaining count is accurate after window reset."""
        # Exhaust limit
        for _ in range(5):
            await memory_backend.is_allowed("test_key", limit=5, window=60)

        # Simulate expiration
        count, window_start = memory_backend.get_counter("test_key")
        memory_backend.set_counter("test_key", count, window_start - 70)

        # After reset, should have full limit minus 1
        result = await memory_backend.is_allowed("test_key", limit=5, window=60)
        assert result.remaining == 4


# =============================================================================
# Test Edge Cases
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_limit_of_one(self, memory_backend):
        """Test rate limit with limit of 1."""
        result1 = await memory_backend.is_allowed("test_key", limit=1, window=60)
        assert result1.allowed is True
        assert result1.remaining == 0

        result2 = await memory_backend.is_allowed("test_key", limit=1, window=60)
        assert result2.allowed is False

    @pytest.mark.asyncio
    async def test_very_short_window(self, memory_backend):
        """Test rate limit with very short window."""
        result = await memory_backend.is_allowed("test_key", limit=10, window=1)
        assert result.allowed is True
        assert result.reset_at <= time.time() + 1

    @pytest.mark.asyncio
    async def test_large_limit(self, memory_backend):
        """Test rate limit with large limit."""
        result = await memory_backend.is_allowed("test_key", limit=10000, window=60)
        assert result.allowed is True
        assert result.remaining == 9999

    @pytest.mark.asyncio
    async def test_empty_key(self, memory_backend):
        """Test rate limit with empty key."""
        result = await memory_backend.is_allowed("", limit=10, window=60)
        assert result.allowed is True

    @pytest.mark.asyncio
    async def test_special_characters_in_key(self, memory_backend):
        """Test rate limit with special characters in key."""
        key = "rate:user:test@example.com"
        result = await memory_backend.is_allowed(key, limit=10, window=60)
        assert result.allowed is True

    @pytest.mark.asyncio
    async def test_unicode_in_key(self, memory_backend):
        """Test rate limit with unicode characters in key."""
        key = "rate:user:user_name_with_unicode"
        result = await memory_backend.is_allowed(key, limit=10, window=60)
        assert result.allowed is True


# =============================================================================
# Test Different Endpoint Limits
# =============================================================================

class TestEndpointLimits:
    """Tests for different endpoint-specific limits."""

    def test_chat_endpoint_has_specific_limit(self):
        """Test that /chat endpoint has its specific limit."""
        config = get_limit("/chat", authenticated=False)
        assert config.requests == 30

    def test_upload_endpoint_has_specific_limit(self):
        """Test that /upload/content endpoint has its specific limit."""
        config = get_limit("/upload/content", authenticated=False)
        assert config.requests == 10

    def test_health_endpoint_has_higher_limit(self):
        """Test that /health endpoint has higher limit."""
        config = get_limit("/health", authenticated=False)
        assert config.requests == 300

    def test_conversations_endpoint_has_specific_limit(self):
        """Test that /conversations endpoint has its specific limit."""
        config = get_limit("/conversations/user123", authenticated=True)
        assert config.requests == 60

    def test_authenticated_gets_higher_default(self):
        """Test that authenticated users get higher default limit."""
        anon_config = get_limit("/unknown", authenticated=False)
        auth_config = get_limit("/unknown", authenticated=True)
        assert auth_config.requests > anon_config.requests


# =============================================================================
# Test rate_limit Decorator
# =============================================================================

class TestRateLimitDecorator:
    """Tests for rate_limit decorator."""

    def test_decorator_with_custom_values(self):
        """Test decorator with custom requests and window."""
        @rate_limit(requests=5, window_seconds=30)
        async def test_func():
            pass

        assert hasattr(test_func, '_rate_limit_config')
        assert test_func._rate_limit_config.requests == 5
        assert test_func._rate_limit_config.window_seconds == 30

    def test_decorator_with_limit_name(self):
        """Test decorator with predefined limit name."""
        @rate_limit(limit_name="chat")
        async def test_func():
            pass

        assert hasattr(test_func, '_rate_limit_config')
        assert test_func._rate_limit_config.requests == 30

    def test_decorator_with_invalid_limit_name(self):
        """Test decorator with invalid limit name falls back to None."""
        @rate_limit(limit_name="nonexistent")
        async def test_func():
            pass

        assert test_func._rate_limit_config is None


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    """Integration tests for rate limiting system."""

    def test_full_rate_limit_flow(self):
        """Test complete rate limiting flow."""
        backend = MemoryRateLimitBackend()
        limiter = RateLimiter(backend=backend)

        app = FastAPI()

        @app.get("/api/test")
        async def api_endpoint():
            return {"message": "success"}

        config = RateLimitConfig(requests=3, window_seconds=60)

        with patch('app.middleware.rate_limit.get_limit', return_value=config):
            app.add_middleware(RateLimitMiddleware, rate_limiter=limiter)
            client = TestClient(app)

            # Requests should succeed up to limit
            for i in range(3):
                response = client.get("/api/test")
                assert response.status_code == 200
                remaining = int(response.headers["X-RateLimit-Remaining"])
                assert remaining == 2 - i

            # Next request should fail
            response = client.get("/api/test")
            assert response.status_code == 429
            assert "Retry-After" in response.headers

    def test_rate_limit_isolation_between_endpoints(self):
        """Test that rate limits are correctly applied per endpoint."""
        backend = MemoryRateLimitBackend()
        limiter = RateLimiter(backend=backend)

        app = FastAPI()

        @app.get("/chat")
        async def chat_endpoint():
            return {"message": "chat"}

        @app.get("/health")
        async def health_endpoint():
            return {"status": "healthy"}

        app.add_middleware(RateLimitMiddleware, rate_limiter=limiter)
        client = TestClient(app)

        # Chat endpoint should use chat limit (30)
        response = client.get("/chat")
        assert response.status_code == 200
        assert int(response.headers["X-RateLimit-Limit"]) == 30

        # Health endpoint should use health limit (300)
        response = client.get("/health")
        assert response.status_code == 200
        assert int(response.headers["X-RateLimit-Limit"]) == 300

    def test_rate_limiter_singleton(self):
        """Test that default rate_limiter singleton works."""
        # rate_limiter should be a RateLimiter instance
        assert isinstance(rate_limiter, RateLimiter)
        assert isinstance(rate_limiter.backend, MemoryRateLimitBackend)


# =============================================================================
# Test Concurrent Access
# =============================================================================

class TestConcurrentAccess:
    """Tests for concurrent access scenarios."""

    @pytest.mark.asyncio
    async def test_concurrent_requests_same_key(self, memory_backend):
        """Test concurrent requests to same key."""
        limit = 10

        async def make_request():
            return await memory_backend.is_allowed("concurrent_key", limit=limit, window=60)

        # Make concurrent requests
        results = await asyncio.gather(*[make_request() for _ in range(5)])

        allowed_count = sum(1 for r in results if r.allowed)
        assert allowed_count == 5

    @pytest.mark.asyncio
    async def test_concurrent_requests_exceed_limit(self, memory_backend):
        """Test concurrent requests that exceed limit."""
        limit = 5

        async def make_request():
            return await memory_backend.is_allowed("concurrent_key2", limit=limit, window=60)

        # Make more concurrent requests than the limit
        results = await asyncio.gather(*[make_request() for _ in range(10)])

        allowed_count = sum(1 for r in results if r.allowed)
        # Due to potential race conditions, we should have at most `limit` allowed
        assert allowed_count <= limit


# =============================================================================
# Test Headers Format
# =============================================================================

class TestHeadersFormat:
    """Tests for rate limit headers format."""

    def test_headers_are_strings(self, client):
        """Test that all rate limit headers are strings."""
        response = client.get("/test")

        assert isinstance(response.headers["X-RateLimit-Limit"], str)
        assert isinstance(response.headers["X-RateLimit-Remaining"], str)
        assert isinstance(response.headers["X-RateLimit-Reset"], str)

    def test_headers_are_valid_integers(self, client):
        """Test that rate limit headers are valid integer strings."""
        response = client.get("/test")

        # Should not raise
        int(response.headers["X-RateLimit-Limit"])
        int(response.headers["X-RateLimit-Remaining"])
        int(response.headers["X-RateLimit-Reset"])

    def test_429_response_headers(self):
        """Test 429 response includes all required headers."""
        backend = MemoryRateLimitBackend()
        limiter = RateLimiter(backend=backend)

        app = FastAPI()

        @app.get("/test")
        async def test_endpoint():
            return {"message": "success"}

        config = RateLimitConfig(requests=1, window_seconds=60)

        with patch('app.middleware.rate_limit.get_limit', return_value=config):
            app.add_middleware(RateLimitMiddleware, rate_limiter=limiter)
            client = TestClient(app)

            # First request succeeds
            client.get("/test")

            # Second request gets 429
            response = client.get("/test")
            assert response.status_code == 429

            # Check all headers present
            assert "X-RateLimit-Limit" in response.headers
            assert "X-RateLimit-Remaining" in response.headers
            assert "X-RateLimit-Reset" in response.headers
            assert "Retry-After" in response.headers

            # Verify values
            assert response.headers["X-RateLimit-Remaining"] == "0"
            assert int(response.headers["Retry-After"]) > 0
