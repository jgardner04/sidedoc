"""Package and unpackage sidedoc archives."""

import json
import zipfile
from pathlib import Path
from sidedoc.models import Block, Style, Manifest
from sidedoc.utils import compute_file_hash, get_iso_timestamp
from sidedoc import __version__


def block_to_structure_dict(block: Block) -> dict:
    """Convert a Block to its structure.json dictionary representation.

    Args:
        block: Block to serialize

    Returns:
        Dictionary suitable for structure.json
    """
    from dataclasses import asdict

    result = {
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
    }

    if block.chart_metadata is not None:
        result["chart_metadata"] = asdict(block.chart_metadata)
    if block.smartart_metadata is not None:
        result["smartart_metadata"] = asdict(block.smartart_metadata)
    if block.chart_parts_manifest is not None:
        result["chart_parts_manifest"] = asdict(block.chart_parts_manifest)

    return result


def _build_metadata(
    content_md: str,
    blocks: list[Block],
    styles: list[Style],
    source_file: str,
) -> tuple[dict, dict, dict]:
    """Build structure, styles, and manifest dicts from extraction data.

    Returns:
        Tuple of (structure_data, styles_data, manifest_data)
    """
    structure_data = {
        "blocks": [block_to_structure_dict(block) for block in blocks]
    }

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
) -> None:
    """Create a .sidedoc/.sdoc ZIP archive.

    Args:
        output_path: Output path for archive file
        content_md: Markdown content
        blocks: List of Block objects
        styles: List of Style objects
        source_file: Original source file path
        image_data: Optional dict mapping image filenames to image bytes
    """
    structure_data, styles_data, manifest_data = _build_metadata(
        content_md, blocks, styles, source_file
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
) -> None:
    """Create a .sidedoc directory.

    Args:
        output_path: Output path for directory
        content_md: Markdown content
        blocks: List of Block objects
        styles: List of Style objects
        source_file: Original source file path
        image_data: Optional dict mapping image filenames to image bytes
    """
    structure_data, styles_data, manifest_data = _build_metadata(
        content_md, blocks, styles, source_file
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
            file_path = assets_dir / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_bytes(image_bytes)
