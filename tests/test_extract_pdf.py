"""Test PDF document extraction functionality.

All tests require docling and are gated behind the 'pdf' marker.
Run with: pytest tests/test_extract_pdf.py -m pdf
Skip with: pytest -m 'not pdf'
"""

import json
import hashlib
from pathlib import Path

import pytest

try:
    import docling  # noqa: F401
    HAS_DOCLING = True
except ImportError:
    HAS_DOCLING = False

pytestmark = [
    pytest.mark.pdf,
    pytest.mark.skipif(not HAS_DOCLING, reason="docling not installed"),
]

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestExtractPdfSimple:
    """Test basic PDF extraction with simple.pdf."""

    def test_extract_pdf_simple_produces_blocks(self):
        """Extract simple.pdf and verify it returns blocks with expected types."""
        from sidedoc.extract_pdf import extract_pdf_document

        blocks, image_data, sections = extract_pdf_document(
            str(FIXTURES_DIR / "simple.pdf")
        )

        assert len(blocks) >= 2, "Should extract at least a heading and a paragraph"

        types = [b.type for b in blocks]
        assert "heading" in types, "Should detect at least one heading"
        assert "paragraph" in types, "Should detect at least one paragraph"

    def test_extract_pdf_blocks_have_valid_ids(self):
        """Each block should have a unique ID."""
        from sidedoc.extract_pdf import extract_pdf_document

        blocks, _, _ = extract_pdf_document(str(FIXTURES_DIR / "simple.pdf"))

        ids = [b.id for b in blocks]
        assert len(ids) == len(set(ids)), "Block IDs must be unique"
        for block_id in ids:
            assert block_id.startswith("block-"), f"Block ID should start with 'block-': {block_id}"

    def test_extract_pdf_blocks_have_content_hashes(self):
        """Each block should have a SHA256 content hash."""
        from sidedoc.extract_pdf import extract_pdf_document

        blocks, _, _ = extract_pdf_document(str(FIXTURES_DIR / "simple.pdf"))

        for block in blocks:
            assert block.content_hash, f"Block {block.id} missing content_hash"
            # Verify it's a valid SHA256
            expected = hashlib.sha256(block.content.encode()).hexdigest()
            assert block.content_hash == expected, (
                f"Block {block.id} hash mismatch: {block.content_hash} != {expected}"
            )

    def test_extract_pdf_blocks_have_valid_offsets(self):
        """content_start and content_end should be valid non-negative offsets."""
        from sidedoc.extract_pdf import extract_pdf_document
        from sidedoc.extract import blocks_to_markdown

        blocks, _, _ = extract_pdf_document(str(FIXTURES_DIR / "simple.pdf"))
        content_md = blocks_to_markdown(blocks)

        for block in blocks:
            assert block.content_start >= 0, f"Block {block.id} has negative content_start"
            assert block.content_end >= block.content_start, (
                f"Block {block.id} content_end < content_start"
            )
            assert block.content_end <= len(content_md), (
                f"Block {block.id} content_end exceeds content length"
            )

    def test_extract_pdf_heading_has_level(self):
        """Heading blocks should have a level set."""
        from sidedoc.extract_pdf import extract_pdf_document

        blocks, _, _ = extract_pdf_document(str(FIXTURES_DIR / "simple.pdf"))

        headings = [b for b in blocks if b.type == "heading"]
        assert len(headings) >= 1, "Should find at least one heading"
        for h in headings:
            assert h.level is not None, f"Heading {h.id} missing level"
            assert 1 <= h.level <= 6, f"Heading {h.id} has invalid level: {h.level}"

    def test_extract_pdf_heading_content_has_markdown_prefix(self):
        """Heading content should start with # prefix."""
        from sidedoc.extract_pdf import extract_pdf_document

        blocks, _, _ = extract_pdf_document(str(FIXTURES_DIR / "simple.pdf"))

        headings = [b for b in blocks if b.type == "heading"]
        for h in headings:
            assert h.content.startswith("#"), (
                f"Heading {h.id} content should start with '#': {h.content[:50]}"
            )


class TestTableToGfm:
    """Test GFM table generation internals."""

    def test_no_header_no_double_separator(self):
        """A table with no header rows should have exactly one separator."""
        from sidedoc.extract_pdf import _table_to_gfm

        table_data = {
            "num_rows": 2,
            "num_cols": 2,
            "table_cells": [
                {"start_row_offset_idx": 0, "start_col_offset_idx": 0, "text": "A"},
                {"start_row_offset_idx": 0, "start_col_offset_idx": 1, "text": "B"},
                {"start_row_offset_idx": 1, "start_col_offset_idx": 0, "text": "C"},
                {"start_row_offset_idx": 1, "start_col_offset_idx": 1, "text": "D"},
            ],
        }
        result = _table_to_gfm(table_data)
        lines = result.strip().split("\n")
        sep_count = sum(1 for line in lines if set(line.replace(" ", "")) <= set("|-:"))
        assert sep_count == 1, f"Expected 1 separator row, got {sep_count}: {lines}"


class TestBuildTableMetadata:
    """Test table metadata generation internals."""

    def test_no_header_rows_when_none_detected(self):
        """header_rows should be 0 when no cells have column_header=True."""
        from sidedoc.extract_pdf import _build_table_metadata

        table_data = {
            "num_rows": 2,
            "num_cols": 2,
            "table_cells": [
                {"start_row_offset_idx": 0, "start_col_offset_idx": 0, "text": "A",
                 "column_header": False, "row_span": 1, "col_span": 1},
                {"start_row_offset_idx": 0, "start_col_offset_idx": 1, "text": "B",
                 "column_header": False, "row_span": 1, "col_span": 1},
                {"start_row_offset_idx": 1, "start_col_offset_idx": 0, "text": "C",
                 "column_header": False, "row_span": 1, "col_span": 1},
                {"start_row_offset_idx": 1, "start_col_offset_idx": 1, "text": "D",
                 "column_header": False, "row_span": 1, "col_span": 1},
            ],
        }
        metadata = _build_table_metadata(table_data)
        assert metadata["header_rows"] == 0, (
            f"Expected header_rows=0 when no headers, got {metadata['header_rows']}"
        )


class TestExtractPdfTable:
    """Test PDF table extraction with tables.pdf."""

    def test_extract_pdf_table_produces_table_block(self):
        """Extract tables.pdf and verify at least one table block exists."""
        from sidedoc.extract_pdf import extract_pdf_document

        blocks, _, _ = extract_pdf_document(str(FIXTURES_DIR / "tables.pdf"))

        table_blocks = [b for b in blocks if b.type == "table"]
        assert len(table_blocks) >= 1, "Should extract at least one table"

    def test_extract_pdf_table_has_metadata(self):
        """Table blocks should have table_metadata with rows and cols."""
        from sidedoc.extract_pdf import extract_pdf_document

        blocks, _, _ = extract_pdf_document(str(FIXTURES_DIR / "tables.pdf"))

        table_blocks = [b for b in blocks if b.type == "table"]
        assert len(table_blocks) >= 1

        table = table_blocks[0]
        assert table.table_metadata is not None, "Table should have table_metadata"
        assert "rows" in table.table_metadata, "table_metadata should have 'rows'"
        assert "cols" in table.table_metadata, "table_metadata should have 'cols'"
        assert table.table_metadata["rows"] >= 2, "Table should have at least 2 rows"
        assert table.table_metadata["cols"] >= 2, "Table should have at least 2 columns"

    def test_extract_pdf_table_content_is_gfm(self):
        """Table content should be GFM pipe table syntax."""
        from sidedoc.extract_pdf import extract_pdf_document

        blocks, _, _ = extract_pdf_document(str(FIXTURES_DIR / "tables.pdf"))

        table_blocks = [b for b in blocks if b.type == "table"]
        assert len(table_blocks) >= 1

        content = table_blocks[0].content
        lines = content.strip().split("\n")
        assert len(lines) >= 3, "GFM table needs at least header, separator, and one row"
        assert "|" in lines[0], "First line should contain pipe characters"
        assert "---" in lines[1], "Second line should be separator row"


class TestExtractPdfStyles:
    """Test PDF style extraction."""

    def test_extract_pdf_styles_generated(self):
        """Each block should have a corresponding Style."""
        from sidedoc.extract_pdf import extract_pdf_document, extract_pdf_styles

        blocks, _, _ = extract_pdf_document(str(FIXTURES_DIR / "simple.pdf"))
        styles = extract_pdf_styles(str(FIXTURES_DIR / "simple.pdf"), blocks)

        assert len(styles) == len(blocks), "Should have one style per block"
        for style, block in zip(styles, blocks):
            assert style.block_id == block.id, (
                f"Style block_id {style.block_id} doesn't match block {block.id}"
            )

    def test_extract_pdf_styles_have_defaults(self):
        """Styles should have reasonable default values."""
        from sidedoc.extract_pdf import extract_pdf_document, extract_pdf_styles

        blocks, _, _ = extract_pdf_document(str(FIXTURES_DIR / "simple.pdf"))
        styles = extract_pdf_styles(str(FIXTURES_DIR / "simple.pdf"), blocks)

        for style in styles:
            assert style.font_name, f"Style {style.block_id} missing font_name"
            assert style.font_size > 0, f"Style {style.block_id} has invalid font_size"
            assert style.alignment in ("left", "center", "right", "justify"), (
                f"Style {style.block_id} has invalid alignment: {style.alignment}"
            )


class TestExtractPdfCli:
    """Test CLI integration for PDF extraction."""

    def test_extract_pdf_cli_integration(self, tmp_path):
        """sidedoc extract simple.pdf should create a .sidedoc/ directory."""
        from click.testing import CliRunner
        from sidedoc.cli import main

        output = str(tmp_path / "simple.sidedoc")
        runner = CliRunner()
        result = runner.invoke(
            main, ["extract", str(FIXTURES_DIR / "simple.pdf"), "-o", output]
        )

        assert result.exit_code == 0, f"CLI failed: {result.output}"
        assert Path(output).exists(), "Output directory not created"
        assert (Path(output) / "content.md").exists(), "Missing content.md"

    def test_extract_pdf_cli_warns_track_changes(self, tmp_path):
        """--track-changes with PDF should produce a warning."""
        from click.testing import CliRunner
        from sidedoc.cli import main

        output = str(tmp_path / "simple.sidedoc")
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["extract", str(FIXTURES_DIR / "simple.pdf"), "-o", output, "--track-changes"],
        )

        assert result.exit_code == 0
        assert "ignored for PDF" in result.output or "ignored for PDF" in (result.stderr_bytes or b"").decode()


class TestExtractPdfEndToEnd:
    """Test full PDF extraction pipeline."""

    def test_pdf_to_sidedoc_directory_e2e(self, tmp_path):
        """Extract simple.pdf into a sidedoc directory and verify all files."""
        from sidedoc.extract_pdf import extract_pdf_document, extract_pdf_styles
        from sidedoc.extract import blocks_to_markdown
        from sidedoc.package import create_sidedoc_directory

        blocks, image_data, sections = extract_pdf_document(
            str(FIXTURES_DIR / "simple.pdf")
        )
        styles = extract_pdf_styles(str(FIXTURES_DIR / "simple.pdf"), blocks)
        content_md = blocks_to_markdown(blocks)

        output = str(tmp_path / "simple.sidedoc")
        create_sidedoc_directory(
            output, content_md, blocks, styles,
            str(FIXTURES_DIR / "simple.pdf"),
            image_data=image_data, sections=sections,
            source_format="pdf",
        )

        output_path = Path(output)
        assert (output_path / "content.md").exists(), "Missing content.md"
        assert (output_path / "structure.json").exists(), "Missing structure.json"
        assert (output_path / "styles.json").exists(), "Missing styles.json"
        assert (output_path / "manifest.json").exists(), "Missing manifest.json"

        # Verify content.md has actual content
        content = (output_path / "content.md").read_text()
        assert len(content) > 50, "content.md seems too short"

    def test_pdf_manifest_has_source_format(self, tmp_path):
        """manifest.json should contain source_format: 'pdf'."""
        from sidedoc.extract_pdf import extract_pdf_document, extract_pdf_styles
        from sidedoc.extract import blocks_to_markdown
        from sidedoc.package import create_sidedoc_directory

        blocks, image_data, sections = extract_pdf_document(
            str(FIXTURES_DIR / "simple.pdf")
        )
        styles = extract_pdf_styles(str(FIXTURES_DIR / "simple.pdf"), blocks)
        content_md = blocks_to_markdown(blocks)

        output = str(tmp_path / "simple.sidedoc")
        create_sidedoc_directory(
            output, content_md, blocks, styles,
            str(FIXTURES_DIR / "simple.pdf"),
            image_data=image_data, sections=sections,
            source_format="pdf",
        )

        manifest = json.loads((Path(output) / "manifest.json").read_text())
        assert manifest["source_format"] == "pdf", (
            f"Expected source_format 'pdf', got '{manifest.get('source_format')}'"
        )

    def test_docx_manifest_has_source_format_docx(self, tmp_path):
        """Verify existing DOCX path also sets source_format: 'docx'."""
        from sidedoc.extract import extract_document, extract_styles, blocks_to_markdown
        from sidedoc.package import create_sidedoc_directory

        docx_path = str(FIXTURES_DIR / "simple.docx")
        blocks, image_data, sections = extract_document(docx_path)
        styles = extract_styles(docx_path, blocks)
        content_md = blocks_to_markdown(blocks)

        output = str(tmp_path / "simple.sidedoc")
        create_sidedoc_directory(
            output, content_md, blocks, styles, docx_path,
            image_data=image_data, sections=sections,
        )

        manifest = json.loads((Path(output) / "manifest.json").read_text())
        assert manifest["source_format"] == "docx", (
            f"Expected source_format 'docx', got '{manifest.get('source_format')}'"
        )


class TestExtractPdfErrors:
    """Test error-path handling in PDF extraction."""

    def test_nonexistent_file_raises(self):
        """Extracting a path that does not exist should raise FileNotFoundError."""
        from sidedoc.extract_pdf import extract_pdf_document

        with pytest.raises(FileNotFoundError):
            extract_pdf_document("/nonexistent/path/to/file.pdf")

    def test_non_pdf_file_raises(self, tmp_path):
        """Extracting a text file with .pdf extension should raise ConversionError."""
        from docling.exceptions import ConversionError

        from sidedoc.extract_pdf import extract_pdf_document

        fake = tmp_path / "fake.pdf"
        fake.write_text("this is not a pdf")
        with pytest.raises(ConversionError):
            extract_pdf_document(str(fake))
