"""Tests for sync module - block matching algorithm."""

import hashlib
from sidedoc.models import Block
from sidedoc.sync import match_blocks


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
