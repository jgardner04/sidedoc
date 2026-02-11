"""Tests for sidedoc sync command."""

import json
import tempfile
import zipfile
from pathlib import Path
from click.testing import CliRunner
from sidedoc.cli import main
from tests.helpers import create_sidedoc_dir


def test_sync_command_detects_changes() -> None:
    """Test that sync command detects and syncs changes in content.md."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as temp_dir:
        sidedoc_path = Path(temp_dir) / "test.sidedoc"

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

        # Create directory with new content (added a paragraph)
        create_sidedoc_dir(sidedoc_path, "# New Title\n\nNew paragraph.", old_structure)

        result = runner.invoke(main, ["sync", str(sidedoc_path)])

        assert result.exit_code == 0
        assert "Synced" in result.output or "✓" in result.output

        # Verify structure was updated
        updated_structure = json.loads((sidedoc_path / "structure.json").read_text())
        assert len(updated_structure["blocks"]) == 2


def test_sync_command_with_output_builds_docx() -> None:
    """Test that sync command with -o flag builds updated docx."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as temp_dir:
        sidedoc_path = Path(temp_dir) / "test.sidedoc"
        output_docx = Path(temp_dir) / "output.docx"

        create_sidedoc_dir(sidedoc_path, "# Title\n\nParagraph.", {"blocks": []})

        result = runner.invoke(main, ["sync", str(sidedoc_path), "-o", str(output_docx)])

        assert result.exit_code == 0
        assert output_docx.exists()


def test_sync_command_missing_file() -> None:
    """Test that sync command handles missing file error."""
    runner = CliRunner()
    result = runner.invoke(main, ["sync", "nonexistent.sidedoc"])

    assert result.exit_code == 2  # EXIT_NOT_FOUND
    assert "not found" in result.output.lower() or "does not exist" in result.output.lower()


def test_sync_command_rejects_zip() -> None:
    """Test that sync command rejects ZIP archives."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as temp_dir:
        zip_path = Path(temp_dir) / "test.sdoc"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("content.md", "# Title")
            zf.writestr("structure.json", json.dumps({"blocks": []}))
            zf.writestr("styles.json", json.dumps({"block_styles": {}}))
            zf.writestr("manifest.json", json.dumps({}))

        result = runner.invoke(main, ["sync", str(zip_path)])

        assert result.exit_code != 0
        assert "Cannot sync a ZIP archive" in result.output


def test_sync_command_invalid_sidedoc() -> None:
    """Test that sync command handles invalid sidedoc format."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a directory with missing files
        invalid_path = Path(temp_dir) / "invalid.sidedoc"
        invalid_path.mkdir()
        (invalid_path / "random.txt").write_text("not a sidedoc")

        result = runner.invoke(main, ["sync", str(invalid_path)])

        # Should fail with invalid format or error
        assert result.exit_code != 0
