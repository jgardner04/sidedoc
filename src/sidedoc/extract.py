"""Extract content from Word documents to sidedoc format."""

import hashlib
import io
from pathlib import Path
from typing import Any, Optional
from urllib.parse import unquote
from docx import Document
from docx.shared import Pt
from docx.oxml.ns import qn
from PIL import Image
from sidedoc.models import Block, Style, TrackChange
from sidedoc.constants import (
    MAX_IMAGE_SIZE,
    MAX_TABLE_ROWS,
    MAX_TABLE_COLS,
    EMUS_PER_INCH,
    ALIGNMENT_NUMERIC_TO_STRING,
    GFM_ALIGNMENT_TO_SEPARATOR,
    DEFAULT_ALIGNMENT,
)


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
    # Encode characters that break markdown link syntax
    # Spaces need encoding
    result = url.replace(" ", "%20")
    # Parentheses MUST be encoded - they break markdown link syntax
    # [text](url_(with)_parens) is ambiguous: first ) closes the link
    result = result.replace("(", "%28")
    result = result.replace(")", "%29")
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


def detect_track_changes(docx_path: str) -> bool:
    """Detect whether a Word document contains track changes.

    Scans the document for any w:ins (insertion) or w:del (deletion) elements
    to determine if the document has revision tracking.

    Args:
        docx_path: Path to .docx file

    Returns:
        True if the document contains any track changes, False otherwise
    """
    doc = Document(docx_path)

    for paragraph in doc.paragraphs:
        para_elem = paragraph._element

        # Check for any insertion elements
        ins_elements = para_elem.findall(f'.//{{{WORDPROCESSINGML_NS}}}ins')
        if ins_elements:
            return True

        # Check for any deletion elements
        del_elements = para_elem.findall(f'.//{{{WORDPROCESSINGML_NS}}}del')
        if del_elements:
            return True

    return False


def extract_track_change_metadata(element: Any) -> tuple[str, str, str]:
    """Extract author, date, and revision_id from a track change element.

    Args:
        element: The w:ins or w:del XML element

    Returns:
        Tuple of (author, date, revision_id)
    """
    author = element.get(f'{{{WORDPROCESSINGML_NS}}}author') or ""
    date = element.get(f'{{{WORDPROCESSINGML_NS}}}date') or ""
    revision_id = element.get(f'{{{WORDPROCESSINGML_NS}}}id') or ""
    return author, date, revision_id


def extract_insertion_text(ins_element: Any) -> str:
    """Extract text content from a w:ins element.

    Args:
        ins_element: The w:ins XML element

    Returns:
        The inserted text
    """
    text_parts = []
    # Find all w:t elements within the insertion
    for text_elem in ins_element.findall(f'.//{{{WORDPROCESSINGML_NS}}}t'):
        if text_elem.text:
            text_parts.append(text_elem.text)
    return "".join(text_parts)


def extract_deletion_text(del_element: Any) -> str:
    """Extract text content from a w:del element.

    Args:
        del_element: The w:del XML element

    Returns:
        The deleted text
    """
    text_parts = []
    # Find all w:delText elements within the deletion
    for del_text_elem in del_element.findall(f'.//{{{WORDPROCESSINGML_NS}}}delText'):
        if del_text_elem.text:
            text_parts.append(del_text_elem.text)
    return "".join(text_parts)


def extract_paragraph_accept_all(
    para_elem: Any, doc_part: Any = None
) -> tuple[str, list[dict[str, Any]] | None, None]:
    """Extract content from a paragraph, accepting all track changes.

    When track changes are disabled (--no-track-changes), this function:
    - Includes insertion text as plain text (accepts insertions)
    - Excludes deletion text (accepts deletions, removing the text)
    - Handles regular runs and hyperlinks normally

    Args:
        para_elem: The paragraph's XML element
        doc_part: Document part for accessing hyperlink relationships

    Returns:
        Tuple of (markdown_content, inline_formatting, None)
        Note: track_changes is always None as we're accepting all changes
    """
    markdown_parts = []
    inline_formatting: list[dict[str, Any]] = []
    plain_text_position = 0

    for child in para_elem:
        tag = child.tag

        if tag == f'{{{WORDPROCESSINGML_NS}}}ins':
            # Accept insertion: include the text without CriticMarkup
            inserted_text = extract_insertion_text(child)
            if inserted_text:
                markdown_parts.append(inserted_text)
                plain_text_position += len(inserted_text)

        elif tag == f'{{{WORDPROCESSINGML_NS}}}del':
            # Accept deletion: skip the deleted text (don't include it)
            pass

        elif tag == f'{{{WORDPROCESSINGML_NS}}}hyperlink':
            if doc_part is None:
                continue

            url = get_hyperlink_url(child, doc_part)
            if url is None:
                text, is_bold, is_italic = extract_hyperlink_text_and_formatting(child)
                if text:
                    markdown_parts.append(text)
                    plain_text_position += len(text)
                continue

            text, is_bold, is_italic = extract_hyperlink_text_and_formatting(child)
            if not text:
                continue

            encoded_url = encode_url_for_markdown(url)
            escaped_text = escape_markdown_link_text(text)

            if is_bold and is_italic:
                link_md = f"[***{escaped_text}***]({encoded_url})"
            elif is_bold:
                link_md = f"[**{escaped_text}**]({encoded_url})"
            elif is_italic:
                link_md = f"[*{escaped_text}*]({encoded_url})"
            else:
                link_md = f"[{escaped_text}]({encoded_url})"

            markdown_parts.append(link_md)
            plain_text_position += len(text)

        elif tag == f'{{{WORDPROCESSINGML_NS}}}r':
            # Regular run
            text_parts = []
            for t_elem in child.findall(f'{{{WORDPROCESSINGML_NS}}}t'):
                if t_elem.text:
                    text_parts.append(t_elem.text)

            if text_parts:
                run_text = "".join(text_parts)
                markdown_parts.append(run_text)

                rPr = child.find(f'{{{WORDPROCESSINGML_NS}}}rPr')
                if rPr is not None:
                    is_bold = rPr.find(f'{{{WORDPROCESSINGML_NS}}}b') is not None
                    is_italic = rPr.find(f'{{{WORDPROCESSINGML_NS}}}i') is not None

                    if is_bold or is_italic:
                        inline_formatting.append({
                            'start': plain_text_position,
                            'end': plain_text_position + len(run_text),
                            'bold': is_bold,
                            'italic': is_italic,
                        })

                plain_text_position += len(run_text)

    markdown_content = "".join(markdown_parts)
    return (
        markdown_content,
        inline_formatting if inline_formatting else None,
        None  # No track changes when accepting all
    )


def extract_paragraph_with_track_changes(
    para_elem: Any, doc_part: Any = None
) -> tuple[str, list[dict[str, Any]] | None, list[TrackChange] | None]:
    """Extract content from a paragraph, including track changes as CriticMarkup.

    This function walks the paragraph XML and handles:
    - Regular runs (w:r)
    - Insertions (w:ins) -> converted to {++text++}
    - Deletions (w:del) -> converted to {--text--}
    - Hyperlinks (w:hyperlink)

    Args:
        para_elem: The paragraph's XML element
        doc_part: Document part for accessing hyperlink relationships

    Returns:
        Tuple of (markdown_content, inline_formatting, track_changes)
    """
    markdown_parts = []
    inline_formatting: list[dict[str, Any]] = []
    track_changes: list[TrackChange] = []
    plain_text_position = 0  # Position in plain text without CriticMarkup markers

    for child in para_elem:
        tag = child.tag

        if tag == f'{{{WORDPROCESSINGML_NS}}}ins':
            # This is an insertion element
            inserted_text = extract_insertion_text(child)
            if inserted_text:
                author, date, revision_id = extract_track_change_metadata(child)

                # Add CriticMarkup to markdown
                criticmarkup = f"{{++{inserted_text}++}}"
                markdown_parts.append(criticmarkup)

                # Record track change metadata
                track_changes.append(TrackChange(
                    type="insertion",
                    start=plain_text_position,
                    end=plain_text_position + len(inserted_text),
                    author=author,
                    date=date,
                    revision_id=revision_id,
                ))

                plain_text_position += len(inserted_text)

        elif tag == f'{{{WORDPROCESSINGML_NS}}}del':
            # This is a deletion element
            deleted_text = extract_deletion_text(child)
            if deleted_text:
                author, date, revision_id = extract_track_change_metadata(child)

                # Add CriticMarkup to markdown
                criticmarkup = f"{{--{deleted_text}--}}"
                markdown_parts.append(criticmarkup)

                # Record track change metadata
                track_changes.append(TrackChange(
                    type="deletion",
                    start=plain_text_position,
                    end=plain_text_position + len(deleted_text),
                    author=author,
                    date=date,
                    revision_id=revision_id,
                    deleted_text=deleted_text,
                ))

                # Note: For deletions, the text doesn't contribute to visible content position
                # But we include it in the CriticMarkup, so advance position
                plain_text_position += len(deleted_text)

        elif tag == f'{{{WORDPROCESSINGML_NS}}}hyperlink':
            # This is a hyperlink element - handle similarly to extract_inline_formatting
            if doc_part is None:
                continue

            url = get_hyperlink_url(child, doc_part)
            if url is None:
                text, is_bold, is_italic = extract_hyperlink_text_and_formatting(child)
                if text:
                    markdown_parts.append(text)
                    plain_text_position += len(text)
                continue

            text, is_bold, is_italic = extract_hyperlink_text_and_formatting(child)
            if not text:
                continue

            encoded_url = encode_url_for_markdown(url)
            escaped_text = escape_markdown_link_text(text)

            if is_bold and is_italic:
                link_md = f"[***{escaped_text}***]({encoded_url})"
            elif is_bold:
                link_md = f"[**{escaped_text}**]({encoded_url})"
            elif is_italic:
                link_md = f"[*{escaped_text}*]({encoded_url})"
            else:
                link_md = f"[{escaped_text}]({encoded_url})"

            markdown_parts.append(link_md)

            inline_formatting.append({
                "type": "hyperlink",
                "start": plain_text_position,
                "end": plain_text_position + len(text),
                "url": url
            })

            plain_text_position += len(text)

        elif tag == f'{{{WORDPROCESSINGML_NS}}}r':
            # This is a regular run element
            text_parts = []
            for run_child in child:
                run_child_tag = run_child.tag
                if run_child_tag == f'{{{WORDPROCESSINGML_NS}}}t':
                    if run_child.text:
                        text_parts.append(run_child.text)
                elif run_child_tag == f'{{{WORDPROCESSINGML_NS}}}br':
                    text_parts.append('\n')

            text = "".join(text_parts)
            if not text:
                continue

            rPr = child.find(f'{{{WORDPROCESSINGML_NS}}}rPr')
            is_bold = is_formatting_enabled(rPr, 'b')
            is_italic = is_formatting_enabled(rPr, 'i')
            is_underline = is_formatting_enabled(rPr, 'u')

            markdown_text = text
            if is_bold and is_italic:
                markdown_text = f"***{text}***"
            elif is_bold:
                markdown_text = f"**{text}**"
            elif is_italic:
                markdown_text = f"*{text}*"

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
    return (
        markdown_content,
        inline_formatting if inline_formatting else None,
        track_changes if track_changes else None
    )


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

            # Escape special characters in link text that would break markdown
            escaped_text = escape_markdown_link_text(text)

            # Build markdown link with optional bold/italic
            # We put formatting inside the link text: [**text**](url)
            if is_bold and is_italic:
                link_md = f"[***{escaped_text}***]({encoded_url})"
            elif is_bold:
                link_md = f"[**{escaped_text}**]({encoded_url})"
            elif is_italic:
                link_md = f"[*{escaped_text}*]({encoded_url})"
            else:
                link_md = f"[{escaped_text}]({encoded_url})"

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


def get_cell_alignment(cell: Any) -> str:
    """Extract horizontal alignment from a cell.

    Args:
        cell: python-docx cell object

    Returns:
        Alignment string: 'left', 'center', or 'right'
    """
    # Check if cell has paragraphs with alignment
    if cell.paragraphs:
        para = cell.paragraphs[0]
        if para.alignment is not None:
            # Note: GFM tables only support left/center/right, so we map
            # justify to left. This is different from ALIGNMENT_NUMERIC_TO_STRING.
            cell_alignment_map = {
                0: "left",      # WD_ALIGN_PARAGRAPH.LEFT
                1: "center",    # WD_ALIGN_PARAGRAPH.CENTER
                2: "right",     # WD_ALIGN_PARAGRAPH.RIGHT
                3: "left",      # WD_ALIGN_PARAGRAPH.JUSTIFY → left for GFM
            }
            return cell_alignment_map.get(para.alignment, DEFAULT_ALIGNMENT)

    return DEFAULT_ALIGNMENT


def get_column_alignments(table: Any) -> list[str]:
    """Extract column alignments from first row cells.

    Args:
        table: python-docx Table object

    Returns:
        List of alignment strings for each column
    """
    if not table.rows:
        return []

    alignments = []
    first_row = table.rows[0]
    for cell in first_row.cells:
        alignments.append(get_cell_alignment(cell))

    return alignments


def alignment_to_gfm_separator(alignment: str) -> str:
    """Convert alignment to GFM separator indicator.

    Args:
        alignment: 'left', 'center', or 'right'

    Returns:
        GFM alignment indicator like ':---', ':---:', or '---:'
    """
    return GFM_ALIGNMENT_TO_SEPARATOR.get(alignment, GFM_ALIGNMENT_TO_SEPARATOR[DEFAULT_ALIGNMENT])


def escape_cell_content_for_gfm(text: str) -> str:
    """Escape special characters in cell content for GFM table.

    Args:
        text: Cell text content

    Returns:
        Escaped text safe for GFM table cells
    """
    # Escape pipe characters that would break table syntax
    result = text.replace("|", "\\|")
    # Replace newlines with <br> or space (newlines break table rows)
    result = result.replace("\n", " ")
    return result


def table_to_gfm(table: Any) -> str:
    """Convert a python-docx table to GFM pipe table syntax.

    Args:
        table: python-docx Table object

    Returns:
        GFM pipe table markdown string
    """
    rows = []

    # Get column alignments
    alignments = get_column_alignments(table)

    for row_idx, row in enumerate(table.rows):
        cells = []
        for cell in row.cells:
            # Get cell text, stripping whitespace, and escape special characters
            cell_text = escape_cell_content_for_gfm(cell.text.strip())
            cells.append(cell_text)

        # Create pipe-separated row
        row_line = "| " + " | ".join(cells) + " |"
        rows.append(row_line)

        # Add separator row after header (first row)
        if row_idx == 0:
            # Create separator with alignment indicators
            separator_cells = []
            for i, _ in enumerate(cells):
                alignment = alignments[i] if i < len(alignments) else "left"
                separator_cells.append(alignment_to_gfm_separator(alignment))
            separator_line = "| " + " | ".join(separator_cells) + " |"
            rows.append(separator_line)

    return "\n".join(rows)


def extract_table_metadata(table: Any, table_index: int) -> dict[str, Any]:
    """Extract metadata from a table for storage in structure.json.

    Args:
        table: python-docx Table object
        table_index: Index of this table in the document

    Returns:
        Dictionary with table metadata including rows, cols, cells, column_alignments, and docx_table_index
    """
    num_rows = len(table.rows)
    num_cols = len(table.columns) if num_rows > 0 else 0

    # Validate table dimensions to prevent memory exhaustion
    if num_rows > MAX_TABLE_ROWS:
        raise ValueError(f"Table has too many rows ({num_rows}), maximum is {MAX_TABLE_ROWS}")
    if num_cols > MAX_TABLE_COLS:
        raise ValueError(f"Table has too many columns ({num_cols}), maximum is {MAX_TABLE_COLS}")

    # Build cells metadata - 2D array of cell info
    cells: list[list[dict[str, Any]]] = []

    for row_idx, row in enumerate(table.rows):
        row_cells: list[dict[str, Any]] = []
        for col_idx, cell in enumerate(row.cells):
            cell_text = cell.text.strip()
            cell_hash = compute_content_hash(cell_text)
            row_cells.append({
                "row": row_idx,
                "col": col_idx,
                "content_hash": cell_hash
            })
        cells.append(row_cells)

    # Extract column alignments
    column_alignments = get_column_alignments(table)

    return {
        "rows": num_rows,
        "cols": num_cols,
        "cells": cells,
        "column_alignments": column_alignments,
        "docx_table_index": table_index
    }


def _process_paragraph(
    paragraph: Any,
    doc_part: Any,
    block_index: int,
    para_index: int,
    content_position: int,
    image_counter: int,
    list_number_counter: int,
    previous_list_type: Optional[str],
    image_data: dict[str, bytes],
    extract_track_changes: bool = False,
    track_changes_explicit: Optional[bool] = None,
) -> tuple[Block, int, int, Optional[str], dict[str, bytes]]:
    """Process a single paragraph element.

    Args:
        paragraph: python-docx paragraph object
        doc_part: Document part for accessing relationships
        block_index: Index for generating block ID
        para_index: Paragraph index in document
        content_position: Current position in content stream
        image_counter: Counter for image numbering
        list_number_counter: Counter for numbered lists
        previous_list_type: Type of previous list item
        image_data: Dictionary to store image data
        extract_track_changes: Whether to extract track changes as CriticMarkup
        track_changes_explicit: The explicit track_changes parameter (None, True, or False)

    Returns:
        Tuple of (block, new_image_counter, new_list_counter, new_list_type, image_data)
    """
    style_name = paragraph.style.name if paragraph.style else "Normal"
    image_path = None
    block_track_changes = None

    image_info = extract_image_from_paragraph(paragraph, doc_part, image_counter)
    if image_info:
        # This is an image paragraph
        image_filename, image_extension, image_bytes, error_message = image_info

        if error_message:
            markdown_content = f"[Image {image_counter} skipped: {error_message}]"
            block_type = "paragraph"
            level_value = None
            inline_formatting = None
        else:
            image_path = f"assets/{image_filename}"
            markdown_content = f"![Image {image_counter}]({image_path})"
            block_type = "image"
            level_value = None
            inline_formatting = None
            image_data[image_filename] = image_bytes

        image_counter += 1
        list_number_counter = 0
        previous_list_type = None
    else:
        # Choose extraction function based on track changes mode
        if extract_track_changes:
            text_content, inline_formatting, block_track_changes = extract_paragraph_with_track_changes(
                paragraph._element, doc_part
            )
        elif track_changes_explicit is False:
            # Explicit --no-track-changes: accept all changes
            text_content, inline_formatting, block_track_changes = extract_paragraph_accept_all(
                paragraph._element, doc_part
            )
        else:
            # No track changes: use original extraction
            text_content, inline_formatting = extract_inline_formatting(paragraph, doc_part)

        if style_name.startswith("Heading"):
            try:
                level = int(style_name.split()[-1])
            except (ValueError, IndexError):
                level = 1
            markdown_content = "#" * level + " " + text_content
            block_type = "heading"
            level_value = level
            list_number_counter = 0
            previous_list_type = None
        elif style_name == "List Bullet":
            markdown_content = "- " + text_content
            block_type = "list"
            level_value = None
            if previous_list_type != "bullet":
                list_number_counter = 0
            previous_list_type = "bullet"
        elif style_name == "List Number":
            if previous_list_type != "number":
                list_number_counter = 0
            list_number_counter += 1
            markdown_content = f"{list_number_counter}. " + text_content
            block_type = "list"
            level_value = None
            previous_list_type = "number"
        else:
            markdown_content = text_content
            block_type = "paragraph"
            level_value = None
            list_number_counter = 0
            previous_list_type = None

    content_start = content_position
    content_end = content_position + len(markdown_content)

    block = Block(
        id=generate_block_id(block_index),
        type=block_type,
        content=markdown_content,
        docx_paragraph_index=para_index,
        content_start=content_start,
        content_end=content_end,
        content_hash=compute_content_hash(markdown_content),
        level=level_value,
        inline_formatting=inline_formatting,
        image_path=image_path,
        track_changes=block_track_changes,
    )

    return block, image_counter, list_number_counter, previous_list_type, image_data


def extract_blocks(
    docx_path: str,
    track_changes: Optional[bool] = None,
) -> tuple[list[Block], dict[str, bytes]]:
    """Extract blocks from a Word document.

    Converts paragraphs, headings, and tables to Block objects with markdown content.
    Processes the document body in order to correctly interleave paragraphs and tables.

    Args:
        docx_path: Path to .docx file
        track_changes: Track changes mode. If None, auto-detect based on document.
                      If True, extract track changes as CriticMarkup.
                      If False, accept all changes and extract plain text.

    Returns:
        Tuple of (blocks, image_data) where image_data maps filenames to image bytes
    """
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    doc = Document(docx_path)
    blocks: list[Block] = []
    image_data: dict[str, bytes] = {}
    content_position = 0
    list_number_counter = 0
    previous_list_type: Optional[str] = None
    image_counter = 1
    block_index = 0
    para_index = 0
    table_index = 0

    # Determine track changes mode
    # If not specified (None), auto-detect based on document content
    extract_track_changes = track_changes
    if extract_track_changes is None:
        extract_track_changes = detect_track_changes(docx_path)

    # Iterate over document body elements in order
    # This correctly interleaves paragraphs and tables
    body = doc.element.body
    for child in body:
        tag = child.tag.split('}')[-1]  # Get tag without namespace

        if tag == 'p':
            # Create a Paragraph object from the XML element
            paragraph = Paragraph(child, doc)

            block, image_counter, list_number_counter, previous_list_type, image_data = _process_paragraph(
                paragraph=paragraph,
                doc_part=doc.part,
                block_index=block_index,
                para_index=para_index,
                content_position=content_position,
                image_counter=image_counter,
                list_number_counter=list_number_counter,
                previous_list_type=previous_list_type,
                image_data=image_data,
                extract_track_changes=extract_track_changes,
                track_changes_explicit=track_changes,
            )

            blocks.append(block)
            content_position = block.content_end + 1
            block_index += 1
            para_index += 1

            # Reset list counters for non-list content
            if block.type not in ("list",):
                list_number_counter = 0
                previous_list_type = None

        elif tag == 'tbl':
            # Create a Table object from the XML element
            table = Table(child, doc)

            # Convert table to GFM markdown
            markdown_content = table_to_gfm(table)

            # Extract table metadata for structure.json
            table_metadata = extract_table_metadata(table, table_index)

            content_start = content_position
            content_end = content_position + len(markdown_content)

            block = Block(
                id=generate_block_id(block_index),
                type="table",
                content=markdown_content,
                docx_paragraph_index=-1,  # Tables don't have paragraph index
                content_start=content_start,
                content_end=content_end,
                content_hash=compute_content_hash(markdown_content),
                level=None,
                inline_formatting=None,
                image_path=None,
                table_metadata=table_metadata
            )

            blocks.append(block)
            content_position = content_end + 1
            block_index += 1
            table_index += 1

            # Reset list counters
            list_number_counter = 0
            previous_list_type = None

    return blocks, image_data


def extract_table_formatting(table: Any) -> dict[str, Any]:
    """Extract formatting information from a table.

    Args:
        table: python-docx Table object

    Returns:
        Dictionary with table formatting: column_widths, table_alignment, table_style
    """
    from docx.shared import Inches, Twips

    # Extract column widths
    column_widths: list[float] = []
    for col in table.columns:
        # Width is in EMUs (English Metric Units) or can be None
        width = col.width
        if width:
            # Convert to inches
            width_inches = width / EMUS_PER_INCH
            column_widths.append(round(width_inches, 2))
        else:
            # Default width if not specified
            column_widths.append(1.0)

    # Extract table alignment
    # Default is left
    table_alignment = "left"
    # python-docx doesn't have direct table alignment property
    # It's stored in the table's XML properties
    tblPr = table._tbl.tblPr
    if tblPr is not None:
        jc = tblPr.find(f'{{{WORDPROCESSINGML_NS}}}jc')
        if jc is not None:
            val = jc.get(qn('w:val'))
            if val:
                alignment_map = {
                    'left': 'left',
                    'center': 'center',
                    'right': 'right',
                    'start': 'left',
                    'end': 'right'
                }
                table_alignment = alignment_map.get(val, 'left')

    # Extract table style name if present
    table_style_name = None
    if table.style:
        table_style_name = table.style.name

    return {
        "column_widths": column_widths,
        "table_alignment": table_alignment,
        "table_style": table_style_name
    }


def extract_styles(docx_path: str, blocks: list[Block]) -> list[Style]:
    """Extract style information from Word document.

    Args:
        docx_path: Path to .docx file
        blocks: List of Block objects

    Returns:
        List of Style objects
    """
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    doc = Document(docx_path)
    styles: list[Style] = []

    # Create a mapping from block_id to block for quick lookup
    block_map = {block.id: block for block in blocks}

    # Iterate over document body in order to match blocks correctly
    body = doc.element.body
    block_index = 0

    for child in body:
        if block_index >= len(blocks):
            break

        tag = child.tag.split('}')[-1]
        block = blocks[block_index]

        if tag == 'p':
            paragraph = Paragraph(child, doc)

            # Get font properties
            font_name = "Calibri"
            font_size = 11
            alignment = "left"

            if paragraph.style and paragraph.style.font.name:
                font_name = paragraph.style.font.name

            if paragraph.style and paragraph.style.font.size:
                font_size = int(paragraph.style.font.size.pt)

            if paragraph.alignment is not None:
                alignment = ALIGNMENT_NUMERIC_TO_STRING.get(
                    paragraph.alignment, DEFAULT_ALIGNMENT
                )

            style = Style(
                block_id=block.id,
                docx_style=paragraph.style.name if paragraph.style else "Normal",
                font_name=font_name,
                font_size=font_size,
                alignment=alignment,
            )
            styles.append(style)
            block_index += 1

        elif tag == 'tbl':
            table = Table(child, doc)

            # Extract table-specific formatting
            table_formatting = extract_table_formatting(table)

            # Create style with table_formatting
            style = Style(
                block_id=block.id,
                docx_style="Table",
                font_name="Calibri",  # Default for tables
                font_size=11,
                alignment="left",
                table_formatting=table_formatting
            )
            styles.append(style)
            block_index += 1

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
