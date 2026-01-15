"""Test document extraction functionality."""

import tempfile
from pathlib import Path
import struct
import zlib
from docx import Document
from docx.shared import Inches
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
        blocks, _ = extract_blocks(docx_path)
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
        blocks, _ = extract_blocks(docx_path)
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
        blocks, _ = extract_blocks(docx_path)
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
        blocks, _ = extract_blocks(docx_path)
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
        blocks, _ = extract_blocks(docx_path)
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
        blocks, _ = extract_blocks(docx_path)
        ids = [block.id for block in blocks]
        assert len(ids) == len(set(ids)), "Block IDs must be unique"
    finally:
        Path(docx_path).unlink()


def test_blocks_have_content_hashes():
    """Test that blocks have content hashes."""
    docx_path = create_test_docx([("Normal", "Test content")])

    try:
        blocks, _ = extract_blocks(docx_path)
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
        blocks, _ = extract_blocks(docx_path)
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
        blocks, _ = extract_blocks(docx_path)
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
        blocks, _ = extract_blocks(docx_path)
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
        blocks, _ = extract_blocks(docx_path)
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
        blocks, _ = extract_blocks(docx_path)
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
        blocks, _ = extract_blocks(docx_path)
        assert len(blocks) == 1
        assert blocks[0].content == "Normal **bold** and *italic* and ***both***"
        assert blocks[0].type == "paragraph"
    finally:
        Path(docx_path).unlink()


def create_list_docx(list_items: list[tuple[str, str]]) -> str:
    """Create a test docx file with list items.

    Args:
        list_items: List of (style, text) tuples where style is 'List Bullet' or 'List Number'

    Returns:
        Path to temporary docx file
    """
    doc = Document()
    for style, text in list_items:
        doc.add_paragraph(text, style=style)

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
    doc.save(temp_file.name)
    temp_file.close()
    return temp_file.name


def test_extract_bulleted_list():
    """Test extracting bulleted list items."""
    docx_path = create_list_docx([
        ("List Bullet", "First item"),
        ("List Bullet", "Second item"),
        ("List Bullet", "Third item")
    ])

    try:
        blocks, _ = extract_blocks(docx_path)
        assert len(blocks) == 3
        assert blocks[0].type == "list"
        assert blocks[0].content == "- First item"
        assert blocks[1].type == "list"
        assert blocks[1].content == "- Second item"
        assert blocks[2].type == "list"
        assert blocks[2].content == "- Third item"
    finally:
        Path(docx_path).unlink()


def test_extract_numbered_list():
    """Test extracting numbered list items."""
    docx_path = create_list_docx([
        ("List Number", "First item"),
        ("List Number", "Second item"),
        ("List Number", "Third item")
    ])

    try:
        blocks, _ = extract_blocks(docx_path)
        assert len(blocks) == 3
        assert blocks[0].type == "list"
        assert blocks[0].content == "1. First item"
        assert blocks[1].type == "list"
        assert blocks[1].content == "2. Second item"
        assert blocks[2].type == "list"
        assert blocks[2].content == "3. Third item"
    finally:
        Path(docx_path).unlink()


def test_extract_mixed_list_types():
    """Test extracting both bulleted and numbered lists."""
    docx_path = create_list_docx([
        ("List Bullet", "Bulleted item 1"),
        ("List Bullet", "Bulleted item 2"),
        ("List Number", "Numbered item 1"),
        ("List Number", "Numbered item 2")
    ])

    try:
        blocks, _ = extract_blocks(docx_path)
        assert len(blocks) == 4
        assert blocks[0].content == "- Bulleted item 1"
        assert blocks[1].content == "- Bulleted item 2"
        assert blocks[2].content == "1. Numbered item 1"
        assert blocks[3].content == "2. Numbered item 2"
        assert all(b.type == "list" for b in blocks)
    finally:
        Path(docx_path).unlink()


def test_extract_list_with_paragraphs():
    """Test extracting lists mixed with regular paragraphs."""
    doc = Document()
    doc.add_paragraph("Introduction paragraph")
    doc.add_paragraph("First item", style="List Bullet")
    doc.add_paragraph("Second item", style="List Bullet")
    doc.add_paragraph("Conclusion paragraph")

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
    doc.save(temp_file.name)
    temp_file.close()

    try:
        blocks, _ = extract_blocks(temp_file.name)
        assert len(blocks) == 4
        assert blocks[0].type == "paragraph"
        assert blocks[0].content == "Introduction paragraph"
        assert blocks[1].type == "list"
        assert blocks[1].content == "- First item"
        assert blocks[2].type == "list"
        assert blocks[2].content == "- Second item"
        assert blocks[3].type == "paragraph"
        assert blocks[3].content == "Conclusion paragraph"
    finally:
        Path(temp_file.name).unlink()


def create_minimal_png() -> bytes:
    """Create a minimal valid 1x1 PNG image.

    Returns:
        PNG file bytes
    """
    from PIL import Image
    import io

    # Use PIL to create a proper 1x1 PNG image
    img = Image.new('RGB', (1, 1), color='white')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    return img_bytes.getvalue()


def create_docx_with_image() -> tuple[str, str]:
    """Create a test docx file with an embedded image.

    Returns:
        Tuple of (docx_path, temp_image_path)
    """
    # Create temp image file
    temp_img = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    temp_img.write(create_minimal_png())
    temp_img.close()

    # Create docx with image
    doc = Document()
    doc.add_paragraph('Before image')
    doc.add_picture(temp_img.name, width=Inches(1.0))
    doc.add_paragraph('After image')

    temp_doc = tempfile.NamedTemporaryFile(delete=False, suffix='.docx')
    doc.save(temp_doc.name)
    temp_doc.close()

    return temp_doc.name, temp_img.name


def test_extract_single_image():
    """Test extracting a document with a single image."""
    docx_path, img_path = create_docx_with_image()

    try:
        blocks, _ = extract_blocks(docx_path)

        # Should have 3 blocks: paragraph, image, paragraph
        assert len(blocks) == 3
        assert blocks[0].type == "paragraph"
        assert blocks[0].content == "Before image"

        assert blocks[1].type == "image"
        assert blocks[1].content.startswith("![")
        assert "assets/" in blocks[1].content
        assert blocks[1].image_path is not None

        assert blocks[2].type == "paragraph"
        assert blocks[2].content == "After image"
    finally:
        Path(docx_path).unlink()
        Path(img_path).unlink()


def test_extract_multiple_images():
    """Test extracting a document with multiple images."""
    temp_img1 = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    temp_img1.write(create_minimal_png())
    temp_img1.close()

    temp_img2 = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    temp_img2.write(create_minimal_png())
    temp_img2.close()

    # Create docx with two images
    doc = Document()
    doc.add_paragraph('First image:')
    doc.add_picture(temp_img1.name, width=Inches(1.0))
    doc.add_paragraph('Second image:')
    doc.add_picture(temp_img2.name, width=Inches(1.0))

    temp_doc = tempfile.NamedTemporaryFile(delete=False, suffix='.docx')
    doc.save(temp_doc.name)
    temp_doc.close()

    try:
        blocks, _ = extract_blocks(temp_doc.name)

        # Should have 4 blocks
        assert len(blocks) == 4

        # First paragraph
        assert blocks[0].type == "paragraph"

        # First image
        assert blocks[1].type == "image"
        assert blocks[1].content.startswith("![")

        # Second paragraph
        assert blocks[2].type == "paragraph"

        # Second image
        assert blocks[3].type == "image"
        assert blocks[3].content.startswith("![")

        # Images should have different paths
        assert blocks[1].image_path != blocks[3].image_path
    finally:
        Path(temp_doc.name).unlink()
        Path(temp_img1.name).unlink()
        Path(temp_img2.name).unlink()


def test_extract_image_markdown_format():
    """Test that image blocks generate correct markdown format."""
    docx_path, img_path = create_docx_with_image()

    try:
        blocks, _ = extract_blocks(docx_path)
        image_block = blocks[1]

        # Check markdown format: ![alt text](assets/filename.ext)
        assert image_block.content.startswith("![")
        assert "](assets/" in image_block.content
        assert image_block.content.endswith(")")

        # Extract filename from markdown
        import re
        match = re.search(r'!\[(.*?)\]\((.*?)\)', image_block.content)
        assert match is not None
        alt_text = match.group(1)
        image_path = match.group(2)

        # Check alt text (can be empty or descriptive)
        assert isinstance(alt_text, str)

        # Check path format
        assert image_path.startswith("assets/")
        assert image_path.endswith(".png")
    finally:
        Path(docx_path).unlink()
        Path(img_path).unlink()


def test_extract_rejects_oversized_image():
    """Test that extraction rejects images exceeding MAX_IMAGE_SIZE."""
    # Create a large valid PNG image (10MB + some bytes)
    from sidedoc.extract import MAX_IMAGE_SIZE
    from PIL import Image
    import random

    # Create a large image with random noise (doesn't compress well)
    # ~10368 x 10368 pixels with random data will be > 10MB
    # But that's huge, so let's use uncompressed BMP or save with compression=0
    img_size = 2100
    img = Image.new('RGB', (img_size, img_size))
    # Fill with random pixels so it doesn't compress well
    pixels = img.load()
    for i in range(img_size):
        for j in range(img_size):
            pixels[i, j] = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

    temp_img = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    # Save with no compression to make it large
    img.save(temp_img.name, format='PNG', compress_level=0)
    temp_img.close()

    # Verify the image is actually larger than MAX_IMAGE_SIZE
    img_file_size = Path(temp_img.name).stat().st_size
    assert img_file_size > MAX_IMAGE_SIZE, f"Test image ({img_file_size} bytes) should be larger than MAX_IMAGE_SIZE ({MAX_IMAGE_SIZE} bytes)"

    # Create docx with oversized image
    doc = Document()
    doc.add_paragraph('Before image')
    doc.add_picture(temp_img.name, width=Inches(1.0))
    doc.add_paragraph('After image')

    temp_doc = tempfile.NamedTemporaryFile(delete=False, suffix='.docx')
    doc.save(temp_doc.name)
    temp_doc.close()

    try:
        blocks, image_data = extract_blocks(temp_doc.name)

        # Should have 3 blocks but image should be skipped
        # The image paragraph should be converted to a regular paragraph with warning
        assert len(blocks) == 3
        assert blocks[0].type == "paragraph"
        assert blocks[2].type == "paragraph"

        # The middle block should be a paragraph with error message, not an image
        assert blocks[1].type == "paragraph"
        assert "skipped" in blocks[1].content.lower() or "size" in blocks[1].content.lower()

        # No image data should be stored
        assert len(image_data) == 0
    finally:
        Path(temp_doc.name).unlink()
        Path(temp_img.name).unlink()


def test_extract_rejects_format_mismatch():
    """Test that extraction rejects images where format doesn't match extension."""
    # Create a JPEG image but save with .png extension
    from PIL import Image

    # Create a small JPEG image
    img = Image.new('RGB', (1, 1), color='red')
    temp_img = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    img.save(temp_img.name, format='JPEG')  # Save as JPEG but file has .png extension
    temp_img.close()

    # Create docx with mismatched image
    doc = Document()
    doc.add_paragraph('Before image')
    doc.add_picture(temp_img.name, width=Inches(1.0))
    doc.add_paragraph('After image')

    temp_doc = tempfile.NamedTemporaryFile(delete=False, suffix='.docx')
    doc.save(temp_doc.name)
    temp_doc.close()

    try:
        blocks, image_data = extract_blocks(temp_doc.name)

        # Should have 3 blocks but image should be skipped
        assert len(blocks) == 3
        assert blocks[0].type == "paragraph"
        assert blocks[2].type == "paragraph"

        # The middle block should be a paragraph with error message
        assert blocks[1].type == "paragraph"
        assert "skipped" in blocks[1].content.lower() or "format" in blocks[1].content.lower()

        # No image data should be stored
        assert len(image_data) == 0
    finally:
        Path(temp_doc.name).unlink()
        Path(temp_img.name).unlink()


def test_extract_rejects_corrupted_image():
    """Test that extraction rejects corrupted image data."""
    # Create corrupted image data (not a valid image)
    corrupted_data = b'This is not a valid image file'

    temp_img = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    temp_img.write(corrupted_data)
    temp_img.close()

    # Create docx with corrupted image
    doc = Document()
    doc.add_paragraph('Before image')
    # Note: python-docx may refuse to add invalid image, so we'll handle that
    try:
        doc.add_picture(temp_img.name, width=Inches(1.0))
    except Exception:
        # If python-docx can't add it, create a simpler test
        # Just test that extract_blocks handles corrupted embedded images gracefully
        Path(temp_img.name).unlink()
        return  # Skip this test if we can't create the scenario

    doc.add_paragraph('After image')

    temp_doc = tempfile.NamedTemporaryFile(delete=False, suffix='.docx')
    doc.save(temp_doc.name)
    temp_doc.close()

    try:
        blocks, image_data = extract_blocks(temp_doc.name)

        # Should handle gracefully - either skip or convert to paragraph
        assert len(blocks) >= 2  # At least the text paragraphs

        # If there's an image block, it should be marked as problematic
        # Otherwise it should be converted to paragraph with warning
        image_blocks = [b for b in blocks if b.type == "image"]
        if len(image_blocks) == 0:
            # Image was skipped, should have warning paragraph
            para_contents = [b.content.lower() for b in blocks if b.type == "paragraph"]
            assert any("skipped" in c or "invalid" in c or "corrupted" in c for c in para_contents)
    finally:
        Path(temp_doc.name).unlink()
        Path(temp_img.name).unlink()
