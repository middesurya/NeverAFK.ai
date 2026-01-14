"""
Prometheus metrics middleware for request monitoring.

Provides:
- Request count tracking
- Latency histogram with Prometheus-compatible buckets
- Error rate monitoring
- Per-method and per-status tracking

AC-2: GET /metrics returns Prometheus-format metrics
AC-3: Metrics includes request count, latency histogram, error rate
"""

import time
from dataclasses import dataclass, field
from typing import Optional, Dict, List
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, PlainTextResponse


@dataclass
class Histogram:
    """
    Prometheus-compatible histogram for tracking distributions.

    Uses configurable buckets for latency measurements.
    Provides cumulative bucket counts as required by Prometheus format.
    """
    name: str
    buckets: List[float] = field(
        default_factory=lambda: [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10]
    )
    values: List[float] = field(default_factory=list)
    sum: float = 0.0
    count: int = 0

    def observe(self, value: float):
        """
        Record an observation in the histogram.

        Args:
            value: The value to record (e.g., request duration in seconds)
        """
        self.values.append(value)
        self.sum += value
        self.count += 1

    def get_bucket_counts(self) -> Dict[float, int]:
        """
        Get cumulative bucket counts for Prometheus format.

        Returns:
            Dictionary mapping bucket boundaries to cumulative counts
        """
        bucket_counts = {b: 0 for b in self.buckets}
        bucket_counts[float('inf')] = 0

        for v in self.values:
            for b in sorted(self.buckets) + [float('inf')]:
                if v <= b:
                    bucket_counts[b] += 1
                    break

        # Make cumulative
        cumulative = {}
        total = 0
        for b in sorted(self.buckets) + [float('inf')]:
            total += bucket_counts[b]
            cumulative[b] = total

        return cumulative


@dataclass
class Counter:
    """
    Prometheus-compatible counter metric.

    Counters can only increase or be reset to zero.
    """
    name: str
    value: int = 0
    labels: dict = field(default_factory=dict)

    def inc(self, amount: int = 1):
        """
        Increment the counter.

        Args:
            amount: Value to add to the counter (default: 1)
        """
        self.value += amount


class MetricsCollector:
    """
    Collects and aggregates metrics for the application.

    Provides Prometheus-compatible output format.
    """

    def __init__(self):
        self.request_count = Counter("http_requests_total")
        self.request_latency = Histogram("http_request_duration_seconds")
        self.error_count = Counter("http_errors_total")
        self._method_counts: Dict[str, int] = {}
        self._status_counts: Dict[int, int] = {}
        self._endpoint_latencies: Dict[str, List[float]] = {}

    def record_request(self, method: str, path: str, status: int, duration: float):
        """
        Record metrics for a completed request.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: Request path
            status: HTTP status code
            duration: Request duration in seconds
        """
        self.request_count.inc()
        self.request_latency.observe(duration)

        if status >= 400:
            self.error_count.inc()

        self._method_counts[method] = self._method_counts.get(method, 0) + 1
        self._status_counts[status] = self._status_counts.get(status, 0) + 1

        if path not in self._endpoint_latencies:
            self._endpoint_latencies[path] = []
        self._endpoint_latencies[path].append(duration)

    def get_prometheus_metrics(self) -> str:
        """
        Generate Prometheus-format metrics output.

        Returns:
            Multi-line string in Prometheus exposition format
        """
        lines = []

        # Request count
        lines.append("# HELP http_requests_total Total HTTP requests")
        lines.append("# TYPE http_requests_total counter")
        lines.append(f"http_requests_total {self.request_count.value}")

        # Error count
        lines.append("# HELP http_errors_total Total HTTP errors")
        lines.append("# TYPE http_errors_total counter")
        lines.append(f"http_errors_total {self.error_count.value}")

        # Request duration histogram
        lines.append("# HELP http_request_duration_seconds Request latency histogram")
        lines.append("# TYPE http_request_duration_seconds histogram")
        bucket_counts = self.request_latency.get_bucket_counts()
        for bucket, count in sorted(bucket_counts.items()):
            if bucket == float('inf'):
                lines.append(f'http_request_duration_seconds_bucket{{le="+Inf"}} {count}')
            else:
                lines.append(f'http_request_duration_seconds_bucket{{le="{bucket}"}} {count}')
        lines.append(f"http_request_duration_seconds_sum {self.request_latency.sum}")
        lines.append(f"http_request_duration_seconds_count {self.request_latency.count}")

        # Method counts
        for method, count in self._method_counts.items():
            lines.append(f'http_requests_by_method{{method="{method}"}} {count}')

        # Status counts
        for status, count in self._status_counts.items():
            lines.append(f'http_requests_by_status{{status="{status}"}} {count}')

        return "\n".join(lines)


# Singleton metrics collector instance
metrics_collector = MetricsCollector()


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware that records request metrics.

    Measures request duration and records it with the metrics collector.
    Excludes the /metrics endpoint to prevent self-referential metrics.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request and record metrics.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain

        Returns:
            HTTP response from the handler
        """
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time

        # Don't record metrics for /metrics endpoint
        if request.url.path != "/metrics":
            metrics_collector.record_request(
                method=request.method,
                path=request.url.path,
                status=response.status_code,
                duration=duration
            )

        return response


def get_metrics_endpoint():
    """
    Endpoint handler for /metrics.

    Returns Prometheus-format metrics as plain text.

    Returns:
        PlainTextResponse with Prometheus metrics
    """
    return PlainTextResponse(
        content=metrics_collector.get_prometheus_metrics(),
        media_type="text/plain; charset=utf-8"
    )


__all__ = [
    "Histogram",
    "Counter",
    "MetricsCollector",
    "MetricsMiddleware",
    "metrics_collector",
    "get_metrics_endpoint",
]
