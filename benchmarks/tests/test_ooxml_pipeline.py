"""Tests for OOXML pipeline implementation."""

from pathlib import Path
import tempfile
import zipfile

import pytest


class TestOoxmlPipeline:
    """Test that the OOXML pipeline works correctly."""

    def test_pipeline_module_exists(self, benchmarks_dir: Path) -> None:
        """Test that ooxml_pipeline.py exists."""
        pipeline_path = benchmarks_dir / "pipelines" / "ooxml_pipeline.py"
        assert pipeline_path.exists(), "benchmarks/pipelines/ooxml_pipeline.py does not exist"

    def test_pipeline_is_importable(self) -> None:
        """Test that OoxmlPipeline can be imported."""
        from benchmarks.pipelines.ooxml_pipeline import OoxmlPipeline

        assert OoxmlPipeline is not None

    def test_pipeline_inherits_from_base(self) -> None:
        """Test that OoxmlPipeline inherits from BasePipeline."""
        from benchmarks.pipelines.base import BasePipeline
        from benchmarks.pipelines.ooxml_pipeline import OoxmlPipeline

        assert issubclass(OoxmlPipeline, BasePipeline)

    def test_pipeline_can_be_instantiated(self) -> None:
        """Test that OoxmlPipeline can be instantiated."""
        from benchmarks.pipelines.ooxml_pipeline import OoxmlPipeline

        pipeline = OoxmlPipeline()
        assert pipeline is not None

    def test_extract_content_returns_xml_with_comments(self, simple_docx: Path) -> None:
        """Test that extract_content returns XML with comment markers."""
        from benchmarks.pipelines.ooxml_pipeline import OoxmlPipeline

        pipeline = OoxmlPipeline()
        content = pipeline.extract_content(simple_docx)

        assert isinstance(content, str)
        assert len(content) > 0
        # OOXML content should contain XML comment markers for file names
        assert "<!-- [Content_Types].xml -->" in content

    def test_extract_content_contains_document_xml(self, simple_docx: Path) -> None:
        """Test that extract_content includes document.xml content."""
        from benchmarks.pipelines.ooxml_pipeline import OoxmlPipeline

        pipeline = OoxmlPipeline()
        content = pipeline.extract_content(simple_docx)

        # Should contain the main document XML
        assert "<!-- word/document.xml -->" in content

    def test_apply_edit_is_noop(self) -> None:
        """Test that apply_edit is a no-op (returns content unchanged)."""
        from benchmarks.pipelines.ooxml_pipeline import OoxmlPipeline

        pipeline = OoxmlPipeline()
        original = "Original XML content."
        edit = "Some edit instruction."

        result = pipeline.apply_edit(original, edit)

        assert result == original

    def test_rebuild_document_returns_none_output_path(self) -> None:
        """Test that rebuild_document returns PipelineResult with None output_path."""
        from benchmarks.pipelines.ooxml_pipeline import OoxmlPipeline
        from benchmarks.pipelines.base import PipelineResult

        pipeline = OoxmlPipeline()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.docx"

            result = pipeline.rebuild_document(
                "content", Path("/fake/original.docx"), output_path
            )

            assert isinstance(result, PipelineResult)
            assert result.output_path is None
            assert result.error is not None

    def test_full_pipeline_workflow(self, simple_docx: Path) -> None:
        """Test the complete workflow (extract only, since edit/rebuild are no-ops)."""
        from benchmarks.pipelines.ooxml_pipeline import OoxmlPipeline

        pipeline = OoxmlPipeline()

        # Extract
        content = pipeline.extract_content(simple_docx)
        assert len(content) > 0
        assert "<!--" in content  # XML comments present

        # Apply edit (should be no-op)
        edited = pipeline.apply_edit(content, "edit instruction")
        assert edited == content

        # Rebuild (should return None output)
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.docx"
            result = pipeline.rebuild_document(content, simple_docx, output_path)
            assert result.output_path is None
            assert result.error is not None

    def test_extract_skips_path_traversal_members(self) -> None:
        """Test that extract_content skips zip members with path traversal."""
        from benchmarks.pipelines.ooxml_pipeline import OoxmlPipeline

        pipeline = OoxmlPipeline()

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a zip with a path-traversal member and a safe member
            zip_path = Path(tmpdir) / "malicious.docx"
            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("../../malicious.xml", "<evil/>")
                zf.writestr("word/document.xml", "<doc>safe</doc>")

            content = pipeline.extract_content(zip_path)

            assert "malicious" not in content
            assert "<!-- word/document.xml -->" in content
            assert "<doc>safe</doc>" in content

    def test_extract_skips_absolute_path_members(self) -> None:
        """Test that extract_content skips zip members with absolute paths."""
        from benchmarks.pipelines.ooxml_pipeline import OoxmlPipeline

        pipeline = OoxmlPipeline()

        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "absolute.docx"
            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("/etc/passwd.xml", "<evil/>")
                zf.writestr("word/document.xml", "<doc>safe</doc>")

            content = pipeline.extract_content(zip_path)

            assert "passwd" not in content
            assert "<doc>safe</doc>" in content

    def test_extract_sanitizes_comment_injection(self) -> None:
        """Test that member names with --> are sanitized in HTML comments."""
        from benchmarks.pipelines.ooxml_pipeline import OoxmlPipeline

        pipeline = OoxmlPipeline()

        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "injection.docx"
            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("word/evil-->.xml", "<injected/>")

            content = pipeline.extract_content(zip_path)

            # Every comment-header line should contain exactly one --> (closing delimiter)
            lines = content.split("\n")
            comment_lines = [l for l in lines if l.startswith("<!-- ")]
            assert comment_lines, "Expected at least one comment line"
            for cl in comment_lines:
                assert cl.count("-->") == 1, f"Injected --> in comment: {cl}"

    def test_extract_skips_backslash_path_traversal(self) -> None:
        """Test that backslash-style path traversal is rejected."""
        from benchmarks.pipelines.ooxml_pipeline import OoxmlPipeline

        pipeline = OoxmlPipeline()

        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "backslash.docx"
            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("..\\..\\malicious.xml", "<evil/>")
                zf.writestr("word/document.xml", "<doc>safe</doc>")

            content = pipeline.extract_content(zip_path)

            assert "malicious" not in content
            assert "<doc>safe</doc>" in content
