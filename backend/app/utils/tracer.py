"""
Distributed tracing utility with OpenTelemetry compatibility (PRD-019).

This module provides:
- OpenTelemetry compatible trace and span ID generation
- Span creation with parent-child relationships
- W3C traceparent/tracestate header parsing and formatting
- Context propagation utilities
- Thread-safe span management
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any, Union
from enum import Enum
import uuid
import time
import re
import threading
from contextvars import ContextVar


# Context variable for current span
current_span: ContextVar[Optional["Span"]] = ContextVar("current_span", default=None)


class SpanStatus(Enum):
    """Span status codes following OpenTelemetry specification."""
    UNSET = "UNSET"
    OK = "OK"
    ERROR = "ERROR"


@dataclass
class SpanEvent:
    """Represents an event that occurred during a span's lifetime."""
    name: str
    timestamp: float = field(default_factory=time.time)
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TraceContext:
    """Extracted trace context from headers."""
    trace_id: str
    parent_span_id: str
    trace_flags: int = 0
    tracestate: Dict[str, str] = field(default_factory=dict)

    @property
    def is_sampled(self) -> bool:
        """Check if the trace is sampled (bit 0 of trace_flags)."""
        return bool(self.trace_flags & 0x01)


@dataclass
class Span:
    """
    Represents a single operation within a trace.

    A span contains timing information, attributes, events, and links
    to parent/child spans within the same trace.
    """
    trace_id: str
    span_id: str
    name: str
    parent_span_id: Optional[str] = None
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: List[SpanEvent] = field(default_factory=list)
    status: SpanStatus = SpanStatus.UNSET
    status_message: str = ""
    _tracer: Optional["Tracer"] = field(default=None, repr=False)
    _previous_span: Optional["Span"] = field(default=None, repr=False)

    def end(self) -> None:
        """End the span and record its duration."""
        self.end_time = time.time()
        # Restore previous span in context
        if self._previous_span is not None:
            current_span.set(self._previous_span)
        else:
            current_span.set(None)

    @property
    def duration_ms(self) -> float:
        """Calculate span duration in milliseconds."""
        if self.end_time is not None:
            return (self.end_time - self.start_time) * 1000
        return 0.0

    def set_attribute(self, key: str, value: Any) -> None:
        """Set a single attribute on the span."""
        self.attributes[key] = value

    def set_attributes(self, attributes: Dict[str, Any]) -> None:
        """Set multiple attributes on the span."""
        self.attributes.update(attributes)

    def set_status(self, status: SpanStatus, message: str = "") -> None:
        """Set the span status."""
        self.status = status
        self.status_message = message

    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
        """Add an event to the span."""
        event = SpanEvent(
            name=name,
            timestamp=time.time(),
            attributes=attributes or {}
        )
        self.events.append(event)

    def record_exception(self, exception: Exception) -> None:
        """Record an exception as a span event."""
        self.add_event(
            name="exception",
            attributes={
                "exception.type": type(exception).__name__,
                "exception.message": str(exception),
                "exception.stacktrace": ""  # Could add traceback if needed
            }
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert span to dictionary for serialization."""
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "name": self.name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "status": self.status.value,
            "status_message": self.status_message,
            "attributes": self.attributes,
            "events": [
                {
                    "name": event.name,
                    "timestamp": event.timestamp,
                    "attributes": event.attributes
                }
                for event in self.events
            ]
        }

    def __enter__(self) -> "Span":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - end the span."""
        if exc_type is not None:
            self.set_status(SpanStatus.ERROR, str(exc_val))
            self.record_exception(exc_val)
        self.end()


def generate_trace_id() -> str:
    """
    Generate a random 128-bit trace ID as a 32-character hex string.

    OpenTelemetry trace IDs are 128-bit (16 bytes) represented as
    32 lowercase hex characters.
    """
    while True:
        trace_id = uuid.uuid4().hex
        # Ensure it's not all zeros (invalid in OpenTelemetry)
        if trace_id != '0' * 32:
            return trace_id


def generate_span_id() -> str:
    """
    Generate a random 64-bit span ID as a 16-character hex string.

    OpenTelemetry span IDs are 64-bit (8 bytes) represented as
    16 lowercase hex characters.
    """
    while True:
        # Generate 8 random bytes (64 bits)
        span_id = uuid.uuid4().hex[:16]
        # Ensure it's not all zeros (invalid in OpenTelemetry)
        if span_id != '0' * 16:
            return span_id


# W3C traceparent regex pattern
# Format: version-traceid-parentid-traceflags
# Example: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
TRACEPARENT_PATTERN = re.compile(
    r'^([0-9a-f]{2})-([0-9a-f]{32})-([0-9a-f]{16})-([0-9a-f]{2})$',
    re.IGNORECASE
)


def parse_traceparent(header: str) -> Optional[TraceContext]:
    """
    Parse a W3C traceparent header.

    Format: {version}-{trace-id}-{parent-id}-{trace-flags}
    Example: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01

    Args:
        header: The traceparent header value

    Returns:
        TraceContext if valid, None otherwise
    """
    if not header:
        return None

    match = TRACEPARENT_PATTERN.match(header.strip())
    if not match:
        return None

    version, trace_id, parent_id, trace_flags = match.groups()

    # Version 00 is the only supported version currently
    if version != "00":
        return None

    # Trace ID and parent ID cannot be all zeros
    if trace_id == '0' * 32:
        return None
    if parent_id == '0' * 16:
        return None

    return TraceContext(
        trace_id=trace_id.lower(),
        parent_span_id=parent_id.lower(),
        trace_flags=int(trace_flags, 16)
    )


def format_traceparent(trace_id: str, span_id: str, sampled: bool = True) -> str:
    """
    Format a W3C traceparent header.

    Args:
        trace_id: The 32-character trace ID
        span_id: The 16-character span ID
        sampled: Whether the trace is sampled

    Returns:
        Formatted traceparent header string
    """
    trace_flags = "01" if sampled else "00"
    return f"00-{trace_id}-{span_id}-{trace_flags}"


def parse_tracestate(header: str) -> Dict[str, str]:
    """
    Parse a W3C tracestate header.

    Format: vendor1=value1,vendor2=value2

    Args:
        header: The tracestate header value

    Returns:
        Dictionary of vendor key-value pairs
    """
    if not header or not header.strip():
        return {}

    result = {}
    pairs = header.split(',')

    for pair in pairs:
        pair = pair.strip()
        if '=' in pair:
            key, value = pair.split('=', 1)
            result[key.strip()] = value.strip()

    return result


def format_tracestate(state: Dict[str, str]) -> str:
    """
    Format a W3C tracestate header.

    Args:
        state: Dictionary of vendor key-value pairs

    Returns:
        Formatted tracestate header string
    """
    return ','.join(f"{k}={v}" for k, v in state.items())


def get_current_span() -> Optional[Span]:
    """Get the current active span from context."""
    return current_span.get()


def extract_context(headers: Dict[str, str]) -> Optional[TraceContext]:
    """
    Extract trace context from HTTP headers.

    Looks for W3C traceparent and tracestate headers.

    Args:
        headers: Dictionary of HTTP headers

    Returns:
        TraceContext if traceparent header is valid, None otherwise
    """
    # Normalize header keys to lowercase for case-insensitive lookup
    normalized = {k.lower(): v for k, v in headers.items()}

    traceparent = normalized.get('traceparent')
    if not traceparent:
        return None

    context = parse_traceparent(traceparent)
    if not context:
        return None

    # Parse tracestate if present
    tracestate = normalized.get('tracestate', '')
    context.tracestate = parse_tracestate(tracestate)

    return context


def inject_context(span: Span, headers: Dict[str, str]) -> None:
    """
    Inject trace context into HTTP headers.

    Adds W3C traceparent header to the provided headers dict.

    Args:
        span: The current span to inject
        headers: Dictionary of HTTP headers to modify
    """
    headers['traceparent'] = format_traceparent(
        span.trace_id,
        span.span_id,
        sampled=True
    )


class Tracer:
    """
    Main tracer class for creating and managing spans.

    Thread-safe implementation that supports:
    - Span creation with automatic parent detection
    - Context propagation
    - Span recording and retrieval
    """

    def __init__(self, service_name: str = "strong_mvp"):
        """
        Initialize the tracer.

        Args:
            service_name: Name of the service for identification in traces
        """
        self.service_name = service_name
        self._spans: List[Span] = []
        self._lock = threading.Lock()

    def start_span(
        self,
        name: str,
        parent: Optional[Span] = None,
        context: Optional[TraceContext] = None
    ) -> Span:
        """
        Start a new span.

        Args:
            name: Name of the operation this span represents
            parent: Optional parent span for creating child spans
            context: Optional trace context from extracted headers

        Returns:
            A new Span instance
        """
        # Store the current span to restore later
        previous_span = current_span.get()

        # Determine trace_id and parent_span_id
        if context:
            # Propagated context from incoming request
            trace_id = context.trace_id
            parent_span_id = context.parent_span_id
        elif parent:
            # Explicit parent span
            trace_id = parent.trace_id
            parent_span_id = parent.span_id
        else:
            # New root span
            trace_id = generate_trace_id()
            parent_span_id = None

        span = Span(
            trace_id=trace_id,
            span_id=generate_span_id(),
            parent_span_id=parent_span_id,
            name=name,
            _tracer=self,
            _previous_span=previous_span
        )

        # Set as current span
        current_span.set(span)

        # Record the span for later retrieval
        with self._lock:
            self._spans.append(span)

        return span

    def get_finished_spans(self) -> List[Span]:
        """
        Get all finished (ended) spans.

        Returns:
            List of spans that have been ended
        """
        with self._lock:
            return [span for span in self._spans if span.end_time is not None]

    def get_all_spans(self) -> List[Span]:
        """
        Get all spans (both finished and unfinished).

        Returns:
            List of all spans
        """
        with self._lock:
            return list(self._spans)

    def clear_spans(self) -> None:
        """Clear all recorded spans."""
        with self._lock:
            self._spans.clear()


# Global tracer instance
tracer = Tracer()
