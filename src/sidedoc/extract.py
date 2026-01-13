"""Extract content from Word documents to sidedoc format."""

import hashlib
from pathlib import Path
from typing import Any
from docx import Document
from docx.shared import Pt
from sidedoc.models import Block, Style


def generate_block_id(index: int) -> str:
    """Generate a unique block ID.

    Args:
        index: Block index in document

    Returns:
        Unique block ID
    """
    return f"block-{index}"


def compute_content_hash(content: str) -> str:
    """Compute SHA256 hash of content.

    Args:
        content: Block content text

    Returns:
        Hex digest of content hash
    """
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def extract_inline_formatting(paragraph: Any) -> tuple[str, list[dict[str, Any]] | None]:
    """Extract inline formatting from paragraph runs.

    Args:
        paragraph: python-docx paragraph object

    Returns:
        Tuple of (markdown_content, inline_formatting_list)
        markdown_content has bold/italic converted to markdown
        inline_formatting_list records underline and other formatting
    """
    markdown_parts = []
    inline_formatting: list[dict[str, Any]] = []
    plain_text_position = 0  # Position in plain text without markdown markers

    for run in paragraph.runs:
        text = run.text
        if not text:
            continue

        is_bold = run.bold is True
        is_italic = run.italic is True
        is_underline = run.underline is True

        # Build markdown with bold/italic markers
        markdown_text = text
        if is_bold and is_italic:
            markdown_text = f"***{text}***"
        elif is_bold:
            markdown_text = f"**{text}**"
        elif is_italic:
            markdown_text = f"*{text}*"

        # Record underline in inline_formatting (positions are in plain text without markdown)
        if is_underline:
            inline_formatting.append({
                "type": "underline",
                "start": plain_text_position,
                "end": plain_text_position + len(text),
                "underline": True
            })

        markdown_parts.append(markdown_text)
        plain_text_position += len(text)  # Track plain text position, not markdown

    markdown_content = "".join(markdown_parts)
    return markdown_content, inline_formatting if inline_formatting else None


def extract_blocks(docx_path: str) -> list[Block]:
    """Extract blocks from a Word document.

    Converts paragraphs and headings to Block objects with markdown content.

    Args:
        docx_path: Path to .docx file

    Returns:
        List of Block objects
    """
    doc = Document(docx_path)
    blocks: list[Block] = []
    content_position = 0

    for para_index, paragraph in enumerate(doc.paragraphs):
        style_name = paragraph.style.name if paragraph.style else "Normal"

        # Extract inline formatting (bold, italic, underline)
        text_content, inline_formatting = extract_inline_formatting(paragraph)

        # Determine block type and content
        if style_name.startswith("Heading"):
            # Extract heading level (e.g., "Heading 1" -> 1)
            try:
                level = int(style_name.split()[-1])
            except (ValueError, IndexError):
                level = 1

            markdown_content = "#" * level + " " + text_content
            block_type = "heading"
        else:
            # Normal paragraph
            markdown_content = text_content
            block_type = "paragraph"
            level = None

        # Calculate content positions
        content_start = content_position
        content_end = content_position + len(markdown_content)

        # Create block
        block = Block(
            id=generate_block_id(para_index),
            type=block_type,
            content=markdown_content,
            docx_paragraph_index=para_index,
            content_start=content_start,
            content_end=content_end,
            content_hash=compute_content_hash(markdown_content),
            level=level,
            inline_formatting=inline_formatting
        )

        blocks.append(block)

        # Update position for next block (including newline)
        content_position = content_end + 1

    return blocks


def extract_styles(docx_path: str, blocks: list[Block]) -> list[Style]:
    """Extract style information from Word document.

    Args:
        docx_path: Path to .docx file
        blocks: List of Block objects

    Returns:
        List of Style objects
    """
    doc = Document(docx_path)
    styles: list[Style] = []

    for para_index, paragraph in enumerate(doc.paragraphs):
        if para_index >= len(blocks):
            break

        block = blocks[para_index]

        # Get font properties
        font_name = "Calibri"  # Default
        font_size = 11  # Default
        alignment = "left"  # Default

        if paragraph.style and paragraph.style.font.name:
            font_name = paragraph.style.font.name

        if paragraph.style and paragraph.style.font.size:
            font_size = int(paragraph.style.font.size.pt)

        # Get alignment
        if paragraph.alignment is not None:
            alignment_map = {
                0: "left",
                1: "center",
                2: "right",
                3: "justify",
            }
            alignment = alignment_map.get(paragraph.alignment, "left")

        # Create style
        style = Style(
            block_id=block.id,
            docx_style=paragraph.style.name if paragraph.style else "Normal",
            font_name=font_name,
            font_size=font_size,
            alignment=alignment,
        )

        styles.append(style)

    return styles


def blocks_to_markdown(blocks: list[Block]) -> str:
    """Convert blocks to markdown content.

    Args:
        blocks: List of Block objects

    Returns:
        Markdown content string
    """
    lines = [block.content for block in blocks]
    return "\n".join(lines)
