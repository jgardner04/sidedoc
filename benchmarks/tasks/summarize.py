"""Summarization task (US-018).

This module provides the SummarizeTask which uses LiteLLM
to generate bullet point summaries of document content.
"""

import litellm

from benchmarks.tasks.base import BaseTask, TaskResult


class SummarizeTask(BaseTask):
    """Task that summarizes document content in 3-5 bullet points.

    Uses LiteLLM for unified access to multiple LLM providers.
    Provider-specific API keys are read from environment variables.
    """

    SUMMARIZATION_PROMPT = (
        "Summarize this document in 3-5 bullet points. "
        "Focus on the key points and main ideas."
    )

    def execute(self, content: str, model: str) -> TaskResult:
        """Execute the summarization task on the given content.

        Args:
            content: The document content to summarize.
            model: The LLM model identifier (e.g., 'claude-sonnet-4-20250514', 'ollama/llama3').

        Returns:
            TaskResult with summary and token counts.
        """
        try:
            response = litellm.completion(
                model=model,
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": f"{self.SUMMARIZATION_PROMPT}\n\n{content}",
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
