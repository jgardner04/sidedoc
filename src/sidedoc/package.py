"""Package and unpackage sidedoc archives."""

import json
import re
import zipfile
from pathlib import Path
from sidedoc.models import Block, SectionProperties, Style, Manifest
from sidedoc.utils import compute_file_hash, get_iso_timestamp
from sidedoc import __version__

# Known limitation: multi-line footnote definitions not supported.
# Only single-line [^N]: text definitions are captured; indented continuation
# lines (per Markdown spec) are silently dropped.
_FOOTNOTE_DEF_PATTERN = re.compile(r'^\[\^(\d+)\]:\s*(.+)$', re.MULTILINE)


def block_to_structure_dict(block: Block) -> dict:
    """Convert a Block to its structure.json dictionary representation.

    Args:
        block: Block to serialize

    Returns:
        Dictionary suitable for structure.json
    """
    return {
        "id": block.id,
        "type": block.type,
        "docx_paragraph_index": block.docx_paragraph_index,
        "content_start": block.content_start,
        "content_end": block.content_end,
        "content_hash": block.content_hash,
        "level": block.level,
        "image_path": block.image_path,
        "inline_formatting": block.inline_formatting,
        "table_metadata": block.table_metadata,
        "track_changes": [
            {
                "type": tc.type,
                "start": tc.start,
                "end": tc.end,
                "author": tc.author,
                "date": tc.date,
                "revision_id": tc.revision_id,
                "deleted_text": tc.deleted_text,
            }
            for tc in block.track_changes
        ] if block.track_changes else None,
        "footnote_references": block.footnote_references,
        "text_box_metadata": block.text_box_metadata,
    }


def _collect_footnotes_metadata(
    content_md: str, blocks: list[Block]
) -> dict[str, dict]:
    """Collect footnote/endnote metadata from blocks and content for structure.json.

    Returns:
        Dict mapping note_id string to {content, note_type, original_id}.
    """
    # Build note_type mapping from block references
    ref_info: dict[int, dict] = {}
    for block in blocks:
        if block.footnote_references:
            for ref in block.footnote_references:
                note_id = ref["note_id"]
                ref_info[note_id] = {
                    "note_type": ref.get("note_type", "footnote"),
                    "original_id": ref.get("original_id", str(note_id)),
                }

    if not ref_info:
        return {}

    # Parse definitions from content
    defs: dict[int, str] = {}
    for m in _FOOTNOTE_DEF_PATTERN.finditer(content_md):
        defs[int(m.group(1))] = m.group(2)

    result: dict[str, dict] = {}
    for note_id, info in ref_info.items():
        result[str(note_id)] = {
            "content": defs.get(note_id, ""),
            "note_type": info["note_type"],
            "original_id": info["original_id"],
        }
    return result


def section_to_structure_dict(section: SectionProperties) -> dict:
    """Convert a SectionProperties to its structure.json dictionary representation.

    Args:
        section: SectionProperties to serialize

    Returns:
        Dictionary suitable for structure.json sections array
    """
    result: dict = {
        "column_count": section.column_count,
        "column_spacing": section.column_spacing,
        "equal_width": section.equal_width,
        "start_block_index": section.start_block_index,
        "end_block_index": section.end_block_index,
    }
    if section.columns:
        result["columns"] = [
            {"width": col.width, "space": col.space}
            for col in section.columns
        ]
    return result


def _build_metadata(
    content_md: str,
    blocks: list[Block],
    styles: list[Style],
    source_file: str,
    sections: list[SectionProperties] | None = None,
) -> tuple[dict, dict, dict]:
    """Build structure, styles, and manifest dicts from extraction data.

    Returns:
        Tuple of (structure_data, styles_data, manifest_data)
    """
    structure_data: dict = {
        "blocks": [block_to_structure_dict(block) for block in blocks]
    }
    # Only include sections when there's a non-trivial layout (multi-column
    # or multi-section). A single default section with 1 column is omitted
    # to keep structure.json clean for simple documents.
    if sections and not (
        len(sections) == 1
        and sections[0].column_count == 1
        and sections[0].equal_width
    ):
        structure_data["sections"] = [
            section_to_structure_dict(s) for s in sections
        ]

    # Build top-level footnotes metadata from blocks and content
    footnotes_meta = _collect_footnotes_metadata(content_md, blocks)
    if footnotes_meta:
        structure_data["footnotes"] = footnotes_meta

    styles_data = {
        "block_styles": {
            style.block_id: {
                "docx_style": style.docx_style,
                "font_name": style.font_name,
                "font_size": style.font_size,
                "alignment": style.alignment,
                "bold": style.bold,
                "italic": style.italic,
                "underline": style.underline,
                "table_formatting": style.table_formatting,
            }
            for style in styles
        },
        "document_defaults": {
            "font_name": "Calibri",
            "font_size": 11,
        },
    }

    timestamp = get_iso_timestamp()
    content_hash = compute_file_hash(source_file)

    manifest = Manifest(
        sidedoc_version="1.0.0",
        created_at=timestamp,
        modified_at=timestamp,
        source_file=Path(source_file).name,
        source_hash=content_hash,
        content_hash=content_hash,
        generator=f"sidedoc-cli/{__version__}",
    )

    manifest_data = {
        "sidedoc_version": manifest.sidedoc_version,
        "created_at": manifest.created_at,
        "modified_at": manifest.modified_at,
        "source_file": manifest.source_file,
        "source_hash": manifest.source_hash,
        "content_hash": manifest.content_hash,
        "generator": manifest.generator,
    }

    return structure_data, styles_data, manifest_data


def create_sidedoc_archive(
    output_path: str,
    content_md: str,
    blocks: list[Block],
    styles: list[Style],
    source_file: str,
    image_data: dict[str, bytes] | None = None,
    sections: list[SectionProperties] | None = None,
) -> None:
    """Create a .sidedoc/.sdoc ZIP archive.

    Args:
        output_path: Output path for archive file
        content_md: Markdown content
        blocks: List of Block objects
        styles: List of Style objects
        source_file: Original source file path
        image_data: Optional dict mapping image filenames to image bytes
        sections: Optional list of SectionProperties for column layouts
    """
    structure_data, styles_data, manifest_data = _build_metadata(
        content_md, blocks, styles, source_file, sections
    )

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr("content.md", content_md)
        zip_file.writestr("structure.json", json.dumps(structure_data, indent=2))
        zip_file.writestr("styles.json", json.dumps(styles_data, indent=2))
        zip_file.writestr("manifest.json", json.dumps(manifest_data, indent=2))

        if image_data:
            for filename, image_bytes in image_data.items():
                zip_file.writestr(f"assets/{filename}", image_bytes)


def create_sidedoc_directory(
    output_path: str,
    content_md: str,
    blocks: list[Block],
    styles: list[Style],
    source_file: str,
    image_data: dict[str, bytes] | None = None,
    sections: list[SectionProperties] | None = None,
) -> None:
    """Create a .sidedoc directory.

    Args:
        output_path: Output path for directory
        content_md: Markdown content
        blocks: List of Block objects
        styles: List of Style objects
        source_file: Original source file path
        image_data: Optional dict mapping image filenames to image bytes
        sections: Optional list of SectionProperties for column layouts
    """
    structure_data, styles_data, manifest_data = _build_metadata(
        content_md, blocks, styles, source_file, sections
    )

    out = Path(output_path)
    out.mkdir(parents=True, exist_ok=True)

    (out / "content.md").write_text(content_md, encoding="utf-8")
    (out / "structure.json").write_text(json.dumps(structure_data, indent=2), encoding="utf-8")
    (out / "styles.json").write_text(json.dumps(styles_data, indent=2), encoding="utf-8")
    (out / "manifest.json").write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")

    if image_data:
        assets_dir = out / "assets"
        assets_dir.mkdir(exist_ok=True)
        for filename, image_bytes in image_data.items():
            (assets_dir / filename).write_bytes(image_bytes)
