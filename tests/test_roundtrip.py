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
    """Test complete workflow: extract → build from directory, and extract --pack → unpack → pack → build."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create original
        doc = Document()
        doc.add_paragraph("Test Document", style="Heading 1")
        doc.add_paragraph("This is a test")
        doc.save("original.docx")

        # Extract to directory
        result = runner.invoke(main, ["extract", "original.docx"])
        assert result.exit_code == 0
        assert Path("original.sidedoc").is_dir()
        assert Path("original.sidedoc/content.md").exists()

        # Build from directory
        result = runner.invoke(main, ["build", "original.sidedoc", "-o", "from_dir.docx"])
        assert result.exit_code == 0

        # Verify document from directory
        from_dir = Document("from_dir.docx")
        texts = [p.text for p in from_dir.paragraphs]
        assert "Test Document" in texts
        assert "This is a test" in texts

        # Also test ZIP distribution workflow: pack → unpack → build
        result = runner.invoke(main, ["pack", "original.sidedoc", "-o", "distributed.sdoc"])
        assert result.exit_code == 0

        result = runner.invoke(main, ["unpack", "distributed.sdoc", "-o", "unpacked.sidedoc"])
        assert result.exit_code == 0
        assert Path("unpacked.sidedoc/content.md").exists()

        result = runner.invoke(main, ["build", "unpacked.sidedoc", "-o", "final.docx"])
        assert result.exit_code == 0

        final = Document("final.docx")
        texts = [p.text for p in final.paragraphs]
        assert "Test Document" in texts
        assert "This is a test" in texts


def _count_runs_by_format(doc):
    """Helper: tally bold/italic/underline runs across all paragraphs."""
    bold = italic = underline = 0
    asterisks = 0
    for p in doc.paragraphs:
        for r in p.runs:
            if r.bold:
                bold += 1
            if r.italic:
                italic += 1
            if r.underline:
                underline += 1
            asterisks += r.text.count("*")
    return bold, italic, underline, asterisks


def test_roundtrip_paragraph_preserves_bold_italic():
    """Issue #72: bold/italic in plain paragraphs were rebuilt as literal **/* text.

    The paragraph emission path (reconstruct.py) was calling add_paragraph(content)
    directly, never parsing markdown emphasis into runs.
    """
    runner = CliRunner()
    with runner.isolated_filesystem():
        doc = Document()
        p = doc.add_paragraph()
        p.add_run("Plain ")
        r = p.add_run("bold"); r.bold = True
        p.add_run(" and ")
        r = p.add_run("italic"); r.italic = True
        p.add_run(".")
        doc.save("src.docx")

        assert runner.invoke(main, ["extract", "src.docx"]).exit_code == 0
        assert runner.invoke(main, ["build", "src.sidedoc", "-o", "rebuilt.docx"]).exit_code == 0

        rebuilt = Document("rebuilt.docx")
        bold, italic, _, asterisks = _count_runs_by_format(rebuilt)
        assert bold >= 1, "bold run lost on rebuild"
        assert italic >= 1, "italic run lost on rebuild"
        assert asterisks == 0, "literal * leaked into rebuilt docx"


def test_roundtrip_heading_preserves_bold():
    """Bold inside a heading must survive rebuild as a bold run, not literal **."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        doc = Document()
        h = doc.add_paragraph(style="Heading 1")
        h.add_run("Intro ")
        r = h.add_run("Title"); r.bold = True
        doc.save("src.docx")

        assert runner.invoke(main, ["extract", "src.docx"]).exit_code == 0
        assert runner.invoke(main, ["build", "src.sidedoc", "-o", "rebuilt.docx"]).exit_code == 0

        rebuilt = Document("rebuilt.docx")
        bold, _, _, asterisks = _count_runs_by_format(rebuilt)
        assert bold >= 1
        assert asterisks == 0


def test_roundtrip_bold_with_trailing_space():
    """The exact reporter symptom: bold run 'СОДЕРЖАНИЕ ' must rebuild as bold."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        doc = Document()
        p = doc.add_paragraph()
        r = p.add_run("СОДЕРЖАНИЕ "); r.bold = True
        p.add_run("body")
        doc.save("src.docx")

        assert runner.invoke(main, ["extract", "src.docx"]).exit_code == 0
        assert runner.invoke(main, ["build", "src.sidedoc", "-o", "rebuilt.docx"]).exit_code == 0

        rebuilt = Document("rebuilt.docx")
        bold, _, _, asterisks = _count_runs_by_format(rebuilt)
        assert bold >= 1
        assert asterisks == 0
        # The Russian word survives intact.
        assert any("СОДЕРЖАНИЕ" in p.text for p in rebuilt.paragraphs)
