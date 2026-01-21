"""Sync module for matching blocks and updating documents."""

import hashlib
import json
import tempfile
import zipfile
from pathlib import Path
from typing import Optional, Any
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
import mistune
from sidedoc.models import Block
from sidedoc.utils import get_iso_timestamp, compute_similarity

# Maximum size for individual assets (50MB) to prevent ZIP bomb attacks
MAX_ASSET_SIZE = 50 * 1024 * 1024  # 50MB in bytes

# Similarity threshold for matching blocks (0.0 to 1.0)
# Blocks at the same position must have at least this similarity to be considered edits
# Below this threshold, they are treated as delete + add operations
SIMILARITY_THRESHOLD = 0.7  # 70% similarity required


def match_blocks(
    old_blocks: list[Block], new_blocks: list[Block]
) -> dict[str, Block]:
    """Match old blocks to new blocks using hashes, positions, and similarity.

    Matching strategy:
    1. First pass: Match by content hash (unchanged blocks)
    2. Second pass: Match by type, position, and similarity threshold (edited blocks)
       - Blocks at the same position with the same type are only matched if
         their content similarity meets the SIMILARITY_THRESHOLD
       - This prevents incorrectly treating "delete + add" as "edit"

    Args:
        old_blocks: List of blocks from previous version (structure.json)
        new_blocks: List of blocks from edited content.md

    Returns:
        Dictionary mapping old block IDs to their corresponding new blocks.
        Unmatched old blocks indicate deletions.
        Unmatched new blocks indicate additions.
    """
    matches: dict[str, Block] = {}
    used_new_blocks: set[int] = set()

    # First pass: Match by content hash (unchanged blocks)
    for old_block in old_blocks:
        for i, new_block in enumerate(new_blocks):
            if i in used_new_blocks:
                continue
            if old_block.content_hash == new_block.content_hash:
                matches[old_block.id] = new_block
                used_new_blocks.add(i)
                break

    # Second pass: Match by type, position, and similarity (edited blocks)
    # This handles blocks that were edited but are at the exact same position
    # We only match if:
    # 1. Positions are identical
    # 2. Types match
    # 3. Content similarity meets threshold
    remaining_old = [b for b in old_blocks if b.id not in matches]
    remaining_new_indices = [
        i for i in range(len(new_blocks)) if i not in used_new_blocks
    ]

    for old_block in remaining_old:
        old_idx = old_blocks.index(old_block)

        # Only match if there's a new block at the exact same position with same type
        if old_idx in remaining_new_indices:
            new_block = new_blocks[old_idx]
            if old_block.type == new_block.type:
                # Check content similarity to distinguish edits from delete+add
                similarity = compute_similarity(old_block.content, new_block.content)
                if similarity >= SIMILARITY_THRESHOLD:
                    matches[old_block.id] = new_block
                    used_new_blocks.add(old_idx)
                    remaining_new_indices.remove(old_idx)

    return matches


def apply_inline_formatting(paragraph: Any, content: str) -> None:
    """Apply inline formatting from markdown to a paragraph.

    Uses mistune for robust markdown parsing to handle:
    - Nested formatting (**bold *italic* text**)
    - Escaped asterisks (\\*literal\\*)
    - Malformed markdown (graceful degradation)

    Args:
        paragraph: python-docx Paragraph object
        content: Text content with markdown formatting
    """
    # Parse the content to extract formatting runs
    runs = _parse_inline_markdown(content)

    # Apply each run to the paragraph
    if not runs:
        paragraph.add_run(content)
    else:
        for text, bold, italic in runs:
            run = paragraph.add_run(text)
            if bold:
                run.bold = True
            if italic:
                run.italic = True


def _parse_inline_markdown(content: str) -> list[tuple[str, bool, bool]]:
    """Parse inline markdown formatting using mistune.

    Returns a list of (text, is_bold, is_italic) tuples representing
    the text runs with their formatting.

    Args:
        content: Markdown text to parse

    Returns:
        List of tuples: (text, bold, italic)
    """
    # Create markdown parser that returns AST instead of HTML
    md = mistune.create_markdown(renderer=None)

    # Parse the content
    try:
        tokens, _ = md.parse(content)
    except Exception:
        # On parse error, return content as plain text (graceful degradation)
        return [(content, False, False)]

    # Extract inline content from paragraph tokens
    runs: list[tuple[str, bool, bool]] = []
    for block_token in tokens:
        if block_token.get("type") == "paragraph":
            children = block_token.get("children", [])
            _process_tokens(children, runs, bold=False, italic=False)
        else:
            # Handle other block types by extracting raw text
            raw = block_token.get("raw", "")
            if raw:
                runs.append((raw, False, False))

    return runs if runs else [(content, False, False)]


def _process_tokens(
    tokens: list[dict[str, Any]],
    runs: list[tuple[str, bool, bool]],
    bold: bool,
    italic: bool,
) -> None:
    """Recursively process mistune tokens into text runs.

    Args:
        tokens: List of mistune inline tokens
        runs: Output list to append runs to
        bold: Whether current context is bold
        italic: Whether current context is italic
    """
    for token in tokens:
        token_type = token.get("type", "")

        if token_type == "text":
            # Plain text - use current formatting state
            raw = token.get("raw", "")
            if raw:
                runs.append((raw, bold, italic))

        elif token_type == "strong":
            # Bold - recurse with bold=True
            children = token.get("children", [])
            _process_tokens(children, runs, bold=True, italic=italic)

        elif token_type == "emphasis":
            # Italic - recurse with italic=True
            children = token.get("children", [])
            _process_tokens(children, runs, bold=bold, italic=True)

        elif token_type == "codespan":
            # Inline code - treat as plain text
            raw = token.get("raw", "")
            if raw:
                runs.append((raw, bold, italic))

        elif token_type == "softbreak" or token_type == "linebreak":
            # Line breaks - add space or newline
            runs.append((" ", bold, italic))

        else:
            # Unknown token type - try to extract text/raw content
            # This handles escapes and other edge cases
            raw = token.get("raw", "")
            children = token.get("children", [])

            if children:
                _process_tokens(children, runs, bold, italic)
            elif raw:
                runs.append((raw, bold, italic))


def _create_reverse_mapping(matches: dict[str, Block]) -> dict[str, str]:
    """Create reverse mapping from new block IDs to old block IDs.

    Args:
        matches: Dictionary mapping old block IDs to new blocks

    Returns:
        Dictionary mapping new block IDs to old block IDs
    """
    new_to_old: dict[str, str] = {}
    for old_id, new_block in matches.items():
        new_to_old[new_block.id] = old_id
    return new_to_old


def _get_block_style(
    block: Block,
    new_to_old: dict[str, str],
    styles: dict[str, Any]
) -> dict[str, Any]:
    """Get the style for a block if it was matched to an old block.

    Args:
        block: The new block to get style for
        new_to_old: Mapping from new block IDs to old block IDs
        styles: Style information dictionary with block_styles

    Returns:
        Style dictionary for the block, or empty dict if no style
    """
    old_block_id = new_to_old.get(block.id)
    if old_block_id:
        return styles.get("block_styles", {}).get(old_block_id, {})
    return {}


def _create_paragraph_from_block(doc: Any, block: Block) -> Any:
    """Create a paragraph from a block based on its type.

    Args:
        doc: python-docx Document object
        block: Block to create paragraph from

    Returns:
        python-docx Paragraph object
    """
    if block.type == "heading" and block.level:
        text = block.content.lstrip("#").strip()
        style_name = f"Heading {block.level}"
        return doc.add_paragraph(text, style=style_name)
    elif block.type == "paragraph":
        if "**" in block.content or "*" in block.content:
            para = doc.add_paragraph()
            apply_inline_formatting(para, block.content)
            return para
        else:
            return doc.add_paragraph(block.content)
    else:
        return doc.add_paragraph(block.content)


def _apply_block_formatting(para: Any, block_style: dict[str, Any]) -> None:
    """Apply formatting from block_style to a paragraph.

    Args:
        para: python-docx Paragraph object
        block_style: Style dictionary with font_name, font_size, alignment
    """
    if not block_style:
        return

    if "font_name" in block_style and para.style:
        para.style.font.name = block_style["font_name"]
    if "font_size" in block_style and para.style:
        para.style.font.size = Pt(block_style["font_size"])

    alignment = block_style.get("alignment", "left")
    alignment_map = {
        "left": WD_ALIGN_PARAGRAPH.LEFT,
        "center": WD_ALIGN_PARAGRAPH.CENTER,
        "right": WD_ALIGN_PARAGRAPH.RIGHT,
        "justify": WD_ALIGN_PARAGRAPH.JUSTIFY,
    }
    if alignment in alignment_map:
        para.alignment = alignment_map[alignment]


def generate_updated_docx(
    new_blocks: list[Block],
    matches: dict[str, Block],
    styles: dict[str, Any],
    output_path: str,
) -> None:
    """Generate an updated docx file from new blocks.

    This function creates a new docx with content from new_blocks.
    - Matched blocks preserve their formatting from styles
    - New blocks receive default formatting based on type
    - Deleted blocks are omitted (not in new_blocks)
    - Inline formatting from markdown is applied

    Args:
        new_blocks: List of new Block objects from edited content.md
        matches: Dictionary mapping old block IDs to new blocks
        styles: Style information dictionary with block_styles
        output_path: Path where docx should be saved
    """
    doc = Document()
    new_to_old = _create_reverse_mapping(matches)

    for block in new_blocks:
        block_style = _get_block_style(block, new_to_old, styles)
        para = _create_paragraph_from_block(doc, block)
        _apply_block_formatting(para, block_style)

    doc.save(output_path)


def update_sidedoc_metadata(
    sidedoc_path: str,
    new_blocks: list[Block],
    new_content: str,
) -> None:
    """Update metadata files in sidedoc archive after sync.

    Regenerates structure.json and updates manifest.json, then repackages the archive.

    Args:
        sidedoc_path: Path to .sidedoc file
        new_blocks: Updated list of Block objects from edited content
        new_content: New markdown content
    """
    # Read existing files from archive
    with zipfile.ZipFile(sidedoc_path, "r") as zf:
        # Read styles.json (preserve it)
        styles_data = json.loads(zf.read("styles.json").decode("utf-8"))

        # Read old manifest to preserve some fields
        old_manifest = json.loads(zf.read("manifest.json").decode("utf-8"))

        # Collect any assets (images) to preserve
        assets = {}
        for file_info in zf.filelist:
            if file_info.filename.startswith("assets/"):
                # Validate asset size to prevent ZIP bomb attacks
                if file_info.file_size > MAX_ASSET_SIZE:
                    raise ValueError(
                        f"Asset '{file_info.filename}' exceeds maximum size "
                        f"({file_info.file_size} bytes > {MAX_ASSET_SIZE} bytes). "
                        "This may be a malicious ZIP bomb attack."
                    )
                assets[file_info.filename] = zf.read(file_info.filename)

    # Generate new structure.json
    structure_data = {
        "blocks": [
            {
                "id": block.id,
                "type": block.type,
                "docx_paragraph_index": block.docx_paragraph_index,
                "content_start": block.content_start,
                "content_end": block.content_end,
                "content_hash": block.content_hash,
                "level": block.level,
                "image_path": block.image_path,
                "inline_formatting": block.inline_formatting,
            }
            for block in new_blocks
        ]
    }

    # Compute new content hash
    content_hash = hashlib.sha256(new_content.encode()).hexdigest()

    # Update manifest.json
    manifest_data = {
        "sidedoc_version": old_manifest["sidedoc_version"],
        "created_at": old_manifest["created_at"],  # Preserve original
        "modified_at": get_iso_timestamp(),  # Update to now
        "source_file": old_manifest["source_file"],
        "source_hash": old_manifest["source_hash"],
        "content_hash": content_hash,  # Update with new hash
        "generator": old_manifest["generator"],
    }

    # Repackage archive with updated files
    # Write to temp file first, then replace original
    with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".sidedoc") as tmp:
        tmp_path = tmp.name

    try:
        with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zf:
            # Write updated content and metadata
            zf.writestr("content.md", new_content)
            zf.writestr("structure.json", json.dumps(structure_data, indent=2))
            zf.writestr("styles.json", json.dumps(styles_data, indent=2))
            zf.writestr("manifest.json", json.dumps(manifest_data, indent=2))

            # Preserve assets
            for asset_path, asset_data in assets.items():
                zf.writestr(asset_path, asset_data)

        # Replace original file with updated one
        Path(tmp_path).replace(sidedoc_path)
    except Exception:
        # Clean up temp file only if replace failed
        if Path(tmp_path).exists():
            Path(tmp_path).unlink()
        raise
