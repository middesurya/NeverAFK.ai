"""
Tests for structured logging with correlation IDs (PRD-013).

TDD RED Phase - Tests written before implementation.
"""

import pytest
import json
import logging
import io
import sys
import re
import uuid
import time
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime
from contextlib import redirect_stdout


class TestJSONFormat:
    """Tests for AC-1: Log output is valid JSON with timestamp, level, message."""

    def test_json_format_basic_log(self):
        """Test that log output is valid JSON."""
        from app.utils.logger import get_logger, StructuredFormatter

        # Create a StringIO to capture log output
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(StructuredFormatter())

        logger = logging.getLogger("test_json_basic")
        logger.setLevel(logging.INFO)
        logger.handlers = []
        logger.addHandler(handler)

        logger.info("Test message")

        output = stream.getvalue()
        log_entry = json.loads(output.strip())

        assert isinstance(log_entry, dict), "Log output should be valid JSON object"

    def test_json_format_contains_timestamp(self):
        """Test that log output contains timestamp field."""
        from app.utils.logger import get_logger, StructuredFormatter

        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(StructuredFormatter())

        logger = logging.getLogger("test_json_timestamp")
        logger.setLevel(logging.INFO)
        logger.handlers = []
        logger.addHandler(handler)

        logger.info("Test message")

        output = stream.getvalue()
        log_entry = json.loads(output.strip())

        assert "timestamp" in log_entry, "Log should contain timestamp field"
        assert log_entry["timestamp"].endswith("Z"), "Timestamp should be in ISO format with Z suffix"

    def test_json_format_contains_level(self):
        """Test that log output contains level field."""
        from app.utils.logger import get_logger, StructuredFormatter

        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(StructuredFormatter())

        logger = logging.getLogger("test_json_level")
        logger.setLevel(logging.INFO)
        logger.handlers = []
        logger.addHandler(handler)

        logger.info("Test message")

        output = stream.getvalue()
        log_entry = json.loads(output.strip())

        assert "level" in log_entry, "Log should contain level field"
        assert log_entry["level"] == "INFO", "Level should match log level"

    def test_json_format_contains_message(self):
        """Test that log output contains message field."""
        from app.utils.logger import get_logger, StructuredFormatter

        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(StructuredFormatter())

        logger = logging.getLogger("test_json_message")
        logger.setLevel(logging.INFO)
        logger.handlers = []
        logger.addHandler(handler)

        test_message = "This is a test message"
        logger.info(test_message)

        output = stream.getvalue()
        log_entry = json.loads(output.strip())

        assert "message" in log_entry, "Log should contain message field"
        assert log_entry["message"] == test_message, "Message should match logged message"

    def test_json_format_warning_level(self):
        """Test that warning level is correctly captured."""
        from app.utils.logger import get_logger, StructuredFormatter

        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(StructuredFormatter())

        logger = logging.getLogger("test_json_warning")
        logger.setLevel(logging.WARNING)
        logger.handlers = []
        logger.addHandler(handler)

        logger.warning("Warning message")

        output = stream.getvalue()
        log_entry = json.loads(output.strip())

        assert log_entry["level"] == "WARNING", "Level should be WARNING"

    def test_json_format_error_level(self):
        """Test that error level is correctly captured."""
        from app.utils.logger import get_logger, StructuredFormatter

        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(StructuredFormatter())

        logger = logging.getLogger("test_json_error")
        logger.setLevel(logging.ERROR)
        logger.handlers = []
        logger.addHandler(handler)

        logger.error("Error message")

        output = stream.getvalue()
        log_entry = json.loads(output.strip())

        assert log_entry["level"] == "ERROR", "Level should be ERROR"

    def test_json_format_debug_level(self):
        """Test that debug level is correctly captured."""
        from app.utils.logger import get_logger, StructuredFormatter

        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(StructuredFormatter())

        logger = logging.getLogger("test_json_debug")
        logger.setLevel(logging.DEBUG)
        logger.handlers = []
        logger.addHandler(handler)

        logger.debug("Debug message")

        output = stream.getvalue()
        log_entry = json.loads(output.strip())

        assert log_entry["level"] == "DEBUG", "Level should be DEBUG"

    def test_json_format_contains_module_info(self):
        """Test that log contains module and function info."""
        from app.utils.logger import get_logger, StructuredFormatter

        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(StructuredFormatter())

        logger = logging.getLogger("test_json_module")
        logger.setLevel(logging.INFO)
        logger.handlers = []
        logger.addHandler(handler)

        logger.info("Test message")

        output = stream.getvalue()
        log_entry = json.loads(output.strip())

        assert "module" in log_entry, "Log should contain module field"
        assert "function" in log_entry, "Log should contain function field"
        assert "line" in log_entry, "Log should contain line field"

    def test_json_format_logger_name(self):
        """Test that logger name is included in output."""
        from app.utils.logger import get_logger, StructuredFormatter

        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(StructuredFormatter())

        logger_name = "test_json_logger_name"
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)
        logger.handlers = []
        logger.addHandler(handler)

        logger.info("Test message")

        output = stream.getvalue()
        log_entry = json.loads(output.strip())

        assert "logger" in log_entry, "Log should contain logger field"
        assert log_entry["logger"] == logger_name, "Logger name should match"

    def test_json_format_timestamp_iso_format(self):
        """Test that timestamp is in proper ISO format."""
        from app.utils.logger import get_logger, StructuredFormatter

        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(StructuredFormatter())

        logger = logging.getLogger("test_json_iso")
        logger.setLevel(logging.INFO)
        logger.handlers = []
        logger.addHandler(handler)

        logger.info("Test message")

        output = stream.getvalue()
        log_entry = json.loads(output.strip())

        timestamp = log_entry["timestamp"]
        # Should be parseable as ISO format
        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        assert True, "Timestamp should be valid ISO format"


class TestCorrelationID:
    """Tests for AC-2: Correlation ID generated and included in all logs."""

    def test_correlation_id_generated(self):
        """Test that correlation ID can be generated."""
        from app.utils.logger import set_correlation_id, get_correlation_id

        cid = set_correlation_id()

        assert cid is not None, "Correlation ID should be generated"
        # Should be a valid UUID format
        try:
            uuid.UUID(cid)
            valid = True
        except ValueError:
            valid = False
        assert valid, "Correlation ID should be valid UUID format"

    def test_correlation_id_custom_value(self):
        """Test that custom correlation ID can be set."""
        from app.utils.logger import set_correlation_id, get_correlation_id

        custom_id = "custom-correlation-123"
        set_correlation_id(custom_id)

        result = get_correlation_id()
        assert result == custom_id, "Custom correlation ID should be retrievable"

    def test_correlation_id_unique(self):
        """Test that generated correlation IDs are unique."""
        from app.utils.logger import set_correlation_id

        ids = set()
        for _ in range(100):
            cid = set_correlation_id()
            ids.add(cid)

        assert len(ids) == 100, "All generated correlation IDs should be unique"

    def test_correlation_id_in_log(self):
        """Test that correlation ID appears in log output."""
        from app.utils.logger import (
            get_logger, StructuredFormatter,
            set_correlation_id, get_correlation_id
        )

        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(StructuredFormatter())

        logger = logging.getLogger("test_cid_in_log")
        logger.setLevel(logging.INFO)
        logger.handlers = []
        logger.addHandler(handler)

        test_cid = "test-correlation-id-12345"
        set_correlation_id(test_cid)

        logger.info("Test message with correlation ID")

        output = stream.getvalue()
        log_entry = json.loads(output.strip())

        assert "correlation_id" in log_entry, "Log should contain correlation_id field"
        assert log_entry["correlation_id"] == test_cid, "Correlation ID should match set value"

    def test_correlation_id_propagates_across_logs(self):
        """Test that same correlation ID appears in multiple logs."""
        from app.utils.logger import (
            get_logger, StructuredFormatter,
            set_correlation_id, correlation_id_var
        )

        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(StructuredFormatter())

        logger = logging.getLogger("test_cid_propagate")
        logger.setLevel(logging.INFO)
        logger.handlers = []
        logger.addHandler(handler)

        test_cid = "propagate-correlation-id"
        set_correlation_id(test_cid)

        logger.info("First message")
        logger.info("Second message")
        logger.info("Third message")

        output = stream.getvalue()
        lines = output.strip().split('\n')

        for line in lines:
            log_entry = json.loads(line)
            assert log_entry["correlation_id"] == test_cid, "All logs should have same correlation ID"

    def test_correlation_id_empty_by_default(self):
        """Test that correlation ID is empty when not set."""
        from app.utils.logger import get_correlation_id, correlation_id_var

        # Reset correlation ID
        correlation_id_var.set('')

        result = get_correlation_id()
        assert result == '', "Correlation ID should be empty when not set"

    def test_correlation_id_uuid_format(self):
        """Test that generated correlation ID is valid UUID."""
        from app.utils.logger import set_correlation_id

        cid = set_correlation_id()

        # Validate UUID format
        pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        assert re.match(pattern, cid, re.IGNORECASE), "Correlation ID should be valid UUID format"

    def test_correlation_id_not_in_log_when_empty(self):
        """Test that correlation_id field is not present when not set."""
        from app.utils.logger import (
            get_logger, StructuredFormatter, correlation_id_var
        )

        # Reset correlation ID
        correlation_id_var.set('')

        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(StructuredFormatter())

        logger = logging.getLogger("test_cid_empty")
        logger.setLevel(logging.INFO)
        logger.handlers = []
        logger.addHandler(handler)

        logger.info("Test message without correlation ID")

        output = stream.getvalue()
        log_entry = json.loads(output.strip())

        # When correlation_id is empty string, it should not be included
        assert "correlation_id" not in log_entry or log_entry.get("correlation_id") == '', \
            "correlation_id should not be present or should be empty when not set"


class TestRequestLog:
    """Tests for AC-3: Request/response log includes duration, status, path."""

    @pytest.mark.asyncio
    async def test_request_log_includes_path(self):
        """Test that request log includes path."""
        from app.middleware.logging import LoggingMiddleware
        from app.utils.logger import StructuredFormatter, set_correlation_id, correlation_id_var
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        # Reset correlation ID
        correlation_id_var.set('')

        app = FastAPI()
        app.add_middleware(LoggingMiddleware)

        @app.get("/test/path")
        async def test_endpoint():
            return {"status": "ok"}

        # Capture logs
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(StructuredFormatter())

        logger = logging.getLogger("app.middleware.logging")
        logger.setLevel(logging.INFO)
        original_handlers = logger.handlers.copy()
        logger.handlers = []
        logger.addHandler(handler)

        try:
            client = TestClient(app)
            response = client.get("/test/path")

            output = stream.getvalue()
            assert "/test/path" in output, "Log should contain request path"
        finally:
            logger.handlers = original_handlers

    @pytest.mark.asyncio
    async def test_request_log_includes_method(self):
        """Test that request log includes HTTP method."""
        from app.middleware.logging import LoggingMiddleware
        from app.utils.logger import StructuredFormatter, correlation_id_var
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        correlation_id_var.set('')

        app = FastAPI()
        app.add_middleware(LoggingMiddleware)

        @app.post("/test/method")
        async def test_endpoint():
            return {"status": "ok"}

        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(StructuredFormatter())

        logger = logging.getLogger("app.middleware.logging")
        logger.setLevel(logging.INFO)
        original_handlers = logger.handlers.copy()
        logger.handlers = []
        logger.addHandler(handler)

        try:
            client = TestClient(app)
            response = client.post("/test/method")

            output = stream.getvalue()
            assert "POST" in output, "Log should contain HTTP method"
        finally:
            logger.handlers = original_handlers

    @pytest.mark.asyncio
    async def test_request_log_includes_status_code(self):
        """Test that request log includes status code."""
        from app.middleware.logging import LoggingMiddleware
        from app.utils.logger import StructuredFormatter, correlation_id_var
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        correlation_id_var.set('')

        app = FastAPI()
        app.add_middleware(LoggingMiddleware)

        @app.get("/test/status")
        async def test_endpoint():
            return {"status": "ok"}

        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(StructuredFormatter())

        logger = logging.getLogger("app.middleware.logging")
        logger.setLevel(logging.INFO)
        original_handlers = logger.handlers.copy()
        logger.handlers = []
        logger.addHandler(handler)

        try:
            client = TestClient(app)
            response = client.get("/test/status")

            output = stream.getvalue()
            # Look for status_code in JSON
            assert "status_code" in output, "Log should contain status_code field"
            assert "200" in output, "Log should contain status code 200"
        finally:
            logger.handlers = original_handlers

    @pytest.mark.asyncio
    async def test_request_log_includes_duration(self):
        """Test that request log includes duration in milliseconds."""
        from app.middleware.logging import LoggingMiddleware
        from app.utils.logger import StructuredFormatter, correlation_id_var
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        correlation_id_var.set('')

        app = FastAPI()
        app.add_middleware(LoggingMiddleware)

        @app.get("/test/duration")
        async def test_endpoint():
            return {"status": "ok"}

        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(StructuredFormatter())

        logger = logging.getLogger("app.middleware.logging")
        logger.setLevel(logging.INFO)
        original_handlers = logger.handlers.copy()
        logger.handlers = []
        logger.addHandler(handler)

        try:
            client = TestClient(app)
            response = client.get("/test/duration")

            output = stream.getvalue()
            assert "duration_ms" in output, "Log should contain duration_ms field"
        finally:
            logger.handlers = original_handlers

    @pytest.mark.asyncio
    async def test_request_log_correlation_id_in_response(self):
        """Test that correlation ID is returned in response header."""
        from app.middleware.logging import LoggingMiddleware
        from app.utils.logger import correlation_id_var
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        correlation_id_var.set('')

        app = FastAPI()
        app.add_middleware(LoggingMiddleware)

        @app.get("/test/correlation")
        async def test_endpoint():
            return {"status": "ok"}

        client = TestClient(app)
        response = client.get("/test/correlation")

        assert "X-Correlation-ID" in response.headers, "Response should contain X-Correlation-ID header"

    @pytest.mark.asyncio
    async def test_request_log_uses_provided_correlation_id(self):
        """Test that provided correlation ID is used from request header."""
        from app.middleware.logging import LoggingMiddleware
        from app.utils.logger import correlation_id_var
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        correlation_id_var.set('')

        app = FastAPI()
        app.add_middleware(LoggingMiddleware)

        @app.get("/test/provided-cid")
        async def test_endpoint():
            return {"status": "ok"}

        provided_cid = "provided-correlation-id-xyz"
        client = TestClient(app)
        response = client.get("/test/provided-cid", headers={"X-Correlation-ID": provided_cid})

        assert response.headers.get("X-Correlation-ID") == provided_cid, \
            "Response should contain the provided correlation ID"

    @pytest.mark.asyncio
    async def test_request_log_request_started_event(self):
        """Test that request started event is logged."""
        from app.middleware.logging import LoggingMiddleware
        from app.utils.logger import StructuredFormatter, correlation_id_var
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        correlation_id_var.set('')

        app = FastAPI()
        app.add_middleware(LoggingMiddleware)

        @app.get("/test/started")
        async def test_endpoint():
            return {"status": "ok"}

        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(StructuredFormatter())

        logger = logging.getLogger("app.middleware.logging")
        logger.setLevel(logging.INFO)
        original_handlers = logger.handlers.copy()
        logger.handlers = []
        logger.addHandler(handler)

        try:
            client = TestClient(app)
            response = client.get("/test/started")

            output = stream.getvalue()
            assert "request_started" in output, "Log should contain request_started event"
        finally:
            logger.handlers = original_handlers

    @pytest.mark.asyncio
    async def test_request_log_request_completed_event(self):
        """Test that request completed event is logged."""
        from app.middleware.logging import LoggingMiddleware
        from app.utils.logger import StructuredFormatter, correlation_id_var
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        correlation_id_var.set('')

        app = FastAPI()
        app.add_middleware(LoggingMiddleware)

        @app.get("/test/completed")
        async def test_endpoint():
            return {"status": "ok"}

        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(StructuredFormatter())

        logger = logging.getLogger("app.middleware.logging")
        logger.setLevel(logging.INFO)
        original_handlers = logger.handlers.copy()
        logger.handlers = []
        logger.addHandler(handler)

        try:
            client = TestClient(app)
            response = client.get("/test/completed")

            output = stream.getvalue()
            assert "request_completed" in output, "Log should contain request_completed event"
        finally:
            logger.handlers = original_handlers

    @pytest.mark.asyncio
    async def test_request_log_excludes_health_path(self):
        """Test that /health path is excluded from logging."""
        from app.middleware.logging import LoggingMiddleware
        from app.utils.logger import StructuredFormatter, correlation_id_var
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        correlation_id_var.set('')

        app = FastAPI()
        app.add_middleware(LoggingMiddleware)

        @app.get("/health")
        async def health_endpoint():
            return {"status": "healthy"}

        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(StructuredFormatter())

        logger = logging.getLogger("app.middleware.logging")
        logger.setLevel(logging.INFO)
        original_handlers = logger.handlers.copy()
        logger.handlers = []
        logger.addHandler(handler)

        try:
            client = TestClient(app)
            response = client.get("/health")

            output = stream.getvalue()
            # Health endpoint should not generate logs
            assert output.strip() == "" or "/health" not in output, \
                "Health endpoint should be excluded from logging"
        finally:
            logger.handlers = original_handlers

    @pytest.mark.asyncio
    async def test_request_log_includes_query_params(self):
        """Test that query parameters are included in log."""
        from app.middleware.logging import LoggingMiddleware
        from app.utils.logger import StructuredFormatter, correlation_id_var
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        correlation_id_var.set('')

        app = FastAPI()
        app.add_middleware(LoggingMiddleware)

        @app.get("/test/query")
        async def test_endpoint(param1: str = None):
            return {"param1": param1}

        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(StructuredFormatter())

        logger = logging.getLogger("app.middleware.logging")
        logger.setLevel(logging.INFO)
        original_handlers = logger.handlers.copy()
        logger.handlers = []
        logger.addHandler(handler)

        try:
            client = TestClient(app)
            response = client.get("/test/query?param1=value1")

            output = stream.getvalue()
            assert "param1=value1" in output, "Log should contain query parameters"
        finally:
            logger.handlers = original_handlers


class TestErrorLog:
    """Tests for AC-4: Error log includes stack trace and context."""

    def test_error_log_includes_exception_type(self):
        """Test that error log includes exception type."""
        from app.utils.logger import get_logger, StructuredFormatter

        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(StructuredFormatter())

        logger = logging.getLogger("test_error_type")
        logger.setLevel(logging.ERROR)
        logger.handlers = []
        logger.addHandler(handler)

        try:
            raise ValueError("Test error")
        except ValueError:
            logger.error("An error occurred", exc_info=True)

        output = stream.getvalue()
        log_entry = json.loads(output.strip())

        assert "exception" in log_entry, "Error log should contain exception field"
        assert log_entry["exception"]["type"] == "ValueError", "Should include exception type"

    def test_error_log_includes_exception_message(self):
        """Test that error log includes exception message."""
        from app.utils.logger import get_logger, StructuredFormatter

        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(StructuredFormatter())

        logger = logging.getLogger("test_error_message")
        logger.setLevel(logging.ERROR)
        logger.handlers = []
        logger.addHandler(handler)

        try:
            raise RuntimeError("Detailed error message")
        except RuntimeError:
            logger.error("An error occurred", exc_info=True)

        output = stream.getvalue()
        log_entry = json.loads(output.strip())

        assert log_entry["exception"]["message"] == "Detailed error message", \
            "Should include exception message"

    def test_error_log_includes_traceback(self):
        """Test that error log includes full traceback."""
        from app.utils.logger import get_logger, StructuredFormatter

        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(StructuredFormatter())

        logger = logging.getLogger("test_error_traceback")
        logger.setLevel(logging.ERROR)
        logger.handlers = []
        logger.addHandler(handler)

        try:
            raise KeyError("missing_key")
        except KeyError:
            logger.error("An error occurred", exc_info=True)

        output = stream.getvalue()
        log_entry = json.loads(output.strip())

        assert "traceback" in log_entry["exception"], "Should include traceback"
        assert "Traceback" in log_entry["exception"]["traceback"], "Traceback should be formatted"

    @pytest.mark.asyncio
    async def test_error_log_from_middleware(self):
        """Test that middleware logs errors with traceback."""
        from app.middleware.logging import LoggingMiddleware
        from app.utils.logger import StructuredFormatter, correlation_id_var
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        correlation_id_var.set('')

        app = FastAPI()
        app.add_middleware(LoggingMiddleware)

        @app.get("/test/error")
        async def error_endpoint():
            raise ValueError("Intentional error")

        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(StructuredFormatter())

        logger = logging.getLogger("app.middleware.logging")
        logger.setLevel(logging.ERROR)
        original_handlers = logger.handlers.copy()
        logger.handlers = []
        logger.addHandler(handler)

        try:
            client = TestClient(app, raise_server_exceptions=False)
            response = client.get("/test/error")

            output = stream.getvalue()
            # Should have logged the error
            if output:
                assert "request_error" in output or "ValueError" in output, \
                    "Error should be logged with event type or exception"
        finally:
            logger.handlers = original_handlers

    def test_error_log_nested_exception(self):
        """Test that nested exceptions are captured."""
        from app.utils.logger import get_logger, StructuredFormatter

        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(StructuredFormatter())

        logger = logging.getLogger("test_error_nested")
        logger.setLevel(logging.ERROR)
        logger.handlers = []
        logger.addHandler(handler)

        try:
            try:
                raise ValueError("Inner error")
            except ValueError:
                raise RuntimeError("Outer error")
        except RuntimeError:
            logger.error("Nested error occurred", exc_info=True)

        output = stream.getvalue()
        log_entry = json.loads(output.strip())

        assert log_entry["exception"]["type"] == "RuntimeError", "Should capture outer exception"
        assert "ValueError" in log_entry["exception"]["traceback"], \
            "Traceback should include inner exception info"

    def test_error_log_without_exception(self):
        """Test error logging without exception info."""
        from app.utils.logger import get_logger, StructuredFormatter

        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(StructuredFormatter())

        logger = logging.getLogger("test_error_no_exc")
        logger.setLevel(logging.ERROR)
        logger.handlers = []
        logger.addHandler(handler)

        logger.error("Error without exception")

        output = stream.getvalue()
        log_entry = json.loads(output.strip())

        assert "exception" not in log_entry, "Should not have exception field when no exc_info"
        assert log_entry["level"] == "ERROR", "Level should still be ERROR"


class TestSensitiveFieldFiltering:
    """Tests for sensitive field filtering in logs."""

    def test_password_filtered(self):
        """Test that password field is filtered from logs."""
        from app.utils.logger import get_logger, StructuredFormatter, StructuredLogger

        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(StructuredFormatter())

        logging.setLoggerClass(StructuredLogger)
        logger = logging.getLogger("test_filter_password")
        logger.setLevel(logging.INFO)
        logger.handlers = []
        logger.addHandler(handler)

        logger.info("Login attempt", extra={'extra_fields': {'username': 'testuser', 'password': 'secret123'}})

        output = stream.getvalue()
        log_entry = json.loads(output.strip())

        assert "password" not in log_entry, "Password should be filtered"
        assert "username" in log_entry, "Non-sensitive fields should be included"

    def test_token_filtered(self):
        """Test that token field is filtered from logs."""
        from app.utils.logger import get_logger, StructuredFormatter, StructuredLogger

        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(StructuredFormatter())

        logging.setLoggerClass(StructuredLogger)
        logger = logging.getLogger("test_filter_token")
        logger.setLevel(logging.INFO)
        logger.handlers = []
        logger.addHandler(handler)

        logger.info("API call", extra={'extra_fields': {'token': 'abc123', 'endpoint': '/api/data'}})

        output = stream.getvalue()
        log_entry = json.loads(output.strip())

        assert "token" not in log_entry, "Token should be filtered"
        assert "endpoint" in log_entry, "Non-sensitive fields should be included"

    def test_api_key_filtered(self):
        """Test that api_key field is filtered from logs."""
        from app.utils.logger import get_logger, StructuredFormatter, StructuredLogger

        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(StructuredFormatter())

        logging.setLoggerClass(StructuredLogger)
        logger = logging.getLogger("test_filter_api_key")
        logger.setLevel(logging.INFO)
        logger.handlers = []
        logger.addHandler(handler)

        logger.info("External call", extra={'extra_fields': {'api_key': 'key123', 'service': 'external'}})

        output = stream.getvalue()
        log_entry = json.loads(output.strip())

        assert "api_key" not in log_entry, "API key should be filtered"
        assert "service" in log_entry, "Non-sensitive fields should be included"

    def test_secret_filtered(self):
        """Test that secret field is filtered from logs."""
        from app.utils.logger import get_logger, StructuredFormatter, StructuredLogger

        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(StructuredFormatter())

        logging.setLoggerClass(StructuredLogger)
        logger = logging.getLogger("test_filter_secret")
        logger.setLevel(logging.INFO)
        logger.handlers = []
        logger.addHandler(handler)

        logger.info("Config loaded", extra={'extra_fields': {'secret': 'mysecret', 'env': 'production'}})

        output = stream.getvalue()
        log_entry = json.loads(output.strip())

        assert "secret" not in log_entry, "Secret should be filtered"
        assert "env" in log_entry, "Non-sensitive fields should be included"

    def test_authorization_filtered(self):
        """Test that authorization field is filtered from logs."""
        from app.utils.logger import get_logger, StructuredFormatter, StructuredLogger

        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(StructuredFormatter())

        logging.setLoggerClass(StructuredLogger)
        logger = logging.getLogger("test_filter_auth")
        logger.setLevel(logging.INFO)
        logger.handlers = []
        logger.addHandler(handler)

        logger.info("Request headers", extra={'extra_fields': {'authorization': 'Bearer xyz', 'content_type': 'application/json'}})

        output = stream.getvalue()
        log_entry = json.loads(output.strip())

        assert "authorization" not in log_entry, "Authorization should be filtered"
        assert "content_type" in log_entry, "Non-sensitive fields should be included"

    def test_case_insensitive_filtering(self):
        """Test that filtering is case-insensitive."""
        from app.utils.logger import get_logger, StructuredFormatter, StructuredLogger

        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(StructuredFormatter())

        logging.setLoggerClass(StructuredLogger)
        logger = logging.getLogger("test_filter_case")
        logger.setLevel(logging.INFO)
        logger.handlers = []
        logger.addHandler(handler)

        logger.info("Mixed case", extra={'extra_fields': {'PASSWORD': 'secret', 'Token': 'abc', 'API_KEY': 'key'}})

        output = stream.getvalue()
        log_entry = json.loads(output.strip())

        # All sensitive fields should be filtered regardless of case
        assert "PASSWORD" not in log_entry, "PASSWORD should be filtered"
        assert "Token" not in log_entry, "Token should be filtered"
        assert "API_KEY" not in log_entry, "API_KEY should be filtered"


class TestLogLevelConfiguration:
    """Tests for log level configuration."""

    def test_default_log_level_info(self):
        """Test that default log level is INFO."""
        from app.utils.logger import get_logger

        logger = get_logger("test_default_level")

        assert logger.level == logging.INFO, "Default log level should be INFO"

    def test_set_debug_level(self):
        """Test setting DEBUG log level."""
        from app.utils.logger import get_logger

        logger = get_logger("test_debug_level", level="DEBUG")

        assert logger.level == logging.DEBUG, "Log level should be DEBUG"

    def test_set_warning_level(self):
        """Test setting WARNING log level."""
        from app.utils.logger import get_logger

        logger = get_logger("test_warning_level", level="WARNING")

        assert logger.level == logging.WARNING, "Log level should be WARNING"

    def test_set_error_level(self):
        """Test setting ERROR log level."""
        from app.utils.logger import get_logger

        logger = get_logger("test_error_level", level="ERROR")

        assert logger.level == logging.ERROR, "Log level should be ERROR"

    def test_case_insensitive_level(self):
        """Test that level setting is case-insensitive."""
        from app.utils.logger import get_logger

        logger1 = get_logger("test_case_level1", level="debug")
        logger2 = get_logger("test_case_level2", level="DEBUG")
        logger3 = get_logger("test_case_level3", level="Debug")

        assert logger1.level == logging.DEBUG
        assert logger2.level == logging.DEBUG
        assert logger3.level == logging.DEBUG

    def test_debug_messages_filtered_at_info_level(self):
        """Test that debug messages are not logged at INFO level."""
        from app.utils.logger import get_logger, StructuredFormatter

        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(StructuredFormatter())

        logger = logging.getLogger("test_filter_debug")
        logger.setLevel(logging.INFO)
        logger.handlers = []
        logger.addHandler(handler)

        logger.debug("Debug message")
        logger.info("Info message")

        output = stream.getvalue()

        assert "Debug message" not in output, "Debug message should not be logged at INFO level"
        assert "Info message" in output, "Info message should be logged at INFO level"


class TestContextPreservation:
    """Tests for context preservation in logs."""

    def test_extra_fields_preserved(self):
        """Test that extra fields are preserved in log output."""
        from app.utils.logger import get_logger, StructuredFormatter, StructuredLogger

        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(StructuredFormatter())

        logging.setLoggerClass(StructuredLogger)
        logger = logging.getLogger("test_extra_fields")
        logger.setLevel(logging.INFO)
        logger.handlers = []
        logger.addHandler(handler)

        logger.info("Test message", extra={'extra_fields': {'user_id': '123', 'action': 'login'}})

        output = stream.getvalue()
        log_entry = json.loads(output.strip())

        assert log_entry.get("user_id") == "123", "Extra field user_id should be preserved"
        assert log_entry.get("action") == "login", "Extra field action should be preserved"

    def test_correlation_id_context_isolated(self):
        """Test that correlation ID context is properly isolated."""
        from app.utils.logger import set_correlation_id, get_correlation_id, correlation_id_var

        # Set a correlation ID
        cid1 = set_correlation_id("context-1")
        assert get_correlation_id() == "context-1"

        # Set a different correlation ID
        cid2 = set_correlation_id("context-2")
        assert get_correlation_id() == "context-2"

        # Reset
        correlation_id_var.set('')
        assert get_correlation_id() == ''

    def test_multiple_loggers_independent(self):
        """Test that multiple loggers work independently."""
        from app.utils.logger import get_logger, StructuredFormatter

        stream1 = io.StringIO()
        stream2 = io.StringIO()

        handler1 = logging.StreamHandler(stream1)
        handler1.setFormatter(StructuredFormatter())
        handler2 = logging.StreamHandler(stream2)
        handler2.setFormatter(StructuredFormatter())

        logger1 = logging.getLogger("test_logger_1")
        logger1.setLevel(logging.INFO)
        logger1.handlers = []
        logger1.addHandler(handler1)

        logger2 = logging.getLogger("test_logger_2")
        logger2.setLevel(logging.INFO)
        logger2.handlers = []
        logger2.addHandler(handler2)

        logger1.info("Message from logger 1")
        logger2.info("Message from logger 2")

        output1 = stream1.getvalue()
        output2 = stream2.getvalue()

        assert "Message from logger 1" in output1
        assert "Message from logger 2" in output2
        assert "Message from logger 2" not in output1
        assert "Message from logger 1" not in output2

    def test_formatter_thread_safe(self):
        """Test that formatter works correctly in multi-threaded context."""
        import threading
        from app.utils.logger import StructuredFormatter

        formatter = StructuredFormatter()
        errors = []
        results = []
        lock = threading.Lock()

        def log_message(msg_id):
            try:
                record = logging.LogRecord(
                    name=f"test_{msg_id}",
                    level=logging.INFO,
                    pathname="test.py",
                    lineno=1,
                    msg=f"Message {msg_id}",
                    args=(),
                    exc_info=None
                )
                output = formatter.format(record)
                log_entry = json.loads(output)
                with lock:
                    results.append((msg_id, log_entry))
            except Exception as e:
                with lock:
                    errors.append(e)

        threads = [threading.Thread(target=log_message, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"No errors should occur: {errors}"
        assert len(results) == 10, "All messages should be processed"


class TestDefaultLogger:
    """Tests for default logger instance."""

    def test_default_logger_exists(self):
        """Test that default logger instance is available."""
        from app.utils.logger import logger

        assert logger is not None, "Default logger should exist"
        assert isinstance(logger, logging.Logger), "Should be a Logger instance"

    def test_default_logger_named(self):
        """Test that default logger has correct name."""
        from app.utils.logger import logger

        assert logger.name == "strong_mvp", "Default logger should be named 'strong_mvp'"


class TestMiddlewareIntegration:
    """Tests for middleware integration with the application."""

    @pytest.mark.asyncio
    async def test_middleware_adds_correlation_header(self):
        """Test that middleware adds correlation ID to response headers."""
        from app.middleware.logging import LoggingMiddleware
        from app.utils.logger import correlation_id_var
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        correlation_id_var.set('')

        app = FastAPI()
        app.add_middleware(LoggingMiddleware)

        @app.get("/test")
        async def test_endpoint():
            return {"status": "ok"}

        client = TestClient(app)
        response = client.get("/test")

        assert "X-Correlation-ID" in response.headers
        # Should be a valid UUID
        cid = response.headers["X-Correlation-ID"]
        try:
            uuid.UUID(cid)
            valid = True
        except ValueError:
            valid = False
        assert valid, "Correlation ID in header should be valid UUID"

    @pytest.mark.asyncio
    async def test_middleware_preserves_request_correlation(self):
        """Test that middleware preserves correlation ID from request."""
        from app.middleware.logging import LoggingMiddleware
        from app.utils.logger import correlation_id_var
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        correlation_id_var.set('')

        app = FastAPI()
        app.add_middleware(LoggingMiddleware)

        @app.get("/test")
        async def test_endpoint():
            return {"status": "ok"}

        test_cid = "test-preserve-correlation-123"
        client = TestClient(app)
        response = client.get("/test", headers={"X-Correlation-ID": test_cid})

        assert response.headers["X-Correlation-ID"] == test_cid, \
            "Response should contain the same correlation ID from request"

    @pytest.mark.asyncio
    async def test_middleware_logs_client_ip(self):
        """Test that middleware logs client IP address."""
        from app.middleware.logging import LoggingMiddleware
        from app.utils.logger import StructuredFormatter, correlation_id_var
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        correlation_id_var.set('')

        app = FastAPI()
        app.add_middleware(LoggingMiddleware)

        @app.get("/test/ip")
        async def test_endpoint():
            return {"status": "ok"}

        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(StructuredFormatter())

        logger = logging.getLogger("app.middleware.logging")
        logger.setLevel(logging.INFO)
        original_handlers = logger.handlers.copy()
        logger.handlers = []
        logger.addHandler(handler)

        try:
            client = TestClient(app)
            response = client.get("/test/ip")

            output = stream.getvalue()
            assert "client_ip" in output, "Log should contain client_ip field"
        finally:
            logger.handlers = original_handlers

    @pytest.mark.asyncio
    async def test_middleware_excludes_metrics_path(self):
        """Test that /metrics path is excluded from logging."""
        from app.middleware.logging import LoggingMiddleware
        from app.utils.logger import StructuredFormatter, correlation_id_var
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        correlation_id_var.set('')

        app = FastAPI()
        app.add_middleware(LoggingMiddleware)

        @app.get("/metrics")
        async def metrics_endpoint():
            return {"metrics": "data"}

        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(StructuredFormatter())

        logger = logging.getLogger("app.middleware.logging")
        logger.setLevel(logging.INFO)
        original_handlers = logger.handlers.copy()
        logger.handlers = []
        logger.addHandler(handler)

        try:
            client = TestClient(app)
            response = client.get("/metrics")

            output = stream.getvalue()
            assert output.strip() == "" or "/metrics" not in output, \
                "Metrics endpoint should be excluded from logging"
        finally:
            logger.handlers = original_handlers

    @pytest.mark.asyncio
    async def test_middleware_excludes_favicon_path(self):
        """Test that /favicon.ico path is excluded from logging."""
        from app.middleware.logging import LoggingMiddleware
        from app.utils.logger import StructuredFormatter, correlation_id_var
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        correlation_id_var.set('')

        app = FastAPI()
        app.add_middleware(LoggingMiddleware)

        @app.get("/favicon.ico")
        async def favicon_endpoint():
            return {"icon": "data"}

        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(StructuredFormatter())

        logger = logging.getLogger("app.middleware.logging")
        logger.setLevel(logging.INFO)
        original_handlers = logger.handlers.copy()
        logger.handlers = []
        logger.addHandler(handler)

        try:
            client = TestClient(app)
            response = client.get("/favicon.ico")

            output = stream.getvalue()
            assert output.strip() == "" or "/favicon.ico" not in output, \
                "Favicon endpoint should be excluded from logging"
        finally:
            logger.handlers = original_handlers
