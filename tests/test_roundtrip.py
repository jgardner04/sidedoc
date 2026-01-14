"""Test roundtrip: extract → build produces correct output."""

import tempfile
from pathlib import Path
from click.testing import CliRunner
from docx import Document
from sidedoc.cli import main


def test_roundtrip_preserves_headings():
    """Test that extract → build preserves heading styles."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create original docx
        doc = Document()
        doc.add_paragraph("Main Title", style="Heading 1")
        doc.add_paragraph("Introduction text")
        doc.add_paragraph("Section Title", style="Heading 2")
        doc.add_paragraph("Section content")

        docx_path = "original.docx"
        doc.save(docx_path)

        # Extract
        result = runner.invoke(main, ["extract", docx_path])
        assert result.exit_code == 0

        # Build
        result = runner.invoke(main, ["build", "original.sidedoc", "-o", "rebuilt.docx"])
        assert result.exit_code == 0

        # Verify rebuilt document
        rebuilt = Document("rebuilt.docx")
        assert len(rebuilt.paragraphs) >= 4

        # Check text content is preserved
        texts = [p.text for p in rebuilt.paragraphs]
        assert "Main Title" in texts
        assert "Introduction text" in texts
        assert "Section Title" in texts
        assert "Section content" in texts


def test_roundtrip_simple_document():
    """Test roundtrip with a simple document."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create simple docx
        doc = Document()
        doc.add_paragraph("Hello world")
        doc.add_paragraph("Second paragraph")

        doc.save("test.docx")

        # Extract and build
        runner.invoke(main, ["extract", "test.docx"])
        result = runner.invoke(main, ["build", "test.sidedoc", "-o", "rebuilt.docx"])

        assert result.exit_code == 0

        # Verify content
        rebuilt = Document("rebuilt.docx")
        texts = [p.text for p in rebuilt.paragraphs]
        assert "Hello world" in texts
        assert "Second paragraph" in texts


def test_roundtrip_multiple_heading_levels():
    """Test roundtrip with multiple heading levels."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create docx with various heading levels
        doc = Document()
        doc.add_paragraph("H1", style="Heading 1")
        doc.add_paragraph("H2", style="Heading 2")
        doc.add_paragraph("H3", style="Heading 3")

        doc.save("test.docx")

        # Extract and build
        runner.invoke(main, ["extract", "test.docx"])
        result = runner.invoke(main, ["build", "test.sidedoc"])

        assert result.exit_code == 0

        # Verify headings preserved
        rebuilt = Document("test.docx")
        texts = [p.text for p in rebuilt.paragraphs]
        assert "H1" in texts
        assert "H2" in texts
        assert "H3" in texts


def test_complete_workflow():
    """Test complete workflow: extract → unpack → pack → build."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create original
        doc = Document()
        doc.add_paragraph("Test Document", style="Heading 1")
        doc.add_paragraph("This is a test")
        doc.save("original.docx")

        # Extract
        result = runner.invoke(main, ["extract", "original.docx"])
        assert result.exit_code == 0

        # Unpack
        result = runner.invoke(main, ["unpack", "original.sidedoc", "-o", "unpacked"])
        assert result.exit_code == 0

        # Verify unpacked files
        assert Path("unpacked/content.md").exists()
        assert Path("unpacked/manifest.json").exists()

        # Pack back
        result = runner.invoke(main, ["pack", "unpacked", "-o", "repacked.sidedoc"])
        assert result.exit_code == 0

        # Build from repacked
        result = runner.invoke(main, ["build", "repacked.sidedoc", "-o", "final.docx"])
        assert result.exit_code == 0

        # Verify final document
        final = Document("final.docx")
        texts = [p.text for p in final.paragraphs]
        assert "Test Document" in texts
        assert "This is a test" in texts
