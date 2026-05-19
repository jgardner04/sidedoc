"""Tests for optional PDF dependency boundaries."""

import hashlib
import json
import sys

from click.testing import CliRunner

from sidedoc.cli import main
from sidedoc.models import Block, Style
from sidedoc.package import create_sidedoc_directory


def _style() -> Style:
    return Style(block_id="block-0", docx_style="Normal", font_name="Calibri", font_size=11, alignment="left")


def test_extract_pdf_module_imports_without_docling(monkeypatch):
    """Importing PDF extraction helpers should not require docling."""
    monkeypatch.setitem(sys.modules, "docling.document_converter", None)

    import sidedoc.extract_pdf as extract_pdf

    assert callable(extract_pdf.require_docling)


def test_reconstruct_pdf_module_imports_without_weasyprint(monkeypatch):
    """Importing PDF reconstruction helpers should not require weasyprint."""
    monkeypatch.setitem(sys.modules, "weasyprint", None)

    import sidedoc.reconstruct_pdf as reconstruct_pdf

    assert callable(reconstruct_pdf.require_weasyprint)
    assert reconstruct_pdf._markdown_to_html("**bold**")


def test_extract_missing_pdf_file_is_reported_before_docling(tmp_path, monkeypatch):
    """Missing input PDFs should fail deterministically without importing docling."""
    monkeypatch.setitem(sys.modules, "docling.document_converter", None)

    runner = CliRunner()
    missing_pdf = tmp_path / "missing.pdf"
    result = runner.invoke(main, ["extract", str(missing_pdf)])

    assert result.exit_code != 0
    assert "does not exist" in result.output
    assert "docling" not in result.output.lower()
    assert "Traceback" not in result.output


def test_table_to_gfm_uses_one_separator_for_headerless_tables():
    """Headerless Docling tables should get exactly one GFM separator row."""
    from sidedoc.extract_pdf import _table_to_gfm

    table_data = {
        "num_rows": 2,
        "num_cols": 2,
        "table_cells": [
            {"start_row_offset_idx": 0, "start_col_offset_idx": 0, "text": "A"},
            {"start_row_offset_idx": 0, "start_col_offset_idx": 1, "text": "B"},
            {"start_row_offset_idx": 1, "start_col_offset_idx": 0, "text": "C"},
            {"start_row_offset_idx": 1, "start_col_offset_idx": 1, "text": "D"},
        ],
    }

    lines = _table_to_gfm(table_data).splitlines()
    separators = [line for line in lines if line == "| --- | --- |"]
    assert separators == ["| --- | --- |"]


def test_extract_pdf_without_extra_has_actionable_error(tmp_path, monkeypatch):
    """PDF extraction should fail at invocation with an install hint when docling is absent."""
    monkeypatch.setitem(sys.modules, "docling.document_converter", None)
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n%%EOF")

    runner = CliRunner()
    result = runner.invoke(main, ["extract", str(pdf_path)])

    assert result.exit_code != 0
    assert "PDF extraction requires docling" in result.output
    assert "pip install sidedoc[pdf]" in result.output
    assert "Traceback" not in result.output


def test_build_pdf_without_extra_has_actionable_error(tmp_path, monkeypatch):
    """PDF reconstruction should fail at invocation with an install hint when weasyprint is absent."""
    monkeypatch.setitem(sys.modules, "weasyprint", None)
    sidedoc_dir = tmp_path / "sample.sidedoc"
    create_sidedoc_directory(
        str(sidedoc_dir),
        "Hello",
        [Block(id="block-0", type="paragraph", content="Hello", docx_paragraph_index=0, content_start=0, content_end=5, content_hash=hashlib.sha256(b"Hello").hexdigest())],
        [_style()],
        __file__,
        source_format="pdf",
    )

    runner = CliRunner()
    result = runner.invoke(main, ["build", str(sidedoc_dir)])

    assert result.exit_code != 0
    assert "PDF reconstruction requires weasyprint" in result.output
    assert "pip install sidedoc[pdf]" in result.output
    assert "Traceback" not in result.output


def test_pdf_sync_rejected_clearly(tmp_path):
    """Sync is DOCX-only and should reject PDF-sourced sidedoc directories."""
    sidedoc_dir = tmp_path / "sample.sidedoc"
    create_sidedoc_directory(
        str(sidedoc_dir),
        "Hello",
        [Block(id="block-0", type="paragraph", content="Hello", docx_paragraph_index=0, content_start=0, content_end=5, content_hash=hashlib.sha256(b"Hello").hexdigest())],
        [_style()],
        __file__,
        source_format="pdf",
    )

    runner = CliRunner()
    result = runner.invoke(main, ["sync", str(sidedoc_dir)])

    assert result.exit_code != 0
    assert "PDF sync is not supported" in result.output
    assert "Traceback" not in result.output


def test_manifest_hashes_and_source_format(tmp_path):
    """Manifest source_hash hashes the source file and content_hash hashes content.md."""
    source = tmp_path / "source.pdf"
    source.write_bytes(b"source bytes")
    content = "Hello content"
    sidedoc_dir = tmp_path / "sample.sidedoc"

    create_sidedoc_directory(
        str(sidedoc_dir),
        content,
        [Block(id="block-0", type="paragraph", content=content, docx_paragraph_index=0, content_start=0, content_end=len(content), content_hash=hashlib.sha256(content.encode()).hexdigest())],
        [_style()],
        str(source),
        source_format="pdf",
    )

    manifest = json.loads((sidedoc_dir / "manifest.json").read_text())
    assert manifest["source_format"] == "pdf"
    assert manifest["source_hash"] == hashlib.sha256(b"source bytes").hexdigest()
    assert manifest["content_hash"] == hashlib.sha256(content.encode()).hexdigest()
