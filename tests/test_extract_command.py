"""Test extract command integration."""

import json
import tempfile
import zipfile
from pathlib import Path
from click.testing import CliRunner
from docx import Document
from sidedoc.cli import main


def create_test_docx() -> str:
    """Create a test docx file."""
    doc = Document()
    doc.add_paragraph("Test Title", style="Heading 1")
    doc.add_paragraph("This is a test paragraph.")

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
    doc.save(temp_file.name)
    temp_file.close()
    return temp_file.name


def test_extract_command_creates_sidedoc_file():
    """Test that extract command creates a .sidedoc file."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create test docx
        docx_path = create_test_docx()

        try:
            # Run extract command
            result = runner.invoke(main, ["extract", docx_path])

            # Check command succeeded
            assert result.exit_code == 0

            # Check .sidedoc file was created
            sidedoc_path = Path(docx_path).with_suffix(".sidedoc")
            assert sidedoc_path.exists()

            # Verify it's a valid ZIP
            assert zipfile.is_zipfile(sidedoc_path)
        finally:
            Path(docx_path).unlink(missing_ok=True)


def test_extract_command_with_custom_output():
    """Test extract command with -o flag."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        docx_path = create_test_docx()
        output_path = "custom_output.sidedoc"

        try:
            result = runner.invoke(main, ["extract", docx_path, "-o", output_path])

            assert result.exit_code == 0
            assert Path(output_path).exists()
        finally:
            Path(docx_path).unlink(missing_ok=True)
            Path(output_path).unlink(missing_ok=True)


def test_extract_creates_valid_zip_structure():
    """Test that extract creates proper ZIP structure."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        docx_path = create_test_docx()

        try:
            result = runner.invoke(main, ["extract", docx_path])
            assert result.exit_code == 0

            sidedoc_path = Path(docx_path).with_suffix(".sidedoc")
            with zipfile.ZipFile(sidedoc_path, "r") as zf:
                names = zf.namelist()

                # Check required files exist
                assert "content.md" in names
                assert "structure.json" in names
                assert "styles.json" in names
                assert "manifest.json" in names
        finally:
            Path(docx_path).unlink(missing_ok=True)


def test_extract_creates_valid_manifest():
    """Test that manifest.json has required fields."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        docx_path = create_test_docx()

        try:
            result = runner.invoke(main, ["extract", docx_path])
            assert result.exit_code == 0

            sidedoc_path = Path(docx_path).with_suffix(".sidedoc")
            with zipfile.ZipFile(sidedoc_path, "r") as zf:
                manifest_data = json.loads(zf.read("manifest.json"))

                # Check required fields
                assert "sidedoc_version" in manifest_data
                assert "created_at" in manifest_data
                assert "modified_at" in manifest_data
                assert "source_file" in manifest_data
                assert "source_hash" in manifest_data
                assert "content_hash" in manifest_data
                assert "generator" in manifest_data
        finally:
            Path(docx_path).unlink(missing_ok=True)


def test_extract_error_on_missing_file():
    """Test that extract returns error code 2 for missing file."""
    runner = CliRunner()
    result = runner.invoke(main, ["extract", "nonexistent.docx"])

    # Click handles missing files with exit code 2
    assert result.exit_code == 2
