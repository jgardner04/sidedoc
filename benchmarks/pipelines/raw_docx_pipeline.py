"""Raw DOCX pipeline implementation (US-008).

This pipeline extracts raw text from docx files using python-docx.
It serves as a baseline for comparison - it can extract text but cannot
apply edits or rebuild documents.
"""

import time
from pathlib import Path

from docx import Document

from benchmarks.metrics.token_counter import TokenCounter
from benchmarks.pipelines.base import BasePipeline, PipelineResult


class RawDocxPipeline(BasePipeline):
    """Pipeline that extracts raw text from docx files.

    This pipeline:
    1. Extracts all paragraph text from docx using python-docx
    2. Cannot apply edits (returns content unchanged)
    3. Cannot rebuild documents (returns None)

    This serves as a baseline for token counting comparison.
    """

    def __init__(self) -> None:
        """Initialize the Raw DOCX pipeline."""
        self._current_content: str = ""
        self._token_counter = TokenCounter()

    def extract_content(self, document_path: Path) -> str:
        """Extract text content from a document using python-docx.

        Args:
            document_path: Path to the document to extract from.

        Returns:
            The extracted text content as a string (all paragraph text).
        """
        doc = Document(str(document_path))

        # Extract text from all paragraphs
        paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
        content = "\n".join(paragraphs)

        self._current_content = content
        return content

    def apply_edit(self, content: str, edit_instruction: str) -> str:
        """Apply an edit to the content (no-op for raw docx).

        Raw DOCX pipeline cannot apply edits - it simply returns the
        original content unchanged. This is because raw text extraction
        loses all formatting information needed to reconstruct the document.

        Args:
            content: The original text content.
            edit_instruction: The edit instruction (ignored).

        Returns:
            The original content unchanged.
        """
        return content

    def rebuild_document(
        self, content: str, original_path: Path, output_path: Path
    ) -> PipelineResult:
        """Rebuild a document from edited content (not supported).

        Raw DOCX pipeline cannot rebuild documents - this is a baseline
        for comparison only.

        Args:
            content: The text content.
            original_path: Path to the original document.
            output_path: Path where the rebuilt document would be saved.

        Returns:
            PipelineResult with None output_path and an explanatory error.
        """
        start_time = time.time()
        elapsed = time.time() - start_time

        # Calculate token counts using proper tokenizer
        input_tokens = self._token_counter.count_tokens(content)
        output_tokens = 0  # No output generated

        return PipelineResult(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            time_elapsed=elapsed,
            output_path=None,
            error="Raw DOCX pipeline cannot rebuild documents (baseline for comparison only)",
        )
