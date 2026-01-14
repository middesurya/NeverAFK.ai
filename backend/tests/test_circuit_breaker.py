"""
Comprehensive tests for circuit breaker pattern implementation.
Tests cover:
- Circuit breaker states (CLOSED, OPEN, HALF_OPEN)
- State transitions based on failures and successes
- Configurable thresholds
- Graceful error handling
- Retry-after calculations
- Decorator functionality
- Per-service configurations
- Stats tracking
- Timeout behavior
"""

import pytest
import time
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from dataclasses import dataclass


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def default_config():
    """Create a default circuit breaker configuration."""
    from app.config.resilience import CircuitBreakerConfig
    return CircuitBreakerConfig()


@pytest.fixture
def strict_config():
    """Create a strict circuit breaker configuration with low thresholds."""
    from app.config.resilience import CircuitBreakerConfig
    return CircuitBreakerConfig(failure_threshold=2, success_threshold=1, timeout_seconds=5.0)


@pytest.fixture
def circuit_breaker():
    """Create a fresh circuit breaker for each test."""
    from app.utils.circuit_breaker import CircuitBreaker
    return CircuitBreaker("test_service")


@pytest.fixture
def circuit_breaker_strict(strict_config):
    """Create a circuit breaker with strict configuration."""
    from app.utils.circuit_breaker import CircuitBreaker
    return CircuitBreaker("test_service", config=strict_config)


# =============================================================================
# Test CircuitBreakerConfig
# =============================================================================

class TestCircuitBreakerConfig:
    """Tests for CircuitBreakerConfig dataclass."""

    def test_config_creation_with_defaults(self):
        """Test default configuration values."""
        from app.config.resilience import CircuitBreakerConfig
        config = CircuitBreakerConfig()
        assert config.failure_threshold == 5
        assert config.success_threshold == 3
        assert config.timeout_seconds == 30.0

    def test_config_creation_with_custom_values(self):
        """Test configuration with custom values."""
        from app.config.resilience import CircuitBreakerConfig
        config = CircuitBreakerConfig(
            failure_threshold=10,
            success_threshold=5,
            timeout_seconds=60.0
        )
        assert config.failure_threshold == 10
        assert config.success_threshold == 5
        assert config.timeout_seconds == 60.0

    def test_config_is_dataclass(self):
        """Test that config is a proper dataclass."""
        from app.config.resilience import CircuitBreakerConfig
        config = CircuitBreakerConfig()
        # Dataclasses should have __dataclass_fields__
        assert hasattr(config, '__dataclass_fields__')


class TestServiceConfigs:
    """Tests for per-service configurations."""

    def test_openai_config_exists(self):
        """Test that OpenAI has specific configuration."""
        from app.config.resilience import SERVICE_CONFIGS
        assert "openai" in SERVICE_CONFIGS
        assert SERVICE_CONFIGS["openai"].failure_threshold == 3
        assert SERVICE_CONFIGS["openai"].timeout_seconds == 60

    def test_pinecone_config_exists(self):
        """Test that Pinecone has specific configuration."""
        from app.config.resilience import SERVICE_CONFIGS
        assert "pinecone" in SERVICE_CONFIGS
        assert SERVICE_CONFIGS["pinecone"].failure_threshold == 5
        assert SERVICE_CONFIGS["pinecone"].timeout_seconds == 30

    def test_supabase_config_exists(self):
        """Test that Supabase has specific configuration."""
        from app.config.resilience import SERVICE_CONFIGS
        assert "supabase" in SERVICE_CONFIGS
        assert SERVICE_CONFIGS["supabase"].failure_threshold == 5
        assert SERVICE_CONFIGS["supabase"].timeout_seconds == 30

    def test_default_config_exists(self):
        """Test that default configuration exists."""
        from app.config.resilience import SERVICE_CONFIGS
        assert "default" in SERVICE_CONFIGS

    def test_get_config_returns_service_specific(self):
        """Test get_config returns service-specific config."""
        from app.config.resilience import get_config
        config = get_config("openai")
        assert config.failure_threshold == 3

    def test_get_config_returns_default_for_unknown(self):
        """Test get_config returns default for unknown service."""
        from app.config.resilience import get_config, SERVICE_CONFIGS
        config = get_config("unknown_service")
        assert config == SERVICE_CONFIGS["default"]


# =============================================================================
# Test CircuitState Enum
# =============================================================================

class TestCircuitState:
    """Tests for CircuitState enum."""

    def test_circuit_state_closed(self):
        """Test CLOSED state value."""
        from app.utils.circuit_breaker import CircuitState
        assert CircuitState.CLOSED.value == "closed"

    def test_circuit_state_open(self):
        """Test OPEN state value."""
        from app.utils.circuit_breaker import CircuitState
        assert CircuitState.OPEN.value == "open"

    def test_circuit_state_half_open(self):
        """Test HALF_OPEN state value."""
        from app.utils.circuit_breaker import CircuitState
        assert CircuitState.HALF_OPEN.value == "half_open"

    def test_all_states_defined(self):
        """Test all three states are defined."""
        from app.utils.circuit_breaker import CircuitState
        states = list(CircuitState)
        assert len(states) == 3


# =============================================================================
# Test CircuitStats
# =============================================================================

class TestCircuitStats:
    """Tests for CircuitStats dataclass."""

    def test_stats_default_values(self):
        """Test default stats values."""
        from app.utils.circuit_breaker import CircuitStats
        stats = CircuitStats()
        assert stats.failures == 0
        assert stats.successes == 0
        assert stats.last_failure_time == 0.0
        assert stats.consecutive_successes == 0

    def test_stats_custom_values(self):
        """Test stats with custom values."""
        from app.utils.circuit_breaker import CircuitStats
        stats = CircuitStats(
            failures=5,
            successes=10,
            last_failure_time=1000.0,
            consecutive_successes=3
        )
        assert stats.failures == 5
        assert stats.successes == 10
        assert stats.last_failure_time == 1000.0
        assert stats.consecutive_successes == 3


# =============================================================================
# Test CircuitBreakerError
# =============================================================================

class TestCircuitBreakerError:
    """Tests for CircuitBreakerError exception."""

    def test_error_creation(self):
        """Test error creation with service and retry_after."""
        from app.utils.circuit_breaker import CircuitBreakerError
        error = CircuitBreakerError("openai", 30.0)
        assert error.service == "openai"
        assert error.retry_after == 30.0

    def test_error_message(self):
        """Test error message format."""
        from app.utils.circuit_breaker import CircuitBreakerError
        error = CircuitBreakerError("openai", 30.0)
        assert "openai" in str(error)
        assert "30.0" in str(error)

    def test_error_inheritance(self):
        """Test error inherits from Exception."""
        from app.utils.circuit_breaker import CircuitBreakerError
        error = CircuitBreakerError("test", 10.0)
        assert isinstance(error, Exception)

    def test_error_zero_retry_after(self):
        """Test error with zero retry_after."""
        from app.utils.circuit_breaker import CircuitBreakerError
        error = CircuitBreakerError("test", 0.0)
        assert error.retry_after == 0.0


# =============================================================================
# Test CircuitBreaker - Closed State (AC-1)
# =============================================================================

class TestCircuitBreakerClosedState:
    """Tests for circuit breaker in CLOSED state (AC-1)."""

    def test_initial_state_is_closed(self, circuit_breaker):
        """Test that circuit starts in CLOSED state."""
        from app.utils.circuit_breaker import CircuitState
        assert circuit_breaker.state == CircuitState.CLOSED
        assert circuit_breaker.is_closed is True

    def test_closed_allows_requests(self, circuit_breaker):
        """Test that CLOSED state allows requests."""
        assert circuit_breaker.allow_request() is True

    def test_closed_state_properties(self, circuit_breaker):
        """Test state properties when closed."""
        assert circuit_breaker.is_closed is True
        assert circuit_breaker.is_open is False
        assert circuit_breaker.is_half_open is False

    def test_success_in_closed_state(self, circuit_breaker):
        """Test recording success in CLOSED state resets failures."""
        from app.utils.circuit_breaker import CircuitState
        circuit_breaker._stats.failures = 2
        circuit_breaker.record_success()
        assert circuit_breaker._stats.failures == 0
        assert circuit_breaker.state == CircuitState.CLOSED

    def test_single_failure_keeps_closed(self, circuit_breaker):
        """Test single failure keeps circuit closed."""
        from app.utils.circuit_breaker import CircuitState
        circuit_breaker.record_failure()
        assert circuit_breaker.state == CircuitState.CLOSED

    def test_failures_below_threshold_keeps_closed(self, circuit_breaker):
        """Test failures below threshold keep circuit closed."""
        from app.utils.circuit_breaker import CircuitState
        for _ in range(circuit_breaker.config.failure_threshold - 1):
            circuit_breaker.record_failure()
        assert circuit_breaker.state == CircuitState.CLOSED


# =============================================================================
# Test CircuitBreaker - Opens After Failures (AC-2)
# =============================================================================

class TestCircuitBreakerOpens:
    """Tests for circuit breaker opening after failures (AC-2)."""

    def test_opens_after_failure_threshold(self, circuit_breaker_strict):
        """Test circuit opens after reaching failure threshold."""
        from app.utils.circuit_breaker import CircuitState
        # strict_config has failure_threshold=2
        circuit_breaker_strict.record_failure()
        assert circuit_breaker_strict.state == CircuitState.CLOSED

        circuit_breaker_strict.record_failure()
        assert circuit_breaker_strict.state == CircuitState.OPEN

    def test_open_rejects_requests(self, circuit_breaker_strict):
        """Test that OPEN state rejects requests."""
        # Open the circuit
        for _ in range(2):
            circuit_breaker_strict.record_failure()

        assert circuit_breaker_strict.allow_request() is False

    def test_open_state_properties(self, circuit_breaker_strict):
        """Test state properties when open."""
        for _ in range(2):
            circuit_breaker_strict.record_failure()

        assert circuit_breaker_strict.is_closed is False
        assert circuit_breaker_strict.is_open is True
        assert circuit_breaker_strict.is_half_open is False

    def test_failures_tracked_correctly(self, circuit_breaker_strict):
        """Test that failure count is tracked correctly."""
        circuit_breaker_strict.record_failure()
        assert circuit_breaker_strict._stats.failures == 1

        circuit_breaker_strict.record_failure()
        assert circuit_breaker_strict._stats.failures == 2

    def test_last_failure_time_recorded(self, circuit_breaker_strict):
        """Test that last failure time is recorded."""
        before = time.time()
        circuit_breaker_strict.record_failure()
        after = time.time()

        assert circuit_breaker_strict._stats.last_failure_time >= before
        assert circuit_breaker_strict._stats.last_failure_time <= after

    def test_default_config_failure_threshold(self, circuit_breaker):
        """Test default config requires 5 failures to open."""
        from app.utils.circuit_breaker import CircuitState
        for _ in range(4):
            circuit_breaker.record_failure()
        assert circuit_breaker.state == CircuitState.CLOSED

        circuit_breaker.record_failure()
        assert circuit_breaker.state == CircuitState.OPEN


# =============================================================================
# Test CircuitBreaker - Half-Open State (AC-3)
# =============================================================================

class TestCircuitBreakerHalfOpen:
    """Tests for circuit breaker HALF_OPEN state (AC-3)."""

    def test_transitions_to_half_open_after_timeout(self, circuit_breaker_strict):
        """Test circuit transitions to HALF_OPEN after timeout."""
        from app.utils.circuit_breaker import CircuitState
        # Open the circuit
        for _ in range(2):
            circuit_breaker_strict.record_failure()
        assert circuit_breaker_strict._state == CircuitState.OPEN

        # Simulate timeout passing
        circuit_breaker_strict._stats.last_failure_time = time.time() - 10

        # Access state property should trigger transition
        assert circuit_breaker_strict.state == CircuitState.HALF_OPEN

    def test_half_open_allows_test_request(self, circuit_breaker_strict):
        """Test HALF_OPEN state allows test requests."""
        from app.utils.circuit_breaker import CircuitState
        # Open and transition to half-open
        for _ in range(2):
            circuit_breaker_strict.record_failure()
        circuit_breaker_strict._stats.last_failure_time = time.time() - 10

        # Should allow request
        assert circuit_breaker_strict.state == CircuitState.HALF_OPEN
        assert circuit_breaker_strict.allow_request() is True

    def test_half_open_state_properties(self, circuit_breaker_strict):
        """Test state properties when half-open."""
        for _ in range(2):
            circuit_breaker_strict.record_failure()
        circuit_breaker_strict._stats.last_failure_time = time.time() - 10

        # Trigger transition
        _ = circuit_breaker_strict.state

        assert circuit_breaker_strict.is_closed is False
        assert circuit_breaker_strict.is_open is False
        assert circuit_breaker_strict.is_half_open is True

    def test_success_in_half_open_closes_circuit(self, circuit_breaker_strict):
        """Test success in HALF_OPEN closes circuit (success_threshold=1)."""
        from app.utils.circuit_breaker import CircuitState
        # Open and transition to half-open
        for _ in range(2):
            circuit_breaker_strict.record_failure()
        circuit_breaker_strict._stats.last_failure_time = time.time() - 10
        circuit_breaker_strict._state = CircuitState.HALF_OPEN

        # Record success
        circuit_breaker_strict.record_success()

        assert circuit_breaker_strict.state == CircuitState.CLOSED

    def test_failure_in_half_open_reopens_circuit(self, circuit_breaker_strict):
        """Test failure in HALF_OPEN reopens circuit."""
        from app.utils.circuit_breaker import CircuitState
        # Open and transition to half-open
        for _ in range(2):
            circuit_breaker_strict.record_failure()
        circuit_breaker_strict._stats.last_failure_time = time.time() - 10
        circuit_breaker_strict._state = CircuitState.HALF_OPEN

        # Record failure
        circuit_breaker_strict.record_failure()

        assert circuit_breaker_strict._state == CircuitState.OPEN

    def test_multiple_successes_needed_to_close(self, default_config):
        """Test that multiple successes may be needed to close."""
        from app.utils.circuit_breaker import CircuitBreaker, CircuitState
        # Use config that requires 3 successes
        breaker = CircuitBreaker("test", config=default_config)

        # Open and transition to half-open
        for _ in range(5):
            breaker.record_failure()
        breaker._stats.last_failure_time = time.time() - 60
        breaker._state = CircuitState.HALF_OPEN

        # First success
        breaker.record_success()
        assert breaker._state == CircuitState.HALF_OPEN

        # Second success
        breaker.record_success()
        assert breaker._state == CircuitState.HALF_OPEN

        # Third success - should close
        breaker.record_success()
        assert breaker._state == CircuitState.CLOSED


# =============================================================================
# Test CircuitBreaker - Graceful Error (AC-4)
# =============================================================================

class TestCircuitBreakerGracefulError:
    """Tests for graceful error handling when circuit is open (AC-4)."""

    def test_error_includes_service_name(self, circuit_breaker_strict):
        """Test that error includes service name."""
        from app.utils.circuit_breaker import CircuitBreakerError
        for _ in range(2):
            circuit_breaker_strict.record_failure()

        try:
            if not circuit_breaker_strict.allow_request():
                raise CircuitBreakerError(
                    circuit_breaker_strict.service,
                    circuit_breaker_strict.get_retry_after()
                )
        except CircuitBreakerError as e:
            assert e.service == "test_service"

    def test_error_includes_retry_after(self, circuit_breaker_strict):
        """Test that error includes retry_after value."""
        from app.utils.circuit_breaker import CircuitBreakerError
        for _ in range(2):
            circuit_breaker_strict.record_failure()

        retry_after = circuit_breaker_strict.get_retry_after()
        error = CircuitBreakerError(circuit_breaker_strict.service, retry_after)
        assert error.retry_after > 0
        assert error.retry_after <= circuit_breaker_strict.config.timeout_seconds

    def test_graceful_error_message_format(self, circuit_breaker_strict):
        """Test graceful error message format."""
        from app.utils.circuit_breaker import CircuitBreakerError
        error = CircuitBreakerError("openai", 25.5)
        msg = str(error)
        assert "Circuit breaker open" in msg
        assert "openai" in msg
        assert "Retry after" in msg


# =============================================================================
# Test Retry-After Calculation
# =============================================================================

class TestRetryAfterCalculation:
    """Tests for retry_after calculation."""

    def test_retry_after_when_just_opened(self, circuit_breaker_strict):
        """Test retry_after equals timeout when just opened."""
        for _ in range(2):
            circuit_breaker_strict.record_failure()

        retry_after = circuit_breaker_strict.get_retry_after()
        # Should be close to timeout_seconds (5.0)
        assert retry_after > 4.5
        assert retry_after <= 5.0

    def test_retry_after_decreases_over_time(self, circuit_breaker_strict):
        """Test retry_after decreases as time passes."""
        for _ in range(2):
            circuit_breaker_strict.record_failure()

        # Simulate 3 seconds passing
        circuit_breaker_strict._stats.last_failure_time = time.time() - 3

        retry_after = circuit_breaker_strict.get_retry_after()
        # Should be close to 2 seconds (5 - 3)
        assert retry_after > 1.5
        assert retry_after <= 2.0

    def test_retry_after_zero_when_closed(self, circuit_breaker):
        """Test retry_after is zero when circuit is closed."""
        assert circuit_breaker.get_retry_after() == 0.0

    def test_retry_after_zero_after_timeout(self, circuit_breaker_strict):
        """Test retry_after is zero after timeout expires."""
        for _ in range(2):
            circuit_breaker_strict.record_failure()

        # Simulate timeout passing
        circuit_breaker_strict._stats.last_failure_time = time.time() - 10

        retry_after = circuit_breaker_strict.get_retry_after()
        assert retry_after == 0.0


# =============================================================================
# Test Circuit Reset
# =============================================================================

class TestCircuitReset:
    """Tests for circuit breaker reset functionality."""

    def test_reset_clears_state(self, circuit_breaker_strict):
        """Test reset returns circuit to closed state."""
        from app.utils.circuit_breaker import CircuitState
        for _ in range(2):
            circuit_breaker_strict.record_failure()
        assert circuit_breaker_strict._state == CircuitState.OPEN

        circuit_breaker_strict.reset()
        assert circuit_breaker_strict._state == CircuitState.CLOSED

    def test_reset_clears_stats(self, circuit_breaker_strict):
        """Test reset clears all stats."""
        for _ in range(2):
            circuit_breaker_strict.record_failure()

        circuit_breaker_strict.reset()
        assert circuit_breaker_strict._stats.failures == 0
        assert circuit_breaker_strict._stats.successes == 0
        assert circuit_breaker_strict._stats.last_failure_time == 0.0
        assert circuit_breaker_strict._stats.consecutive_successes == 0


# =============================================================================
# Test Execute Method
# =============================================================================

class TestCircuitBreakerExecute:
    """Tests for circuit breaker execute method."""

    @pytest.mark.asyncio
    async def test_execute_success(self, circuit_breaker):
        """Test execute with successful function."""
        async def success_func():
            return "success"

        result = await circuit_breaker.execute(success_func)
        assert result == "success"

    @pytest.mark.asyncio
    async def test_execute_records_success(self, circuit_breaker):
        """Test execute records success on successful call."""
        async def success_func():
            return "success"

        await circuit_breaker.execute(success_func)
        # Failure count should remain 0
        assert circuit_breaker._stats.failures == 0

    @pytest.mark.asyncio
    async def test_execute_failure_records_failure(self, circuit_breaker):
        """Test execute records failure on exception."""
        async def failing_func():
            raise ValueError("test error")

        with pytest.raises(ValueError):
            await circuit_breaker.execute(failing_func)

        assert circuit_breaker._stats.failures == 1

    @pytest.mark.asyncio
    async def test_execute_raises_circuit_breaker_error_when_open(self, circuit_breaker_strict):
        """Test execute raises CircuitBreakerError when circuit is open."""
        from app.utils.circuit_breaker import CircuitBreakerError
        # Open the circuit
        for _ in range(2):
            circuit_breaker_strict.record_failure()

        async def success_func():
            return "success"

        with pytest.raises(CircuitBreakerError):
            await circuit_breaker_strict.execute(success_func)

    @pytest.mark.asyncio
    async def test_execute_with_args(self, circuit_breaker):
        """Test execute passes args to function."""
        async def func_with_args(a, b):
            return a + b

        result = await circuit_breaker.execute(func_with_args, 1, 2)
        assert result == 3

    @pytest.mark.asyncio
    async def test_execute_with_kwargs(self, circuit_breaker):
        """Test execute passes kwargs to function."""
        async def func_with_kwargs(a, b=10):
            return a + b

        result = await circuit_breaker.execute(func_with_kwargs, 5, b=20)
        assert result == 25


# =============================================================================
# Test Decorator
# =============================================================================

class TestCircuitBreakerDecorator:
    """Tests for circuit_breaker decorator."""

    def test_decorator_creates_breaker(self):
        """Test decorator creates circuit breaker for function."""
        from app.utils.circuit_breaker import circuit_breaker as cb_decorator

        @cb_decorator("test_service")
        async def test_func():
            return "result"

        assert hasattr(test_func, 'circuit_breaker')

    def test_decorator_uses_service_name(self):
        """Test decorator uses provided service name."""
        from app.utils.circuit_breaker import circuit_breaker as cb_decorator

        @cb_decorator("custom_service")
        async def test_func():
            return "result"

        assert test_func.circuit_breaker.service == "custom_service"

    @pytest.mark.asyncio
    async def test_decorator_executes_function(self):
        """Test decorated function executes normally."""
        from app.utils.circuit_breaker import circuit_breaker as cb_decorator

        @cb_decorator("test_service")
        async def test_func():
            return "result"

        result = await test_func()
        assert result == "result"

    @pytest.mark.asyncio
    async def test_decorator_tracks_failures(self):
        """Test decorator tracks failures."""
        from app.utils.circuit_breaker import circuit_breaker as cb_decorator

        @cb_decorator("test_service")
        async def failing_func():
            raise ValueError("error")

        with pytest.raises(ValueError):
            await failing_func()

        assert failing_func.circuit_breaker._stats.failures == 1

    @pytest.mark.asyncio
    async def test_decorator_opens_circuit_after_threshold(self):
        """Test decorator opens circuit after failure threshold."""
        from app.utils.circuit_breaker import circuit_breaker as cb_decorator, CircuitState, CircuitBreakerConfig

        config = CircuitBreakerConfig(failure_threshold=2, success_threshold=1, timeout_seconds=5.0)

        @cb_decorator("test_service")
        async def failing_func():
            raise ValueError("error")

        # Override config
        failing_func.circuit_breaker.config = config

        # Cause failures
        for _ in range(2):
            with pytest.raises(ValueError):
                await failing_func()

        assert failing_func.circuit_breaker._state == CircuitState.OPEN


# =============================================================================
# Test Breaker Registry
# =============================================================================

class TestBreakerRegistry:
    """Tests for circuit breaker registry."""

    def test_get_breaker_creates_new(self):
        """Test get_breaker creates new breaker for unknown service."""
        from app.utils.circuit_breaker import get_breaker, _breakers

        # Clear registry
        _breakers.clear()

        breaker = get_breaker("new_service")
        assert breaker.service == "new_service"

    def test_get_breaker_returns_existing(self):
        """Test get_breaker returns existing breaker for known service."""
        from app.utils.circuit_breaker import get_breaker, _breakers

        # Clear registry
        _breakers.clear()

        breaker1 = get_breaker("existing_service")
        breaker2 = get_breaker("existing_service")

        assert breaker1 is breaker2

    def test_different_services_different_breakers(self):
        """Test different services get different breakers."""
        from app.utils.circuit_breaker import get_breaker, _breakers

        # Clear registry
        _breakers.clear()

        breaker1 = get_breaker("service1")
        breaker2 = get_breaker("service2")

        assert breaker1 is not breaker2
        assert breaker1.service == "service1"
        assert breaker2.service == "service2"


# =============================================================================
# Test Service-Specific Configurations
# =============================================================================

class TestServiceSpecificConfigs:
    """Tests for service-specific configurations."""

    def test_openai_breaker_uses_openai_config(self):
        """Test OpenAI service uses OpenAI-specific config."""
        from app.utils.circuit_breaker import CircuitBreaker
        breaker = CircuitBreaker("openai")
        assert breaker.config.failure_threshold == 3
        assert breaker.config.timeout_seconds == 60

    def test_pinecone_breaker_uses_pinecone_config(self):
        """Test Pinecone service uses Pinecone-specific config."""
        from app.utils.circuit_breaker import CircuitBreaker
        breaker = CircuitBreaker("pinecone")
        assert breaker.config.failure_threshold == 5
        assert breaker.config.timeout_seconds == 30

    def test_unknown_service_uses_default_config(self):
        """Test unknown service uses default config."""
        from app.utils.circuit_breaker import CircuitBreaker
        from app.config.resilience import SERVICE_CONFIGS
        breaker = CircuitBreaker("unknown_service")
        assert breaker.config == SERVICE_CONFIGS["default"]


# =============================================================================
# Test Logging
# =============================================================================

class TestCircuitBreakerLogging:
    """Tests for circuit breaker logging."""

    def test_logs_circuit_open(self, circuit_breaker_strict, caplog):
        """Test logging when circuit opens."""
        import logging
        caplog.set_level(logging.WARNING)

        for _ in range(2):
            circuit_breaker_strict.record_failure()

        assert any("OPENED" in record.message for record in caplog.records)

    def test_logs_circuit_close(self, circuit_breaker_strict, caplog):
        """Test logging when circuit closes."""
        import logging
        from app.utils.circuit_breaker import CircuitState
        caplog.set_level(logging.INFO)

        # Open circuit
        for _ in range(2):
            circuit_breaker_strict.record_failure()

        # Transition to half-open
        circuit_breaker_strict._stats.last_failure_time = time.time() - 10
        circuit_breaker_strict._state = CircuitState.HALF_OPEN

        # Close circuit
        circuit_breaker_strict.record_success()

        assert any("CLOSED" in record.message for record in caplog.records)

    def test_logs_transition_to_half_open(self, circuit_breaker_strict, caplog):
        """Test logging when transitioning to half-open."""
        import logging
        caplog.set_level(logging.INFO)

        # Open circuit
        for _ in range(2):
            circuit_breaker_strict.record_failure()

        # Simulate timeout
        circuit_breaker_strict._stats.last_failure_time = time.time() - 10

        # Access state to trigger transition
        _ = circuit_breaker_strict.state

        assert any("HALF_OPEN" in record.message for record in caplog.records)


# =============================================================================
# Test Edge Cases
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_consecutive_successes_reset_on_failure(self, circuit_breaker_strict):
        """Test consecutive successes reset on failure."""
        from app.utils.circuit_breaker import CircuitState
        # Open and transition to half-open
        for _ in range(2):
            circuit_breaker_strict.record_failure()
        circuit_breaker_strict._stats.last_failure_time = time.time() - 10
        circuit_breaker_strict._state = CircuitState.HALF_OPEN

        # Record some successes
        circuit_breaker_strict._stats.consecutive_successes = 2

        # Record failure
        circuit_breaker_strict.record_failure()

        assert circuit_breaker_strict._stats.consecutive_successes == 0

    def test_failure_time_updated_on_each_failure(self, circuit_breaker):
        """Test last_failure_time is updated on each failure."""
        circuit_breaker.record_failure()
        first_time = circuit_breaker._stats.last_failure_time

        time.sleep(0.01)

        circuit_breaker.record_failure()
        second_time = circuit_breaker._stats.last_failure_time

        assert second_time > first_time

    def test_circuit_stays_closed_after_partial_failures_and_success(self, circuit_breaker_strict):
        """Test circuit stays closed if success occurs before threshold."""
        from app.utils.circuit_breaker import CircuitState
        circuit_breaker_strict.record_failure()
        circuit_breaker_strict.record_success()

        assert circuit_breaker_strict.state == CircuitState.CLOSED
        assert circuit_breaker_strict._stats.failures == 0

    def test_very_long_timeout(self):
        """Test circuit with very long timeout."""
        from app.utils.circuit_breaker import CircuitBreaker, CircuitBreakerConfig
        config = CircuitBreakerConfig(failure_threshold=1, timeout_seconds=3600.0)
        breaker = CircuitBreaker("test", config=config)

        breaker.record_failure()

        # Should be open and have long retry_after
        assert breaker.is_open
        assert breaker.get_retry_after() > 3500


# =============================================================================
# Test Concurrent Access
# =============================================================================

class TestConcurrentAccess:
    """Tests for concurrent access scenarios."""

    @pytest.mark.asyncio
    async def test_concurrent_failures(self, circuit_breaker_strict):
        """Test concurrent failure recording."""
        from app.utils.circuit_breaker import CircuitState

        async def record_failure():
            circuit_breaker_strict.record_failure()

        # Record failures concurrently
        await asyncio.gather(*[record_failure() for _ in range(5)])

        # Should be open
        assert circuit_breaker_strict._state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_concurrent_execute_calls(self, circuit_breaker):
        """Test concurrent execute calls."""
        async def success_func(value):
            await asyncio.sleep(0.01)
            return value

        results = await asyncio.gather(*[
            circuit_breaker.execute(success_func, i)
            for i in range(5)
        ])

        assert results == [0, 1, 2, 3, 4]


# =============================================================================
# Test Integration Scenarios
# =============================================================================

class TestIntegrationScenarios:
    """Integration tests for realistic scenarios."""

    @pytest.mark.asyncio
    async def test_full_circuit_lifecycle(self):
        """Test complete circuit lifecycle: closed -> open -> half-open -> closed."""
        from app.utils.circuit_breaker import CircuitBreaker, CircuitBreakerConfig, CircuitState

        config = CircuitBreakerConfig(failure_threshold=2, success_threshold=1, timeout_seconds=0.1)
        breaker = CircuitBreaker("test", config=config)

        # 1. Start closed
        assert breaker.state == CircuitState.CLOSED

        # 2. Failures open circuit
        for _ in range(2):
            breaker.record_failure()
        assert breaker._state == CircuitState.OPEN

        # 3. Wait for timeout, transitions to half-open
        await asyncio.sleep(0.15)
        assert breaker.state == CircuitState.HALF_OPEN

        # 4. Success closes circuit
        breaker.record_success()
        assert breaker.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_api_simulation_with_failing_service(self):
        """Test simulating API calls to a failing service."""
        from app.utils.circuit_breaker import CircuitBreaker, CircuitBreakerConfig, CircuitBreakerError

        config = CircuitBreakerConfig(failure_threshold=3, success_threshold=2, timeout_seconds=1.0)
        breaker = CircuitBreaker("api", config=config)

        call_count = 0

        async def failing_api_call():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("API unavailable")

        # First 3 calls should fail but reach the API
        for _ in range(3):
            with pytest.raises(ConnectionError):
                await breaker.execute(failing_api_call)

        assert call_count == 3
        assert breaker.is_open

        # Next call should fail fast without reaching API
        with pytest.raises(CircuitBreakerError):
            await breaker.execute(failing_api_call)

        # Call count should not have increased
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_recovery_after_transient_failure(self):
        """Test recovery after transient failures."""
        from app.utils.circuit_breaker import CircuitBreaker, CircuitBreakerConfig, CircuitState

        config = CircuitBreakerConfig(failure_threshold=3, success_threshold=2, timeout_seconds=0.1)
        breaker = CircuitBreaker("test", config=config)

        # Some failures but not enough to open
        breaker.record_failure()
        breaker.record_failure()
        assert breaker.state == CircuitState.CLOSED

        # Service recovers
        breaker.record_success()

        # Failures should be reset
        assert breaker._stats.failures == 0
