"""Tests for summarization task (US-018)."""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


BENCHMARKS_DIR = Path(__file__).parent.parent


class TestSummarizeTask:
    """Test the summarization task (US-018)."""

    def test_module_exists(self) -> None:
        """Test that summarize.py exists in tasks directory."""
        module_path = BENCHMARKS_DIR / "tasks" / "summarize.py"
        assert module_path.exists(), "benchmarks/tasks/summarize.py does not exist"

    def test_summarize_task_is_importable(self) -> None:
        """Test that SummarizeTask can be imported."""
        from benchmarks.tasks.summarize import SummarizeTask

        assert SummarizeTask is not None

    def test_summarize_task_inherits_from_base(self) -> None:
        """Test that SummarizeTask inherits from BaseTask."""
        from benchmarks.tasks.base import BaseTask
        from benchmarks.tasks.summarize import SummarizeTask

        assert issubclass(SummarizeTask, BaseTask)

    def test_summarize_task_can_be_instantiated(self) -> None:
        """Test that SummarizeTask can be instantiated."""
        from benchmarks.tasks.summarize import SummarizeTask

        task = SummarizeTask()
        assert task is not None

    def test_summarize_task_reads_api_key_from_env(self) -> None:
        """Test that SummarizeTask reads ANTHROPIC_API_KEY from environment."""
        from benchmarks.tasks.summarize import SummarizeTask

        # Task should not raise if API key is set
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            task = SummarizeTask()
            assert task is not None

    def test_summarize_task_has_execute_method(self) -> None:
        """Test that SummarizeTask has execute method."""
        from benchmarks.tasks.summarize import SummarizeTask

        task = SummarizeTask()
        assert hasattr(task, "execute")
        assert callable(task.execute)

    def test_execute_returns_task_result(self) -> None:
        """Test that execute returns a TaskResult."""
        from benchmarks.tasks.base import TaskResult
        from benchmarks.tasks.summarize import SummarizeTask

        # Mock the Anthropic API response
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="- Point 1\n- Point 2\n- Point 3")]
        mock_response.usage.input_tokens = 100
        mock_response.usage.output_tokens = 50

        with patch("benchmarks.tasks.summarize.anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.Anthropic.return_value = mock_client

            task = SummarizeTask()
            result = task.execute("Test document content")

            assert isinstance(result, TaskResult)
            assert result.prompt_tokens == 100
            assert result.completion_tokens == 50
            assert "Point 1" in result.result_text

    def test_execute_uses_summarization_prompt(self) -> None:
        """Test that execute sends content with summarization prompt."""
        from benchmarks.tasks.summarize import SummarizeTask

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="- Summary")]
        mock_response.usage.input_tokens = 50
        mock_response.usage.output_tokens = 20

        with patch("benchmarks.tasks.summarize.anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.Anthropic.return_value = mock_client

            task = SummarizeTask()
            task.execute("Document content here")

            # Check that the API was called with summarization prompt
            call_args = mock_client.messages.create.call_args
            messages = call_args.kwargs.get("messages", call_args.args[0] if call_args.args else None)

            # Verify prompt mentions bullet points
            prompt_text = str(messages)
            assert "bullet" in prompt_text.lower() or "summarize" in prompt_text.lower()

    def test_execute_handles_api_error(self) -> None:
        """Test that execute handles API errors gracefully."""
        from benchmarks.tasks.base import TaskResult
        from benchmarks.tasks.summarize import SummarizeTask

        with patch("benchmarks.tasks.summarize.anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.side_effect = Exception("API Error")
            mock_anthropic.Anthropic.return_value = mock_client

            task = SummarizeTask()
            result = task.execute("Test content")

            assert isinstance(result, TaskResult)
            assert result.error is not None
            assert "API Error" in result.error

    def test_execute_includes_document_content_in_message(self) -> None:
        """Test that the document content is included in the API call."""
        from benchmarks.tasks.summarize import SummarizeTask

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="- Summary")]
        mock_response.usage.input_tokens = 50
        mock_response.usage.output_tokens = 20

        test_content = "This is my unique test document content 12345"

        with patch("benchmarks.tasks.summarize.anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.Anthropic.return_value = mock_client

            task = SummarizeTask()
            task.execute(test_content)

            # Check that content was passed to API
            call_args = mock_client.messages.create.call_args
            call_str = str(call_args)
            assert "12345" in call_str or test_content in call_str
