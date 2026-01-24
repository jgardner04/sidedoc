"""Tests for multi-turn edit task (US-020)."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


BENCHMARKS_DIR = Path(__file__).parent.parent


class TestMultiTurnEditTask:
    """Test the multi-turn edit task (US-020)."""

    def test_module_exists(self) -> None:
        """Test that edit_multiturn.py exists in tasks directory."""
        module_path = BENCHMARKS_DIR / "tasks" / "edit_multiturn.py"
        assert module_path.exists(), "benchmarks/tasks/edit_multiturn.py does not exist"

    def test_multi_turn_edit_task_is_importable(self) -> None:
        """Test that MultiTurnEditTask can be imported."""
        from benchmarks.tasks.edit_multiturn import MultiTurnEditTask

        assert MultiTurnEditTask is not None

    def test_multi_turn_edit_task_inherits_from_base(self) -> None:
        """Test that MultiTurnEditTask inherits from BaseTask."""
        from benchmarks.tasks.base import BaseTask
        from benchmarks.tasks.edit_multiturn import MultiTurnEditTask

        assert issubclass(MultiTurnEditTask, BaseTask)

    def test_multi_turn_edit_task_takes_list_of_instructions(self) -> None:
        """Test that MultiTurnEditTask takes list of 3 edit instructions."""
        from benchmarks.tasks.edit_multiturn import MultiTurnEditTask

        instructions = [
            "Make it shorter",
            "Add more details",
            "Fix grammar",
        ]
        task = MultiTurnEditTask(edit_instructions=instructions)
        assert task.edit_instructions == instructions

    def test_multi_turn_edit_task_has_execute_method(self) -> None:
        """Test that MultiTurnEditTask has execute method."""
        from benchmarks.tasks.edit_multiturn import MultiTurnEditTask

        task = MultiTurnEditTask(edit_instructions=["Edit 1", "Edit 2", "Edit 3"])
        assert hasattr(task, "execute")
        assert callable(task.execute)

    def test_execute_returns_task_result(self) -> None:
        """Test that execute returns a TaskResult."""
        from benchmarks.tasks.base import TaskResult
        from benchmarks.tasks.edit_multiturn import MultiTurnEditTask

        def mock_completion(*args, **kwargs):
            response = MagicMock()
            mock_choice = MagicMock()
            mock_choice.message.content = "Edited content"
            response.choices = [mock_choice]
            response.usage.prompt_tokens = 100
            response.usage.completion_tokens = 50
            return response

        with patch("benchmarks.tasks.edit_multiturn.litellm") as mock_litellm:
            mock_litellm.completion.side_effect = mock_completion

            task = MultiTurnEditTask(edit_instructions=["E1", "E2", "E3"])
            result = task.execute("Original content", "claude-sonnet-4-20250514")

            assert isinstance(result, TaskResult)

    def test_execute_runs_3_rounds(self) -> None:
        """Test that execute runs 3 rounds of edits."""
        from benchmarks.tasks.edit_multiturn import MultiTurnEditTask

        call_count = 0

        def mock_completion(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            response = MagicMock()
            mock_choice = MagicMock()
            mock_choice.message.content = f"Edit round {call_count}"
            response.choices = [mock_choice]
            response.usage.prompt_tokens = 100
            response.usage.completion_tokens = 50
            return response

        with patch("benchmarks.tasks.edit_multiturn.litellm") as mock_litellm:
            mock_litellm.completion.side_effect = mock_completion

            task = MultiTurnEditTask(edit_instructions=["E1", "E2", "E3"])
            task.execute("Content", "claude-sonnet-4-20250514")

            assert call_count == 3

    def test_execute_accumulates_tokens(self) -> None:
        """Test that execute accumulates token counts across rounds."""
        from benchmarks.tasks.edit_multiturn import MultiTurnEditTask

        round_num = 0

        def mock_completion(*args, **kwargs):
            nonlocal round_num
            round_num += 1
            response = MagicMock()
            mock_choice = MagicMock()
            mock_choice.message.content = "Edited"
            response.choices = [mock_choice]
            response.usage.prompt_tokens = 100 * round_num
            response.usage.completion_tokens = 50 * round_num
            return response

        with patch("benchmarks.tasks.edit_multiturn.litellm") as mock_litellm:
            mock_litellm.completion.side_effect = mock_completion

            task = MultiTurnEditTask(edit_instructions=["E1", "E2", "E3"])
            result = task.execute("Content", "claude-sonnet-4-20250514")

            # Total should be 100+200+300=600 input, 50+100+150=300 output
            assert result.prompt_tokens == 600
            assert result.completion_tokens == 300

    def test_result_contains_final_edited_content(self) -> None:
        """Test that the result contains the final edited content."""
        from benchmarks.tasks.edit_multiturn import MultiTurnEditTask

        round_num = 0

        def mock_completion(*args, **kwargs):
            nonlocal round_num
            round_num += 1
            response = MagicMock()
            mock_choice = MagicMock()
            mock_choice.message.content = f"After edit {round_num}"
            response.choices = [mock_choice]
            response.usage.prompt_tokens = 50
            response.usage.completion_tokens = 25
            return response

        with patch("benchmarks.tasks.edit_multiturn.litellm") as mock_litellm:
            mock_litellm.completion.side_effect = mock_completion

            task = MultiTurnEditTask(edit_instructions=["E1", "E2", "E3"])
            result = task.execute("Original", "claude-sonnet-4-20250514")

            # Final result should be from round 3
            assert result.result_text == "After edit 3"

    def test_execute_passes_output_to_next_round(self) -> None:
        """Test that each round's output becomes input for next round."""
        from benchmarks.tasks.edit_multiturn import MultiTurnEditTask

        call_inputs = []

        def mock_completion(*args, **kwargs):
            messages = kwargs.get("messages", [])
            if messages:
                call_inputs.append(messages[0]["content"])
            response = MagicMock()
            mock_choice = MagicMock()
            content = f"Output{len(call_inputs)}"
            mock_choice.message.content = content
            response.choices = [mock_choice]
            response.usage.prompt_tokens = 50
            response.usage.completion_tokens = 25
            return response

        with patch("benchmarks.tasks.edit_multiturn.litellm") as mock_litellm:
            mock_litellm.completion.side_effect = mock_completion

            task = MultiTurnEditTask(edit_instructions=["E1", "E2", "E3"])
            task.execute("Original", "claude-sonnet-4-20250514")

            # Round 2 should receive Output1, Round 3 should receive Output2
            assert "Output1" in call_inputs[1]
            assert "Output2" in call_inputs[2]

    def test_execute_handles_api_error(self) -> None:
        """Test that execute handles API errors gracefully."""
        from benchmarks.tasks.base import TaskResult
        from benchmarks.tasks.edit_multiturn import MultiTurnEditTask

        with patch("benchmarks.tasks.edit_multiturn.litellm") as mock_litellm:
            mock_litellm.completion.side_effect = Exception("API failed")

            task = MultiTurnEditTask(edit_instructions=["E1", "E2", "E3"])
            result = task.execute("Content", "claude-sonnet-4-20250514")

            assert isinstance(result, TaskResult)
            assert result.error is not None
            assert "API failed" in result.error
