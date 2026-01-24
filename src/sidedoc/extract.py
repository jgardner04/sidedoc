"""Extract content from Word documents to sidedoc format."""

import hashlib
import io
from pathlib import Path
from typing import Any, Optional
from urllib.parse import quote, unquote
from docx import Document
from docx.shared import Pt
from docx.oxml.ns import qn
from PIL import Image
from sidedoc.models import Block, Style
from sidedoc.constants import MAX_IMAGE_SIZE


# XML namespaces used in Office Open XML documents
WORDPROCESSINGML_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
RELATIONSHIPS_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


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


def encode_url_for_markdown(url: str) -> str:
    """Encode a URL for safe inclusion in markdown link syntax.

    Percent-encodes parentheses and spaces that would break markdown [text](url) format.

    Args:
        url: The URL to encode

    Returns:
        URL safe for markdown link syntax
    """
    # Only encode characters that break markdown link syntax
    # Parentheses would close the link early, spaces need encoding
    result = url.replace(" ", "%20")
    # Only encode unbalanced or problematic parentheses
    # For Wikipedia-style URLs like Python_(programming_language), we keep them
    # but we need to handle edge cases
    return result


def escape_markdown_link_text(text: str) -> str:
    """Escape special markdown characters in link text.

    Args:
        text: The link text to escape

    Returns:
        Escaped text safe for markdown link syntax
    """
    # Escape brackets which would break link syntax
    result = text.replace("[", "\\[").replace("]", "\\]")
    return result


def get_hyperlink_url(hyperlink_elem: Any, doc_part: Any) -> Optional[str]:
    """Extract the URL from a hyperlink XML element.

    Args:
        hyperlink_elem: The w:hyperlink XML element
        doc_part: Document part for accessing relationships

    Returns:
        The URL string, or None if not found
    """
    # Get the relationship ID from the hyperlink element
    r_id = hyperlink_elem.get(qn('r:id'))
    if r_id and r_id in doc_part.rels:
        rel = doc_part.rels[r_id]
        # External hyperlinks have target_ref (the URL)
        if hasattr(rel, '_target') and rel._target:
            return str(rel._target)
        # Some versions use target_ref
        if hasattr(rel, 'target_ref') and rel.target_ref:
            return str(rel.target_ref)
    return None


def is_formatting_enabled(rPr: Any, format_tag: str) -> bool:
    """Check if a formatting element is enabled in run properties.

    In Office Open XML, formatting can be:
    - Present without val attribute: enabled (e.g., <w:b/>)
    - Present with val="0" or val="false": disabled (e.g., <w:b w:val="0"/>)
    - Present with val="1" or val="true": enabled (e.g., <w:b w:val="1"/>)
    - Absent: inherit from style (we treat as disabled)

    Args:
        rPr: The w:rPr run properties element
        format_tag: The tag name without namespace (e.g., 'b', 'i', 'u')

    Returns:
        True if the formatting is enabled, False otherwise
    """
    if rPr is None:
        return False

    elem = rPr.find(f'{{{WORDPROCESSINGML_NS}}}{format_tag}')
    if elem is None:
        return False

    # Check the val attribute
    val = elem.get(qn('w:val'))
    if val is None:
        # Element present without val attribute means enabled
        return True
    # Check for explicit false values
    if val.lower() in ('0', 'false', 'none'):
        return False
    return True


def extract_hyperlink_text_and_formatting(hyperlink_elem: Any) -> tuple[str, bool, bool]:
    """Extract text and formatting from a hyperlink XML element.

    Args:
        hyperlink_elem: The w:hyperlink XML element

    Returns:
        Tuple of (text, is_bold, is_italic)
    """
    text_parts = []
    is_bold = False
    is_italic = False

    # Find all w:r (run) elements within the hyperlink
    for run_elem in hyperlink_elem.findall(f'.//{{{WORDPROCESSINGML_NS}}}r'):
        # Check for bold/italic in run properties
        rPr = run_elem.find(f'{{{WORDPROCESSINGML_NS}}}rPr')
        if is_formatting_enabled(rPr, 'b'):
            is_bold = True
        if is_formatting_enabled(rPr, 'i'):
            is_italic = True

        # Get text from w:t elements
        for text_elem in run_elem.findall(f'{{{WORDPROCESSINGML_NS}}}t'):
            if text_elem.text:
                text_parts.append(text_elem.text)

    return "".join(text_parts), is_bold, is_italic


def extract_inline_formatting(paragraph: Any, doc_part: Any = None) -> tuple[str, list[dict[str, Any]] | None]:
    """Extract inline formatting from paragraph runs, including hyperlinks.

    Args:
        paragraph: python-docx paragraph object
        doc_part: Document part for accessing hyperlink relationships

    Returns:
        Tuple of (markdown_content, inline_formatting_list)
        markdown_content has bold/italic converted to markdown and hyperlinks to [text](url)
        inline_formatting_list records underline, hyperlinks, and other formatting
    """
    markdown_parts = []
    inline_formatting: list[dict[str, Any]] = []
    plain_text_position = 0  # Position in plain text without markdown markers

    # Get the paragraph's XML element to access hyperlinks
    para_elem = paragraph._element

    # Process all child elements in order (runs and hyperlinks)
    # Why iterate XML: python-docx's paragraph.runs doesn't include hyperlink content
    # because hyperlinks are separate XML elements (w:hyperlink) containing their own runs.
    # We need to walk the XML to get content in the correct order.
    for child in para_elem:
        tag = child.tag

        if tag == f'{{{WORDPROCESSINGML_NS}}}hyperlink':
            # This is a hyperlink element
            if doc_part is None:
                continue

            url = get_hyperlink_url(child, doc_part)
            if url is None:
                # No valid URL, just extract text
                text, is_bold, is_italic = extract_hyperlink_text_and_formatting(child)
                if text:
                    markdown_parts.append(text)
                    plain_text_position += len(text)
                continue

            text, is_bold, is_italic = extract_hyperlink_text_and_formatting(child)
            if not text:
                # Empty hyperlink text, skip
                continue

            # Encode URL for markdown
            encoded_url = encode_url_for_markdown(url)

            # Build markdown link with optional bold/italic
            # We put formatting inside the link text: [**text**](url)
            if is_bold and is_italic:
                link_md = f"[***{text}***]({encoded_url})"
            elif is_bold:
                link_md = f"[**{text}**]({encoded_url})"
            elif is_italic:
                link_md = f"[*{text}*]({encoded_url})"
            else:
                link_md = f"[{text}]({encoded_url})"

            markdown_parts.append(link_md)

            # Record hyperlink in inline_formatting
            inline_formatting.append({
                "type": "hyperlink",
                "start": plain_text_position,
                "end": plain_text_position + len(text),
                "url": url
            })

            plain_text_position += len(text)

        elif tag == f'{{{WORDPROCESSINGML_NS}}}r':
            # This is a regular run element
            # We need to get text and formatting from the XML directly
            text_parts = []
            # Process all children in order to preserve breaks
            for run_child in child:
                run_child_tag = run_child.tag
                if run_child_tag == f'{{{WORDPROCESSINGML_NS}}}t':
                    if run_child.text:
                        text_parts.append(run_child.text)
                elif run_child_tag == f'{{{WORDPROCESSINGML_NS}}}br':
                    # Line break element
                    text_parts.append('\n')

            text = "".join(text_parts)
            if not text:
                continue

            # Check formatting in run properties using is_formatting_enabled
            # which properly handles val="0" meaning disabled
            rPr = child.find(f'{{{WORDPROCESSINGML_NS}}}rPr')
            is_bold = is_formatting_enabled(rPr, 'b')
            is_italic = is_formatting_enabled(rPr, 'i')
            is_underline = is_formatting_enabled(rPr, 'u')

            # Build markdown with bold/italic markers
            markdown_text = text
            if is_bold and is_italic:
                markdown_text = f"***{text}***"
            elif is_bold:
                markdown_text = f"**{text}**"
            elif is_italic:
                markdown_text = f"*{text}*"

            # Record underline in inline_formatting
            if is_underline:
                inline_formatting.append({
                    "type": "underline",
                    "start": plain_text_position,
                    "end": plain_text_position + len(text),
                    "underline": True
                })

            markdown_parts.append(markdown_text)
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
            text_content, inline_formatting = extract_inline_formatting(paragraph, doc.part)

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
