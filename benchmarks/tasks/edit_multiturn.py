"""Multi-turn edit task (US-020).

This module provides the MultiTurnEditTask which uses LiteLLM
to apply multiple sequential edit instructions to document content.
"""

import litellm

from benchmarks.tasks.base import BaseTask, TaskResult


class MultiTurnEditTask(BaseTask):
    """Task that applies multiple edit instructions sequentially.

    Uses LiteLLM for unified access to multiple LLM providers.
    Provider-specific API keys are read from environment variables.
    """

    def __init__(self, edit_instructions: list[str]) -> None:
        """Initialize the multi-turn edit task.

        Args:
            edit_instructions: List of 3 edit instructions to apply sequentially.
        """
        self.edit_instructions = edit_instructions

    def execute(self, content: str, model: str) -> TaskResult:
        """Execute the multi-turn edit task on the given content.

        Applies each edit instruction sequentially, passing the output
        of each round as input to the next round.

        Args:
            content: The document content to edit.
            model: The LLM model identifier (e.g., 'claude-sonnet-4-20250514', 'ollama/llama3').

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

                # Accumulate token usage
                if response.usage:
                    total_prompt_tokens += response.usage.prompt_tokens or 0
                    total_completion_tokens += response.usage.completion_tokens or 0

                # Get the edited content for next round
                if response.choices and response.choices[0].message:
                    current_content = response.choices[0].message.content or current_content

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
