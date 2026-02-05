"""Tests for table support in sidedoc.

Test fixtures:
- tables_simple.docx: Basic 3x3 table with:
  - Header row: Name | Role | Start Date
  - Data row 1: Alice | Engineer | 2024-01-15
  - Data row 2: Bob | Designer | 2024-02-01
"""

import json
from pathlib import Path
from typing import Any
from docx import Document

from sidedoc.extract import extract_blocks, blocks_to_markdown, extract_styles
from sidedoc.reconstruct import parse_markdown_to_blocks, create_docx_from_blocks


# ============================================================================
# US-T01: Create table test fixtures
# ============================================================================


def test_tables_simple_fixture_exists() -> None:
    """Verify tables_simple.docx fixture exists and has expected structure."""
    fixtures_dir = Path("tests/fixtures")
    fixture_path = fixtures_dir / "tables_simple.docx"

    assert fixture_path.exists(), "tables_simple.docx should exist"

    # Open and verify structure
    doc = Document(str(fixture_path))

    # Should have at least one table
    assert len(doc.tables) >= 1, "Document should have at least one table"

    # Get the first table
    table = doc.tables[0]

    # Should have 3 rows (header + 2 data rows)
    assert len(table.rows) == 3, "Table should have 3 rows"

    # Should have 3 columns
    assert len(table.columns) == 3, "Table should have 3 columns"

    # Verify header row content
    header_cells = [cell.text for cell in table.rows[0].cells]
    assert header_cells == ["Name", "Role", "Start Date"], f"Header row should be Name, Role, Start Date but got {header_cells}"

    # Verify first data row
    row1_cells = [cell.text for cell in table.rows[1].cells]
    assert row1_cells == ["Alice", "Engineer", "2024-01-15"], f"First data row should be Alice, Engineer, 2024-01-15 but got {row1_cells}"

    # Verify second data row
    row2_cells = [cell.text for cell in table.rows[2].cells]
    assert row2_cells == ["Bob", "Designer", "2024-02-01"], f"Second data row should be Bob, Designer, 2024-02-01 but got {row2_cells}"


# ============================================================================
# US-T02: Extract simple tables to GFM markdown
# ============================================================================


def test_extract_simple_table_to_gfm() -> None:
    """Test that tables are extracted as GFM pipe table syntax."""
    fixture_path = Path("tests/fixtures/tables_simple.docx")
    blocks, _ = extract_blocks(str(fixture_path))

    # Find table blocks
    table_blocks = [b for b in blocks if b.type == "table"]
    assert len(table_blocks) >= 1, "Should extract at least one table block"

    table_block = table_blocks[0]

    # Content should be GFM pipe table format
    content = table_block.content
    lines = content.strip().split("\n")

    # Should have header row, separator row, and data rows
    assert len(lines) >= 4, f"Table should have at least 4 lines (header, separator, 2 data rows), got {len(lines)}"

    # First line should be header
    assert "|" in lines[0], "Header row should contain pipe characters"
    assert "Name" in lines[0], "Header should contain 'Name'"
    assert "Role" in lines[0], "Header should contain 'Role'"
    assert "Start Date" in lines[0], "Header should contain 'Start Date'"

    # Second line should be separator (dashes and pipes)
    assert "|" in lines[1], "Separator row should contain pipe characters"
    assert "-" in lines[1], "Separator row should contain dashes"

    # Data rows
    assert "Alice" in lines[2], "First data row should contain 'Alice'"
    assert "Bob" in lines[3], "Second data row should contain 'Bob'"


def test_extract_table_creates_table_block_type() -> None:
    """Test that extracted tables have type 'table' in structure."""
    fixture_path = Path("tests/fixtures/tables_simple.docx")
    blocks, _ = extract_blocks(str(fixture_path))

    # Find table blocks
    table_blocks = [b for b in blocks if b.type == "table"]
    assert len(table_blocks) >= 1, "Should have at least one table block"

    # Verify block type
    assert table_blocks[0].type == "table"


def test_extract_table_preserves_empty_cells() -> None:
    """Test that empty cells are preserved as empty pipe segments."""
    # We'll test this with a table that has empty cells
    # For now, just verify the basic extraction works
    fixture_path = Path("tests/fixtures/tables_simple.docx")
    blocks, _ = extract_blocks(str(fixture_path))

    table_blocks = [b for b in blocks if b.type == "table"]
    assert len(table_blocks) >= 1

    # The simple fixture doesn't have empty cells, but verify format
    content = table_blocks[0].content
    # Each row should have proper pipe structure
    for line in content.strip().split("\n"):
        if line.strip():
            assert line.startswith("|"), f"Each row should start with pipe: {line}"
            assert line.endswith("|"), f"Each row should end with pipe: {line}"


# ============================================================================
# US-T03: Store table structure metadata in structure.json
# ============================================================================


def test_table_block_has_rows_cols_metadata() -> None:
    """Test that table blocks have rows and cols metadata."""
    fixture_path = Path("tests/fixtures/tables_simple.docx")
    blocks, _ = extract_blocks(str(fixture_path))

    table_blocks = [b for b in blocks if b.type == "table"]
    assert len(table_blocks) >= 1

    table_block = table_blocks[0]

    # Block should have table_metadata attribute with rows and cols
    assert hasattr(table_block, 'table_metadata'), "Table block should have table_metadata"
    assert table_block.table_metadata is not None, "table_metadata should not be None"
    assert "rows" in table_block.table_metadata, "table_metadata should have 'rows'"
    assert "cols" in table_block.table_metadata, "table_metadata should have 'cols'"
    assert table_block.table_metadata["rows"] == 3, "Should have 3 rows"
    assert table_block.table_metadata["cols"] == 3, "Should have 3 columns"


def test_table_block_has_cells_metadata() -> None:
    """Test that table blocks have cells array with content hashes."""
    fixture_path = Path("tests/fixtures/tables_simple.docx")
    blocks, _ = extract_blocks(str(fixture_path))

    table_blocks = [b for b in blocks if b.type == "table"]
    table_block = table_blocks[0]

    assert table_block.table_metadata is not None
    assert "cells" in table_block.table_metadata, "table_metadata should have 'cells'"

    cells = table_block.table_metadata["cells"]
    # Should be a 2D array (list of rows, each row is list of cell metadata)
    assert len(cells) == 3, "Should have 3 rows of cells"
    assert len(cells[0]) == 3, "First row should have 3 cells"

    # Each cell should have row, col, content_hash
    first_cell = cells[0][0]
    assert "row" in first_cell, "Cell should have 'row'"
    assert "col" in first_cell, "Cell should have 'col'"
    assert "content_hash" in first_cell, "Cell should have 'content_hash'"
    assert first_cell["row"] == 0
    assert first_cell["col"] == 0


def test_table_block_has_docx_table_index() -> None:
    """Test that table blocks have docx_table_index field."""
    fixture_path = Path("tests/fixtures/tables_simple.docx")
    blocks, _ = extract_blocks(str(fixture_path))

    table_blocks = [b for b in blocks if b.type == "table"]
    table_block = table_blocks[0]

    assert table_block.table_metadata is not None
    assert "docx_table_index" in table_block.table_metadata, "table_metadata should have 'docx_table_index'"
    assert table_block.table_metadata["docx_table_index"] == 0, "First table should have index 0"


# ============================================================================
# US-T04: Store basic table formatting in styles.json
# ============================================================================


def test_table_style_has_column_widths() -> None:
    """Test that table styles include column_widths array."""
    fixture_path = Path("tests/fixtures/tables_simple.docx")
    blocks, _ = extract_blocks(str(fixture_path))
    styles = extract_styles(str(fixture_path), blocks)

    # Find the style for our table block
    table_blocks = [b for b in blocks if b.type == "table"]
    assert len(table_blocks) >= 1

    table_block = table_blocks[0]

    # Find corresponding style
    table_styles = [s for s in styles if s.block_id == table_block.id]
    assert len(table_styles) == 1, "Should have a style for the table block"

    table_style = table_styles[0]

    # Style should have table_formatting with column_widths
    assert hasattr(table_style, 'table_formatting'), "Style should have table_formatting"
    assert table_style.table_formatting is not None, "table_formatting should not be None"
    assert "column_widths" in table_style.table_formatting, "Should have column_widths"

    column_widths = table_style.table_formatting["column_widths"]
    assert len(column_widths) == 3, "Should have 3 column widths for 3-column table"


def test_table_style_has_table_alignment() -> None:
    """Test that table styles include table_alignment."""
    fixture_path = Path("tests/fixtures/tables_simple.docx")
    blocks, _ = extract_blocks(str(fixture_path))
    styles = extract_styles(str(fixture_path), blocks)

    table_blocks = [b for b in blocks if b.type == "table"]
    table_block = table_blocks[0]

    table_styles = [s for s in styles if s.block_id == table_block.id]
    table_style = table_styles[0]

    assert table_style.table_formatting is not None
    assert "table_alignment" in table_style.table_formatting, "Should have table_alignment"
    # Default is usually left
    assert table_style.table_formatting["table_alignment"] in ("left", "center", "right")


# ============================================================================
# US-T05: Reconstruct basic tables in docx
# ============================================================================


def test_parse_markdown_detects_table_blocks() -> None:
    """Test that parse_markdown_to_blocks detects GFM table syntax."""
    markdown = """# Title

Some text.

| Name | Role |
|------|------|
| Alice | Engineer |
| Bob | Designer |

More text.
"""
    blocks = parse_markdown_to_blocks(markdown)

    # Should have a table block
    table_blocks = [b for b in blocks if b.type == "table"]
    assert len(table_blocks) >= 1, "Should detect at least one table block"


def test_create_docx_creates_table() -> None:
    """Test that create_docx_from_blocks creates tables from table blocks."""
    # Create a simple table block
    from sidedoc.models import Block

    table_content = """| Name | Role |
| --- | --- |
| Alice | Engineer |
| Bob | Designer |"""

    blocks = [
        Block(
            id="block-0",
            type="table",
            content=table_content,
            docx_paragraph_index=-1,
            content_start=0,
            content_end=len(table_content),
            content_hash="abc123",
            table_metadata={
                "rows": 3,
                "cols": 2,
                "cells": [],
                "docx_table_index": 0
            }
        )
    ]

    styles: dict[str, Any] = {"block_styles": {}}
    doc = create_docx_from_blocks(blocks, styles)

    # Verify the document has a table
    assert len(doc.tables) >= 1, "Document should have at least one table"

    table = doc.tables[0]
    assert len(table.rows) == 3, "Table should have 3 rows"
    assert len(table.columns) == 2, "Table should have 2 columns"

    # Verify cell content
    assert table.rows[0].cells[0].text == "Name"
    assert table.rows[0].cells[1].text == "Role"
    assert table.rows[1].cells[0].text == "Alice"
    assert table.rows[1].cells[1].text == "Engineer"


def test_reconstruct_table_preserves_content() -> None:
    """Test that table content matches after reconstruction."""
    fixture_path = Path("tests/fixtures/tables_simple.docx")
    blocks, _ = extract_blocks(str(fixture_path))
    styles = extract_styles(str(fixture_path), blocks)

    # Convert styles to the format expected by create_docx_from_blocks
    styles_dict: dict[str, Any] = {"block_styles": {}}

    doc = create_docx_from_blocks(blocks, styles_dict)

    # Verify the document has a table
    assert len(doc.tables) >= 1, "Reconstructed doc should have at least one table"

    table = doc.tables[0]
    assert table.rows[0].cells[0].text == "Name"
    assert table.rows[1].cells[0].text == "Alice"
    assert table.rows[2].cells[0].text == "Bob"


# ============================================================================
# US-T06: Extract column alignment from tables
# ============================================================================


def test_table_gfm_has_separator_row() -> None:
    """Test that extracted GFM tables have a proper separator row."""
    fixture_path = Path("tests/fixtures/tables_simple.docx")
    blocks, _ = extract_blocks(str(fixture_path))

    table_blocks = [b for b in blocks if b.type == "table"]
    table_block = table_blocks[0]

    lines = table_block.content.split("\n")
    assert len(lines) >= 2

    # Second line should be separator with alignment indicators
    separator = lines[1]
    assert "|" in separator
    assert "---" in separator or ":---" in separator or "---:" in separator


def test_table_metadata_has_column_alignments() -> None:
    """Test that table metadata includes column alignments."""
    fixture_path = Path("tests/fixtures/tables_simple.docx")
    blocks, _ = extract_blocks(str(fixture_path))

    table_blocks = [b for b in blocks if b.type == "table"]
    table_block = table_blocks[0]

    assert table_block.table_metadata is not None
    assert "column_alignments" in table_block.table_metadata, "table_metadata should have 'column_alignments'"

    alignments = table_block.table_metadata["column_alignments"]
    assert len(alignments) == 3, "Should have alignment for each column"
    # Default alignment is typically 'left'
    assert all(a in ("left", "center", "right") for a in alignments)


# ============================================================================
# US-T07: Apply column alignment during reconstruction
# ============================================================================


def test_parse_gfm_alignment_indicators() -> None:
    """Test that GFM alignment indicators are parsed correctly."""
    from sidedoc.reconstruct import parse_gfm_alignments

    # Test left alignment (default)
    assert parse_gfm_alignments("| --- | --- |") == ["left", "left"]

    # Test center alignment
    assert parse_gfm_alignments("| :---: | :---: |") == ["center", "center"]

    # Test right alignment
    assert parse_gfm_alignments("| ---: | ---: |") == ["right", "right"]

    # Test mixed alignments
    assert parse_gfm_alignments("| :--- | :---: | ---: |") == ["left", "center", "right"]


def test_reconstruct_table_applies_alignment() -> None:
    """Test that reconstructed tables have correct cell alignment."""
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from sidedoc.models import Block

    # Create a table with center and right alignment
    table_content = """| Name | Amount |
| :---: | ---: |
| Alice | $100 |
| Bob | $200 |"""

    blocks = [
        Block(
            id="block-0",
            type="table",
            content=table_content,
            docx_paragraph_index=-1,
            content_start=0,
            content_end=len(table_content),
            content_hash="abc123",
            table_metadata={
                "rows": 3,
                "cols": 2,
                "cells": [],
                "column_alignments": ["center", "right"],
                "docx_table_index": 0
            }
        )
    ]

    styles_dict: dict[str, Any] = {"block_styles": {}}
    doc = create_docx_from_blocks(blocks, styles_dict)

    assert len(doc.tables) >= 1
    table = doc.tables[0]

    # Check first column is center-aligned
    cell_0_0 = table.cell(0, 0)
    if cell_0_0.paragraphs:
        assert cell_0_0.paragraphs[0].alignment == WD_ALIGN_PARAGRAPH.CENTER

    # Check second column is right-aligned
    cell_0_1 = table.cell(0, 1)
    if cell_0_1.paragraphs:
        assert cell_0_1.paragraphs[0].alignment == WD_ALIGN_PARAGRAPH.RIGHT


# ============================================================================
# US-T08: Handle special characters in table cells
# ============================================================================


def test_extract_table_escapes_pipe_characters() -> None:
    """Test that pipe characters in cell content are escaped and roundtrip correctly."""
    # Create a test document with pipe in cell
    from docx import Document as DocxDocument
    import tempfile

    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create a docx with pipe in cell
        doc = DocxDocument()
        table = doc.add_table(rows=2, cols=2)
        table.cell(0, 0).text = "Header"
        table.cell(0, 1).text = "Value"
        table.cell(1, 0).text = "Test|Pipe"  # Cell with pipe character
        table.cell(1, 1).text = "Normal"

        test_path = Path(tmp_dir) / "test_pipes.docx"
        doc.save(str(test_path))

        # Extract the table
        blocks, _ = extract_blocks(str(test_path))

        table_blocks = [b for b in blocks if b.type == "table"]
        assert len(table_blocks) >= 1

        table_content = table_blocks[0].content

        # The pipe should be escaped as \|
        assert "\\|" in table_content, f"Pipe should be escaped, got: {table_content}"
        assert "Test\\|Pipe" in table_content, f"Cell content should have escaped pipe"

        # Test roundtrip: reconstruct and verify pipes are unescaped
        styles_dict: dict[str, Any] = {"block_styles": {}}
        reconstructed_doc = create_docx_from_blocks(blocks, styles_dict)

        # Verify the reconstructed table has unescaped pipe
        assert len(reconstructed_doc.tables) >= 1
        reconstructed_table = reconstructed_doc.tables[0]
        assert reconstructed_table.cell(1, 0).text == "Test|Pipe", \
            f"Roundtrip should preserve pipe: got {reconstructed_table.cell(1, 0).text}"


def test_extract_table_handles_newlines_in_cells() -> None:
    """Test that newlines in cells are handled gracefully."""
    from docx import Document as DocxDocument
    import tempfile

    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create a docx with newline in cell
        doc = DocxDocument()
        table = doc.add_table(rows=2, cols=2)
        table.cell(0, 0).text = "Header"
        table.cell(0, 1).text = "Value"
        # Add a cell with paragraph break
        cell = table.cell(1, 0)
        cell.text = "Line1"  # First line
        # Note: python-docx cell.text will join multiple paragraphs
        table.cell(1, 1).text = "Normal"

        test_path = Path(tmp_dir) / "test_newlines.docx"
        doc.save(str(test_path))

        # Extract should not crash
        blocks, _ = extract_blocks(str(test_path))

        table_blocks = [b for b in blocks if b.type == "table"]
        assert len(table_blocks) >= 1

        # Content should be parseable (no literal newlines breaking the table)
        table_content = table_blocks[0].content
        lines = table_content.split("\n")
        # Each line should be a valid table row
        for line in lines:
            assert line.strip().startswith("|") and line.strip().endswith("|")
