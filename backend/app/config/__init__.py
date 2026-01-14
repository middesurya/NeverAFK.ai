"""
Configuration module for the backend application.
"""

from .models import ModelProvider, MODEL_CONFIG, DEFAULT_MODEL_ORDER
from .rate_limits import (
    RateLimitConfig,
    DEFAULT_LIMITS,
    ENDPOINT_LIMITS,
    get_limit,
    get_limit_by_name,
)
from .resilience import (
    CircuitBreakerConfig,
    SERVICE_CONFIGS,
    get_config,
)

__all__ = [
    "ModelProvider",
    "MODEL_CONFIG",
    "DEFAULT_MODEL_ORDER",
    "RateLimitConfig",
    "DEFAULT_LIMITS",
    "ENDPOINT_LIMITS",
    "get_limit",
    "get_limit_by_name",
    "CircuitBreakerConfig",
    "SERVICE_CONFIGS",
    "get_config",
]
