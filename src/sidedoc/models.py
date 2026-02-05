"""Data models for sidedoc format."""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class Block:
    """Represents a content block in a sidedoc document.

    Blocks can be headings, paragraphs, lists, images, or tables.
    """

    id: str
    type: str  # "heading", "paragraph", "list", "image", "table"
    content: str
    docx_paragraph_index: int
    content_start: int
    content_end: int
    content_hash: str
    level: Optional[int] = None  # For headings (1-6)
    image_path: Optional[str] = None  # For images
    inline_formatting: Optional[list[dict[str, Any]]] = None
    table_metadata: Optional[dict[str, Any]] = None  # For tables: rows, cols, cells, docx_table_index


@dataclass
class Style:
    """Represents formatting information for a block.

    Stores font, size, alignment, and inline formatting.
    For tables, includes table_formatting with column_widths, table_alignment, etc.
    """

    block_id: str
    docx_style: str
    font_name: str
    font_size: int
    alignment: str  # "left", "center", "right", "justify"
    bold: Optional[bool] = None
    italic: Optional[bool] = None
    underline: Optional[bool] = None
    table_formatting: Optional[dict[str, Any]] = None  # For tables: column_widths, table_alignment, table_style


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
