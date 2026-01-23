"""Single-edit task (US-019).

This module provides the SingleEditTask which uses the Anthropic API
to apply a single edit instruction to document content.
"""

import anthropic

from benchmarks.tasks.base import BaseTask, TaskResult


class SingleEditTask(BaseTask):
    """Task that applies a single edit instruction to document content.

    Uses the Anthropic API (Claude) to process the edit.
    Reads ANTHROPIC_API_KEY from environment.
    """

    def __init__(self, edit_instruction: str) -> None:
        """Initialize the single-edit task.

        Args:
            edit_instruction: The instruction describing the edit to apply.
        """
        self.edit_instruction = edit_instruction
        self._client = anthropic.Anthropic()

    def execute(self, content: str) -> TaskResult:
        """Execute the edit task on the given content.

        Args:
            content: The document content to edit.

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

            message = self._client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
            )

            result_text = ""
            if message.content:
                first_block = message.content[0]
                if hasattr(first_block, "text"):
                    result_text = first_block.text

            return TaskResult(
                prompt_tokens=message.usage.input_tokens,
                completion_tokens=message.usage.output_tokens,
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
