"""Single-edit task (US-019).

This module provides the SingleEditTask which uses LiteLLM
to apply a single edit instruction to document content.
"""

import litellm

from benchmarks.tasks.base import BaseTask, TaskResult


class SingleEditTask(BaseTask):
    """Task that applies a single edit instruction to document content.

    Uses LiteLLM for unified access to multiple LLM providers.
    Provider-specific API keys are read from environment variables.
    """

    def __init__(self, edit_instruction: str) -> None:
        """Initialize the single-edit task.

        Args:
            edit_instruction: The instruction describing the edit to apply.
        """
        self.edit_instruction = edit_instruction

    def execute(self, content: str, model: str) -> TaskResult:
        """Execute the edit task on the given content.

        Args:
            content: The document content to edit.
            model: The LLM model identifier (e.g., 'claude-sonnet-4-20250514', 'ollama/llama3').

        Returns:
            TaskResult with edited content and token counts.
        """
        try:
            prompt = (
                f"Apply the following edit to the document:\n\n"
                f"Edit instruction: {self.edit_instruction}\n\n"
                f"Document:\n{content}\n\n"
                f"Return only the edited document, without explanation."
            )

            response = litellm.completion(
                model=model,
                max_tokens=4096,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
            )

            result_text = ""
            if response.choices and response.choices[0].message:
                result_text = response.choices[0].message.content or ""

            # Get token usage from response
            prompt_tokens = 0
            completion_tokens = 0
            if response.usage:
                prompt_tokens = response.usage.prompt_tokens or 0
                completion_tokens = response.usage.completion_tokens or 0

            return TaskResult(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                result_text=result_text,
                error=None,
            )

        except Exception as e:
            return TaskResult(
                prompt_tokens=0,
                completion_tokens=0,
                result_text="",
                error=str(e),
            )
