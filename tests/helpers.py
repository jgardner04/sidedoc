"""Shared test helpers for sidedoc tests."""

import json
from pathlib import Path


def create_sidedoc_dir(path: Path, content_md: str, structure: dict,
                       styles: dict | None = None, manifest: dict | None = None) -> None:
    """Create a .sidedoc directory for testing.

    Args:
        path: Directory path to create
        content_md: Markdown content for content.md
        structure: Structure dict for structure.json
        styles: Optional styles dict (defaults to empty block_styles with Arial 11pt)
        manifest: Optional manifest dict (defaults to a complete test manifest)
    """
    path.mkdir(parents=True, exist_ok=True)
    (path / "content.md").write_text(content_md)
    (path / "structure.json").write_text(json.dumps(structure))
    (path / "styles.json").write_text(json.dumps(
        styles or {"block_styles": {}, "document_defaults": {"font_name": "Arial", "font_size": 11}}
    ))
    (path / "manifest.json").write_text(json.dumps(manifest or {
        "sidedoc_version": "1.0.0",
        "created_at": "2024-01-01T00:00:00+00:00",
        "modified_at": "2024-01-01T00:00:00+00:00",
        "source_file": "test.docx",
        "source_hash": "abc123",
        "content_hash": "old_hash",
        "generator": "sidedoc-cli/0.1.0",
    }))
