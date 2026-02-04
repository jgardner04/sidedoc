"""Reconstruct Word documents from sidedoc format."""

import json
import re
import zipfile
import tempfile
from pathlib import Path
from typing import Any, Optional
from urllib.parse import unquote
from docx import Document
from docx.shared import Pt, Inches
from docx.document import Document as DocumentType
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from sidedoc.models import Block, Style
from sidedoc.constants import (
    DEFAULT_IMAGE_WIDTH_INCHES,
    ALIGNMENT_STRING_TO_ENUM,
    GFM_SEPARATOR_PATTERNS,
    DEFAULT_ALIGNMENT,
)


# Regex to match markdown hyperlinks: [text](url)
# The link text pattern handles escaped brackets (e.g., \[ and \]) by matching either:
# - any character except ] or \
# - OR a backslash followed by any character (which handles \[ and \])
HYPERLINK_PATTERN = re.compile(r'\[((?:[^\]\\]|\\.)*)\]\(([^)]+)\)')

# Standard hyperlink color (blue)
HYPERLINK_COLOR = "0563C1"


def add_hyperlink_to_paragraph(
    paragraph: Any, text: str, url: str,
    bold: bool = False, italic: bool = False
) -> None:
    """Add a hyperlink to a paragraph.

    Creates a proper w:hyperlink element with the text and URL.

    Args:
        paragraph: python-docx Paragraph object
        text: Display text for the hyperlink
        url: URL the hyperlink points to
        bold: Whether the hyperlink text should be bold
        italic: Whether the hyperlink text should be italic
    """
    # Decode percent-encoded URLs for storage in relationship
    decoded_url = unquote(url)

    # Get the document part to create relationships
    part = paragraph.part

    # Create the relationship for the hyperlink
    r_id = part.relate_to(
        decoded_url,
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink",
        is_external=True
    )

    # Create the hyperlink element
    hyperlink = OxmlElement('w:hyperlink')
    hyperlink.set(qn('r:id'), r_id)

    # Create a run for the text
    run = OxmlElement('w:r')

    # Add run properties (hyperlink styling: blue color and underline)
    rPr = OxmlElement('w:rPr')

    color = OxmlElement('w:color')
    color.set(qn('w:val'), HYPERLINK_COLOR)
    rPr.append(color)

    underline = OxmlElement('w:u')
    underline.set(qn('w:val'), 'single')
    rPr.append(underline)

    # Add bold formatting if requested
    if bold:
        bold_elem = OxmlElement('w:b')
        rPr.append(bold_elem)

    # Add italic formatting if requested
    if italic:
        italic_elem = OxmlElement('w:i')
        rPr.append(italic_elem)

    run.append(rPr)

    # Add the text
    text_elem = OxmlElement('w:t')
    text_elem.text = text
    # Preserve spaces
    text_elem.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
    run.append(text_elem)

    # Add run to hyperlink
    hyperlink.append(run)

    # Add hyperlink to paragraph
    paragraph._p.append(hyperlink)


def parse_link_text_formatting(link_text: str) -> tuple[str, bool, bool]:
    """Parse formatting markers from link text.

    Handles markdown formatting markers like **bold**, *italic*, ***bold italic***.

    Args:
        link_text: The raw link text that may contain markdown formatting markers

    Returns:
        Tuple of (plain_text, is_bold, is_italic)
    """
    text = link_text
    is_bold = False
    is_italic = False

    # Check for bold+italic: ***text*** or ___text___
    if (text.startswith("***") and text.endswith("***") and len(text) > 6):
        text = text[3:-3]
        is_bold = True
        is_italic = True
    elif (text.startswith("___") and text.endswith("___") and len(text) > 6):
        text = text[3:-3]
        is_bold = True
        is_italic = True
    # Check for bold: **text** or __text__
    elif (text.startswith("**") and text.endswith("**") and len(text) > 4):
        text = text[2:-2]
        is_bold = True
    elif (text.startswith("__") and text.endswith("__") and len(text) > 4):
        text = text[2:-2]
        is_bold = True
    # Check for italic: *text* or _text_
    elif (text.startswith("*") and text.endswith("*") and len(text) > 2):
        text = text[1:-1]
        is_italic = True
    elif (text.startswith("_") and text.endswith("_") and len(text) > 2):
        text = text[1:-1]
        is_italic = True

    # Unescape brackets that were escaped during extraction
    text = text.replace("\\[", "[").replace("\\]", "]")

    return text, is_bold, is_italic


def add_text_with_hyperlinks(paragraph: Any, content: str) -> None:
    """Add text content to a paragraph, converting markdown hyperlinks.

    Parses [text](url) patterns and creates proper hyperlinks.
    Also handles formatting markers inside link text like [**bold**](url).

    Args:
        paragraph: python-docx Paragraph object
        content: Text content that may contain markdown hyperlinks
    """
    last_end = 0

    for match in HYPERLINK_PATTERN.finditer(content):
        # Add text before the hyperlink
        before_text = content[last_end:match.start()]
        if before_text:
            paragraph.add_run(before_text)

        # Get the link text and URL
        link_text = match.group(1)
        link_url = match.group(2)

        # Parse formatting from link text
        plain_text, is_bold, is_italic = parse_link_text_formatting(link_text)

        # Add the hyperlink with formatting
        add_hyperlink_to_paragraph(paragraph, plain_text, link_url, bold=is_bold, italic=is_italic)

        last_end = match.end()

    # Add any remaining text after the last hyperlink
    if last_end < len(content):
        paragraph.add_run(content[last_end:])


def parse_gfm_alignments(separator_line: str) -> list[str]:
    """Parse GFM alignment indicators from separator line.

    Args:
        separator_line: The separator line like "| --- | :---: | ---: |"

    Returns:
        List of alignments: 'left', 'center', or 'right' for each column
    """
    stripped = separator_line.strip()
    if not stripped:
        return []

    # Remove outer pipes if present
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]

    cells = [c.strip() for c in stripped.split("|")]
    alignments = []

    for cell in cells:
        cell = cell.strip()
        if not cell:
            continue

        # Detect alignment using GFM_SEPARATOR_PATTERNS
        starts_colon = cell.startswith(":")
        ends_colon = cell.endswith(":")

        detected = DEFAULT_ALIGNMENT
        for align, (expected_start, expected_end) in GFM_SEPARATOR_PATTERNS.items():
            if starts_colon == expected_start and ends_colon == expected_end:
                detected = align
                break
        alignments.append(detected)

    return alignments


def is_table_separator_line(line: str) -> bool:
    """Check if a line is a GFM table separator line.

    Separator lines have the format: | --- | --- | or |:---:|---:|
    """
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return False

    # Remove outer pipes and split by pipe
    inner = stripped[1:-1]
    cells = [c.strip() for c in inner.split("|")]

    if not cells:
        return False

    for cell in cells:
        # Each cell should be only dashes with optional colons for alignment
        cell = cell.strip()
        if not cell:
            continue
        # Remove alignment colons
        cell = cell.strip(":")
        # Should be only dashes
        if not cell or not all(c == "-" for c in cell):
            return False

    return True


def is_table_row(line: str) -> bool:
    """Check if a line could be a GFM table row (starts and ends with pipe)."""
    stripped = line.strip()
    return stripped.startswith("|") and stripped.endswith("|")


def parse_markdown_to_blocks(markdown_content: str) -> list[Block]:
    """Parse markdown content into Block objects.

    Args:
        markdown_content: Markdown text

    Returns:
        List of Block objects
    """
    blocks: list[Block] = []
    lines = markdown_content.split("\n")
    block_id = 0
    content_position = 0
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped_line = line.strip()

        if not stripped_line:
            i += 1
            continue

        # Check if this is the start of a GFM table
        # A table starts with a row that starts/ends with pipes
        # and is followed by a separator line
        if is_table_row(stripped_line) and i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            if is_table_separator_line(next_line):
                # This is a table! Collect all table lines
                table_lines = [stripped_line, next_line]
                j = i + 2
                while j < len(lines) and is_table_row(lines[j].strip()):
                    table_lines.append(lines[j].strip())
                    j += 1

                table_content = "\n".join(table_lines)

                # Parse table dimensions
                num_rows = len(table_lines) - 1  # Subtract separator row
                num_cols = len([c for c in stripped_line.split("|") if c.strip()])

                block = Block(
                    id=f"block-{block_id}",
                    type="table",
                    content=table_content,
                    docx_paragraph_index=-1,
                    content_start=content_position,
                    content_end=content_position + len(table_content),
                    content_hash="",
                    table_metadata={
                        "rows": num_rows,
                        "cols": num_cols,
                        "cells": [],
                        "docx_table_index": 0
                    }
                )
                blocks.append(block)
                block_id += 1
                content_position += len(table_content) + 1
                i = j
                continue

        # Handle other block types
        if stripped_line.startswith("![") and "](" in stripped_line and stripped_line.endswith(")"):
            # Extract image path from markdown
            start_idx = stripped_line.find("](") + 2
            end_idx = stripped_line.rfind(")")
            image_path = stripped_line[start_idx:end_idx]

            block = Block(
                id=f"block-{block_id}",
                type="image",
                content=stripped_line,
                docx_paragraph_index=block_id,
                content_start=content_position,
                content_end=content_position + len(stripped_line),
                content_hash="",
                image_path=image_path,
            )
        elif stripped_line.startswith("#"):
            level = 0
            while level < len(stripped_line) and stripped_line[level] == "#":
                level += 1

            block = Block(
                id=f"block-{block_id}",
                type="heading",
                content=stripped_line,
                docx_paragraph_index=block_id,
                content_start=content_position,
                content_end=content_position + len(stripped_line),
                content_hash="",
                level=level,
            )
        else:
            block = Block(
                id=f"block-{block_id}",
                type="paragraph",
                content=stripped_line,
                docx_paragraph_index=block_id,
                content_start=content_position,
                content_end=content_position + len(stripped_line),
                content_hash="",
            )

        blocks.append(block)
        block_id += 1
        content_position += len(stripped_line) + 1
        i += 1

    return blocks


def has_hyperlinks(content: str) -> bool:
    """Check if content contains markdown hyperlinks.

    Args:
        content: Text content to check

    Returns:
        True if hyperlinks are present
    """
    return bool(HYPERLINK_PATTERN.search(content))


def split_gfm_row(line: str) -> list[str]:
    """Split a GFM table row respecting escaped pipes.

    A naive split on '|' would incorrectly split cells containing escaped
    pipes (\\|). This function respects escape sequences.

    Args:
        line: A table row line like "| Name | Test\\|Pipe |"

    Returns:
        List of cell values with escaped characters unescaped
    """
    # Remove outer pipes if present
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]

    # Split respecting escaped pipes
    cells = []
    current: list[str] = []
    i = 0

    while i < len(stripped):
        # Check for escaped pipe
        if i < len(stripped) - 1 and stripped[i] == '\\' and stripped[i + 1] == '|':
            current.append('|')  # Unescape: \| becomes literal |
            i += 2
        elif stripped[i] == '|':
            # Unescaped pipe - cell boundary
            cells.append(''.join(current).strip())
            current = []
            i += 1
        else:
            current.append(stripped[i])
            i += 1

    # Don't forget the last cell
    cells.append(''.join(current).strip())

    return cells


def parse_gfm_table(table_content: str) -> tuple[list[list[str]], list[str]]:
    """Parse GFM table content into a 2D array of cell values and alignments.

    Args:
        table_content: GFM pipe table markdown

    Returns:
        Tuple of (rows, alignments) where rows is a list of rows and alignments
        is a list of column alignments
    """
    lines = table_content.strip().split("\n")
    rows: list[list[str]] = []
    alignments: list[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Check for separator row and extract alignments
        if is_table_separator_line(stripped):
            alignments = parse_gfm_alignments(stripped)
            continue

        # Parse row cells using proper escape-aware splitting
        cells = split_gfm_row(stripped)
        rows.append(cells)

    return rows, alignments


# Maximum table dimensions to prevent memory exhaustion from malicious input
MAX_TABLE_ROWS = 1000
MAX_TABLE_COLS = 100


def create_table_from_gfm(doc: DocumentType, table_content: str, styles: dict[str, Any], block_id: str) -> None:
    """Create a table in the document from GFM table content.

    Args:
        doc: Document object
        table_content: GFM pipe table markdown
        styles: Style information dictionary
        block_id: Block ID for looking up table styles

    Raises:
        ValueError: If table dimensions exceed reasonable limits
    """
    rows, alignments = parse_gfm_table(table_content)

    if not rows:
        return

    num_rows = len(rows)
    num_cols = max(len(row) for row in rows) if rows else 0

    if num_rows == 0 or num_cols == 0:
        return

    # Validate table dimensions to prevent memory exhaustion
    if num_rows > MAX_TABLE_ROWS:
        raise ValueError(f"Table has too many rows ({num_rows}), maximum is {MAX_TABLE_ROWS}")
    if num_cols > MAX_TABLE_COLS:
        raise ValueError(f"Table has too many columns ({num_cols}), maximum is {MAX_TABLE_COLS}")

    # Create the table
    table = doc.add_table(rows=num_rows, cols=num_cols)

    # Populate cells
    for row_idx, row_data in enumerate(rows):
        for col_idx, cell_text in enumerate(row_data):
            if col_idx < len(table.columns):
                cell = table.cell(row_idx, col_idx)
                cell.text = cell_text

                # Apply alignment to the cell's paragraph
                if alignments and col_idx < len(alignments):
                    alignment = alignments[col_idx]
                    if cell.paragraphs and alignment in ALIGNMENT_STRING_TO_ENUM:
                        cell.paragraphs[0].alignment = ALIGNMENT_STRING_TO_ENUM[alignment]

    # Apply column widths from styles if available
    block_style = styles.get("block_styles", {}).get(block_id, {})
    table_formatting = block_style.get("table_formatting", {})

    if table_formatting:
        column_widths = table_formatting.get("column_widths", [])
        for col_idx, width in enumerate(column_widths):
            if col_idx < len(table.columns):
                # Width is in inches, convert to EMUs
                table.columns[col_idx].width = Inches(width)


def create_docx_from_blocks(blocks: list[Block], styles: dict[str, Any], assets_dir: Optional[Path] = None) -> DocumentType:
    """Create a Word document from Block objects.

    Args:
        blocks: List of Block objects
        styles: Style information dictionary
        assets_dir: Optional path to assets directory for image files

    Returns:
        Document object
    """
    doc = Document()
    para = None  # Track current paragraph for styling

    for block in blocks:
        if block.type == "heading" and block.level:
            # Add heading with appropriate style
            style_name = f"Heading {block.level}"
            # Remove markdown markers
            text = block.content.lstrip("#").strip()

            # Check for hyperlinks in heading
            if has_hyperlinks(text):
                para = doc.add_paragraph(style=style_name)
                add_text_with_hyperlinks(para, text)
            else:
                para = doc.add_paragraph(text, style=style_name)
        elif block.type == "table":
            # Handle table blocks
            create_table_from_gfm(doc, block.content, styles, block.id)
            para = None  # Tables don't have paragraph styling
        elif block.type == "image":
            # Handle image blocks
            if block.image_path and assets_dir:
                # Extract filename from image_path (e.g., "assets/image1.png" -> "image1.png")
                image_filename = block.image_path.split("/")[-1]
                image_file_path = assets_dir / image_filename

                if image_file_path.exists():
                    # Add image to document
                    para = doc.add_paragraph()
                    run = para.add_run()
                    run.add_picture(str(image_file_path), width=Inches(DEFAULT_IMAGE_WIDTH_INCHES))
                else:
                    # Image file missing - add placeholder text
                    para = doc.add_paragraph(f"[Missing image: {block.image_path}]")
            else:
                # No assets directory or image_path - add placeholder
                para = doc.add_paragraph("[Image]")
        elif block.type == "paragraph":
            # Check for hyperlinks in paragraph
            if has_hyperlinks(block.content):
                para = doc.add_paragraph()
                add_text_with_hyperlinks(para, block.content)
            else:
                para = doc.add_paragraph(block.content)
        else:
            # Default to paragraph for unknown types
            # Check for hyperlinks
            if has_hyperlinks(block.content):
                para = doc.add_paragraph()
                add_text_with_hyperlinks(para, block.content)
            else:
                para = doc.add_paragraph(block.content)

        # Apply styling if available (only for paragraph-based blocks)
        if para is not None:
            block_style = styles.get("block_styles", {}).get(block.id, {})
            if block_style and para.style:
                if "font_name" in block_style:
                    para.style.font.name = block_style["font_name"]
                if "font_size" in block_style:
                    para.style.font.size = Pt(block_style["font_size"])

                # Apply alignment
                alignment = block_style.get("alignment", DEFAULT_ALIGNMENT)
                if alignment in ALIGNMENT_STRING_TO_ENUM:
                    para.alignment = ALIGNMENT_STRING_TO_ENUM[alignment]

    return doc


def build_docx_from_sidedoc(sidedoc_path: str, output_path: str) -> None:
    """Build a Word document from a sidedoc archive.

    Args:
        sidedoc_path: Path to .sidedoc file
        output_path: Path for output .docx file
    """
    # Create temporary directory for assets
    with tempfile.TemporaryDirectory() as temp_dir:
        assets_dir = Path(temp_dir) / "assets"
        assets_dir.mkdir(exist_ok=True)

        with zipfile.ZipFile(sidedoc_path, "r") as zip_file:
            # Read content.md
            content_md = zip_file.read("content.md").decode("utf-8")

            # Read styles.json
            styles_data = json.loads(zip_file.read("styles.json").decode("utf-8"))

            # Read structure.json
            structure_data = json.loads(zip_file.read("structure.json").decode("utf-8"))

            # Extract assets if they exist
            for file_info in zip_file.filelist:
                if file_info.filename.startswith("assets/"):
                    # Extract asset file
                    zip_file.extract(file_info, temp_dir)

        # Parse markdown to blocks
        blocks = parse_markdown_to_blocks(content_md)

        # Create document with assets directory
        doc = create_docx_from_blocks(blocks, styles_data, assets_dir)

        # Save document
        doc.save(output_path)
