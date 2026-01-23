"""Tests for base task interface (US-017)."""

from pathlib import Path

import pytest


BENCHMARKS_DIR = Path(__file__).parent.parent


class TestBaseTask:
    """Test the base task interface (US-017)."""

    def test_module_exists(self) -> None:
        """Test that base.py exists in tasks directory."""
        module_path = BENCHMARKS_DIR / "tasks" / "base.py"
        assert module_path.exists(), "benchmarks/tasks/base.py does not exist"

    def test_base_task_is_importable(self) -> None:
        """Test that BaseTask can be imported."""
        from benchmarks.tasks.base import BaseTask

        assert BaseTask is not None

    def test_task_result_is_importable(self) -> None:
        """Test that TaskResult can be imported."""
        from benchmarks.tasks.base import TaskResult

        assert TaskResult is not None

    def test_base_task_is_abstract(self) -> None:
        """Test that BaseTask is an abstract class."""
        from abc import ABC

        from benchmarks.tasks.base import BaseTask

        assert issubclass(BaseTask, ABC)

    def test_base_task_has_execute_method(self) -> None:
        """Test that BaseTask has abstract execute method."""
        from benchmarks.tasks.base import BaseTask

        assert hasattr(BaseTask, "execute")

    def test_task_result_has_required_fields(self) -> None:
        """Test that TaskResult has required fields."""
        from benchmarks.tasks.base import TaskResult

        result = TaskResult(
            prompt_tokens=100,
            completion_tokens=50,
            result_text="Test result",
            error=None,
        )

        assert result.prompt_tokens == 100
        assert result.completion_tokens == 50
        assert result.result_text == "Test result"
        assert result.error is None

    def test_task_result_accepts_error(self) -> None:
        """Test that TaskResult can contain an error."""
        from benchmarks.tasks.base import TaskResult

        result = TaskResult(
            prompt_tokens=0,
            completion_tokens=0,
            result_text="",
            error="Test error",
        )

        assert result.error == "Test error"

    def test_base_task_execute_returns_task_result(self) -> None:
        """Test that execute method signature expects str and returns TaskResult."""
        from benchmarks.tasks.base import BaseTask, TaskResult

        # Create a concrete implementation to test
        class ConcreteTask(BaseTask):
            def execute(self, content: str) -> TaskResult:
                return TaskResult(
                    prompt_tokens=len(content),
                    completion_tokens=10,
                    result_text="Executed",
                    error=None,
                )

        task = ConcreteTask()
        result = task.execute("test content")

        assert isinstance(result, TaskResult)
        assert result.result_text == "Executed"

    def test_base_task_cannot_be_instantiated(self) -> None:
        """Test that BaseTask cannot be directly instantiated."""
        from benchmarks.tasks.base import BaseTask

        with pytest.raises(TypeError):
            BaseTask()  # type: ignore
