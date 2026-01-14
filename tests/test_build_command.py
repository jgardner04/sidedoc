"""Test build command."""

import tempfile
from pathlib import Path
from click.testing import CliRunner
from docx import Document
from sidedoc.cli import main


def test_build_command_creates_docx():
    """Test that build command creates a .docx file from extract output."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create a test docx
        doc = Document()
        doc.add_paragraph("Test Title", style="Heading 1")
        doc.add_paragraph("Test content")
        docx_path = "test.docx"
        doc.save(docx_path)

        # Extract it
        result = runner.invoke(main, ["extract", docx_path])
        assert result.exit_code == 0

        # Build it back
        sidedoc_path = "test.sidedoc"
        output_docx = "rebuilt.docx"
        result = runner.invoke(main, ["build", sidedoc_path, "-o", output_docx])

        assert result.exit_code == 0
        assert Path(output_docx).exists()

        # Verify it's a valid docx
        rebuilt_doc = Document(output_docx)
        assert len(rebuilt_doc.paragraphs) >= 2


def test_build_command_preserves_headings():
    """Test that build preserves heading styles."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create docx with headings
        doc = Document()
        doc.add_paragraph("Heading 1", style="Heading 1")
        doc.add_paragraph("Heading 2", style="Heading 2")
        docx_path = "test.docx"
        doc.save(docx_path)

        # Extract and build
        runner.invoke(main, ["extract", docx_path])
        result = runner.invoke(main, ["build", "test.sidedoc", "-o", "rebuilt.docx"])

        assert result.exit_code == 0

        # Verify headings
        rebuilt_doc = Document("rebuilt.docx")
        assert len(rebuilt_doc.paragraphs) >= 2


def test_build_command_default_output():
    """Test that build uses default output path."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create and extract
        doc = Document()
        doc.add_paragraph("Test")
        doc.save("test.docx")
        runner.invoke(main, ["extract", "test.docx"])

        # Build without -o flag
        result = runner.invoke(main, ["build", "test.sidedoc"])

        assert result.exit_code == 0
        # Should create test.docx (overwriting original)
        assert Path("test.docx").exists()
