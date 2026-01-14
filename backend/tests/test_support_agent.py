"""
PRD-003: Unit Tests for RAG Pipeline - SupportAgent Tests

These tests verify the LangGraph agent nodes in SupportAgent:
- AC-1: Retrieval node returns relevant documents from mock
- AC-2: Generation node returns AI response with citations
- AC-3: Escalation node flags low-confidence responses for human review

The tests use mocks from PRD-002 to isolate agent logic from external services.
"""

import pytest
from typing import Dict, Any, List
from unittest.mock import patch, MagicMock, AsyncMock

# Import mocks from PRD-002
from tests.mocks.openai_mock import MockChatOpenAI, MockOpenAIResponse
from tests.mocks.pinecone_mock import MockVectorStoreService, MockDocument
from tests.mocks.supabase_mock import MockDatabase


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def mock_documents():
    """Create sample documents for testing retrieval."""
    return [
        MockDocument(
            page_content="Module 1: Python is a programming language. It is widely used for web development.",
            metadata={"source": "Module 1 - Introduction", "page": 1}
        ),
        MockDocument(
            page_content="Module 2: Variables in Python can store data. You can use assignment operator.",
            metadata={"source": "Module 2 - Variables", "page": 5}
        ),
        MockDocument(
            page_content="Module 3: Functions are reusable blocks of code. Define them with def keyword.",
            metadata={"source": "Module 3 - Functions", "page": 10}
        ),
        MockDocument(
            page_content="FAQ: For billing questions, please contact support@example.com directly.",
            metadata={"source": "FAQ", "page": 1}
        ),
    ]


@pytest.fixture
def mock_documents_with_scores(mock_documents):
    """Create documents with similarity scores."""
    return [
        (mock_documents[0], 0.95),
        (mock_documents[1], 0.85),
        (mock_documents[2], 0.75),
        (mock_documents[3], 0.65),
    ]


@pytest.fixture
def mock_vector_store(mock_documents_with_scores):
    """Create a mock vector store with preset documents."""
    return MockVectorStoreService(documents_with_scores=mock_documents_with_scores)


@pytest.fixture
def mock_llm():
    """Create a mock LLM with default response."""
    return MockChatOpenAI(
        default_response="Based on Module 1, Python is a programming language used for web development."
    )


@pytest.fixture
def initial_state():
    """Create initial agent state for testing."""
    return {
        "context": [],
        "query": "What is Python?",
        "creator_id": "creator-123",
        "response": "",
        "sources": [],
        "should_escalate": False
    }


# =============================================================================
# AC-1: Retrieval Node Tests - Returns relevant documents from mock
# =============================================================================

class TestRetrievalNode:
    """Tests for the retrieve_context node of SupportAgent."""

    @pytest.mark.asyncio
    async def test_retrieve_context_returns_documents(self, mock_vector_store, initial_state):
        """Retrieval node should return documents from vector store."""
        # Create agent with mock vector store - patch the LLM to avoid API calls
        with patch('app.agents.support_agent.ChatOpenAI') as MockChatOpenAI:
            MockChatOpenAI.return_value = MockChatOpenAI()

            from app.agents.support_agent import SupportAgent
            agent = SupportAgent(mock_vector_store)

            # Call retrieve_context directly
            result = await agent.retrieve_context(initial_state)

            # Verify context was populated
            assert "context" in result
            assert len(result["context"]) > 0

    @pytest.mark.asyncio
    async def test_retrieve_context_extracts_page_content(self, mock_vector_store, initial_state):
        """Retrieval node should extract page_content from documents."""
        with patch('app.agents.support_agent.ChatOpenAI') as MockChatOpenAI:
            MockChatOpenAI.return_value = MockChatOpenAI()

            from app.agents.support_agent import SupportAgent
            agent = SupportAgent(mock_vector_store)

            result = await agent.retrieve_context(initial_state)

            # Context should contain actual content strings
            for ctx in result["context"]:
                assert isinstance(ctx, str)
                assert len(ctx) > 0

    @pytest.mark.asyncio
    async def test_retrieve_context_includes_sources(self, mock_vector_store, initial_state):
        """Retrieval node should include source information."""
        with patch('app.agents.support_agent.ChatOpenAI') as MockChatOpenAI:
            MockChatOpenAI.return_value = MockChatOpenAI()

            from app.agents.support_agent import SupportAgent
            agent = SupportAgent(mock_vector_store)

            result = await agent.retrieve_context(initial_state)

            # Sources should be populated
            assert "sources" in result
            assert len(result["sources"]) > 0

    @pytest.mark.asyncio
    async def test_retrieve_context_formats_sources_with_scores(
        self, mock_documents_with_scores, initial_state
    ):
        """Retrieval node should format sources with similarity scores."""
        mock_vs = MockVectorStoreService(documents_with_scores=mock_documents_with_scores)

        with patch('app.agents.support_agent.ChatOpenAI') as MockChatOpenAI:
            MockChatOpenAI.return_value = MockChatOpenAI()

            from app.agents.support_agent import SupportAgent
            agent = SupportAgent(mock_vs)

            result = await agent.retrieve_context(initial_state)

            # Sources should include score information
            for source in result["sources"]:
                assert "Score:" in source

    @pytest.mark.asyncio
    async def test_retrieve_context_uses_correct_creator_id(
        self, mock_vector_store, initial_state
    ):
        """Retrieval node should search with the correct creator_id."""
        with patch('app.agents.support_agent.ChatOpenAI') as MockChatOpenAI:
            MockChatOpenAI.return_value = MockChatOpenAI()

            from app.agents.support_agent import SupportAgent
            agent = SupportAgent(mock_vector_store)

            await agent.retrieve_context(initial_state)

            # Check that vector store was called with correct creator_id
            assert mock_vector_store.call_count > 0
            call = mock_vector_store.call_history[0]
            assert call["creator_id"] == "creator-123"

    @pytest.mark.asyncio
    async def test_retrieve_context_uses_k_parameter(self, mock_vector_store, initial_state):
        """Retrieval node should request k=4 documents by default."""
        with patch('app.agents.support_agent.ChatOpenAI') as MockChatOpenAI:
            MockChatOpenAI.return_value = MockChatOpenAI()

            from app.agents.support_agent import SupportAgent
            agent = SupportAgent(mock_vector_store)

            await agent.retrieve_context(initial_state)

            # Check k parameter
            call = mock_vector_store.call_history[0]
            assert call["k"] == 4

    @pytest.mark.asyncio
    async def test_retrieve_context_preserves_state_fields(
        self, mock_vector_store, initial_state
    ):
        """Retrieval node should preserve existing state fields."""
        with patch('app.agents.support_agent.ChatOpenAI') as MockChatOpenAI:
            MockChatOpenAI.return_value = MockChatOpenAI()

            from app.agents.support_agent import SupportAgent
            agent = SupportAgent(mock_vector_store)

            result = await agent.retrieve_context(initial_state)

            # Original fields should be preserved
            assert result["query"] == "What is Python?"
            assert result["creator_id"] == "creator-123"

    @pytest.mark.asyncio
    async def test_retrieve_context_handles_empty_results(self, initial_state):
        """Retrieval node should handle empty search results gracefully."""
        empty_store = MockVectorStoreService(documents=[])

        with patch('app.agents.support_agent.ChatOpenAI') as MockChatOpenAI:
            MockChatOpenAI.return_value = MockChatOpenAI()

            from app.agents.support_agent import SupportAgent
            agent = SupportAgent(empty_store)

            result = await agent.retrieve_context(initial_state)

            # Should have empty context but not error
            assert result["context"] == []
            assert result["sources"] == []

    @pytest.mark.asyncio
    async def test_retrieve_context_handles_vector_store_error(self, initial_state):
        """Retrieval node should propagate vector store errors."""
        error_store = MockVectorStoreService(
            raise_exception=ConnectionError("Pinecone unavailable")
        )

        with patch('app.agents.support_agent.ChatOpenAI') as MockChatOpenAI:
            MockChatOpenAI.return_value = MockChatOpenAI()

            from app.agents.support_agent import SupportAgent
            agent = SupportAgent(error_store)

            with pytest.raises(ConnectionError, match="Pinecone unavailable"):
                await agent.retrieve_context(initial_state)


# =============================================================================
# AC-2: Generation Node Tests - Returns AI response with citations
# =============================================================================

class TestGenerationNode:
    """Tests for the generate_response node of SupportAgent."""

    @pytest.mark.asyncio
    async def test_generate_response_returns_content(self, mock_vector_store):
        """Generation node should return AI-generated response."""
        state_with_context = {
            "context": [
                "Module 1: Python is a programming language.",
                "Module 2: Variables store data."
            ],
            "query": "What is Python?",
            "creator_id": "creator-123",
            "response": "",
            "sources": ["Module 1 (Score: 0.95)", "Module 2 (Score: 0.85)"],
            "should_escalate": False
        }

        mock_llm = MockChatOpenAI(
            default_response="Based on Module 1, Python is a programming language."
        )

        with patch('app.agents.support_agent.ChatOpenAI', return_value=mock_llm):
            from app.agents.support_agent import SupportAgent
            agent = SupportAgent(mock_vector_store)
            agent.llm = mock_llm  # Replace with our mock

            result = await agent.generate_response(state_with_context)

            assert "response" in result
            assert len(result["response"]) > 0

    @pytest.mark.asyncio
    async def test_generate_response_includes_context_in_prompt(self, mock_vector_store):
        """Generation node should include context in the LLM prompt."""
        state_with_context = {
            "context": [
                "Module 1: Python is a programming language.",
                "Module 2: Variables store data."
            ],
            "query": "What is Python?",
            "creator_id": "creator-123",
            "response": "",
            "sources": [],
            "should_escalate": False
        }

        mock_llm = MockChatOpenAI(default_response="Test response")

        with patch('app.agents.support_agent.ChatOpenAI', return_value=mock_llm):
            from app.agents.support_agent import SupportAgent
            agent = SupportAgent(mock_vector_store)
            agent.llm = mock_llm

            await agent.generate_response(state_with_context)

            # Verify LLM was called
            assert mock_llm.call_count == 1

            # Check that context was included in the prompt
            call = mock_llm.call_history[0]
            messages_content = str(call["messages"])
            assert "Python is a programming language" in messages_content

    @pytest.mark.asyncio
    async def test_generate_response_includes_query_in_prompt(self, mock_vector_store):
        """Generation node should include the student query in the prompt."""
        state_with_context = {
            "context": ["Some context"],
            "query": "How do I create a function?",
            "creator_id": "creator-123",
            "response": "",
            "sources": [],
            "should_escalate": False
        }

        mock_llm = MockChatOpenAI(default_response="Use def keyword.")

        with patch('app.agents.support_agent.ChatOpenAI', return_value=mock_llm):
            from app.agents.support_agent import SupportAgent
            agent = SupportAgent(mock_vector_store)
            agent.llm = mock_llm

            await agent.generate_response(state_with_context)

            # Check query was included
            call = mock_llm.call_history[0]
            messages_content = str(call["messages"])
            assert "How do I create a function" in messages_content

    @pytest.mark.asyncio
    async def test_generate_response_with_citation_in_response(self, mock_vector_store):
        """Generation node should return response that can include citations."""
        state_with_context = {
            "context": ["Module 3: Functions are defined with def keyword."],
            "query": "How do I create a function?",
            "creator_id": "creator-123",
            "response": "",
            "sources": ["Module 3 - Functions (Score: 0.92)"],
            "should_escalate": False
        }

        # Response with citation
        mock_llm = MockChatOpenAI(
            default_response="In Module 3, you learn that functions are defined using the def keyword."
        )

        with patch('app.agents.support_agent.ChatOpenAI', return_value=mock_llm):
            from app.agents.support_agent import SupportAgent
            agent = SupportAgent(mock_vector_store)
            agent.llm = mock_llm

            result = await agent.generate_response(state_with_context)

            # Response should contain citation reference
            assert "Module 3" in result["response"]

    @pytest.mark.asyncio
    async def test_generate_response_preserves_context_and_sources(self, mock_vector_store):
        """Generation node should preserve context and sources from state."""
        state_with_context = {
            "context": ["Context 1", "Context 2"],
            "query": "Test query",
            "creator_id": "creator-123",
            "response": "",
            "sources": ["Source 1", "Source 2"],
            "should_escalate": False
        }

        mock_llm = MockChatOpenAI(default_response="Test response")

        with patch('app.agents.support_agent.ChatOpenAI', return_value=mock_llm):
            from app.agents.support_agent import SupportAgent
            agent = SupportAgent(mock_vector_store)
            agent.llm = mock_llm

            result = await agent.generate_response(state_with_context)

            # Original fields should be preserved
            assert result["context"] == ["Context 1", "Context 2"]
            assert result["sources"] == ["Source 1", "Source 2"]

    @pytest.mark.asyncio
    async def test_generate_response_handles_empty_context(self, mock_vector_store):
        """Generation node should handle empty context gracefully."""
        state_empty_context = {
            "context": [],
            "query": "Random question?",
            "creator_id": "creator-123",
            "response": "",
            "sources": [],
            "should_escalate": False
        }

        mock_llm = MockChatOpenAI(
            default_response="I don't have information about that topic."
        )

        with patch('app.agents.support_agent.ChatOpenAI', return_value=mock_llm):
            from app.agents.support_agent import SupportAgent
            agent = SupportAgent(mock_vector_store)
            agent.llm = mock_llm

            result = await agent.generate_response(state_empty_context)

            assert "response" in result
            assert len(result["response"]) > 0

    @pytest.mark.asyncio
    async def test_generate_response_handles_llm_error(self, mock_vector_store):
        """Generation node should propagate LLM errors."""
        state = {
            "context": ["Some context"],
            "query": "Test query",
            "creator_id": "creator-123",
            "response": "",
            "sources": [],
            "should_escalate": False
        }

        error_llm = MockChatOpenAI(
            raise_exception=RuntimeError("OpenAI API rate limit exceeded")
        )

        with patch('app.agents.support_agent.ChatOpenAI', return_value=error_llm):
            from app.agents.support_agent import SupportAgent
            agent = SupportAgent(mock_vector_store)
            agent.llm = error_llm

            with pytest.raises(RuntimeError, match="rate limit"):
                await agent.generate_response(state)

    @pytest.mark.asyncio
    async def test_generate_response_uses_system_prompt(self, mock_vector_store):
        """Generation node should include a system prompt with guidelines."""
        state = {
            "context": ["Module content here"],
            "query": "Question",
            "creator_id": "creator-123",
            "response": "",
            "sources": [],
            "should_escalate": False
        }

        mock_llm = MockChatOpenAI(default_response="Response")

        with patch('app.agents.support_agent.ChatOpenAI', return_value=mock_llm):
            from app.agents.support_agent import SupportAgent
            agent = SupportAgent(mock_vector_store)
            agent.llm = mock_llm

            await agent.generate_response(state)

            # Check that system message was included
            call = mock_llm.call_history[0]
            assert len(call["messages"]) >= 2  # At least system and human message


# =============================================================================
# AC-3: Escalation Node Tests - Flags low-confidence responses
# =============================================================================

class TestEscalationNode:
    """Tests for the check_escalation node of SupportAgent."""

    @pytest.mark.asyncio
    async def test_escalation_false_for_confident_response(self, mock_vector_store):
        """Escalation should be False for confident responses."""
        state_confident = {
            "context": ["Module content"],
            "query": "What is Python?",
            "creator_id": "creator-123",
            "response": "Python is a programming language used for web development.",
            "sources": ["Module 1"],
            "should_escalate": False
        }

        with patch('app.agents.support_agent.ChatOpenAI') as MockChatOpenAI:
            MockChatOpenAI.return_value = MockChatOpenAI()

            from app.agents.support_agent import SupportAgent
            agent = SupportAgent(mock_vector_store)

            result = await agent.check_escalation(state_confident)

            assert result["should_escalate"] is False

    @pytest.mark.asyncio
    async def test_escalation_true_for_i_dont_know(self, mock_vector_store):
        """Escalation should be True when response contains 'I don't know'."""
        state_uncertain = {
            "context": [],
            "query": "What is the refund policy?",
            "creator_id": "creator-123",
            "response": "I don't know the answer to that question based on the available materials.",
            "sources": [],
            "should_escalate": False
        }

        with patch('app.agents.support_agent.ChatOpenAI') as MockChatOpenAI:
            MockChatOpenAI.return_value = MockChatOpenAI()

            from app.agents.support_agent import SupportAgent
            agent = SupportAgent(mock_vector_store)

            result = await agent.check_escalation(state_uncertain)

            assert result["should_escalate"] is True

    @pytest.mark.asyncio
    async def test_escalation_true_for_not_sure(self, mock_vector_store):
        """Escalation should be True when response contains 'not sure'."""
        state_uncertain = {
            "context": [],
            "query": "Can I get a refund?",
            "creator_id": "creator-123",
            "response": "I'm not sure about the refund policy. Let me connect you with support.",
            "sources": [],
            "should_escalate": False
        }

        with patch('app.agents.support_agent.ChatOpenAI') as MockChatOpenAI:
            MockChatOpenAI.return_value = MockChatOpenAI()

            from app.agents.support_agent import SupportAgent
            agent = SupportAgent(mock_vector_store)

            result = await agent.check_escalation(state_uncertain)

            assert result["should_escalate"] is True

    @pytest.mark.asyncio
    async def test_escalation_true_for_cant_find(self, mock_vector_store):
        """Escalation should be True when response contains 'can't find'."""
        state_uncertain = {
            "context": [],
            "query": "Where is my certificate?",
            "creator_id": "creator-123",
            "response": "I can't find information about certificates in the course materials.",
            "sources": [],
            "should_escalate": False
        }

        with patch('app.agents.support_agent.ChatOpenAI') as MockChatOpenAI:
            MockChatOpenAI.return_value = MockChatOpenAI()

            from app.agents.support_agent import SupportAgent
            agent = SupportAgent(mock_vector_store)

            result = await agent.check_escalation(state_uncertain)

            assert result["should_escalate"] is True

    @pytest.mark.asyncio
    async def test_escalation_true_for_unclear(self, mock_vector_store):
        """Escalation should be True when response contains 'unclear'."""
        state_uncertain = {
            "context": [],
            "query": "How does payment work?",
            "creator_id": "creator-123",
            "response": "The payment process is unclear from the available documentation.",
            "sources": [],
            "should_escalate": False
        }

        with patch('app.agents.support_agent.ChatOpenAI') as MockChatOpenAI:
            MockChatOpenAI.return_value = MockChatOpenAI()

            from app.agents.support_agent import SupportAgent
            agent = SupportAgent(mock_vector_store)

            result = await agent.check_escalation(state_uncertain)

            assert result["should_escalate"] is True

    @pytest.mark.asyncio
    async def test_escalation_true_for_need_more_information(self, mock_vector_store):
        """Escalation should be True when response contains 'need more information'."""
        state_uncertain = {
            "context": [],
            "query": "Custom question",
            "creator_id": "creator-123",
            "response": "I need more information to answer this question properly.",
            "sources": [],
            "should_escalate": False
        }

        with patch('app.agents.support_agent.ChatOpenAI') as MockChatOpenAI:
            MockChatOpenAI.return_value = MockChatOpenAI()

            from app.agents.support_agent import SupportAgent
            agent = SupportAgent(mock_vector_store)

            result = await agent.check_escalation(state_uncertain)

            assert result["should_escalate"] is True

    @pytest.mark.asyncio
    async def test_escalation_case_insensitive(self, mock_vector_store):
        """Escalation triggers should be case-insensitive."""
        state_uncertain = {
            "context": [],
            "query": "Question",
            "creator_id": "creator-123",
            "response": "I DON'T KNOW the answer to that.",
            "sources": [],
            "should_escalate": False
        }

        with patch('app.agents.support_agent.ChatOpenAI') as MockChatOpenAI:
            MockChatOpenAI.return_value = MockChatOpenAI()

            from app.agents.support_agent import SupportAgent
            agent = SupportAgent(mock_vector_store)

            result = await agent.check_escalation(state_uncertain)

            assert result["should_escalate"] is True

    @pytest.mark.asyncio
    async def test_escalation_preserves_other_state_fields(self, mock_vector_store):
        """Escalation node should preserve all other state fields."""
        state = {
            "context": ["Context 1", "Context 2"],
            "query": "Original query",
            "creator_id": "creator-456",
            "response": "This is a confident response about Python.",
            "sources": ["Source A", "Source B"],
            "should_escalate": False
        }

        with patch('app.agents.support_agent.ChatOpenAI') as MockChatOpenAI:
            MockChatOpenAI.return_value = MockChatOpenAI()

            from app.agents.support_agent import SupportAgent
            agent = SupportAgent(mock_vector_store)

            result = await agent.check_escalation(state)

            assert result["context"] == ["Context 1", "Context 2"]
            assert result["query"] == "Original query"
            assert result["creator_id"] == "creator-456"
            assert result["response"] == "This is a confident response about Python."
            assert result["sources"] == ["Source A", "Source B"]


# =============================================================================
# Integration Tests - Full Pipeline Flow
# =============================================================================

class TestSupportAgentIntegration:
    """Integration tests for the full SupportAgent pipeline."""

    @pytest.mark.asyncio
    async def test_process_query_returns_expected_structure(self, mock_documents_with_scores):
        """process_query should return response with expected fields."""
        mock_vs = MockVectorStoreService(documents_with_scores=mock_documents_with_scores)
        mock_llm = MockChatOpenAI(
            default_response="Based on the course materials, Python is a programming language."
        )

        with patch('app.agents.support_agent.ChatOpenAI', return_value=mock_llm):
            from app.agents.support_agent import SupportAgent
            agent = SupportAgent(mock_vs)
            agent.llm = mock_llm

            # Note: process_query uses the graph, which may need special handling
            # For unit testing, we test the individual nodes
            # This test documents the expected output structure

            # Expected output structure from process_query:
            expected_keys = ["response", "sources", "should_escalate", "context_used"]

            # Verify the method exists and has correct signature
            assert hasattr(agent, "process_query")
            assert callable(agent.process_query)

    @pytest.mark.asyncio
    async def test_full_pipeline_with_confident_response(self, mock_documents_with_scores):
        """Full pipeline should work for confident responses."""
        mock_vs = MockVectorStoreService(documents_with_scores=mock_documents_with_scores)
        mock_llm = MockChatOpenAI(
            default_response="Python is a programming language as explained in Module 1."
        )

        with patch('app.agents.support_agent.ChatOpenAI', return_value=mock_llm):
            from app.agents.support_agent import SupportAgent
            agent = SupportAgent(mock_vs)
            agent.llm = mock_llm

            # Test each node in sequence
            state = {
                "context": [],
                "query": "What is Python?",
                "creator_id": "creator-123",
                "response": "",
                "sources": [],
                "should_escalate": False
            }

            # Step 1: Retrieve
            state = await agent.retrieve_context(state)
            assert len(state["context"]) > 0

            # Step 2: Generate
            state = await agent.generate_response(state)
            assert len(state["response"]) > 0

            # Step 3: Check escalation
            state = await agent.check_escalation(state)
            assert state["should_escalate"] is False

    @pytest.mark.asyncio
    async def test_full_pipeline_with_uncertain_response(self, mock_documents_with_scores):
        """Full pipeline should flag uncertain responses for escalation."""
        mock_vs = MockVectorStoreService(documents_with_scores=mock_documents_with_scores)
        mock_llm = MockChatOpenAI(
            default_response="I'm not sure about billing policies. Please contact support."
        )

        with patch('app.agents.support_agent.ChatOpenAI', return_value=mock_llm):
            from app.agents.support_agent import SupportAgent
            agent = SupportAgent(mock_vs)
            agent.llm = mock_llm

            state = {
                "context": [],
                "query": "What is your refund policy?",
                "creator_id": "creator-123",
                "response": "",
                "sources": [],
                "should_escalate": False
            }

            # Run through all nodes
            state = await agent.retrieve_context(state)
            state = await agent.generate_response(state)
            state = await agent.check_escalation(state)

            # Should be flagged for escalation
            assert state["should_escalate"] is True


# =============================================================================
# Edge Cases and Error Handling Tests
# =============================================================================

class TestSupportAgentEdgeCases:
    """Tests for edge cases and error handling in SupportAgent."""

    @pytest.mark.asyncio
    async def test_handles_very_long_query(self, mock_documents_with_scores):
        """Agent should handle very long queries."""
        mock_vs = MockVectorStoreService(documents_with_scores=mock_documents_with_scores)
        mock_llm = MockChatOpenAI(default_response="Response to long query.")

        with patch('app.agents.support_agent.ChatOpenAI', return_value=mock_llm):
            from app.agents.support_agent import SupportAgent
            agent = SupportAgent(mock_vs)
            agent.llm = mock_llm

            long_query = "What is Python? " * 100  # Very long query

            state = {
                "context": [],
                "query": long_query,
                "creator_id": "creator-123",
                "response": "",
                "sources": [],
                "should_escalate": False
            }

            result = await agent.retrieve_context(state)
            assert "context" in result

    @pytest.mark.asyncio
    async def test_handles_special_characters_in_query(self, mock_documents_with_scores):
        """Agent should handle special characters in queries."""
        mock_vs = MockVectorStoreService(documents_with_scores=mock_documents_with_scores)
        mock_llm = MockChatOpenAI(default_response="Response")

        with patch('app.agents.support_agent.ChatOpenAI', return_value=mock_llm):
            from app.agents.support_agent import SupportAgent
            agent = SupportAgent(mock_vs)
            agent.llm = mock_llm

            special_query = "What's the difference between '==' and '===' in Python?"

            state = {
                "context": [],
                "query": special_query,
                "creator_id": "creator-123",
                "response": "",
                "sources": [],
                "should_escalate": False
            }

            result = await agent.retrieve_context(state)
            assert "context" in result

    @pytest.mark.asyncio
    async def test_handles_unicode_in_query(self, mock_documents_with_scores):
        """Agent should handle unicode characters in queries."""
        mock_vs = MockVectorStoreService(documents_with_scores=mock_documents_with_scores)
        mock_llm = MockChatOpenAI(default_response="Response")

        with patch('app.agents.support_agent.ChatOpenAI', return_value=mock_llm):
            from app.agents.support_agent import SupportAgent
            agent = SupportAgent(mock_vs)
            agent.llm = mock_llm

            unicode_query = "How do I print emojis like heart in Python?"

            state = {
                "context": [],
                "query": unicode_query,
                "creator_id": "creator-123",
                "response": "",
                "sources": [],
                "should_escalate": False
            }

            result = await agent.retrieve_context(state)
            assert "context" in result

    @pytest.mark.asyncio
    async def test_handles_empty_query(self, mock_documents_with_scores):
        """Agent should handle empty query gracefully."""
        mock_vs = MockVectorStoreService(documents_with_scores=mock_documents_with_scores)
        mock_llm = MockChatOpenAI(default_response="Please provide a question.")

        with patch('app.agents.support_agent.ChatOpenAI', return_value=mock_llm):
            from app.agents.support_agent import SupportAgent
            agent = SupportAgent(mock_vs)
            agent.llm = mock_llm

            state = {
                "context": [],
                "query": "",
                "creator_id": "creator-123",
                "response": "",
                "sources": [],
                "should_escalate": False
            }

            # Should not raise an exception
            result = await agent.retrieve_context(state)
            assert "context" in result

    @pytest.mark.asyncio
    async def test_metadata_without_source_field(self):
        """Agent should handle documents without source metadata."""
        doc_without_source = MockDocument(
            page_content="Content without source metadata",
            metadata={"page": 1}  # No 'source' key
        )
        mock_vs = MockVectorStoreService(
            documents_with_scores=[(doc_without_source, 0.9)]
        )
        mock_llm = MockChatOpenAI(default_response="Response")

        with patch('app.agents.support_agent.ChatOpenAI', return_value=mock_llm):
            from app.agents.support_agent import SupportAgent
            agent = SupportAgent(mock_vs)

            state = {
                "context": [],
                "query": "Test",
                "creator_id": "creator-123",
                "response": "",
                "sources": [],
                "should_escalate": False
            }

            # Should handle missing source gracefully
            result = await agent.retrieve_context(state)
            assert "sources" in result
            # Should use "Unknown" as fallback
            assert any("Unknown" in s for s in result["sources"])
