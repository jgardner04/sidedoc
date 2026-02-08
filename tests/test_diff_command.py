"""Tests for sidedoc diff command."""

import json
import tempfile
import zipfile
from pathlib import Path
from click.testing import CliRunner
from sidedoc.cli import main
from tests.helpers import create_sidedoc_dir


def test_diff_command_shows_added_blocks() -> None:
    """Test that diff command shows added blocks."""
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
                    "content_end": 7,
                    "content_hash": "hash1",
                    "level": 1,
                    "image_path": None,
                    "inline_formatting": None,
                }
            ]
        }

        # New content has added paragraph vs old structure
        create_sidedoc_dir(sidedoc_path, "# Title\n\nNew paragraph added.", old_structure)

        result = runner.invoke(main, ["diff", str(sidedoc_path)])

        assert result.exit_code == 0
        assert "+" in result.output or "added" in result.output.lower()


def test_diff_command_shows_removed_blocks() -> None:
    """Test that diff command shows removed blocks."""
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

        # New content has only 1 block (paragraph removed)
        create_sidedoc_dir(sidedoc_path, "# Title", old_structure)

        result = runner.invoke(main, ["diff", str(sidedoc_path)])

        assert result.exit_code == 0
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

        create_sidedoc_dir(sidedoc_path, "Modified text.", old_structure)

        result = runner.invoke(main, ["diff", str(sidedoc_path)])

        assert result.exit_code == 0
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

        create_sidedoc_dir(sidedoc_path, content, old_structure)

        result = runner.invoke(main, ["diff", str(sidedoc_path)])

        assert result.exit_code == 0
        output_lower = result.output.lower()
        assert "no changes" in output_lower or "unchanged" in output_lower


def test_diff_rejects_zip_archive() -> None:
    """Test that diff command rejects ZIP archives."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as temp_dir:
        zip_path = Path(temp_dir) / "test.sdoc"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("content.md", "# Title")
            zf.writestr("structure.json", json.dumps({"blocks": []}))
            zf.writestr("styles.json", json.dumps({"block_styles": {}}))
            zf.writestr("manifest.json", json.dumps({}))

        result = runner.invoke(main, ["diff", str(zip_path)])

        assert result.exit_code != 0
        assert "Cannot diff a ZIP archive" in result.output
