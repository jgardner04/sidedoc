"""Tests for sidedoc diff command."""

import json
import tempfile
import zipfile
from pathlib import Path
from click.testing import CliRunner
from sidedoc.cli import main


def test_diff_command_shows_added_blocks() -> None:
    """Test that diff command shows added blocks."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as temp_dir:
        sidedoc_path = Path(temp_dir) / "test.sidedoc"

        # Create sidedoc with initial content
        old_content = "# Title"
        old_structure = {
            "blocks": [
                {
                    "id": "block-1",
                    "type": "heading",
                    "docx_paragraph_index": 0,
                    "content_start": 0,
                    "content_end": 7,
                    "content_hash": "hash1",
                    "level": 1,
                    "image_path": None,
                    "inline_formatting": None,
                }
            ]
        }
        styles = {"block_styles": {}, "document_defaults": {"font_name": "Arial", "font_size": 11}}
        manifest = {
            "sidedoc_version": "1.0.0",
            "created_at": "2024-01-01T00:00:00+00:00",
            "modified_at": "2024-01-01T00:00:00+00:00",
            "source_file": "test.docx",
            "source_hash": "abc123",
            "content_hash": "old_hash",
            "generator": "sidedoc-cli/0.1.0",
        }

        # Create archive with OLD content in structure
        with zipfile.ZipFile(sidedoc_path, "w") as zip_file:
            # Write NEW content (added paragraph)
            zip_file.writestr("content.md", "# Title\n\nNew paragraph added.")
            zip_file.writestr("structure.json", json.dumps(old_structure))
            zip_file.writestr("styles.json", json.dumps(styles))
            zip_file.writestr("manifest.json", json.dumps(manifest))

        # Run diff command
        result = runner.invoke(main, ["diff", str(sidedoc_path)])

        assert result.exit_code == 0
        # Should show added content
        assert "+" in result.output or "added" in result.output.lower()


def test_diff_command_shows_removed_blocks() -> None:
    """Test that diff command shows removed blocks."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as temp_dir:
        sidedoc_path = Path(temp_dir) / "test.sidedoc"

        # Old structure has 2 blocks
        old_structure = {
            "blocks": [
                {
                    "id": "block-1",
                    "type": "heading",
                    "docx_paragraph_index": 0,
                    "content_start": 0,
                    "content_end": 7,
                    "content_hash": "hash1",
                    "level": 1,
                    "image_path": None,
                    "inline_formatting": None,
                },
                {
                    "id": "block-2",
                    "type": "paragraph",
                    "docx_paragraph_index": 1,
                    "content_start": 9,
                    "content_end": 29,
                    "content_hash": "hash2",
                    "level": None,
                    "image_path": None,
                    "inline_formatting": None,
                },
            ]
        }

        with zipfile.ZipFile(sidedoc_path, "w") as zip_file:
            # New content has only 1 block (paragraph removed)
            zip_file.writestr("content.md", "# Title")
            zip_file.writestr("structure.json", json.dumps(old_structure))
            zip_file.writestr("styles.json", json.dumps({"block_styles": {}}))
            zip_file.writestr("manifest.json", json.dumps({
                "sidedoc_version": "1.0.0",
                "created_at": "2024-01-01T00:00:00+00:00",
                "modified_at": "2024-01-01T00:00:00+00:00",
                "source_file": "test.docx",
                "source_hash": "abc",
                "content_hash": "hash",
                "generator": "sidedoc-cli/0.1.0",
            }))

        result = runner.invoke(main, ["diff", str(sidedoc_path)])

        assert result.exit_code == 0
        # Should show removed content
        assert "-" in result.output or "removed" in result.output.lower()


def test_diff_command_shows_modified_blocks() -> None:
    """Test that diff command shows modified blocks."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as temp_dir:
        sidedoc_path = Path(temp_dir) / "test.sidedoc"

        old_structure = {
            "blocks": [
                {
                    "id": "block-1",
                    "type": "paragraph",
                    "docx_paragraph_index": 0,
                    "content_start": 0,
                    "content_end": 13,
                    "content_hash": "hash1",
                    "level": None,
                    "image_path": None,
                    "inline_formatting": None,
                }
            ]
        }

        with zipfile.ZipFile(sidedoc_path, "w") as zip_file:
            # Modified content (different from what structure has)
            zip_file.writestr("content.md", "Modified text.")
            zip_file.writestr("structure.json", json.dumps(old_structure))
            zip_file.writestr("styles.json", json.dumps({"block_styles": {}}))
            zip_file.writestr("manifest.json", json.dumps({
                "sidedoc_version": "1.0.0",
                "created_at": "2024-01-01T00:00:00+00:00",
                "modified_at": "2024-01-01T00:00:00+00:00",
                "source_file": "test.docx",
                "source_hash": "abc",
                "content_hash": "hash",
                "generator": "sidedoc-cli/0.1.0",
            }))

        result = runner.invoke(main, ["diff", str(sidedoc_path)])

        assert result.exit_code == 0
        # Should show modification or both old and new
        output_lower = result.output.lower()
        assert "modified" in output_lower or ("+" in result.output and "-" in result.output)


def test_diff_command_no_changes() -> None:
    """Test that diff command handles no changes gracefully."""
    import hashlib

    def compute_hash(content: str) -> str:
        return hashlib.sha256(content.encode()).hexdigest()

    runner = CliRunner()

    with tempfile.TemporaryDirectory() as temp_dir:
        sidedoc_path = Path(temp_dir) / "test.sidedoc"

        content = "# Title\n\nParagraph."

        # Create matching content and structure with REAL hashes
        old_structure = {
            "blocks": [
                {
                    "id": "block-1",
                    "type": "heading",
                    "docx_paragraph_index": 0,
                    "content_start": 0,
                    "content_end": 7,
                    "content_hash": compute_hash("# Title"),
                    "level": 1,
                    "image_path": None,
                    "inline_formatting": None,
                },
                {
                    "id": "block-2",
                    "type": "paragraph",
                    "docx_paragraph_index": 1,
                    "content_start": 9,
                    "content_end": 19,
                    "content_hash": compute_hash("Paragraph."),
                    "level": None,
                    "image_path": None,
                    "inline_formatting": None,
                },
            ]
        }

        with zipfile.ZipFile(sidedoc_path, "w") as zip_file:
            zip_file.writestr("content.md", content)
            zip_file.writestr("structure.json", json.dumps(old_structure))
            zip_file.writestr("styles.json", json.dumps({"block_styles": {}}))
            zip_file.writestr("manifest.json", json.dumps({
                "sidedoc_version": "1.0.0",
                "created_at": "2024-01-01T00:00:00+00:00",
                "modified_at": "2024-01-01T00:00:00+00:00",
                "source_file": "test.docx",
                "source_hash": "abc",
                "content_hash": "hash",
                "generator": "sidedoc-cli/0.1.0",
            }))

        result = runner.invoke(main, ["diff", str(sidedoc_path)])

        assert result.exit_code == 0
        # Should indicate no changes
        output_lower = result.output.lower()
        assert "no changes" in output_lower or "unchanged" in output_lower
