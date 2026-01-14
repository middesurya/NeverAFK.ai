"""
PRD-004: Integration Tests for API Endpoints - Chat Tests

Tests for POST /chat endpoint:
- AC-1: POST /chat returns 200 with AI response and sources
- AC-2: POST /chat with missing message returns 422

These tests verify the chat endpoint handles requests correctly,
including authentication, validation, and AI response generation.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from tests.mocks.supabase_mock import MockDatabase


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def mock_agent_response():
    """Create a standard mock agent response."""
    return {
        "response": "Python is a programming language as explained in Module 1.",
        "sources": ["Module 1 - Introduction (Score: 0.92)"],
        "should_escalate": False,
        "context_used": 2
    }


@pytest.fixture
def mock_agent_escalate_response():
    """Create a mock agent response that triggers escalation."""
    return {
        "response": "I don't know the answer to that question.",
        "sources": [],
        "should_escalate": True,
        "context_used": 0
    }


# =============================================================================
# AC-1: POST /chat returns 200 with AI response and sources
# =============================================================================

class TestChatSuccess:
    """Tests for successful chat requests - AC-1."""

    def test_chat_returns_200_with_creator_id(self, client, mock_agent_response):
        """Chat should return 200 when creator_id is provided."""
        mock_db = MockDatabase()

        with patch('main.support_agent.process_query', new_callable=AsyncMock) as mock_process:
            mock_process.return_value = mock_agent_response
            with patch('main.db', mock_db):
                response = client.post(
                    "/chat",
                    json={
                        "message": "What is Python?",
                        "creator_id": "test-creator-123"
                    }
                )

                assert response.status_code == 200

    def test_chat_returns_response_field(self, client, mock_agent_response):
        """Chat should return response field in the body."""
        mock_db = MockDatabase()

        with patch('main.support_agent.process_query', new_callable=AsyncMock) as mock_process:
            mock_process.return_value = mock_agent_response
            with patch('main.db', mock_db):
                response = client.post(
                    "/chat",
                    json={
                        "message": "What is Python?",
                        "creator_id": "test-creator-123"
                    }
                )

                data = response.json()
                assert "response" in data
                assert len(data["response"]) > 0

    def test_chat_returns_sources_field(self, client, mock_agent_response):
        """Chat should return sources field listing relevant materials."""
        mock_db = MockDatabase()

        with patch('main.support_agent.process_query', new_callable=AsyncMock) as mock_process:
            mock_process.return_value = mock_agent_response
            with patch('main.db', mock_db):
                response = client.post(
                    "/chat",
                    json={
                        "message": "What is Python?",
                        "creator_id": "test-creator-123"
                    }
                )

                data = response.json()
                assert "sources" in data
                assert isinstance(data["sources"], list)

    def test_chat_returns_should_escalate_field(self, client, mock_agent_response):
        """Chat should return should_escalate boolean field."""
        mock_db = MockDatabase()

        with patch('main.support_agent.process_query', new_callable=AsyncMock) as mock_process:
            mock_process.return_value = mock_agent_response
            with patch('main.db', mock_db):
                response = client.post(
                    "/chat",
                    json={
                        "message": "What is Python?",
                        "creator_id": "test-creator-123"
                    }
                )

                data = response.json()
                assert "should_escalate" in data
                assert isinstance(data["should_escalate"], bool)

    def test_chat_returns_conversation_id(self, client, mock_agent_response):
        """Chat should return conversation_id field."""
        mock_db = MockDatabase()

        with patch('main.support_agent.process_query', new_callable=AsyncMock) as mock_process:
            mock_process.return_value = mock_agent_response
            with patch('main.db', mock_db):
                response = client.post(
                    "/chat",
                    json={
                        "message": "What is Python?",
                        "creator_id": "test-creator-123"
                    }
                )

                data = response.json()
                assert "conversation_id" in data
                assert isinstance(data["conversation_id"], str)

    def test_chat_uses_provided_conversation_id(self, client, mock_agent_response):
        """Chat should use provided conversation_id if given."""
        mock_db = MockDatabase()

        with patch('main.support_agent.process_query', new_callable=AsyncMock) as mock_process:
            mock_process.return_value = mock_agent_response
            with patch('main.db', mock_db):
                response = client.post(
                    "/chat",
                    json={
                        "message": "Follow-up question",
                        "creator_id": "test-creator-123",
                        "conversation_id": "existing-conv-456"
                    }
                )

                data = response.json()
                assert data["conversation_id"] == "existing-conv-456"

    def test_chat_escalates_uncertain_response(self, client, mock_agent_escalate_response):
        """Chat should set should_escalate=True for uncertain responses."""
        mock_db = MockDatabase()

        with patch('main.support_agent.process_query', new_callable=AsyncMock) as mock_process:
            mock_process.return_value = mock_agent_escalate_response
            with patch('main.db', mock_db):
                response = client.post(
                    "/chat",
                    json={
                        "message": "What is the refund policy?",
                        "creator_id": "test-creator-123"
                    }
                )

                data = response.json()
                assert data["should_escalate"] is True

    def test_chat_does_not_escalate_confident_response(self, client, mock_agent_response):
        """Chat should set should_escalate=False for confident responses."""
        mock_db = MockDatabase()

        with patch('main.support_agent.process_query', new_callable=AsyncMock) as mock_process:
            mock_process.return_value = mock_agent_response
            with patch('main.db', mock_db):
                response = client.post(
                    "/chat",
                    json={
                        "message": "What is Python?",
                        "creator_id": "test-creator-123"
                    }
                )

                data = response.json()
                assert data["should_escalate"] is False


# =============================================================================
# AC-2: POST /chat with missing message returns 422
# =============================================================================

class TestChatValidation:
    """Tests for chat request validation - AC-2."""

    def test_chat_missing_message_returns_422(self, client):
        """Chat should return 422 when message is missing."""
        response = client.post(
            "/chat",
            json={
                "creator_id": "test-creator-123"
            }
        )

        assert response.status_code == 422

    def test_chat_empty_body_returns_422(self, client):
        """Chat should return 422 when request body is empty."""
        response = client.post(
            "/chat",
            json={}
        )

        assert response.status_code == 422

    def test_chat_null_message_returns_422(self, client):
        """Chat should return 422 when message is null."""
        response = client.post(
            "/chat",
            json={
                "message": None,
                "creator_id": "test-creator-123"
            }
        )

        assert response.status_code == 422

    def test_chat_invalid_json_returns_422(self, client):
        """Chat should return 422 for invalid JSON."""
        response = client.post(
            "/chat",
            content="not valid json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422

    def test_chat_missing_creator_id_returns_401(self, client, mock_agent_response):
        """Chat should return 401 when creator_id is missing and no auth token."""
        with patch('main.support_agent.process_query', new_callable=AsyncMock) as mock_process:
            mock_process.return_value = mock_agent_response
            response = client.post(
                "/chat",
                json={
                    "message": "What is Python?"
                    # No creator_id provided
                }
            )

            assert response.status_code == 401

    def test_chat_validation_error_has_detail(self, client):
        """Validation errors should include detail message."""
        response = client.post(
            "/chat",
            json={}
        )

        data = response.json()
        assert "detail" in data


# =============================================================================
# Edge Cases and Special Characters
# =============================================================================

class TestChatEdgeCases:
    """Tests for chat edge cases."""

    def test_chat_empty_message_string(self, client, mock_agent_response):
        """Chat should handle empty message string."""
        mock_db = MockDatabase()

        with patch('main.support_agent.process_query', new_callable=AsyncMock) as mock_process:
            mock_process.return_value = mock_agent_response
            with patch('main.db', mock_db):
                response = client.post(
                    "/chat",
                    json={
                        "message": "",
                        "creator_id": "test-creator-123"
                    }
                )

                # Empty string is valid input (not missing)
                assert response.status_code == 200

    def test_chat_whitespace_only_message(self, client, mock_agent_response):
        """Chat should handle whitespace-only message."""
        mock_db = MockDatabase()

        with patch('main.support_agent.process_query', new_callable=AsyncMock) as mock_process:
            mock_process.return_value = mock_agent_response
            with patch('main.db', mock_db):
                response = client.post(
                    "/chat",
                    json={
                        "message": "   \n\t   ",
                        "creator_id": "test-creator-123"
                    }
                )

                assert response.status_code == 200

    def test_chat_special_characters(self, client, mock_agent_response):
        """Chat should handle special characters in message."""
        mock_db = MockDatabase()

        with patch('main.support_agent.process_query', new_callable=AsyncMock) as mock_process:
            mock_process.return_value = mock_agent_response
            with patch('main.db', mock_db):
                response = client.post(
                    "/chat",
                    json={
                        "message": "What's the difference between '==' and '!=' operators?",
                        "creator_id": "test-creator-123"
                    }
                )

                assert response.status_code == 200
                data = response.json()
                assert "response" in data

    def test_chat_unicode_characters(self, client, mock_agent_response):
        """Chat should handle unicode characters."""
        mock_db = MockDatabase()

        with patch('main.support_agent.process_query', new_callable=AsyncMock) as mock_process:
            mock_process.return_value = mock_agent_response
            with patch('main.db', mock_db):
                response = client.post(
                    "/chat",
                    json={
                        "message": "How do I print characters like a, e, n in Python?",
                        "creator_id": "test-creator-123"
                    }
                )

                assert response.status_code == 200

    def test_chat_very_long_message(self, client, mock_agent_response):
        """Chat should handle very long messages."""
        mock_db = MockDatabase()
        long_message = "What is Python? " * 500  # Very long message

        with patch('main.support_agent.process_query', new_callable=AsyncMock) as mock_process:
            mock_process.return_value = mock_agent_response
            with patch('main.db', mock_db):
                response = client.post(
                    "/chat",
                    json={
                        "message": long_message,
                        "creator_id": "test-creator-123"
                    }
                )

                assert response.status_code == 200

    def test_chat_html_injection(self, client, mock_agent_response):
        """Chat should handle HTML in message safely."""
        mock_db = MockDatabase()

        with patch('main.support_agent.process_query', new_callable=AsyncMock) as mock_process:
            mock_process.return_value = mock_agent_response
            with patch('main.db', mock_db):
                response = client.post(
                    "/chat",
                    json={
                        "message": "<script>alert('xss')</script>What is Python?",
                        "creator_id": "test-creator-123"
                    }
                )

                assert response.status_code == 200

    def test_chat_sql_injection_attempt(self, client, mock_agent_response):
        """Chat should handle SQL injection attempts safely."""
        mock_db = MockDatabase()

        with patch('main.support_agent.process_query', new_callable=AsyncMock) as mock_process:
            mock_process.return_value = mock_agent_response
            with patch('main.db', mock_db):
                response = client.post(
                    "/chat",
                    json={
                        "message": "'; DROP TABLE users; --",
                        "creator_id": "test-creator-123"
                    }
                )

                assert response.status_code == 200


# =============================================================================
# Database Interaction Tests
# =============================================================================

class TestChatDatabaseInteraction:
    """Tests for chat database interactions."""

    def test_chat_saves_conversation(self, client, mock_agent_response):
        """Chat should save conversation to database."""
        mock_db = MockDatabase()

        with patch('main.support_agent.process_query', new_callable=AsyncMock) as mock_process:
            mock_process.return_value = mock_agent_response
            with patch('main.db', mock_db):
                response = client.post(
                    "/chat",
                    json={
                        "message": "What is Python?",
                        "creator_id": "test-creator-123"
                    }
                )

                assert response.status_code == 200

                # Verify save_conversation was called
                save_calls = [c for c in mock_db.call_history if c["method"] == "save_conversation"]
                assert len(save_calls) == 1
                assert save_calls[0]["creator_id"] == "test-creator-123"
                assert save_calls[0]["student_message"] == "What is Python?"

    def test_chat_updates_credit_usage(self, client, mock_agent_response):
        """Chat should update credit usage."""
        mock_db = MockDatabase()
        mock_db.set_creator_credits("test-creator-123", 100)

        with patch('main.support_agent.process_query', new_callable=AsyncMock) as mock_process:
            mock_process.return_value = mock_agent_response
            with patch('main.db', mock_db):
                response = client.post(
                    "/chat",
                    json={
                        "message": "What is Python?",
                        "creator_id": "test-creator-123"
                    }
                )

                assert response.status_code == 200

                # Verify update_credit_usage was called
                credit_calls = [c for c in mock_db.call_history if c["method"] == "update_credit_usage"]
                assert len(credit_calls) == 1
                assert credit_calls[0]["creator_id"] == "test-creator-123"
                assert credit_calls[0]["credits_used"] == 1


# =============================================================================
# Response Format Tests
# =============================================================================

class TestChatResponseFormat:
    """Tests for chat response format conformance."""

    def test_chat_response_is_json(self, client, mock_agent_response):
        """Chat should return JSON response."""
        mock_db = MockDatabase()

        with patch('main.support_agent.process_query', new_callable=AsyncMock) as mock_process:
            mock_process.return_value = mock_agent_response
            with patch('main.db', mock_db):
                response = client.post(
                    "/chat",
                    json={
                        "message": "What is Python?",
                        "creator_id": "test-creator-123"
                    }
                )

                assert response.headers.get("content-type") == "application/json"
                # Should not raise JSONDecodeError
                data = response.json()
                assert isinstance(data, dict)

    def test_chat_response_matches_schema(self, client, mock_agent_response):
        """Chat response should match ChatResponse schema."""
        mock_db = MockDatabase()

        with patch('main.support_agent.process_query', new_callable=AsyncMock) as mock_process:
            mock_process.return_value = mock_agent_response
            with patch('main.db', mock_db):
                response = client.post(
                    "/chat",
                    json={
                        "message": "What is Python?",
                        "creator_id": "test-creator-123"
                    }
                )

                data = response.json()

                # Verify all required fields are present with correct types
                assert isinstance(data["response"], str)
                assert isinstance(data["sources"], list)
                assert isinstance(data["should_escalate"], bool)
                assert isinstance(data["conversation_id"], str)

    def test_chat_sources_are_strings(self, client, mock_agent_response):
        """Chat sources should be a list of strings."""
        mock_db = MockDatabase()

        with patch('main.support_agent.process_query', new_callable=AsyncMock) as mock_process:
            mock_process.return_value = mock_agent_response
            with patch('main.db', mock_db):
                response = client.post(
                    "/chat",
                    json={
                        "message": "What is Python?",
                        "creator_id": "test-creator-123"
                    }
                )

                data = response.json()
                for source in data["sources"]:
                    assert isinstance(source, str)


# =============================================================================
# Agent Integration Tests
# =============================================================================

class TestChatAgentIntegration:
    """Tests for chat endpoint integration with support agent."""

    def test_chat_passes_correct_query_to_agent(self, client, mock_agent_response):
        """Chat should pass the user's message to the agent."""
        mock_db = MockDatabase()

        with patch('main.support_agent.process_query', new_callable=AsyncMock) as mock_process:
            mock_process.return_value = mock_agent_response
            with patch('main.db', mock_db):
                response = client.post(
                    "/chat",
                    json={
                        "message": "What is Python?",
                        "creator_id": "test-creator-123"
                    }
                )

                assert response.status_code == 200
                mock_process.assert_called_once()
                call_kwargs = mock_process.call_args.kwargs
                assert call_kwargs["query"] == "What is Python?"

    def test_chat_passes_creator_id_to_agent(self, client, mock_agent_response):
        """Chat should pass creator_id to the agent."""
        mock_db = MockDatabase()

        with patch('main.support_agent.process_query', new_callable=AsyncMock) as mock_process:
            mock_process.return_value = mock_agent_response
            with patch('main.db', mock_db):
                response = client.post(
                    "/chat",
                    json={
                        "message": "What is Python?",
                        "creator_id": "test-creator-123"
                    }
                )

                assert response.status_code == 200
                mock_process.assert_called_once()
                call_kwargs = mock_process.call_args.kwargs
                assert call_kwargs["creator_id"] == "test-creator-123"

    def test_chat_returns_agent_response_content(self, client):
        """Chat should return the response content from the agent."""
        mock_db = MockDatabase()
        custom_response = {
            "response": "Custom response from agent for testing.",
            "sources": ["Custom Source 1", "Custom Source 2"],
            "should_escalate": False,
            "context_used": 3
        }

        with patch('main.support_agent.process_query', new_callable=AsyncMock) as mock_process:
            mock_process.return_value = custom_response
            with patch('main.db', mock_db):
                response = client.post(
                    "/chat",
                    json={
                        "message": "Test question",
                        "creator_id": "test-creator-123"
                    }
                )

                data = response.json()
                assert data["response"] == "Custom response from agent for testing."
                assert data["sources"] == ["Custom Source 1", "Custom Source 2"]
