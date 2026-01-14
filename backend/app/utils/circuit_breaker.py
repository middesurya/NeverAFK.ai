"""
Circuit breaker implementation for graceful degradation when external APIs fail.
Provides three states: CLOSED (normal), OPEN (failing fast), HALF_OPEN (testing recovery).
"""

import time
import logging
from enum import Enum
from typing import Callable, Optional, Any
from dataclasses import dataclass, field
from functools import wraps

from app.config.resilience import CircuitBreakerConfig, get_config

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Possible states for a circuit breaker."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing fast
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitStats:
    """Statistics for a circuit breaker."""
    failures: int = 0
    successes: int = 0
    last_failure_time: float = 0.0
    consecutive_successes: int = 0


class CircuitBreakerError(Exception):
    """Raised when circuit is open."""
    def __init__(self, service: str, retry_after: float):
        self.service = service
        self.retry_after = retry_after
        super().__init__(f"Circuit breaker open for {service}. Retry after {retry_after:.1f}s")


class CircuitBreaker:
    """Circuit breaker implementation with three states."""

    def __init__(self, service: str, config: CircuitBreakerConfig = None):
        """
        Initialize a circuit breaker.

        Args:
            service: Name of the service this breaker protects
            config: Configuration for the circuit breaker
        """
        self.service = service
        self.config = config or get_config(service)
        self._state = CircuitState.CLOSED
        self._stats = CircuitStats()

    @property
    def state(self) -> CircuitState:
        """
        Get the current state of the circuit breaker.
        Checks if we should transition from OPEN to HALF_OPEN.
        """
        # Check if we should transition to half-open
        if self._state == CircuitState.OPEN:
            if time.time() - self._stats.last_failure_time >= self.config.timeout_seconds:
                self._state = CircuitState.HALF_OPEN
                logger.info(f"Circuit {self.service} transitioning to HALF_OPEN")
        return self._state

    @property
    def is_closed(self) -> bool:
        """Check if the circuit is closed (normal operation)."""
        return self.state == CircuitState.CLOSED

    @property
    def is_open(self) -> bool:
        """Check if the circuit is open (failing fast)."""
        return self.state == CircuitState.OPEN

    @property
    def is_half_open(self) -> bool:
        """Check if the circuit is half-open (testing recovery)."""
        return self.state == CircuitState.HALF_OPEN

    def allow_request(self) -> bool:
        """Check if request should be allowed through the circuit."""
        return self.state != CircuitState.OPEN

    def record_success(self):
        """Record a successful call through the circuit."""
        if self._state == CircuitState.HALF_OPEN:
            self._stats.consecutive_successes += 1
            if self._stats.consecutive_successes >= self.config.success_threshold:
                self._close()
        elif self._state == CircuitState.CLOSED:
            self._stats.failures = 0

    def record_failure(self):
        """Record a failed call through the circuit."""
        self._stats.failures += 1
        self._stats.last_failure_time = time.time()
        self._stats.consecutive_successes = 0

        if self._state == CircuitState.HALF_OPEN:
            self._open()
        elif self._state == CircuitState.CLOSED:
            if self._stats.failures >= self.config.failure_threshold:
                self._open()

    def _open(self):
        """Open the circuit (start failing fast)."""
        self._state = CircuitState.OPEN
        logger.warning(f"Circuit {self.service} OPENED after {self._stats.failures} failures")

    def _close(self):
        """Close the circuit (return to normal operation)."""
        self._state = CircuitState.CLOSED
        self._stats = CircuitStats()
        logger.info(f"Circuit {self.service} CLOSED after recovery")

    def reset(self):
        """Reset the circuit to closed state."""
        self._state = CircuitState.CLOSED
        self._stats = CircuitStats()

    def get_retry_after(self) -> float:
        """Get time until retry should be attempted."""
        if self._state != CircuitState.OPEN:
            return 0.0
        elapsed = time.time() - self._stats.last_failure_time
        return max(0.0, self.config.timeout_seconds - elapsed)

    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.

        Args:
            func: Async function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            Result of the function call

        Raises:
            CircuitBreakerError: If the circuit is open
            Exception: If the function raises an exception
        """
        if not self.allow_request():
            raise CircuitBreakerError(self.service, self.get_retry_after())

        try:
            result = await func(*args, **kwargs)
            self.record_success()
            return result
        except Exception as e:
            self.record_failure()
            raise


def circuit_breaker(service: str):
    """
    Decorator to add circuit breaker to async functions.

    Args:
        service: Name of the service this function calls

    Returns:
        Decorator function
    """
    breaker = CircuitBreaker(service)

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await breaker.execute(func, *args, **kwargs)
        wrapper.circuit_breaker = breaker
        return wrapper
    return decorator


# Registry of circuit breakers
_breakers: dict[str, CircuitBreaker] = {}


def get_breaker(service: str) -> CircuitBreaker:
    """
    Get or create circuit breaker for service.

    Args:
        service: Name of the service

    Returns:
        CircuitBreaker instance for the service
    """
    if service not in _breakers:
        _breakers[service] = CircuitBreaker(service)
    return _breakers[service]


__all__ = [
    "CircuitState",
    "CircuitStats",
    "CircuitBreakerError",
    "CircuitBreaker",
    "circuit_breaker",
    "get_breaker",
]
