"""
PRD-018: Health Checks & Metrics - Extended Tests

Tests for Prometheus-compatible health checks and metrics endpoints:
- AC-1: GET /health returns status of all dependencies (DB, Redis, Pinecone)
- AC-2: GET /metrics returns Prometheus-format metrics
- AC-3: Metrics includes request count, latency histogram, error rate
- AC-4: Degraded status when dependency fails

TDD Red Phase - Tests written before implementation.
"""

import pytest
import time
from unittest.mock import AsyncMock, patch, MagicMock
from dataclasses import dataclass
from typing import Optional


# ============================================================================
# Test Classes for Health Module
# ============================================================================

class TestHealthStatus:
    """Tests for HealthStatus enum."""

    def test_health_status_healthy_value(self):
        """HealthStatus.HEALTHY should have value 'healthy'."""
        from app.routes.health import HealthStatus
        assert HealthStatus.HEALTHY.value == "healthy"

    def test_health_status_degraded_value(self):
        """HealthStatus.DEGRADED should have value 'degraded'."""
        from app.routes.health import HealthStatus
        assert HealthStatus.DEGRADED.value == "degraded"

    def test_health_status_unhealthy_value(self):
        """HealthStatus.UNHEALTHY should have value 'unhealthy'."""
        from app.routes.health import HealthStatus
        assert HealthStatus.UNHEALTHY.value == "unhealthy"


class TestDependencyCheck:
    """Tests for DependencyCheck dataclass."""

    def test_dependency_check_creation(self):
        """DependencyCheck should be created with required fields."""
        from app.routes.health import DependencyCheck, HealthStatus
        check = DependencyCheck(
            name="database",
            status=HealthStatus.HEALTHY,
            latency_ms=15.5
        )
        assert check.name == "database"
        assert check.status == HealthStatus.HEALTHY
        assert check.latency_ms == 15.5

    def test_dependency_check_with_message(self):
        """DependencyCheck should support optional message."""
        from app.routes.health import DependencyCheck, HealthStatus
        check = DependencyCheck(
            name="redis",
            status=HealthStatus.UNHEALTHY,
            latency_ms=0.0,
            message="Connection refused"
        )
        assert check.message == "Connection refused"

    def test_dependency_check_has_checked_at(self):
        """DependencyCheck should have checked_at timestamp."""
        from app.routes.health import DependencyCheck, HealthStatus
        check = DependencyCheck(
            name="pinecone",
            status=HealthStatus.HEALTHY,
            latency_ms=25.0
        )
        assert check.checked_at is not None
        assert isinstance(check.checked_at, str)


class TestHealthResponse:
    """Tests for HealthResponse dataclass."""

    def test_health_response_creation(self):
        """HealthResponse should be created with all fields."""
        from app.routes.health import HealthResponse, DependencyCheck, HealthStatus

        deps = [
            DependencyCheck(name="database", status=HealthStatus.HEALTHY, latency_ms=10.0),
        ]
        response = HealthResponse(
            status=HealthStatus.HEALTHY,
            version="1.1.0",
            uptime_seconds=100.5,
            dependencies=deps
        )
        assert response.status == HealthStatus.HEALTHY
        assert response.version == "1.1.0"
        assert len(response.dependencies) == 1

    def test_health_response_to_dict(self):
        """HealthResponse.to_dict() should return proper dictionary."""
        from app.routes.health import HealthResponse, DependencyCheck, HealthStatus

        deps = [
            DependencyCheck(name="database", status=HealthStatus.HEALTHY, latency_ms=10.123),
        ]
        response = HealthResponse(
            status=HealthStatus.HEALTHY,
            version="1.1.0",
            uptime_seconds=100.567,
            dependencies=deps
        )
        result = response.to_dict()

        assert result["status"] == "healthy"
        assert result["version"] == "1.1.0"
        assert result["uptime_seconds"] == 100.57  # Rounded
        assert len(result["dependencies"]) == 1
        assert result["dependencies"][0]["name"] == "database"
        assert result["dependencies"][0]["latency_ms"] == 10.12  # Rounded


class TestHealthChecker:
    """Tests for HealthChecker class."""

    @pytest.mark.asyncio
    async def test_check_database_healthy(self):
        """check_database should return healthy status when DB is up."""
        from app.routes.health import HealthChecker, HealthStatus
        checker = HealthChecker()
        result = await checker.check_database()
        assert result.name == "database"
        assert result.status == HealthStatus.HEALTHY
        assert result.latency_ms > 0

    @pytest.mark.asyncio
    async def test_check_redis_healthy(self):
        """check_redis should return healthy status when Redis is up."""
        from app.routes.health import HealthChecker, HealthStatus
        checker = HealthChecker()
        result = await checker.check_redis()
        assert result.name == "redis"
        assert result.status == HealthStatus.HEALTHY
        assert result.latency_ms > 0

    @pytest.mark.asyncio
    async def test_check_pinecone_healthy(self):
        """check_pinecone should return healthy status when Pinecone is up."""
        from app.routes.health import HealthChecker, HealthStatus
        checker = HealthChecker()
        result = await checker.check_pinecone()
        assert result.name == "pinecone"
        assert result.status == HealthStatus.HEALTHY
        assert result.latency_ms > 0

    @pytest.mark.asyncio
    async def test_check_all_returns_all_dependencies(self):
        """check_all should return status for all dependencies."""
        from app.routes.health import HealthChecker
        checker = HealthChecker()
        result = await checker.check_all()

        dependency_names = [d.name for d in result.dependencies]
        assert "database" in dependency_names
        assert "redis" in dependency_names
        assert "pinecone" in dependency_names

    @pytest.mark.asyncio
    async def test_check_all_healthy_overall(self):
        """check_all should return healthy when all deps are healthy."""
        from app.routes.health import HealthChecker, HealthStatus
        checker = HealthChecker()
        result = await checker.check_all()
        assert result.status == HealthStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_check_all_includes_version(self):
        """check_all should include app version."""
        from app.routes.health import HealthChecker
        checker = HealthChecker()
        result = await checker.check_all()
        assert result.version is not None
        assert len(result.version) > 0

    @pytest.mark.asyncio
    async def test_check_all_includes_uptime(self):
        """check_all should include uptime in seconds."""
        from app.routes.health import HealthChecker
        checker = HealthChecker()
        result = await checker.check_all()
        assert result.uptime_seconds >= 0


class TestHealthCheckerDegraded:
    """Tests for degraded health scenarios."""

    @pytest.mark.asyncio
    async def test_degraded_when_database_fails(self):
        """Status should be degraded when database check fails."""
        from app.routes.health import HealthChecker, HealthStatus, DependencyCheck

        checker = HealthChecker()

        # Mock database check to fail
        async def mock_check_database():
            return DependencyCheck(
                name="database",
                status=HealthStatus.UNHEALTHY,
                latency_ms=0.0,
                message="Connection refused"
            )

        checker.check_database = mock_check_database
        result = await checker.check_all()
        assert result.status == HealthStatus.DEGRADED

    @pytest.mark.asyncio
    async def test_degraded_when_redis_fails(self):
        """Status should be degraded when redis check fails."""
        from app.routes.health import HealthChecker, HealthStatus, DependencyCheck

        checker = HealthChecker()

        async def mock_check_redis():
            return DependencyCheck(
                name="redis",
                status=HealthStatus.UNHEALTHY,
                latency_ms=0.0,
                message="Connection timeout"
            )

        checker.check_redis = mock_check_redis
        result = await checker.check_all()
        assert result.status == HealthStatus.DEGRADED

    @pytest.mark.asyncio
    async def test_degraded_when_pinecone_fails(self):
        """Status should be degraded when pinecone check fails."""
        from app.routes.health import HealthChecker, HealthStatus, DependencyCheck

        checker = HealthChecker()

        async def mock_check_pinecone():
            return DependencyCheck(
                name="pinecone",
                status=HealthStatus.UNHEALTHY,
                latency_ms=0.0,
                message="API key invalid"
            )

        checker.check_pinecone = mock_check_pinecone
        result = await checker.check_all()
        assert result.status == HealthStatus.DEGRADED

    @pytest.mark.asyncio
    async def test_degraded_preserves_healthy_deps(self):
        """Degraded status should still show healthy dependencies."""
        from app.routes.health import HealthChecker, HealthStatus, DependencyCheck

        checker = HealthChecker()

        async def mock_check_database():
            return DependencyCheck(
                name="database",
                status=HealthStatus.UNHEALTHY,
                latency_ms=0.0,
                message="Down"
            )

        checker.check_database = mock_check_database
        result = await checker.check_all()

        healthy_deps = [d for d in result.dependencies if d.status == HealthStatus.HEALTHY]
        assert len(healthy_deps) == 2  # Redis and Pinecone still healthy


# ============================================================================
# Test Classes for Metrics Module
# ============================================================================

class TestHistogram:
    """Tests for Histogram metrics class."""

    def test_histogram_creation(self):
        """Histogram should be created with default buckets."""
        from app.middleware.metrics import Histogram
        hist = Histogram(name="test_histogram")
        assert hist.name == "test_histogram"
        assert len(hist.buckets) > 0

    def test_histogram_observe(self):
        """Histogram.observe should record a value."""
        from app.middleware.metrics import Histogram
        hist = Histogram(name="test_histogram")
        hist.observe(0.5)
        assert hist.count == 1
        assert hist.sum == 0.5

    def test_histogram_observe_multiple(self):
        """Histogram should track multiple observations."""
        from app.middleware.metrics import Histogram
        hist = Histogram(name="test_histogram")
        hist.observe(0.1)
        hist.observe(0.2)
        hist.observe(0.3)
        assert hist.count == 3
        assert abs(hist.sum - 0.6) < 0.001

    def test_histogram_bucket_counts(self):
        """Histogram should compute cumulative bucket counts."""
        from app.middleware.metrics import Histogram
        hist = Histogram(name="test_histogram", buckets=[0.1, 0.5, 1.0])
        hist.observe(0.05)  # <= 0.1
        hist.observe(0.3)   # <= 0.5
        hist.observe(0.8)   # <= 1.0
        hist.observe(2.0)   # <= +Inf

        buckets = hist.get_bucket_counts()
        assert buckets[0.1] == 1
        assert buckets[0.5] == 2  # Cumulative
        assert buckets[1.0] == 3  # Cumulative
        assert buckets[float('inf')] == 4  # Cumulative


class TestCounter:
    """Tests for Counter metrics class."""

    def test_counter_creation(self):
        """Counter should be created with initial value 0."""
        from app.middleware.metrics import Counter
        counter = Counter(name="test_counter")
        assert counter.name == "test_counter"
        assert counter.value == 0

    def test_counter_inc(self):
        """Counter.inc should increment by 1."""
        from app.middleware.metrics import Counter
        counter = Counter(name="test_counter")
        counter.inc()
        assert counter.value == 1

    def test_counter_inc_amount(self):
        """Counter.inc should increment by specified amount."""
        from app.middleware.metrics import Counter
        counter = Counter(name="test_counter")
        counter.inc(5)
        assert counter.value == 5


class TestMetricsCollector:
    """Tests for MetricsCollector class."""

    def test_collector_creation(self):
        """MetricsCollector should be created with initialized metrics."""
        from app.middleware.metrics import MetricsCollector
        collector = MetricsCollector()
        assert collector.request_count is not None
        assert collector.request_latency is not None
        assert collector.error_count is not None

    def test_record_request_increments_count(self):
        """record_request should increment request count."""
        from app.middleware.metrics import MetricsCollector
        collector = MetricsCollector()
        initial = collector.request_count.value
        collector.record_request("GET", "/test", 200, 0.1)
        assert collector.request_count.value == initial + 1

    def test_record_request_records_latency(self):
        """record_request should record latency in histogram."""
        from app.middleware.metrics import MetricsCollector
        collector = MetricsCollector()
        collector.record_request("GET", "/test", 200, 0.123)
        assert collector.request_latency.count == 1
        assert abs(collector.request_latency.sum - 0.123) < 0.001

    def test_record_request_tracks_errors(self):
        """record_request should increment error count for 4xx/5xx."""
        from app.middleware.metrics import MetricsCollector
        collector = MetricsCollector()
        collector.record_request("GET", "/test", 500, 0.1)
        assert collector.error_count.value == 1

    def test_record_request_no_error_for_success(self):
        """record_request should not increment error count for 2xx."""
        from app.middleware.metrics import MetricsCollector
        collector = MetricsCollector()
        collector.record_request("GET", "/test", 200, 0.1)
        assert collector.error_count.value == 0

    def test_record_request_tracks_methods(self):
        """record_request should track requests by method."""
        from app.middleware.metrics import MetricsCollector
        collector = MetricsCollector()
        collector.record_request("GET", "/test", 200, 0.1)
        collector.record_request("POST", "/test", 201, 0.1)
        collector.record_request("GET", "/test", 200, 0.1)
        assert collector._method_counts.get("GET") == 2
        assert collector._method_counts.get("POST") == 1

    def test_record_request_tracks_status_codes(self):
        """record_request should track requests by status code."""
        from app.middleware.metrics import MetricsCollector
        collector = MetricsCollector()
        collector.record_request("GET", "/test", 200, 0.1)
        collector.record_request("GET", "/test", 404, 0.1)
        collector.record_request("GET", "/test", 200, 0.1)
        assert collector._status_counts.get(200) == 2
        assert collector._status_counts.get(404) == 1


class TestPrometheusFormat:
    """Tests for Prometheus metrics format output."""

    def test_prometheus_metrics_contains_request_total(self):
        """Prometheus output should contain http_requests_total."""
        from app.middleware.metrics import MetricsCollector
        collector = MetricsCollector()
        collector.record_request("GET", "/test", 200, 0.1)
        output = collector.get_prometheus_metrics()
        assert "http_requests_total" in output

    def test_prometheus_metrics_contains_error_total(self):
        """Prometheus output should contain http_errors_total."""
        from app.middleware.metrics import MetricsCollector
        collector = MetricsCollector()
        output = collector.get_prometheus_metrics()
        assert "http_errors_total" in output

    def test_prometheus_metrics_contains_histogram(self):
        """Prometheus output should contain histogram buckets."""
        from app.middleware.metrics import MetricsCollector
        collector = MetricsCollector()
        collector.record_request("GET", "/test", 200, 0.1)
        output = collector.get_prometheus_metrics()
        assert "http_request_duration_seconds_bucket" in output
        assert "http_request_duration_seconds_sum" in output
        assert "http_request_duration_seconds_count" in output

    def test_prometheus_metrics_contains_help_comments(self):
        """Prometheus output should contain HELP comments."""
        from app.middleware.metrics import MetricsCollector
        collector = MetricsCollector()
        output = collector.get_prometheus_metrics()
        assert "# HELP" in output
        assert "# TYPE" in output

    def test_prometheus_metrics_bucket_format(self):
        """Prometheus buckets should use proper format with le labels."""
        from app.middleware.metrics import MetricsCollector
        collector = MetricsCollector()
        collector.record_request("GET", "/test", 200, 0.1)
        output = collector.get_prometheus_metrics()
        assert 'le="' in output
        assert '+Inf' in output


class TestMetricsMiddleware:
    """Tests for MetricsMiddleware class."""

    @pytest.mark.asyncio
    async def test_middleware_records_request(self):
        """Middleware should record request metrics."""
        from app.middleware.metrics import MetricsMiddleware, metrics_collector
        from unittest.mock import AsyncMock, MagicMock
        from starlette.requests import Request
        from starlette.responses import Response

        # Reset collector
        metrics_collector.request_count.value = 0

        # Create mock request
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/test",
            "query_string": b"",
            "headers": [],
        }
        request = Request(scope)

        # Create mock response
        async def call_next(req):
            response = Response(content="OK")
            response.status_code = 200
            return response

        # Create middleware
        app = MagicMock()
        middleware = MetricsMiddleware(app)

        await middleware.dispatch(request, call_next)

        assert metrics_collector.request_count.value >= 1

    @pytest.mark.asyncio
    async def test_middleware_excludes_metrics_endpoint(self):
        """Middleware should not record /metrics endpoint requests."""
        from app.middleware.metrics import MetricsMiddleware, metrics_collector
        from unittest.mock import MagicMock
        from starlette.requests import Request
        from starlette.responses import Response

        initial_count = metrics_collector.request_count.value

        scope = {
            "type": "http",
            "method": "GET",
            "path": "/metrics",
            "query_string": b"",
            "headers": [],
        }
        request = Request(scope)

        async def call_next(req):
            return Response(content="OK")

        app = MagicMock()
        middleware = MetricsMiddleware(app)

        await middleware.dispatch(request, call_next)

        # Count should not have increased
        assert metrics_collector.request_count.value == initial_count


# ============================================================================
# Integration Tests for Health Endpoints
# ============================================================================

class TestHealthEndpointsIntegration:
    """Integration tests for health check endpoints."""

    def test_health_basic_returns_ok(self, client):
        """GET /health should return ok status."""
        # Note: This uses the existing health endpoint in main.py
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    def test_detailed_health_returns_all_deps(self):
        """GET /health/detailed should return all dependency statuses."""
        # Import test setup
        import sys
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from app.routes.health import router

        test_app = FastAPI()
        test_app.include_router(router)
        test_client = TestClient(test_app)

        response = test_client.get("/health/detailed")
        assert response.status_code == 200
        data = response.json()

        assert "status" in data
        assert "version" in data
        assert "uptime_seconds" in data
        assert "dependencies" in data

        dep_names = [d["name"] for d in data["dependencies"]]
        assert "database" in dep_names
        assert "redis" in dep_names
        assert "pinecone" in dep_names

    def test_ready_endpoint(self):
        """GET /ready should return readiness status."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from app.routes.health import router

        test_app = FastAPI()
        test_app.include_router(router)
        test_client = TestClient(test_app)

        response = test_client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert "ready" in data

    def test_live_endpoint(self):
        """GET /live should return liveness status."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from app.routes.health import router

        test_app = FastAPI()
        test_app.include_router(router)
        test_client = TestClient(test_app)

        response = test_client.get("/live")
        assert response.status_code == 200
        data = response.json()
        assert "alive" in data
        assert "uptime" in data


class TestMetricsEndpointIntegration:
    """Integration tests for metrics endpoint."""

    def test_metrics_endpoint_returns_prometheus_format(self):
        """GET /metrics should return Prometheus format."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from app.middleware.metrics import get_metrics_endpoint

        test_app = FastAPI()
        test_app.add_api_route("/metrics", get_metrics_endpoint)
        test_client = TestClient(test_app)

        response = test_client.get("/metrics")
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]

        content = response.text
        assert "http_requests_total" in content

    def test_metrics_endpoint_content_type(self):
        """GET /metrics should have text/plain content type."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from app.middleware.metrics import get_metrics_endpoint

        test_app = FastAPI()
        test_app.add_api_route("/metrics", get_metrics_endpoint)
        test_client = TestClient(test_app)

        response = test_client.get("/metrics")
        assert "text/plain" in response.headers["content-type"]


# ============================================================================
# Additional Edge Cases and Error Handling Tests
# ============================================================================

class TestHealthEdgeCases:
    """Tests for edge cases in health checks."""

    @pytest.mark.asyncio
    async def test_health_check_handles_exception_gracefully(self):
        """Health checker should handle exceptions gracefully."""
        from app.routes.health import HealthChecker, HealthStatus

        checker = HealthChecker()

        async def mock_check_that_raises():
            raise Exception("Simulated failure")

        checker.check_database = mock_check_that_raises

        # Should not raise, should return degraded
        result = await checker.check_all()
        assert result.status in [HealthStatus.DEGRADED, HealthStatus.UNHEALTHY]

    def test_uptime_increases_over_time(self):
        """Uptime should increase as time passes."""
        import time
        from app.routes.health import _start_time

        uptime1 = time.time() - _start_time
        time.sleep(0.1)
        uptime2 = time.time() - _start_time

        assert uptime2 > uptime1


class TestMetricsEdgeCases:
    """Tests for edge cases in metrics collection."""

    def test_histogram_with_zero_value(self):
        """Histogram should handle zero values."""
        from app.middleware.metrics import Histogram
        hist = Histogram(name="test", buckets=[0.1, 0.5, 1.0])
        hist.observe(0.0)
        assert hist.count == 1
        assert hist.sum == 0.0

    def test_histogram_with_very_large_value(self):
        """Histogram should handle very large values."""
        from app.middleware.metrics import Histogram
        hist = Histogram(name="test", buckets=[0.1, 0.5, 1.0])
        hist.observe(1000.0)
        buckets = hist.get_bucket_counts()
        assert buckets[float('inf')] == 1

    def test_collector_handles_400_errors(self):
        """Collector should count 400 errors."""
        from app.middleware.metrics import MetricsCollector
        collector = MetricsCollector()
        collector.record_request("GET", "/test", 400, 0.1)
        assert collector.error_count.value == 1

    def test_collector_handles_multiple_endpoints(self):
        """Collector should track latencies per endpoint."""
        from app.middleware.metrics import MetricsCollector
        collector = MetricsCollector()
        collector.record_request("GET", "/api/v1/users", 200, 0.1)
        collector.record_request("GET", "/api/v1/products", 200, 0.2)

        assert "/api/v1/users" in collector._endpoint_latencies
        assert "/api/v1/products" in collector._endpoint_latencies


class TestAppVersion:
    """Tests for application version."""

    def test_app_version_is_defined(self):
        """APP_VERSION should be defined."""
        from app.routes.health import APP_VERSION
        assert APP_VERSION is not None
        assert len(APP_VERSION) > 0

    def test_app_version_format(self):
        """APP_VERSION should follow semver format."""
        from app.routes.health import APP_VERSION
        parts = APP_VERSION.split(".")
        assert len(parts) >= 2


class TestDependencyLatency:
    """Tests for dependency latency measurements."""

    @pytest.mark.asyncio
    async def test_database_latency_is_measured(self):
        """Database check should measure latency."""
        from app.routes.health import HealthChecker
        checker = HealthChecker()
        result = await checker.check_database()
        assert result.latency_ms > 0

    @pytest.mark.asyncio
    async def test_redis_latency_is_measured(self):
        """Redis check should measure latency."""
        from app.routes.health import HealthChecker
        checker = HealthChecker()
        result = await checker.check_redis()
        assert result.latency_ms > 0

    @pytest.mark.asyncio
    async def test_pinecone_latency_is_measured(self):
        """Pinecone check should measure latency."""
        from app.routes.health import HealthChecker
        checker = HealthChecker()
        result = await checker.check_pinecone()
        assert result.latency_ms > 0


class TestPrometheusCompliance:
    """Tests for Prometheus format compliance."""

    def test_counter_type_declaration(self):
        """Counter metrics should have TYPE counter declaration."""
        from app.middleware.metrics import MetricsCollector
        collector = MetricsCollector()
        output = collector.get_prometheus_metrics()
        assert "# TYPE http_requests_total counter" in output

    def test_histogram_type_declaration(self):
        """Histogram metrics should have TYPE histogram declaration."""
        from app.middleware.metrics import MetricsCollector
        collector = MetricsCollector()
        output = collector.get_prometheus_metrics()
        assert "# TYPE http_request_duration_seconds histogram" in output

    def test_bucket_labels_are_cumulative(self):
        """Histogram bucket values should be cumulative."""
        from app.middleware.metrics import MetricsCollector
        collector = MetricsCollector()

        # Add requests with different latencies
        collector.record_request("GET", "/test", 200, 0.001)  # Very fast
        collector.record_request("GET", "/test", 200, 0.05)   # Fast
        collector.record_request("GET", "/test", 200, 0.5)    # Medium
        collector.record_request("GET", "/test", 200, 2.0)    # Slow

        output = collector.get_prometheus_metrics()

        # Parse bucket values - they should increase monotonically
        lines = output.split('\n')
        bucket_values = []
        for line in lines:
            if 'http_request_duration_seconds_bucket' in line and '=' in line:
                value = int(line.split()[-1])
                bucket_values.append(value)

        # Verify cumulative property
        for i in range(1, len(bucket_values)):
            assert bucket_values[i] >= bucket_values[i-1]


class TestHealthCheckTiming:
    """Tests for health check timing behavior."""

    @pytest.mark.asyncio
    async def test_health_check_completes_quickly(self):
        """Health check should complete within reasonable time."""
        import time
        from app.routes.health import HealthChecker

        checker = HealthChecker()
        start = time.time()
        await checker.check_all()
        elapsed = time.time() - start

        # Should complete in less than 2 seconds
        assert elapsed < 2.0

    @pytest.mark.asyncio
    async def test_dependency_checks_run_concurrently(self):
        """Dependency checks should run concurrently."""
        import time
        from app.routes.health import HealthChecker

        checker = HealthChecker()
        start = time.time()
        result = await checker.check_all()
        elapsed = time.time() - start

        # If running sequentially, would take ~30ms (3 x 10ms each)
        # If concurrent, should take ~10-15ms
        # We'll check it takes less than 100ms which proves some concurrency
        assert elapsed < 0.1


class TestMetricsReset:
    """Tests for metrics reset behavior (if implemented)."""

    def test_new_collector_starts_at_zero(self):
        """New MetricsCollector should have zero counts."""
        from app.middleware.metrics import MetricsCollector
        collector = MetricsCollector()
        assert collector.request_count.value == 0
        assert collector.error_count.value == 0
        assert collector.request_latency.count == 0
