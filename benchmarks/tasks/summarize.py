"""Summarization task (US-018).

This module provides the SummarizeTask which uses the Anthropic API
to generate bullet point summaries of document content.
"""

import anthropic

from benchmarks.tasks.base import BaseTask, TaskResult


class SummarizeTask(BaseTask):
    """Task that summarizes document content in 3-5 bullet points.

    Uses the Anthropic API (Claude) to generate summaries.
    Reads ANTHROPIC_API_KEY from environment.
    """

    SUMMARIZATION_PROMPT = (
        "Summarize this document in 3-5 bullet points. "
        "Focus on the key points and main ideas."
    )

    def __init__(self) -> None:
        """Initialize the summarization task."""
        self._client = anthropic.Anthropic()

    def execute(self, content: str) -> TaskResult:
        """Execute the summarization task on the given content.

        Args:
            content: The document content to summarize.

        Returns:
            TaskResult with summary and token counts.
        """
        try:
            message = self._client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": f"{self.SUMMARIZATION_PROMPT}\n\n{content}",
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
