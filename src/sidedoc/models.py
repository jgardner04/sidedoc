"""Data models for sidedoc format."""

from dataclasses import dataclass, field
from typing import Any, Literal, Optional


@dataclass
class TrackChange:
    """Represents a single track change (insertion or deletion).

    Used to store track change metadata from Word documents in structure.json.
    """

    type: Literal["insertion", "deletion"]  # Type of track change
    start: int  # Start position in content (character offset)
    end: int  # End position in content (character offset)
    author: str  # Author who made the change
    date: str  # ISO 8601 timestamp when change was made
    revision_id: str  # Unique revision ID from Word
    deleted_text: Optional[str] = None  # Text that was deleted (only for deletions)


@dataclass
class TrackChangesConfig:
    """Configuration for track changes in a sidedoc document.

    Stored in manifest.json to track whether the document uses track changes.
    """

    enabled: bool  # Whether track changes mode is enabled for this document
    source_had_revisions: bool  # Whether source docx had any track changes
    default_author: str  # Default author name for new changes (e.g., "Sidedoc AI")


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
    table_metadata: Optional[dict[str, Any]] = None  # For tables: rows, cols, cells, column_alignments, docx_table_index, header_rows, merged_cells
    track_changes: Optional[list[TrackChange]] = None  # Track changes for this block
    text_box_metadata: Optional[dict[str, Any]] = None  # For text boxes: anchor_type, width, height, position, border, fill, drawing_xml


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
    table_formatting: Optional[dict[str, Any]] = None  # For tables: column_widths, table_alignment, table_style, cell_styles


@dataclass
class ColumnDefinition:
    """Represents an individual column definition for unequal-width layouts.

    Used when w:equalWidth="0" in OOXML to specify per-column widths.
    """

    width: int  # Column width in twips (1/1440 inch)
    space: Optional[int] = None  # Space after this column in twips


@dataclass
class SectionProperties:
    """Represents section-level properties from OOXML w:sectPr.

    Stores column layout configuration. Extensible for headers/footers later.
    """

    column_count: int = 1
    column_spacing: Optional[int] = None  # Default spacing between columns in twips
    equal_width: bool = True
    columns: Optional[list[ColumnDefinition]] = None  # Per-column definitions (unequal widths)
    start_block_index: Optional[int] = None  # First block index in this section
    end_block_index: Optional[int] = None  # Last block index in this section (inclusive)


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
