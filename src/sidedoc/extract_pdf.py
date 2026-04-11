"""Extract content from PDF files into Sidedoc Block/Style format using Docling."""

import hashlib
from typing import Any

from sidedoc.extract import generate_block_id
from sidedoc.models import Block, SectionProperties, Style

try:
    from docling.document_converter import DocumentConverter
except ImportError as e:
    raise ImportError(
        "PDF extraction requires docling. Install with: pip install sidedoc[pdf]"
    ) from e


def _compute_content_hash(content: str) -> str:
    """Compute SHA256 hash of content string."""
    return hashlib.sha256(content.encode()).hexdigest()


def _detect_header_rows(table_data: dict[str, Any]) -> int:
    """Return the number of header rows (0 or 1) from Docling table data."""
    for cell in table_data.get("table_cells", []):
        if cell.get("column_header", False) and cell["start_row_offset_idx"] == 0:
            return 1
    return 0


def _table_to_gfm(table_data: dict[str, Any]) -> str:
    """Convert Docling table data to GFM pipe table syntax."""
    num_rows = table_data["num_rows"]
    num_cols = table_data["num_cols"]

    if num_rows == 0 or num_cols == 0:
        return ""

    # Build grid from cells
    grid: list[list[str]] = [[""] * num_cols for _ in range(num_rows)]
    for cell in table_data.get("table_cells", []):
        row = cell["start_row_offset_idx"]
        col = cell["start_col_offset_idx"]
        if row < num_rows and col < num_cols:
            grid[row][col] = cell.get("text", "").replace("|", "\\|")

    header_rows = _detect_header_rows(table_data)

    lines = []
    for i, row in enumerate(grid):
        line = "| " + " | ".join(row) + " |"
        lines.append(line)
        if header_rows > 0 and i == header_rows - 1:
            sep = "| " + " | ".join("---" for _ in row) + " |"
            lines.append(sep)

    # If no header rows detected, put separator after first row
    if header_rows == 0 and lines:
        sep = "| " + " | ".join("---" for _ in grid[0]) + " |"
        lines.insert(1, sep)

    return "\n".join(lines)


def _build_table_metadata(table_data: dict[str, Any]) -> dict[str, Any]:
    """Build Sidedoc table_metadata from Docling table data."""
    num_rows = table_data["num_rows"]
    num_cols = table_data["num_cols"]

    cells = []
    merged_cells = []

    for cell in table_data.get("table_cells", []):
        row = cell["start_row_offset_idx"]
        col = cell["start_col_offset_idx"]
        row_span = cell.get("row_span", 1)
        col_span = cell.get("col_span", 1)

        cells.append({
            "row": row,
            "col": col,
            "content_hash": _compute_content_hash(cell.get("text", "")),
        })

        if row_span > 1 or col_span > 1:
            merged_cells.append({
                "start_row": row,
                "start_col": col,
                "row_span": row_span,
                "col_span": col_span,
            })

    return {
        "rows": num_rows,
        "cols": num_cols,
        "cells": cells,
        "column_alignments": ["left"] * num_cols,
        "header_rows": _detect_header_rows(table_data),
        "merged_cells": merged_cells,
    }


def extract_pdf_document(
    pdf_path: str,
) -> tuple[list[Block], dict[str, bytes], list[SectionProperties]]:
    """Extract blocks, images, and sections from a PDF using Docling.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Tuple of (blocks, image_data, sections)
    """
    converter = DocumentConverter()
    result = converter.convert(pdf_path)
    doc = result.document

    # Get structured data for tables and pictures
    doc_dict = doc.export_to_dict()
    tables_data = doc_dict.get("tables", [])


    blocks: list[Block] = []
    image_data: dict[str, bytes] = {}
    table_idx = 0

    # Track markdown content position for content_start/content_end
    content_parts: list[str] = []
    current_offset = 0

    for item, _level in doc.iterate_items():
        item_type = type(item).__name__
        label = getattr(item, "label", "")

        # Skip furniture (headers, footers, page numbers)
        content_layer = getattr(item, "content_layer", "body")
        if content_layer == "furniture":
            continue

        block_index = len(blocks)

        if item_type == "SectionHeaderItem" and label == "section_header":
            doc_level = getattr(item, "level", 1) or 1
            text = getattr(item, "text", "")
            content = "#" * doc_level + " " + text
            block = Block(
                id=generate_block_id(block_index),
                type="heading",
                content=content,
                docx_paragraph_index=block_index,
                content_start=current_offset,
                content_end=current_offset + len(content),
                content_hash=_compute_content_hash(content),
                level=doc_level,
            )
            blocks.append(block)
            content_parts.append(content)
            current_offset += len(content) + 1  # +1 for newline join

        elif item_type == "TableItem" and label == "table":
            if table_idx < len(tables_data):
                tbl = tables_data[table_idx]
                tbl_data = tbl.get("data", {})
                content = _table_to_gfm(tbl_data)
                metadata = _build_table_metadata(tbl_data)
                metadata["docx_table_index"] = table_idx

                block = Block(
                    id=generate_block_id(block_index),
                    type="table",
                    content=content,
                    docx_paragraph_index=block_index,
                    content_start=current_offset,
                    content_end=current_offset + len(content),
                    content_hash=_compute_content_hash(content),
                    table_metadata=metadata,
                )
                blocks.append(block)
                content_parts.append(content)
                current_offset += len(content) + 1
                table_idx += 1

        elif item_type == "PictureItem" and label == "picture":
            # Image extraction not yet implemented — skip to avoid broken asset refs
            continue

        elif item_type == "TextItem":
            text = getattr(item, "text", "")
            if not text.strip():
                continue

            if label == "list_item":
                marker = getattr(item, "marker", "-")
                enumerated = getattr(item, "enumerated", False)
                if enumerated:
                    content = f"1. {text}"
                else:
                    content = f"- {text}"
                block_type = "list"
            elif label == "caption":
                content = f"*{text}*"
                block_type = "paragraph"
            else:
                content = text
                block_type = "paragraph"

            block = Block(
                id=generate_block_id(block_index),
                type=block_type,
                content=content,
                docx_paragraph_index=block_index,
                content_start=current_offset,
                content_end=current_offset + len(content),
                content_hash=_compute_content_hash(content),
            )
            blocks.append(block)
            content_parts.append(content)
            current_offset += len(content) + 1

    sections = [SectionProperties()]
    return blocks, image_data, sections


def extract_pdf_styles(
    pdf_path: str,
    blocks: list[Block],
) -> list[Style]:
    """Generate Style objects for PDF-sourced blocks.

    Uses sensible defaults since PDFs don't have named styles like DOCX.

    Args:
        pdf_path: Path to the PDF file (for future font extraction)
        blocks: List of Block objects from extraction

    Returns:
        List of Style objects, one per block
    """
    styles: list[Style] = []

    for block in blocks:
        if block.type == "heading":
            level = block.level or 1
            # Map heading levels to font sizes
            heading_sizes = {1: 24, 2: 18, 3: 14, 4: 12, 5: 11, 6: 10}
            font_size = heading_sizes.get(level, 12)
            style = Style(
                block_id=block.id,
                docx_style=f"Heading {level}",
                font_name="Helvetica",
                font_size=font_size,
                alignment="left",
                bold=True,
            )
        elif block.type == "table":
            style = Style(
                block_id=block.id,
                docx_style="Table Grid",
                font_name="Helvetica",
                font_size=11,
                alignment="left",
            )
        else:
            # Note: add "image" branch here when PictureItem extraction is implemented
            style = Style(
                block_id=block.id,
                docx_style="Normal",
                font_name="Helvetica",
                font_size=11,
                alignment="left",
            )

        styles.append(style)

    return styles
