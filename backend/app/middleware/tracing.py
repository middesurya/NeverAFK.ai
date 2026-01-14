"""
Tracing middleware for distributed tracing (PRD-019).

This middleware provides:
- Automatic span creation for HTTP requests
- W3C traceparent header propagation
- HTTP attribute recording
- Error handling and status recording
- Path exclusion for health/metrics endpoints
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from typing import Optional, Set

from app.utils.tracer import (
    Tracer,
    tracer as global_tracer,
    extract_context,
    format_traceparent,
    SpanStatus
)


class TracingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for automatic distributed tracing.

    Features:
    - Creates spans for each HTTP request
    - Propagates W3C traceparent headers
    - Records HTTP method, path, and status code
    - Handles errors and records exception events
    - Excludes configurable paths from tracing

    Usage:
        from app.middleware.tracing import TracingMiddleware

        app = FastAPI()
        app.add_middleware(TracingMiddleware)
    """

    EXCLUDED_PATHS: Set[str] = {'/health', '/metrics', '/favicon.ico'}

    def __init__(self, app, tracer: Optional[Tracer] = None):
        """
        Initialize the tracing middleware.

        Args:
            app: The ASGI application
            tracer: Optional custom tracer instance (uses global tracer if not provided)
        """
        super().__init__(app)
        self.tracer = tracer or global_tracer

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process the request with tracing.

        Args:
            request: The incoming HTTP request
            call_next: Callable to invoke the next middleware/endpoint

        Returns:
            The HTTP response with traceparent header added
        """
        # Skip tracing for excluded paths
        if request.url.path in self.EXCLUDED_PATHS:
            return await call_next(request)

        # Extract trace context from incoming headers
        headers = dict(request.headers)
        context = extract_context(headers)

        # Create span name from HTTP method and path
        span_name = f"HTTP {request.method} {request.url.path}"

        # Start the span with propagated context if available
        span = self.tracer.start_span(span_name, context=context)

        # Set standard HTTP attributes
        span.set_attributes({
            "http.method": request.method,
            "http.url": str(request.url.path),
            "http.scheme": request.url.scheme,
            "http.host": request.url.hostname or "",
            "http.target": str(request.url.path),
            "http.user_agent": request.headers.get("user-agent", ""),
            "service.name": self.tracer.service_name,
        })

        # Add query parameters if present
        if request.url.query:
            span.set_attribute("http.query", str(request.url.query))

        # Add client IP if available
        if request.client:
            span.set_attribute("net.peer.ip", request.client.host)

        try:
            # Process the request
            response = await call_next(request)

            # Record the response status code
            span.set_attribute("http.status_code", response.status_code)

            # Set span status based on HTTP status code
            if 200 <= response.status_code < 400:
                span.set_status(SpanStatus.OK)
            elif response.status_code >= 400:
                span.set_status(SpanStatus.ERROR, f"HTTP {response.status_code}")

            # Add traceparent header to response
            response.headers["traceparent"] = format_traceparent(
                span.trace_id,
                span.span_id,
                sampled=True
            )

            return response

        except Exception as e:
            # Record the exception
            span.set_status(SpanStatus.ERROR, str(e))
            span.record_exception(e)
            span.set_attribute("http.status_code", 500)
            raise

        finally:
            # End the span
            span.end()
