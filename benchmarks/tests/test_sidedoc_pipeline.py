"""Tests for Sidedoc pipeline implementation (US-006)."""

from pathlib import Path
import tempfile
import zipfile

import pytest


class TestSidedocPipeline:
    """Test that the Sidedoc pipeline works correctly."""

    def test_pipeline_module_exists(self, benchmarks_dir: Path) -> None:
        """Test that sidedoc_pipeline.py exists."""
        pipeline_path = benchmarks_dir / "pipelines" / "sidedoc_pipeline.py"
        assert pipeline_path.exists(), "benchmarks/pipelines/sidedoc_pipeline.py does not exist"

    def test_pipeline_is_importable(self) -> None:
        """Test that SidedocPipeline can be imported."""
        from benchmarks.pipelines.sidedoc_pipeline import SidedocPipeline

        assert SidedocPipeline is not None

    def test_pipeline_inherits_from_base(self) -> None:
        """Test that SidedocPipeline inherits from BasePipeline."""
        from benchmarks.pipelines.base import BasePipeline
        from benchmarks.pipelines.sidedoc_pipeline import SidedocPipeline

        assert issubclass(SidedocPipeline, BasePipeline)

    def test_pipeline_can_be_instantiated(self) -> None:
        """Test that SidedocPipeline can be instantiated."""
        from benchmarks.pipelines.sidedoc_pipeline import SidedocPipeline

        pipeline = SidedocPipeline()
        assert pipeline is not None

    def test_extract_content_with_simple_fixture(self, simple_docx: Path) -> None:
        """Test that extract_content extracts markdown from a docx file."""
        from benchmarks.pipelines.sidedoc_pipeline import SidedocPipeline

        pipeline = SidedocPipeline()
        content = pipeline.extract_content(simple_docx)

        # Should return non-empty string with markdown content
        assert isinstance(content, str)
        assert len(content) > 0

    def test_extract_content_creates_sidedoc(self, simple_docx: Path) -> None:
        """Test that extract_content creates a sidedoc archive."""
        from benchmarks.pipelines.sidedoc_pipeline import SidedocPipeline

        pipeline = SidedocPipeline()
        pipeline.extract_content(simple_docx)

        # Check that sidedoc was created
        assert pipeline._sidedoc_path is not None
        assert pipeline._sidedoc_path.exists()

    def test_apply_edit_modifies_content(self, simple_docx: Path) -> None:
        """Test that apply_edit modifies the content string."""
        from benchmarks.pipelines.sidedoc_pipeline import SidedocPipeline

        pipeline = SidedocPipeline()
        original_content = pipeline.extract_content(simple_docx)

        # Apply a simple edit (append text)
        edit_text = "\n\nThis is an added paragraph."
        edited_content = pipeline.apply_edit(original_content, edit_text)

        assert edit_text in edited_content
        assert len(edited_content) > len(original_content)

    def test_apply_edit_updates_sidedoc_archive(self, simple_docx: Path) -> None:
        """Test that apply_edit updates the content.md in the sidedoc archive."""
        from benchmarks.pipelines.sidedoc_pipeline import SidedocPipeline

        pipeline = SidedocPipeline()
        pipeline.extract_content(simple_docx)

        # Apply an edit
        edit_text = "\n\nTest edit for verification."
        pipeline.apply_edit(pipeline._current_content, edit_text)

        # Read the sidedoc archive and verify content.md was updated
        assert pipeline._sidedoc_path is not None
        with zipfile.ZipFile(pipeline._sidedoc_path, "r") as zip_file:
            content_md = zip_file.read("content.md").decode("utf-8")
            assert edit_text in content_md

    def test_rebuild_document_creates_docx(self, simple_docx: Path) -> None:
        """Test that rebuild_document creates a new docx file."""
        from benchmarks.pipelines.sidedoc_pipeline import SidedocPipeline

        pipeline = SidedocPipeline()
        content = pipeline.extract_content(simple_docx)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.docx"

            result = pipeline.rebuild_document(content, simple_docx, output_path)

            # Check that output was created
            assert output_path.exists()
            assert result.output_path == output_path
            assert result.error is None

    def test_rebuild_document_returns_pipeline_result(self, simple_docx: Path) -> None:
        """Test that rebuild_document returns PipelineResult with metrics."""
        from benchmarks.pipelines.sidedoc_pipeline import SidedocPipeline
        from benchmarks.pipelines.base import PipelineResult

        pipeline = SidedocPipeline()
        content = pipeline.extract_content(simple_docx)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.docx"

            result = pipeline.rebuild_document(content, simple_docx, output_path)

            assert isinstance(result, PipelineResult)
            assert result.input_tokens >= 0
            assert result.output_tokens >= 0
            assert result.time_elapsed >= 0

    def test_full_pipeline_workflow(self, simple_docx: Path) -> None:
        """Test the complete extract -> edit -> rebuild workflow."""
        from benchmarks.pipelines.sidedoc_pipeline import SidedocPipeline

        pipeline = SidedocPipeline()

        # Extract
        content = pipeline.extract_content(simple_docx)
        assert len(content) > 0

        # Edit
        edited = pipeline.apply_edit(content, "\n\nNew paragraph added.")
        assert "New paragraph added" in edited

        # Rebuild
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "rebuilt.docx"
            result = pipeline.rebuild_document(edited, simple_docx, output_path)

            assert output_path.exists()
            assert result.error is None
