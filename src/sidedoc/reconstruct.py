"""Reconstruct Word documents from sidedoc format."""

import json
import zipfile
from pathlib import Path
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
import mistune
from sidedoc.models import Block, Style


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

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Detect headings
        if line.startswith("#"):
            level = 0
            while level < len(line) and line[level] == "#":
                level += 1

            content = line[level:].strip()
            block = Block(
                id=f"block-{block_id}",
                type="heading",
                content=line,
                docx_paragraph_index=block_id,
                content_start=content_position,
                content_end=content_position + len(line),
                content_hash="",
                level=level,
            )
        else:
            # Regular paragraph
            block = Block(
                id=f"block-{block_id}",
                type="paragraph",
                content=line,
                docx_paragraph_index=block_id,
                content_start=content_position,
                content_end=content_position + len(line),
                content_hash="",
            )

        blocks.append(block)
        block_id += 1
        content_position += len(line) + 1

    return blocks


def create_docx_from_blocks(blocks: list[Block], styles: dict) -> Document:
    """Create a Word document from Block objects.

    Args:
        blocks: List of Block objects
        styles: Style information dictionary

    Returns:
        Document object
    """
    doc = Document()

    for block in blocks:
        if block.type == "heading" and block.level:
            # Add heading with appropriate style
            style_name = f"Heading {block.level}"
            # Remove markdown markers
            text = block.content.lstrip("#").strip()
            para = doc.add_paragraph(text, style=style_name)
        elif block.type == "paragraph":
            para = doc.add_paragraph(block.content)
        else:
            # Default to paragraph for unknown types
            para = doc.add_paragraph(block.content)

        # Apply styling if available
        block_style = styles.get("block_styles", {}).get(block.id, {})
        if block_style:
            if "font_name" in block_style:
                para.style.font.name = block_style["font_name"]
            if "font_size" in block_style:
                para.style.font.size = Pt(block_style["font_size"])

            # Apply alignment
            alignment = block_style.get("alignment", "left")
            alignment_map = {
                "left": WD_ALIGN_PARAGRAPH.LEFT,
                "center": WD_ALIGN_PARAGRAPH.CENTER,
                "right": WD_ALIGN_PARAGRAPH.RIGHT,
                "justify": WD_ALIGN_PARAGRAPH.JUSTIFY,
            }
            if alignment in alignment_map:
                para.alignment = alignment_map[alignment]

    return doc


def build_docx_from_sidedoc(sidedoc_path: str, output_path: str) -> None:
    """Build a Word document from a sidedoc archive.

    Args:
        sidedoc_path: Path to .sidedoc file
        output_path: Path for output .docx file
    """
    with zipfile.ZipFile(sidedoc_path, "r") as zf:
        # Read content.md
        content_md = zf.read("content.md").decode("utf-8")

        # Read styles.json
        styles_data = json.loads(zf.read("styles.json").decode("utf-8"))

        # Read structure.json
        structure_data = json.loads(zf.read("structure.json").decode("utf-8"))

    # Parse markdown to blocks
    blocks = parse_markdown_to_blocks(content_md)

    # Create document
    doc = create_docx_from_blocks(blocks, styles_data)

    # Save document
    doc.save(output_path)
