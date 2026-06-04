"""Tests for PDF pipeline hardening (PR #61 review findings C1-C3, I1-I5).

These cover silent content-loss prevention (warn-and-continue + --strict),
table fidelity (header-less rendering, merged cells), and the .sdoc
path-traversal guard. They use fake duck-typed Docling documents (no real
docling required) plus caplog for warning assertions, matching the existing
pattern in test_pdf_optional_boundaries.py.
"""

import json
import logging
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest
from click.testing import CliRunner


# --------------------------------------------------------------------------
# Fake Docling document helpers
# --------------------------------------------------------------------------

def _fake_converter(doc):
    class FakeConverter:
        def convert(self, _pdf_path):
            return SimpleNamespace(document=doc)
    return FakeConverter


def _write_pdf(tmp_path):
    pdf = tmp_path / "sample.pdf"
    pdf.write_bytes(b"%PDF-1.4\n%%EOF")
    return pdf


# --------------------------------------------------------------------------
# C3 — robust item dispatch (ListItem recognized; unsupported items warn)
# --------------------------------------------------------------------------

def test_list_item_round_trips(tmp_path, monkeypatch):
    """A Docling ListItem (subclass of TextItem) must produce a list block."""
    import sidedoc.extract_pdf as extract_pdf

    class ListItem:  # name mirrors Docling's real subclass
        def __init__(self, text):
            self.text = text
            self.label = "list_item"
            self.enumerated = False
            self.content_layer = "body"

    class FakeDoc:
        def export_to_dict(self):
            return {"tables": []}

        def iterate_items(self):
            yield ListItem("Apples"), 0
            yield ListItem("Oranges"), 0

    monkeypatch.setattr(extract_pdf, "require_docling", lambda: _fake_converter(FakeDoc()))
    blocks, _img, _sec = extract_pdf.extract_pdf_document(str(_write_pdf(tmp_path)))

    assert [b.type for b in blocks] == ["list", "list"]
    assert [b.content for b in blocks] == ["- Apples", "- Oranges"]


def test_unsupported_item_restarts_ordered_list_numbering(tmp_path, monkeypatch):
    """An unsupported item interrupting a list must reset ordered numbering."""
    import sidedoc.extract_pdf as extract_pdf

    class ListItem:
        def __init__(self, text):
            self.text = text
            self.label = "list_item"
            self.enumerated = True
            self.content_layer = "body"

    class FormulaItem:
        text = "E=mc^2"
        label = "formula"
        content_layer = "body"

    class FakeDoc:
        def export_to_dict(self):
            return {"tables": []}

        def iterate_items(self):
            yield ListItem("First"), 0      # 1. First
            yield FormulaItem(), 0          # interrupts the list (skipped)
            yield ListItem("Second"), 0     # should restart at 1.

    monkeypatch.setattr(extract_pdf, "require_docling", lambda: _fake_converter(FakeDoc()))
    blocks, _img, _sec = extract_pdf.extract_pdf_document(str(_write_pdf(tmp_path)))

    list_contents = [b.content for b in blocks if b.type == "list"]
    assert list_contents == ["1. First", "1. Second"]


def test_unsupported_item_warns_and_is_omitted(tmp_path, monkeypatch, caplog):
    """An unrecognized Docling item must warn and be omitted (not silently dropped)."""
    import sidedoc.extract_pdf as extract_pdf

    class FormulaItem:
        text = "E=mc^2"
        label = "formula"
        content_layer = "body"

    class FakeDoc:
        def export_to_dict(self):
            return {"tables": []}

        def iterate_items(self):
            yield FormulaItem(), 0

    monkeypatch.setattr(extract_pdf, "require_docling", lambda: _fake_converter(FakeDoc()))

    with caplog.at_level(logging.WARNING):
        blocks, _img, _sec = extract_pdf.extract_pdf_document(str(_write_pdf(tmp_path)))

    assert blocks == []
    assert "unsupported pdf element" in caplog.text.lower()
    assert "FormulaItem" in caplog.text


# --------------------------------------------------------------------------
# I1 — table correlation by self_ref (no positional desync)
# --------------------------------------------------------------------------

def test_table_self_ref_miss_warns_without_desync(tmp_path, monkeypatch, caplog):
    """An unresolved table warns and is skipped without shifting later tables."""
    import sidedoc.extract_pdf as extract_pdf

    def cell(r, c, text):
        return {"start_row_offset_idx": r, "start_col_offset_idx": c, "text": text,
                "row_span": 1, "col_span": 1, "column_header": False}

    good = {"num_rows": 1, "num_cols": 2, "table_cells": [cell(0, 0, "X"), cell(0, 1, "Y")]}

    class TableItem:
        def __init__(self, self_ref):
            self.label = "table"
            self.content_layer = "body"
            self.self_ref = self_ref

    class FakeDoc:
        def export_to_dict(self):
            # Only the second table has data; first is unresolved.
            return {"tables": [{"self_ref": "#/tables/1", "data": good}]}

        def iterate_items(self):
            yield TableItem("#/tables/0"), 0   # unresolved -> warn, skip
            yield TableItem("#/tables/1"), 0   # resolves to `good`

    monkeypatch.setattr(extract_pdf, "require_docling", lambda: _fake_converter(FakeDoc()))

    with caplog.at_level(logging.WARNING):
        blocks, _img, _sec = extract_pdf.extract_pdf_document(str(_write_pdf(tmp_path)))

    tables = [b for b in blocks if b.type == "table"]
    assert len(tables) == 1, "Unresolved table skipped; resolved table preserved"
    assert "X" in tables[0].content and "Y" in tables[0].content, "No content desync"
    assert "table" in caplog.text.lower()


# --------------------------------------------------------------------------
# I2 — _build_table_metadata bounds guard parity with _table_to_gfm
# --------------------------------------------------------------------------

def test_build_table_metadata_excludes_out_of_bounds_cells():
    from sidedoc.extract_pdf import _build_table_metadata

    table_data = {
        "num_rows": 1,
        "num_cols": 1,
        "table_cells": [
            {"start_row_offset_idx": 0, "start_col_offset_idx": 0, "text": "in",
             "row_span": 1, "col_span": 1, "column_header": False},
            {"start_row_offset_idx": 5, "start_col_offset_idx": 5, "text": "out",
             "row_span": 1, "col_span": 1, "column_header": False},
        ],
    }
    meta = _build_table_metadata(table_data)
    assert len(meta["cells"]) == 1, "Out-of-bounds cell must be excluded from metadata"
    assert meta["cells"][0]["row"] == 0 and meta["cells"][0]["col"] == 0


# --------------------------------------------------------------------------
# I4 — skipped images warn with a count
# --------------------------------------------------------------------------

def test_skipped_images_warn_with_count(tmp_path, monkeypatch, caplog):
    import sidedoc.extract_pdf as extract_pdf

    class PictureItem:
        label = "picture"
        content_layer = "body"

    class FakeDoc:
        def export_to_dict(self):
            return {"tables": []}

        def iterate_items(self):
            yield PictureItem(), 0
            yield PictureItem(), 0

    monkeypatch.setattr(extract_pdf, "require_docling", lambda: _fake_converter(FakeDoc()))

    with caplog.at_level(logging.WARNING):
        blocks, _img, _sec = extract_pdf.extract_pdf_document(str(_write_pdf(tmp_path)))

    assert blocks == []
    assert "2 image" in caplog.text
    assert "skipped" in caplog.text.lower()


# --------------------------------------------------------------------------
# C2 — header-less vs header table render differently
# --------------------------------------------------------------------------

def test_render_table_html_emits_thead_only_with_header_rows():
    from sidedoc.reconstruct_pdf import _render_table_html

    rows = [["A", "B"], ["C", "D"]]
    with_header = _render_table_html(rows, {"header_rows": 1})
    no_header = _render_table_html(rows, {"header_rows": 0})

    assert "<th>" in with_header and "<thead" in with_header
    assert "<th" not in no_header and "<thead" not in no_header
    # Both still render all four data cells (2 header th + 2 body td vs 4 td).
    assert with_header.count("<th>") == 2 and with_header.count("<td") == 2
    assert no_header.count("<td") == 4


# --------------------------------------------------------------------------
# I3 — merged cells render colspan/rowspan and omit covered cells
# --------------------------------------------------------------------------

def test_render_table_html_merged_cell_colspan():
    from sidedoc.reconstruct_pdf import _render_table_html

    rows = [["Merged", ""], ["C", "D"]]
    meta = {
        "header_rows": 0,
        "merged_cells": [{"start_row": 0, "start_col": 0, "row_span": 1, "col_span": 2}],
    }
    html = _render_table_html(rows, meta)
    assert 'colspan="2"' in html
    # Row 0 emits a single spanning cell (covered cell omitted): 1 + 2 = 3 cells total.
    assert html.count("<td") == 3


# --------------------------------------------------------------------------
# C2/overlay — content.md table overlay honors metadata; drift falls back + warns
# --------------------------------------------------------------------------

def test_content_overlay_uses_metadata_header_rows():
    from sidedoc.reconstruct_pdf import _content_md_to_html

    content_md = "Intro\n\n| A | B |\n| --- | --- |\n| C | D |\n"
    table_metas = [{"header_rows": 0}]
    html = _content_md_to_html(content_md, table_metas, has_structure=True)

    assert "<th" not in html, "header_rows=0 must not render a bold header"
    assert "Intro" in html


def test_content_overlay_handles_adjacent_tables(caplog):
    """Two back-to-back tables (joined by a single newline) must each overlay
    their own metadata, not collapse into one segment and trip drift fallback."""
    from sidedoc.reconstruct_pdf import _content_md_to_html

    # blocks_to_markdown joins blocks with a single "\n", so two table blocks
    # become an unbroken run of pipe lines.
    content_md = (
        "| A | B |\n| --- | --- |\n| C | D |\n"
        "| E | F |\n| --- | --- |\n| G | H |"
    )
    metas = [{"header_rows": 0}, {"header_rows": 1}]

    with caplog.at_level(logging.WARNING):
        html = _content_md_to_html(content_md, metas, has_structure=True)

    assert "drift" not in caplog.text.lower() and "out of sync" not in caplog.text.lower()
    assert html.count("<table>") == 2, "Each adjacent table renders separately"
    # First table header_rows=0 -> no thead; second header_rows=1 -> one thead.
    assert html.count("<thead>") == 1


def test_content_overlay_drift_falls_back_and_warns(caplog):
    from sidedoc.reconstruct_pdf import _content_md_to_html

    content_md = "| A | B |\n| --- | --- |\n| C | D |\n"
    # Metadata claims zero tables but content has one -> drift.
    with caplog.at_level(logging.WARNING):
        html = _content_md_to_html(content_md, [], has_structure=True)

    assert "<table" in html, "Fallback still renders the table"
    assert "table" in caplog.text.lower()


# --------------------------------------------------------------------------
# I5 — WeasyPrint asset warnings surface through our logger
# --------------------------------------------------------------------------

def test_build_surfaces_weasyprint_asset_warnings(tmp_path, monkeypatch, caplog):
    import sidedoc.reconstruct_pdf as reconstruct_pdf

    sidedoc_dir = tmp_path / "doc.sidedoc"
    sidedoc_dir.mkdir()
    (sidedoc_dir / "manifest.json").write_text(json.dumps({"source_format": "pdf"}))
    (sidedoc_dir / "content.md").write_text("![x](assets/missing.png)")

    class FakeHTML:
        def __init__(self, string, base_url):
            pass

        def write_pdf(self, output_path):
            logging.getLogger("weasyprint").warning("Failed to load image at assets/missing.png")
            Path(output_path).write_bytes(b"%PDF-1.4\n%%EOF")

    monkeypatch.setattr(reconstruct_pdf, "require_weasyprint", lambda: SimpleNamespace(HTML=FakeHTML))

    with caplog.at_level(logging.WARNING, logger="sidedoc.reconstruct_pdf"):
        reconstruct_pdf.build_pdf_from_sidedoc(str(sidedoc_dir), str(tmp_path / "out.pdf"))

    assert "asset" in caplog.text.lower()
    assert "missing.png" in caplog.text


# --------------------------------------------------------------------------
# C1 — .sdoc asset path-traversal guard is enforced
# --------------------------------------------------------------------------

def test_build_pdf_rejects_traversal_asset(tmp_path, monkeypatch):
    import sidedoc.reconstruct_pdf as reconstruct_pdf

    sdoc = tmp_path / "evil.sdoc"
    with zipfile.ZipFile(sdoc, "w") as zf:
        zf.writestr("manifest.json", json.dumps({"source_format": "pdf"}))
        zf.writestr("content.md", "hello")
        # Enough ../ to actually escape the temp render root.
        zf.writestr("assets/../../../evil.txt", b"pwned")

    class FakeHTML:
        def __init__(self, string, base_url):
            pass

        def write_pdf(self, output_path):
            Path(output_path).write_bytes(b"%PDF-1.4\n%%EOF")

    monkeypatch.setattr(reconstruct_pdf, "require_weasyprint", lambda: SimpleNamespace(HTML=FakeHTML))

    with pytest.raises(ValueError, match="path traversal"):
        reconstruct_pdf.build_pdf_from_sidedoc(str(sdoc), str(tmp_path / "out.pdf"))

    assert not (tmp_path / "evil.txt").exists()


# --------------------------------------------------------------------------
# --strict — content warnings become a non-zero exit
# --------------------------------------------------------------------------

def _strict_pdf_dir(tmp_path):
    """A PDF sidedoc whose content has a table but whose metadata has none (drift)."""
    d = tmp_path / "drift.sidedoc"
    d.mkdir()
    (d / "manifest.json").write_text(json.dumps({"source_format": "pdf"}))
    (d / "content.md").write_text("| A | B |\n| --- | --- |\n| C | D |\n")
    (d / "styles.json").write_text(json.dumps({"styles": []}))
    (d / "structure.json").write_text(json.dumps({"blocks": []}))
    return d


def test_build_strict_exits_nonzero_on_warning(tmp_path, monkeypatch):
    import sidedoc.reconstruct_pdf as reconstruct_pdf
    from sidedoc.cli import main, EXIT_ERROR

    class FakeHTML:
        def __init__(self, string, base_url):
            pass

        def write_pdf(self, output_path):
            Path(output_path).write_bytes(b"%PDF-1.4\n%%EOF")

    monkeypatch.setattr(reconstruct_pdf, "require_weasyprint", lambda: SimpleNamespace(HTML=FakeHTML))

    d = _strict_pdf_dir(tmp_path)
    runner = CliRunner()

    strict = runner.invoke(main, ["build", str(d), "-o", str(tmp_path / "s.pdf"), "--strict"])
    assert strict.exit_code == EXIT_ERROR
    assert "Warning" in strict.output

    lax = runner.invoke(main, ["build", str(d), "-o", str(tmp_path / "l.pdf")])
    assert lax.exit_code == 0
    assert "Warning" in lax.output


def test_extract_strict_exits_nonzero_on_warning(tmp_path, monkeypatch):
    import sidedoc.extract_pdf as extract_pdf
    from sidedoc.cli import main, EXIT_ERROR

    class PictureItem:
        label = "picture"
        content_layer = "body"

    class TextItem:
        text = "Body"
        label = "paragraph"
        content_layer = "body"

    class FakeDoc:
        def export_to_dict(self):
            return {"tables": []}

        def iterate_items(self):
            yield PictureItem(), 0
            yield TextItem(), 0

    monkeypatch.setattr(extract_pdf, "require_docling", lambda: _fake_converter(FakeDoc()))

    pdf = _write_pdf(tmp_path)
    runner = CliRunner()

    strict = runner.invoke(main, ["extract", str(pdf), "-o", str(tmp_path / "s.sidedoc"), "--strict"])
    assert strict.exit_code == EXIT_ERROR
    assert "image" in strict.output.lower()

    lax = runner.invoke(main, ["extract", str(pdf), "-o", str(tmp_path / "l.sidedoc")])
    assert lax.exit_code == 0
