"""
Logging middleware for structured request/response logging (PRD-013).

This middleware provides:
- Request/response logging with method, path, status, and duration
- Correlation ID generation and propagation
- Error logging with stack traces
- Path exclusion for health/metrics endpoints
"""

import time
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.utils.logger import get_logger, set_correlation_id, get_correlation_id

logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for structured request/response logging.

    Features:
    - Generates or uses provided X-Correlation-ID header
    - Logs request started and completed events
    - Includes duration, status code, method, and path
    - Excludes configurable paths from logging (health, metrics, favicon)
    - Logs errors with full stack traces

    The correlation ID is propagated through the request context and
    returned in the response headers.
    """

    EXCLUDED_PATHS = {'/health', '/metrics', '/favicon.ico'}

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process the request with logging.

        Args:
            request: The incoming HTTP request.
            call_next: Callable to invoke the next middleware/endpoint.

        Returns:
            The HTTP response with X-Correlation-ID header added.
        """
        # Skip logging for excluded paths
        if request.url.path in self.EXCLUDED_PATHS:
            return await call_next(request)

        # Set correlation ID (from header or generate new)
        correlation_id = request.headers.get('X-Correlation-ID') or str(uuid.uuid4())
        set_correlation_id(correlation_id)

        # Record start time
        start_time = time.time()

        # Log incoming request
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={'extra_fields': {
                'event': 'request_started',
                'method': request.method,
                'path': request.url.path,
                'query': str(request.query_params) if request.query_params else None,
                'client_ip': request.client.host if request.client else 'unknown',
            }}
        )

        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"Request failed: {request.method} {request.url.path}",
                exc_info=True,
                extra={'extra_fields': {
                    'event': 'request_error',
                    'method': request.method,
                    'path': request.url.path,
                    'duration_ms': round(duration * 1000, 2),
                    'error': str(e),
                }}
            )
            raise

        # Calculate duration
        duration = time.time() - start_time

        # Log response
        logger.info(
            f"Request completed: {request.method} {request.url.path} - {response.status_code}",
            extra={'extra_fields': {
                'event': 'request_completed',
                'method': request.method,
                'path': request.url.path,
                'status_code': response.status_code,
                'duration_ms': round(duration * 1000, 2),
            }}
        )

        # Add correlation ID to response header
        response.headers['X-Correlation-ID'] = correlation_id

        return response
