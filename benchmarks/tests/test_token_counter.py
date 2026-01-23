"""Tests for token counter utility (US-011)."""

from pathlib import Path

import pytest


BENCHMARKS_DIR = Path(__file__).parent.parent


class TestTokenCounter:
    """Test that the token counter utility works correctly."""

    def test_module_exists(self) -> None:
        """Test that token_counter.py exists."""
        module_path = BENCHMARKS_DIR / "metrics" / "token_counter.py"
        assert module_path.exists(), "benchmarks/metrics/token_counter.py does not exist"

    def test_token_counter_is_importable(self) -> None:
        """Test that TokenCounter can be imported."""
        from benchmarks.metrics.token_counter import TokenCounter

        assert TokenCounter is not None

    def test_count_tokens_returns_integer(self) -> None:
        """Test that count_tokens returns an integer."""
        from benchmarks.metrics.token_counter import TokenCounter

        counter = TokenCounter()
        result = counter.count_tokens("Hello, world!")

        assert isinstance(result, int)

    def test_count_tokens_uses_cl100k_base(self) -> None:
        """Test that TokenCounter uses tiktoken cl100k_base encoding."""
        from benchmarks.metrics.token_counter import TokenCounter

        counter = TokenCounter()

        # Verify the encoding name
        assert counter.encoding_name == "cl100k_base"

    def test_count_tokens_empty_string(self) -> None:
        """Test that count_tokens handles empty string."""
        from benchmarks.metrics.token_counter import TokenCounter

        counter = TokenCounter()
        result = counter.count_tokens("")

        assert result == 0

    def test_count_tokens_simple_text(self) -> None:
        """Test count_tokens with simple text matches expected value."""
        from benchmarks.metrics.token_counter import TokenCounter

        counter = TokenCounter()

        # "Hello, world!" should be a small number of tokens
        result = counter.count_tokens("Hello, world!")

        assert result > 0
        assert result < 10  # Should be just a few tokens

    def test_count_tokens_longer_text(self) -> None:
        """Test count_tokens with longer text."""
        from benchmarks.metrics.token_counter import TokenCounter

        counter = TokenCounter()

        # A paragraph of text
        text = (
            "The quick brown fox jumps over the lazy dog. "
            "This is a common pangram used to test fonts and keyboards. "
            "It contains every letter of the English alphabet."
        )

        result = counter.count_tokens(text)

        # Should be more tokens than simple text
        assert result > 10
        assert result < 100

    def test_count_tokens_unicode(self) -> None:
        """Test count_tokens handles unicode characters."""
        from benchmarks.metrics.token_counter import TokenCounter

        counter = TokenCounter()

        # Text with unicode characters
        result = counter.count_tokens("Hello, \u4e16\u754c!")  # Hello, world in Chinese

        assert isinstance(result, int)
        assert result > 0

    def test_count_tokens_multiline(self) -> None:
        """Test count_tokens handles multiline text."""
        from benchmarks.metrics.token_counter import TokenCounter

        counter = TokenCounter()

        text = """Line 1
        Line 2
        Line 3"""

        result = counter.count_tokens(text)

        assert isinstance(result, int)
        assert result > 0

    def test_count_tokens_is_deterministic(self) -> None:
        """Test that count_tokens returns the same value for the same input."""
        from benchmarks.metrics.token_counter import TokenCounter

        counter = TokenCounter()
        text = "Test text for determinism check."

        result1 = counter.count_tokens(text)
        result2 = counter.count_tokens(text)

        assert result1 == result2
