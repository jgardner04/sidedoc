# PDF Pipeline Hardening — Design Spec

**Date:** 2026-06-04
**Status:** Design approved, implementation in progress
**Related:** PR #61 (JON-126, PDF extraction & reconstruction), branch
`jonathan/jon-126-explore-pdf-to-sidedoc-pipeline-using-vision-models`

## Context

PR #61 added PDF round-trip support (`extract doc.pdf → .sidedoc/ → build → doc.pdf`) via IBM
Docling (extract) and WeasyPrint (reconstruct). A four-agent PR review confirmed the core is sound
(lazy optional imports, `source_format` routing, the path-traversal guard logic, and the
`content_hash` fix are all correct), but surfaced a cluster of **silent content-loss** and
**table-fidelity** issues plus one untested security control. This spec covers the pre-merge
remediation: C1–C3 and I1–I5 from the review.

The unifying defect: several code paths drop document content (unrecognized Docling items, a
dropped/desynced table, skipped images, a PDF rendered with unloadable assets) **beneath a `✓`
success line, with nothing on stderr** — data loss reported as success. The fix is a consistent
warn-and-continue policy with an opt-in `--strict` mode, plus correctness fixes to table rendering
and metadata.

## Goals

- No content dropped silently: every drop/skip surfaces a `Warning:` on stderr.
- `--strict` makes any drop a hard (non-zero) failure for CI/pipelines; default stays best-effort.
- Tables round-trip faithfully: header-less tables don't render a bogus bold header; merged cells
  render with `colspan`/`rowspan`; content (GFM) and `table_metadata` never disagree.
- The path-traversal guard on untrusted `.sdoc` assets has test coverage.

## Non-goals

- PDF image *extraction* (still skipped — but now warned). Tracked separately.
- PDF layout fidelity beyond tables/headers (A4 generic CSS stays).
- PDF sync (still unsupported).

## Decisions (from brainstorming)

1. **Scope:** all pre-merge findings — C1–C3, I1–I5 (suggestions S1–S9 deferred).
2. **Drop policy:** warn-and-continue by default; new `--strict` flag turns any warning into a
   non-zero exit. Mirrors the existing `validate` warnings-list pattern and the existing
   `Warning: --track-changes ignored for PDF input` precedent.
3. **Header-less tables:** resolve via **HTML table rendering** in `reconstruct_pdf` (full control
   over header vs no-header, and enables merged cells), implemented as an overlay over content.md
   (Approach A) so content.md stays the authoritative source of text.

## Architecture

### Cross-cutting: the warning channel

Library functions **report**, the CLI **decides**.

> **Implementation note (refined during build):** rather than change
> `extract_pdf_document`'s return signature to a 4-tuple (which would churn ~16 existing
> call sites and every future caller), the warning channel is **logger-based**. The PDF
> helpers emit `logging.WARNING` on their module loggers (`sidedoc.extract_pdf`,
> `sidedoc.reconstruct_pdf`); `build_pdf_from_sidedoc` additionally captures the
> `weasyprint` logger and re-emits asset failures on its own logger. This unifies extract-
> and build-side warnings under the `sidedoc` logger and keeps all signatures stable.

- The CLI wraps the PDF extract/build call in a `_collect_pdf_warnings()` context manager
  that attaches a handler to the `sidedoc` logger and collects WARNING+ messages.
- `_emit_pdf_warnings()` prints each as `Warning: <msg>` to stderr (`err=True`); with the
  `✓` line printed and exit 0 — **unless** `--strict` is set and warnings are non-empty, in
  which case it exits `EXIT_ERROR` *after* printing the warnings (the `✓` line is suppressed).
- `--strict` is a new `is_flag` option on both `extract` and `build`.

This keeps the library pure/testable (assert via `caplog`) and policy in one place.

### Component 1 — Extraction hardening (`src/sidedoc/extract_pdf.py`)

A `warnings: list[str]` is accumulated through `extract_pdf_document` and returned.

1. **Robust item dispatch (C3).** *(Refined during build:)* the original plan called for
   `isinstance` against Docling's item classes, but that would (a) force a real `docling` import,
   breaking the no-`docling` boundary, and (b) break the suite's duck-typed fake docs. Instead,
   dispatch keys on item-class name **and** `label`, recognizing `"ListItem"` alongside `"TextItem"`
   (`_TEXT_ITEM_TYPES` / `_TEXT_ITEM_LABELS`). This fixes the same latent list-drop bug
   (`ListItem` subclasses `TextItem`, so `type().__name__ == "TextItem"` previously missed it) while
   staying import-free and testable.
2. **Terminal `else` (C3).** Any item matching no branch →
   `warnings.append(f"Skipped unsupported PDF element: {type(item).__name__}/{label}")`.
3. **Table correlation by `self_ref`, not counting (I1).** Build a dict of export-dict tables keyed
   by `self_ref`; resolve each `TableItem` via its `self_ref`. On miss → warn and skip that table
   only (no positional `table_idx`, so no cascading desync). Positional fallback only if `self_ref`
   is unavailable on the pinned Docling version, still warning on any out-of-range case.
4. **Bounds-guard parity (I2).** `_build_table_metadata` gains the same
   `if row < num_rows and col < num_cols` guard `_table_to_gfm` already has, so the GFM grid and the
   metadata agree on which cells exist.
5. **Picture tally (I4).** Count skipped `PictureItem`s; emit one summary warning
   `N image(s) skipped (PDF image extraction not yet supported)`.

`header_rows` in metadata becomes the single source of header truth (consumed by the build path).

### Component 2 — Table HTML rendering (`src/sidedoc/reconstruct_pdf.py`)

Approach A (content.md authoritative for text; `table_metadata` an overlay for structure),
implemented by **segmentation** rather than mistune-output DOM surgery (no HTML-parser dependency,
no coupling to mistune's markup):

1. Read `content.md` (text source) and, via `SidedocStore`, `structure.json` (table blocks +
   `table_metadata`, in document order).
2. Segment `content.md` into table regions and non-table regions using the existing
   `is_table_row()` / `is_table_separator_line()` from `reconstruct.py`. Because
   `blocks_to_markdown` joins blocks with a single `\n`, **adjacent table blocks form one
   unbroken run of pipe lines** — split each run into individual tables by their separator
   lines (`_split_gfm_tables`) so per-table metadata correlates one-to-one (otherwise two
   adjacent tables collapse into one and falsely trip the drift fallback / `--strict`).
3. Non-table regions → `mistune.html()` as today.
4. Each table region → build HTML directly:
   - parse the grid text with `parse_gfm_table()` (reused from `reconstruct.py`);
   - correlate with the next table block's `table_metadata` (document order);
   - emit `<thead>` for the first `header_rows` rows **only when `header_rows > 0`** (fixes C2);
   - emit `colspan`/`rowspan` from `merged_cells`, skipping covered cells (fixes I3);
   - apply `text-align` from `column_alignments`.
5. Concatenate segments in order into the document body; existing `_CSS`, `@page`, and the
   directory-vs-archive asset handling (incl. the path-traversal guard) are unchanged.

**Fail-safe (drift):** if `structure.json` is missing, or the count of detected table regions ≠ the
count of table blocks in metadata, skip the overlay — render tables with plain `mistune.html()` —
and append a warning. Text is never lost; only the structural overlay is skipped.

The shared CSS keeps `th { font-weight: bold; background: … }`, but headerless tables now emit no
`<th>`, so they render as plain bodies.

### Component 3 — Build-side asset surfacing (`src/sidedoc/reconstruct_pdf.py`)

WeasyPrint logs missing/unloadable assets to the `weasyprint` logger at WARNING and does not raise.
Around each `write_pdf()` call, attach a temporary `logging.Handler` that captures WARNING+ records,
convert them to `warnings` entries (e.g. `PDF asset issue: <message>`), and detach in a `finally`.
These flow through the CLI channel and trip `--strict`.

### Component 4 — Security test coverage (C1)

No code change — add a test exercising the existing
`raise ValueError("Unsafe path traversal detected: …")` branch in the `.sdoc` asset-extraction path.

## Data flow

```
extract:  PDF ──Docling──▶ items ──isinstance dispatch──▶ blocks + table_metadata
                                         │
                                         └─▶ warnings (unsupported items, dropped tables, skipped images)
          (blocks, images, sections, warnings) ──▶ cli.extract ──▶ stderr warnings; ✓ / strict-exit

build:    content.md ─┬─ non-table ──mistune──┐
                      └─ table region ──parse_gfm_table + table_metadata──▶ HTML table
          structure.json ──table_metadata (header_rows, merged_cells, alignments)──┘
          assembled HTML ──WeasyPrint(write_pdf)──▶ PDF
                                  │
                                  └─ weasyprint logger ──▶ warnings (missing assets)
          warnings ──▶ cli.build ──▶ stderr warnings; ✓ / strict-exit
```

## Error handling

| Situation | Behavior (default) | `--strict` |
|-----------|--------------------|-----------|
| Unrecognized Docling item | `Warning:`, item omitted | non-zero exit |
| Table `self_ref` unresolved | `Warning:`, that table skipped | non-zero exit |
| Out-of-bounds table cell | dropped from GFM and metadata (consistent) | — |
| Image (`PictureItem`) | `Warning:` with count, image skipped | non-zero exit |
| `structure.json` missing / table count drift | `Warning:`, plain-GFM table fallback | non-zero exit |
| WeasyPrint missing asset | `Warning:` from captured log, PDF still written | non-zero exit |
| Path traversal in `.sdoc` asset | `ValueError` raised (unchanged) | raised |

## Testing strategy (TDD — write the failing test first)

In `tests/test_extract_pdf.py` / `tests/test_pdf_optional_boundaries.py` (extend the fake-Docling-doc
pattern already there) and `tests/test_reconstruct_pdf.py`:

1. **C1** `test_build_pdf_rejects_traversal_asset`: craft a `.sdoc` with an `assets/../evil.txt`
   entry; assert `ValueError("Unsafe path traversal detected…")` and nothing written outside the
   render root.
2. **C2** `test_headerless_vs_header_table_render_differently`: a headerless table renders no `<th>`
   (no bold header); a header table renders `<thead>`. Replaces the non-discriminating
   `"---" in lines[1]` assertion.
3. **C3a** `test_list_item_round_trips`: a real `ListItem` (or `isinstance` path) produces a `list`
   block — guards the `type().__name__` fragility.
4. **C3b** `test_unsupported_item_warns`: an unrecognized item type yields a warning and is omitted.
5. **I1** `test_table_self_ref_miss_warns_without_desync`: an unresolved table warns and does not
   shift subsequent tables' content.
6. **I2** `test_build_table_metadata_bounds_guard`: out-of-bounds cells excluded from metadata,
   matching the GFM grid.
7. **I3** `test_merged_cell_renders_colspan_rowspan`: a `col_span:2` cell produces `colspan="2"` and
   omits the covered cell.
8. **I4** `test_skipped_images_warn`: a `PictureItem` doc yields the image-skipped warning with count.
9. **I5** `test_missing_asset_warns_on_build`: a content.md referencing a missing asset surfaces a
   warning captured from the weasyprint logger.
10. **strict** `test_strict_mode_nonzero_exit`: `extract --strict` / `build --strict` exit non-zero
    when warnings are present, zero when not.

## Verification

- `pytest -m pdf` and `pytest -m "not pdf"` both green; `pytest tests/` overall green.
- `mypy src/sidedoc/extract_pdf.py src/sidedoc/reconstruct_pdf.py src/sidedoc/cli.py` clean.
- Manual: `sidedoc extract tests/fixtures/tables.pdf` → `sidedoc build` round-trips; a headerless
  table no longer renders a bold first row; an image-bearing PDF prints the skip warning;
  `--strict` exits non-zero on that PDF; a crafted traversal `.sdoc` is rejected.

## Reused existing code (avoid reinvention)

- `reconstruct.py`: `parse_gfm_table()` (grid + alignments), `is_table_row()`,
  `is_table_separator_line()`, and `create_table_from_gfm()` as the DOCX reference for how
  `header_rows`/`merged_cells` are consumed.
- `extract_pdf.py`: `require_docling()` pattern for the new lazy item-class import helper.
- `cli.py`: the `validate` command's warnings-list-to-stderr pattern; existing `EXIT_*` codes.
- `models.py`: `Block.table_metadata` keys (`rows`, `cols`, `cells`, `column_alignments`,
  `header_rows`, `merged_cells`).
