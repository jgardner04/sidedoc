"""Document Intelligence pipeline implementation (US-009, US-010).

This pipeline uses Azure Document Intelligence to extract content from documents.
It can extract text but loses most formatting when rebuilding.
"""

import os
import time
from pathlib import Path
from typing import Optional, Any

from docx import Document

from benchmarks.metrics.token_counter import TokenCounter
from benchmarks.pipelines.base import BasePipeline, PipelineResult


class AzureCredentialsNotFoundError(Exception):
    """Raised when Azure Document Intelligence credentials are not configured."""

    def __init__(self) -> None:
        super().__init__(
            "Azure Document Intelligence credentials not found. "
            "Please set environment variables:\n"
            "  - AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT\n"
            "  - AZURE_DOCUMENT_INTELLIGENCE_KEY\n\n"
            "You can get these from the Azure Portal."
        )


class DocIntelPipeline(BasePipeline):
    """Pipeline that uses Azure Document Intelligence for document processing.

    This pipeline:
    1. Uses Azure Document Intelligence API to extract text from documents
    2. Allows editing of the extracted text
    3. Rebuilds documents as plain text (loses original formatting)

    Requires Azure Document Intelligence credentials to be configured.
    """

    def __init__(self) -> None:
        """Initialize the Document Intelligence pipeline.

        Raises:
            AzureCredentialsNotFoundError: If Azure credentials are not configured.
        """
        self._endpoint = os.environ.get("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
        self._key = os.environ.get("AZURE_DOCUMENT_INTELLIGENCE_KEY")

        if not self._endpoint or not self._key:
            raise AzureCredentialsNotFoundError()

        self._current_content: str = ""
        self._client: Optional[Any] = None
        self._api_cost: float = 0.0
        self._token_counter = TokenCounter()

        # Initialize the client lazily to avoid import errors when credentials not needed
        self._init_client()

    def _init_client(self) -> None:
        """Initialize the Azure Document Intelligence client."""
        try:
            from azure.ai.formrecognizer import DocumentAnalysisClient
            from azure.core.credentials import AzureKeyCredential

            self._client = DocumentAnalysisClient(
                endpoint=self._endpoint,
                credential=AzureKeyCredential(self._key),
            )
        except ImportError:
            # azure-ai-formrecognizer not installed, client will be None
            # Tests can mock _client directly
            pass

    def extract_content(self, document_path: Path) -> str:
        """Extract text content from a document using Azure Document Intelligence.

        Args:
            document_path: Path to the document to extract from.

        Returns:
            The extracted text content as a string.
        """
        if self._client is None:
            raise RuntimeError("Azure Document Intelligence client not initialized")

        with open(document_path, "rb") as f:
            poller = self._client.begin_analyze_document(
                "prebuilt-read",
                document=f,
            )
            result = poller.result()

        # Extract text content
        content: str = result.content if result.content else ""

        # Track approximate API cost (~$0.01 per page)
        page_count = len(result.pages) if hasattr(result, "pages") and result.pages else 1
        self._api_cost = page_count * 0.01

        self._current_content = content
        return content

    def apply_edit(self, content: str, edit_instruction: str) -> str:
        """Apply an edit to the content.

        For the Document Intelligence pipeline, the edit_instruction is
        simply appended to the content.

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
        """Rebuild a document from edited content.

        Note: Document Intelligence extracts text but loses formatting.
        The rebuilt document will be plain text in a docx wrapper.

        Args:
            content: The edited text content.
            original_path: Path to the original document (not used).
            output_path: Path where the rebuilt document should be saved.

        Returns:
            PipelineResult with metrics and status.
        """
        start_time = time.time()

        try:
            # Create a new docx with the text content
            doc = Document()

            # Split content into paragraphs and add them
            paragraphs = content.split("\n")
            for para_text in paragraphs:
                if para_text.strip():
                    doc.add_paragraph(para_text)

            doc.save(str(output_path))

            elapsed = time.time() - start_time

            # Calculate token counts using proper tokenizer
            input_tokens = self._token_counter.count_tokens(content)
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

    @property
    def api_cost(self) -> float:
        """Get the accumulated API cost for this pipeline."""
        return self._api_cost
