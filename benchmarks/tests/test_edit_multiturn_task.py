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

        def mock_create(*args, **kwargs):
            response = MagicMock()
            response.content = [MagicMock(text="Edited content")]
            response.usage.input_tokens = 100
            response.usage.output_tokens = 50
            return response

        with patch("benchmarks.tasks.edit_multiturn.anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.side_effect = mock_create
            mock_anthropic.Anthropic.return_value = mock_client

            task = MultiTurnEditTask(edit_instructions=["E1", "E2", "E3"])
            result = task.execute("Original content")

            assert isinstance(result, TaskResult)

    def test_execute_runs_3_rounds(self) -> None:
        """Test that execute runs 3 rounds of edits."""
        from benchmarks.tasks.edit_multiturn import MultiTurnEditTask

        call_count = 0

        def mock_create(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            response = MagicMock()
            response.content = [MagicMock(text=f"Edit round {call_count}")]
            response.usage.input_tokens = 100
            response.usage.output_tokens = 50
            return response

        with patch("benchmarks.tasks.edit_multiturn.anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.side_effect = mock_create
            mock_anthropic.Anthropic.return_value = mock_client

            task = MultiTurnEditTask(edit_instructions=["E1", "E2", "E3"])
            task.execute("Content")

            assert call_count == 3

    def test_execute_accumulates_tokens(self) -> None:
        """Test that execute accumulates token counts across rounds."""
        from benchmarks.tasks.edit_multiturn import MultiTurnEditTask

        round_num = 0

        def mock_create(*args, **kwargs):
            nonlocal round_num
            round_num += 1
            response = MagicMock()
            response.content = [MagicMock(text="Edited")]
            response.usage.input_tokens = 100 * round_num
            response.usage.output_tokens = 50 * round_num
            return response

        with patch("benchmarks.tasks.edit_multiturn.anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.side_effect = mock_create
            mock_anthropic.Anthropic.return_value = mock_client

            task = MultiTurnEditTask(edit_instructions=["E1", "E2", "E3"])
            result = task.execute("Content")

            # Total should be 100+200+300=600 input, 50+100+150=300 output
            assert result.prompt_tokens == 600
            assert result.completion_tokens == 300

    def test_result_contains_final_edited_content(self) -> None:
        """Test that the result contains the final edited content."""
        from benchmarks.tasks.edit_multiturn import MultiTurnEditTask

        round_num = 0

        def mock_create(*args, **kwargs):
            nonlocal round_num
            round_num += 1
            response = MagicMock()
            response.content = [MagicMock(text=f"After edit {round_num}")]
            response.usage.input_tokens = 50
            response.usage.output_tokens = 25
            return response

        with patch("benchmarks.tasks.edit_multiturn.anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.side_effect = mock_create
            mock_anthropic.Anthropic.return_value = mock_client

            task = MultiTurnEditTask(edit_instructions=["E1", "E2", "E3"])
            result = task.execute("Original")

            # Final result should be from round 3
            assert result.result_text == "After edit 3"

    def test_execute_passes_output_to_next_round(self) -> None:
        """Test that each round's output becomes input for next round."""
        from benchmarks.tasks.edit_multiturn import MultiTurnEditTask

        call_inputs = []

        def mock_create(*args, **kwargs):
            messages = kwargs.get("messages", [])
            if messages:
                call_inputs.append(messages[0]["content"])
            response = MagicMock()
            content = f"Output{len(call_inputs)}"
            response.content = [MagicMock(text=content)]
            response.usage.input_tokens = 50
            response.usage.output_tokens = 25
            return response

        with patch("benchmarks.tasks.edit_multiturn.anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.side_effect = mock_create
            mock_anthropic.Anthropic.return_value = mock_client

            task = MultiTurnEditTask(edit_instructions=["E1", "E2", "E3"])
            task.execute("Original")

            # Round 2 should receive Output1, Round 3 should receive Output2
            assert "Output1" in call_inputs[1]
            assert "Output2" in call_inputs[2]

    def test_execute_handles_api_error(self) -> None:
        """Test that execute handles API errors gracefully."""
        from benchmarks.tasks.base import TaskResult
        from benchmarks.tasks.edit_multiturn import MultiTurnEditTask

        with patch("benchmarks.tasks.edit_multiturn.anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.side_effect = Exception("API failed")
            mock_anthropic.Anthropic.return_value = mock_client

            task = MultiTurnEditTask(edit_instructions=["E1", "E2", "E3"])
            result = task.execute("Content")

            assert isinstance(result, TaskResult)
            assert result.error is not None
            assert "API failed" in result.error
