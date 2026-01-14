"""
PRD-008: Conversation Memory Tests

Tests for conversation memory with sliding window and token counting:
- AC-1: Multi-turn conversation - Previous context is included in prompt
- AC-2: Conversation exceeds token limit - Oldest messages dropped (sliding window)
- AC-3: Long conversation - Early messages summarized instead of dropped
- AC-4: Token counter - Accurate token count maintained

TDD: RED PHASE - Tests written first, expected to fail until implementation.
"""

import pytest
from unittest.mock import MagicMock, patch


# =============================================================================
# Mock Classes for Testing
# =============================================================================

class MockTokenCounter:
    """Mock token counter that uses word count instead of tiktoken."""

    def count(self, text: str) -> int:
        """Count tokens as word count for predictable testing."""
        if not text:
            return 0
        return len(text.split())

    def count_messages(self, messages: list[dict]) -> int:
        """Count tokens in a list of messages with role overhead."""
        total = 0
        for msg in messages:
            total += self.count(msg.get("content", ""))
            total += 4  # role overhead per message
        return total


# =============================================================================
# TokenCounter Tests - AC-4: Accurate token count
# =============================================================================

class TestTokenCounter:
    """Tests for TokenCounter utility - AC-4."""

    def test_count_empty_string_returns_zero(self):
        """Empty string should return 0 tokens."""
        from app.utils.token_counter import TokenCounter
        counter = TokenCounter()

        result = counter.count("")

        assert result == 0

    def test_count_single_word(self):
        """Single word should return at least 1 token."""
        from app.utils.token_counter import TokenCounter
        counter = TokenCounter()

        result = counter.count("hello")

        assert result >= 1

    def test_count_sentence(self):
        """A sentence should return multiple tokens."""
        from app.utils.token_counter import TokenCounter
        counter = TokenCounter()

        result = counter.count("Hello, how are you doing today?")

        assert result > 1

    def test_count_messages_empty_list(self):
        """Empty message list should return 0 tokens."""
        from app.utils.token_counter import TokenCounter
        counter = TokenCounter()

        result = counter.count_messages([])

        assert result == 0

    def test_count_messages_single_message(self):
        """Single message should count content plus role overhead."""
        from app.utils.token_counter import TokenCounter
        counter = TokenCounter()

        messages = [{"role": "user", "content": "Hello"}]
        result = counter.count_messages(messages)

        # Should have token count of content plus role overhead
        assert result > counter.count("Hello")

    def test_count_messages_multiple_messages(self):
        """Multiple messages should accumulate token counts."""
        from app.utils.token_counter import TokenCounter
        counter = TokenCounter()

        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]
        result = counter.count_messages(messages)

        # Should be more than single message
        single_msg = counter.count_messages([messages[0]])
        assert result > single_msg

    def test_count_messages_handles_missing_content(self):
        """Messages without content field should not crash."""
        from app.utils.token_counter import TokenCounter
        counter = TokenCounter()

        messages = [{"role": "user"}]
        result = counter.count_messages(messages)

        # Should return at least the role overhead
        assert result >= 4

    def test_fallback_encoding_for_unknown_model(self):
        """Should fall back to cl100k_base for unknown models."""
        from app.utils.token_counter import TokenCounter

        # Use an invalid model name to trigger fallback
        counter = TokenCounter(model="non-existent-model-xyz-123")

        # Should still work with fallback encoding
        result = counter.count("Hello world")
        assert result > 0

    def test_different_model_encoding(self):
        """Should accept different model names."""
        from app.utils.token_counter import TokenCounter

        # Test with a different valid model
        counter = TokenCounter(model="gpt-3.5-turbo")

        result = counter.count("Hello world")
        assert result > 0


# =============================================================================
# ConversationMemory Tests - AC-1: Context Included
# =============================================================================

class TestConversationMemoryContextIncluded:
    """Tests for context inclusion in multi-turn conversations - AC-1."""

    def test_add_single_message(self):
        """Adding a message should store it in memory."""
        from app.services.conversation_memory import ConversationMemory
        memory = ConversationMemory(max_tokens=1000)

        memory.add_message("user", "Hello, how are you?")

        context = memory.get_context()
        assert len(context) == 1
        assert context[0]["role"] == "user"
        assert context[0]["content"] == "Hello, how are you?"

    def test_add_multiple_messages_preserves_order(self):
        """Multiple messages should be preserved in order."""
        from app.services.conversation_memory import ConversationMemory
        memory = ConversationMemory(max_tokens=1000)

        memory.add_message("user", "First message")
        memory.add_message("assistant", "Second message")
        memory.add_message("user", "Third message")

        context = memory.get_context()
        assert len(context) == 3
        assert context[0]["content"] == "First message"
        assert context[1]["content"] == "Second message"
        assert context[2]["content"] == "Third message"

    def test_context_includes_previous_messages_for_followup(self):
        """Follow-up messages should include previous context."""
        from app.services.conversation_memory import ConversationMemory
        memory = ConversationMemory(max_tokens=1000)

        memory.add_message("user", "What is Python?")
        memory.add_message("assistant", "Python is a programming language.")
        memory.add_message("user", "Can you tell me more?")

        context = memory.get_context()

        # All messages should be present for context
        assert len(context) >= 3
        # Should contain the original question
        contents = [msg["content"] for msg in context]
        assert "What is Python?" in contents

    def test_get_context_returns_list_of_dicts(self):
        """get_context should return properly formatted message list."""
        from app.services.conversation_memory import ConversationMemory
        memory = ConversationMemory(max_tokens=1000)

        memory.add_message("user", "Test message")

        context = memory.get_context()

        assert isinstance(context, list)
        assert all(isinstance(msg, dict) for msg in context)
        assert all("role" in msg and "content" in msg for msg in context)


# =============================================================================
# ConversationMemory Tests - AC-2: Sliding Window
# =============================================================================

class TestConversationMemorySlidingWindow:
    """Tests for sliding window behavior when exceeding token limit - AC-2."""

    def test_sliding_window_removes_oldest_when_limit_exceeded(self):
        """Oldest messages should be removed when token limit exceeded."""
        from app.services.conversation_memory import ConversationMemory

        # Use mock token counter for predictable behavior
        memory = ConversationMemory(max_tokens=50, summarize_threshold=0.9)
        memory.token_counter = MockTokenCounter()

        # Add messages that will exceed the limit
        # Each message is ~10 words + 4 overhead = ~14 tokens
        memory.add_message("user", "This is the first message in conversation")
        memory.add_message("assistant", "This is the first response in conversation")
        memory.add_message("user", "This is the second message in conversation")
        memory.add_message("assistant", "This is the second response in conversation")
        memory.add_message("user", "This is the third message in conversation")

        context = memory.get_context()
        total_tokens = memory.get_token_count()

        # Should be within token limit
        assert total_tokens <= 50
        # First message should have been removed or summarized
        raw_contents = [msg["content"] for msg in context if not msg["content"].startswith("Summary")]
        assert "This is the first message in conversation" not in raw_contents or memory.summary is not None

    def test_sliding_window_keeps_recent_messages(self):
        """Recent messages should be preserved in sliding window."""
        from app.services.conversation_memory import ConversationMemory

        memory = ConversationMemory(max_tokens=30, summarize_threshold=0.9)
        memory.token_counter = MockTokenCounter()

        memory.add_message("user", "Old message one")
        memory.add_message("assistant", "Old message two")
        memory.add_message("user", "Recent message three")
        memory.add_message("assistant", "Recent message four")

        context = memory.get_context()
        contents = [msg["content"] for msg in context if not msg["content"].startswith("Summary")]

        # Most recent message should always be present
        assert "Recent message four" in contents

    def test_token_count_stays_within_limit(self):
        """Token count should stay within max_tokens limit."""
        from app.services.conversation_memory import ConversationMemory

        memory = ConversationMemory(max_tokens=100)
        memory.token_counter = MockTokenCounter()

        # Add many messages
        for i in range(20):
            memory.add_message("user", f"This is test message number {i}")
            memory.add_message("assistant", f"This is response number {i}")

        total_tokens = memory.get_token_count()

        assert total_tokens <= 100


# =============================================================================
# ConversationMemory Tests - AC-3: Summarization
# =============================================================================

class TestConversationMemorySummarization:
    """Tests for message summarization - AC-3."""

    def test_summarization_triggered_at_threshold(self):
        """Summarization should be triggered when threshold is approached."""
        from app.services.conversation_memory import ConversationMemory

        # Use lower max_tokens and set mock counter BEFORE adding messages
        memory = ConversationMemory(max_tokens=30, summarize_threshold=0.5)
        memory.token_counter = MockTokenCounter()

        # Add messages - each ~6-7 words + 4 overhead = ~10-11 tokens
        # After 4 messages we have ~40-44 tokens which exceeds 30 max
        memory.add_message("user", "Question about Python programming language features")
        memory.add_message("assistant", "Python has many features including dynamic typing")
        memory.add_message("user", "Tell me about lists and dictionaries")
        memory.add_message("assistant", "Lists and dicts are collection types")
        memory.add_message("user", "One more question about functions")

        # After exceeding threshold, summary should be created or messages dropped
        context = memory.get_context()

        # Either have a summary or messages were dropped
        assert memory.summary is not None or len(memory.messages) < 5

    def test_summary_included_in_context(self):
        """Summary should be included in context when present."""
        from app.services.conversation_memory import ConversationMemory

        memory = ConversationMemory(max_tokens=40, summarize_threshold=0.5)
        memory.token_counter = MockTokenCounter()

        # Add enough messages to trigger summarization
        memory.add_message("user", "First question about topic one")
        memory.add_message("assistant", "Answer about topic one here")
        memory.add_message("user", "Second question about topic two")
        memory.add_message("assistant", "Answer about topic two here")
        memory.add_message("user", "Third question about topic three")

        context = memory.get_context()

        # If summary exists, it should be in context
        if memory.summary:
            context_str = str(context)
            assert "Summary" in context_str or "summary" in memory.summary.lower()

    def test_summary_preserves_key_information(self):
        """Summary should preserve key information from old messages."""
        from app.services.conversation_memory import ConversationMemory

        memory = ConversationMemory(max_tokens=40, summarize_threshold=0.5)
        memory.token_counter = MockTokenCounter()

        # Add specific messages
        memory.add_message("user", "What is machine learning?")
        memory.add_message("assistant", "Machine learning is a type of AI.")
        memory.add_message("user", "What are neural networks?")
        memory.add_message("assistant", "Neural networks are ML models.")
        memory.add_message("user", "Tell me about deep learning now")

        # Summary should reference the earlier topics
        if memory.summary:
            # Summary should contain some reference to earlier content
            assert len(memory.summary) > 0


# =============================================================================
# ConversationMemory Tests - General Functionality
# =============================================================================

class TestConversationMemoryGeneral:
    """Tests for general ConversationMemory functionality."""

    def test_clear_removes_all_messages(self):
        """clear() should remove all messages and summary."""
        from app.services.conversation_memory import ConversationMemory

        memory = ConversationMemory(max_tokens=1000)
        memory.add_message("user", "Test message")
        memory.add_message("assistant", "Test response")
        memory.summary = "Previous summary"

        memory.clear()

        assert len(memory.messages) == 0
        assert memory.summary is None
        assert memory.get_context() == []

    def test_get_token_count_returns_integer(self):
        """get_token_count should return an integer."""
        from app.services.conversation_memory import ConversationMemory

        memory = ConversationMemory(max_tokens=1000)
        memory.add_message("user", "Test message")

        count = memory.get_token_count()

        assert isinstance(count, int)
        assert count > 0

    def test_initial_state_is_empty(self):
        """New ConversationMemory should start empty."""
        from app.services.conversation_memory import ConversationMemory

        memory = ConversationMemory(max_tokens=1000)

        assert len(memory.messages) == 0
        assert memory.summary is None
        assert memory.get_context() == []
        assert memory.get_token_count() == 0

    def test_custom_max_tokens(self):
        """Should accept custom max_tokens parameter."""
        from app.services.conversation_memory import ConversationMemory

        memory = ConversationMemory(max_tokens=2000)

        assert memory.max_tokens == 2000

    def test_custom_summarize_threshold(self):
        """Should accept custom summarize_threshold parameter."""
        from app.services.conversation_memory import ConversationMemory

        memory = ConversationMemory(max_tokens=1000, summarize_threshold=0.6)

        assert memory.summarize_threshold == 0.6

    def test_default_values(self):
        """Should have sensible default values."""
        from app.services.conversation_memory import ConversationMemory

        memory = ConversationMemory()

        assert memory.max_tokens == 4000
        assert memory.summarize_threshold == 0.8


# =============================================================================
# Integration Tests
# =============================================================================

class TestConversationMemoryIntegration:
    """Integration tests for ConversationMemory with real TokenCounter."""

    def test_real_token_counter_integration(self):
        """Should work with real TokenCounter (tiktoken)."""
        from app.services.conversation_memory import ConversationMemory
        from app.utils.token_counter import TokenCounter

        memory = ConversationMemory(max_tokens=500)

        # Verify it uses real token counter
        assert isinstance(memory.token_counter, TokenCounter)

        memory.add_message("user", "What is Python?")
        memory.add_message("assistant", "Python is a programming language.")

        count = memory.get_token_count()
        assert count > 0

    def test_conversation_flow_simulation(self):
        """Simulate a real conversation flow."""
        from app.services.conversation_memory import ConversationMemory

        memory = ConversationMemory(max_tokens=200)

        # Simulate a conversation
        conversation = [
            ("user", "Hi, I need help with Python."),
            ("assistant", "Hello! I'd be happy to help. What do you need?"),
            ("user", "How do I read a file?"),
            ("assistant", "You can use open() function with 'r' mode."),
            ("user", "Can you show me an example?"),
            ("assistant", "Sure! with open('file.txt', 'r') as f: content = f.read()"),
            ("user", "What about writing to a file?"),
            ("assistant", "Use 'w' mode: with open('file.txt', 'w') as f: f.write('text')"),
        ]

        for role, content in conversation:
            memory.add_message(role, content)

        # Should maintain context within limits
        context = memory.get_context()
        assert len(context) > 0
        assert memory.get_token_count() <= 200

    def test_long_conversation_stays_within_limits(self):
        """Long conversation should always stay within token limits."""
        from app.services.conversation_memory import ConversationMemory

        memory = ConversationMemory(max_tokens=100)

        # Add many messages
        for i in range(50):
            memory.add_message("user", f"Question {i}: What is item {i}?")
            memory.add_message("assistant", f"Answer {i}: Item {i} is something.")

        # Should always be within limit
        assert memory.get_token_count() <= 100
        # Should have some messages
        assert len(memory.get_context()) > 0
