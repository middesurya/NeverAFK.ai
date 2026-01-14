"""
Mock implementation for Pinecone vector store service.
PRD-002: Mock External Services
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


class MockDocument:
    """Mock document matching LangChain Document structure."""

    def __init__(self, page_content: str, metadata: Optional[Dict[str, Any]] = None):
        self.page_content = page_content
        self.metadata = metadata or {}


class MockVectorStoreService:
    """Mock implementation of VectorStoreService for testing without API calls."""

    def __init__(
        self,
        documents: Optional[List[MockDocument]] = None,
        documents_with_scores: Optional[List[Tuple[MockDocument, float]]] = None,
        raise_exception: Optional[Exception] = None
    ):
        self.documents = documents or []
        self._documents_with_scores = documents_with_scores
        self._raise_exception = raise_exception
        self.call_history: List[Dict[str, Any]] = []

    @property
    def call_count(self) -> int:
        return len(self.call_history)

    async def similarity_search(
        self,
        query: str,
        creator_id: str,
        k: int = 4,
        namespace: Optional[str] = None
    ) -> List[Tuple[MockDocument, float]]:
        """Search for similar documents, returning (doc, score) tuples."""
        if self._raise_exception:
            raise self._raise_exception

        # Record the call
        self.call_history.append({
            "method": "similarity_search",
            "query": query,
            "creator_id": creator_id,
            "k": k,
            "namespace": namespace,
            "timestamp": datetime.now()
        })

        # Handle k=0 or empty documents
        if k == 0:
            return []

        # Return preset documents with scores if provided
        if self._documents_with_scores:
            return self._documents_with_scores[:k]

        # Return documents with default scores
        if not self.documents:
            return []

        results = []
        for doc in self.documents[:k]:
            # Default similarity score for mock results
            score = 0.85
            results.append((doc, score))

        return results

    async def add_documents(
        self,
        documents: List[MockDocument],
        creator_id: str,
        namespace: Optional[str] = None
    ) -> Dict[str, Any]:
        """Add documents to the vector store."""
        if self._raise_exception:
            raise self._raise_exception

        # Record the call
        self.call_history.append({
            "method": "add_documents",
            "document_count": len(documents),
            "creator_id": creator_id,
            "namespace": namespace,
            "timestamp": datetime.now()
        })

        # Add documents to internal storage
        self.documents.extend(documents)

        return {
            "status": "success",
            "document_count": len(documents)
        }

    def reset_history(self) -> None:
        """Reset call history."""
        self.call_history = []
