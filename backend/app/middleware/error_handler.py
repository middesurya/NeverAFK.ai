"""
Global error handler middleware for FastAPI applications.
Captures unhandled exceptions and reports them to the error tracker.
"""

import logging
from typing import Callable, Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from app.utils.error_tracker import ErrorTracker, error_tracker as global_error_tracker

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Middleware that catches unhandled exceptions and reports them to the error tracker.

    Features:
    - Captures unhandled exceptions
    - Adds request context to error events
    - Adds request breadcrumbs
    - Returns consistent error responses
    """

    def __init__(
        self,
        app: ASGIApp,
        tracker: ErrorTracker = None,
        include_stack_trace: bool = False,
        error_message: str = "Internal server error"
    ):
        """
        Initialize the error handler middleware.

        Args:
            app: The ASGI application
            tracker: Error tracker instance (uses global if not provided)
            include_stack_trace: Whether to include stack trace in response
            error_message: Default error message for responses
        """
        super().__init__(app)
        self.tracker = tracker or global_error_tracker
        self.include_stack_trace = include_stack_trace
        self.error_message = error_message

    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """
        Process the request and catch any unhandled exceptions.

        Args:
            request: The incoming request
            call_next: The next middleware/route handler

        Returns:
            Response from the application or error response
        """
        # Add request breadcrumb
        self._add_request_breadcrumb(request)

        try:
            response = await call_next(request)
            return response

        except Exception as exc:
            # Capture the exception with request context
            event_id = self._capture_error(request, exc)

            logger.error(
                f"Unhandled exception: {type(exc).__name__}: {str(exc)} "
                f"(event_id={event_id}, path={request.url.path})"
            )

            # Return error response
            return self._create_error_response(exc, event_id)

    def _add_request_breadcrumb(self, request: Request):
        """Add a breadcrumb for the incoming request."""
        self.tracker.add_breadcrumb(
            category="http",
            message=f"{request.method} {request.url.path}",
            data={
                "method": request.method,
                "path": request.url.path,
                "query": str(request.query_params) if request.query_params else None
            }
        )

    def _capture_error(self, request: Request, exc: Exception) -> Optional[str]:
        """
        Capture an error with request context.

        Args:
            request: The request that caused the error
            exc: The exception that was raised

        Returns:
            Event ID from the error tracker
        """
        # Build request context
        context = self._build_request_context(request)

        # Capture the exception
        event_id = self.tracker.capture_exception(exc, context=context)

        return event_id

    def _build_request_context(self, request: Request) -> dict:
        """
        Build context dictionary from request.

        Args:
            request: The incoming request

        Returns:
            Dictionary with request context
        """
        context = {
            "request": {
                "method": request.method,
                "path": request.url.path,
                "query_string": str(request.query_params) if request.query_params else "",
                "headers": dict(request.headers) if request.headers else {},
            },
            "url": str(request.url),
            "path": request.url.path
        }

        # Add client info if available
        if request.client:
            context["client"] = {
                "host": request.client.host,
                "port": request.client.port
            }

        return context

    def _create_error_response(
        self,
        exc: Exception,
        event_id: Optional[str]
    ) -> JSONResponse:
        """
        Create a JSON error response.

        Args:
            exc: The exception that was raised
            event_id: The event ID from the error tracker

        Returns:
            JSONResponse with error details
        """
        response_data = {
            "error": self.error_message,
            "detail": str(exc) if self.include_stack_trace else self.error_message,
        }

        if event_id:
            response_data["event_id"] = event_id

        return JSONResponse(
            status_code=500,
            content=response_data
        )


def setup_error_handler(
    app,
    tracker: ErrorTracker = None,
    include_stack_trace: bool = False
):
    """
    Set up error handler middleware on a FastAPI application.

    Args:
        app: FastAPI application instance
        tracker: Error tracker instance (uses global if not provided)
        include_stack_trace: Whether to include stack trace in error responses
    """
    app.add_middleware(
        ErrorHandlerMiddleware,
        tracker=tracker,
        include_stack_trace=include_stack_trace
    )
    logger.info("Error handler middleware configured")


__all__ = [
    "ErrorHandlerMiddleware",
    "setup_error_handler",
]
