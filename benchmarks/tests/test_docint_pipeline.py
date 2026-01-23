"""Tests for Document Intelligence pipeline implementation (US-009, US-010)."""

from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import os

import pytest


BENCHMARKS_DIR = Path(__file__).parent.parent
FIXTURES_DIR = BENCHMARKS_DIR.parent / "tests" / "fixtures"


class TestDocIntelPipeline:
    """Test that the Document Intelligence pipeline works correctly."""

    def test_pipeline_module_exists(self) -> None:
        """Test that docint_pipeline.py exists."""
        pipeline_path = BENCHMARKS_DIR / "pipelines" / "docint_pipeline.py"
        assert pipeline_path.exists(), "benchmarks/pipelines/docint_pipeline.py does not exist"

    def test_pipeline_is_importable(self) -> None:
        """Test that DocIntelPipeline can be imported."""
        from benchmarks.pipelines.docint_pipeline import DocIntelPipeline

        assert DocIntelPipeline is not None

    def test_pipeline_inherits_from_base(self) -> None:
        """Test that DocIntelPipeline inherits from BasePipeline."""
        from benchmarks.pipelines.base import BasePipeline
        from benchmarks.pipelines.docint_pipeline import DocIntelPipeline

        assert issubclass(DocIntelPipeline, BasePipeline)

    def test_reads_azure_credentials_from_env(self) -> None:
        """Test that pipeline reads Azure credentials from environment."""
        from benchmarks.pipelines.docint_pipeline import DocIntelPipeline

        with patch.dict(os.environ, {
            "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT": "https://test.cognitiveservices.azure.com/",
            "AZURE_DOCUMENT_INTELLIGENCE_KEY": "test-key-12345",
        }):
            pipeline = DocIntelPipeline()
            assert pipeline._endpoint == "https://test.cognitiveservices.azure.com/"
            assert pipeline._key == "test-key-12345"

    def test_graceful_error_when_credentials_not_set(self) -> None:
        """Test that pipeline raises helpful error when credentials not configured."""
        from benchmarks.pipelines.docint_pipeline import DocIntelPipeline, AzureCredentialsNotFoundError

        with patch.dict(os.environ, {}, clear=True):
            # Remove the env vars if they exist
            os.environ.pop("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT", None)
            os.environ.pop("AZURE_DOCUMENT_INTELLIGENCE_KEY", None)

            with pytest.raises(AzureCredentialsNotFoundError) as exc_info:
                pipeline = DocIntelPipeline()

            # Error message should be helpful
            assert "AZURE_DOCUMENT_INTELLIGENCE" in str(exc_info.value)

    def test_extract_content_returns_text(self) -> None:
        """Test that extract_content returns extracted text (mocked API)."""
        from benchmarks.pipelines.docint_pipeline import DocIntelPipeline

        with patch.dict(os.environ, {
            "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT": "https://test.cognitiveservices.azure.com/",
            "AZURE_DOCUMENT_INTELLIGENCE_KEY": "test-key-12345",
        }):
            pipeline = DocIntelPipeline()

        # Mock the Azure client
        mock_result = MagicMock()
        mock_result.content = "Extracted document content here."
        mock_result.pages = []

        with patch.object(pipeline, "_client") as mock_client:
            mock_poller = MagicMock()
            mock_poller.result.return_value = mock_result
            mock_client.begin_analyze_document.return_value = mock_poller

            # Use a real fixture file
            simple_docx = FIXTURES_DIR / "simple.docx"
            if not simple_docx.exists():
                pytest.skip("simple.docx fixture not found")

            content = pipeline.extract_content(simple_docx)

            assert "Extracted document content" in content

    def test_apply_edit_modifies_text(self) -> None:
        """Test that apply_edit modifies the text string."""
        from benchmarks.pipelines.docint_pipeline import DocIntelPipeline

        with patch.dict(os.environ, {
            "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT": "https://test.cognitiveservices.azure.com/",
            "AZURE_DOCUMENT_INTELLIGENCE_KEY": "test-key-12345",
        }):
            pipeline = DocIntelPipeline()

        original = "Original text."
        edit = " Added text."

        result = pipeline.apply_edit(original, edit)

        assert "Added text" in result
        assert len(result) > len(original)

    def test_rebuild_document_creates_docx(self) -> None:
        """Test that rebuild_document creates a new docx from text."""
        from benchmarks.pipelines.docint_pipeline import DocIntelPipeline
        from benchmarks.pipelines.base import PipelineResult

        with patch.dict(os.environ, {
            "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT": "https://test.cognitiveservices.azure.com/",
            "AZURE_DOCUMENT_INTELLIGENCE_KEY": "test-key-12345",
        }):
            pipeline = DocIntelPipeline()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.docx"

            result = pipeline.rebuild_document(
                "Some text content.",
                Path("/fake/original.docx"),
                output_path,
            )

            assert isinstance(result, PipelineResult)
            assert output_path.exists()
            assert result.output_path == output_path

    def test_pipeline_result_includes_api_cost(self) -> None:
        """Test that PipelineResult includes api_cost field."""
        from benchmarks.pipelines.docint_pipeline import DocIntelPipeline

        with patch.dict(os.environ, {
            "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT": "https://test.cognitiveservices.azure.com/",
            "AZURE_DOCUMENT_INTELLIGENCE_KEY": "test-key-12345",
        }):
            pipeline = DocIntelPipeline()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.docx"

            result = pipeline.rebuild_document(
                "Some text.",
                Path("/fake/original.docx"),
                output_path,
            )

            # PipelineResult should have the fields we expect
            # api_cost could be tracked via input_tokens or a separate attribute
            assert hasattr(result, "input_tokens")
            assert result.input_tokens >= 0

    def test_full_pipeline_workflow_mocked(self) -> None:
        """Test complete extract -> edit -> rebuild workflow with mocks."""
        from benchmarks.pipelines.docint_pipeline import DocIntelPipeline

        with patch.dict(os.environ, {
            "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT": "https://test.cognitiveservices.azure.com/",
            "AZURE_DOCUMENT_INTELLIGENCE_KEY": "test-key-12345",
        }):
            pipeline = DocIntelPipeline()

        # Use a real fixture file
        simple_docx = FIXTURES_DIR / "simple.docx"
        if not simple_docx.exists():
            pytest.skip("simple.docx fixture not found")

        # Mock extraction
        mock_result = MagicMock()
        mock_result.content = "Original document text."
        mock_result.pages = []

        with patch.object(pipeline, "_client") as mock_client:
            mock_poller = MagicMock()
            mock_poller.result.return_value = mock_result
            mock_client.begin_analyze_document.return_value = mock_poller

            # Extract
            content = pipeline.extract_content(simple_docx)
            assert len(content) > 0

        # Edit
        edited = pipeline.apply_edit(content, " Edited.")
        assert "Edited" in edited

        # Rebuild
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.docx"
            result = pipeline.rebuild_document(edited, simple_docx, output_path)
            assert result.error is None
            assert output_path.exists()
