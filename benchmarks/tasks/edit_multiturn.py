"""Multi-turn edit task (US-020).

This module provides the MultiTurnEditTask which uses the Anthropic API
to apply multiple sequential edit instructions to document content.
"""

import anthropic

from benchmarks.tasks.base import BaseTask, TaskResult


class MultiTurnEditTask(BaseTask):
    """Task that applies multiple edit instructions sequentially.

    Uses the Anthropic API (Claude) to process 3 rounds of edits.
    Reads ANTHROPIC_API_KEY from environment.
    """

    def __init__(self, edit_instructions: list[str]) -> None:
        """Initialize the multi-turn edit task.

        Args:
            edit_instructions: List of 3 edit instructions to apply sequentially.
        """
        self.edit_instructions = edit_instructions
        self._client = anthropic.Anthropic()

    def execute(self, content: str) -> TaskResult:
        """Execute the multi-turn edit task on the given content.

        Applies each edit instruction sequentially, passing the output
        of each round as input to the next round.

        Args:
            content: The document content to edit.

        Returns:
            TaskResult with final content and accumulated token counts.
        """
        total_prompt_tokens = 0
        total_completion_tokens = 0
        current_content = content

        try:
            for instruction in self.edit_instructions:
                prompt = (
                    f"Apply the following edit to the document:\n\n"
                    f"Edit instruction: {instruction}\n\n"
                    f"Document:\n{current_content}\n\n"
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

                total_prompt_tokens += message.usage.input_tokens
                total_completion_tokens += message.usage.output_tokens

                # Get the edited content for next round
                if message.content:
                    first_block = message.content[0]
                    if hasattr(first_block, "text"):
                        current_content = first_block.text

            return TaskResult(
                prompt_tokens=total_prompt_tokens,
                completion_tokens=total_completion_tokens,
                result_text=current_content,
                error=None,
            )

        except Exception as e:
            return TaskResult(
                prompt_tokens=total_prompt_tokens,
                completion_tokens=total_completion_tokens,
                result_text=current_content,
                error=str(e),
            )
