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
from sidedoc.models import Block, Style, TrackChange
from sidedoc.constants import (
    DEFAULT_IMAGE_WIDTH_INCHES,
    INSERTION_PATTERN,
    DELETION_PATTERN,
    SUBSTITUTION_PATTERN,
)


# Regex to match markdown hyperlinks: [text](url)
# The link text pattern handles escaped brackets (e.g., \[ and \]) by matching either:
# - any character except ] or \
# - OR a backslash followed by any character (which handles \[ and \])
HYPERLINK_PATTERN = re.compile(r'\[((?:[^\]\\]|\\.)*)\]\(([^)]+)\)')

# Word processing ML namespace
WORDPROCESSINGML_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

# XML namespace for preserving whitespace
XML_SPACE_NS = "{http://www.w3.org/XML/1998/namespace}space"

# Standard hyperlink color (blue)
HYPERLINK_COLOR = "0563C1"


def parse_criticmarkup(text: str) -> list[tuple[str, str]]:
    """Parse CriticMarkup syntax into segments.

    Identifies insertions {++text++}, deletions {--text--}, and substitutions {~~old~>new~~}
    in the text and returns a list of segments with their types.

    Args:
        text: Text that may contain CriticMarkup syntax

    Returns:
        List of (type, content) tuples where type is "text", "insertion", "deletion", or "substitution"
    """
    segments: list[tuple[str, str]] = []
    last_end = 0

    # Compile patterns
    ins_pattern = re.compile(INSERTION_PATTERN)
    del_pattern = re.compile(DELETION_PATTERN)
    sub_pattern = re.compile(SUBSTITUTION_PATTERN)

    # Find all matches with their positions
    all_matches: list[tuple[int, int, str, str, Optional[str]]] = []

    for match in ins_pattern.finditer(text):
        all_matches.append((match.start(), match.end(), "insertion", match.group(1), None))

    for match in del_pattern.finditer(text):
        all_matches.append((match.start(), match.end(), "deletion", match.group(1), None))

    for match in sub_pattern.finditer(text):
        # Substitution has two parts: old text and new text
        all_matches.append((match.start(), match.end(), "substitution", match.group(1), match.group(2)))

    # Sort by position
    all_matches.sort(key=lambda x: x[0])

    for start, end, match_type, content, new_content in all_matches:
        # Add any text before this match
        if start > last_end:
            segments.append(("text", text[last_end:start]))

        if match_type == "substitution":
            # Substitution expands to deletion followed by insertion
            segments.append(("deletion", content))
            if new_content:
                segments.append(("insertion", new_content))
        else:
            segments.append((match_type, content))

        last_end = end

    # Add remaining text after last match
    if last_end < len(text):
        segments.append(("text", text[last_end:]))

    # If no CriticMarkup was found, return the whole text as a single segment
    if not segments:
        segments.append(("text", text))

    return segments


def create_ins_element(text: str, author: str, date: str, revision_id: str) -> Any:
    """Create a w:ins XML element for track change insertion.

    Args:
        text: The inserted text
        author: Author who made the change
        date: ISO 8601 timestamp
        revision_id: Unique revision ID

    Returns:
        lxml Element representing the w:ins element
    """
    ins = OxmlElement("w:ins")
    ins.set(qn("w:id"), revision_id)
    ins.set(qn("w:author"), author)
    ins.set(qn("w:date"), date)

    # Create run inside insertion
    run = OxmlElement("w:r")
    ins.append(run)

    # Create text element
    t = OxmlElement("w:t")
    t.text = text
    t.set(XML_SPACE_NS, "preserve")
    run.append(t)

    return ins


def create_del_element(text: str, author: str, date: str, revision_id: str) -> Any:
    """Create a w:del XML element for track change deletion.

    Args:
        text: The deleted text
        author: Author who made the change
        date: ISO 8601 timestamp
        revision_id: Unique revision ID

    Returns:
        lxml Element representing the w:del element
    """
    del_elem = OxmlElement("w:del")
    del_elem.set(qn("w:id"), revision_id)
    del_elem.set(qn("w:author"), author)
    del_elem.set(qn("w:date"), date)

    # Create run inside deletion
    run = OxmlElement("w:r")
    del_elem.append(run)

    # Create delText element (not regular w:t)
    del_text = OxmlElement("w:delText")
    del_text.text = text
    del_text.set(XML_SPACE_NS, "preserve")
    run.append(del_text)

    return del_elem


def add_text_with_track_changes(
    paragraph: Any,
    content: str,
    track_changes: Optional[list[TrackChange]] = None,
    default_author: str = "Sidedoc AI",
    default_date: str = "",
) -> None:
    """Add text content with track changes to a paragraph.

    Parses CriticMarkup syntax and creates appropriate w:ins and w:del elements.
    If track_changes metadata is provided, uses those author/date values.

    Args:
        paragraph: python-docx Paragraph object
        content: Text content with CriticMarkup syntax
        track_changes: Optional list of TrackChange metadata
        default_author: Default author for new track changes
        default_date: Default date for new track changes
    """
    from datetime import datetime

    if not default_date:
        default_date = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    segments = parse_criticmarkup(content)

    # Create a mapping from track change content to metadata
    tc_lookup: dict[tuple[str, str], TrackChange] = {}
    if track_changes:
        for tc in track_changes:
            if tc.type == "deletion" and tc.deleted_text:
                tc_lookup[("deletion", tc.deleted_text)] = tc
            elif tc.type == "insertion":
                # For insertions, we need to figure out the text from position
                # This is approximate - we'll use the content between positions
                pass

    revision_counter = [1]  # Use list to allow modification in nested function

    def get_next_revision_id() -> str:
        rid = str(revision_counter[0])
        revision_counter[0] += 1
        return rid

    para_elem = paragraph._p

    for seg_type, seg_content in segments:
        if seg_type == "text":
            # Regular text - add as run
            if seg_content:
                run = OxmlElement("w:r")
                t = OxmlElement("w:t")
                t.text = seg_content
                t.set(XML_SPACE_NS, "preserve")
                run.append(t)
                para_elem.append(run)

        elif seg_type == "insertion":
            # Look up metadata or use defaults
            author = default_author
            date = default_date
            revision_id = get_next_revision_id()

            # Try to find matching track change
            if track_changes:
                for tc in track_changes:
                    if tc.type == "insertion":
                        author = tc.author
                        date = tc.date
                        revision_id = tc.revision_id or get_next_revision_id()
                        break

            ins_elem = create_ins_element(seg_content, author, date, revision_id)
            para_elem.append(ins_elem)

        elif seg_type == "deletion":
            # Look up metadata or use defaults
            author = default_author
            date = default_date
            revision_id = get_next_revision_id()

            # Try to find matching track change
            key = ("deletion", seg_content)
            if key in tc_lookup:
                tc = tc_lookup[key]
                author = tc.author
                date = tc.date
                revision_id = tc.revision_id or get_next_revision_id()
            elif track_changes:
                for tc in track_changes:
                    if tc.type == "deletion" and tc.deleted_text == seg_content:
                        author = tc.author
                        date = tc.date
                        revision_id = tc.revision_id or get_next_revision_id()
                        break

            del_elem = create_del_element(seg_content, author, date, revision_id)
            para_elem.append(del_elem)


def has_criticmarkup(content: str) -> bool:
    """Check if content contains CriticMarkup syntax.

    Args:
        content: Text content to check

    Returns:
        True if CriticMarkup is present
    """
    return bool(
        re.search(INSERTION_PATTERN, content)
        or re.search(DELETION_PATTERN, content)
        or re.search(SUBSTITUTION_PATTERN, content)
    )


def validate_criticmarkup(content: str) -> list[str]:
    """Validate CriticMarkup syntax and return any errors.

    Checks for:
    - Unclosed {++ (missing ++})
    - Unclosed {-- (missing --})
    - Malformed {~~ (missing ~> or ~~})

    Args:
        content: Text content to validate

    Returns:
        List of error messages (empty if no errors)
    """
    errors: list[str] = []
    lines = content.split('\n')

    for line_num, line in enumerate(lines, 1):
        # Check for unclosed insertions
        ins_opens = line.count('{++')
        ins_closes = len(re.findall(r'\+\+\}', line))
        if ins_opens > ins_closes:
            errors.append(f"Line {line_num}: Unclosed insertion {{++ (missing ++}})")

        # Check for unclosed deletions
        del_opens = line.count('{--')
        del_closes = len(re.findall(r'--\}', line))
        if del_opens > del_closes:
            errors.append(f"Line {line_num}: Unclosed deletion {{-- (missing --}})")

        # Check for malformed substitutions
        sub_opens = line.count('{~~')
        sub_closes = len(re.findall(r'~~\}', line))
        if sub_opens > sub_closes:
            errors.append(f"Line {line_num}: Unclosed substitution {{~~ (missing ~~}})")

        # Check for substitution missing ~> separator
        for match in re.finditer(r'\{~~([^~]*)~~\}', line):
            if '~>' not in match.group(1):
                errors.append(f"Line {line_num}: Malformed substitution (missing ~> separator)")

    return errors


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

            # Check for CriticMarkup first
            if has_criticmarkup(text):
                para = doc.add_paragraph(style=style_name)
                add_text_with_track_changes(para, text, block.track_changes)
            elif has_hyperlinks(text):
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
            # Check for CriticMarkup first
            if has_criticmarkup(block.content):
                para = doc.add_paragraph()
                add_text_with_track_changes(para, block.content, block.track_changes)
            elif has_hyperlinks(block.content):
                para = doc.add_paragraph()
                add_text_with_hyperlinks(para, block.content)
            else:
                para = doc.add_paragraph(block.content)
        else:
            # Default to paragraph for unknown types
            # Check for CriticMarkup first
            if has_criticmarkup(block.content):
                para = doc.add_paragraph()
                add_text_with_track_changes(para, block.content, block.track_changes)
            elif has_hyperlinks(block.content):
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

        # Enrich blocks with track changes data from structure.json
        structure_blocks = structure_data.get("blocks", [])
        for block, struct_block in zip(blocks, structure_blocks):
            # Transfer track changes if present
            if "track_changes" in struct_block and struct_block["track_changes"]:
                block.track_changes = [
                    TrackChange(
                        type=tc["type"],
                        start=tc["start"],
                        end=tc["end"],
                        author=tc["author"],
                        date=tc["date"],
                        revision_id=tc.get("revision_id", ""),
                        deleted_text=tc.get("deleted_text"),
                    )
                    for tc in struct_block["track_changes"]
                ]

        # Create document with assets directory
        doc = create_docx_from_blocks(blocks, styles_data, assets_dir)

        # Save document
        doc.save(output_path)
