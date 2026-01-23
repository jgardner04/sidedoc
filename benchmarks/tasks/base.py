"""Base task interface (US-017).

This module provides the abstract base class for benchmark tasks
and the TaskResult dataclass for task execution results.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class TaskResult:
    """Result from executing a benchmark task.

    Attributes:
        prompt_tokens: Number of tokens in the prompt sent to the API.
        completion_tokens: Number of tokens in the API response.
        result_text: The text result from the task execution.
        error: Error message if the task failed, None otherwise.
    """

    prompt_tokens: int
    completion_tokens: int
    result_text: str
    error: Optional[str]


class BaseTask(ABC):
    """Abstract base class for benchmark tasks.

    All benchmark tasks must implement the execute() method
    which takes document content and returns a TaskResult.
    """

    @abstractmethod
    def execute(self, content: str) -> TaskResult:
        """Execute the task on the given document content.

        Args:
            content: The document content to process.

        Returns:
            TaskResult with execution metrics and result.
        """
        pass
