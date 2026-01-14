"""
Conversation Memory Service

Implements sliding window memory management with token counting and summarization.
Part of PRD-008: Conversation Memory implementation.

Features:
- Multi-turn conversation context (AC-1)
- Sliding window when exceeding token limit (AC-2)
- Summarization of old messages (AC-3)
- Accurate token counting with tiktoken (AC-4)
"""

from typing import Optional
from app.utils.token_counter import TokenCounter


class ConversationMemory:
    """
    Manages conversation memory with sliding window and summarization.

    Keeps track of conversation messages while ensuring the total token count
    stays within a specified limit. When the limit is approached, older messages
    are summarized before being dropped to preserve context.
    """

    def __init__(self, max_tokens: int = 4000, summarize_threshold: float = 0.8):
        """
        Initialize the conversation memory.

        Args:
            max_tokens: Maximum number of tokens to keep in context.
                       Defaults to 4000.
            summarize_threshold: Threshold (0.0-1.0) at which to trigger
                                summarization. Defaults to 0.8 (80% of max).
        """
        self.messages: list[dict] = []
        self.max_tokens = max_tokens
        self.summarize_threshold = summarize_threshold
        self.token_counter = TokenCounter()
        self.summary: Optional[str] = None

    def add_message(self, role: str, content: str) -> None:
        """
        Add a message to the conversation memory.

        Automatically manages the sliding window and triggers summarization
        when the token limit is approached.

        Args:
            role: The role of the message sender (e.g., "user", "assistant").
            content: The content of the message.
        """
        self.messages.append({"role": role, "content": content})
        self._manage_window()

    def get_context(self) -> list[dict]:
        """
        Get the current conversation context.

        Returns a list of messages including any summary of earlier
        conversation if present.

        Returns:
            List of message dicts with 'role' and 'content' keys.
        """
        context = []
        if self.summary:
            context.append({
                "role": "system",
                "content": f"Summary of earlier conversation: {self.summary}"
            })
        context.extend(self.messages)
        return context

    def get_token_count(self) -> int:
        """
        Get the current total token count of the context.

        Returns:
            Total number of tokens in the current context.
        """
        return self.token_counter.count_messages(self.get_context())

    def _manage_window(self) -> None:
        """
        Manage the sliding window to keep token count within limits.

        Triggers summarization when approaching the threshold, and
        drops oldest messages when exceeding the max tokens.
        """
        while self.get_token_count() > self.max_tokens and len(self.messages) > 2:
            current_tokens = self.get_token_count()
            threshold_tokens = self.max_tokens * self.summarize_threshold

            if current_tokens > threshold_tokens and len(self.messages) > 4:
                self._summarize_oldest()
            else:
                # Drop the oldest message
                self.messages.pop(0)

    def _summarize_oldest(self) -> None:
        """
        Summarize the oldest messages to preserve context while reducing tokens.

        Takes the oldest 2 messages and creates a summary, then removes
        those messages from the active list.
        """
        if len(self.messages) > 4:
            # Take oldest 2 messages to summarize
            to_summarize = self.messages[:2]

            # Create a simple summary of the old messages
            user_content = to_summarize[0].get("content", "")[:50]
            summary_text = f"User asked about {user_content}..."

            # Append to existing summary or create new one
            if self.summary:
                self.summary = f"{self.summary} {summary_text}"
            else:
                self.summary = summary_text

            # Remove summarized messages
            self.messages = self.messages[2:]

    def clear(self) -> None:
        """
        Clear all messages and summary from memory.

        Resets the conversation memory to its initial empty state.
        """
        self.messages = []
        self.summary = None
