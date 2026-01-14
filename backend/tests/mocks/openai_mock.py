"""
Mock implementation for OpenAI ChatGPT service.
PRD-002: Mock External Services
"""

from datetime import datetime
from typing import Any, Dict, List, Optional


class MockOpenAIResponse:
    """Mock response object matching OpenAI/LangChain response structure."""

    def __init__(self, content: str):
        self.content = content


class MockChatOpenAI:
    """Mock implementation of ChatOpenAI for testing without API calls."""

    def __init__(
        self,
        default_response: str = "This is a mock response.",
        responses: Optional[List[str]] = None,
        raise_exception: Optional[Exception] = None
    ):
        self.default_response = default_response
        self._responses = responses or []
        self._response_index = 0
        self._raise_exception = raise_exception
        self.call_history: List[Dict[str, Any]] = []

    @property
    def call_count(self) -> int:
        return len(self.call_history)

    async def ainvoke(self, messages: List[Any]) -> MockOpenAIResponse:
        """Async invoke matching LangChain ChatOpenAI interface."""
        if self._raise_exception:
            raise self._raise_exception

        # Record the call
        self.call_history.append({
            "messages": self._serialize_messages(messages),
            "timestamp": datetime.now()
        })

        # Get response content
        if self._responses and self._response_index < len(self._responses):
            content = self._responses[self._response_index]
            self._response_index += 1
        else:
            content = self.default_response

        return MockOpenAIResponse(content)

    def _serialize_messages(self, messages: List[Any]) -> List[Dict[str, Any]]:
        """Convert messages to serializable format."""
        result = []
        for msg in messages:
            if isinstance(msg, dict):
                result.append(msg)
            elif hasattr(msg, "content"):
                result.append({"content": msg.content})
            else:
                result.append({"content": str(msg)})
        return result

    def reset_history(self) -> None:
        """Reset call history and response index."""
        self.call_history = []
        self._response_index = 0
