"""Package and unpackage sidedoc archives."""

import json
import zipfile
from pathlib import Path
from sidedoc.models import Block, Style, Manifest
from sidedoc.utils import compute_file_hash, get_iso_timestamp
from sidedoc import __version__


def create_sidedoc_archive(
    output_path: str,
    content_md: str,
    blocks: list[Block],
    styles: list[Style],
    source_file: str,
    image_data: dict[str, bytes] | None = None,
) -> None:
    """Create a .sidedoc ZIP archive.

    Args:
        output_path: Output path for .sidedoc file
        content_md: Markdown content
        blocks: List of Block objects
        styles: List of Style objects
        source_file: Original source file path
        image_data: Optional dict mapping image filenames to image bytes
    """
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
            for block in blocks
        ]
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
        content_hash=content_hash,  # Will be updated after writing content.md
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

    # Create ZIP archive
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr("content.md", content_md)
        zip_file.writestr("structure.json", json.dumps(structure_data, indent=2))
        zip_file.writestr("styles.json", json.dumps(styles_data, indent=2))
        zip_file.writestr("manifest.json", json.dumps(manifest_data, indent=2))

        # Preserve image assets from the original document
        if image_data:
            for filename, image_bytes in image_data.items():
                zip_file.writestr(f"assets/{filename}", image_bytes)
