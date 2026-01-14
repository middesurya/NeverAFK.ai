"""
PRD-009: Input Sanitizer Middleware

This middleware intercepts incoming requests to protected endpoints and
checks for prompt injection attempts before they reach the LLM.

Features:
- Intercepts POST requests to chat endpoints
- Checks message content for injection attempts
- Returns safe error responses without exposing detection logic
- Logs all blocked injection attempts for security monitoring
"""

import json
import logging
from typing import Callable

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.security.prompt_guard import prompt_guard, ThreatLevel

logger = logging.getLogger(__name__)


class InputSanitizerMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for sanitizing user input and detecting prompt injections.

    This middleware checks all POST requests to protected endpoints (like /chat)
    for potential prompt injection attempts. When an injection is detected,
    it returns a safe, generic error message that doesn't reveal the detection
    mechanism to potential attackers.

    Example:
        app = FastAPI()
        app.add_middleware(InputSanitizerMiddleware)
    """

    # Endpoints that require injection protection
    PROTECTED_ENDPOINTS = [
        "/chat",
        "/chat/stream",
    ]

    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """
        Process the request, checking for prompt injections on protected endpoints.

        Args:
            request: The incoming HTTP request
            call_next: The next middleware/endpoint handler

        Returns:
            Response from the next handler, or HTTPException if injection detected

        Raises:
            HTTPException: 400 status if prompt injection is detected
        """
        # Only check POST requests to protected endpoints
        if request.method == "POST" and self._is_protected_endpoint(request.url.path):
            try:
                # Read and parse the request body
                body = await request.body()

                if body:
                    try:
                        data = json.loads(body)
                        message = data.get("message", "")

                        if message:
                            result = prompt_guard.check_input(message)

                            if result.is_injection:
                                # Log the attempt with details for security monitoring
                                client_ip = (
                                    request.client.host
                                    if request.client
                                    else "unknown"
                                )
                                logger.warning(
                                    f"Prompt injection blocked: "
                                    f"threat_level={result.threat_level.value}, "
                                    f"client_ip={client_ip}, "
                                    f"endpoint={request.url.path}"
                                )

                                # Return a generic error that doesn't expose
                                # our detection mechanism
                                raise HTTPException(
                                    status_code=400,
                                    detail=(
                                        "Your message could not be processed. "
                                        "Please rephrase your question."
                                    )
                                )

                    except json.JSONDecodeError:
                        # Let the endpoint validation handle invalid JSON
                        pass

            except HTTPException:
                # Re-raise HTTP exceptions (including our injection detection)
                raise
            except Exception as e:
                # Log unexpected errors but don't block the request
                logger.error(f"Error in input sanitizer middleware: {e}")

        # Continue to the next handler
        return await call_next(request)

    def _is_protected_endpoint(self, path: str) -> bool:
        """
        Check if the given path is a protected endpoint.

        Args:
            path: The URL path to check

        Returns:
            True if the path is protected, False otherwise
        """
        return any(
            path.startswith(endpoint) for endpoint in self.PROTECTED_ENDPOINTS
        )
