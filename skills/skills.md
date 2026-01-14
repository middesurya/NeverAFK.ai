# Skills & Learned Patterns

This file contains reusable patterns learned during TDD development. Auto-updated by the @skill-updater agent.

**Last Updated:** 2026-01-12

---

## Project-Specific Patterns

### RAG Pipeline Pattern

**When to use:** Building content-aware AI responses

**Source:** Initial architecture

**Pattern:**
```
User Question → LangGraph Supervisor
├── Course Content Agent (semantic search)
├── Policy Agent (billing, access rules)
├── Progress Tracker (student context)
└── Escalation Agent (human handoff)
```

**Anti-pattern:** Don't use single monolithic prompts for multi-domain questions.

---

### Pinecone Namespace Isolation

**When to use:** Multi-tenant vector storage

**Source:** Initial architecture

**Pattern:**
- Each creator gets their own namespace
- Query format: `namespace=creator_id`
- Never mix namespaces in single query

**Example:**
```python
results = await vector_store.similarity_search(
    query=user_question,
    creator_id=creator_id,  # Used as namespace
    k=4
)
```

---

### Supabase Auth + JWT Validation

**When to use:** Protected API endpoints

**Source:** Initial architecture

**Pattern:**
```python
from app.utils.auth import get_current_user, get_optional_user

# Required auth
@app.get("/protected")
async def protected_route(user = Depends(get_current_user)):
    return {"user_id": user.user_id}

# Optional auth
@app.get("/public")
async def public_route(user = Depends(get_optional_user)):
    if user:
        # Authenticated
    else:
        # Anonymous
```

---

## Testing Patterns

### API Test Pattern (Python)

**When to use:** Testing FastAPI endpoints

**Pattern:**
```python
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_given_condition_when_action_then_result():
    # Arrange
    payload = {"key": "value"}

    # Act
    response = client.post("/endpoint", json=payload)

    # Assert
    assert response.status_code == 200
    assert "expected_key" in response.json()
```

---

### React Component Test Pattern

**When to use:** Testing Next.js components

**Pattern:**
```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import Component from './Component';

describe('Component', () => {
  it('given props when rendered then shows expected', () => {
    render(<Component prop="value" />);
    expect(screen.getByText('expected')).toBeInTheDocument();
  });
});
```

---

## Gotchas & Solutions

### CORS Issues with Embed Widget

**Problem:** Embed widget blocked by CORS

**Solution:** Enable CORS for all origins in FastAPI:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Useful Commands

### Development
```bash
# Frontend
cd frontend && npm run dev

# Backend
cd backend && uvicorn main:app --reload --port 8000

# Tests
cd backend && python test_api.py
cd frontend && npm test
```

### Deployment
```bash
# Frontend (Vercel)
vercel --prod

# Backend (Railway)
railway up
```

---

## Patterns Learned Today

*Updated automatically by @skill-updater*

---

### PRD-001: Pytest Fixture with Dependency Mocking

**When to use:** Setting up pytest for FastAPI apps with heavy dependencies

**Source:** PRD-001 (2026-01-12)

**Pattern:**
```python
# conftest.py - Mock heavy dependencies at module level
import sys
from unittest.mock import MagicMock

# Mock before importing app
sys.modules['langchain'] = MagicMock()
sys.modules['pinecone'] = MagicMock()
sys.modules['supabase'] = MagicMock()

import pytest
from fastapi.testclient import TestClient
from main import app as fastapi_app

@pytest.fixture
def app():
    return fastapi_app

@pytest.fixture
def client(app):
    return TestClient(app)
```

**pytest.ini config:**
```ini
[pytest]
asyncio_mode = auto
testpaths = tests
```

**Anti-pattern:** Don't import the app directly without mocking external services - it will fail on missing API keys.

---

### PRD-002: Service Mock Pattern with Call History

**When to use:** Mocking external services (OpenAI, Pinecone, Supabase) for isolated testing

**Source:** PRD-002 (2026-01-12)

**Pattern:**
```python
# tests/mocks/openai_mock.py
from datetime import datetime

class MockOpenAIResponse:
    def __init__(self, content: str):
        self.content = content

class MockChatOpenAI:
    def __init__(self, default_response="Mock response", responses=None):
        self.default_response = default_response
        self.responses = responses or []
        self.call_history = []
        self._response_index = 0

    async def ainvoke(self, messages):
        self.call_history.append({
            "messages": messages,
            "timestamp": datetime.now().isoformat()
        })
        if self.responses and self._response_index < len(self.responses):
            response = self.responses[self._response_index]
            self._response_index += 1
            return MockOpenAIResponse(response)
        return MockOpenAIResponse(self.default_response)

    @property
    def call_count(self):
        return len(self.call_history)

    def reset_history(self):
        self.call_history = []
        self._response_index = 0
```

**Usage in tests:**
```python
@pytest.fixture
def mock_openai():
    return MockChatOpenAI(default_response="Test response")

async def test_ai_generates_response(mock_openai):
    response = await mock_openai.ainvoke([{"role": "user", "content": "Hi"}])
    assert response.content == "Test response"
    assert mock_openai.call_count == 1
```

**Anti-pattern:** Don't create mocks that always succeed - include `raise_exception` flag for error testing.

---

### PRD-003: LangGraph Node Unit Testing

**When to use:** Testing individual LangGraph agent nodes in isolation

**Source:** PRD-003 (2026-01-12)

**Pattern:**
```python
# Test each LangGraph node independently
import pytest
from tests.mocks.openai_mock import MockChatOpenAI
from tests.mocks.pinecone_mock import MockVectorStoreService, MockDocument

class TestRetrievalNode:
    @pytest.fixture
    def mock_vector_store(self):
        return MockVectorStoreService(documents=[
            MockDocument("Content 1", {"source": "doc1.pdf"}),
            MockDocument("Content 2", {"source": "doc2.pdf"})
        ])

    @pytest.fixture
    def agent(self, mock_vector_store):
        # Inject mock instead of real service
        from app.agents.support_agent import SupportAgent
        agent = SupportAgent.__new__(SupportAgent)
        agent.vector_store = mock_vector_store
        return agent

    async def test_retrieval_returns_documents(self, agent):
        state = {"query": "test", "creator_id": "test-creator", "context": [], "sources": []}
        result = await agent.retrieve_context(state)
        assert len(result["context"]) > 0
        assert agent.vector_store.call_count == 1
```

**Anti-pattern:** Don't test LangGraph internal graph compilation - focus on node business logic.

---

### PRD-004: FastAPI Integration Test Pattern

**When to use:** Testing API endpoints with full request/response cycle

**Source:** PRD-004 (2026-01-12)

**Pattern:**
```python
import pytest
from io import BytesIO

class TestChatEndpoint:
    def test_chat_success(self, client):
        response = client.post("/chat", json={
            "message": "What is the course about?",
            "creator_id": "test-creator"
        })
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "sources" in data
        assert "should_escalate" in data

    def test_chat_validation_error(self, client):
        response = client.post("/chat", json={})
        assert response.status_code == 422

class TestUploadEndpoint:
    def test_upload_file(self, client):
        file_content = BytesIO(b"Test content")
        response = client.post("/upload/content",
            files={"file": ("test.txt", file_content, "text/plain")},
            data={"creator_id": "test", "content_type": "text"}
        )
        assert response.status_code == 200
```

**Anti-pattern:** Don't test with real API keys - always use mocked services.

---

### PRD-005: Pytest Coverage Configuration

**When to use:** Setting up test coverage for pytest projects

**Source:** PRD-005 (2026-01-12)

**Pattern:**
```ini
# .coveragerc
[run]
source = app
omit =
    */tests/*
    */__pycache__/*

[report]
exclude_lines =
    pragma: no cover
    if __name__ == .__main__.:
fail_under = 80
```

```ini
# pytest.ini
[pytest]
asyncio_mode = auto
addopts = --cov=app --cov-report=term-missing --cov-fail-under=80
```

**Usage:** `pytest --cov=app --cov-report=xml tests/`

**Anti-pattern:** Don't exclude critical code from coverage just to hit the target.

---

### PRD-006: SSE Streaming Response Pattern

**When to use:** Real-time token-by-token AI response streaming

**Source:** PRD-006 (2026-01-12)

**Pattern:**
```python
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import json

async def stream_generator(message, creator_id):
    # Get full response
    result = await support_agent.process_query(message, creator_id)

    # Stream word by word
    words = result["response"].split(" ")
    for i, word in enumerate(words):
        token = word if i == 0 else " " + word
        yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

    # Final event with metadata
    yield f"data: {json.dumps({'type': 'done', 'sources': result['sources'], 'should_escalate': result['should_escalate']})}\n\n"

@router.post("/chat/stream")
async def chat_stream(message: ChatMessage):
    return StreamingResponse(
        stream_generator(message.message, message.creator_id),
        media_type="text/event-stream; charset=utf-8"
    )
```

**Anti-pattern:** Don't buffer entire response - stream as tokens arrive.

---

### PRD-008: Conversation Memory Pattern

**When to use:** Multi-turn chat requiring context management with token limits

**Source:** PRD-008 (2026-01-13)

**Pattern:**
```python
from app.utils.token_counter import TokenCounter

class ConversationMemory:
    def __init__(self, max_tokens: int = 4000, summarize_threshold: float = 0.8):
        self.messages = []
        self.max_tokens = max_tokens
        self.summarize_threshold = summarize_threshold
        self.token_counter = TokenCounter()
        self.summary = None

    def add_message(self, role: str, content: str) -> None:
        self.messages.append({"role": role, "content": content})
        self._manage_window()  # Sliding window + summarization

    def get_context(self) -> list[dict]:
        context = []
        if self.summary:
            context.append({"role": "system", "content": f"Summary: {self.summary}"})
        context.extend(self.messages)
        return context
```

**Anti-pattern:** Don't drop messages without summarizing - important early context is lost.

---

### PRD-009: Prompt Injection Detection Pattern

**When to use:** LLM security - detecting and blocking malicious user inputs

**Source:** PRD-009 (2026-01-13)

**Pattern:**
```python
from dataclasses import dataclass
from enum import Enum
import re

class ThreatLevel(Enum):
    NONE = "none"
    MEDIUM = "medium"
    HIGH = "high"

@dataclass
class InjectionCheckResult:
    is_injection: bool
    threat_level: ThreatLevel
    matched_pattern: str = ""

class PromptGuard:
    PATTERNS = [
        r"ignore\s+(all\s+)?(previous|prior)\s+instructions?",
        r"you\s+are\s+now\s+",
        r"DAN\s+mode",
    ]

    def check_input(self, text: str) -> InjectionCheckResult:
        for pattern in self.compiled_patterns:
            if match := pattern.search(text):
                return InjectionCheckResult(is_injection=True, ...)
        return InjectionCheckResult(is_injection=False, threat_level=ThreatLevel.NONE)
```

**Anti-pattern:** Don't expose detection logic in error messages - attackers can probe.

---

### PRD-010: Response Evaluation Pattern

**When to use:** Confidence scoring and hallucination detection for AI responses

**Source:** PRD-010 (2026-01-13)

**Pattern:**
```python
@dataclass
class EvaluationResult:
    confidence_score: float  # 0.0 - 1.0
    confidence_level: ConfidenceLevel  # HIGH/MEDIUM/LOW
    hallucination_flags: list[str]
    needs_review: bool

class ResponseEvaluator:
    def evaluate(self, response: str, sources: list[dict]) -> EvaluationResult:
        # 60% source relevance + 40% content coverage
        confidence = (avg_source_score * 0.6) + (coverage * 0.4)

        # Detect ungrounded claims (numbers, dates, definitive statements)
        hallucinations = self._detect_hallucinations(response, sources)

        # Flag for review if low confidence or hallucinations
        needs_review = confidence < 0.5 or len(hallucinations) > 0
```

**Anti-pattern:** Don't block low-confidence responses - flag them for review instead.

---

*Add new patterns below this line*
