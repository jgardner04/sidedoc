"""Sync module for matching blocks and updating documents."""

import hashlib
import json
import re
import tempfile
import zipfile
from pathlib import Path
from typing import Optional, Any
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from sidedoc.models import Block
from sidedoc.utils import get_iso_timestamp


def match_blocks(
    old_blocks: list[Block], new_blocks: list[Block]
) -> dict[str, Block]:
    """Match old blocks to new blocks using hashes and positions.

    Matching strategy:
    1. First pass: Match by content hash (unchanged blocks)
    2. Second pass: Match by type and position (edited blocks)

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

    # Second pass: Match by type and exact position (edited blocks)
    # This handles blocks that were edited but are at the exact same position
    # We only match if the positions are identical to avoid false matches
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
                matches[old_block.id] = new_block
                used_new_blocks.add(old_idx)
                remaining_new_indices.remove(old_idx)

    return matches


def apply_inline_formatting(paragraph: Any, content: str) -> None:
    """Apply inline formatting from markdown to a paragraph.

    Parses markdown formatting (bold, italic) and creates runs with appropriate formatting.

    Args:
        paragraph: python-docx Paragraph object
        content: Text content with markdown formatting
    """
    # Pattern to match **bold**, *italic*, and plain text
    # This is a simplified implementation - full markdown parsing would be more complex
    parts = []
    current_pos = 0

    # Match **bold**
    for match in re.finditer(r'\*\*([^*]+)\*\*', content):
        # Add plain text before bold
        if match.start() > current_pos:
            parts.append(("plain", content[current_pos:match.start()]))
        parts.append(("bold", match.group(1)))
        current_pos = match.end()

    # Add remaining text
    if current_pos < len(content):
        remaining = content[current_pos:]
        # Now check for *italic* in remaining
        parts.extend(_parse_italic(remaining))
    else:
        # Check for italic in the parts we already have
        new_parts = []
        for style, text in parts:
            if style == "plain":
                new_parts.extend(_parse_italic(text))
            else:
                new_parts.append((style, text))
        parts = new_parts

    # Apply formatting to runs
    if not parts:
        paragraph.add_run(content)
    else:
        for style, text in parts:
            run = paragraph.add_run(text)
            if style == "bold":
                run.bold = True
            elif style == "italic":
                run.italic = True
            elif style == "bold_italic":
                run.bold = True
                run.italic = True


def _parse_italic(text: str) -> list[tuple[str, str]]:
    """Parse italic formatting from text."""
    parts = []
    current_pos = 0

    for match in re.finditer(r'\*([^*]+)\*', text):
        if match.start() > current_pos:
            parts.append(("plain", text[current_pos:match.start()]))
        parts.append(("italic", match.group(1)))
        current_pos = match.end()

    if current_pos < len(text):
        parts.append(("plain", text[current_pos:]))

    return parts if parts else [("plain", text)]


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

    # Create reverse mapping: new block -> old block ID (for style lookup)
    new_to_old: dict[str, str] = {}
    for old_id, new_block in matches.items():
        new_to_old[new_block.id] = old_id

    for block in new_blocks:
        # Determine which style to use
        old_block_id = new_to_old.get(block.id)
        block_style = {}
        if old_block_id:
            # Matched block - use its old style
            block_style = styles.get("block_styles", {}).get(old_block_id, {})

        # Create paragraph based on block type
        if block.type == "heading" and block.level:
            # Remove markdown markers from heading
            text = block.content.lstrip("#").strip()
            style_name = f"Heading {block.level}"
            para = doc.add_paragraph(text, style=style_name)
        elif block.type == "paragraph":
            # Check if content has inline formatting
            if "**" in block.content or "*" in block.content:
                para = doc.add_paragraph()
                apply_inline_formatting(para, block.content)
            else:
                para = doc.add_paragraph(block.content)
        else:
            # Default to paragraph for other types
            para = doc.add_paragraph(block.content)

        # Apply formatting if available
        if block_style:
            if "font_name" in block_style and para.style:
                para.style.font.name = block_style["font_name"]
            if "font_size" in block_style and para.style:
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

    # Save document
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
    finally:
        # Clean up temp file if it still exists
        if Path(tmp_path).exists():
            Path(tmp_path).unlink()
