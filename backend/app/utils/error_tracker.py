"""
Error tracking and reporting service (Sentry-like functionality).
Provides error capture with context, stack traces, user context, breadcrumbs, and more.
"""

import uuid
import json
import hashlib
import traceback
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any, Type

logger = logging.getLogger(__name__)


@dataclass
class ErrorEvent:
    """Represents a captured error event."""
    id: str
    type: str
    message: str
    timestamp: datetime
    stack_trace: str
    context: dict = field(default_factory=dict)
    user_id: Optional[str] = None
    tags: dict = field(default_factory=dict)
    breadcrumbs: list = field(default_factory=list)
    level: str = "error"
    fingerprint: Optional[str] = None


class ErrorTracker:
    """
    Error tracking service for capturing and managing errors.

    Provides:
    - Exception capture with context
    - Stack trace extraction
    - User context management
    - Breadcrumb recording
    - Tag and extra context management
    - Error filtering
    - Event serialization
    """

    MAX_EVENTS = 1000
    MAX_BREADCRUMBS = 100

    def __init__(
        self,
        dsn: str = None,
        environment: str = "development",
        max_events: int = None,
        max_breadcrumbs: int = None
    ):
        """
        Initialize the error tracker.

        Args:
            dsn: Data source name (connection string) for remote error service
            environment: Environment name (development, staging, production)
            max_events: Maximum number of events to store
            max_breadcrumbs: Maximum number of breadcrumbs to keep
        """
        self.dsn = dsn
        self.environment = environment
        self._max_events = max_events or self.MAX_EVENTS
        self._max_breadcrumbs = max_breadcrumbs or self.MAX_BREADCRUMBS

        self._events: list[ErrorEvent] = []
        self._breadcrumbs: list[dict] = []
        self._user_context: Optional[dict] = None
        self._tags: dict = {}
        self._extra: dict = {}
        self._ignored_exceptions: set[Type[Exception]] = set()

    @property
    def is_enabled(self) -> bool:
        """Check if error tracking is enabled (has DSN configured)."""
        return self.dsn is not None

    def capture_exception(
        self,
        exc: Exception,
        context: dict = None,
        level: str = "error",
        fingerprint: str = None
    ) -> Optional[str]:
        """
        Capture an exception and create an error event.

        Args:
            exc: The exception to capture
            context: Additional context data
            level: Error level (error, warning, critical)
            fingerprint: Custom fingerprint for grouping

        Returns:
            Event ID if captured, None if ignored
        """
        # Check if exception type should be ignored
        if type(exc) in self._ignored_exceptions:
            logger.debug(f"Ignoring exception of type {type(exc).__name__}")
            return None

        # Generate event ID
        event_id = str(uuid.uuid4())

        # Extract stack trace
        stack_trace = self._extract_stack_trace(exc)

        # Merge context with extra context
        merged_context = {**self._extra}
        if context:
            merged_context.update(context)

        # Create event
        event = ErrorEvent(
            id=event_id,
            type=type(exc).__name__,
            message=str(exc),
            timestamp=datetime.utcnow(),
            stack_trace=stack_trace,
            context=merged_context,
            user_id=self._user_context.get("id") if self._user_context else None,
            tags={**self._tags},
            breadcrumbs=list(self._breadcrumbs),
            level=level,
            fingerprint=fingerprint or self.generate_fingerprint(exc)
        )

        # Store event
        self._store_event(event)

        logger.info(f"Captured {type(exc).__name__}: {str(exc)[:100]} (event_id={event_id})")

        return event_id

    def capture_message(
        self,
        message: str,
        level: str = "info",
        context: dict = None
    ) -> str:
        """
        Capture a message as an error event.

        Args:
            message: The message to capture
            level: Message level (info, warning, error)
            context: Additional context data

        Returns:
            Event ID
        """
        event_id = str(uuid.uuid4())

        # Merge context with extra context
        merged_context = {**self._extra}
        if context:
            merged_context.update(context)

        event = ErrorEvent(
            id=event_id,
            type="Message",
            message=message,
            timestamp=datetime.utcnow(),
            stack_trace="",
            context=merged_context,
            user_id=self._user_context.get("id") if self._user_context else None,
            tags={**self._tags},
            breadcrumbs=list(self._breadcrumbs),
            level=level
        )

        self._store_event(event)
        logger.info(f"Captured message: {message[:100]} (event_id={event_id})")

        return event_id

    def _extract_stack_trace(self, exc: Exception) -> str:
        """Extract stack trace from exception."""
        try:
            return "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        except Exception:
            return f"{type(exc).__name__}: {str(exc)}"

    def extract_frames(self, exc: Exception) -> list[dict]:
        """
        Extract stack frames from exception.

        Args:
            exc: The exception to extract frames from

        Returns:
            List of frame dictionaries with file, line, function info
        """
        frames = []
        tb = exc.__traceback__

        while tb is not None:
            frame = tb.tb_frame
            frames.append({
                "filename": frame.f_code.co_filename,
                "lineno": tb.tb_lineno,
                "function": frame.f_code.co_name,
                "locals": {k: repr(v)[:100] for k, v in frame.f_locals.items()
                          if not k.startswith("_")}
            })
            tb = tb.tb_next

        return frames

    def _store_event(self, event: ErrorEvent):
        """Store an event, enforcing max events limit."""
        self._events.append(event)

        # Enforce limit - remove oldest events
        if len(self._events) > self._max_events:
            self._events = self._events[-self._max_events:]

    def get_events(
        self,
        type_filter: str = None,
        level_filter: str = None
    ) -> list[ErrorEvent]:
        """
        Get stored events, optionally filtered.

        Args:
            type_filter: Filter by error type
            level_filter: Filter by error level

        Returns:
            List of matching events
        """
        events = self._events

        if type_filter:
            events = [e for e in events if e.type == type_filter]

        if level_filter:
            events = [e for e in events if e.level == level_filter]

        return events

    # User context methods
    def set_user(
        self,
        user_id: str,
        email: str = None,
        username: str = None,
        **kwargs
    ):
        """
        Set user context for error tracking.

        Args:
            user_id: User identifier
            email: User email
            username: User name
            **kwargs: Additional user data
        """
        self._user_context = {
            "id": user_id,
            **({"email": email} if email else {}),
            **({"username": username} if username else {}),
            **kwargs
        }

    def clear_user(self):
        """Clear user context."""
        self._user_context = None

    # Breadcrumb methods
    def add_breadcrumb(
        self,
        category: str,
        message: str,
        data: dict = None,
        level: str = "info"
    ):
        """
        Add a breadcrumb for debugging context.

        Args:
            category: Breadcrumb category (http, navigation, ui, etc.)
            message: Breadcrumb message
            data: Additional data
            level: Breadcrumb level
        """
        breadcrumb = {
            "category": category,
            "message": message,
            "data": data or {},
            "timestamp": datetime.utcnow().isoformat(),
            "level": level
        }

        self._breadcrumbs.append(breadcrumb)

        # Enforce limit - keep newest breadcrumbs
        if len(self._breadcrumbs) > self._max_breadcrumbs:
            self._breadcrumbs = self._breadcrumbs[-self._max_breadcrumbs:]

    def clear_breadcrumbs(self):
        """Clear all breadcrumbs."""
        self._breadcrumbs = []

    # Tag and extra context methods
    def set_tag(self, key: str, value: str):
        """Set a tag for error grouping."""
        self._tags[key] = value

    def clear_tags(self):
        """Clear all tags."""
        self._tags = {}

    def set_extra(self, key: str, value: Any):
        """Set extra context data."""
        self._extra[key] = value

    def clear_extra(self):
        """Clear extra context."""
        self._extra = {}

    # Filtering methods
    def add_ignore_exception(self, exc_type: Type[Exception]):
        """Add an exception type to be ignored."""
        self._ignored_exceptions.add(exc_type)

    def remove_ignore_exception(self, exc_type: Type[Exception]):
        """Remove an exception type from ignore list."""
        self._ignored_exceptions.discard(exc_type)

    # Serialization methods
    def event_to_dict(self, event: ErrorEvent) -> dict:
        """Convert an event to a dictionary."""
        return {
            "id": event.id,
            "type": event.type,
            "message": event.message,
            "timestamp": event.timestamp.isoformat(),
            "stack_trace": event.stack_trace,
            "context": event.context,
            "user_id": event.user_id,
            "tags": event.tags,
            "breadcrumbs": event.breadcrumbs,
            "level": event.level,
            "fingerprint": event.fingerprint
        }

    def event_to_json(self, event: ErrorEvent) -> str:
        """Convert an event to JSON string."""
        return json.dumps(self.event_to_dict(event))

    # Fingerprinting methods
    def generate_fingerprint(self, exc: Exception) -> str:
        """
        Generate a fingerprint for error grouping.

        Args:
            exc: The exception to fingerprint

        Returns:
            Fingerprint string
        """
        # Create fingerprint from exception type and message
        fingerprint_data = f"{type(exc).__name__}:{str(exc)}"
        return hashlib.md5(fingerprint_data.encode()).hexdigest()

    # Clear and reset
    def clear(self):
        """Clear all events, breadcrumbs, and context."""
        self._events = []
        self._breadcrumbs = []
        self._user_context = None
        self._tags = {}
        self._extra = {}


# Global error tracker instance
error_tracker = ErrorTracker()


def configure_error_tracker(
    dsn: str = None,
    environment: str = None,
    **kwargs
):
    """
    Configure the global error tracker.

    Args:
        dsn: Data source name for remote error service
        environment: Environment name
        **kwargs: Additional configuration options
    """
    global error_tracker

    if dsn:
        error_tracker.dsn = dsn
    if environment:
        error_tracker.environment = environment

    logger.info(f"Error tracker configured: dsn={'configured' if dsn else 'none'}, "
                f"environment={environment or error_tracker.environment}")


__all__ = [
    "ErrorEvent",
    "ErrorTracker",
    "error_tracker",
    "configure_error_tracker",
]
