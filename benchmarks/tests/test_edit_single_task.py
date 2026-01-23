"""Tests for single-edit task (US-019)."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


BENCHMARKS_DIR = Path(__file__).parent.parent


class TestSingleEditTask:
    """Test the single-edit task (US-019)."""

    def test_module_exists(self) -> None:
        """Test that edit_single.py exists in tasks directory."""
        module_path = BENCHMARKS_DIR / "tasks" / "edit_single.py"
        assert module_path.exists(), "benchmarks/tasks/edit_single.py does not exist"

    def test_single_edit_task_is_importable(self) -> None:
        """Test that SingleEditTask can be imported."""
        from benchmarks.tasks.edit_single import SingleEditTask

        assert SingleEditTask is not None

    def test_single_edit_task_inherits_from_base(self) -> None:
        """Test that SingleEditTask inherits from BaseTask."""
        from benchmarks.tasks.base import BaseTask
        from benchmarks.tasks.edit_single import SingleEditTask

        assert issubclass(SingleEditTask, BaseTask)

    def test_single_edit_task_takes_instruction_parameter(self) -> None:
        """Test that SingleEditTask takes edit_instruction in constructor."""
        from benchmarks.tasks.edit_single import SingleEditTask

        task = SingleEditTask(edit_instruction="Make the text more concise")
        assert task.edit_instruction == "Make the text more concise"

    def test_single_edit_task_has_execute_method(self) -> None:
        """Test that SingleEditTask has execute method."""
        from benchmarks.tasks.edit_single import SingleEditTask

        task = SingleEditTask(edit_instruction="Fix grammar")
        assert hasattr(task, "execute")
        assert callable(task.execute)

    def test_execute_returns_task_result(self) -> None:
        """Test that execute returns a TaskResult."""
        from benchmarks.tasks.base import TaskResult
        from benchmarks.tasks.edit_single import SingleEditTask

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Edited content here")]
        mock_response.usage.input_tokens = 150
        mock_response.usage.output_tokens = 75

        with patch("benchmarks.tasks.edit_single.anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.Anthropic.return_value = mock_client

            task = SingleEditTask(edit_instruction="Make it shorter")
            result = task.execute("Original content that is long")

            assert isinstance(result, TaskResult)
            assert result.prompt_tokens == 150
            assert result.completion_tokens == 75
            assert "Edited content" in result.result_text

    def test_execute_sends_instruction_and_content(self) -> None:
        """Test that execute sends both instruction and content to API."""
        from benchmarks.tasks.edit_single import SingleEditTask

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Edited")]
        mock_response.usage.input_tokens = 50
        mock_response.usage.output_tokens = 20

        test_instruction = "Add more details about XYZ"
        test_content = "Document content ABC123"

        with patch("benchmarks.tasks.edit_single.anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.Anthropic.return_value = mock_client

            task = SingleEditTask(edit_instruction=test_instruction)
            task.execute(test_content)

            call_args = mock_client.messages.create.call_args
            call_str = str(call_args)

            # Both instruction and content should be in the call
            assert "XYZ" in call_str or test_instruction in call_str
            assert "ABC123" in call_str or test_content in call_str

    def test_execute_handles_api_error(self) -> None:
        """Test that execute handles API errors gracefully."""
        from benchmarks.tasks.base import TaskResult
        from benchmarks.tasks.edit_single import SingleEditTask

        with patch("benchmarks.tasks.edit_single.anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.side_effect = Exception("Connection failed")
            mock_anthropic.Anthropic.return_value = mock_client

            task = SingleEditTask(edit_instruction="Edit this")
            result = task.execute("Content")

            assert isinstance(result, TaskResult)
            assert result.error is not None
            assert "Connection failed" in result.error

    def test_result_contains_edited_content(self) -> None:
        """Test that the result contains the edited content from API."""
        from benchmarks.tasks.edit_single import SingleEditTask

        edited_text = "This is the edited version of the document"

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=edited_text)]
        mock_response.usage.input_tokens = 100
        mock_response.usage.output_tokens = 50

        with patch("benchmarks.tasks.edit_single.anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.Anthropic.return_value = mock_client

            task = SingleEditTask(edit_instruction="Improve clarity")
            result = task.execute("Original document")

            assert result.result_text == edited_text
