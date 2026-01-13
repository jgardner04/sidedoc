"""Test document extraction functionality."""

import tempfile
from pathlib import Path
from docx import Document
from sidedoc.extract import extract_blocks
from sidedoc.models import Block


def create_test_docx(content_items: list[tuple[str, str]]) -> str:
    """Create a test docx file with specified content.

    Args:
        content_items: List of (style, text) tuples

    Returns:
        Path to temporary docx file
    """
    doc = Document()
    for style, text in content_items:
        doc.add_paragraph(text, style=style)

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
    doc.save(temp_file.name)
    temp_file.close()
    return temp_file.name


def test_extract_blocks_function_exists():
    """Test that extract_blocks function exists."""
    assert callable(extract_blocks)


def test_extract_single_paragraph():
    """Test extracting a simple paragraph."""
    docx_path = create_test_docx([("Normal", "Hello world")])

    try:
        blocks = extract_blocks(docx_path)
        assert len(blocks) == 1
        assert blocks[0].type == "paragraph"
        assert blocks[0].content == "Hello world"
        assert blocks[0].docx_paragraph_index == 0
    finally:
        Path(docx_path).unlink()


def test_extract_heading_1():
    """Test extracting Heading 1."""
    docx_path = create_test_docx([("Heading 1", "Title")])

    try:
        blocks = extract_blocks(docx_path)
        assert len(blocks) == 1
        assert blocks[0].type == "heading"
        assert blocks[0].content == "# Title"
        assert blocks[0].level == 1
    finally:
        Path(docx_path).unlink()


def test_extract_heading_2():
    """Test extracting Heading 2."""
    docx_path = create_test_docx([("Heading 2", "Subtitle")])

    try:
        blocks = extract_blocks(docx_path)
        assert len(blocks) == 1
        assert blocks[0].type == "heading"
        assert blocks[0].content == "## Subtitle"
        assert blocks[0].level == 2
    finally:
        Path(docx_path).unlink()


def test_extract_multiple_paragraphs():
    """Test extracting multiple paragraphs in order."""
    docx_path = create_test_docx([
        ("Normal", "First paragraph"),
        ("Normal", "Second paragraph"),
        ("Normal", "Third paragraph")
    ])

    try:
        blocks = extract_blocks(docx_path)
        assert len(blocks) == 3
        assert blocks[0].content == "First paragraph"
        assert blocks[1].content == "Second paragraph"
        assert blocks[2].content == "Third paragraph"
        assert blocks[0].docx_paragraph_index == 0
        assert blocks[1].docx_paragraph_index == 1
        assert blocks[2].docx_paragraph_index == 2
    finally:
        Path(docx_path).unlink()


def test_extract_mixed_content():
    """Test extracting headings and paragraphs together."""
    docx_path = create_test_docx([
        ("Heading 1", "Main Title"),
        ("Normal", "Introduction paragraph"),
        ("Heading 2", "Section"),
        ("Normal", "Section content")
    ])

    try:
        blocks = extract_blocks(docx_path)
        assert len(blocks) == 4
        assert blocks[0].type == "heading"
        assert blocks[0].level == 1
        assert blocks[1].type == "paragraph"
        assert blocks[2].type == "heading"
        assert blocks[2].level == 2
        assert blocks[3].type == "paragraph"
    finally:
        Path(docx_path).unlink()


def test_blocks_have_unique_ids():
    """Test that each block gets a unique ID."""
    docx_path = create_test_docx([
        ("Normal", "First"),
        ("Normal", "Second")
    ])

    try:
        blocks = extract_blocks(docx_path)
        ids = [block.id for block in blocks]
        assert len(ids) == len(set(ids)), "Block IDs must be unique"
    finally:
        Path(docx_path).unlink()


def test_blocks_have_content_hashes():
    """Test that blocks have content hashes."""
    docx_path = create_test_docx([("Normal", "Test content")])

    try:
        blocks = extract_blocks(docx_path)
        assert blocks[0].content_hash is not None
        assert len(blocks[0].content_hash) > 0
    finally:
        Path(docx_path).unlink()


def test_extract_all_heading_levels():
    """Test extracting all heading levels (1-6)."""
    docx_path = create_test_docx([
        ("Heading 1", "H1"),
        ("Heading 2", "H2"),
        ("Heading 3", "H3"),
        ("Heading 4", "H4"),
        ("Heading 5", "H5"),
        ("Heading 6", "H6")
    ])

    try:
        blocks = extract_blocks(docx_path)
        assert len(blocks) == 6
        for i, block in enumerate(blocks):
            assert block.type == "heading"
            assert block.level == i + 1
            assert block.content == "#" * (i + 1) + f" H{i + 1}"
    finally:
        Path(docx_path).unlink()


def create_formatted_docx(text_runs: list[tuple[str, bool, bool, bool]]) -> str:
    """Create a test docx file with inline formatting.

    Args:
        text_runs: List of (text, bold, italic, underline) tuples

    Returns:
        Path to temporary docx file
    """
    doc = Document()
    para = doc.add_paragraph()

    for text, bold, italic, underline in text_runs:
        run = para.add_run(text)
        run.bold = bold
        run.italic = italic
        run.underline = underline

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
    doc.save(temp_file.name)
    temp_file.close()
    return temp_file.name


def test_extract_bold_text():
    """Test extracting bold text as markdown."""
    docx_path = create_formatted_docx([
        ("This is ", False, False, False),
        ("bold", True, False, False),
        (" text", False, False, False)
    ])

    try:
        blocks = extract_blocks(docx_path)
        assert len(blocks) == 1
        assert blocks[0].content == "This is **bold** text"
        assert blocks[0].type == "paragraph"
    finally:
        Path(docx_path).unlink()


def test_extract_italic_text():
    """Test extracting italic text as markdown."""
    docx_path = create_formatted_docx([
        ("This is ", False, False, False),
        ("italic", False, True, False),
        (" text", False, False, False)
    ])

    try:
        blocks = extract_blocks(docx_path)
        assert len(blocks) == 1
        assert blocks[0].content == "This is *italic* text"
        assert blocks[0].type == "paragraph"
    finally:
        Path(docx_path).unlink()


def test_extract_bold_italic_text():
    """Test extracting bold and italic text as markdown."""
    docx_path = create_formatted_docx([
        ("This is ", False, False, False),
        ("bold and italic", True, True, False),
        (" text", False, False, False)
    ])

    try:
        blocks = extract_blocks(docx_path)
        assert len(blocks) == 1
        assert blocks[0].content == "This is ***bold and italic*** text"
        assert blocks[0].type == "paragraph"
    finally:
        Path(docx_path).unlink()


def test_extract_underline_preserved_in_formatting():
    """Test that underline is preserved in inline_formatting, not markdown."""
    docx_path = create_formatted_docx([
        ("This is ", False, False, False),
        ("underlined", False, False, True),
        (" text", False, False, False)
    ])

    try:
        blocks = extract_blocks(docx_path)
        assert len(blocks) == 1
        # Underline should not appear in markdown content
        assert blocks[0].content == "This is underlined text"
        # But should be recorded in inline_formatting
        assert blocks[0].inline_formatting is not None
        assert len(blocks[0].inline_formatting) > 0
        # Find the underline formatting entry
        underline_format = next(
            (fmt for fmt in blocks[0].inline_formatting if fmt.get("underline")),
            None
        )
        assert underline_format is not None
        assert underline_format["start"] == 8  # "This is " = 8 chars
        assert underline_format["end"] == 18  # + "underlined" = 10 chars
    finally:
        Path(docx_path).unlink()


def test_extract_mixed_inline_formatting():
    """Test extracting multiple inline formatting in one paragraph."""
    docx_path = create_formatted_docx([
        ("Normal ", False, False, False),
        ("bold", True, False, False),
        (" and ", False, False, False),
        ("italic", False, True, False),
        (" and ", False, False, False),
        ("both", True, True, False)
    ])

    try:
        blocks = extract_blocks(docx_path)
        assert len(blocks) == 1
        assert blocks[0].content == "Normal **bold** and *italic* and ***both***"
        assert blocks[0].type == "paragraph"
    finally:
        Path(docx_path).unlink()
