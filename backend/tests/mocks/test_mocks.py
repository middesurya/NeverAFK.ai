"""
PRD-002: Tests for Mock External Services

These tests verify that our mock implementations for OpenAI, Pinecone, and Supabase
work correctly without making actual API calls.

IMPORTANT: These tests are designed to FAIL initially because the mock
implementations don't exist yet. The @test-implementer will create the
actual mock classes to make these tests pass.
"""

import pytest
from datetime import datetime
from typing import List, Tuple

# These imports will fail until mock implementations are created
from tests.mocks.openai_mock import MockChatOpenAI, MockOpenAIResponse
from tests.mocks.pinecone_mock import MockVectorStoreService, MockDocument
from tests.mocks.supabase_mock import MockDatabase


# =============================================================================
# AC-1: MockOpenAI Tests - Returns predictable mock response without API call
# =============================================================================

class TestMockOpenAI:
    """Tests for MockChatOpenAI implementation."""

    def test_mock_openai_instantiation(self):
        """Mock should instantiate without API key."""
        mock_llm = MockChatOpenAI()
        assert mock_llm is not None

    def test_mock_openai_with_custom_response(self):
        """Mock should accept custom response text."""
        custom_response = "This is a custom mock response."
        mock_llm = MockChatOpenAI(default_response=custom_response)
        assert mock_llm.default_response == custom_response

    @pytest.mark.asyncio
    async def test_mock_openai_ainvoke_returns_response_object(self):
        """ainvoke should return object with .content attribute."""
        mock_llm = MockChatOpenAI(default_response="Test response content")
        messages = [{"role": "user", "content": "Hello"}]

        response = await mock_llm.ainvoke(messages)

        assert hasattr(response, "content")
        assert response.content == "Test response content"

    @pytest.mark.asyncio
    async def test_mock_openai_ainvoke_with_message_objects(self):
        """ainvoke should handle LangChain message objects."""
        mock_llm = MockChatOpenAI(default_response="Response to messages")

        # Simulate LangChain message objects (SystemMessage, HumanMessage)
        class FakeMessage:
            def __init__(self, content):
                self.content = content

        messages = [
            FakeMessage("You are a helpful assistant."),
            FakeMessage("What is Python?")
        ]

        response = await mock_llm.ainvoke(messages)

        assert response.content == "Response to messages"

    @pytest.mark.asyncio
    async def test_mock_openai_no_actual_api_call(self):
        """Mock should NOT make any actual HTTP/API calls."""
        mock_llm = MockChatOpenAI()
        messages = [{"role": "user", "content": "Test"}]

        # This should complete instantly without network calls
        response = await mock_llm.ainvoke(messages)

        assert response is not None
        # If this test takes more than milliseconds, something is wrong

    @pytest.mark.asyncio
    async def test_mock_openai_sequential_responses(self):
        """Mock should support returning different responses in sequence."""
        responses = ["First response", "Second response", "Third response"]
        mock_llm = MockChatOpenAI(responses=responses)

        for expected in responses:
            result = await mock_llm.ainvoke([{"role": "user", "content": "test"}])
            assert result.content == expected

    @pytest.mark.asyncio
    async def test_mock_openai_response_object_type(self):
        """Response should be MockOpenAIResponse type."""
        mock_llm = MockChatOpenAI()
        response = await mock_llm.ainvoke([])

        assert isinstance(response, MockOpenAIResponse)


# =============================================================================
# AC-2: MockPinecone Tests - Returns mock documents with scores
# =============================================================================

class TestMockPinecone:
    """Tests for MockVectorStoreService implementation."""

    def test_mock_pinecone_instantiation(self):
        """Mock should instantiate without API keys."""
        mock_vs = MockVectorStoreService()
        assert mock_vs is not None

    def test_mock_pinecone_with_preset_documents(self):
        """Mock should accept preset documents for search results."""
        docs = [
            MockDocument(page_content="Doc 1 content", metadata={"source": "source1"}),
            MockDocument(page_content="Doc 2 content", metadata={"source": "source2"}),
        ]
        mock_vs = MockVectorStoreService(documents=docs)
        assert len(mock_vs.documents) == 2

    @pytest.mark.asyncio
    async def test_mock_pinecone_similarity_search_returns_list(self):
        """similarity_search should return a list."""
        mock_vs = MockVectorStoreService()

        results = await mock_vs.similarity_search(
            query="test query",
            creator_id="creator-123",
            k=4
        )

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_mock_pinecone_similarity_search_returns_tuples(self):
        """similarity_search should return List[(Document, score)]."""
        docs = [
            MockDocument(page_content="Content 1", metadata={"source": "s1"}),
        ]
        mock_vs = MockVectorStoreService(documents=docs)

        results = await mock_vs.similarity_search(
            query="test",
            creator_id="creator-123",
            k=4
        )

        assert len(results) > 0
        for item in results:
            assert isinstance(item, tuple)
            assert len(item) == 2
            doc, score = item
            assert hasattr(doc, "page_content")
            assert hasattr(doc, "metadata")
            assert isinstance(score, float)

    @pytest.mark.asyncio
    async def test_mock_pinecone_respects_k_parameter(self):
        """similarity_search should return at most k results."""
        docs = [
            MockDocument(page_content=f"Doc {i}", metadata={"source": f"s{i}"})
            for i in range(10)
        ]
        mock_vs = MockVectorStoreService(documents=docs)

        results = await mock_vs.similarity_search(
            query="test",
            creator_id="creator-123",
            k=3
        )

        assert len(results) <= 3

    @pytest.mark.asyncio
    async def test_mock_pinecone_scores_between_0_and_1(self):
        """Scores should be between 0.0 and 1.0."""
        docs = [
            MockDocument(page_content="Content", metadata={"source": "s1"}),
        ]
        mock_vs = MockVectorStoreService(documents=docs)

        results = await mock_vs.similarity_search(
            query="test",
            creator_id="creator-123",
            k=4
        )

        for doc, score in results:
            assert 0.0 <= score <= 1.0

    @pytest.mark.asyncio
    async def test_mock_pinecone_empty_results(self):
        """Mock should handle no documents gracefully."""
        mock_vs = MockVectorStoreService(documents=[])

        results = await mock_vs.similarity_search(
            query="test",
            creator_id="creator-123",
            k=4
        )

        assert results == []

    @pytest.mark.asyncio
    async def test_mock_pinecone_with_custom_scores(self):
        """Mock should allow setting custom scores for documents."""
        docs_with_scores = [
            (MockDocument(page_content="High relevance", metadata={}), 0.95),
            (MockDocument(page_content="Medium relevance", metadata={}), 0.75),
            (MockDocument(page_content="Low relevance", metadata={}), 0.55),
        ]
        mock_vs = MockVectorStoreService(documents_with_scores=docs_with_scores)

        results = await mock_vs.similarity_search(
            query="test",
            creator_id="creator-123",
            k=4
        )

        assert results[0][1] == 0.95
        assert results[1][1] == 0.75
        assert results[2][1] == 0.55

    @pytest.mark.asyncio
    async def test_mock_pinecone_add_documents(self):
        """Mock should support adding documents."""
        mock_vs = MockVectorStoreService()

        docs = [
            MockDocument(page_content="New doc", metadata={"source": "test"})
        ]

        result = await mock_vs.add_documents(
            documents=docs,
            creator_id="creator-123"
        )

        assert result["status"] == "success"
        assert result["document_count"] == 1

    def test_mock_document_attributes(self):
        """MockDocument should have page_content and metadata."""
        doc = MockDocument(
            page_content="Test content",
            metadata={"source": "test.pdf", "page": 1}
        )

        assert doc.page_content == "Test content"
        assert doc.metadata == {"source": "test.pdf", "page": 1}


# =============================================================================
# AC-3: MockSupabase Tests - Returns mock data matching expected schema
# =============================================================================

class TestMockSupabase:
    """Tests for MockDatabase implementation."""

    def test_mock_supabase_instantiation(self):
        """Mock should instantiate without credentials."""
        mock_db = MockDatabase()
        assert mock_db is not None

    def test_mock_supabase_is_connected(self):
        """Mock should report as connected."""
        mock_db = MockDatabase()
        assert mock_db.is_connected() is True

    def test_mock_supabase_disconnected_mode(self):
        """Mock should support disconnected mode for testing fallbacks."""
        mock_db = MockDatabase(connected=False)
        assert mock_db.is_connected() is False

    @pytest.mark.asyncio
    async def test_mock_supabase_save_conversation(self):
        """save_conversation should return data matching expected schema."""
        mock_db = MockDatabase()

        result = await mock_db.save_conversation(
            creator_id="creator-123",
            student_message="What is Python?",
            ai_response="Python is a programming language.",
            sources=["Module 1", "FAQ"],
            should_escalate=False
        )

        assert result is not None
        assert "id" in result
        assert result["creator_id"] == "creator-123"
        assert result["student_message"] == "What is Python?"
        assert result["ai_response"] == "Python is a programming language."
        assert result["sources"] == ["Module 1", "FAQ"]
        assert result["should_escalate"] is False
        assert "created_at" in result

    @pytest.mark.asyncio
    async def test_mock_supabase_save_conversation_with_escalation(self):
        """save_conversation should correctly store escalation flag."""
        mock_db = MockDatabase()

        result = await mock_db.save_conversation(
            creator_id="creator-456",
            student_message="I need help with billing",
            ai_response="I'm not sure about billing.",
            sources=[],
            should_escalate=True
        )

        assert result["should_escalate"] is True

    @pytest.mark.asyncio
    async def test_mock_supabase_get_conversations(self):
        """get_conversations should return list of conversations."""
        mock_db = MockDatabase()

        # First save some conversations
        await mock_db.save_conversation(
            creator_id="creator-123",
            student_message="Q1",
            ai_response="A1",
            sources=[],
            should_escalate=False
        )
        await mock_db.save_conversation(
            creator_id="creator-123",
            student_message="Q2",
            ai_response="A2",
            sources=[],
            should_escalate=False
        )

        results = await mock_db.get_conversations(creator_id="creator-123")

        assert isinstance(results, list)
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_mock_supabase_get_conversations_respects_limit(self):
        """get_conversations should respect limit parameter."""
        mock_db = MockDatabase()

        # Save multiple conversations
        for i in range(10):
            await mock_db.save_conversation(
                creator_id="creator-123",
                student_message=f"Q{i}",
                ai_response=f"A{i}",
                sources=[],
                should_escalate=False
            )

        results = await mock_db.get_conversations(creator_id="creator-123", limit=5)

        assert len(results) <= 5

    @pytest.mark.asyncio
    async def test_mock_supabase_get_conversations_filters_by_creator(self):
        """get_conversations should filter by creator_id."""
        mock_db = MockDatabase()

        await mock_db.save_conversation(
            creator_id="creator-A",
            student_message="Q for A",
            ai_response="A for A",
            sources=[],
            should_escalate=False
        )
        await mock_db.save_conversation(
            creator_id="creator-B",
            student_message="Q for B",
            ai_response="A for B",
            sources=[],
            should_escalate=False
        )

        results_a = await mock_db.get_conversations(creator_id="creator-A")
        results_b = await mock_db.get_conversations(creator_id="creator-B")

        assert len(results_a) == 1
        assert len(results_b) == 1
        assert results_a[0]["creator_id"] == "creator-A"
        assert results_b[0]["creator_id"] == "creator-B"

    @pytest.mark.asyncio
    async def test_mock_supabase_update_credit_usage(self):
        """update_credit_usage should return updated credits."""
        mock_db = MockDatabase()

        # Set initial credits
        mock_db.set_creator_credits("creator-123", 100)

        result = await mock_db.update_credit_usage(
            creator_id="creator-123",
            credits_used=10
        )

        assert result is not None
        assert result["credits_remaining"] == 90

    @pytest.mark.asyncio
    async def test_mock_supabase_update_credit_usage_multiple_times(self):
        """Credits should decrease correctly with multiple updates."""
        mock_db = MockDatabase()
        mock_db.set_creator_credits("creator-123", 100)

        await mock_db.update_credit_usage("creator-123", 30)
        await mock_db.update_credit_usage("creator-123", 20)
        result = await mock_db.update_credit_usage("creator-123", 10)

        assert result["credits_remaining"] == 40

    @pytest.mark.asyncio
    async def test_mock_supabase_update_credit_usage_no_negative(self):
        """Credits should not go below zero."""
        mock_db = MockDatabase()
        mock_db.set_creator_credits("creator-123", 10)

        result = await mock_db.update_credit_usage("creator-123", 50)

        assert result["credits_remaining"] == 0

    @pytest.mark.asyncio
    async def test_mock_supabase_get_creator(self):
        """get_creator should return creator data."""
        mock_db = MockDatabase()
        mock_db.set_creator_credits("creator-123", 75)

        result = await mock_db.get_creator("creator-123")

        assert result is not None
        assert result["id"] == "creator-123"
        assert result["credits_remaining"] == 75

    @pytest.mark.asyncio
    async def test_mock_supabase_create_creator(self):
        """create_creator should return new creator data."""
        mock_db = MockDatabase()

        result = await mock_db.create_creator(
            email="test@example.com",
            name="Test Creator"
        )

        assert result is not None
        assert "id" in result
        assert result["email"] == "test@example.com"
        assert result["name"] == "Test Creator"
        assert "credits_remaining" in result
        assert "created_at" in result


# =============================================================================
# AC-4: Call History Tracking Tests
# =============================================================================

class TestCallHistoryTracking:
    """Tests for call history tracking across all mocks."""

    @pytest.mark.asyncio
    async def test_openai_tracks_call_history(self):
        """MockChatOpenAI should track all calls."""
        mock_llm = MockChatOpenAI()

        await mock_llm.ainvoke([{"role": "user", "content": "First call"}])
        await mock_llm.ainvoke([{"role": "user", "content": "Second call"}])

        assert len(mock_llm.call_history) == 2
        assert mock_llm.call_history[0]["messages"][0]["content"] == "First call"
        assert mock_llm.call_history[1]["messages"][0]["content"] == "Second call"

    @pytest.mark.asyncio
    async def test_openai_call_history_includes_timestamp(self):
        """Call history should include timestamps."""
        mock_llm = MockChatOpenAI()

        await mock_llm.ainvoke([{"role": "user", "content": "Test"}])

        assert "timestamp" in mock_llm.call_history[0]
        assert isinstance(mock_llm.call_history[0]["timestamp"], datetime)

    def test_openai_call_count(self):
        """MockChatOpenAI should provide call count."""
        mock_llm = MockChatOpenAI()
        assert mock_llm.call_count == 0

    @pytest.mark.asyncio
    async def test_openai_call_count_increments(self):
        """Call count should increment with each call."""
        mock_llm = MockChatOpenAI()

        await mock_llm.ainvoke([])
        assert mock_llm.call_count == 1

        await mock_llm.ainvoke([])
        assert mock_llm.call_count == 2

    @pytest.mark.asyncio
    async def test_pinecone_tracks_similarity_search_calls(self):
        """MockVectorStoreService should track similarity_search calls."""
        mock_vs = MockVectorStoreService()

        await mock_vs.similarity_search("query 1", "creator-1", k=4)
        await mock_vs.similarity_search("query 2", "creator-2", k=2)

        assert len(mock_vs.call_history) == 2
        assert mock_vs.call_history[0]["method"] == "similarity_search"
        assert mock_vs.call_history[0]["query"] == "query 1"
        assert mock_vs.call_history[0]["creator_id"] == "creator-1"
        assert mock_vs.call_history[0]["k"] == 4

    @pytest.mark.asyncio
    async def test_pinecone_tracks_add_documents_calls(self):
        """MockVectorStoreService should track add_documents calls."""
        mock_vs = MockVectorStoreService()
        docs = [MockDocument(page_content="Test", metadata={})]

        await mock_vs.add_documents(docs, "creator-123")

        assert any(
            call["method"] == "add_documents"
            for call in mock_vs.call_history
        )

    def test_pinecone_call_count(self):
        """MockVectorStoreService should provide call count."""
        mock_vs = MockVectorStoreService()
        assert mock_vs.call_count == 0

    @pytest.mark.asyncio
    async def test_supabase_tracks_save_conversation_calls(self):
        """MockDatabase should track save_conversation calls."""
        mock_db = MockDatabase()

        await mock_db.save_conversation(
            creator_id="c1",
            student_message="Q",
            ai_response="A",
            sources=[],
            should_escalate=False
        )

        assert len(mock_db.call_history) >= 1
        save_calls = [c for c in mock_db.call_history if c["method"] == "save_conversation"]
        assert len(save_calls) == 1
        assert save_calls[0]["creator_id"] == "c1"

    @pytest.mark.asyncio
    async def test_supabase_tracks_all_method_calls(self):
        """MockDatabase should track calls to all methods."""
        mock_db = MockDatabase()

        await mock_db.create_creator("test@test.com", "Test")
        await mock_db.get_creator("creator-1")
        await mock_db.save_conversation("c1", "Q", "A", [], False)
        await mock_db.get_conversations("c1")
        await mock_db.update_credit_usage("c1", 5)

        methods_called = [c["method"] for c in mock_db.call_history]

        assert "create_creator" in methods_called
        assert "get_creator" in methods_called
        assert "save_conversation" in methods_called
        assert "get_conversations" in methods_called
        assert "update_credit_usage" in methods_called

    def test_supabase_call_count(self):
        """MockDatabase should provide call count."""
        mock_db = MockDatabase()
        assert mock_db.call_count == 0

    def test_all_mocks_have_reset_history_method(self):
        """All mocks should have a method to reset call history."""
        mock_llm = MockChatOpenAI()
        mock_vs = MockVectorStoreService()
        mock_db = MockDatabase()

        assert hasattr(mock_llm, "reset_history")
        assert hasattr(mock_vs, "reset_history")
        assert hasattr(mock_db, "reset_history")

    @pytest.mark.asyncio
    async def test_reset_history_clears_calls(self):
        """reset_history should clear all tracked calls."""
        mock_llm = MockChatOpenAI()

        await mock_llm.ainvoke([])
        await mock_llm.ainvoke([])
        assert mock_llm.call_count == 2

        mock_llm.reset_history()

        assert mock_llm.call_count == 0
        assert len(mock_llm.call_history) == 0


# =============================================================================
# Edge Cases and Error Handling Tests
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_openai_with_empty_messages(self):
        """Mock should handle empty message list."""
        mock_llm = MockChatOpenAI()

        response = await mock_llm.ainvoke([])

        assert response is not None
        assert hasattr(response, "content")

    @pytest.mark.asyncio
    async def test_pinecone_with_zero_k(self):
        """Mock should handle k=0."""
        docs = [MockDocument(page_content="Test", metadata={})]
        mock_vs = MockVectorStoreService(documents=docs)

        results = await mock_vs.similarity_search(
            query="test",
            creator_id="creator-123",
            k=0
        )

        assert results == []

    @pytest.mark.asyncio
    async def test_pinecone_with_empty_query(self):
        """Mock should handle empty query string."""
        mock_vs = MockVectorStoreService()

        results = await mock_vs.similarity_search(
            query="",
            creator_id="creator-123",
            k=4
        )

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_supabase_get_nonexistent_creator(self):
        """Mock should handle getting non-existent creator."""
        mock_db = MockDatabase()

        result = await mock_db.get_creator("nonexistent-id")

        # Should return None or default creator, not raise exception
        # Behavior matches the real Database class fallback

    @pytest.mark.asyncio
    async def test_supabase_conversations_for_nonexistent_creator(self):
        """Mock should handle getting conversations for non-existent creator."""
        mock_db = MockDatabase()

        results = await mock_db.get_conversations("nonexistent-id")

        assert isinstance(results, list)
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_openai_exception_simulation(self):
        """Mock should support simulating exceptions."""
        mock_llm = MockChatOpenAI(raise_exception=ValueError("Simulated API error"))

        with pytest.raises(ValueError, match="Simulated API error"):
            await mock_llm.ainvoke([])

    @pytest.mark.asyncio
    async def test_pinecone_exception_simulation(self):
        """Mock should support simulating exceptions."""
        mock_vs = MockVectorStoreService(raise_exception=ConnectionError("Simulated connection error"))

        with pytest.raises(ConnectionError, match="Simulated connection error"):
            await mock_vs.similarity_search("test", "creator-123", k=4)

    @pytest.mark.asyncio
    async def test_supabase_exception_simulation(self):
        """Mock should support simulating exceptions."""
        mock_db = MockDatabase(raise_exception=TimeoutError("Simulated timeout"))

        with pytest.raises(TimeoutError, match="Simulated timeout"):
            await mock_db.save_conversation("c1", "Q", "A", [], False)


# =============================================================================
# Integration-Ready Tests (Mock Compatibility with Real Interfaces)
# =============================================================================

class TestMockInterfaceCompatibility:
    """Tests ensuring mocks are compatible with real service interfaces."""

    def test_mock_openai_has_ainvoke_method(self):
        """MockChatOpenAI must have ainvoke method matching ChatOpenAI."""
        mock_llm = MockChatOpenAI()

        assert hasattr(mock_llm, "ainvoke")
        assert callable(mock_llm.ainvoke)

    def test_mock_pinecone_has_required_methods(self):
        """MockVectorStoreService must have methods matching VectorStoreService."""
        mock_vs = MockVectorStoreService()

        assert hasattr(mock_vs, "similarity_search")
        assert hasattr(mock_vs, "add_documents")
        assert callable(mock_vs.similarity_search)
        assert callable(mock_vs.add_documents)

    def test_mock_supabase_has_required_methods(self):
        """MockDatabase must have methods matching Database class."""
        mock_db = MockDatabase()

        assert hasattr(mock_db, "is_connected")
        assert hasattr(mock_db, "create_creator")
        assert hasattr(mock_db, "get_creator")
        assert hasattr(mock_db, "save_conversation")
        assert hasattr(mock_db, "get_conversations")
        assert hasattr(mock_db, "update_credit_usage")

    @pytest.mark.asyncio
    async def test_mock_pinecone_similarity_search_signature(self):
        """similarity_search should accept query, creator_id, k, and optional namespace."""
        mock_vs = MockVectorStoreService()

        # Should work without namespace
        await mock_vs.similarity_search(
            query="test",
            creator_id="creator-123",
            k=4
        )

        # Should work with namespace
        await mock_vs.similarity_search(
            query="test",
            creator_id="creator-123",
            k=4,
            namespace="custom-namespace"
        )

    @pytest.mark.asyncio
    async def test_mock_pinecone_add_documents_signature(self):
        """add_documents should accept documents, creator_id, and optional namespace."""
        mock_vs = MockVectorStoreService()
        docs = [MockDocument(page_content="Test", metadata={})]

        # Should work without namespace
        await mock_vs.add_documents(
            documents=docs,
            creator_id="creator-123"
        )

        # Should work with namespace
        await mock_vs.add_documents(
            documents=docs,
            creator_id="creator-123",
            namespace="custom-namespace"
        )
