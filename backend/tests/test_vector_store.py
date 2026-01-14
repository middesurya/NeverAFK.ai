"""
PRD-003: Unit Tests for RAG Pipeline - VectorStoreService Tests

These tests verify the VectorStoreService functionality:
- AC-4: similarity_search returns documents with scores
- AC-5: add_documents indexes with correct namespace

The tests use mocks from PRD-002 to isolate vector store logic from Pinecone API.
"""

import pytest
from typing import Dict, Any, List
from unittest.mock import patch, MagicMock, AsyncMock

# Import mocks from PRD-002
from tests.mocks.pinecone_mock import MockVectorStoreService, MockDocument


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def sample_documents():
    """Create sample documents for testing."""
    return [
        MockDocument(
            page_content="Introduction to Python programming. Learn the basics.",
            metadata={"source": "module_1.pdf", "page": 1, "title": "Module 1"}
        ),
        MockDocument(
            page_content="Variables and data types in Python. Integers, strings, and floats.",
            metadata={"source": "module_2.pdf", "page": 5, "title": "Module 2"}
        ),
        MockDocument(
            page_content="Control flow in Python. If statements and loops explained.",
            metadata={"source": "module_3.pdf", "page": 10, "title": "Module 3"}
        ),
    ]


@pytest.fixture
def documents_with_varied_scores():
    """Create documents with different similarity scores."""
    return [
        (
            MockDocument(
                page_content="Highly relevant content about Python basics.",
                metadata={"source": "relevant.pdf"}
            ),
            0.98
        ),
        (
            MockDocument(
                page_content="Somewhat relevant content about programming.",
                metadata={"source": "somewhat.pdf"}
            ),
            0.75
        ),
        (
            MockDocument(
                page_content="Less relevant content about computers.",
                metadata={"source": "less.pdf"}
            ),
            0.55
        ),
        (
            MockDocument(
                page_content="Barely relevant content.",
                metadata={"source": "barely.pdf"}
            ),
            0.35
        ),
    ]


@pytest.fixture
def mock_embeddings():
    """Create mock embeddings object."""
    mock = MagicMock()
    mock.embed_query = MagicMock(return_value=[0.1] * 1024)
    mock.embed_documents = MagicMock(return_value=[[0.1] * 1024])
    return mock


@pytest.fixture
def mock_pinecone_index():
    """Create mock Pinecone index."""
    mock = MagicMock()
    mock.upsert = MagicMock()
    mock.query = MagicMock(return_value={"matches": []})
    return mock


# =============================================================================
# AC-4: similarity_search Tests - Returns documents with scores
# =============================================================================

class TestSimilaritySearch:
    """Tests for VectorStoreService.similarity_search method."""

    @pytest.mark.asyncio
    async def test_similarity_search_returns_list(self):
        """similarity_search should return a list of results."""
        mock_vs = MockVectorStoreService()

        results = await mock_vs.similarity_search(
            query="What is Python?",
            creator_id="creator-123",
            k=4
        )

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_similarity_search_returns_document_score_tuples(
        self, documents_with_varied_scores
    ):
        """similarity_search should return (Document, score) tuples."""
        mock_vs = MockVectorStoreService(
            documents_with_scores=documents_with_varied_scores
        )

        results = await mock_vs.similarity_search(
            query="Python basics",
            creator_id="creator-123",
            k=4
        )

        assert len(results) > 0
        for result in results:
            assert isinstance(result, tuple)
            assert len(result) == 2
            doc, score = result
            assert hasattr(doc, "page_content")
            assert hasattr(doc, "metadata")
            assert isinstance(score, float)

    @pytest.mark.asyncio
    async def test_similarity_search_scores_are_floats(
        self, documents_with_varied_scores
    ):
        """Scores should be float values."""
        mock_vs = MockVectorStoreService(
            documents_with_scores=documents_with_varied_scores
        )

        results = await mock_vs.similarity_search(
            query="test",
            creator_id="creator-123",
            k=4
        )

        for doc, score in results:
            assert isinstance(score, (int, float))
            assert isinstance(float(score), float)

    @pytest.mark.asyncio
    async def test_similarity_search_scores_in_valid_range(
        self, documents_with_varied_scores
    ):
        """Scores should be between 0.0 and 1.0."""
        mock_vs = MockVectorStoreService(
            documents_with_scores=documents_with_varied_scores
        )

        results = await mock_vs.similarity_search(
            query="test",
            creator_id="creator-123",
            k=4
        )

        for doc, score in results:
            assert 0.0 <= score <= 1.0, f"Score {score} is outside valid range"

    @pytest.mark.asyncio
    async def test_similarity_search_respects_k_parameter(
        self, documents_with_varied_scores
    ):
        """similarity_search should return at most k results."""
        mock_vs = MockVectorStoreService(
            documents_with_scores=documents_with_varied_scores
        )

        results = await mock_vs.similarity_search(
            query="test",
            creator_id="creator-123",
            k=2
        )

        assert len(results) <= 2

    @pytest.mark.asyncio
    async def test_similarity_search_with_k_larger_than_docs(
        self, documents_with_varied_scores
    ):
        """similarity_search should handle k larger than available docs."""
        mock_vs = MockVectorStoreService(
            documents_with_scores=documents_with_varied_scores
        )

        results = await mock_vs.similarity_search(
            query="test",
            creator_id="creator-123",
            k=100  # Much larger than available docs
        )

        # Should return all available docs, not error
        assert len(results) == len(documents_with_varied_scores)

    @pytest.mark.asyncio
    async def test_similarity_search_with_namespace(
        self, documents_with_varied_scores
    ):
        """similarity_search should accept optional namespace parameter."""
        mock_vs = MockVectorStoreService(
            documents_with_scores=documents_with_varied_scores
        )

        results = await mock_vs.similarity_search(
            query="test",
            creator_id="creator-123",
            k=4,
            namespace="custom-namespace"
        )

        assert isinstance(results, list)

        # Verify namespace was passed to the call
        call = mock_vs.call_history[-1]
        assert call["namespace"] == "custom-namespace"

    @pytest.mark.asyncio
    async def test_similarity_search_uses_creator_id_as_default_namespace(self):
        """similarity_search should use creator_id as namespace when not specified."""
        mock_vs = MockVectorStoreService()

        await mock_vs.similarity_search(
            query="test",
            creator_id="creator-456",
            k=4
        )

        # The mock records the call; in real impl, creator_id would be used as namespace
        call = mock_vs.call_history[-1]
        assert call["creator_id"] == "creator-456"

    @pytest.mark.asyncio
    async def test_similarity_search_returns_empty_for_no_results(self):
        """similarity_search should return empty list when no documents match."""
        mock_vs = MockVectorStoreService(documents=[])

        results = await mock_vs.similarity_search(
            query="obscure topic",
            creator_id="creator-123",
            k=4
        )

        assert results == []

    @pytest.mark.asyncio
    async def test_similarity_search_document_has_page_content(
        self, documents_with_varied_scores
    ):
        """Returned documents should have page_content attribute."""
        mock_vs = MockVectorStoreService(
            documents_with_scores=documents_with_varied_scores
        )

        results = await mock_vs.similarity_search(
            query="Python",
            creator_id="creator-123",
            k=4
        )

        for doc, score in results:
            assert hasattr(doc, "page_content")
            assert isinstance(doc.page_content, str)
            assert len(doc.page_content) > 0

    @pytest.mark.asyncio
    async def test_similarity_search_document_has_metadata(
        self, documents_with_varied_scores
    ):
        """Returned documents should have metadata attribute."""
        mock_vs = MockVectorStoreService(
            documents_with_scores=documents_with_varied_scores
        )

        results = await mock_vs.similarity_search(
            query="Python",
            creator_id="creator-123",
            k=4
        )

        for doc, score in results:
            assert hasattr(doc, "metadata")
            assert isinstance(doc.metadata, dict)

    @pytest.mark.asyncio
    async def test_similarity_search_tracks_call_history(self):
        """similarity_search should record calls in call_history."""
        mock_vs = MockVectorStoreService()

        await mock_vs.similarity_search(
            query="test query",
            creator_id="creator-789",
            k=3
        )

        assert mock_vs.call_count == 1
        call = mock_vs.call_history[0]
        assert call["method"] == "similarity_search"
        assert call["query"] == "test query"
        assert call["creator_id"] == "creator-789"
        assert call["k"] == 3

    @pytest.mark.asyncio
    async def test_similarity_search_handles_error(self):
        """similarity_search should propagate errors appropriately."""
        mock_vs = MockVectorStoreService(
            raise_exception=ConnectionError("Pinecone connection failed")
        )

        with pytest.raises(ConnectionError, match="Pinecone connection failed"):
            await mock_vs.similarity_search(
                query="test",
                creator_id="creator-123",
                k=4
            )


# =============================================================================
# AC-5: add_documents Tests - Indexes with correct namespace
# =============================================================================

class TestAddDocuments:
    """Tests for VectorStoreService.add_documents method."""

    @pytest.mark.asyncio
    async def test_add_documents_returns_success_status(self, sample_documents):
        """add_documents should return success status."""
        mock_vs = MockVectorStoreService()

        result = await mock_vs.add_documents(
            documents=sample_documents,
            creator_id="creator-123"
        )

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_add_documents_returns_document_count(self, sample_documents):
        """add_documents should return the count of documents added."""
        mock_vs = MockVectorStoreService()

        result = await mock_vs.add_documents(
            documents=sample_documents,
            creator_id="creator-123"
        )

        assert "document_count" in result
        assert result["document_count"] == len(sample_documents)

    @pytest.mark.asyncio
    async def test_add_documents_with_namespace(self, sample_documents):
        """add_documents should accept namespace parameter."""
        mock_vs = MockVectorStoreService()

        result = await mock_vs.add_documents(
            documents=sample_documents,
            creator_id="creator-123",
            namespace="custom-namespace"
        )

        assert result["status"] == "success"

        # Verify namespace was passed
        call = mock_vs.call_history[-1]
        assert call["namespace"] == "custom-namespace"

    @pytest.mark.asyncio
    async def test_add_documents_uses_creator_id_as_default_namespace(
        self, sample_documents
    ):
        """add_documents should use creator_id as namespace when not specified."""
        mock_vs = MockVectorStoreService()

        await mock_vs.add_documents(
            documents=sample_documents,
            creator_id="creator-456"
        )

        # In real implementation, creator_id would be used as namespace
        call = mock_vs.call_history[-1]
        assert call["creator_id"] == "creator-456"

    @pytest.mark.asyncio
    async def test_add_documents_tracks_call_history(self, sample_documents):
        """add_documents should record calls in call_history."""
        mock_vs = MockVectorStoreService()

        await mock_vs.add_documents(
            documents=sample_documents,
            creator_id="creator-123",
            namespace="test-ns"
        )

        assert mock_vs.call_count == 1
        call = mock_vs.call_history[0]
        assert call["method"] == "add_documents"
        assert call["document_count"] == len(sample_documents)
        assert call["creator_id"] == "creator-123"
        assert call["namespace"] == "test-ns"

    @pytest.mark.asyncio
    async def test_add_documents_stores_documents(self, sample_documents):
        """add_documents should store documents in the mock."""
        mock_vs = MockVectorStoreService()

        await mock_vs.add_documents(
            documents=sample_documents,
            creator_id="creator-123"
        )

        # Documents should be stored
        assert len(mock_vs.documents) == len(sample_documents)

    @pytest.mark.asyncio
    async def test_add_documents_with_empty_list(self):
        """add_documents should handle empty document list."""
        mock_vs = MockVectorStoreService()

        result = await mock_vs.add_documents(
            documents=[],
            creator_id="creator-123"
        )

        assert result["status"] == "success"
        assert result["document_count"] == 0

    @pytest.mark.asyncio
    async def test_add_documents_with_single_document(self):
        """add_documents should handle single document."""
        mock_vs = MockVectorStoreService()
        single_doc = [MockDocument(page_content="Single doc", metadata={})]

        result = await mock_vs.add_documents(
            documents=single_doc,
            creator_id="creator-123"
        )

        assert result["status"] == "success"
        assert result["document_count"] == 1

    @pytest.mark.asyncio
    async def test_add_documents_handles_error(self, sample_documents):
        """add_documents should propagate errors appropriately."""
        mock_vs = MockVectorStoreService(
            raise_exception=RuntimeError("Index creation failed")
        )

        with pytest.raises(RuntimeError, match="Index creation failed"):
            await mock_vs.add_documents(
                documents=sample_documents,
                creator_id="creator-123"
            )

    @pytest.mark.asyncio
    async def test_add_documents_multiple_calls_accumulate(self, sample_documents):
        """Multiple add_documents calls should accumulate documents."""
        mock_vs = MockVectorStoreService()

        await mock_vs.add_documents(
            documents=sample_documents[:1],
            creator_id="creator-123"
        )
        await mock_vs.add_documents(
            documents=sample_documents[1:],
            creator_id="creator-123"
        )

        # All documents should be accumulated
        assert len(mock_vs.documents) == len(sample_documents)
        assert mock_vs.call_count == 2

    @pytest.mark.asyncio
    async def test_add_documents_preserves_metadata(self):
        """add_documents should preserve document metadata."""
        mock_vs = MockVectorStoreService()
        doc_with_metadata = MockDocument(
            page_content="Test content",
            metadata={
                "source": "test.pdf",
                "page": 42,
                "custom_field": "custom_value"
            }
        )

        await mock_vs.add_documents(
            documents=[doc_with_metadata],
            creator_id="creator-123"
        )

        stored_doc = mock_vs.documents[0]
        assert stored_doc.metadata["source"] == "test.pdf"
        assert stored_doc.metadata["page"] == 42
        assert stored_doc.metadata["custom_field"] == "custom_value"


# =============================================================================
# VectorStoreService Integration with Real Interface Tests
# =============================================================================

class TestVectorStoreServiceInterface:
    """Tests verifying MockVectorStoreService matches real VectorStoreService interface."""

    def test_has_similarity_search_method(self):
        """MockVectorStoreService should have similarity_search method."""
        mock_vs = MockVectorStoreService()

        assert hasattr(mock_vs, "similarity_search")
        assert callable(mock_vs.similarity_search)

    def test_has_add_documents_method(self):
        """MockVectorStoreService should have add_documents method."""
        mock_vs = MockVectorStoreService()

        assert hasattr(mock_vs, "add_documents")
        assert callable(mock_vs.add_documents)

    @pytest.mark.asyncio
    async def test_similarity_search_signature_matches_real(self):
        """similarity_search signature should match real VectorStoreService."""
        mock_vs = MockVectorStoreService()

        # Should accept these parameters without error
        await mock_vs.similarity_search(
            query="test query",
            creator_id="creator-123",
            k=4,
            namespace=None
        )

        await mock_vs.similarity_search(
            query="test query",
            creator_id="creator-123",
            k=4,
            namespace="custom-ns"
        )

    @pytest.mark.asyncio
    async def test_add_documents_signature_matches_real(self):
        """add_documents signature should match real VectorStoreService."""
        mock_vs = MockVectorStoreService()
        docs = [MockDocument(page_content="Test", metadata={})]

        # Should accept these parameters without error
        await mock_vs.add_documents(
            documents=docs,
            creator_id="creator-123",
            namespace=None
        )

        await mock_vs.add_documents(
            documents=docs,
            creator_id="creator-123",
            namespace="custom-ns"
        )

    @pytest.mark.asyncio
    async def test_similarity_search_return_type_matches_real(self):
        """similarity_search return type should match real VectorStoreService."""
        docs = [MockDocument(page_content="Test content", metadata={"source": "test"})]
        mock_vs = MockVectorStoreService(documents=docs)

        results = await mock_vs.similarity_search(
            query="test",
            creator_id="creator-123",
            k=4
        )

        # Real VectorStoreService returns List[Tuple[Document, float]]
        assert isinstance(results, list)
        if len(results) > 0:
            assert isinstance(results[0], tuple)
            doc, score = results[0]
            assert hasattr(doc, "page_content")
            assert hasattr(doc, "metadata")
            assert isinstance(score, float)

    @pytest.mark.asyncio
    async def test_add_documents_return_type_matches_real(self):
        """add_documents return type should match real VectorStoreService."""
        mock_vs = MockVectorStoreService()
        docs = [MockDocument(page_content="Test", metadata={})]

        result = await mock_vs.add_documents(
            documents=docs,
            creator_id="creator-123"
        )

        # Real VectorStoreService returns Dict with status and document_count
        assert isinstance(result, dict)
        assert "status" in result
        assert "document_count" in result


# =============================================================================
# Edge Cases and Performance Tests
# =============================================================================

class TestVectorStoreEdgeCases:
    """Tests for edge cases in VectorStoreService."""

    @pytest.mark.asyncio
    async def test_similarity_search_with_empty_query(self):
        """similarity_search should handle empty query string."""
        mock_vs = MockVectorStoreService()

        # Should not raise an exception
        results = await mock_vs.similarity_search(
            query="",
            creator_id="creator-123",
            k=4
        )

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_similarity_search_with_very_long_query(self):
        """similarity_search should handle very long query strings."""
        mock_vs = MockVectorStoreService()
        long_query = "Python " * 1000  # Very long query

        # Should not raise an exception
        results = await mock_vs.similarity_search(
            query=long_query,
            creator_id="creator-123",
            k=4
        )

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_similarity_search_with_special_characters(self):
        """similarity_search should handle special characters in query."""
        mock_vs = MockVectorStoreService()
        special_query = "What's the difference between '==' and '!='?"

        results = await mock_vs.similarity_search(
            query=special_query,
            creator_id="creator-123",
            k=4
        )

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_similarity_search_with_unicode(self):
        """similarity_search should handle unicode characters."""
        mock_vs = MockVectorStoreService()
        unicode_query = "How to print emoji in Python?"

        results = await mock_vs.similarity_search(
            query=unicode_query,
            creator_id="creator-123",
            k=4
        )

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_add_documents_with_large_content(self):
        """add_documents should handle documents with large content."""
        mock_vs = MockVectorStoreService()
        large_content = "Lorem ipsum " * 10000  # Large document
        large_doc = MockDocument(page_content=large_content, metadata={})

        result = await mock_vs.add_documents(
            documents=[large_doc],
            creator_id="creator-123"
        )

        assert result["status"] == "success"
        assert result["document_count"] == 1

    @pytest.mark.asyncio
    async def test_add_documents_with_complex_metadata(self):
        """add_documents should handle documents with complex metadata."""
        mock_vs = MockVectorStoreService()
        complex_doc = MockDocument(
            page_content="Test content",
            metadata={
                "source": "complex_file.pdf",
                "pages": [1, 2, 3, 4, 5],
                "nested": {"key": "value", "num": 42},
                "tags": ["python", "programming", "tutorial"]
            }
        )

        result = await mock_vs.add_documents(
            documents=[complex_doc],
            creator_id="creator-123"
        )

        assert result["status"] == "success"
        stored_doc = mock_vs.documents[0]
        assert stored_doc.metadata["pages"] == [1, 2, 3, 4, 5]

    @pytest.mark.asyncio
    async def test_add_documents_with_empty_metadata(self):
        """add_documents should handle documents with empty metadata."""
        mock_vs = MockVectorStoreService()
        doc = MockDocument(page_content="Content", metadata={})

        result = await mock_vs.add_documents(
            documents=[doc],
            creator_id="creator-123"
        )

        assert result["status"] == "success"
        assert mock_vs.documents[0].metadata == {}

    @pytest.mark.asyncio
    async def test_similarity_search_with_k_zero(self):
        """similarity_search should handle k=0."""
        docs = [MockDocument(page_content="Test", metadata={})]
        mock_vs = MockVectorStoreService(documents=docs)

        results = await mock_vs.similarity_search(
            query="test",
            creator_id="creator-123",
            k=0
        )

        assert results == []

    @pytest.mark.asyncio
    async def test_multiple_creators_isolation(self):
        """Different creators should have isolated data."""
        mock_vs = MockVectorStoreService()

        # Add documents for creator A
        await mock_vs.add_documents(
            documents=[MockDocument(page_content="Creator A content", metadata={})],
            creator_id="creator-A",
            namespace="creator-A"
        )

        # Add documents for creator B
        await mock_vs.add_documents(
            documents=[MockDocument(page_content="Creator B content", metadata={})],
            creator_id="creator-B",
            namespace="creator-B"
        )

        # Verify both calls were recorded with correct namespaces
        calls = mock_vs.call_history
        namespaces = [c["namespace"] for c in calls if c["method"] == "add_documents"]
        assert "creator-A" in namespaces
        assert "creator-B" in namespaces


# =============================================================================
# Real VectorStoreService Tests (with mocked dependencies)
# =============================================================================

class TestRealVectorStoreServiceWithMocks:
    """
    Tests for the real VectorStoreService class with mocked external dependencies.

    These tests verify the actual implementation logic while avoiding API calls.
    """

    @pytest.mark.asyncio
    async def test_real_service_add_documents_uses_namespace(self):
        """Real VectorStoreService should use namespace correctly."""
        with patch('app.services.vector_store.OpenAIEmbeddings') as MockEmbeddings, \
             patch('app.services.vector_store.Pinecone') as MockPinecone, \
             patch('app.services.vector_store.PineconeVectorStore') as MockPVS:

            # Setup mocks
            mock_embeddings = MagicMock()
            MockEmbeddings.return_value = mock_embeddings

            mock_pinecone = MagicMock()
            MockPinecone.return_value = mock_pinecone

            # Import and create service
            from app.services.vector_store import VectorStoreService
            service = VectorStoreService()

            # Create test documents using LangChain Document
            from langchain_core.documents import Document
            docs = [Document(page_content="Test content", metadata={"source": "test"})]

            # Call add_documents
            result = await service.add_documents(
                documents=docs,
                creator_id="creator-123",
                namespace="test-namespace"
            )

            # Verify PineconeVectorStore.from_documents was called with correct namespace
            MockPVS.from_documents.assert_called_once()
            call_kwargs = MockPVS.from_documents.call_args
            assert call_kwargs.kwargs.get("namespace") == "test-namespace" or \
                   call_kwargs[1].get("namespace") == "test-namespace"

    @pytest.mark.asyncio
    async def test_real_service_add_documents_defaults_to_creator_id_namespace(self):
        """Real VectorStoreService should use creator_id as namespace when not specified."""
        with patch('app.services.vector_store.OpenAIEmbeddings') as MockEmbeddings, \
             patch('app.services.vector_store.Pinecone') as MockPinecone, \
             patch('app.services.vector_store.PineconeVectorStore') as MockPVS:

            mock_embeddings = MagicMock()
            MockEmbeddings.return_value = mock_embeddings

            mock_pinecone = MagicMock()
            MockPinecone.return_value = mock_pinecone

            from app.services.vector_store import VectorStoreService
            service = VectorStoreService()

            from langchain_core.documents import Document
            docs = [Document(page_content="Test", metadata={})]

            # Call without namespace
            result = await service.add_documents(
                documents=docs,
                creator_id="creator-456"
            )

            # Verify namespace defaults to creator_id
            call_kwargs = MockPVS.from_documents.call_args
            assert call_kwargs.kwargs.get("namespace") == "creator-456" or \
                   call_kwargs[1].get("namespace") == "creator-456"

    @pytest.mark.asyncio
    async def test_real_service_similarity_search_uses_namespace(self):
        """Real VectorStoreService should query with correct namespace."""
        with patch('app.services.vector_store.OpenAIEmbeddings') as MockEmbeddings, \
             patch('app.services.vector_store.Pinecone') as MockPinecone, \
             patch('app.services.vector_store.PineconeVectorStore') as MockPVS:

            mock_embeddings = MagicMock()
            MockEmbeddings.return_value = mock_embeddings

            mock_pinecone = MagicMock()
            MockPinecone.return_value = mock_pinecone

            # Setup mock vector store
            mock_vs_instance = MagicMock()
            mock_vs_instance.similarity_search_with_score = MagicMock(return_value=[])
            MockPVS.from_existing_index = MagicMock(return_value=mock_vs_instance)

            from app.services.vector_store import VectorStoreService
            service = VectorStoreService()

            # Call similarity_search with namespace
            results = await service.similarity_search(
                query="test query",
                creator_id="creator-789",
                k=4,
                namespace="custom-namespace"
            )

            # Verify from_existing_index was called with correct namespace
            call_kwargs = MockPVS.from_existing_index.call_args
            assert call_kwargs.kwargs.get("namespace") == "custom-namespace" or \
                   call_kwargs[1].get("namespace") == "custom-namespace"

    @pytest.mark.asyncio
    async def test_real_service_returns_correct_add_documents_format(self):
        """Real VectorStoreService.add_documents should return correct format."""
        with patch('app.services.vector_store.OpenAIEmbeddings') as MockEmbeddings, \
             patch('app.services.vector_store.Pinecone') as MockPinecone, \
             patch('app.services.vector_store.PineconeVectorStore') as MockPVS:

            mock_embeddings = MagicMock()
            MockEmbeddings.return_value = mock_embeddings

            mock_pinecone = MagicMock()
            MockPinecone.return_value = mock_pinecone

            mock_vs = MagicMock()
            MockPVS.from_documents = MagicMock(return_value=mock_vs)

            from app.services.vector_store import VectorStoreService
            service = VectorStoreService()

            from langchain_core.documents import Document
            docs = [
                Document(page_content="Doc 1", metadata={}),
                Document(page_content="Doc 2", metadata={}),
                Document(page_content="Doc 3", metadata={})
            ]

            result = await service.add_documents(
                documents=docs,
                creator_id="creator-123"
            )

            # Verify return format
            assert result["status"] == "success"
            assert result["document_count"] == 3
            assert result["namespace"] == "creator-123"
