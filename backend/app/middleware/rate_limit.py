"""
Rate limiting middleware for FastAPI.
Implements per-user and per-IP rate limiting with sliding window algorithm.
"""

import time
from typing import Optional, Callable, Dict, Tuple, List
from dataclasses import dataclass
from abc import ABC, abstractmethod
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, JSONResponse

from app.config.rate_limits import RateLimitConfig, get_limit, DEFAULT_LIMITS


@dataclass
class RateLimitResult:
    """Result of a rate limit check."""
    allowed: bool
    remaining: int
    reset_at: float
    limit: int

    @property
    def retry_after(self) -> int:
        """Calculate seconds until the rate limit window resets."""
        return max(0, int(self.reset_at - time.time()))


class RateLimitBackend(ABC):
    """Abstract base class for rate limit storage backends."""

    @abstractmethod
    async def is_allowed(self, key: str, limit: int, window: int) -> RateLimitResult:
        """
        Check if a request is allowed under the rate limit.

        Args:
            key: Unique identifier for the rate limit bucket
            limit: Maximum number of requests allowed in the window
            window: Window size in seconds

        Returns:
            RateLimitResult indicating if request is allowed
        """
        pass

    @abstractmethod
    def reset(self, key: str = None) -> None:
        """
        Reset rate limit counters.

        Args:
            key: Specific key to reset, or None to reset all
        """
        pass


class MemoryRateLimitBackend(RateLimitBackend):
    """In-memory rate limit backend using fixed window algorithm."""

    def __init__(self):
        self._counters: Dict[str, Tuple[int, float]] = {}  # key -> (count, window_start)
        self._lock = None  # For thread safety if needed

    async def is_allowed(self, key: str, limit: int, window: int) -> RateLimitResult:
        """Check if request is allowed using fixed window algorithm."""
        now = time.time()

        if key in self._counters:
            count, window_start = self._counters[key]

            # Check if window has expired
            if now >= window_start + window:
                # Reset window
                self._counters[key] = (1, now)
                return RateLimitResult(
                    allowed=True,
                    remaining=limit - 1,
                    reset_at=now + window,
                    limit=limit
                )
            else:
                # Same window
                new_count = count + 1
                if new_count > limit:
                    return RateLimitResult(
                        allowed=False,
                        remaining=0,
                        reset_at=window_start + window,
                        limit=limit
                    )
                self._counters[key] = (new_count, window_start)
                return RateLimitResult(
                    allowed=True,
                    remaining=limit - new_count,
                    reset_at=window_start + window,
                    limit=limit
                )
        else:
            # First request in this window
            self._counters[key] = (1, now)
            return RateLimitResult(
                allowed=True,
                remaining=limit - 1,
                reset_at=now + window,
                limit=limit
            )

    def reset(self, key: str = None) -> None:
        """Reset rate limit counters."""
        if key:
            self._counters.pop(key, None)
        else:
            self._counters.clear()

    def get_counter(self, key: str) -> Optional[Tuple[int, float]]:
        """Get current counter state for a key (for testing/debugging)."""
        return self._counters.get(key)

    def set_counter(self, key: str, count: int, window_start: float) -> None:
        """Set counter state for a key (for testing)."""
        self._counters[key] = (count, window_start)


class SlidingWindowRateLimitBackend(RateLimitBackend):
    """
    In-memory rate limit backend using sliding window log algorithm.
    More accurate than fixed window but uses more memory.
    """

    def __init__(self):
        self._request_logs: Dict[str, List[float]] = {}  # key -> list of request timestamps

    async def is_allowed(self, key: str, limit: int, window: int) -> RateLimitResult:
        """Check if request is allowed using sliding window log algorithm."""
        now = time.time()
        window_start = now - window

        if key not in self._request_logs:
            self._request_logs[key] = []

        # Remove expired entries
        self._request_logs[key] = [
            ts for ts in self._request_logs[key] if ts > window_start
        ]

        current_count = len(self._request_logs[key])

        if current_count >= limit:
            # Find the oldest request to calculate reset time
            oldest_in_window = min(self._request_logs[key]) if self._request_logs[key] else now
            reset_at = oldest_in_window + window
            return RateLimitResult(
                allowed=False,
                remaining=0,
                reset_at=reset_at,
                limit=limit
            )

        # Add current request
        self._request_logs[key].append(now)
        remaining = limit - current_count - 1

        # Reset time is when the oldest request will expire
        if self._request_logs[key]:
            oldest = min(self._request_logs[key])
            reset_at = oldest + window
        else:
            reset_at = now + window

        return RateLimitResult(
            allowed=True,
            remaining=remaining,
            reset_at=reset_at,
            limit=limit
        )

    def reset(self, key: str = None) -> None:
        """Reset rate limit counters."""
        if key:
            self._request_logs.pop(key, None)
        else:
            self._request_logs.clear()

    def get_request_count(self, key: str, window: int = None) -> int:
        """Get current request count for a key (for testing/debugging)."""
        if key not in self._request_logs:
            return 0

        if window is not None:
            now = time.time()
            window_start = now - window
            return len([ts for ts in self._request_logs[key] if ts > window_start])

        return len(self._request_logs[key])


class RateLimiter:
    """Rate limiter with configurable backend."""

    def __init__(self, backend: RateLimitBackend = None):
        self.backend = backend or MemoryRateLimitBackend()

    def _get_key(self, request: Request, user_id: Optional[str] = None) -> str:
        """
        Generate a unique key for the rate limit bucket.

        Args:
            request: The incoming request
            user_id: Optional authenticated user ID

        Returns:
            Unique key string
        """
        if user_id:
            return f"rate:user:{user_id}"
        # Fall back to IP address for anonymous users
        client_ip = self._get_client_ip(request)
        return f"rate:ip:{client_ip}"

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request, considering proxies."""
        # Check for forwarded headers (reverse proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in the chain (original client)
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()

        # Fall back to direct connection IP
        if request.client:
            return request.client.host
        return "unknown"

    async def check(
        self,
        request: Request,
        user_id: Optional[str] = None,
        config: RateLimitConfig = None
    ) -> RateLimitResult:
        """
        Check if a request is allowed under rate limits.

        Args:
            request: The incoming request
            user_id: Optional authenticated user ID
            config: Optional custom rate limit configuration

        Returns:
            RateLimitResult indicating if request is allowed
        """
        key = self._get_key(request, user_id)
        endpoint = request.url.path

        if config is None:
            config = get_limit(endpoint, authenticated=user_id is not None)

        return await self.backend.is_allowed(key, config.requests, config.window_seconds)

    async def check_with_key(
        self,
        key: str,
        config: RateLimitConfig
    ) -> RateLimitResult:
        """
        Check rate limit using a custom key.

        Args:
            key: Custom rate limit key
            config: Rate limit configuration

        Returns:
            RateLimitResult indicating if request is allowed
        """
        return await self.backend.is_allowed(key, config.requests, config.window_seconds)

    def reset(self, key: str = None) -> None:
        """Reset rate limit counters."""
        self.backend.reset(key)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware that applies rate limiting to all requests."""

    def __init__(
        self,
        app,
        rate_limiter: RateLimiter = None,
        get_user_id: Callable = None,
        excluded_paths: List[str] = None
    ):
        """
        Initialize rate limit middleware.

        Args:
            app: The FastAPI application
            rate_limiter: Optional custom rate limiter instance
            get_user_id: Optional async callable to extract user ID from request
            excluded_paths: List of path prefixes to exclude from rate limiting
        """
        super().__init__(app)
        self.rate_limiter = rate_limiter or RateLimiter()
        self.get_user_id = get_user_id
        self.excluded_paths = excluded_paths or []

    def _is_excluded(self, path: str) -> bool:
        """Check if a path is excluded from rate limiting."""
        for excluded in self.excluded_paths:
            if path.startswith(excluded):
                return True
        return False

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and apply rate limiting."""
        # Skip rate limiting for excluded paths
        if self._is_excluded(request.url.path):
            return await call_next(request)

        # Get user ID if authenticated
        user_id = None
        if self.get_user_id:
            try:
                user_id = await self.get_user_id(request)
            except Exception:
                pass  # Anonymous request

        result = await self.rate_limiter.check(request, user_id)

        if not result.allowed:
            # Return a 429 response directly instead of raising HTTPException
            # This is needed because BaseHTTPMiddleware doesn't handle HTTPException well
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Please try again later."},
                headers={
                    "X-RateLimit-Limit": str(result.limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(result.reset_at)),
                    "Retry-After": str(result.retry_after)
                }
            )

        response = await call_next(request)

        # Add rate limit headers to successful responses
        response.headers["X-RateLimit-Limit"] = str(result.limit)
        response.headers["X-RateLimit-Remaining"] = str(result.remaining)
        response.headers["X-RateLimit-Reset"] = str(int(result.reset_at))

        return response


# Decorator for applying rate limits to specific endpoints
def rate_limit(
    requests: int = None,
    window_seconds: int = None,
    limit_name: str = None
):
    """
    Decorator to apply custom rate limits to specific endpoints.

    Usage:
        @rate_limit(requests=10, window_seconds=60)
        async def my_endpoint():
            ...

        @rate_limit(limit_name="chat")
        async def chat_endpoint():
            ...
    """
    def decorator(func):
        if limit_name and limit_name in DEFAULT_LIMITS:
            config = DEFAULT_LIMITS[limit_name]
        elif requests is not None and window_seconds is not None:
            config = RateLimitConfig(requests=requests, window_seconds=window_seconds)
        else:
            config = None

        # Store config on the function for middleware to use
        func._rate_limit_config = config
        return func

    return decorator


# Default singleton instance
rate_limiter = RateLimiter()


__all__ = [
    "RateLimitResult",
    "RateLimitBackend",
    "MemoryRateLimitBackend",
    "SlidingWindowRateLimitBackend",
    "RateLimiter",
    "RateLimitMiddleware",
    "rate_limit",
    "rate_limiter",
]
