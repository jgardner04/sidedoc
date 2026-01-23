"""Pandoc pipeline implementation (US-007).

This pipeline uses Pandoc for document processing via pypandoc.
It converts docx to markdown for editing and back to docx for output.
Note: Pandoc conversion loses significant formatting.
"""

import shutil
import time
from pathlib import Path

import pypandoc

from benchmarks.pipelines.base import BasePipeline, PipelineResult


class PandocNotFoundError(Exception):
    """Raised when Pandoc is not installed or not found in PATH."""

    def __init__(self) -> None:
        super().__init__(
            "Pandoc not found. Please install Pandoc:\n"
            "  - macOS: brew install pandoc\n"
            "  - Ubuntu: sudo apt install pandoc\n"
            "  - Windows: Download from https://pandoc.org/installing.html"
        )


def check_pandoc() -> bool:
    """Check if Pandoc is installed.

    Returns:
        True if Pandoc is available.

    Raises:
        PandocNotFoundError: If Pandoc is not found.
    """
    pandoc_path = shutil.which("pandoc")
    if pandoc_path:
        return True
    raise PandocNotFoundError()


class PandocPipeline(BasePipeline):
    """Pipeline that uses Pandoc for document processing.

    This pipeline:
    1. Converts docx to markdown using pypandoc
    2. Allows editing of the markdown content
    3. Converts markdown back to docx using pypandoc

    Note: Pandoc conversion loses most original formatting.
    """

    def __init__(self) -> None:
        """Initialize the Pandoc pipeline."""
        self._current_content: str = ""

    def extract_content(self, document_path: Path) -> str:
        """Extract text content from a document using Pandoc.

        Args:
            document_path: Path to the document to extract from.

        Returns:
            The extracted text content as markdown.
        """
        check_pandoc()

        # Convert docx to markdown using pypandoc
        markdown_content: str = pypandoc.convert_file(
            str(document_path),
            "markdown",
            format="docx",
        )

        self._current_content = markdown_content
        return markdown_content

    def apply_edit(self, content: str, edit_instruction: str) -> str:
        """Apply an edit to the content.

        For the Pandoc pipeline, the edit_instruction is simply appended
        to the content.

        Args:
            content: The original text content.
            edit_instruction: The edit to apply (appended to content).

        Returns:
            The edited content as a string.
        """
        edited_content = content + edit_instruction
        self._current_content = edited_content
        return edited_content

    def rebuild_document(
        self, content: str, original_path: Path, output_path: Path
    ) -> PipelineResult:
        """Rebuild a document from edited content using Pandoc.

        Args:
            content: The edited text content.
            original_path: Path to the original document (not used by Pandoc).
            output_path: Path where the rebuilt document should be saved.

        Returns:
            PipelineResult with metrics and status.
        """
        start_time = time.time()

        try:
            check_pandoc()

            # Convert markdown to docx using pypandoc
            pypandoc.convert_text(
                content,
                "docx",
                format="markdown",
                outputfile=str(output_path),
            )

            elapsed = time.time() - start_time

            # Calculate token counts (simple character-based approximation)
            input_tokens = len(content) // 4
            output_tokens = input_tokens

            return PipelineResult(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                time_elapsed=elapsed,
                output_path=output_path,
                error=None,
            )

        except Exception as e:
            elapsed = time.time() - start_time
            return PipelineResult(
                input_tokens=0,
                output_tokens=0,
                time_elapsed=elapsed,
                output_path=None,
                error=str(e),
            )
