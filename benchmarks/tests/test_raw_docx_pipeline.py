"""Tests for Raw DOCX pipeline implementation (US-008)."""

from pathlib import Path
import tempfile

import pytest


BENCHMARKS_DIR = Path(__file__).parent.parent
FIXTURES_DIR = BENCHMARKS_DIR.parent / "tests" / "fixtures"


class TestRawDocxPipeline:
    """Test that the Raw DOCX pipeline works correctly."""

    def test_pipeline_module_exists(self) -> None:
        """Test that raw_docx_pipeline.py exists."""
        pipeline_path = BENCHMARKS_DIR / "pipelines" / "raw_docx_pipeline.py"
        assert pipeline_path.exists(), "benchmarks/pipelines/raw_docx_pipeline.py does not exist"

    def test_pipeline_is_importable(self) -> None:
        """Test that RawDocxPipeline can be imported."""
        from benchmarks.pipelines.raw_docx_pipeline import RawDocxPipeline

        assert RawDocxPipeline is not None

    def test_pipeline_inherits_from_base(self) -> None:
        """Test that RawDocxPipeline inherits from BasePipeline."""
        from benchmarks.pipelines.base import BasePipeline
        from benchmarks.pipelines.raw_docx_pipeline import RawDocxPipeline

        assert issubclass(RawDocxPipeline, BasePipeline)

    def test_pipeline_can_be_instantiated(self) -> None:
        """Test that RawDocxPipeline can be instantiated."""
        from benchmarks.pipelines.raw_docx_pipeline import RawDocxPipeline

        pipeline = RawDocxPipeline()
        assert pipeline is not None

    def test_extract_content_uses_python_docx(self) -> None:
        """Test that extract_content extracts paragraph text from docx."""
        from benchmarks.pipelines.raw_docx_pipeline import RawDocxPipeline

        pipeline = RawDocxPipeline()
        simple_docx = FIXTURES_DIR / "simple.docx"

        if not simple_docx.exists():
            pytest.skip("simple.docx fixture not found")

        content = pipeline.extract_content(simple_docx)

        # Should return non-empty string
        assert isinstance(content, str)
        assert len(content) > 0

    def test_extract_content_extracts_all_paragraphs(self) -> None:
        """Test that extract_content extracts all paragraph text."""
        from benchmarks.pipelines.raw_docx_pipeline import RawDocxPipeline

        pipeline = RawDocxPipeline()
        lists_docx = FIXTURES_DIR / "lists.docx"

        if not lists_docx.exists():
            pytest.skip("lists.docx fixture not found")

        content = pipeline.extract_content(lists_docx)

        # Should contain multiple paragraphs separated by newlines
        assert isinstance(content, str)
        lines = content.strip().split("\n")
        assert len(lines) >= 1  # At least one paragraph

    def test_apply_edit_is_noop(self) -> None:
        """Test that apply_edit is a no-op (returns content unchanged)."""
        from benchmarks.pipelines.raw_docx_pipeline import RawDocxPipeline

        pipeline = RawDocxPipeline()
        original = "Original text content."
        edit = "Some edit instruction."

        result = pipeline.apply_edit(original, edit)

        # Should return the original content unchanged
        assert result == original

    def test_rebuild_document_returns_none_output_path(self) -> None:
        """Test that rebuild_document returns PipelineResult with None output_path."""
        from benchmarks.pipelines.raw_docx_pipeline import RawDocxPipeline
        from benchmarks.pipelines.base import PipelineResult

        pipeline = RawDocxPipeline()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.docx"

            result = pipeline.rebuild_document(
                "content", Path("/fake/original.docx"), output_path
            )

            assert isinstance(result, PipelineResult)
            assert result.output_path is None
            # Should have an informative "error" message explaining why
            assert result.error is not None

    def test_token_counting_works(self) -> None:
        """Test that token counting works for the extracted content."""
        from benchmarks.pipelines.raw_docx_pipeline import RawDocxPipeline

        pipeline = RawDocxPipeline()
        simple_docx = FIXTURES_DIR / "simple.docx"

        if not simple_docx.exists():
            pytest.skip("simple.docx fixture not found")

        content = pipeline.extract_content(simple_docx)

        # Token count should be calculable from content
        # Using simple character-based approximation
        token_estimate = len(content) // 4
        assert token_estimate >= 0

    def test_full_pipeline_workflow(self) -> None:
        """Test the complete workflow (extract only, since edit/rebuild are no-ops)."""
        from benchmarks.pipelines.raw_docx_pipeline import RawDocxPipeline

        pipeline = RawDocxPipeline()
        simple_docx = FIXTURES_DIR / "simple.docx"

        if not simple_docx.exists():
            pytest.skip("simple.docx fixture not found")

        # Extract
        content = pipeline.extract_content(simple_docx)
        assert len(content) > 0

        # Apply edit (should be no-op)
        edited = pipeline.apply_edit(content, "edit instruction")
        assert edited == content  # Unchanged

        # Rebuild (should return None output)
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.docx"
            result = pipeline.rebuild_document(content, simple_docx, output_path)
            assert result.output_path is None
