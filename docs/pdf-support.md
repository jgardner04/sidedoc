# PDF Support

PDF support is experimental. PDF extraction uses Docling (`extract_pdf.py`) and reconstruction uses WeasyPrint (`reconstruct_pdf.py`). Both require:

```bash
pip install sidedoc[pdf]
```

## MVP Semantics

- `sidedoc extract document.pdf` creates a `.sidedoc/` directory or `.sdoc` archive from PDF content.
- `sidedoc build document.sidedoc` rebuilds to PDF when `manifest.json` has `"source_format": "pdf"`.
- `sidedoc build document.sdoc` also rebuilds PDF-sourced `.sdoc` archives; relative assets already present in the container (for example `assets/image.png`) are exposed during the WeasyPrint render step.
- `sidedoc sync` remains DOCX-only and rejects PDF-sourced containers.
- Rebuilt PDFs are best-effort markdown/HTML/CSS output via WeasyPrint, not exact original-layout preservation.

## Content-loss warnings and `--strict`

The PDF pipeline is **warn-and-continue** by default: anything it can't handle faithfully is
reported as a `Warning:` on stderr rather than dropped under a `✓` success line. Warnings are raised
for unrecognized Docling items, a table whose Docling reference can't be resolved, skipped images
(image extraction is not yet wired), table metadata that has drifted out of sync with `content.md`,
and WeasyPrint asset-load failures during build.

Pass `--strict` to `extract` or `build` to turn any such warning into a non-zero exit (`EXIT_ERROR`),
for use in CI/pipelines where silent degradation is unacceptable. Internally these warnings travel on
the `sidedoc.extract_pdf` / `sidedoc.reconstruct_pdf` loggers (WeasyPrint's own warnings are captured
and re-emitted there); the CLI collects them and decides whether to fail.

## Table rendering on build

PDF reconstruction renders tables to **HTML** (not by passing GFM through mistune), so it can express
things GFM cannot: a table with `header_rows: 0` renders **without** a bold header row, and merged
cells render with `colspan`/`rowspan`. `content.md` remains the authoritative source of table *text*;
`structure.json`'s `table_metadata` supplies header/merge/alignment structure, correlated with the
table regions in `content.md` in document order. If `structure.json` is missing or its table count
disagrees with `content.md` (drift), the build falls back to plain GFM rendering and warns — text is
never lost, only the structural overlay is skipped.

## Pitfalls to Avoid

- **`mistune.html()` is the correct API.** Use `mistune.html(content_md)` directly — do not wrap it in a custom class or use `mistune.create_markdown()`. The function returns a plain `str` and is the simplest correct approach.
- **GFM separator double-insertion.** `_table_to_gfm()` has two code paths: one that appends a separator after a detected header row, and a fallback that inserts one after row 0 when no headers are detected. These must be `if/else` — never two independent `if` checks — or headerless tables will get two separator rows.
- **Do not coerce `header_rows` to `max(1, ...)`.** Docling tables without any `column_header=True` cells legitimately have `header_rows=0`. Forcing it to 1 creates incorrect GFM (treats a data row as a header) and corrupts `table_metadata`.
- **Guard optional heavy deps.** `fitz` (PyMuPDF), `weasyprint`, and `docling` are all optional. Import them lazily or behind guarded helpers so base imports and non-PDF commands work without `sidedoc[pdf]`.
- **Skip `PictureItem` blocks when image extraction is unimplemented.** Do not emit a block with a broken asset reference. Use `continue` to skip the item entirely; the block list stays clean and no dangling `![alt](assets/...)` references appear in `content.md`. Skipped images are **tallied and warned** (see "Content-loss warnings" above), never silently dropped.
- **WeasyPrint requires a directory `base_url`.** `weasyprint.HTML(string=full_html)` cannot resolve relative paths to assets by itself. For `.sidedoc/` directories, pass the `.sidedoc` directory as `base_url`. For `.sdoc` archives, expose archive assets from a temporary render root and keep that directory alive through `write_pdf()` so container-relative references like `assets/image.png` resolve correctly.

## Current Limitations

- Layout fidelity differs from the source PDF.
- Original fonts are not preserved.
- Image extraction from PDFs is not fully wired (skipped images are warned, not extracted).
- OCR/scanned PDF quality depends on Docling and is not guaranteed by Sidedoc.
