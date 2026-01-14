"""
Pytest configuration and shared fixtures for backend tests.
"""

import sys
import pytest
from unittest.mock import MagicMock

# Create comprehensive mocks for heavy dependencies before importing main
mock_langchain_community = MagicMock()
mock_langchain_community.document_loaders = MagicMock()
mock_langchain_community.document_loaders.PyPDFLoader = MagicMock()
mock_langchain_community.document_loaders.TextLoader = MagicMock()

mock_langchain = MagicMock()
mock_langchain.text_splitter = MagicMock()
mock_langchain.text_splitter.RecursiveCharacterTextSplitter = MagicMock()

mock_langchain_openai = MagicMock()
mock_langchain_openai.OpenAIEmbeddings = MagicMock()
mock_langchain_openai.ChatOpenAI = MagicMock()

mock_langchain_anthropic = MagicMock()
mock_langchain_anthropic.ChatAnthropic = MagicMock()

mock_langchain_pinecone = MagicMock()
mock_langchain_pinecone.PineconeVectorStore = MagicMock()

mock_pinecone = MagicMock()
mock_langgraph = MagicMock()
mock_supabase = MagicMock()

# Register all mocks
sys.modules['langchain_community'] = mock_langchain_community
sys.modules['langchain_community.document_loaders'] = mock_langchain_community.document_loaders
sys.modules['langchain'] = mock_langchain
sys.modules['langchain.text_splitter'] = mock_langchain.text_splitter
sys.modules['langchain_openai'] = mock_langchain_openai
sys.modules['langchain_anthropic'] = mock_langchain_anthropic
sys.modules['langchain_pinecone'] = mock_langchain_pinecone
sys.modules['pinecone'] = mock_pinecone
sys.modules['langgraph'] = mock_langgraph
sys.modules['langgraph.graph'] = MagicMock()
sys.modules['supabase'] = mock_supabase

from fastapi.testclient import TestClient
from main import app as fastapi_app


@pytest.fixture
def app():
    """Return the FastAPI application instance."""
    return fastapi_app


@pytest.fixture
def client(app):
    """Return a TestClient connected to the app."""
    return TestClient(app)
