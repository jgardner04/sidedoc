"""Reconstruct Word documents from sidedoc format."""

import json
import zipfile
import tempfile
from pathlib import Path
from typing import Any, Optional
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.document import Document as DocumentType
import mistune
from sidedoc.models import Block, Style
from sidedoc.constants import DEFAULT_IMAGE_WIDTH_INCHES


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

        if line.startswith("![") and "](" in line and line.endswith(")"):
            # Extract image path from markdown
            start_idx = line.find("](") + 2
            end_idx = line.rfind(")")
            image_path = line[start_idx:end_idx]

            block = Block(
                id=f"block-{block_id}",
                type="image",
                content=line,
                docx_paragraph_index=block_id,
                content_start=content_position,
                content_end=content_position + len(line),
                content_hash="",
                image_path=image_path,
            )
        elif line.startswith("#"):
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

    for block in blocks:
        if block.type == "heading" and block.level:
            # Add heading with appropriate style
            style_name = f"Heading {block.level}"
            # Remove markdown markers
            text = block.content.lstrip("#").strip()
            para = doc.add_paragraph(text, style=style_name)
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
            para = doc.add_paragraph(block.content)
        else:
            # Default to paragraph for unknown types
            para = doc.add_paragraph(block.content)

        # Apply styling if available
        block_style = styles.get("block_styles", {}).get(block.id, {})
        if block_style and para.style:
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
