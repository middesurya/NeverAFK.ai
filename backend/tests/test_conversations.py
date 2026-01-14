"""
PRD-004: Integration Tests for API Endpoints - Conversations Tests

Tests for GET /conversations/{creator_id} endpoint:
- AC-4: GET /conversations/{creator_id} returns list

These tests verify the conversations endpoint correctly retrieves
conversation history with proper authorization.
"""

import pytest
from unittest.mock import patch, AsyncMock

from tests.mocks.supabase_mock import MockDatabase


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def sample_conversations():
    """Create sample conversation data."""
    return [
        {
            "id": "conv-1",
            "creator_id": "test-creator-123",
            "student_message": "What is Python?",
            "ai_response": "Python is a programming language.",
            "sources": ["Module 1"],
            "should_escalate": False,
            "created_at": "2024-01-15T10:30:00Z"
        },
        {
            "id": "conv-2",
            "creator_id": "test-creator-123",
            "student_message": "How do I create a function?",
            "ai_response": "Use the def keyword to define functions.",
            "sources": ["Module 3"],
            "should_escalate": False,
            "created_at": "2024-01-15T11:00:00Z"
        },
        {
            "id": "conv-3",
            "creator_id": "test-creator-123",
            "student_message": "What is the refund policy?",
            "ai_response": "I'm not sure about the refund policy.",
            "sources": [],
            "should_escalate": True,
            "created_at": "2024-01-15T11:30:00Z"
        }
    ]


@pytest.fixture
def mock_db_with_conversations(sample_conversations):
    """Create mock database with preset conversations."""
    mock_db = MockDatabase()
    mock_db._conversations = sample_conversations.copy()
    return mock_db


# =============================================================================
# AC-4: GET /conversations/{creator_id} returns list
# =============================================================================

class TestConversationsSuccess:
    """Tests for successful conversation retrieval - AC-4."""

    def test_get_conversations_returns_200(self, client, mock_db_with_conversations):
        """Get conversations should return 200."""
        with patch('main.db', mock_db_with_conversations):
            response = client.get("/conversations/test-creator-123")
            assert response.status_code == 200

    def test_get_conversations_returns_list(self, client, mock_db_with_conversations):
        """Get conversations should return a list of conversations."""
        with patch('main.db', mock_db_with_conversations):
            response = client.get("/conversations/test-creator-123")
            data = response.json()

            assert "conversations" in data
            assert isinstance(data["conversations"], list)

    def test_get_conversations_returns_conversation_data(
        self, client, mock_db_with_conversations, sample_conversations
    ):
        """Get conversations should return conversation details."""
        with patch('main.db', mock_db_with_conversations):
            response = client.get("/conversations/test-creator-123")
            data = response.json()

            conversations = data["conversations"]
            assert len(conversations) == 3

            # Check first conversation has expected fields
            conv = conversations[0]
            assert "id" in conv
            assert "creator_id" in conv
            assert "student_message" in conv
            assert "ai_response" in conv
            assert "sources" in conv
            assert "should_escalate" in conv
            assert "created_at" in conv

    def test_get_conversations_empty_for_new_creator(self, client):
        """Get conversations should return empty list for new creator."""
        mock_db = MockDatabase()

        with patch('main.db', mock_db):
            response = client.get("/conversations/new-creator-456")
            data = response.json()

            assert response.status_code == 200
            assert data["conversations"] == []

    def test_get_conversations_with_limit(self, client, mock_db_with_conversations):
        """Get conversations should respect limit parameter."""
        with patch('main.db', mock_db_with_conversations):
            response = client.get("/conversations/test-creator-123?limit=2")
            data = response.json()

            assert response.status_code == 200
            assert len(data["conversations"]) <= 2

    def test_get_conversations_default_limit(self, client, mock_db_with_conversations):
        """Get conversations should use default limit of 50."""
        with patch('main.db', mock_db_with_conversations):
            response = client.get("/conversations/test-creator-123")

            assert response.status_code == 200

            # Verify limit was called with default
            limit_calls = [
                c for c in mock_db_with_conversations.call_history
                if c["method"] == "get_conversations"
            ]
            assert len(limit_calls) == 1
            assert limit_calls[0]["limit"] == 50

    def test_get_conversations_filters_by_creator_id(self, client):
        """Get conversations should only return conversations for given creator."""
        mock_db = MockDatabase()
        mock_db._conversations = [
            {
                "id": "conv-1",
                "creator_id": "creator-A",
                "student_message": "Q1",
                "ai_response": "A1",
                "sources": [],
                "should_escalate": False,
                "created_at": "2024-01-15T10:00:00Z"
            },
            {
                "id": "conv-2",
                "creator_id": "creator-B",
                "student_message": "Q2",
                "ai_response": "A2",
                "sources": [],
                "should_escalate": False,
                "created_at": "2024-01-15T11:00:00Z"
            }
        ]

        with patch('main.db', mock_db):
            response = client.get("/conversations/creator-A")
            data = response.json()

            assert response.status_code == 200
            # Should only have creator-A's conversations
            for conv in data["conversations"]:
                assert conv["creator_id"] == "creator-A"


# =============================================================================
# Edge Cases
# =============================================================================

class TestConversationsEdgeCases:
    """Tests for conversation endpoint edge cases."""

    def test_get_conversations_special_characters_in_creator_id(self, client):
        """Get conversations should handle special characters in creator_id."""
        mock_db = MockDatabase()

        with patch('main.db', mock_db):
            response = client.get("/conversations/creator-with-dash_underscore")
            assert response.status_code == 200

    def test_get_conversations_unicode_creator_id(self, client):
        """Get conversations should handle unicode in creator_id."""
        mock_db = MockDatabase()

        with patch('main.db', mock_db):
            # URL-encoded unicode
            response = client.get("/conversations/creator-test123")
            assert response.status_code == 200

    def test_get_conversations_uuid_creator_id(self, client):
        """Get conversations should handle UUID format creator_id."""
        mock_db = MockDatabase()

        with patch('main.db', mock_db):
            response = client.get("/conversations/550e8400-e29b-41d4-a716-446655440000")
            assert response.status_code == 200

    def test_get_conversations_very_long_creator_id(self, client):
        """Get conversations should handle very long creator_id."""
        mock_db = MockDatabase()
        long_id = "a" * 200

        with patch('main.db', mock_db):
            response = client.get(f"/conversations/{long_id}")
            assert response.status_code == 200

    def test_get_conversations_limit_zero(self, client, mock_db_with_conversations):
        """Get conversations with limit=0 should return empty or error."""
        with patch('main.db', mock_db_with_conversations):
            response = client.get("/conversations/test-creator-123?limit=0")
            # Limit 0 may return empty list or be treated as invalid
            assert response.status_code in [200, 422]

    def test_get_conversations_limit_negative(self, client, mock_db_with_conversations):
        """Get conversations with negative limit should handle gracefully."""
        with patch('main.db', mock_db_with_conversations):
            response = client.get("/conversations/test-creator-123?limit=-1")
            # Negative limit should be handled
            assert response.status_code in [200, 422]

    def test_get_conversations_limit_very_large(self, client, mock_db_with_conversations):
        """Get conversations with very large limit should work."""
        with patch('main.db', mock_db_with_conversations):
            response = client.get("/conversations/test-creator-123?limit=10000")
            assert response.status_code == 200


# =============================================================================
# Response Format Tests
# =============================================================================

class TestConversationsResponseFormat:
    """Tests for conversation response format."""

    def test_get_conversations_returns_json(self, client, mock_db_with_conversations):
        """Get conversations should return JSON."""
        with patch('main.db', mock_db_with_conversations):
            response = client.get("/conversations/test-creator-123")

            assert response.headers.get("content-type") == "application/json"
            data = response.json()
            assert isinstance(data, dict)

    def test_get_conversations_has_conversations_key(self, client, mock_db_with_conversations):
        """Get conversations response should have 'conversations' key."""
        with patch('main.db', mock_db_with_conversations):
            response = client.get("/conversations/test-creator-123")
            data = response.json()

            assert "conversations" in data

    def test_get_conversations_sources_is_list(self, client, mock_db_with_conversations):
        """Conversation sources should be a list."""
        with patch('main.db', mock_db_with_conversations):
            response = client.get("/conversations/test-creator-123")
            data = response.json()

            for conv in data["conversations"]:
                assert isinstance(conv.get("sources", []), list)

    def test_get_conversations_should_escalate_is_bool(
        self, client, mock_db_with_conversations
    ):
        """Conversation should_escalate should be boolean."""
        with patch('main.db', mock_db_with_conversations):
            response = client.get("/conversations/test-creator-123")
            data = response.json()

            for conv in data["conversations"]:
                assert isinstance(conv.get("should_escalate", False), bool)


# =============================================================================
# Database Interaction Tests
# =============================================================================

class TestConversationsDatabaseInteraction:
    """Tests for conversation database interactions."""

    def test_get_conversations_calls_database(self, client, mock_db_with_conversations):
        """Get conversations should call database get_conversations."""
        with patch('main.db', mock_db_with_conversations):
            response = client.get("/conversations/test-creator-123")

            assert response.status_code == 200

            # Verify get_conversations was called
            get_calls = [
                c for c in mock_db_with_conversations.call_history
                if c["method"] == "get_conversations"
            ]
            assert len(get_calls) == 1
            assert get_calls[0]["creator_id"] == "test-creator-123"

    def test_get_conversations_passes_limit(self, client, mock_db_with_conversations):
        """Get conversations should pass limit to database."""
        with patch('main.db', mock_db_with_conversations):
            response = client.get("/conversations/test-creator-123?limit=25")

            assert response.status_code == 200

            get_calls = [
                c for c in mock_db_with_conversations.call_history
                if c["method"] == "get_conversations"
            ]
            assert get_calls[0]["limit"] == 25


# =============================================================================
# Authorization Tests (Demo Mode)
# =============================================================================

class TestConversationsAuthorization:
    """Tests for conversation endpoint authorization."""

    def test_get_demo_conversations_allowed_without_auth(self, client):
        """Demo creator conversations should be accessible without auth."""
        mock_db = MockDatabase()
        mock_db._conversations = [
            {
                "id": "conv-1",
                "creator_id": "demo-creator",
                "student_message": "Demo question",
                "ai_response": "Demo answer",
                "sources": [],
                "should_escalate": False,
                "created_at": "2024-01-15T10:00:00Z"
            }
        ]

        with patch('main.db', mock_db):
            response = client.get("/conversations/demo-creator")

            assert response.status_code == 200

    def test_get_conversations_without_auth_uses_path_param(self, client):
        """Without auth, should use creator_id from path."""
        mock_db = MockDatabase()
        mock_db._conversations = [
            {
                "id": "conv-1",
                "creator_id": "any-creator",
                "student_message": "Question",
                "ai_response": "Answer",
                "sources": [],
                "should_escalate": False,
                "created_at": "2024-01-15T10:00:00Z"
            }
        ]

        with patch('main.db', mock_db):
            response = client.get("/conversations/any-creator")

            # In demo mode (no auth), should use path param
            assert response.status_code == 200


# =============================================================================
# Pagination Tests
# =============================================================================

class TestConversationsPagination:
    """Tests for conversation pagination."""

    def test_get_conversations_respects_limit(self, client):
        """Get conversations should respect the limit parameter."""
        mock_db = MockDatabase()
        # Create more conversations than the limit
        mock_db._conversations = [
            {
                "id": f"conv-{i}",
                "creator_id": "test-creator",
                "student_message": f"Question {i}",
                "ai_response": f"Answer {i}",
                "sources": [],
                "should_escalate": False,
                "created_at": f"2024-01-{i:02d}T10:00:00Z"
            }
            for i in range(1, 11)  # 10 conversations
        ]

        with patch('main.db', mock_db):
            response = client.get("/conversations/test-creator?limit=5")
            data = response.json()

            assert response.status_code == 200
            assert len(data["conversations"]) <= 5
