"""Tests for sidedoc sync command."""

import json
import tempfile
import zipfile
from pathlib import Path
from click.testing import CliRunner
from sidedoc.cli import main


def test_sync_command_detects_changes() -> None:
    """Test that sync command detects changes in content.md."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as temp_dir:
        sidedoc_path = Path(temp_dir) / "test.sidedoc"

        # Create a sidedoc archive with initial content
        old_content = "# Old Title\n\nOld paragraph."
        old_structure = {
            "blocks": [
                {
                    "id": "block-1",
                    "type": "heading",
                    "docx_paragraph_index": 0,
                    "content_start": 0,
                    "content_end": 11,
                    "content_hash": "hash1",
                    "level": 1,
                    "image_path": None,
                    "inline_formatting": None,
                }
            ]
        }
        old_styles = {"block_styles": {}, "document_defaults": {"font_name": "Arial", "font_size": 11}}
        old_manifest = {
            "sidedoc_version": "1.0.0",
            "created_at": "2024-01-01T00:00:00+00:00",
            "modified_at": "2024-01-01T00:00:00+00:00",
            "source_file": "test.docx",
            "source_hash": "abc123",
            "content_hash": "old_hash",
            "generator": "sidedoc-cli/0.1.0",
        }

        with zipfile.ZipFile(sidedoc_path, "w") as zip_file:
            zip_file.writestr("content.md", old_content)
            zip_file.writestr("structure.json", json.dumps(old_structure))
            zip_file.writestr("styles.json", json.dumps(old_styles))
            zip_file.writestr("manifest.json", json.dumps(old_manifest))

        # Edit content.md within the archive
        new_content = "# New Title\n\nNew paragraph."
        with zipfile.ZipFile(sidedoc_path, "a") as zip_file:
            # Remove old content.md and add new one
            pass  # Can't remove in append mode, but overwrite works

        # Rewrite with new content
        with zipfile.ZipFile(sidedoc_path, "r") as source_zip:
            styles = source_zip.read("styles.json")
            manifest = source_zip.read("manifest.json")
            structure = source_zip.read("structure.json")

        with zipfile.ZipFile(sidedoc_path, "w") as dest_zip:
            dest_zip.writestr("content.md", new_content)
            dest_zip.writestr("styles.json", styles)
            dest_zip.writestr("manifest.json", manifest)
            dest_zip.writestr("structure.json", structure)

        # Run sync command
        result = runner.invoke(main, ["sync", str(sidedoc_path)])

        assert result.exit_code == 0
        assert "Synced" in result.output or "✓" in result.output

        # Verify structure was updated
        with zipfile.ZipFile(sidedoc_path, "r") as zip_file:
            updated_structure = json.loads(zip_file.read("structure.json"))
            # Should have 2 blocks now (heading + paragraph)
            assert len(updated_structure["blocks"]) == 2


def test_sync_command_with_output_builds_docx() -> None:
    """Test that sync command with -o flag builds updated docx."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as temp_dir:
        sidedoc_path = Path(temp_dir) / "test.sidedoc"
        output_docx = Path(temp_dir) / "output.docx"

        # Create sidedoc with content
        content = "# Title\n\nParagraph."
        structure = {"blocks": []}
        styles = {"block_styles": {}, "document_defaults": {"font_name": "Arial", "font_size": 11}}
        manifest = {
            "sidedoc_version": "1.0.0",
            "created_at": "2024-01-01T00:00:00+00:00",
            "modified_at": "2024-01-01T00:00:00+00:00",
            "source_file": "test.docx",
            "source_hash": "abc123",
            "content_hash": "hash",
            "generator": "sidedoc-cli/0.1.0",
        }

        with zipfile.ZipFile(sidedoc_path, "w") as zip_file:
            zip_file.writestr("content.md", content)
            zip_file.writestr("structure.json", json.dumps(structure))
            zip_file.writestr("styles.json", json.dumps(styles))
            zip_file.writestr("manifest.json", json.dumps(manifest))

        # Run sync with output
        result = runner.invoke(main, ["sync", str(sidedoc_path), "-o", str(output_docx)])

        assert result.exit_code == 0
        assert output_docx.exists()


def test_sync_command_missing_file() -> None:
    """Test that sync command handles missing file error."""
    runner = CliRunner()
    result = runner.invoke(main, ["sync", "nonexistent.sidedoc"])

    assert result.exit_code == 2  # EXIT_NOT_FOUND
    assert "not found" in result.output.lower() or "does not exist" in result.output.lower()


def test_sync_command_invalid_sidedoc() -> None:
    """Test that sync command handles invalid sidedoc format."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create invalid ZIP file (not a sidedoc)
        invalid_path = Path(temp_dir) / "invalid.sidedoc"
        with zipfile.ZipFile(invalid_path, "w") as zip_file:
            zip_file.writestr("random.txt", "not a sidedoc")

        result = runner.invoke(main, ["sync", str(invalid_path)])

        # Should fail with invalid format or error
        assert result.exit_code != 0
