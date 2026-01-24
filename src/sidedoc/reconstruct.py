"""Reconstruct Word documents from sidedoc format."""

import json
import re
import zipfile
import tempfile
from pathlib import Path
from typing import Any, Optional
from urllib.parse import unquote
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.document import Document as DocumentType
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import mistune
from sidedoc.models import Block, Style
from sidedoc.constants import DEFAULT_IMAGE_WIDTH_INCHES


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


def has_hyperlinks(content: str) -> bool:
    """Check if content contains markdown hyperlinks.

    Args:
        content: Text content to check

    Returns:
        True if hyperlinks are present
    """
    return bool(HYPERLINK_PATTERN.search(content))


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

            # Check for hyperlinks in heading
            if has_hyperlinks(text):
                para = doc.add_paragraph(style=style_name)
                add_text_with_hyperlinks(para, text)
            else:
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
