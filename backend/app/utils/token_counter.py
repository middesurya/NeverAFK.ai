"""
Token Counter Utility for Conversation Memory

Uses tiktoken for accurate GPT token counting.
Part of PRD-008: Conversation Memory implementation.
"""

import tiktoken


class TokenCounter:
    """
    Token counter using tiktoken for accurate GPT token counting.

    Provides methods to count tokens in text strings and message lists,
    accounting for the overhead of message formatting in chat completions.
    """

    def __init__(self, model: str = "gpt-4"):
        """
        Initialize the token counter with a specific model encoding.

        Args:
            model: The model name to get encoding for. Defaults to "gpt-4".
        """
        try:
            self.encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            # Fall back to cl100k_base encoding if model not found
            self.encoding = tiktoken.get_encoding("cl100k_base")

    def count(self, text: str) -> int:
        """
        Count the number of tokens in a text string.

        Args:
            text: The text to count tokens for.

        Returns:
            The number of tokens in the text.
        """
        if not text:
            return 0
        return len(self.encoding.encode(text))

    def count_messages(self, messages: list[dict]) -> int:
        """
        Count tokens in a list of chat messages.

        Includes overhead for role formatting in chat completions.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.

        Returns:
            Total token count including role overhead.
        """
        total = 0
        for msg in messages:
            # Count content tokens
            content = msg.get("content", "")
            total += self.count(content)
            # Add overhead for role and message structure
            # This accounts for: <|start|>role<|sep|>content<|end|>
            total += 4
        return total
