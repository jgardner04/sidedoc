"""Tests for docx_style application and paragraph format preservation (JON-91)."""

import json
from pathlib import Path

from docx import Document
from docx.shared import Pt, Inches
from click.testing import CliRunner

from sidedoc.cli import main
from sidedoc.extract import extract_blocks, extract_styles


class TestDocxStyleApplication:
    """Test that docx_style is applied to paragraphs during reconstruction."""

    def test_roundtrip_preserves_paragraph_style(self):
        """Rebuilt document should preserve paragraph styles, not fallback to Normal."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            doc = Document()
            doc.add_paragraph("A quote paragraph", style="Quote")
            doc.add_paragraph("Normal paragraph")
            doc.add_paragraph("Title text", style="Title")
            doc.save("original.docx")

            runner.invoke(main, ["extract", "original.docx"])
            result = runner.invoke(main, ["build", "original.sidedoc", "-o", "rebuilt.docx"])
            assert result.exit_code == 0

            rebuilt = Document("rebuilt.docx")
            style_names = [p.style.name for p in rebuilt.paragraphs]
            assert "Quote" in style_names
            assert "Title" in style_names

    def test_roundtrip_preserves_list_bullet_style(self):
        """List Bullet style should survive round-trip."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            doc = Document()
            doc.add_paragraph("Bullet item", style="List Bullet")
            doc.save("original.docx")

            runner.invoke(main, ["extract", "original.docx"])
            result = runner.invoke(main, ["build", "original.sidedoc", "-o", "rebuilt.docx"])
            assert result.exit_code == 0

            rebuilt = Document("rebuilt.docx")
            # Find the paragraph with the bullet content
            bullet_paras = [p for p in rebuilt.paragraphs if "Bullet item" in p.text]
            assert len(bullet_paras) > 0
            assert bullet_paras[0].style.name == "List Bullet"

    def test_roundtrip_preserves_heading_styles(self):
        """Heading styles should be applied (not just Normal)."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            doc = Document()
            doc.add_paragraph("Chapter One", style="Heading 1")
            doc.add_paragraph("Section A", style="Heading 2")
            doc.add_paragraph("Body text")
            doc.save("original.docx")

            runner.invoke(main, ["extract", "original.docx"])
            result = runner.invoke(main, ["build", "original.sidedoc", "-o", "rebuilt.docx"])
            assert result.exit_code == 0

            rebuilt = Document("rebuilt.docx")
            texts_and_styles = {p.text: p.style.name for p in rebuilt.paragraphs}
            assert texts_and_styles.get("Chapter One") == "Heading 1"
            assert texts_and_styles.get("Section A") == "Heading 2"

    def test_missing_custom_style_falls_back_to_normal(self):
        """When a custom style doesn't exist in the target document, fall back to Normal."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create a document with a custom style
            doc = Document()
            doc.styles.add_style("Legal Citation", 1)  # WD_STYLE_TYPE.PARAGRAPH = 1
            doc.add_paragraph("Case law reference", style="Legal Citation")
            doc.save("original.docx")

            runner.invoke(main, ["extract", "original.docx"])

            # Build should succeed even though the rebuilt doc won't have the custom style
            result = runner.invoke(main, ["build", "original.sidedoc", "-o", "rebuilt.docx"])
            assert result.exit_code == 0

            # Verify the paragraph exists (with Normal fallback)
            rebuilt = Document("rebuilt.docx")
            texts = [p.text for p in rebuilt.paragraphs]
            assert "Case law reference" in texts


class TestParagraphFormatExtraction:
    """Test that paragraph format properties are extracted."""

    def _extract(self, tmp_path, doc):
        """Helper: save doc, extract blocks+styles, return styles list."""
        docx_path = str(tmp_path / "test.docx")
        doc.save(docx_path)
        blocks, _ = extract_blocks(docx_path)
        styles = extract_styles(docx_path, blocks)
        return styles

    def test_extract_left_indent(self, tmp_path):
        """Left indent should be extracted from paragraph format."""
        doc = Document()
        para = doc.add_paragraph("Indented text")
        para.paragraph_format.left_indent = Inches(0.5)

        styles = self._extract(tmp_path, doc)
        para_styles = [s for s in styles if s.docx_style != "Table"]
        assert len(para_styles) > 0
        assert para_styles[0].left_indent is not None
        assert para_styles[0].left_indent > 0

    def test_extract_spacing(self, tmp_path):
        """Space before and after should be extracted from paragraph format."""
        doc = Document()
        para = doc.add_paragraph("Spaced text")
        para.paragraph_format.space_before = Pt(12)
        para.paragraph_format.space_after = Pt(6)

        styles = self._extract(tmp_path, doc)
        para_styles = [s for s in styles if s.docx_style != "Table"]
        assert len(para_styles) > 0
        assert para_styles[0].space_before is not None
        assert para_styles[0].space_after is not None

    def test_extract_keep_together(self, tmp_path):
        """keep_together should be extracted from paragraph format."""
        doc = Document()
        para = doc.add_paragraph("Keep together text")
        para.paragraph_format.keep_together = True

        styles = self._extract(tmp_path, doc)
        para_styles = [s for s in styles if s.docx_style != "Table"]
        assert len(para_styles) > 0
        assert para_styles[0].keep_together is True

    def test_extract_page_break_before(self, tmp_path):
        """page_break_before should be extracted from paragraph format."""
        doc = Document()
        para = doc.add_paragraph("Page break text")
        para.paragraph_format.page_break_before = True

        styles = self._extract(tmp_path, doc)
        para_styles = [s for s in styles if s.docx_style != "Table"]
        assert len(para_styles) > 0
        assert para_styles[0].page_break_before is True


class TestParagraphFormatRoundtrip:
    """Test that paragraph format properties survive round-trip."""

    def test_roundtrip_preserves_indentation(self):
        """Left indent should survive extract → build round-trip."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            doc = Document()
            para = doc.add_paragraph("Indented text")
            para.paragraph_format.left_indent = Inches(0.5)
            doc.save("original.docx")

            runner.invoke(main, ["extract", "original.docx"])
            result = runner.invoke(main, ["build", "original.sidedoc", "-o", "rebuilt.docx"])
            assert result.exit_code == 0

            rebuilt = Document("rebuilt.docx")
            indented = [p for p in rebuilt.paragraphs if "Indented" in p.text]
            assert len(indented) > 0
            assert indented[0].paragraph_format.left_indent is not None
            assert indented[0].paragraph_format.left_indent == Inches(0.5)

    def test_roundtrip_preserves_spacing(self):
        """Space before/after should survive extract → build round-trip."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            doc = Document()
            para = doc.add_paragraph("Spaced text")
            para.paragraph_format.space_before = Pt(12)
            para.paragraph_format.space_after = Pt(6)
            doc.save("original.docx")

            runner.invoke(main, ["extract", "original.docx"])
            result = runner.invoke(main, ["build", "original.sidedoc", "-o", "rebuilt.docx"])
            assert result.exit_code == 0

            rebuilt = Document("rebuilt.docx")
            spaced = [p for p in rebuilt.paragraphs if "Spaced" in p.text]
            assert len(spaced) > 0
            assert spaced[0].paragraph_format.space_before == Pt(12)
            assert spaced[0].paragraph_format.space_after == Pt(6)

    def test_roundtrip_preserves_keep_with_next(self):
        """keep_with_next should survive extract → build round-trip."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            doc = Document()
            para = doc.add_paragraph("Keep with next text")
            para.paragraph_format.keep_with_next = True
            doc.add_paragraph("Following text")
            doc.save("original.docx")

            runner.invoke(main, ["extract", "original.docx"])
            result = runner.invoke(main, ["build", "original.sidedoc", "-o", "rebuilt.docx"])
            assert result.exit_code == 0

            rebuilt = Document("rebuilt.docx")
            kept = [p for p in rebuilt.paragraphs if "Keep with next" in p.text]
            assert len(kept) > 0
            assert kept[0].paragraph_format.keep_with_next is True

    def test_roundtrip_preserves_first_line_indent(self):
        """First line indent should survive extract → build round-trip."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            doc = Document()
            para = doc.add_paragraph("First line indented text")
            para.paragraph_format.first_line_indent = Inches(0.25)
            doc.save("original.docx")

            runner.invoke(main, ["extract", "original.docx"])
            result = runner.invoke(main, ["build", "original.sidedoc", "-o", "rebuilt.docx"])
            assert result.exit_code == 0

            rebuilt = Document("rebuilt.docx")
            indented = [p for p in rebuilt.paragraphs if "First line" in p.text]
            assert len(indented) > 0
            assert indented[0].paragraph_format.first_line_indent == Inches(0.25)


class TestStyleWithDirectFormatting:
    """Test that direct formatting overrides style defaults."""

    def test_direct_formatting_overrides_style(self):
        """Direct formatting on a paragraph should override style defaults after round-trip."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            doc = Document()
            para = doc.add_paragraph("Custom spaced heading", style="Heading 1")
            para.paragraph_format.space_before = Pt(24)
            doc.save("original.docx")

            runner.invoke(main, ["extract", "original.docx"])
            result = runner.invoke(main, ["build", "original.sidedoc", "-o", "rebuilt.docx"])
            assert result.exit_code == 0

            rebuilt = Document("rebuilt.docx")
            heading = [p for p in rebuilt.paragraphs if "Custom spaced" in p.text]
            assert len(heading) > 0
            assert heading[0].style.name == "Heading 1"
            assert heading[0].paragraph_format.space_before == Pt(24)
