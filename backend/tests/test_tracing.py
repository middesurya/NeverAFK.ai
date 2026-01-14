"""
Tests for distributed tracing with OpenTelemetry compatibility (PRD-019).

TDD RED Phase - Tests written before implementation.
"""

import pytest
import json
import io
import sys
import re
import uuid
import time
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime
from contextlib import contextmanager
import threading


class TestTraceIDGeneration:
    """Tests for trace ID generation."""

    def test_trace_id_generated_as_hex_string(self):
        """Test that trace ID is generated as a 32-character hex string."""
        from app.utils.tracer import Tracer

        tracer = Tracer()
        span = tracer.start_span("test-span")

        assert span.trace_id is not None
        assert len(span.trace_id) == 32
        assert all(c in '0123456789abcdef' for c in span.trace_id.lower())

    def test_trace_id_unique_per_trace(self):
        """Test that each new trace gets a unique trace ID."""
        from app.utils.tracer import Tracer

        tracer = Tracer()
        trace_ids = set()

        for _ in range(100):
            span = tracer.start_span("test-span")
            trace_ids.add(span.trace_id)
            span.end()

        assert len(trace_ids) == 100, "All trace IDs should be unique"

    def test_trace_id_inherited_from_parent(self):
        """Test that child spans inherit trace ID from parent."""
        from app.utils.tracer import Tracer

        tracer = Tracer()
        parent = tracer.start_span("parent-span")
        child = tracer.start_span("child-span", parent=parent)

        assert child.trace_id == parent.trace_id

    def test_trace_id_format_opentelemetry_compatible(self):
        """Test that trace ID format is OpenTelemetry compatible (128-bit hex)."""
        from app.utils.tracer import Tracer

        tracer = Tracer()
        span = tracer.start_span("test-span")

        # OpenTelemetry trace IDs are 128-bit (32 hex chars)
        assert len(span.trace_id) == 32
        # Should be valid hex
        int(span.trace_id, 16)

    def test_generate_trace_id_function(self):
        """Test the standalone generate_trace_id function."""
        from app.utils.tracer import generate_trace_id

        trace_id = generate_trace_id()

        assert len(trace_id) == 32
        assert all(c in '0123456789abcdef' for c in trace_id.lower())

    def test_trace_id_not_all_zeros(self):
        """Test that trace ID is not all zeros (invalid in OpenTelemetry)."""
        from app.utils.tracer import generate_trace_id

        for _ in range(10):
            trace_id = generate_trace_id()
            assert trace_id != '0' * 32, "Trace ID should not be all zeros"


class TestSpanIDGeneration:
    """Tests for span ID generation."""

    def test_span_id_generated_as_hex_string(self):
        """Test that span ID is generated as a 16-character hex string."""
        from app.utils.tracer import Tracer

        tracer = Tracer()
        span = tracer.start_span("test-span")

        assert span.span_id is not None
        assert len(span.span_id) == 16
        assert all(c in '0123456789abcdef' for c in span.span_id.lower())

    def test_span_id_unique_per_span(self):
        """Test that each span gets a unique span ID."""
        from app.utils.tracer import Tracer

        tracer = Tracer()
        span_ids = set()

        for _ in range(100):
            span = tracer.start_span("test-span")
            span_ids.add(span.span_id)
            span.end()

        assert len(span_ids) == 100, "All span IDs should be unique"

    def test_span_id_format_opentelemetry_compatible(self):
        """Test that span ID format is OpenTelemetry compatible (64-bit hex)."""
        from app.utils.tracer import Tracer

        tracer = Tracer()
        span = tracer.start_span("test-span")

        # OpenTelemetry span IDs are 64-bit (16 hex chars)
        assert len(span.span_id) == 16
        int(span.span_id, 16)

    def test_generate_span_id_function(self):
        """Test the standalone generate_span_id function."""
        from app.utils.tracer import generate_span_id

        span_id = generate_span_id()

        assert len(span_id) == 16
        assert all(c in '0123456789abcdef' for c in span_id.lower())

    def test_span_id_not_all_zeros(self):
        """Test that span ID is not all zeros (invalid in OpenTelemetry)."""
        from app.utils.tracer import generate_span_id

        for _ in range(10):
            span_id = generate_span_id()
            assert span_id != '0' * 16, "Span ID should not be all zeros"


class TestSpanCreationAndLifecycle:
    """Tests for span creation and lifecycle management."""

    def test_span_creation_with_name(self):
        """Test that span can be created with a name."""
        from app.utils.tracer import Tracer

        tracer = Tracer()
        span = tracer.start_span("my-operation")

        assert span.name == "my-operation"

    def test_span_has_start_time(self):
        """Test that span has a start time when created."""
        from app.utils.tracer import Tracer

        before = time.time()
        tracer = Tracer()
        span = tracer.start_span("test-span")
        after = time.time()

        assert span.start_time is not None
        assert before <= span.start_time <= after

    def test_span_end_sets_end_time(self):
        """Test that calling end() sets the end time."""
        from app.utils.tracer import Tracer

        tracer = Tracer()
        span = tracer.start_span("test-span")

        assert span.end_time is None

        before = time.time()
        span.end()
        after = time.time()

        assert span.end_time is not None
        assert before <= span.end_time <= after

    def test_span_duration_calculation(self):
        """Test that span duration is calculated correctly."""
        from app.utils.tracer import Tracer

        tracer = Tracer()
        span = tracer.start_span("test-span")

        time.sleep(0.05)  # 50ms
        span.end()

        assert span.duration_ms >= 50
        assert span.duration_ms < 200  # Should not take too long

    def test_span_duration_zero_before_end(self):
        """Test that duration is 0 before span is ended."""
        from app.utils.tracer import Tracer

        tracer = Tracer()
        span = tracer.start_span("test-span")

        assert span.duration_ms == 0

    def test_span_default_status_unset(self):
        """Test that span status is UNSET by default."""
        from app.utils.tracer import Tracer, SpanStatus

        tracer = Tracer()
        span = tracer.start_span("test-span")

        assert span.status == SpanStatus.UNSET

    def test_span_set_status_ok(self):
        """Test setting span status to OK."""
        from app.utils.tracer import Tracer, SpanStatus

        tracer = Tracer()
        span = tracer.start_span("test-span")
        span.set_status(SpanStatus.OK)

        assert span.status == SpanStatus.OK

    def test_span_set_status_error(self):
        """Test setting span status to ERROR."""
        from app.utils.tracer import Tracer, SpanStatus

        tracer = Tracer()
        span = tracer.start_span("test-span")
        span.set_status(SpanStatus.ERROR, "Something went wrong")

        assert span.status == SpanStatus.ERROR
        assert span.status_message == "Something went wrong"

    def test_span_context_manager(self):
        """Test that span can be used as a context manager."""
        from app.utils.tracer import Tracer

        tracer = Tracer()

        with tracer.start_span("test-span") as span:
            assert span.end_time is None

        assert span.end_time is not None


class TestParentChildRelationships:
    """Tests for parent-child span relationships."""

    def test_child_span_has_parent_span_id(self):
        """Test that child span has parent's span ID."""
        from app.utils.tracer import Tracer

        tracer = Tracer()
        parent = tracer.start_span("parent-span")
        child = tracer.start_span("child-span", parent=parent)

        assert child.parent_span_id == parent.span_id

    def test_root_span_has_no_parent(self):
        """Test that root span has no parent span ID."""
        from app.utils.tracer import Tracer

        tracer = Tracer()
        span = tracer.start_span("root-span")

        assert span.parent_span_id is None

    def test_nested_spans_maintain_hierarchy(self):
        """Test that deeply nested spans maintain correct hierarchy."""
        from app.utils.tracer import Tracer

        tracer = Tracer()
        root = tracer.start_span("root")
        child1 = tracer.start_span("child1", parent=root)
        child2 = tracer.start_span("child2", parent=child1)
        child3 = tracer.start_span("child3", parent=child2)

        assert child1.trace_id == root.trace_id
        assert child2.trace_id == root.trace_id
        assert child3.trace_id == root.trace_id

        assert child1.parent_span_id == root.span_id
        assert child2.parent_span_id == child1.span_id
        assert child3.parent_span_id == child2.span_id

    def test_sibling_spans_share_parent(self):
        """Test that sibling spans share the same parent."""
        from app.utils.tracer import Tracer

        tracer = Tracer()
        parent = tracer.start_span("parent")
        sibling1 = tracer.start_span("sibling1", parent=parent)
        sibling2 = tracer.start_span("sibling2", parent=parent)

        assert sibling1.parent_span_id == parent.span_id
        assert sibling2.parent_span_id == parent.span_id
        assert sibling1.span_id != sibling2.span_id


class TestSpanAttributes:
    """Tests for span attribute setting."""

    def test_set_single_attribute(self):
        """Test setting a single attribute on span."""
        from app.utils.tracer import Tracer

        tracer = Tracer()
        span = tracer.start_span("test-span")
        span.set_attribute("key", "value")

        assert span.attributes.get("key") == "value"

    def test_set_multiple_attributes(self):
        """Test setting multiple attributes on span."""
        from app.utils.tracer import Tracer

        tracer = Tracer()
        span = tracer.start_span("test-span")
        span.set_attribute("key1", "value1")
        span.set_attribute("key2", "value2")
        span.set_attribute("key3", 123)

        assert span.attributes.get("key1") == "value1"
        assert span.attributes.get("key2") == "value2"
        assert span.attributes.get("key3") == 123

    def test_set_attributes_dict(self):
        """Test setting multiple attributes at once with dict."""
        from app.utils.tracer import Tracer

        tracer = Tracer()
        span = tracer.start_span("test-span")
        span.set_attributes({
            "http.method": "GET",
            "http.url": "/api/users",
            "http.status_code": 200
        })

        assert span.attributes.get("http.method") == "GET"
        assert span.attributes.get("http.url") == "/api/users"
        assert span.attributes.get("http.status_code") == 200

    def test_attribute_types_string(self):
        """Test that string attributes are supported."""
        from app.utils.tracer import Tracer

        tracer = Tracer()
        span = tracer.start_span("test-span")
        span.set_attribute("string_attr", "hello")

        assert span.attributes.get("string_attr") == "hello"

    def test_attribute_types_int(self):
        """Test that integer attributes are supported."""
        from app.utils.tracer import Tracer

        tracer = Tracer()
        span = tracer.start_span("test-span")
        span.set_attribute("int_attr", 42)

        assert span.attributes.get("int_attr") == 42

    def test_attribute_types_float(self):
        """Test that float attributes are supported."""
        from app.utils.tracer import Tracer

        tracer = Tracer()
        span = tracer.start_span("test-span")
        span.set_attribute("float_attr", 3.14)

        assert span.attributes.get("float_attr") == 3.14

    def test_attribute_types_bool(self):
        """Test that boolean attributes are supported."""
        from app.utils.tracer import Tracer

        tracer = Tracer()
        span = tracer.start_span("test-span")
        span.set_attribute("bool_attr", True)

        assert span.attributes.get("bool_attr") == True

    def test_attribute_types_list(self):
        """Test that list attributes are supported."""
        from app.utils.tracer import Tracer

        tracer = Tracer()
        span = tracer.start_span("test-span")
        span.set_attribute("list_attr", ["a", "b", "c"])

        assert span.attributes.get("list_attr") == ["a", "b", "c"]

    def test_attribute_overwrite(self):
        """Test that setting same attribute overwrites previous value."""
        from app.utils.tracer import Tracer

        tracer = Tracer()
        span = tracer.start_span("test-span")
        span.set_attribute("key", "value1")
        span.set_attribute("key", "value2")

        assert span.attributes.get("key") == "value2"


class TestSpanEvents:
    """Tests for span event recording."""

    def test_add_event_basic(self):
        """Test adding a basic event to span."""
        from app.utils.tracer import Tracer

        tracer = Tracer()
        span = tracer.start_span("test-span")
        span.add_event("user_clicked")

        assert len(span.events) == 1
        assert span.events[0].name == "user_clicked"

    def test_add_event_with_attributes(self):
        """Test adding an event with attributes."""
        from app.utils.tracer import Tracer

        tracer = Tracer()
        span = tracer.start_span("test-span")
        span.add_event("db_query", {"query": "SELECT *", "rows": 10})

        assert len(span.events) == 1
        assert span.events[0].name == "db_query"
        assert span.events[0].attributes.get("query") == "SELECT *"
        assert span.events[0].attributes.get("rows") == 10

    def test_add_event_has_timestamp(self):
        """Test that event has timestamp."""
        from app.utils.tracer import Tracer

        before = time.time()
        tracer = Tracer()
        span = tracer.start_span("test-span")
        span.add_event("test_event")
        after = time.time()

        assert span.events[0].timestamp is not None
        assert before <= span.events[0].timestamp <= after

    def test_add_multiple_events(self):
        """Test adding multiple events to span."""
        from app.utils.tracer import Tracer

        tracer = Tracer()
        span = tracer.start_span("test-span")
        span.add_event("event1")
        span.add_event("event2")
        span.add_event("event3")

        assert len(span.events) == 3
        assert span.events[0].name == "event1"
        assert span.events[1].name == "event2"
        assert span.events[2].name == "event3"

    def test_event_order_preserved(self):
        """Test that event order is preserved."""
        from app.utils.tracer import Tracer

        tracer = Tracer()
        span = tracer.start_span("test-span")

        for i in range(10):
            span.add_event(f"event_{i}")

        for i in range(10):
            assert span.events[i].name == f"event_{i}"

    def test_record_exception(self):
        """Test recording an exception as an event."""
        from app.utils.tracer import Tracer

        tracer = Tracer()
        span = tracer.start_span("test-span")

        try:
            raise ValueError("Test error")
        except ValueError as e:
            span.record_exception(e)

        assert len(span.events) == 1
        assert span.events[0].name == "exception"
        assert span.events[0].attributes.get("exception.type") == "ValueError"
        assert span.events[0].attributes.get("exception.message") == "Test error"


class TestW3CTraceparentHeaderParsing:
    """Tests for W3C traceparent header parsing."""

    def test_parse_valid_traceparent(self):
        """Test parsing a valid W3C traceparent header."""
        from app.utils.tracer import parse_traceparent

        header = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
        result = parse_traceparent(header)

        assert result is not None
        assert result.trace_id == "4bf92f3577b34da6a3ce929d0e0e4736"
        assert result.parent_span_id == "00f067aa0ba902b7"
        assert result.trace_flags == 1

    def test_parse_traceparent_sampled_flag(self):
        """Test parsing traceparent with sampled flag set."""
        from app.utils.tracer import parse_traceparent

        header = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
        result = parse_traceparent(header)

        assert result.is_sampled == True

    def test_parse_traceparent_not_sampled(self):
        """Test parsing traceparent with sampled flag not set."""
        from app.utils.tracer import parse_traceparent

        header = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-00"
        result = parse_traceparent(header)

        assert result.is_sampled == False

    def test_parse_invalid_traceparent_wrong_version(self):
        """Test that invalid version returns None."""
        from app.utils.tracer import parse_traceparent

        header = "ff-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
        result = parse_traceparent(header)

        assert result is None

    def test_parse_invalid_traceparent_wrong_format(self):
        """Test that wrong format returns None."""
        from app.utils.tracer import parse_traceparent

        header = "invalid-header-format"
        result = parse_traceparent(header)

        assert result is None

    def test_parse_invalid_traceparent_short_trace_id(self):
        """Test that short trace ID returns None."""
        from app.utils.tracer import parse_traceparent

        header = "00-4bf92f35-00f067aa0ba902b7-01"
        result = parse_traceparent(header)

        assert result is None

    def test_parse_invalid_traceparent_all_zeros_trace_id(self):
        """Test that all zeros trace ID returns None."""
        from app.utils.tracer import parse_traceparent

        header = "00-00000000000000000000000000000000-00f067aa0ba902b7-01"
        result = parse_traceparent(header)

        assert result is None

    def test_parse_invalid_traceparent_all_zeros_span_id(self):
        """Test that all zeros span ID returns None."""
        from app.utils.tracer import parse_traceparent

        header = "00-4bf92f3577b34da6a3ce929d0e0e4736-0000000000000000-01"
        result = parse_traceparent(header)

        assert result is None

    def test_format_traceparent(self):
        """Test formatting a traceparent header."""
        from app.utils.tracer import format_traceparent, Tracer

        tracer = Tracer()
        span = tracer.start_span("test-span")

        header = format_traceparent(span.trace_id, span.span_id, sampled=True)

        assert header.startswith("00-")
        assert span.trace_id in header
        assert span.span_id in header
        assert header.endswith("-01")

    def test_format_traceparent_not_sampled(self):
        """Test formatting a traceparent header with not sampled."""
        from app.utils.tracer import format_traceparent

        header = format_traceparent(
            "4bf92f3577b34da6a3ce929d0e0e4736",
            "00f067aa0ba902b7",
            sampled=False
        )

        assert header == "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-00"


class TestW3CTracestateHeaderParsing:
    """Tests for W3C tracestate header parsing."""

    def test_parse_valid_tracestate(self):
        """Test parsing a valid W3C tracestate header."""
        from app.utils.tracer import parse_tracestate

        header = "vendor1=value1,vendor2=value2"
        result = parse_tracestate(header)

        assert result == {"vendor1": "value1", "vendor2": "value2"}

    def test_parse_empty_tracestate(self):
        """Test parsing an empty tracestate header."""
        from app.utils.tracer import parse_tracestate

        result = parse_tracestate("")

        assert result == {}

    def test_parse_tracestate_with_spaces(self):
        """Test parsing tracestate with spaces around values."""
        from app.utils.tracer import parse_tracestate

        header = "vendor1=value1 , vendor2=value2"
        result = parse_tracestate(header)

        assert result == {"vendor1": "value1", "vendor2": "value2"}

    def test_format_tracestate(self):
        """Test formatting a tracestate header."""
        from app.utils.tracer import format_tracestate

        state = {"vendor1": "value1", "vendor2": "value2"}
        header = format_tracestate(state)

        # Order may vary, so check both possibilities
        assert header in [
            "vendor1=value1,vendor2=value2",
            "vendor2=value2,vendor1=value1"
        ]


class TestContextPropagation:
    """Tests for context propagation."""

    def test_current_span_context_var(self):
        """Test that current span is stored in context variable."""
        from app.utils.tracer import Tracer, get_current_span

        tracer = Tracer()
        span = tracer.start_span("test-span")

        current = get_current_span()
        assert current == span

    def test_current_span_none_initially(self):
        """Test that current span is None initially."""
        from app.utils.tracer import current_span

        # Reset the context var
        current_span.set(None)

        from app.utils.tracer import get_current_span
        assert get_current_span() is None

    def test_context_propagation_nested_spans(self):
        """Test that context propagates correctly through nested spans."""
        from app.utils.tracer import Tracer, get_current_span

        tracer = Tracer()

        with tracer.start_span("parent") as parent:
            assert get_current_span() == parent

            with tracer.start_span("child", parent=parent) as child:
                assert get_current_span() == child

            # After child ends, parent should be current again
            assert get_current_span() == parent

    def test_extract_context_from_headers(self):
        """Test extracting trace context from HTTP headers."""
        from app.utils.tracer import extract_context

        headers = {
            "traceparent": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
            "tracestate": "vendor1=value1"
        }

        context = extract_context(headers)

        assert context is not None
        assert context.trace_id == "4bf92f3577b34da6a3ce929d0e0e4736"
        assert context.parent_span_id == "00f067aa0ba902b7"

    def test_inject_context_to_headers(self):
        """Test injecting trace context to HTTP headers."""
        from app.utils.tracer import Tracer, inject_context

        tracer = Tracer()
        span = tracer.start_span("test-span")

        headers = {}
        inject_context(span, headers)

        assert "traceparent" in headers
        assert span.trace_id in headers["traceparent"]
        assert span.span_id in headers["traceparent"]


class TestTracerConfiguration:
    """Tests for tracer configuration."""

    def test_tracer_service_name(self):
        """Test that tracer has a service name."""
        from app.utils.tracer import Tracer

        tracer = Tracer(service_name="my-service")

        assert tracer.service_name == "my-service"

    def test_tracer_default_service_name(self):
        """Test that tracer has default service name."""
        from app.utils.tracer import Tracer

        tracer = Tracer()

        assert tracer.service_name == "strong_mvp"

    def test_global_tracer_instance(self):
        """Test that global tracer instance exists."""
        from app.utils.tracer import tracer

        assert tracer is not None
        assert tracer.service_name == "strong_mvp"

    def test_tracer_records_spans(self):
        """Test that tracer records created spans."""
        from app.utils.tracer import Tracer

        tracer = Tracer()
        span1 = tracer.start_span("span1")
        span2 = tracer.start_span("span2")

        spans = tracer.get_finished_spans()
        # Spans are not finished yet
        assert len(spans) == 0

        span1.end()
        span2.end()

        spans = tracer.get_finished_spans()
        assert len(spans) == 2

    def test_tracer_clear_spans(self):
        """Test clearing recorded spans."""
        from app.utils.tracer import Tracer

        tracer = Tracer()
        span = tracer.start_span("test-span")
        span.end()

        assert len(tracer.get_finished_spans()) == 1

        tracer.clear_spans()

        assert len(tracer.get_finished_spans()) == 0


class TestSpanToDict:
    """Tests for span serialization to dictionary."""

    def test_span_to_dict_basic(self):
        """Test converting span to dictionary."""
        from app.utils.tracer import Tracer

        tracer = Tracer()
        span = tracer.start_span("test-span")
        span.end()

        data = span.to_dict()

        assert "trace_id" in data
        assert "span_id" in data
        assert "name" in data
        assert "start_time" in data
        assert "end_time" in data
        assert "duration_ms" in data

    def test_span_to_dict_with_parent(self):
        """Test converting span with parent to dictionary."""
        from app.utils.tracer import Tracer

        tracer = Tracer()
        parent = tracer.start_span("parent")
        child = tracer.start_span("child", parent=parent)
        child.end()

        data = child.to_dict()

        assert data["parent_span_id"] == parent.span_id

    def test_span_to_dict_with_attributes(self):
        """Test converting span with attributes to dictionary."""
        from app.utils.tracer import Tracer

        tracer = Tracer()
        span = tracer.start_span("test-span")
        span.set_attribute("key", "value")
        span.end()

        data = span.to_dict()

        assert data["attributes"]["key"] == "value"

    def test_span_to_dict_with_events(self):
        """Test converting span with events to dictionary."""
        from app.utils.tracer import Tracer

        tracer = Tracer()
        span = tracer.start_span("test-span")
        span.add_event("test_event", {"key": "value"})
        span.end()

        data = span.to_dict()

        assert len(data["events"]) == 1
        assert data["events"][0]["name"] == "test_event"


class TestTracingMiddleware:
    """Tests for tracing middleware."""

    @pytest.mark.asyncio
    async def test_middleware_creates_span_for_request(self):
        """Test that middleware creates a span for each request."""
        from app.middleware.tracing import TracingMiddleware
        from app.utils.tracer import Tracer
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        app = FastAPI()
        test_tracer = Tracer()
        app.add_middleware(TracingMiddleware, tracer=test_tracer)

        @app.get("/test")
        async def test_endpoint():
            return {"status": "ok"}

        client = TestClient(app)
        response = client.get("/test")

        spans = test_tracer.get_finished_spans()
        assert len(spans) >= 1
        assert any(span.name == "HTTP GET /test" for span in spans)

    @pytest.mark.asyncio
    async def test_middleware_sets_http_attributes(self):
        """Test that middleware sets HTTP attributes on span."""
        from app.middleware.tracing import TracingMiddleware
        from app.utils.tracer import Tracer
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        app = FastAPI()
        test_tracer = Tracer()
        app.add_middleware(TracingMiddleware, tracer=test_tracer)

        @app.get("/api/users")
        async def test_endpoint():
            return {"status": "ok"}

        client = TestClient(app)
        response = client.get("/api/users")

        spans = test_tracer.get_finished_spans()
        span = spans[0]

        assert span.attributes.get("http.method") == "GET"
        assert span.attributes.get("http.url") == "/api/users"
        assert span.attributes.get("http.status_code") == 200

    @pytest.mark.asyncio
    async def test_middleware_propagates_traceparent(self):
        """Test that middleware propagates traceparent header."""
        from app.middleware.tracing import TracingMiddleware
        from app.utils.tracer import Tracer
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        app = FastAPI()
        test_tracer = Tracer()
        app.add_middleware(TracingMiddleware, tracer=test_tracer)

        @app.get("/test")
        async def test_endpoint():
            return {"status": "ok"}

        trace_id = "4bf92f3577b34da6a3ce929d0e0e4736"
        parent_span_id = "00f067aa0ba902b7"
        traceparent = f"00-{trace_id}-{parent_span_id}-01"

        client = TestClient(app)
        response = client.get("/test", headers={"traceparent": traceparent})

        spans = test_tracer.get_finished_spans()
        span = spans[0]

        assert span.trace_id == trace_id
        assert span.parent_span_id == parent_span_id

    @pytest.mark.asyncio
    async def test_middleware_returns_traceparent_header(self):
        """Test that middleware returns traceparent in response."""
        from app.middleware.tracing import TracingMiddleware
        from app.utils.tracer import Tracer
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        app = FastAPI()
        test_tracer = Tracer()
        app.add_middleware(TracingMiddleware, tracer=test_tracer)

        @app.get("/test")
        async def test_endpoint():
            return {"status": "ok"}

        client = TestClient(app)
        response = client.get("/test")

        assert "traceparent" in response.headers

    @pytest.mark.asyncio
    async def test_middleware_handles_errors(self):
        """Test that middleware handles errors gracefully."""
        from app.middleware.tracing import TracingMiddleware
        from app.utils.tracer import Tracer, SpanStatus
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        app = FastAPI()
        test_tracer = Tracer()
        app.add_middleware(TracingMiddleware, tracer=test_tracer)

        @app.get("/error")
        async def error_endpoint():
            raise ValueError("Test error")

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/error")

        spans = test_tracer.get_finished_spans()
        span = spans[0]

        assert span.status == SpanStatus.ERROR
        assert any(event.name == "exception" for event in span.events)

    @pytest.mark.asyncio
    async def test_middleware_excludes_health_endpoint(self):
        """Test that middleware excludes health endpoint from tracing."""
        from app.middleware.tracing import TracingMiddleware
        from app.utils.tracer import Tracer
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        app = FastAPI()
        test_tracer = Tracer()
        app.add_middleware(TracingMiddleware, tracer=test_tracer)

        @app.get("/health")
        async def health_endpoint():
            return {"status": "healthy"}

        client = TestClient(app)
        response = client.get("/health")

        spans = test_tracer.get_finished_spans()
        assert not any(span.name == "HTTP GET /health" for span in spans)


class TestThreadSafety:
    """Tests for thread safety of tracing."""

    def test_span_creation_thread_safe(self):
        """Test that span creation is thread-safe."""
        from app.utils.tracer import Tracer

        tracer = Tracer()
        spans = []
        errors = []
        lock = threading.Lock()

        def create_span(i):
            try:
                span = tracer.start_span(f"span-{i}")
                span.set_attribute("index", i)
                span.end()
                with lock:
                    spans.append(span)
            except Exception as e:
                with lock:
                    errors.append(e)

        threads = [threading.Thread(target=create_span, args=(i,)) for i in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert len(spans) == 50

        span_ids = {span.span_id for span in spans}
        assert len(span_ids) == 50  # All unique

    def test_tracer_get_spans_thread_safe(self):
        """Test that getting spans is thread-safe."""
        from app.utils.tracer import Tracer

        tracer = Tracer()
        errors = []
        results = []
        lock = threading.Lock()

        # Create some spans first
        for i in range(10):
            span = tracer.start_span(f"span-{i}")
            span.end()

        def get_spans():
            try:
                spans = tracer.get_finished_spans()
                with lock:
                    results.append(len(spans))
            except Exception as e:
                with lock:
                    errors.append(e)

        threads = [threading.Thread(target=get_spans) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert all(r == 10 for r in results)
