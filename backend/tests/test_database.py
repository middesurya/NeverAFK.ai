"""
Tests for the Database class from app.models.database.

These tests verify the Database class behavior when running in local mode
(without Supabase connection), which is the expected behavior in test environments.
"""

import pytest
import os
from unittest.mock import patch


class TestDatabaseLocalMode:
    """Test Database class in local development mode (no Supabase connection)."""

    @pytest.fixture
    def database(self):
        """Create a Database instance in local mode."""
        # Ensure no Supabase env vars are set
        with patch.dict(os.environ, {}, clear=True):
            from app.models.database import Database
            return Database()

    def test_database_initializes_without_client(self, database):
        """Database should initialize with client=None in local mode."""
        assert database.client is None

    def test_is_connected_returns_false(self, database):
        """is_connected should return False when no Supabase connection."""
        assert database.is_connected() is False

    async def test_create_creator_returns_mock_data(self, database):
        """create_creator should return mock data in local mode."""
        result = await database.create_creator(
            email="test@example.com",
            name="Test Creator"
        )

        assert result is not None
        assert result["id"] == "local-creator"
        assert result["email"] == "test@example.com"
        assert result["name"] == "Test Creator"
        assert result["credits_remaining"] == 100
        assert "created_at" in result

    async def test_get_creator_returns_mock_data(self, database):
        """get_creator should return mock data in local mode."""
        result = await database.get_creator("test-creator-123")

        assert result is not None
        assert result["id"] == "test-creator-123"
        assert result["email"] == "demo@example.com"
        assert result["name"] == "Demo Creator"
        assert result["credits_remaining"] == 100
        assert "created_at" in result

    async def test_save_conversation_returns_mock_data(self, database):
        """save_conversation should return mock data in local mode."""
        result = await database.save_conversation(
            creator_id="creator-123",
            student_message="What is Python?",
            ai_response="Python is a programming language.",
            sources=["source1.pdf", "source2.txt"],
            should_escalate=False
        )

        assert result is not None
        assert "id" in result
        assert result["id"].startswith("local-")
        assert result["creator_id"] == "creator-123"
        assert result["student_message"] == "What is Python?"
        assert result["ai_response"] == "Python is a programming language."
        assert result["sources"] == ["source1.pdf", "source2.txt"]
        assert result["should_escalate"] is False
        assert "created_at" in result

    async def test_save_conversation_with_escalation(self, database):
        """save_conversation should correctly handle escalation flag."""
        result = await database.save_conversation(
            creator_id="creator-123",
            student_message="I need human help",
            ai_response="Let me connect you with support.",
            sources=[],
            should_escalate=True
        )

        assert result["should_escalate"] is True

    async def test_get_conversations_returns_empty_list(self, database):
        """get_conversations should return empty list in local mode."""
        result = await database.get_conversations("creator-123")

        assert result == []

    async def test_get_conversations_with_limit(self, database):
        """get_conversations should accept limit parameter."""
        result = await database.get_conversations("creator-123", limit=10)

        assert result == []

    async def test_update_credit_usage_returns_mock_data(self, database):
        """update_credit_usage should return mock data in local mode."""
        result = await database.update_credit_usage(
            creator_id="creator-123",
            credits_used=25
        )

        assert result is not None
        assert result["id"] == "creator-123"
        assert result["credits_remaining"] == 75  # 100 - 25


class TestDatabaseInitialization:
    """Test Database initialization scenarios."""

    def test_database_reads_env_vars(self):
        """Database should read SUPABASE_URL and SUPABASE_ANON_KEY from env."""
        with patch.dict(os.environ, {
            "SUPABASE_URL": "https://test.supabase.co",
            "SUPABASE_ANON_KEY": "test-key-not-valid"
        }):
            from app.models.database import Database
            db = Database()
            assert db.url == "https://test.supabase.co"
            assert db.key == "test-key-not-valid"
            # Should still be None because key doesn't start with 'eyJ'
            assert db.client is None

    def test_database_without_env_vars(self):
        """Database should handle missing env vars gracefully."""
        with patch.dict(os.environ, {}, clear=True):
            from app.models.database import Database
            db = Database()
            assert db.url is None
            assert db.key is None
            assert db.client is None
            assert db.is_connected() is False


class TestDatabaseDataTypes:
    """Test Database handles various data types correctly."""

    @pytest.fixture
    def database(self):
        """Create a Database instance in local mode."""
        with patch.dict(os.environ, {}, clear=True):
            from app.models.database import Database
            return Database()

    async def test_create_creator_with_unicode_name(self, database):
        """create_creator should handle unicode names."""
        result = await database.create_creator(
            email="test@example.com",
            name="Test Creator"
        )
        assert result["name"] == "Test Creator"

    async def test_save_conversation_empty_sources(self, database):
        """save_conversation should handle empty sources list."""
        result = await database.save_conversation(
            creator_id="c1",
            student_message="Question",
            ai_response="Answer",
            sources=[],
            should_escalate=False
        )
        assert result["sources"] == []

    async def test_save_conversation_multiple_sources(self, database):
        """save_conversation should handle multiple sources."""
        sources = ["doc1.pdf", "doc2.txt", "doc3.docx"]
        result = await database.save_conversation(
            creator_id="c1",
            student_message="Question",
            ai_response="Answer",
            sources=sources,
            should_escalate=False
        )
        assert result["sources"] == sources
        assert len(result["sources"]) == 3
