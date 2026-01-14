"""
API versioning middleware for FastAPI.
Handles version detection, deprecation warnings, and version headers.
"""

from typing import Dict, Optional, Callable, List
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.utils.versioning import (
    APIVersion,
    extract_version,
    get_version_info,
    get_deprecation_message,
    VERSION_SUNSET_DATES,
    DEFAULT_VERSION,
)


def get_version_from_request(request: Request) -> APIVersion:
    """
    Extract API version from a FastAPI request.

    Args:
        request: FastAPI Request object

    Returns:
        Detected APIVersion
    """
    path = request.url.path
    headers = dict(request.headers)
    return extract_version(path, headers)


def add_version_headers(headers: Dict[str, str], version: APIVersion) -> None:
    """
    Add version-related headers to response.

    Args:
        headers: Headers dictionary to modify in place
        version: The API version used for the request
    """
    # Always add current version header
    headers["X-API-Version"] = version.value

    # Add deprecation headers if version is deprecated
    version_info = get_version_info(version)

    if version_info.deprecated:
        deprecation_message = get_deprecation_message(version)
        if deprecation_message:
            headers["X-API-Deprecation-Warning"] = deprecation_message
            headers["Deprecation"] = "true"

        # Add Sunset header if available
        sunset_date = VERSION_SUNSET_DATES.get(version)
        if sunset_date:
            headers["Sunset"] = sunset_date
            headers["X-API-Sunset"] = sunset_date


class VersionMiddleware(BaseHTTPMiddleware):
    """
    Middleware that handles API versioning.

    Features:
    - Detects version from path or headers
    - Adds version headers to responses
    - Adds deprecation warnings for old versions
    - Adds Sunset headers for deprecated versions
    """

    def __init__(
        self,
        app,
        excluded_paths: Optional[List[str]] = None,
        on_deprecated_version: Optional[Callable[[APIVersion, Request], None]] = None
    ):
        """
        Initialize the version middleware.

        Args:
            app: The FastAPI application
            excluded_paths: List of path prefixes to exclude from version processing
            on_deprecated_version: Optional callback when deprecated version is used
        """
        super().__init__(app)
        self.excluded_paths = excluded_paths or ["/health", "/metrics", "/docs", "/openapi.json"]
        self.on_deprecated_version = on_deprecated_version

    def _is_excluded(self, path: str) -> bool:
        """Check if a path is excluded from version processing."""
        for excluded in self.excluded_paths:
            if path.startswith(excluded):
                return True
        return False

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and add version headers to response."""
        path = request.url.path

        # Skip version processing for excluded paths
        if self._is_excluded(path):
            return await call_next(request)

        # Detect version from request
        version = get_version_from_request(request)

        # Store version in request state for access in route handlers
        request.state.api_version = version

        # Callback for deprecated version usage (for logging/metrics)
        if version.is_deprecated and self.on_deprecated_version:
            try:
                self.on_deprecated_version(version, request)
            except Exception:
                pass  # Don't let callback errors affect request processing

        # Process the request
        response = await call_next(request)

        # Add version headers to response
        response.headers["X-API-Version"] = version.value

        # Add deprecation headers if needed
        version_info = get_version_info(version)
        if version_info.deprecated:
            deprecation_message = get_deprecation_message(version)
            if deprecation_message:
                response.headers["X-API-Deprecation-Warning"] = deprecation_message
                response.headers["Deprecation"] = "true"

            # Add Sunset header
            sunset_date = VERSION_SUNSET_DATES.get(version)
            if sunset_date:
                response.headers["Sunset"] = sunset_date
                response.headers["X-API-Sunset"] = sunset_date

        return response


def get_request_version(request: Request) -> APIVersion:
    """
    Get the API version from request state.

    This should be called after the version middleware has processed the request.

    Args:
        request: FastAPI Request object

    Returns:
        APIVersion from request state, or DEFAULT_VERSION if not set
    """
    return getattr(request.state, 'api_version', DEFAULT_VERSION)


def require_version(
    min_version: Optional[APIVersion] = None,
    max_version: Optional[APIVersion] = None,
    exact_version: Optional[APIVersion] = None
):
    """
    Decorator factory for version requirements on endpoints.

    Usage:
        @app.get("/resource")
        @require_version(min_version=APIVersion.V2)
        async def resource_endpoint(request: Request):
            ...

    Args:
        min_version: Minimum required version
        max_version: Maximum allowed version
        exact_version: Exact version required

    Returns:
        Decorator function
    """
    def decorator(func):
        func._version_requirements = {
            'min_version': min_version,
            'max_version': max_version,
            'exact_version': exact_version
        }
        return func
    return decorator


__all__ = [
    "VersionMiddleware",
    "get_version_from_request",
    "add_version_headers",
    "get_request_version",
    "require_version",
]
