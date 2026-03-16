"""Tests for text box and shape extraction and reconstruction."""

import json
from pathlib import Path

import pytest

from sidedoc.extract import extract_blocks, extract_styles, blocks_to_markdown
from sidedoc.reconstruct import parse_markdown_to_blocks, build_docx_from_sidedoc
from sidedoc.package import block_to_structure_dict


@pytest.fixture
def textboxes_docx(fixtures_dir):
    """Return path to the textboxes fixture."""
    path = fixtures_dir / "textboxes.docx"
    if not path.exists():
        pytest.skip("textboxes.docx fixture not found; run create_fixtures.py")
    return str(path)


# =============================================================================
# Extraction tests
# =============================================================================


class TestTextBoxExtraction:
    """Tests for extracting text box content from docx."""

    def test_text_box_content_extracted(self, textboxes_docx):
        """Text box content should appear in extracted blocks."""
        blocks, _ = extract_blocks(textboxes_docx)
        all_content = " ".join(b.content for b in blocks)
        assert "This is a simple text box." in all_content

    def test_text_box_block_type(self, textboxes_docx):
        """Text box blocks should have type 'textbox'."""
        blocks, _ = extract_blocks(textboxes_docx)
        textbox_blocks = [b for b in blocks if b.type == "textbox"]
        assert len(textbox_blocks) >= 1

    def test_multiple_text_boxes_extracted(self, textboxes_docx):
        """All text boxes in the document should be extracted."""
        blocks, _ = extract_blocks(textboxes_docx)
        textbox_blocks = [b for b in blocks if b.type == "textbox"]
        # Fixture has 3 text boxes (simple, formatted, shape with text)
        assert len(textbox_blocks) == 3

    def test_text_box_metadata_has_anchor_type(self, textboxes_docx):
        """Text box metadata should include anchor type."""
        blocks, _ = extract_blocks(textboxes_docx)
        textbox_blocks = [b for b in blocks if b.type == "textbox"]
        first = textbox_blocks[0]
        assert first.text_box_metadata is not None
        assert first.text_box_metadata["anchor_type"] in ("anchor", "inline")

    def test_text_box_metadata_has_dimensions(self, textboxes_docx):
        """Text box metadata should include width and height."""
        blocks, _ = extract_blocks(textboxes_docx)
        textbox_blocks = [b for b in blocks if b.type == "textbox"]
        first = textbox_blocks[0]
        assert first.text_box_metadata is not None
        assert "width" in first.text_box_metadata
        assert "height" in first.text_box_metadata
        assert first.text_box_metadata["width"] > 0
        assert first.text_box_metadata["height"] > 0

    def test_text_box_metadata_has_drawing_xml(self, textboxes_docx):
        """Text box metadata should store original DrawingML XML for reconstruction."""
        blocks, _ = extract_blocks(textboxes_docx)
        textbox_blocks = [b for b in blocks if b.type == "textbox"]
        first = textbox_blocks[0]
        assert first.text_box_metadata is not None
        assert "drawing_xml" in first.text_box_metadata
        assert len(first.text_box_metadata["drawing_xml"]) > 0

    def test_anchored_text_box_position(self, textboxes_docx):
        """Anchored text box should have position offsets."""
        blocks, _ = extract_blocks(textboxes_docx)
        textbox_blocks = [b for b in blocks if b.type == "textbox"]
        anchored = [b for b in textbox_blocks
                     if b.text_box_metadata and b.text_box_metadata["anchor_type"] == "anchor"]
        assert len(anchored) >= 1
        first = anchored[0]
        assert "position_h" in first.text_box_metadata
        assert "position_v" in first.text_box_metadata

    def test_inline_text_box_extracted(self, textboxes_docx):
        """Inline text boxes should be extracted."""
        blocks, _ = extract_blocks(textboxes_docx)
        textbox_blocks = [b for b in blocks if b.type == "textbox"]
        inline = [b for b in textbox_blocks
                   if b.text_box_metadata and b.text_box_metadata["anchor_type"] == "inline"]
        assert len(inline) >= 1

    def test_text_box_with_multiple_paragraphs(self, textboxes_docx):
        """Text box with multiple paragraphs should have all content."""
        blocks, _ = extract_blocks(textboxes_docx)
        all_content = " ".join(b.content for b in blocks)
        assert "Bold heading inside text box" in all_content
        assert "Regular paragraph in text box." in all_content

    def test_shape_with_text_extracted(self, textboxes_docx):
        """Shapes with text content (non-txBox) should also be extracted."""
        blocks, _ = extract_blocks(textboxes_docx)
        all_content = " ".join(b.content for b in blocks)
        assert "Text inside a shape." in all_content

    def test_text_box_markdown_format(self, textboxes_docx):
        """Text box content should use HTML comment markers in markdown."""
        blocks, _ = extract_blocks(textboxes_docx)
        textbox_blocks = [b for b in blocks if b.type == "textbox"]
        first = textbox_blocks[0]
        assert first.content.startswith("<!-- textbox")
        assert first.content.endswith("<!-- /textbox -->")

    def test_no_regression_in_regular_paragraphs(self, textboxes_docx):
        """Regular paragraphs should still be extracted correctly."""
        blocks, _ = extract_blocks(textboxes_docx)
        paragraph_content = [b.content for b in blocks if b.type == "paragraph"]
        assert "Text before the first text box." in paragraph_content
        assert "Text between text boxes." in paragraph_content
        assert "Text after all text boxes." in paragraph_content

    def test_no_regression_images(self, fixtures_dir):
        """Image extraction should not regress with text box changes."""
        images_path = str(fixtures_dir / "images.docx")
        blocks, image_data = extract_blocks(images_path)
        image_blocks = [b for b in blocks if b.type == "image"]
        assert len(image_blocks) == 3
        assert len(image_data) == 3

    def test_fill_color_extracted(self, textboxes_docx):
        """Text box with fill color should have it in metadata."""
        blocks, _ = extract_blocks(textboxes_docx)
        textbox_blocks = [b for b in blocks if b.type == "textbox"]
        filled = [b for b in textbox_blocks
                   if b.text_box_metadata and b.text_box_metadata.get("fill_color")]
        assert len(filled) >= 1
        assert filled[0].text_box_metadata["fill_color"] == "FFFF00"

    def test_border_color_extracted(self, textboxes_docx):
        """Text box with border should have border_color in metadata."""
        blocks, _ = extract_blocks(textboxes_docx)
        textbox_blocks = [b for b in blocks if b.type == "textbox"]
        bordered = [b for b in textbox_blocks
                     if b.text_box_metadata and b.text_box_metadata.get("border_color")]
        assert len(bordered) >= 1


class TestTextBoxStyles:
    """Tests for text box style extraction."""

    def test_text_box_style_extracted(self, textboxes_docx):
        """Text box blocks should have styles extracted."""
        blocks, _ = extract_blocks(textboxes_docx)
        styles = extract_styles(textboxes_docx, blocks)
        assert len(styles) == len(blocks)


# =============================================================================
# Serialization tests
# =============================================================================


class TestTextBoxSerialization:
    """Tests for text box metadata serialization."""

    def test_block_to_structure_dict_includes_text_box_metadata(self, textboxes_docx):
        """block_to_structure_dict should include text_box_metadata."""
        blocks, _ = extract_blocks(textboxes_docx)
        textbox_blocks = [b for b in blocks if b.type == "textbox"]
        d = block_to_structure_dict(textbox_blocks[0])
        assert "text_box_metadata" in d
        assert d["text_box_metadata"] is not None
        assert "drawing_xml" in d["text_box_metadata"]

    def test_text_box_metadata_serializable(self, textboxes_docx):
        """Text box metadata should be JSON-serializable."""
        blocks, _ = extract_blocks(textboxes_docx)
        textbox_blocks = [b for b in blocks if b.type == "textbox"]
        d = block_to_structure_dict(textbox_blocks[0])
        # Should not raise
        json.dumps(d)


# =============================================================================
# Markdown representation tests
# =============================================================================


class TestTextBoxMarkdown:
    """Tests for text box markdown representation."""

    def test_blocks_to_markdown_includes_text_boxes(self, textboxes_docx):
        """blocks_to_markdown should include text box content."""
        blocks, _ = extract_blocks(textboxes_docx)
        md = blocks_to_markdown(blocks)
        assert "This is a simple text box." in md

    def test_parse_markdown_recognizes_textbox_blocks(self):
        """parse_markdown_to_blocks should recognize textbox markers."""
        md = (
            "Regular paragraph.\n"
            "<!-- textbox -->\n"
            "Text box content here.\n"
            "<!-- /textbox -->\n"
            "Another paragraph."
        )
        blocks = parse_markdown_to_blocks(md)
        textbox_blocks = [b for b in blocks if b.type == "textbox"]
        assert len(textbox_blocks) == 1
        assert "Text box content here." in textbox_blocks[0].content


# =============================================================================
# Reconstruction tests
# =============================================================================


class TestTextBoxReconstruction:
    """Tests for text box reconstruction in build."""

    def test_round_trip_preserves_text_box_content(self, textboxes_docx, tmp_path):
        """Extract -> build round-trip should preserve text box content."""
        from sidedoc.package import create_sidedoc_directory

        blocks, image_data = extract_blocks(textboxes_docx)
        styles = extract_styles(textboxes_docx, blocks)
        content_md = blocks_to_markdown(blocks)

        sidedoc_dir = str(tmp_path / "test.sidedoc")
        create_sidedoc_directory(sidedoc_dir, content_md, blocks, styles,
                                textboxes_docx, image_data)

        output_docx = str(tmp_path / "rebuilt.docx")
        build_docx_from_sidedoc(sidedoc_dir, output_docx)

        blocks2, _ = extract_blocks(output_docx)
        all_content = " ".join(b.content for b in blocks2)
        assert "This is a simple text box." in all_content

    def test_round_trip_preserves_text_box_count(self, textboxes_docx, tmp_path):
        """Round-trip should preserve the number of text boxes."""
        from sidedoc.package import create_sidedoc_directory

        blocks, image_data = extract_blocks(textboxes_docx)
        styles = extract_styles(textboxes_docx, blocks)
        content_md = blocks_to_markdown(blocks)

        sidedoc_dir = str(tmp_path / "test.sidedoc")
        create_sidedoc_directory(sidedoc_dir, content_md, blocks, styles,
                                textboxes_docx, image_data)

        output_docx = str(tmp_path / "rebuilt.docx")
        build_docx_from_sidedoc(sidedoc_dir, output_docx)

        blocks2, _ = extract_blocks(output_docx)
        original_count = len([b for b in blocks if b.type == "textbox"])
        rebuilt_count = len([b for b in blocks2 if b.type == "textbox"])
        assert rebuilt_count == original_count

    def test_textbox_without_metadata_falls_back_to_text(self, tmp_path):
        """Textbox block without metadata should fall back to plain text."""
        from sidedoc.reconstruct import create_docx_from_blocks
        from sidedoc.models import Block
        import hashlib

        content = "<!-- textbox -->\nFallback text\n<!-- /textbox -->"
        block = Block(
            id="block-0",
            type="textbox",
            content=content,
            docx_paragraph_index=0,
            content_start=0,
            content_end=len(content),
            content_hash=hashlib.sha256(content.encode()).hexdigest(),
        )

        doc = create_docx_from_blocks([block], {"block_styles": {}})
        assert len(doc.paragraphs) == 1
        assert doc.paragraphs[0].text == "Fallback text"
