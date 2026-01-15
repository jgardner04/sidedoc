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


def test_unpack_rejects_path_traversal_in_assets():
    """Test that unpack rejects malicious paths with .. in assets directory."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".sidedoc")

        # Create a malicious sidedoc with path traversal
        with zipfile.ZipFile(temp_file.name, "w") as zf:
            zf.writestr("content.md", "# Test\n\n![image](assets/../../etc/passwd)")
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
            # Attempt to write outside assets directory
            zf.writestr("assets/../../etc/passwd", "malicious content")

        temp_file.close()
        output_dir = "unpacked"

        try:
            result = runner.invoke(main, ["unpack", temp_file.name, "-o", output_dir])

            # Should fail with invalid format error
            assert result.exit_code == 3  # EXIT_INVALID_FORMAT
            assert "path traversal" in result.output.lower() or "invalid path" in result.output.lower()

            # Ensure the malicious file was NOT written outside the directory
            assert not Path("/etc/passwd").exists() or Path("/etc/passwd").read_text() != "malicious content"
        finally:
            Path(temp_file.name).unlink(missing_ok=True)


def test_unpack_rejects_absolute_paths():
    """Test that unpack rejects absolute paths in archive."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".sidedoc")

        # Create a malicious sidedoc with absolute path
        with zipfile.ZipFile(temp_file.name, "w") as zf:
            zf.writestr("content.md", "# Test")
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
            # Attempt absolute path
            zf.writestr("/tmp/malicious.txt", "malicious content")

        temp_file.close()
        output_dir = "unpacked"

        try:
            result = runner.invoke(main, ["unpack", temp_file.name, "-o", output_dir])

            # Should fail with invalid format error
            assert result.exit_code == 3  # EXIT_INVALID_FORMAT
            assert "path traversal" in result.output.lower() or "invalid path" in result.output.lower()
        finally:
            Path(temp_file.name).unlink(missing_ok=True)


def test_unpack_allows_valid_nested_paths():
    """Test that unpack allows valid nested paths within assets directory."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".sidedoc")

        # Create a sidedoc with valid nested paths
        with zipfile.ZipFile(temp_file.name, "w") as zf:
            zf.writestr("content.md", "# Test")
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
            # Valid nested path in assets
            zf.writestr("assets/images/photo.jpg", b"fake image data")

        temp_file.close()
        output_dir = "unpacked"

        try:
            result = runner.invoke(main, ["unpack", temp_file.name, "-o", output_dir])

            # Should succeed
            assert result.exit_code == 0

            # Check nested file was extracted properly
            assert (Path(output_dir) / "assets" / "images" / "photo.jpg").exists()
        finally:
            Path(temp_file.name).unlink(missing_ok=True)
