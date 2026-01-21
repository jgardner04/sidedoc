"""Extract content from Word documents to sidedoc format."""

import hashlib
import io
from pathlib import Path
from typing import Any, Optional
from docx import Document
from docx.shared import Pt
from PIL import Image
from sidedoc.models import Block, Style
from sidedoc.constants import MAX_IMAGE_SIZE


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


def validate_image(image_bytes: bytes, expected_extension: str) -> tuple[bool, str]:
    """Validate image size, format, and integrity.

    Args:
        image_bytes: Raw image data
        expected_extension: Expected file extension (e.g., 'png', 'jpg')

    Returns:
        Tuple of (is_valid, error_message). If valid, error_message is empty.
    """
    # Check size first - fastest validation, prevents processing huge files
    # Why check size: Protects against ZIP bombs and malicious documents with
    # extremely large embedded images that could cause memory issues
    if len(image_bytes) > MAX_IMAGE_SIZE:
        size_mb = len(image_bytes) / (1024 * 1024)
        max_mb = MAX_IMAGE_SIZE / (1024 * 1024)
        return False, f"Image exceeds maximum size ({size_mb:.1f}MB > {max_mb:.0f}MB)"

    # Validate image data and format using PIL
    try:
        # First pass: verify image integrity
        # Why verify: Detects corrupted or malicious image data before we try to
        # process it further. This prevents crashes from malformed images.
        # Note: We must load the image twice because PIL's verify() method makes
        # the image object unusable for further operations. This is a known PIL
        # limitation. For large images near the 10MB limit, this doubles memory
        # usage temporarily, but it's necessary to ensure both integrity and
        # format validation.
        img = Image.open(io.BytesIO(image_bytes))
        img.verify()  # Verify that it's a valid image

        # Second pass: reopen to check format (verify() makes the image unusable)
        # Why check format: Detects extension spoofing (e.g., malware.exe renamed
        # to image.png). We verify the actual image format matches the extension.
        img = Image.open(io.BytesIO(image_bytes))

        # Map extensions to PIL formats
        # Why mapping: PIL uses format names like "JPEG" while file extensions are
        # "jpg" or "jpeg". We need to normalize for comparison.
        extension_to_format = {
            'png': 'PNG',
            'jpg': 'JPEG',
            'jpeg': 'JPEG',
            'gif': 'GIF',
            'bmp': 'BMP',
            'tiff': 'TIFF',
            'tif': 'TIFF',
        }

        expected_format = extension_to_format.get(expected_extension.lower())
        if expected_format and img.format != expected_format:
            return False, f"Image format mismatch (extension: {expected_extension}, actual: {img.format})"

        return True, ""

    except (Image.UnidentifiedImageError, OSError, ValueError) as e:
        # UnidentifiedImageError: PIL cannot identify the image format
        # OSError: File-related errors (truncated file, etc.)
        # ValueError: Invalid image data
        # Why catch these: Documents may contain corrupted images or non-image data
        # embedded as images. We want to skip these gracefully with an error message
        # rather than crash the entire extraction.
        return False, f"Invalid or corrupted image data: {str(e)}"


def extract_image_from_paragraph(paragraph: Any, doc_part: Any, image_counter: int) -> Optional[tuple[str, str, bytes, str]]:
    """Check if paragraph contains an image and extract it.

    Args:
        paragraph: python-docx paragraph object
        doc_part: Document part for accessing relationships
        image_counter: Counter for generating unique image names

    Returns:
        Tuple of (image_filename, image_extension, image_bytes, error_message) if image found.
        If image is valid, error_message is empty. If invalid, error_message contains the reason.
        Returns None if no image found.
    """
    # Check for drawing elements (images) in paragraph runs
    # Why check runs: Word documents store images inside run elements within paragraphs.
    # A paragraph may have multiple runs, and any of them could contain an image.
    for run in paragraph.runs:
        # Navigate XML structure to find drawing elements
        # Why XML namespaces: Word documents use Office Open XML format with specific
        # namespaces. We need the full namespace URI to find elements correctly.
        drawing_elems = run._element.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}drawing')
        for drawing in drawing_elems:
            # Find blip element (contains image reference)
            # Why blip: In Office Open XML, a "blip" (binary large image or picture)
            # element contains the relationship ID pointing to the actual image data.
            blips = drawing.findall('.//{http://schemas.openxmlformats.org/drawingml/2006/main}blip')
            for blip in blips:
                # Get relationship ID that points to the image part
                # Why r:embed: Images aren't stored inline - they're stored as separate
                # "parts" in the ZIP archive, referenced via relationship IDs.
                r_embed = blip.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
                if r_embed and r_embed in doc_part.rels:
                    # Get image part using the relationship ID
                    # Why relationships: This is how Office Open XML connects elements
                    # to their binary data. The relationship maps ID -> actual image.
                    image_part = doc_part.rels[r_embed].target_part
                    # Get extension from content type or part name
                    extension = image_part.partname.split('.')[-1]
                    # Get image bytes (the actual binary image data)
                    image_bytes = image_part.blob

                    # Validate image before including it in the sidedoc
                    # Why validate: Protects against corrupted images, format mismatches,
                    # and security issues like ZIP bombs or format spoofing
                    is_valid, error_message = validate_image(image_bytes, extension)

                    # Generate unique filename
                    # Why counter: Multiple images in a document need unique filenames
                    # in the assets/ directory to avoid collisions
                    image_filename = f"image{image_counter}.{extension}"

                    # Return image data with validation result
                    # Why return error_message even if invalid: The caller decides how to
                    # handle invalid images (skip, show error message, etc.)
                    return (image_filename, extension, image_bytes, error_message)

    return None


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

    # Process each run (formatted text segment) in the paragraph
    # Why runs: Word stores formatting at the "run" level - each run is a segment
    # of text with consistent formatting. A paragraph with "Hello **world**" has
    # two runs: one for "Hello " and one for "world" with bold formatting.
    for run in paragraph.runs:
        text = run.text
        if not text:
            continue

        # Extract formatting flags from the run
        # Why check "is True": python-docx returns None for unset properties, False
        # for explicitly disabled, and True for enabled. We only want explicit True.
        is_bold = run.bold is True
        is_italic = run.italic is True
        is_underline = run.underline is True

        # Build markdown with bold/italic markers
        # Why markdown: Bold and italic are well-supported in markdown, so we convert
        # them to markdown syntax for AI-friendly editing.
        markdown_text = text
        if is_bold and is_italic:
            markdown_text = f"***{text}***"
        elif is_bold:
            markdown_text = f"**{text}**"
        elif is_italic:
            markdown_text = f"*{text}*"

        # Record underline in inline_formatting (positions are in plain text without markdown)
        # Why separate: Markdown doesn't have standard underline syntax, so we store
        # it separately in inline_formatting with character positions. The positions
        # refer to the plain text (without ** or * markers) so they remain valid
        # when we convert markdown back to docx.
        if is_underline:
            inline_formatting.append({
                "type": "underline",
                "start": plain_text_position,
                "end": plain_text_position + len(text),
                "underline": True
            })

        markdown_parts.append(markdown_text)
        # Track plain text position, not markdown position
        # Why plain text: The inline_formatting positions need to match the text
        # without markdown markers, so we only count the actual text length
        plain_text_position += len(text)

    markdown_content = "".join(markdown_parts)
    return markdown_content, inline_formatting if inline_formatting else None


def extract_blocks(docx_path: str) -> tuple[list[Block], dict[str, bytes]]:
    """Extract blocks from a Word document.

    Converts paragraphs and headings to Block objects with markdown content.

    Args:
        docx_path: Path to .docx file

    Returns:
        Tuple of (blocks, image_data) where image_data maps filenames to image bytes
    """
    doc = Document(docx_path)
    blocks: list[Block] = []
    image_data: dict[str, bytes] = {}  # Map image filenames to image bytes
    content_position = 0
    list_number_counter = 0  # Track numbered list position
    previous_list_type = None  # Track list type changes
    image_counter = 1  # Track image numbering

    for para_index, paragraph in enumerate(doc.paragraphs):
        style_name = paragraph.style.name if paragraph.style else "Normal"
        image_path = None  # Initialize for all paragraphs

        image_info = extract_image_from_paragraph(paragraph, doc.part, image_counter)
        if image_info:
            # This is an image paragraph
            image_filename, image_extension, image_bytes, error_message = image_info

            if error_message:
                # Image validation failed - create a paragraph with error message
                markdown_content = f"[Image {image_counter} skipped: {error_message}]"
                block_type = "paragraph"
                level_value = None
                inline_formatting = None
                # Don't store invalid image data
            else:
                # Image is valid
                image_path = f"assets/{image_filename}"
                markdown_content = f"![Image {image_counter}]({image_path})"
                block_type = "image"
                level_value = None
                inline_formatting = None
                # Store image data
                image_data[image_filename] = image_bytes

            # Increment counter for both valid and invalid images to maintain consistent numbering
            image_counter += 1

            # Reset list counters
            list_number_counter = 0
            previous_list_type = None
        else:
            text_content, inline_formatting = extract_inline_formatting(paragraph)

            if style_name.startswith("Heading"):
                # Extract heading level (e.g., "Heading 1" -> 1)
                try:
                    level = int(style_name.split()[-1])
                except (ValueError, IndexError):
                    level = 1

                markdown_content = "#" * level + " " + text_content
                block_type = "heading"
                level_value = level
                # Reset list counter when encountering non-list content
                list_number_counter = 0
                previous_list_type = None
            elif style_name == "List Bullet":
                # Bulleted list item
                markdown_content = "- " + text_content
                block_type = "list"
                level_value = None
                # Reset numbered list counter when switching to bullets
                if previous_list_type != "bullet":
                    list_number_counter = 0
                previous_list_type = "bullet"
            elif style_name == "List Number":
                # Numbered list item
                # Reset counter when switching from bullets or starting new list
                if previous_list_type != "number":
                    list_number_counter = 0
                list_number_counter += 1
                markdown_content = f"{list_number_counter}. " + text_content
                block_type = "list"
                level_value = None
                previous_list_type = "number"
            else:
                # Normal paragraph
                markdown_content = text_content
                block_type = "paragraph"
                level_value = None
                # Reset list counter when encountering non-list content
                list_number_counter = 0
                previous_list_type = None

        content_start = content_position
        content_end = content_position + len(markdown_content)

        block = Block(
            id=generate_block_id(para_index),
            type=block_type,
            content=markdown_content,
            docx_paragraph_index=para_index,
            content_start=content_start,
            content_end=content_end,
            content_hash=compute_content_hash(markdown_content),
            level=level_value,
            inline_formatting=inline_formatting,
            image_path=image_path
        )

        blocks.append(block)
        content_position = content_end + 1

    return blocks, image_data


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
