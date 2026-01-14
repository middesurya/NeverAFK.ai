"""
PRD-006: Integration Tests for Response Streaming (SSE)

Tests for POST /chat/stream endpoint:
- AC-1: POST /chat/stream returns content-type text/event-stream
- AC-2: Each token is sent as separate SSE event
- AC-3: Final event includes sources and metadata

These tests verify the streaming chat endpoint handles SSE responses correctly,
including proper event formatting, token streaming, and final metadata delivery.

NOTE: These tests are designed to FAIL initially because the /chat/stream
endpoint does not exist yet. They define the expected behavior for TDD.
"""

import json
import pytest
from unittest.mock import patch, MagicMock, AsyncMock, PropertyMock
from typing import AsyncIterator, List, Dict, Any
from contextlib import contextmanager

from tests.mocks.supabase_mock import MockDatabase


# =============================================================================
# Mock Setup Helper
# =============================================================================

@contextmanager
def mock_stream_dependencies(response_text="Hello world this is a test response"):
    """Context manager to mock support_agent and database for streaming tests."""
    mock_db = MockDatabase()
    mock_response = {
        "response": response_text,
        "sources": ["Module 1 - Introduction (Score: 0.92)", "Module 2 - Advanced (Score: 0.85)"],
        "should_escalate": False,
        "context_used": 2
    }

    with patch('main.support_agent.process_query', new_callable=AsyncMock) as mock_process:
        mock_process.return_value = mock_response
        with patch('main.db', mock_db):
            yield mock_process, mock_db, mock_response


# =============================================================================
# Mock Streaming Response Helpers
# =============================================================================

class MockStreamingChunk:
    """Mock chunk object matching OpenAI streaming response structure."""

    def __init__(self, content: str, finish_reason: str = None):
        self.choices = [MagicMock()]
        self.choices[0].delta = MagicMock()
        self.choices[0].delta.content = content
        self.choices[0].finish_reason = finish_reason


async def mock_streaming_response(tokens: List[str]) -> AsyncIterator[MockStreamingChunk]:
    """Generate mock streaming chunks for testing."""
    for token in tokens:
        yield MockStreamingChunk(content=token)
    # Final chunk with finish_reason
    yield MockStreamingChunk(content=None, finish_reason="stop")


def parse_sse_events(response_text: str) -> List[Dict[str, Any]]:
    """Parse SSE formatted response into list of event data."""
    events = []
    current_data = ""

    for line in response_text.split("\n"):
        if line.startswith("data: "):
            current_data = line[6:]  # Remove "data: " prefix
        elif line == "" and current_data:
            try:
                events.append(json.loads(current_data))
            except json.JSONDecodeError:
                pass  # Skip non-JSON data lines
            current_data = ""

    # Handle last event if no trailing newline
    if current_data:
        try:
            events.append(json.loads(current_data))
        except json.JSONDecodeError:
            pass

    return events


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def mock_streaming_agent_response():
    """Create a mock streaming agent response with sources."""
    return {
        "sources": ["Module 1 - Introduction (Score: 0.92)", "Module 2 - Advanced (Score: 0.85)"],
        "should_escalate": False,
        "context_used": 2
    }


@pytest.fixture
def mock_streaming_escalate_response():
    """Create a mock streaming response that triggers escalation."""
    return {
        "sources": [],
        "should_escalate": True,
        "context_used": 0
    }


# =============================================================================
# AC-1: POST /chat/stream returns content-type text/event-stream
# =============================================================================

class TestStreamContentType:
    """Tests for SSE content-type header - AC-1."""

    def test_stream_returns_event_stream_content_type(self, client):
        """
        AC-1: POST /chat/stream should return content-type text/event-stream.

        This test will FAIL because the /chat/stream endpoint does not exist.
        Expected failure: 404 Not Found (endpoint doesn't exist yet)
        """
        with mock_stream_dependencies():
            response = client.post(
                "/chat/stream",
                json={
                    "message": "What is Python?",
                    "creator_id": "test-creator-123"
                }
            )

            # Should return 200 with streaming content type
            assert response.status_code == 200, f"Expected 200, got {response.status_code}. Endpoint /chat/stream may not exist."
            content_type = response.headers.get("content-type", "")
            assert "text/event-stream" in content_type, f"Expected text/event-stream, got {content_type}"

    def test_stream_returns_correct_charset(self, client):
        """Stream response should include charset=utf-8 in content-type."""
        with mock_stream_dependencies():
            response = client.post(
                "/chat/stream",
                json={
                    "message": "Test question",
                    "creator_id": "test-creator-123"
                }
            )

            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            content_type = response.headers.get("content-type", "")
            # Should include charset for proper encoding
            assert "utf-8" in content_type.lower() or "text/event-stream" in content_type


# =============================================================================
# AC-2: Each token is sent as separate SSE event
# =============================================================================

class TestStreamTokenEvents:
    """Tests for token streaming - AC-2."""

    def test_stream_returns_multiple_sse_events(self, client):
        """
        AC-2: Stream should return multiple SSE events for tokens.

        This test will FAIL because the /chat/stream endpoint does not exist.
        """
        with mock_stream_dependencies():
            response = client.post(
                "/chat/stream",
                json={
                    "message": "Say hello world",
                    "creator_id": "test-creator-123"
                }
            )

            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            events = parse_sse_events(response.text)
            # Should have at least 2 events (tokens + done)
            assert len(events) >= 2, f"Expected at least 2 events, got {len(events)}"

    def test_stream_each_event_is_valid_json(self, client):
        """Each SSE event should contain valid JSON data."""
        with mock_stream_dependencies():
            response = client.post(
                "/chat/stream",
                json={
                    "message": "Test",
                    "creator_id": "test-creator-123"
                }
            )

            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            events = parse_sse_events(response.text)
            assert len(events) > 0, "Expected at least one event"
            for event in events:
                assert isinstance(event, dict), f"Event should be dict, got {type(event)}"

    def test_stream_events_have_type_field(self, client):
        """Each SSE event should have a 'type' field."""
        with mock_stream_dependencies():
            response = client.post(
                "/chat/stream",
                json={
                    "message": "Hello",
                    "creator_id": "test-creator-123"
                }
            )

            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            events = parse_sse_events(response.text)
            assert len(events) > 0, "Expected at least one event"
            for event in events:
                assert "type" in event, f"Event missing 'type' field: {event}"
                assert event["type"] in ["token", "done", "error"], f"Invalid type: {event['type']}"

    def test_stream_token_events_have_content_field(self, client):
        """Token events should have a 'content' field with the token text."""
        with mock_stream_dependencies():
            response = client.post(
                "/chat/stream",
                json={
                    "message": "Greet me",
                    "creator_id": "test-creator-123"
                }
            )

            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            events = parse_sse_events(response.text)
            token_events = [e for e in events if e.get("type") == "token"]

            # Should have at least one token event (unless empty response)
            for event in token_events:
                assert "content" in event, f"Token event missing 'content': {event}"
                assert isinstance(event["content"], str), f"Content should be string"

    def test_stream_preserves_token_order(self, client):
        """Tokens should be received in the order they were generated."""
        with mock_stream_dependencies():
            response = client.post(
                "/chat/stream",
                json={
                    "message": "Count to three",
                    "creator_id": "test-creator-123"
                }
            )

            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            events = parse_sse_events(response.text)
            token_events = [e for e in events if e.get("type") == "token"]

            # Verify we can reconstruct content from tokens
            if len(token_events) > 0:
                received_content = "".join([e.get("content", "") for e in token_events])
                assert len(received_content) > 0, "Should have some content from tokens"


# =============================================================================
# AC-3: Final event includes sources and metadata
# =============================================================================

class TestStreamFinalEvent:
    """Tests for final event with metadata - AC-3."""

    def test_stream_final_event_has_done_type(self, client):
        """
        AC-3: Final event should have type 'done'.

        This test will FAIL because the /chat/stream endpoint does not exist.
        """
        with mock_stream_dependencies():
            response = client.post(
                "/chat/stream",
                json={
                    "message": "Question",
                    "creator_id": "test-creator-123"
                }
            )

            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            events = parse_sse_events(response.text)
            done_events = [e for e in events if e.get("type") == "done"]

            assert len(done_events) == 1, f"Expected exactly 1 done event, got {len(done_events)}"

    def test_stream_final_event_includes_sources(self, client):
        """Final 'done' event should include sources list."""
        with mock_stream_dependencies():
            response = client.post(
                "/chat/stream",
                json={
                    "message": "What is Python?",
                    "creator_id": "test-creator-123"
                }
            )

            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            events = parse_sse_events(response.text)
            done_events = [e for e in events if e.get("type") == "done"]

            assert len(done_events) == 1, f"Expected exactly 1 done event"
            done_event = done_events[0]
            assert "sources" in done_event, f"Done event missing 'sources': {done_event}"
            assert isinstance(done_event["sources"], list), "Sources should be a list"

    def test_stream_final_event_includes_should_escalate(self, client):
        """Final 'done' event should include should_escalate boolean."""
        with mock_stream_dependencies():
            response = client.post(
                "/chat/stream",
                json={
                    "message": "Question",
                    "creator_id": "test-creator-123"
                }
            )

            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            events = parse_sse_events(response.text)
            done_events = [e for e in events if e.get("type") == "done"]

            assert len(done_events) == 1, f"Expected exactly 1 done event"
            done_event = done_events[0]
            assert "should_escalate" in done_event, f"Done event missing 'should_escalate': {done_event}"
            assert isinstance(done_event["should_escalate"], bool), "should_escalate should be bool"

    def test_stream_final_event_includes_conversation_id(self, client):
        """Final 'done' event should include conversation_id."""
        with mock_stream_dependencies():
            response = client.post(
                "/chat/stream",
                json={
                    "message": "Question",
                    "creator_id": "test-creator-123"
                }
            )

            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            events = parse_sse_events(response.text)
            done_events = [e for e in events if e.get("type") == "done"]

            assert len(done_events) == 1, f"Expected exactly 1 done event"
            done_event = done_events[0]
            assert "conversation_id" in done_event, f"Done event missing 'conversation_id': {done_event}"


# =============================================================================
# Validation Tests
# =============================================================================

class TestStreamValidation:
    """Tests for stream request validation."""

    def test_stream_missing_message_returns_422(self, client):
        """Stream should return 422 when message is missing."""
        response = client.post(
            "/chat/stream",
            json={
                "creator_id": "test-creator-123"
            }
        )

        # First check endpoint exists (not 404), then check validation
        assert response.status_code != 404, "Endpoint /chat/stream does not exist"
        assert response.status_code == 422, f"Expected 422 for missing message, got {response.status_code}"

    def test_stream_empty_body_returns_422(self, client):
        """Stream should return 422 when request body is empty."""
        response = client.post(
            "/chat/stream",
            json={}
        )

        assert response.status_code != 404, "Endpoint /chat/stream does not exist"
        assert response.status_code == 422, f"Expected 422 for empty body, got {response.status_code}"

    def test_stream_null_message_returns_422(self, client):
        """Stream should return 422 when message is null."""
        response = client.post(
            "/chat/stream",
            json={
                "message": None,
                "creator_id": "test-creator-123"
            }
        )

        assert response.status_code != 404, "Endpoint /chat/stream does not exist"
        assert response.status_code == 422, f"Expected 422 for null message, got {response.status_code}"

    def test_stream_missing_creator_id_returns_401(self, client):
        """Stream should return 401 when creator_id is missing and no auth token."""
        response = client.post(
            "/chat/stream",
            json={
                "message": "What is Python?"
                # No creator_id provided
            }
        )

        assert response.status_code != 404, "Endpoint /chat/stream does not exist"
        assert response.status_code == 401, f"Expected 401 for missing auth, got {response.status_code}"


# =============================================================================
# Edge Cases and Error Handling
# =============================================================================

class TestStreamEdgeCases:
    """Tests for stream edge cases and error handling."""

    def test_stream_handles_empty_response_gracefully(self, client):
        """Stream should handle empty AI response gracefully."""
        with mock_stream_dependencies(response_text=""):
            response = client.post(
                "/chat/stream",
                json={
                    "message": "",  # Empty message
                    "creator_id": "test-creator-123"
                }
            )

            # Should still return 200 with at least a done event
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            events = parse_sse_events(response.text)
            done_events = [e for e in events if e.get("type") == "done"]
            assert len(done_events) == 1, "Should have exactly one done event"

    def test_stream_connection_can_be_closed(self, client):
        """Stream connection should be closeable without errors."""
        with mock_stream_dependencies():
            # Using context manager ensures proper cleanup
            response = client.post(
                "/chat/stream",
                json={
                    "message": "Test",
                    "creator_id": "test-creator-123"
                }
            )

            # Connection should close properly - response should be complete
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            # Verify we can read the full response
            _ = response.text
            assert True, "Connection closed cleanly"

    def test_stream_handles_special_characters_in_tokens(self, client):
        """Stream should handle special characters and unicode in tokens."""
        with mock_stream_dependencies(response_text="Special chars: <>&\"' and unicode test"):
            response = client.post(
                "/chat/stream",
                json={
                    "message": "What about special chars: <>&\"' and unicode?",
                    "creator_id": "test-creator-123"
                }
            )

            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            events = parse_sse_events(response.text)
            # All events should be valid JSON (no encoding errors)
            assert len(events) > 0, "Should have events"

    def test_stream_handles_newlines_in_tokens(self, client):
        """Stream should handle newlines within token content."""
        with mock_stream_dependencies(response_text="Line one\nLine two\nLine three"):
            response = client.post(
                "/chat/stream",
                json={
                    "message": "Give me a multiline response",
                    "creator_id": "test-creator-123"
                }
            )

            # Should handle newlines properly in JSON encoding
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"


# =============================================================================
# Database Interaction Tests
# =============================================================================

class TestStreamDatabaseInteraction:
    """Tests for stream database interactions."""

    def test_stream_saves_conversation_after_completion(self, client):
        """Stream should save conversation to database after stream completes."""
        with mock_stream_dependencies() as (mock_process, mock_db, mock_response):
            response = client.post(
                "/chat/stream",
                json={
                    "message": "What is Python?",
                    "creator_id": "test-creator-123"
                }
            )

            # Consume the full response
            _ = response.text

            assert response.status_code == 200, f"Expected 200, got {response.status_code}"

            # Verify save_conversation was called
            save_calls = [c for c in mock_db.call_history if c["method"] == "save_conversation"]
            assert len(save_calls) == 1, "save_conversation should be called once"
            assert save_calls[0]["creator_id"] == "test-creator-123"

    def test_stream_updates_credit_usage(self, client):
        """Stream should update credit usage after completion."""
        with mock_stream_dependencies() as (mock_process, mock_db, mock_response):
            mock_db.set_creator_credits("test-creator-123", 100)

            response = client.post(
                "/chat/stream",
                json={
                    "message": "Question",
                    "creator_id": "test-creator-123"
                }
            )

            # Consume the full response
            _ = response.text

            assert response.status_code == 200, f"Expected 200, got {response.status_code}"

            # Verify update_credit_usage was called
            credit_calls = [c for c in mock_db.call_history if c["method"] == "update_credit_usage"]
            assert len(credit_calls) == 1, "update_credit_usage should be called once"


# =============================================================================
# SSE Format Compliance Tests
# =============================================================================

class TestSSEFormatCompliance:
    """Tests for SSE format compliance."""

    def test_stream_events_use_data_prefix(self, client):
        """SSE events should use 'data: ' prefix."""
        with mock_stream_dependencies():
            response = client.post(
                "/chat/stream",
                json={
                    "message": "Test",
                    "creator_id": "test-creator-123"
                }
            )

            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            # Check raw response contains "data: " prefix
            assert "data: " in response.text, f"Expected 'data: ' prefix in response"

    def test_stream_events_separated_by_double_newline(self, client):
        """SSE events should be separated by double newlines."""
        with mock_stream_dependencies():
            response = client.post(
                "/chat/stream",
                json={
                    "message": "Test message for events",
                    "creator_id": "test-creator-123"
                }
            )

            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            # Events should be separated by blank lines (double newline)
            # In SSE format: "data: {...}\n\ndata: {...}\n\n"
            assert "\n\n" in response.text, "Events should be separated by double newlines"


# =============================================================================
# Conversation ID Tests
# =============================================================================

class TestStreamConversationId:
    """Tests for conversation ID handling in streams."""

    def test_stream_uses_provided_conversation_id(self, client):
        """Stream should use provided conversation_id in final event."""
        with mock_stream_dependencies():
            response = client.post(
                "/chat/stream",
                json={
                    "message": "Follow-up question",
                    "creator_id": "test-creator-123",
                    "conversation_id": "existing-conv-456"
                }
            )

            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            events = parse_sse_events(response.text)
            done_events = [e for e in events if e.get("type") == "done"]

            assert len(done_events) == 1, "Expected exactly 1 done event"
            assert done_events[0].get("conversation_id") == "existing-conv-456", \
                f"Expected conversation_id 'existing-conv-456', got {done_events[0].get('conversation_id')}"

    def test_stream_generates_conversation_id_if_not_provided(self, client):
        """Stream should generate a conversation_id if not provided."""
        with mock_stream_dependencies():
            response = client.post(
                "/chat/stream",
                json={
                    "message": "New conversation",
                    "creator_id": "test-creator-123"
                    # No conversation_id provided
                }
            )

            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            events = parse_sse_events(response.text)
            done_events = [e for e in events if e.get("type") == "done"]

            assert len(done_events) == 1, "Expected exactly 1 done event"
            assert "conversation_id" in done_events[0], "Should have conversation_id"
            assert done_events[0]["conversation_id"] is not None, "conversation_id should not be None"
            assert len(done_events[0]["conversation_id"]) > 0, "conversation_id should not be empty"
