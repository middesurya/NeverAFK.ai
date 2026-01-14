"""Routes package for API endpoints."""

from app.routes.health import router as health_router
from app.routes.websocket import router as websocket_router

__all__ = ["health_router", "websocket_router"]
