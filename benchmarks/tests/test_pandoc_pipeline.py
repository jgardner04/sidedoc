"""Tests for Pandoc pipeline implementation (US-007)."""

from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile

import pytest


BENCHMARKS_DIR = Path(__file__).parent.parent
FIXTURES_DIR = BENCHMARKS_DIR.parent / "tests" / "fixtures"


class TestPandocPipeline:
    """Test that the Pandoc pipeline works correctly."""

    def test_pipeline_module_exists(self) -> None:
        """Test that pandoc_pipeline.py exists."""
        pipeline_path = BENCHMARKS_DIR / "pipelines" / "pandoc_pipeline.py"
        assert pipeline_path.exists(), "benchmarks/pipelines/pandoc_pipeline.py does not exist"

    def test_pipeline_is_importable(self) -> None:
        """Test that PandocPipeline can be imported."""
        from benchmarks.pipelines.pandoc_pipeline import PandocPipeline

        assert PandocPipeline is not None

    def test_pipeline_inherits_from_base(self) -> None:
        """Test that PandocPipeline inherits from BasePipeline."""
        from benchmarks.pipelines.base import BasePipeline
        from benchmarks.pipelines.pandoc_pipeline import PandocPipeline

        assert issubclass(PandocPipeline, BasePipeline)

    def test_check_pandoc_returns_true_when_installed(self) -> None:
        """Test that check_pandoc returns True when Pandoc is available."""
        from benchmarks.pipelines.pandoc_pipeline import check_pandoc

        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/usr/local/bin/pandoc"
            result = check_pandoc()
            assert result is True

    def test_check_pandoc_raises_when_not_installed(self) -> None:
        """Test that check_pandoc raises helpful error when not installed."""
        from benchmarks.pipelines.pandoc_pipeline import check_pandoc, PandocNotFoundError

        with patch("shutil.which") as mock_which:
            mock_which.return_value = None
            with pytest.raises(PandocNotFoundError) as exc_info:
                check_pandoc()

            # Error message should be helpful
            assert "pandoc" in str(exc_info.value).lower()

    def test_extract_content_uses_pypandoc(self) -> None:
        """Test that extract_content uses pypandoc for conversion."""
        from benchmarks.pipelines.pandoc_pipeline import PandocPipeline

        pipeline = PandocPipeline()

        with patch("benchmarks.pipelines.pandoc_pipeline.pypandoc") as mock_pypandoc:
            mock_pypandoc.convert_file.return_value = "# Test Markdown\n\nParagraph text."

            with patch("benchmarks.pipelines.pandoc_pipeline.check_pandoc"):
                result = pipeline.extract_content(Path("/fake/doc.docx"))

            mock_pypandoc.convert_file.assert_called_once()
            assert "Test Markdown" in result

    def test_apply_edit_modifies_content(self) -> None:
        """Test that apply_edit modifies the markdown string."""
        from benchmarks.pipelines.pandoc_pipeline import PandocPipeline

        pipeline = PandocPipeline()
        original = "# Heading\n\nParagraph."
        edit = "\n\nNew paragraph."

        result = pipeline.apply_edit(original, edit)

        assert "New paragraph" in result
        assert len(result) > len(original)

    def test_rebuild_document_uses_pypandoc(self) -> None:
        """Test that rebuild_document uses pypandoc to create docx."""
        from benchmarks.pipelines.pandoc_pipeline import PandocPipeline
        from benchmarks.pipelines.base import PipelineResult

        pipeline = PandocPipeline()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.docx"

            with patch("benchmarks.pipelines.pandoc_pipeline.pypandoc") as mock_pypandoc:
                mock_pypandoc.convert_text.return_value = None
                # Simulate file creation
                output_path.write_bytes(b"fake docx")

                with patch("benchmarks.pipelines.pandoc_pipeline.check_pandoc"):
                    result = pipeline.rebuild_document(
                        "# Test", Path("/fake/original.docx"), output_path
                    )

            assert isinstance(result, PipelineResult)
            mock_pypandoc.convert_text.assert_called_once()

    def test_extract_content_with_real_fixture(self) -> None:
        """Test extract_content with a real docx file (if pandoc is installed)."""
        from benchmarks.pipelines.pandoc_pipeline import PandocPipeline, PandocNotFoundError

        pipeline = PandocPipeline()
        simple_docx = FIXTURES_DIR / "simple.docx"

        if not simple_docx.exists():
            pytest.skip("simple.docx fixture not found")

        try:
            content = pipeline.extract_content(simple_docx)
            assert isinstance(content, str)
            assert len(content) > 0
        except PandocNotFoundError:
            pytest.skip("Pandoc not installed")

    def test_full_pipeline_workflow_mocked(self) -> None:
        """Test the complete extract -> edit -> rebuild workflow with mocks."""
        from benchmarks.pipelines.pandoc_pipeline import PandocPipeline

        pipeline = PandocPipeline()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.docx"

            with patch("benchmarks.pipelines.pandoc_pipeline.pypandoc") as mock_pypandoc:
                mock_pypandoc.convert_file.return_value = "# Original\n\nParagraph."
                mock_pypandoc.convert_text.return_value = None

                with patch("benchmarks.pipelines.pandoc_pipeline.check_pandoc"):
                    # Extract
                    content = pipeline.extract_content(Path("/fake/doc.docx"))
                    assert len(content) > 0

                    # Edit
                    edited = pipeline.apply_edit(content, "\n\nAdded text.")
                    assert "Added text" in edited

                    # Rebuild (create fake output)
                    output_path.write_bytes(b"fake docx")
                    result = pipeline.rebuild_document(edited, Path("/fake/doc.docx"), output_path)
                    assert result.error is None
