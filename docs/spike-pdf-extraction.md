# Spike: PDF-to-Sidedoc Round-Trip (JON-126)

**Date:** 2026-04-08
**Status:** Complete — working prototype
**Branch:** `jonathan/jon-126-explore-pdf-to-sidedoc-pipeline-using-vision-models`

## Summary

This spike explored adding PDF support to Sidedoc: `extract` a PDF into a sidedoc container, edit the content, and `build` back to PDF. The spike produced a working prototype with 21 new tests (all passing, zero regressions).

## Key Findings

### 1. What's the right extraction approach?

**Answer: Docling (IBM)**

| Library | Quality | Tables | Charts | Speed | Install Size |
|---------|---------|--------|--------|-------|-------------|
| **Docling** | Excellent | TableFormer ML model, merged cells, headers | Yes (2026) | 0.5-2s/page | 892 MB + ~1.5 GB models |
| PyMuPDF4LLM | Good (digital only) | GFM only, no metadata | No | 0.12s/page | ~50 MB |
| Vision models | Good (scans) | Via prompting | Via prompting | Slow, GPU needed | ~8 GB |

Docling handles both digital and scanned PDFs internally, outputs structured JSON with cell-level table data that maps directly to Sidedoc's `table_metadata` format. PyMuPDF4LLM is faster but lacks the structured table metadata needed for round-trip fidelity.

**Evidence:**
- Census Brief (22 pages): 43.5s, 8 tables extracted with correct row/col spans
- Docling paper (9 pages): 4.6s, 3 tables with merged cells detected
- Table metadata mapping: `start_row_offset_idx` → row, `start_col_offset_idx` → col, `row_span`/`col_span` directly available

### 2. Is in-place PDF editing viable for sync?

**Answer: No — the redaction API does not work for text replacement.**

PyMuPDF's `add_redact_annot()` + `apply_redactions()` approach:
- Removes original text (leaves visible gaps)
- Places replacement text at the bottom of the page as separate blocks
- Table cell edits are similarly displaced
- Fundamentally designed for removal, not seamless replacement

**Alternative chosen:** Full reconstruction via WeasyPrint (markdown → HTML/CSS → PDF). This handles all edit types including reflow, and doesn't require the original PDF file.

### 3. What's the actual Docling install footprint?

| Component | Size |
|-----------|------|
| Total venv | 892 MB |
| torch | 354 MB (40%) |
| transformers | 44 MB |
| docling itself | 2 MB |
| Package count | 106 |
| Model weights (first use) | ~1.5 GB additional |

**Verdict:** Acceptable for an optional dependency (`pip install sidedoc[pdf]`). The optional dependency group keeps the default install clean. torch is the heaviest transitive dependency.

### 4. What does styles.json look like without a source DOCX?

PDF-sourced styles use sensible defaults:
- `docx_style`: Mapped from block type ("Heading 1", "Normal", "Table Grid")
- `font_name`: "Helvetica" (default)
- `font_size`: Mapped from heading level (h1=24pt, h2=18pt, body=11pt)
- `alignment`: "left" (default)

Future improvement: Extract actual font names and sizes from Docling's provenance data (bounding boxes include font info).

### 5. What architecture changes are needed?

**Changes made in this spike:**

1. **`source_format` field in Manifest** — `manifest.json` now includes `"source_format": "pdf"` or `"docx"`. This lets `build` auto-detect which reconstructor to use.

2. **New modules:**
   - `extract_pdf.py` — PDF extraction via Docling, produces standard Block/Style lists
   - `reconstruct_pdf.py` — PDF reconstruction via WeasyPrint (markdown → HTML → PDF)

3. **CLI changes:**
   - `extract` command detects `.pdf` extension and routes to PDF extractor
   - `build` command reads `source_format` from manifest and routes to PDF or DOCX reconstructor

4. **No changes to:** `models.py` (Block/Style are format-agnostic), `package.py` (already format-agnostic), `sync.py`, `reconstruct.py`

## Architecture

```
PDF → extract_pdf.py → [Block, Style] → package.py → .sidedoc/
                                                          ↓
                                           (edit content.md)
                                                          ↓
.sidedoc/ → reconstruct_pdf.py → HTML/CSS → WeasyPrint → .pdf
```

The existing DOCX pipeline is unchanged:
```
DOCX → extract.py → [Block, Style] → package.py → .sidedoc/
                                                        ↓
.sidedoc/ → reconstruct.py → python-docx → .docx
```

## Limitations

1. **Layout fidelity:** Rebuilt PDF uses WeasyPrint's default A4 layout with CSS styling, not the original PDF's exact layout. Content is preserved; visual appearance differs.
2. **Images:** Image extraction from PDF is not yet wired (Docling detects images but byte extraction needs work).
3. **Charts:** Not tested in this spike. Docling has chart extraction (2026) but it's experimental.
4. **Sync:** `sidedoc sync` is not yet supported for PDF-sourced sidedocs. Currently only `extract` and `build` work.
5. **Scanned PDFs:** Docling handles OCR internally but quality was not tested.
6. **Font fidelity:** Rebuilt PDF uses Helvetica; original fonts are not preserved.

## Test Coverage

- 16 extraction tests (blocks, IDs, hashes, offsets, headings, tables, styles, CLI, e2e, manifest)
- 5 reconstruction tests (build PDF, text content, table content, CLI auto-detect, round-trip)
- 577 existing tests: zero regressions

## Recommendations for Production

1. **Image extraction:** Wire Docling's picture data to `image_data` dict for asset extraction.
2. **Font extraction:** Use Docling's provenance bboxes to extract actual font info for `styles.json`.
3. **Sync support:** Extend `sync.py` to handle PDF-sourced sidedocs (rebuild via WeasyPrint instead of python-docx).
4. **CI configuration:** Add `pdf` marker to CI matrix so PDF tests run separately (Docling model download is slow).
5. **WeasyPrint styling:** Use `styles.json` data to generate more accurate CSS (column widths, alignment, colors).
