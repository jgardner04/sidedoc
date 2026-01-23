"""Base pipeline interface for document processing (US-005).

This module defines the abstract base class that all benchmark pipelines
must implement, as well as the result dataclass for pipeline operations.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class PipelineResult:
    """Result of a pipeline operation.

    Attributes:
        input_tokens: Number of tokens in the input content.
        output_tokens: Number of tokens in the output content.
        time_elapsed: Time taken for the operation in seconds.
        output_path: Path to the output file, if any.
        error: Error message if the operation failed, None otherwise.
    """

    input_tokens: int
    output_tokens: int
    time_elapsed: float
    output_path: Optional[Path]
    error: Optional[str]


class BasePipeline(ABC):
    """Abstract base class for document processing pipelines.

    All benchmark pipelines must inherit from this class and implement
    the abstract methods for extracting content, applying edits, and
    rebuilding documents.
    """

    @abstractmethod
    def extract_content(self, document_path: Path) -> str:
        """Extract text content from a document.

        Args:
            document_path: Path to the document to extract from.

        Returns:
            The extracted text content as a string.
        """
        pass

    @abstractmethod
    def apply_edit(self, content: str, edit_instruction: str) -> str:
        """Apply an edit to the content.

        Args:
            content: The original text content.
            edit_instruction: Instruction describing the edit to apply.

        Returns:
            The edited content as a string.
        """
        pass

    @abstractmethod
    def rebuild_document(self, content: str, original_path: Path, output_path: Path) -> PipelineResult:
        """Rebuild a document from edited content.

        Args:
            content: The edited text content.
            original_path: Path to the original document (for reference).
            output_path: Path where the rebuilt document should be saved.

        Returns:
            PipelineResult with metrics and status.
        """
        pass
