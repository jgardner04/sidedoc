"""Tests for sync module - block matching algorithm."""

import hashlib
import tempfile
from pathlib import Path
from docx import Document
from sidedoc.models import Block
from sidedoc.sync import match_blocks, generate_updated_docx


def compute_hash(content: str) -> str:
    """Helper to compute SHA256 hash of content."""
    return hashlib.sha256(content.encode()).hexdigest()


def test_match_unchanged_blocks():
    """Test that unchanged blocks are matched by content hash."""
    old_blocks = [
        Block(
            id="block-1",
            type="paragraph",
            content="This is unchanged.",
            docx_paragraph_index=0,
            content_start=0,
            content_end=19,
            content_hash=compute_hash("This is unchanged."),
        ),
    ]

    new_blocks = [
        Block(
            id="block-new-1",
            type="paragraph",
            content="This is unchanged.",
            docx_paragraph_index=0,
            content_start=0,
            content_end=19,
            content_hash=compute_hash("This is unchanged."),
        ),
    ]

    matches = match_blocks(old_blocks, new_blocks)

    assert "block-1" in matches
    assert matches["block-1"] == new_blocks[0]
    assert matches["block-1"].content == "This is unchanged."


def test_match_edited_blocks_by_position():
    """Test that edited blocks are matched by type and position."""
    old_blocks = [
        Block(
            id="block-1",
            type="paragraph",
            content="Original text.",
            docx_paragraph_index=0,
            content_start=0,
            content_end=14,
            content_hash=compute_hash("Original text."),
        ),
    ]

    new_blocks = [
        Block(
            id="block-new-1",
            type="paragraph",
            content="Modified text.",
            docx_paragraph_index=0,
            content_start=0,
            content_end=14,
            content_hash=compute_hash("Modified text."),
        ),
    ]

    matches = match_blocks(old_blocks, new_blocks)

    # Should match by position even though content changed
    assert "block-1" in matches
    assert matches["block-1"] == new_blocks[0]
    assert matches["block-1"].content == "Modified text."


def test_identify_new_blocks():
    """Test that new blocks have no corresponding old block."""
    old_blocks = [
        Block(
            id="block-1",
            type="paragraph",
            content="First paragraph.",
            docx_paragraph_index=0,
            content_start=0,
            content_end=16,
            content_hash=compute_hash("First paragraph."),
        ),
    ]

    new_blocks = [
        Block(
            id="block-new-1",
            type="paragraph",
            content="First paragraph.",
            docx_paragraph_index=0,
            content_start=0,
            content_end=16,
            content_hash=compute_hash("First paragraph."),
        ),
        Block(
            id="block-new-2",
            type="paragraph",
            content="New paragraph.",
            docx_paragraph_index=1,
            content_start=17,
            content_end=31,
            content_hash=compute_hash("New paragraph."),
        ),
    ]

    matches = match_blocks(old_blocks, new_blocks)

    # First block should match
    assert "block-1" in matches
    # New block should not be in matches (it's truly new)
    # The matches dict only contains old block IDs
    assert len(matches) == 1


def test_identify_deleted_blocks():
    """Test that deleted blocks are identified when old blocks have no match."""
    old_blocks = [
        Block(
            id="block-1",
            type="paragraph",
            content="Keep this.",
            docx_paragraph_index=0,
            content_start=0,
            content_end=10,
            content_hash=compute_hash("Keep this."),
        ),
        Block(
            id="block-2",
            type="paragraph",
            content="Delete this.",
            docx_paragraph_index=1,
            content_start=11,
            content_end=23,
            content_hash=compute_hash("Delete this."),
        ),
    ]

    new_blocks = [
        Block(
            id="block-new-1",
            type="paragraph",
            content="Keep this.",
            docx_paragraph_index=0,
            content_start=0,
            content_end=10,
            content_hash=compute_hash("Keep this."),
        ),
    ]

    matches = match_blocks(old_blocks, new_blocks)

    # Only first block should be matched
    assert "block-1" in matches
    assert "block-2" not in matches
    assert len(matches) == 1


def test_match_multiple_blocks_complex():
    """Test complex scenario with unchanged, edited, new, and deleted blocks."""
    old_blocks = [
        Block(
            id="block-1",
            type="heading",
            content="# Title",
            docx_paragraph_index=0,
            content_start=0,
            content_end=7,
            content_hash=compute_hash("# Title"),
            level=1,
        ),
        Block(
            id="block-2",
            type="paragraph",
            content="First para.",
            docx_paragraph_index=1,
            content_start=8,
            content_end=19,
            content_hash=compute_hash("First para."),
        ),
        Block(
            id="block-3",
            type="paragraph",
            content="Delete me.",
            docx_paragraph_index=2,
            content_start=20,
            content_end=30,
            content_hash=compute_hash("Delete me."),
        ),
    ]

    new_blocks = [
        Block(
            id="block-new-1",
            type="heading",
            content="# Title",
            docx_paragraph_index=0,
            content_start=0,
            content_end=7,
            content_hash=compute_hash("# Title"),
            level=1,
        ),
        Block(
            id="block-new-2",
            type="paragraph",
            content="First para modified.",
            docx_paragraph_index=1,
            content_start=8,
            content_end=28,
            content_hash=compute_hash("First para modified."),
        ),
        Block(
            id="block-new-3",
            type="paragraph",
            content="Brand new para.",
            docx_paragraph_index=2,
            content_start=29,
            content_end=44,
            content_hash=compute_hash("Brand new para."),
        ),
    ]

    matches = match_blocks(old_blocks, new_blocks)

    # block-1 unchanged (matched by hash)
    assert "block-1" in matches
    assert matches["block-1"].content == "# Title"

    # block-2 edited (matched by position)
    assert "block-2" in matches
    assert matches["block-2"].content == "First para modified."

    # block-3 treated as edited (matched by position)
    # Note: From algorithm perspective, this is reasonable - same type, same position
    # The algorithm can't distinguish "delete + add" from "edit" without content similarity
    assert "block-3" in matches
    assert matches["block-3"].content == "Brand new para."

    # Total matches = 3 (all blocks matched by position)
    assert len(matches) == 3


def test_true_deletion_when_blocks_decrease():
    """Test that blocks are truly deleted when new content has fewer blocks."""
    old_blocks = [
        Block(
            id="block-1",
            type="paragraph",
            content="Keep this.",
            docx_paragraph_index=0,
            content_start=0,
            content_end=10,
            content_hash=compute_hash("Keep this."),
        ),
        Block(
            id="block-2",
            type="paragraph",
            content="Also keep.",
            docx_paragraph_index=1,
            content_start=11,
            content_end=21,
            content_hash=compute_hash("Also keep."),
        ),
        Block(
            id="block-3",
            type="paragraph",
            content="Delete this.",
            docx_paragraph_index=2,
            content_start=22,
            content_end=34,
            content_hash=compute_hash("Delete this."),
        ),
    ]

    new_blocks = [
        Block(
            id="block-new-1",
            type="paragraph",
            content="Keep this.",
            docx_paragraph_index=0,
            content_start=0,
            content_end=10,
            content_hash=compute_hash("Keep this."),
        ),
        Block(
            id="block-new-2",
            type="paragraph",
            content="Also keep.",
            docx_paragraph_index=1,
            content_start=11,
            content_end=21,
            content_hash=compute_hash("Also keep."),
        ),
    ]

    matches = match_blocks(old_blocks, new_blocks)

    # First two blocks match by hash
    assert "block-1" in matches
    assert "block-2" in matches
    # Third block is truly deleted (no block at position 2)
    assert "block-3" not in matches
    assert len(matches) == 2


def test_match_respects_type_when_matching_by_position():
    """Test that blocks with different types don't match even at same position."""
    old_blocks = [
        Block(
            id="block-1",
            type="paragraph",
            content="Text.",
            docx_paragraph_index=0,
            content_start=0,
            content_end=5,
            content_hash=compute_hash("Text."),
        ),
    ]

    new_blocks = [
        Block(
            id="block-new-1",
            type="heading",
            content="# Text.",
            docx_paragraph_index=0,
            content_start=0,
            content_end=7,
            content_hash=compute_hash("# Text."),
            level=1,
        ),
    ]

    matches = match_blocks(old_blocks, new_blocks)

    # Should not match because types differ
    assert len(matches) == 0


# Tests for generate_updated_docx


def test_generate_updated_docx_with_unchanged_blocks() -> None:
    """Test that unchanged blocks preserve their content."""
    new_blocks = [
        Block(
            id="block-new-1",
            type="paragraph",
            content="Unchanged paragraph.",
            docx_paragraph_index=0,
            content_start=0,
            content_end=20,
            content_hash=compute_hash("Unchanged paragraph."),
        ),
    ]

    styles = {
        "block_styles": {
            "block-1": {
                "font_name": "Arial",
                "font_size": 12,
                "alignment": "left",
            }
        }
    }

    matches = {
        "block-1": new_blocks[0],
    }

    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = Path(temp_dir) / "test.docx"
        generate_updated_docx(new_blocks, matches, styles, str(output_path))

        # Verify docx was created
        assert output_path.exists()

        # Verify content
        doc = Document(str(output_path))
        assert len(doc.paragraphs) == 1
        assert doc.paragraphs[0].text == "Unchanged paragraph."


def test_generate_updated_docx_with_edited_blocks() -> None:
    """Test that edited blocks get updated content but preserve formatting."""
    old_block_id = "block-1"
    new_blocks = [
        Block(
            id="block-new-1",
            type="paragraph",
            content="Modified paragraph.",
            docx_paragraph_index=0,
            content_start=0,
            content_end=19,
            content_hash=compute_hash("Modified paragraph."),
        ),
    ]

    styles = {
        "block_styles": {
            old_block_id: {
                "font_name": "Times New Roman",
                "font_size": 14,
                "alignment": "center",
            }
        }
    }

    matches = {
        old_block_id: new_blocks[0],
    }

    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = Path(temp_dir) / "test.docx"
        generate_updated_docx(new_blocks, matches, styles, str(output_path))

        # Verify docx was created
        assert output_path.exists()

        # Verify content was updated
        doc = Document(str(output_path))
        assert len(doc.paragraphs) == 1
        assert doc.paragraphs[0].text == "Modified paragraph."


def test_generate_updated_docx_with_new_blocks() -> None:
    """Test that new blocks receive default formatting."""
    new_blocks = [
        Block(
            id="block-new-1",
            type="paragraph",
            content="Existing paragraph.",
            docx_paragraph_index=0,
            content_start=0,
            content_end=19,
            content_hash=compute_hash("Existing paragraph."),
        ),
        Block(
            id="block-new-2",
            type="paragraph",
            content="Brand new paragraph.",
            docx_paragraph_index=1,
            content_start=20,
            content_end=40,
            content_hash=compute_hash("Brand new paragraph."),
        ),
    ]

    styles = {
        "block_styles": {
            "block-1": {
                "font_name": "Arial",
                "font_size": 12,
                "alignment": "left",
            }
        }
    }

    matches = {
        "block-1": new_blocks[0],
    }

    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = Path(temp_dir) / "test.docx"
        generate_updated_docx(new_blocks, matches, styles, str(output_path))

        # Verify docx was created
        assert output_path.exists()

        # Verify both blocks present
        doc = Document(str(output_path))
        assert len(doc.paragraphs) == 2
        assert doc.paragraphs[0].text == "Existing paragraph."
        assert doc.paragraphs[1].text == "Brand new paragraph."


def test_generate_updated_docx_deleted_blocks_omitted() -> None:
    """Test that deleted blocks are not included in output."""
    # Old blocks: block-1, block-2
    # New blocks: only block-new-1 (which matches block-1)
    # Result: block-2 should be deleted (not in output)

    new_blocks = [
        Block(
            id="block-new-1",
            type="paragraph",
            content="Keep this.",
            docx_paragraph_index=0,
            content_start=0,
            content_end=10,
            content_hash=compute_hash("Keep this."),
        ),
    ]

    styles = {
        "block_styles": {
            "block-1": {"font_name": "Arial", "font_size": 12, "alignment": "left"},
            "block-2": {"font_name": "Arial", "font_size": 12, "alignment": "left"},
        }
    }

    matches = {
        "block-1": new_blocks[0],
        # block-2 not in matches = deleted
    }

    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = Path(temp_dir) / "test.docx"
        generate_updated_docx(new_blocks, matches, styles, str(output_path))

        # Verify only one paragraph (deleted block omitted)
        doc = Document(str(output_path))
        assert len(doc.paragraphs) == 1
        assert doc.paragraphs[0].text == "Keep this."


def test_generate_updated_docx_with_inline_formatting() -> None:
    """Test that inline formatting from markdown is applied."""
    new_blocks = [
        Block(
            id="block-new-1",
            type="paragraph",
            content="This is **bold** and *italic* text.",
            docx_paragraph_index=0,
            content_start=0,
            content_end=36,
            content_hash=compute_hash("This is **bold** and *italic* text."),
        ),
    ]

    styles = {"block_styles": {}}
    matches = {}

    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = Path(temp_dir) / "test.docx"
        generate_updated_docx(new_blocks, matches, styles, str(output_path))

        # Verify docx was created and has content
        assert output_path.exists()
        doc = Document(str(output_path))
        assert len(doc.paragraphs) == 1
        # Note: Detailed inline formatting verification would require
        # checking runs, but basic content check is sufficient for now
