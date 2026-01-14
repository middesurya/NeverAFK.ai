"""
Resilience configuration for the API.
Defines circuit breaker configurations for different external services.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class CircuitBreakerConfig:
    """Configuration for a circuit breaker."""
    failure_threshold: int = 5      # Failures before opening
    success_threshold: int = 3      # Successes to close from half-open
    timeout_seconds: float = 30.0   # Time before trying half-open


# Per-service configurations
SERVICE_CONFIGS = {
    "openai": CircuitBreakerConfig(failure_threshold=3, timeout_seconds=60),
    "pinecone": CircuitBreakerConfig(failure_threshold=5, timeout_seconds=30),
    "supabase": CircuitBreakerConfig(failure_threshold=5, timeout_seconds=30),
    "default": CircuitBreakerConfig(),
}


def get_config(service: str) -> CircuitBreakerConfig:
    """
    Get the circuit breaker configuration for a given service.

    Args:
        service: The name of the external service

    Returns:
        CircuitBreakerConfig for the service
    """
    return SERVICE_CONFIGS.get(service, SERVICE_CONFIGS["default"])


__all__ = [
    "CircuitBreakerConfig",
    "SERVICE_CONFIGS",
    "get_config",
]
