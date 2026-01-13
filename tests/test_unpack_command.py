"""Test unpack command."""

import json
import tempfile
import zipfile
from pathlib import Path
from click.testing import CliRunner
from docx import Document
from sidedoc.cli import main


def create_test_sidedoc() -> str:
    """Create a test .sidedoc file."""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".sidedoc")

    with zipfile.ZipFile(temp_file.name, "w") as zf:
        zf.writestr("content.md", "# Test\n\nContent")
        zf.writestr("structure.json", json.dumps({"blocks": []}))
        zf.writestr("styles.json", json.dumps({"block_styles": {}}))
        zf.writestr("manifest.json", json.dumps({
            "sidedoc_version": "1.0.0",
            "created_at": "2026-01-01T00:00:00Z",
            "modified_at": "2026-01-01T00:00:00Z",
            "source_file": "test.docx",
            "source_hash": "abc123",
            "content_hash": "def456",
            "generator": "test"
        }))

    temp_file.close()
    return temp_file.name


def test_unpack_command_extracts_files():
    """Test that unpack extracts all files."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        sidedoc_path = create_test_sidedoc()
        output_dir = "unpacked"

        try:
            result = runner.invoke(main, ["unpack", sidedoc_path, "-o", output_dir])

            assert result.exit_code == 0

            # Check all files were extracted
            output_path = Path(output_dir)
            assert (output_path / "content.md").exists()
            assert (output_path / "structure.json").exists()
            assert (output_path / "styles.json").exists()
            assert (output_path / "manifest.json").exists()
        finally:
            Path(sidedoc_path).unlink(missing_ok=True)


def test_unpack_preserves_content():
    """Test that unpack preserves file content."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        sidedoc_path = create_test_sidedoc()
        output_dir = "unpacked"

        try:
            result = runner.invoke(main, ["unpack", sidedoc_path, "-o", output_dir])

            assert result.exit_code == 0

            # Check content is preserved
            content = (Path(output_dir) / "content.md").read_text()
            assert "# Test" in content
            assert "Content" in content
        finally:
            Path(sidedoc_path).unlink(missing_ok=True)
