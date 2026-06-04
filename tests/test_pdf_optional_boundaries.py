"""Tests for optional PDF dependency boundaries."""

import hashlib
import json
import sys
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest

from click.testing import CliRunner

from sidedoc.cli import EXIT_INVALID_FORMAT, main
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


def test_extract_pdf_document_numbers_contiguous_ordered_lists(tmp_path, monkeypatch):
    """PDF ordered lists should use increasing markers without importing real Docling."""
    from sidedoc.extract import blocks_to_markdown
    import sidedoc.extract_pdf as extract_pdf

    class TextItem:
        def __init__(self, text: str, enumerated: bool = True) -> None:
            self.text = text
            self.label = "list_item"
            self.enumerated = enumerated
            self.content_layer = "body"

    class FakeDoc:
        def export_to_dict(self):
            return {"tables": []}

        def iterate_items(self):
            yield TextItem("First"), 0
            yield TextItem("Second"), 0
            yield TextItem("Third"), 0
            yield TextItem("Bullet", enumerated=False), 0

    class FakeConverter:
        def convert(self, _pdf_path: str):
            return SimpleNamespace(document=FakeDoc())

    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n%%EOF")
    monkeypatch.setattr(extract_pdf, "require_docling", lambda: FakeConverter)

    blocks, _image_data, _sections = extract_pdf.extract_pdf_document(str(pdf_path))

    assert [block.content for block in blocks] == [
        "1. First",
        "2. Second",
        "3. Third",
        "- Bullet",
    ]
    assert blocks_to_markdown(blocks).splitlines() == [
        "1. First",
        "2. Second",
        "3. Third",
        "- Bullet",
    ]


def test_extract_pdf_document_restarts_ordered_lists_after_paragraph(tmp_path, monkeypatch):
    """PDF ordered list numbering should reset after a non-list paragraph."""
    import sidedoc.extract_pdf as extract_pdf

    class TextItem:
        def __init__(self, text: str, label: str = "list_item", enumerated: bool = True) -> None:
            self.text = text
            self.label = label
            self.enumerated = enumerated
            self.content_layer = "body"

    class FakeDoc:
        def export_to_dict(self):
            return {"tables": []}

        def iterate_items(self):
            yield TextItem("First"), 0
            yield TextItem("Paragraph break", label="paragraph", enumerated=False), 0
            yield TextItem("Restarted"), 0

    class FakeConverter:
        def convert(self, _pdf_path: str):
            return SimpleNamespace(document=FakeDoc())

    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n%%EOF")
    monkeypatch.setattr(extract_pdf, "require_docling", lambda: FakeConverter)

    blocks, _image_data, _sections = extract_pdf.extract_pdf_document(str(pdf_path))

    assert [block.content for block in blocks] == [
        "1. First",
        "Paragraph break",
        "1. Restarted",
    ]


def test_extract_pdf_offsets_slice_serialized_markdown_exactly(tmp_path, monkeypatch):
    """PDF block offsets should exactly slice blocks_to_markdown output."""
    from sidedoc.extract import blocks_to_markdown
    import sidedoc.extract_pdf as extract_pdf

    class SectionHeaderItem:
        text = "Title"
        label = "section_header"
        level = 1
        content_layer = "body"

    class TextItem:
        text = "Body paragraph"
        label = "paragraph"
        content_layer = "body"

    class FakeDoc:
        def export_to_dict(self):
            return {"tables": []}

        def iterate_items(self):
            yield SectionHeaderItem(), 0
            yield TextItem(), 0

    class FakeConverter:
        def convert(self, _pdf_path: str):
            return SimpleNamespace(document=FakeDoc())

    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n%%EOF")
    monkeypatch.setattr(extract_pdf, "require_docling", lambda: FakeConverter)

    blocks, _image_data, _sections = extract_pdf.extract_pdf_document(str(pdf_path))
    content_md = blocks_to_markdown(blocks)

    for index, block in enumerate(blocks):
        assert content_md[block.content_start:block.content_end] == block.content
        next_char = content_md[block.content_end:block.content_end + 1]
        assert next_char == ("\n" if index < len(blocks) - 1 else "")


def test_extract_pdf_document_missing_file_raises_before_docling(tmp_path, monkeypatch):
    """Direct PDF extraction should precheck missing paths before loading Docling."""
    import sidedoc.extract_pdf as extract_pdf

    def fail_require_docling():
        raise AssertionError("require_docling should not be called for missing files")

    monkeypatch.setattr(extract_pdf, "require_docling", fail_require_docling)

    with pytest.raises(FileNotFoundError):
        extract_pdf.extract_pdf_document(str(tmp_path / "missing.pdf"))


def test_build_pdf_missing_content_fails_before_weasyprint(tmp_path, monkeypatch):
    """Malformed PDF sidedoc containers should identify missing content.md early."""
    import sidedoc.reconstruct_pdf as reconstruct_pdf

    sidedoc_dir = tmp_path / "broken.sidedoc"
    sidedoc_dir.mkdir()
    (sidedoc_dir / "manifest.json").write_text(json.dumps({"source_format": "pdf"}))

    def fail_require_weasyprint():
        raise AssertionError("require_weasyprint should not be called without content.md")

    monkeypatch.setattr(reconstruct_pdf, "require_weasyprint", fail_require_weasyprint)

    with pytest.raises(FileNotFoundError, match="content.md not found in sidedoc"):
        reconstruct_pdf.build_pdf_from_sidedoc(str(sidedoc_dir), str(tmp_path / "out.pdf"))


def test_build_pdf_missing_content_cli_has_clear_error(tmp_path):
    """CLI build should report missing content.md without a traceback."""
    sidedoc_dir = tmp_path / "broken.sidedoc"
    sidedoc_dir.mkdir()
    (sidedoc_dir / "manifest.json").write_text(json.dumps({"source_format": "pdf"}))

    runner = CliRunner()
    result = runner.invoke(main, ["build", str(sidedoc_dir)])

    assert result.exit_code != 0
    assert "content.md not found in sidedoc" in result.output
    assert "Traceback" not in result.output


def test_build_invalid_source_format_exits_invalid_format(tmp_path):
    """Build should classify explicit unsupported source_format as invalid metadata."""
    sidedoc_dir = tmp_path / "invalid.sidedoc"
    sidedoc_dir.mkdir()
    (sidedoc_dir / "manifest.json").write_text(json.dumps({"source_format": "bogus"}))

    runner = CliRunner()
    result = runner.invoke(main, ["build", str(sidedoc_dir)])

    assert result.exit_code == EXIT_INVALID_FORMAT
    assert "Unsupported source_format in manifest.json: bogus" in result.output
    assert "Traceback" not in result.output


def test_sync_invalid_source_format_exits_invalid_format(tmp_path):
    """Sync should classify explicit unsupported source_format as invalid metadata."""
    sidedoc_dir = tmp_path / "invalid.sidedoc"
    sidedoc_dir.mkdir()
    (sidedoc_dir / "manifest.json").write_text(json.dumps({"source_format": "bogus"}))

    runner = CliRunner()
    result = runner.invoke(main, ["sync", str(sidedoc_dir)])

    assert result.exit_code == EXIT_INVALID_FORMAT
    assert "Unsupported source_format in manifest.json: bogus" in result.output
    assert "Traceback" not in result.output


def test_build_unrelated_value_error_uses_generic_exit(tmp_path, monkeypatch):
    """Only source_format ValueError should be classified as invalid format."""
    import sidedoc.cli as cli

    sidedoc_dir = tmp_path / "valid.sidedoc"
    sidedoc_dir.mkdir()
    (sidedoc_dir / "manifest.json").write_text(json.dumps({"source_format": "docx"}))

    def raise_value_error(_input_file: str, _output: str) -> None:
        raise ValueError("downstream build problem")

    monkeypatch.setattr(cli, "build_docx_from_sidedoc", raise_value_error)

    runner = CliRunner()
    result = runner.invoke(main, ["build", str(sidedoc_dir)])

    assert result.exit_code == cli.EXIT_ERROR
    assert "downstream build problem" in result.output
    assert "Traceback" not in result.output


def test_sync_unrelated_value_error_uses_generic_exit(tmp_path, monkeypatch):
    """Only source_format ValueError should be classified as invalid format during sync."""
    import sidedoc.cli as cli

    sidedoc_dir = tmp_path / "valid.sidedoc"
    create_sidedoc_directory(
        str(sidedoc_dir),
        "Hello",
        [Block(id="block-0", type="paragraph", content="Hello", docx_paragraph_index=0, content_start=0, content_end=5, content_hash=hashlib.sha256(b"Hello").hexdigest())],
        [_style()],
        __file__,
        source_format="docx",
    )

    def raise_value_error(_content_md: str):
        raise ValueError("downstream sync problem")

    monkeypatch.setattr(cli, "parse_markdown_to_blocks", raise_value_error)

    runner = CliRunner()
    result = runner.invoke(main, ["sync", str(sidedoc_dir)])

    assert result.exit_code == cli.EXIT_ERROR
    assert "downstream sync problem" in result.output
    assert "Traceback" not in result.output


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


def test_build_pdf_from_sdoc_without_assets_uses_live_directory_base_url(tmp_path, monkeypatch):
    """PDF builds should support .sdoc archives even when no assets exist."""
    import sidedoc.reconstruct_pdf as reconstruct_pdf

    sdoc_path = tmp_path / "sample.sdoc"
    with zipfile.ZipFile(sdoc_path, "w") as zf:
        zf.writestr("manifest.json", json.dumps({"source_format": "pdf"}))
        zf.writestr("content.md", "Hello archive")

    observed = {}

    class FakeHTML:
        def __init__(self, string: str, base_url: str) -> None:
            observed["html"] = string
            observed["base_url"] = base_url

        def write_pdf(self, output_path: str) -> None:
            assert Path(observed["base_url"]).is_dir()
            Path(output_path).write_bytes(b"%PDF-1.4\n%%EOF")

    monkeypatch.setattr(reconstruct_pdf, "require_weasyprint", lambda: SimpleNamespace(HTML=FakeHTML))

    output_path = tmp_path / "out.pdf"
    reconstruct_pdf.build_pdf_from_sidedoc(str(sdoc_path), str(output_path))

    assert output_path.exists()
    assert "Hello archive" in observed["html"]


def test_build_pdf_from_sdoc_resolves_assets_during_write_pdf(tmp_path, monkeypatch):
    """Archive assets should exist relative to base_url while WeasyPrint renders."""
    import sidedoc.reconstruct_pdf as reconstruct_pdf

    sdoc_path = tmp_path / "sample.sdoc"
    with zipfile.ZipFile(sdoc_path, "w") as zf:
        zf.writestr("manifest.json", json.dumps({"source_format": "pdf"}))
        zf.writestr("content.md", "![Alt](assets/image.png)")
        zf.writestr("assets/image.png", b"fake image bytes")

    observed = {}

    class FakeHTML:
        def __init__(self, string: str, base_url: str) -> None:
            observed["html"] = string
            observed["base_url"] = base_url

        def write_pdf(self, output_path: str) -> None:
            base_url = Path(observed["base_url"])
            assert base_url.is_dir()
            assert (base_url / "assets" / "image.png").exists()
            assert "assets/image.png" in observed["html"]
            Path(output_path).write_bytes(b"%PDF-1.4\n%%EOF")

    monkeypatch.setattr(reconstruct_pdf, "require_weasyprint", lambda: SimpleNamespace(HTML=FakeHTML))

    output_path = tmp_path / "out.pdf"
    reconstruct_pdf.build_pdf_from_sidedoc(str(sdoc_path), str(output_path))

    assert output_path.exists()


def test_build_pdf_from_sidedoc_directory_uses_directory_base_url(tmp_path, monkeypatch):
    """Directory PDF builds should resolve assets relative to the .sidedoc directory."""
    import sidedoc.reconstruct_pdf as reconstruct_pdf

    sidedoc_dir = tmp_path / "sample.sidedoc"
    assets_dir = sidedoc_dir / "assets"
    assets_dir.mkdir(parents=True)
    (sidedoc_dir / "manifest.json").write_text(json.dumps({"source_format": "pdf"}))
    (sidedoc_dir / "content.md").write_text("![Alt](assets/image.png)")
    (assets_dir / "image.png").write_bytes(b"fake image bytes")

    observed = {}

    class FakeHTML:
        def __init__(self, string: str, base_url: str) -> None:
            observed["html"] = string
            observed["base_url"] = base_url

        def write_pdf(self, output_path: str) -> None:
            assert Path(observed["base_url"]) == sidedoc_dir.resolve()
            assert (Path(observed["base_url"]) / "assets" / "image.png").exists()
            assert "assets/image.png" in observed["html"]
            Path(output_path).write_bytes(b"%PDF-1.4\n%%EOF")

    monkeypatch.setattr(reconstruct_pdf, "require_weasyprint", lambda: SimpleNamespace(HTML=FakeHTML))

    output_path = tmp_path / "out.pdf"
    reconstruct_pdf.build_pdf_from_sidedoc(str(sidedoc_dir), str(output_path))

    assert output_path.exists()


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
