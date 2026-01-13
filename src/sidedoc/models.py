"""Data models for sidedoc format."""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class Block:
    """Represents a content block in a sidedoc document.

    Blocks can be headings, paragraphs, lists, or images.
    """

    id: str
    type: str  # "heading", "paragraph", "list", "image"
    content: str
    docx_paragraph_index: int
    content_start: int
    content_end: int
    content_hash: str
    level: Optional[int] = None  # For headings (1-6)
    image_path: Optional[str] = None  # For images
    inline_formatting: Optional[list[dict[str, Any]]] = None


@dataclass
class Style:
    """Represents formatting information for a block.

    Stores font, size, alignment, and inline formatting.
    """

    block_id: str
    docx_style: str
    font_name: str
    font_size: int
    alignment: str  # "left", "center", "right", "justify"
    bold: Optional[bool] = None
    italic: Optional[bool] = None
    underline: Optional[bool] = None


@dataclass
class Manifest:
    """Represents metadata for a sidedoc document.

    Tracks version, timestamps, source info, and hashes.
    """

    sidedoc_version: str
    created_at: str  # ISO 8601 format
    modified_at: str  # ISO 8601 format
    source_file: str
    source_hash: str  # SHA256 hash of source file
    content_hash: str  # SHA256 hash of content.md
    generator: str  # e.g., "sidedoc-cli/0.1.0"
