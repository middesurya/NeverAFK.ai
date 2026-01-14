"""
Rate limiting configuration for the API.
Defines rate limits for different user types and endpoints.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class RateLimitConfig:
    """Configuration for a rate limit."""
    requests: int
    window_seconds: int

    @property
    def window_minutes(self) -> float:
        """Return the window size in minutes."""
        return self.window_seconds / 60

    def __post_init__(self):
        """Validate configuration values."""
        if self.requests <= 0:
            raise ValueError("requests must be positive")
        if self.window_seconds <= 0:
            raise ValueError("window_seconds must be positive")


# Default rate limits for different contexts
DEFAULT_LIMITS = {
    # Standard authenticated user limit
    "authenticated": RateLimitConfig(requests=100, window_seconds=60),  # 100 per minute
    # Anonymous/unauthenticated user limit (stricter)
    "anonymous": RateLimitConfig(requests=20, window_seconds=60),       # 20 per minute
    # Chat endpoint specific limit (moderate)
    "chat": RateLimitConfig(requests=30, window_seconds=60),            # 30 per minute
    # Upload endpoint limit (stricter due to resource usage)
    "upload": RateLimitConfig(requests=10, window_seconds=60),          # 10 per minute
    # Health check endpoint (very permissive)
    "health": RateLimitConfig(requests=300, window_seconds=60),         # 300 per minute
    # Streaming chat endpoint
    "chat_stream": RateLimitConfig(requests=20, window_seconds=60),     # 20 per minute
    # Conversations endpoint
    "conversations": RateLimitConfig(requests=60, window_seconds=60),   # 60 per minute
}

# Endpoint to limit type mapping
ENDPOINT_LIMITS = {
    "/chat": "chat",
    "/chat/stream": "chat_stream",
    "/upload/content": "upload",
    "/health": "health",
    "/conversations": "conversations",
}


def get_limit(endpoint: str, authenticated: bool = False) -> RateLimitConfig:
    """
    Get the rate limit configuration for a given endpoint.

    Args:
        endpoint: The API endpoint path
        authenticated: Whether the request is from an authenticated user

    Returns:
        RateLimitConfig for the endpoint/user combination
    """
    # Check if there's a specific limit for this endpoint
    for path_prefix, limit_name in ENDPOINT_LIMITS.items():
        if endpoint.startswith(path_prefix):
            if limit_name in DEFAULT_LIMITS:
                return DEFAULT_LIMITS[limit_name]

    # Fall back to authenticated/anonymous limits
    return DEFAULT_LIMITS["authenticated" if authenticated else "anonymous"]


def get_limit_by_name(name: str) -> Optional[RateLimitConfig]:
    """
    Get a rate limit configuration by its name.

    Args:
        name: The name of the rate limit configuration

    Returns:
        RateLimitConfig if found, None otherwise
    """
    return DEFAULT_LIMITS.get(name)


__all__ = [
    "RateLimitConfig",
    "DEFAULT_LIMITS",
    "ENDPOINT_LIMITS",
    "get_limit",
    "get_limit_by_name",
]
