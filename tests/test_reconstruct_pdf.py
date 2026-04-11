"""Test PDF reconstruction from sidedoc format.

All tests require weasyprint and are gated behind the 'pdf' marker.
"""

import json
from pathlib import Path

import pytest

try:
    import weasyprint  # noqa: F401
    HAS_WEASYPRINT = True
except ImportError:
    HAS_WEASYPRINT = False

try:
    import docling  # noqa: F401
    HAS_DOCLING = True
except ImportError:
    HAS_DOCLING = False

try:
    import fitz
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

pytestmark = pytest.mark.pdf

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.mark.skipif(
    not (HAS_WEASYPRINT and HAS_DOCLING),
    reason="weasyprint and docling required",
)
class TestReconstructPdf:
    """Test building PDF from sidedoc directory (no PyMuPDF needed)."""

    def test_build_pdf_from_sidedoc(self, tmp_path):
        """Extract PDF to sidedoc, then build back to PDF."""
        from sidedoc.extract_pdf import extract_pdf_document, extract_pdf_styles
        from sidedoc.extract import blocks_to_markdown
        from sidedoc.package import create_sidedoc_directory
        from sidedoc.reconstruct_pdf import build_pdf_from_sidedoc

        # Extract
        blocks, image_data, sections = extract_pdf_document(
            str(FIXTURES_DIR / "simple.pdf")
        )
        styles = extract_pdf_styles(str(FIXTURES_DIR / "simple.pdf"), blocks)
        content_md = blocks_to_markdown(blocks)

        sidedoc_dir = str(tmp_path / "simple.sidedoc")
        create_sidedoc_directory(
            sidedoc_dir, content_md, blocks, styles,
            str(FIXTURES_DIR / "simple.pdf"),
            image_data=image_data, sections=sections,
            source_format="pdf",
        )

        # Build PDF
        output_pdf = str(tmp_path / "rebuilt.pdf")
        build_pdf_from_sidedoc(sidedoc_dir, output_pdf)

        assert Path(output_pdf).exists(), "Output PDF not created"
        assert Path(output_pdf).stat().st_size > 100, "Output PDF seems too small"

    def test_build_command_auto_detects_pdf(self, tmp_path):
        """sidedoc build should auto-detect PDF source and output .pdf."""
        from click.testing import CliRunner
        from sidedoc.cli import main

        # First extract
        sidedoc_dir = str(tmp_path / "simple.sidedoc")
        runner = CliRunner()
        result = runner.invoke(
            main, ["extract", str(FIXTURES_DIR / "simple.pdf"), "-o", sidedoc_dir]
        )
        assert result.exit_code == 0, f"Extract failed: {result.output}"

        # Then build — should auto-detect PDF and output .pdf
        result = runner.invoke(main, ["build", sidedoc_dir])
        assert result.exit_code == 0, f"Build failed: {result.output}"

        output_pdf = tmp_path / "simple.pdf"
        assert output_pdf.exists(), "Should have created simple.pdf"

    def test_pdf_roundtrip_e2e(self, tmp_path):
        """Full round-trip: PDF → sidedoc → PDF."""
        from sidedoc.extract_pdf import extract_pdf_document, extract_pdf_styles
        from sidedoc.extract import blocks_to_markdown
        from sidedoc.package import create_sidedoc_directory
        from sidedoc.reconstruct_pdf import build_pdf_from_sidedoc

        source = str(FIXTURES_DIR / "mixed.pdf")
        sidedoc_dir = str(tmp_path / "mixed.sidedoc")
        output_pdf = str(tmp_path / "mixed_rebuilt.pdf")

        # Extract
        blocks, image_data, sections = extract_pdf_document(source)
        styles = extract_pdf_styles(source, blocks)
        content_md = blocks_to_markdown(blocks)
        create_sidedoc_directory(
            sidedoc_dir, content_md, blocks, styles, source,
            image_data=image_data, sections=sections,
            source_format="pdf",
        )

        # Build
        build_pdf_from_sidedoc(sidedoc_dir, output_pdf)

        assert Path(output_pdf).exists()
        assert Path(output_pdf).stat().st_size > 100


@pytest.mark.skipif(
    not (HAS_WEASYPRINT and HAS_DOCLING and HAS_PYMUPDF),
    reason="weasyprint, docling, and pymupdf required",
)
class TestReconstructPdfContent:
    """Tests that verify rebuilt PDF content using PyMuPDF."""

    def test_build_pdf_contains_text(self, tmp_path):
        """Rebuilt PDF should contain the original text content."""
        from sidedoc.extract_pdf import extract_pdf_document, extract_pdf_styles
        from sidedoc.extract import blocks_to_markdown
        from sidedoc.package import create_sidedoc_directory
        from sidedoc.reconstruct_pdf import build_pdf_from_sidedoc

        blocks, image_data, sections = extract_pdf_document(
            str(FIXTURES_DIR / "simple.pdf")
        )
        styles = extract_pdf_styles(str(FIXTURES_DIR / "simple.pdf"), blocks)
        content_md = blocks_to_markdown(blocks)

        sidedoc_dir = str(tmp_path / "simple.sidedoc")
        create_sidedoc_directory(
            sidedoc_dir, content_md, blocks, styles,
            str(FIXTURES_DIR / "simple.pdf"),
            image_data=image_data, sections=sections,
            source_format="pdf",
        )

        output_pdf = str(tmp_path / "rebuilt.pdf")
        build_pdf_from_sidedoc(sidedoc_dir, output_pdf)

        # Verify the rebuilt PDF contains expected text
        doc = fitz.open(output_pdf)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()

        assert "Sidedoc" in text, f"Expected 'Sidedoc' in rebuilt PDF, got: {text[:200]}"
        assert "AI-native" in text or "document format" in text, (
            f"Expected content from original in rebuilt PDF"
        )

    def test_build_pdf_with_table(self, tmp_path):
        """Rebuilt PDF from tables.pdf should contain table content."""
        from sidedoc.extract_pdf import extract_pdf_document, extract_pdf_styles
        from sidedoc.extract import blocks_to_markdown
        from sidedoc.package import create_sidedoc_directory
        from sidedoc.reconstruct_pdf import build_pdf_from_sidedoc

        blocks, image_data, sections = extract_pdf_document(
            str(FIXTURES_DIR / "tables.pdf")
        )
        styles = extract_pdf_styles(str(FIXTURES_DIR / "tables.pdf"), blocks)
        content_md = blocks_to_markdown(blocks)

        sidedoc_dir = str(tmp_path / "tables.sidedoc")
        create_sidedoc_directory(
            sidedoc_dir, content_md, blocks, styles,
            str(FIXTURES_DIR / "tables.pdf"),
            image_data=image_data, sections=sections,
            source_format="pdf",
        )

        output_pdf = str(tmp_path / "rebuilt.pdf")
        build_pdf_from_sidedoc(sidedoc_dir, output_pdf)

        doc = fitz.open(output_pdf)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()

        assert "Alice Smith" in text, "Table data should be in rebuilt PDF"
        assert "Engineer" in text, "Table data should be in rebuilt PDF"
