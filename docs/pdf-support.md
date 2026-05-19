# PDF Support

PDF support is experimental. PDF extraction uses Docling (`extract_pdf.py`) and reconstruction uses WeasyPrint (`reconstruct_pdf.py`). Both require:

```bash
pip install sidedoc[pdf]
```

## MVP Semantics

- `sidedoc extract document.pdf` creates a `.sidedoc/` directory or `.sdoc` archive from PDF content.
- `sidedoc build document.sidedoc` rebuilds to PDF when `manifest.json` has `"source_format": "pdf"`.
- `sidedoc sync` remains DOCX-only and rejects PDF-sourced containers.
- Rebuilt PDFs are best-effort markdown/HTML/CSS output via WeasyPrint, not exact original-layout preservation.

## Pitfalls to Avoid

- **`mistune.html()` is the correct API.** Use `mistune.html(content_md)` directly — do not wrap it in a custom class or use `mistune.create_markdown()`. The function returns a plain `str` and is the simplest correct approach.
- **GFM separator double-insertion.** `_table_to_gfm()` has two code paths: one that appends a separator after a detected header row, and a fallback that inserts one after row 0 when no headers are detected. These must be `if/else` — never two independent `if` checks — or headerless tables will get two separator rows.
- **Do not coerce `header_rows` to `max(1, ...)`.** Docling tables without any `column_header=True` cells legitimately have `header_rows=0`. Forcing it to 1 creates incorrect GFM (treats a data row as a header) and corrupts `table_metadata`.
- **Guard optional heavy deps.** `fitz` (PyMuPDF), `weasyprint`, and `docling` are all optional. Import them lazily or behind guarded helpers so base imports and non-PDF commands work without `sidedoc[pdf]`.
- **Skip `PictureItem` blocks when image extraction is unimplemented.** Do not emit a block with a broken asset reference. Use `continue` to skip the item entirely; the block list stays clean and no dangling `![alt](assets/...)` references appear in `content.md`.
- **WeasyPrint requires `base_url`.** `weasyprint.HTML(string=full_html)` cannot resolve relative paths to assets. Always pass `base_url=str(Path(sidedoc_path).resolve())` so embedded images in `assets/` resolve correctly.

## Current Limitations

- Layout fidelity differs from the source PDF.
- Original fonts are not preserved.
- Image extraction from PDFs is not fully wired.
- OCR/scanned PDF quality depends on Docling and is not guaranteed by Sidedoc.
