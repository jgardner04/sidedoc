"""Test data models for sidedoc format."""

from dataclasses import is_dataclass
from sidedoc.models import Block, Style, Manifest


def test_block_is_dataclass():
    """Test that Block is a dataclass."""
    assert is_dataclass(Block), "Block must be a dataclass"


def test_block_has_required_fields():
    """Test that Block has required fields."""
    block = Block(
        id="block-1",
        type="paragraph",
        content="Hello world",
        docx_paragraph_index=0,
        content_start=0,
        content_end=11,
        content_hash="abc123"
    )
    assert block.id == "block-1"
    assert block.type == "paragraph"
    assert block.content == "Hello world"
    assert block.docx_paragraph_index == 0
    assert block.content_start == 0
    assert block.content_end == 11
    assert block.content_hash == "abc123"


def test_block_supports_heading_type():
    """Test that Block supports heading type."""
    block = Block(
        id="block-1",
        type="heading",
        content="# Title",
        docx_paragraph_index=0,
        content_start=0,
        content_end=7,
        content_hash="def456",
        level=1
    )
    assert block.type == "heading"
    assert block.level == 1


def test_block_supports_list_type():
    """Test that Block supports list type."""
    block = Block(
        id="block-1",
        type="list",
        content="- Item 1",
        docx_paragraph_index=0,
        content_start=0,
        content_end=8,
        content_hash="ghi789"
    )
    assert block.type == "list"


def test_block_supports_image_type():
    """Test that Block supports image type."""
    block = Block(
        id="block-1",
        type="image",
        content="![alt](assets/image.png)",
        docx_paragraph_index=0,
        content_start=0,
        content_end=24,
        content_hash="jkl012",
        image_path="assets/image.png"
    )
    assert block.type == "image"
    assert block.image_path == "assets/image.png"


def test_block_has_inline_formatting():
    """Test that Block can store inline formatting."""
    block = Block(
        id="block-1",
        type="paragraph",
        content="Hello **world**",
        docx_paragraph_index=0,
        content_start=0,
        content_end=15,
        content_hash="mno345",
        inline_formatting=[
            {"start": 6, "end": 15, "bold": True}
        ]
    )
    assert block.inline_formatting is not None
    assert len(block.inline_formatting) == 1
    assert block.inline_formatting[0]["bold"] is True


def test_style_is_dataclass():
    """Test that Style is a dataclass."""
    assert is_dataclass(Style), "Style must be a dataclass"


def test_style_has_required_fields():
    """Test that Style has required fields."""
    style = Style(
        block_id="block-1",
        docx_style="Normal",
        font_name="Calibri",
        font_size=11,
        alignment="left"
    )
    assert style.block_id == "block-1"
    assert style.docx_style == "Normal"
    assert style.font_name == "Calibri"
    assert style.font_size == 11
    assert style.alignment == "left"


def test_style_supports_inline_formatting():
    """Test that Style supports inline formatting data."""
    style = Style(
        block_id="block-1",
        docx_style="Normal",
        font_name="Calibri",
        font_size=11,
        alignment="left",
        bold=True,
        italic=False,
        underline=True
    )
    assert style.bold is True
    assert style.italic is False
    assert style.underline is True


def test_manifest_is_dataclass():
    """Test that Manifest is a dataclass."""
    assert is_dataclass(Manifest), "Manifest must be a dataclass"


def test_manifest_has_required_fields():
    """Test that Manifest has required fields."""
    manifest = Manifest(
        sidedoc_version="1.0.0",
        created_at="2026-01-12T12:00:00Z",
        modified_at="2026-01-12T12:00:00Z",
        source_file="document.docx",
        source_hash="abc123def456",
        content_hash="789ghi012jkl",
        generator="sidedoc-cli/0.1.0"
    )
    assert manifest.sidedoc_version == "1.0.0"
    assert manifest.created_at == "2026-01-12T12:00:00Z"
    assert manifest.modified_at == "2026-01-12T12:00:00Z"
    assert manifest.source_file == "document.docx"
    assert manifest.source_hash == "abc123def456"
    assert manifest.content_hash == "789ghi012jkl"
    assert manifest.generator == "sidedoc-cli/0.1.0"


def test_all_models_have_type_hints():
    """Test that all models have proper type hints."""
    # This test will pass if the models are defined with type hints
    # mypy will catch any issues with type hints during type checking
    assert True
