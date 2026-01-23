"""Token counter utility (US-011).

This module provides accurate token counting using tiktoken
with the cl100k_base encoding (used by Claude and GPT-4).
"""

import tiktoken


class TokenCounter:
    """Token counter using tiktoken cl100k_base encoding.

    This class provides accurate token counting for text content,
    using the same tokenizer that Claude and GPT-4 use.
    """

    def __init__(self) -> None:
        """Initialize the token counter with cl100k_base encoding."""
        self._encoding = tiktoken.get_encoding("cl100k_base")

    @property
    def encoding_name(self) -> str:
        """Get the name of the encoding being used."""
        return "cl100k_base"

    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in a text string.

        Args:
            text: The text to count tokens for.

        Returns:
            The number of tokens in the text.
        """
        if not text:
            return 0

        tokens = self._encoding.encode(text)
        return len(tokens)
