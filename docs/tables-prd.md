# PRD: Table Support for Sidedoc

## Introduction

Add full table support to Sidedoc, enabling AI agents to read, edit, restructure, and create tables in Word documents while preserving formatting fidelity on roundtrip. Tables are ubiquitous in enterprise documents (financial reports, project plans, specifications) and were explicitly deferred from MVP as "Not Supported."

This feature enables AI agents to work with tabular data using standard GFM (GitHub Flavored Markdown) pipe table syntax while the system preserves complex Word formatting—borders, shading, column widths, merged cells, and alignment—for human consumption.

**Project Repository:** `sidedoc` (Python package)
**Author:** Jonathan Gardner
**Status:** Complete — All phases implemented and merged (PR #40, #42)

## Goals

- Extract tables from docx and represent them as GFM pipe tables in content.md
- Preserve full table formatting (borders, shading, widths, alignment) during roundtrip
- Enable AI agents to edit cell content with inline formatting (bold, italic, hyperlinks)
- Enable AI agents to add/remove rows and columns with smart formatting inheritance
- Preserve merged cells via metadata (content.md shows unmerged structure)
- Maintain backward compatibility with existing sidedoc archives
- Achieve 95%+ visual fidelity on roundtrip for supported table scenarios

## Non-Goals (Out of Scope)

- **Nested tables** (tables inside table cells) — complex layout, rare in practice
- **Table formulas** — extracted as static text, not evaluated
- **Conditional formatting** — cell styling based on values
- **Auto-fit behaviors** — column width algorithms
- **Vertical text in cells** — preserve opaquely if present
- **Drawing objects in cells** — shapes, SmartArt within tables

## Target Users

1. **AI developers** building document processing pipelines who need AI to read/edit tabular data
2. **Enterprise document teams** processing Word documents with financial, legal, or operational tables
3. **Claude Code users** who want to work with Word documents containing tables efficiently

## User Stories

### Phase 1: Basic Table Extraction & Rebuild

#### US-T01: Extract tables from docx to markdown
**Description:** As an AI developer, I want tables extracted as GFM pipe tables so that I can read and process tabular data efficiently.

**Acceptance Criteria:**
- [x] Tables in docx are extracted as GFM pipe table syntax in content.md
- [x] Column alignment is represented using GFM syntax (`:---|`, `:---:|`, `---:|`)
- [x] Each table becomes a block with type "table" in structure.json
- [x] structure.json records table dimensions (rows, cols) and cell metadata
- [x] Empty cells are preserved as empty pipe segments `| |`
- [x] Typecheck passes
- [x] Unit tests cover simple, multi-row, and multi-column tables

#### US-T02: Store table structure metadata
**Description:** As a developer, I need table structure stored in structure.json so that tables can be reconstructed accurately.

**Acceptance Criteria:**
- [x] structure.json stores `rows`, `cols`, `cells` array for each table block
- [x] Each cell has `row`, `col`, `content_hash`, and `docx_cell_paragraphs` mapping
- [x] `header_rows` field indicates which rows are header rows
- [x] Cell positions enable change detection during sync
- [x] Typecheck passes
- [x] Unit tests verify structure schema compliance

#### US-T03: Store table formatting metadata
**Description:** As a developer, I need table formatting stored in styles.json so that visual appearance survives roundtrip.

**Acceptance Criteria:**
- [x] styles.json stores `table_style` (Word built-in style name)
- [x] styles.json stores `column_widths` array
- [x] styles.json stores `table_alignment` (left, center, right)
- [x] Cell-level formatting stored in `cell_styles` keyed by "row,col"
- [x] Cell styles include: alignment, vertical_alignment, background_color, borders
- [x] Only non-default cells are stored (compact representation)
- [x] Typecheck passes
- [x] Unit tests verify formatting extraction for various table styles

#### US-T04: Reconstruct tables in docx from sidedoc
**Description:** As a user, I want tables in the rebuilt docx to look identical to the original so that formatting is preserved.

**Acceptance Criteria:**
- [x] GFM pipe table syntax converts to docx tables via `doc.add_table()`
- [x] Column widths match original
- [x] Cell alignment (horizontal and vertical) applied correctly
- [x] Borders render correctly on all sides
- [x] Cell shading/background colors applied
- [ ] Tables work in Microsoft Word, Google Docs, and LibreOffice
- [x] Typecheck passes
- [ ] Visual comparison confirms 95%+ fidelity

#### US-T05: Handle table edge cases during extraction
**Description:** As a developer, I need edge cases handled gracefully so that extraction doesn't fail on complex documents.

**Acceptance Criteria:**
- [x] Empty tables (0 rows or 0 cols) handled gracefully
- [x] Tables with only header rows work correctly
- [x] Very wide tables (20+ columns) preserved correctly
- [x] Very tall tables (100+ rows) processed efficiently
- [x] Tables with special characters in cells (pipes, backticks) are escaped
- [x] Typecheck passes
- [x] Unit tests cover all edge cases

---

### Phase 2: Cell Content Editing + Sync

#### US-T06: Sync cell content changes to docx
**Description:** As an AI agent, I want to edit cell text and have changes reflected in the synced docx.

**Acceptance Criteria:**
- [x] Cell content hash changes are detected during sync
- [x] Modified cell content updates in docx while preserving cell formatting
- [x] Unchanged cells retain exact original formatting
- [x] Sync handles multiple cell edits in same table
- [x] Typecheck passes
- [x] Integration test confirms cell edit sync works

#### US-T07: Support inline formatting in table cells
**Description:** As an AI agent, I want to use bold, italic, and hyperlinks in table cells.

**Acceptance Criteria:**
- [x] `**bold**` in cell content renders as bold in docx cell
- [x] `*italic*` in cell content renders as italic
- [x] `[text](url)` in cell content creates clickable hyperlink
- [x] Mixed formatting (`**bold** and *italic*`) works correctly
- [x] Inline formatting preserved on roundtrip
- [x] Typecheck passes
- [x] Unit tests cover inline formatting in cells

#### US-T08: Preserve cell formatting during content edits
**Description:** As a user, I want cell formatting preserved when AI edits cell content.

**Acceptance Criteria:**
- [x] Editing cell text preserves cell background color
- [x] Editing cell text preserves cell borders
- [x] Editing cell text preserves cell alignment
- [x] Editing cell text preserves font settings
- [x] Typecheck passes
- [x] Integration test confirms formatting preservation

---

### Phase 3: Structural Manipulation

#### US-T09: Add rows to tables via markdown
**Description:** As an AI agent, I want to add new rows to tables by editing content.md.

**Acceptance Criteria:**
- [x] Adding a row in GFM table adds row in synced docx
- [x] New row inherits formatting from adjacent row (smart inheritance)
- [x] Row can be added at beginning, middle, or end of table
- [x] Multiple rows can be added in single sync
- [x] Typecheck passes
- [x] Unit tests verify row addition scenarios

#### US-T10: Remove rows from tables via markdown
**Description:** As an AI agent, I want to remove rows from tables by editing content.md.

**Acceptance Criteria:**
- [x] Removing a row in GFM table removes row in synced docx
- [x] Remaining rows maintain correct formatting
- [x] Removing header row is handled gracefully (warning or new header)
- [x] Multiple rows can be removed in single sync
- [x] Typecheck passes
- [x] Unit tests verify row removal scenarios

#### US-T11: Add columns to tables via markdown
**Description:** As an AI agent, I want to add new columns to tables by editing content.md.

**Acceptance Criteria:**
- [x] Adding a column in GFM table adds column in synced docx
- [x] New column inherits width from adjacent column
- [x] New column cells inherit formatting from adjacent cells
- [x] Column can be added at beginning, middle, or end
- [x] Typecheck passes
- [x] Unit tests verify column addition scenarios

#### US-T12: Remove columns from tables via markdown
**Description:** As an AI agent, I want to remove columns from tables by editing content.md.

**Acceptance Criteria:**
- [x] Removing a column in GFM table removes column in synced docx
- [x] Remaining columns maintain correct formatting and widths
- [x] Multiple columns can be removed in single sync
- [x] Typecheck passes
- [x] Unit tests verify column removal scenarios

---

### Phase 4: Full Formatting Fidelity

#### US-T13: Extract and preserve merged cells
**Description:** As a user, I want merged cells preserved so that complex table layouts survive roundtrip.

**Acceptance Criteria:**
- [x] Horizontally merged cells detected and stored in structure.json
- [x] Vertically merged cells detected and stored in structure.json
- [x] `merged_cells` array contains `{start_row, start_col, row_span, col_span}`
- [x] content.md shows all cell positions (secondary merge cells are empty)
- [x] Rebuilt docx applies merges correctly via `cell.merge()`
- [x] Typecheck passes
- [x] Unit tests cover horizontal, vertical, and complex merges

#### US-T14: Extract all cell border styles
**Description:** As a user, I want all border styles preserved so that tables look identical.

**Acceptance Criteria:**
- [x] All four borders (top, bottom, left, right) extracted per cell
- [x] Border style (single, double, dashed, etc.) preserved
- [x] Border width preserved
- [x] Border color preserved
- [x] Borders applied correctly during rebuild
- [x] Typecheck passes
- [x] Unit tests verify border extraction for various styles

#### US-T15: Extract cell shading and background colors
**Description:** As a user, I want cell colors preserved so that formatted tables look correct.

**Acceptance Criteria:**
- [x] Cell background/shading color extracted as hex value
- [x] Pattern fills preserved where applicable
- [x] Colors applied correctly during rebuild
- [x] Header row styling preserved
- [x] Alternating row colors preserved (if using table style)
- [x] Typecheck passes
- [x] Unit tests verify color extraction

#### US-T16: Handle header row designation
**Description:** As a user, I want header rows marked so that accessibility and styling are preserved.

**Acceptance Criteria:**
- [x] Header rows identified during extraction
- [x] `header_rows` field in structure.json indicates header count
- [x] Header row styling preserved separately
- [x] Rebuilt table marks rows as headers for accessibility
- [x] Typecheck passes
- [x] Unit tests verify header handling

#### US-T17: Validate sidedoc with tables
**Description:** As a user, I want validation to check table integrity so that I catch issues before building.

**Acceptance Criteria:**
- [x] `sidedoc validate` checks table structure in structure.json
- [x] Validation confirms cell count matches GFM table in content.md
- [x] Validation checks merged cell regions don't overlap
- [x] Validation warns if table formatting is incomplete
- [x] Clear error messages for table-related validation failures
- [x] Typecheck passes
- [x] Unit tests cover validation scenarios

---

### Phase 5: Documentation & Polish

#### US-T18: Update test fixtures with table examples
**Description:** As a developer, I need test fixtures that include tables so that automated tests verify the feature.

**Acceptance Criteria:**
- [x] Create `tests/fixtures/tables_simple.docx` with basic 3x3 table
- [x] Create `tests/fixtures/tables_formatted.docx` with borders, shading
- [x] Create `tests/fixtures/tables_merged.docx` with merged cells
- [x] Create `tests/fixtures/tables_complex.docx` with all features
- [x] Document fixture contents in test file comments
- [x] Typecheck passes

#### US-T19: Update CLI help and documentation
**Description:** As a user, I want documentation updated so that I understand table support is available.

**Acceptance Criteria:**
- [x] README.md updated with table support in "Supported Elements" section
- [ ] Format specification updated with table structure/styles schema
- [ ] CHANGELOG.md entry for table feature
- [ ] Examples showing table extraction and reconstruction
- [x] Typecheck passes

#### US-T20: Create table roundtrip integration tests
**Description:** As a developer, I need comprehensive integration tests to ensure table quality.

**Acceptance Criteria:**
- [x] Roundtrip test: extract → build for simple tables
- [x] Roundtrip test: extract → edit → sync → build for cell edits
- [x] Roundtrip test: structural changes (add/remove rows/cols)
- [x] Roundtrip test: complex tables with merges and formatting
- [ ] Visual diff comparison in CI pipeline
- [ ] 95%+ fidelity metric automated
- [x] Typecheck passes

## Functional Requirements

- **FR-T1:** Extract docx tables as GFM pipe table syntax in content.md
- **FR-T2:** Store table structure (rows, cols, cells, merged_cells) in structure.json
- **FR-T3:** Store table formatting (widths, borders, shading, alignment) in styles.json
- **FR-T4:** Reconstruct tables from sidedoc using `doc.add_table()` and cell formatting
- **FR-T5:** Detect cell content changes during sync via content hashing
- **FR-T6:** Apply smart inheritance when adding rows/columns (formatting from adjacent)
- **FR-T7:** Preserve merged cells via metadata, not markdown syntax
- **FR-T8:** Support inline formatting (bold, italic, hyperlinks) within cells
- **FR-T9:** Escape special characters (pipes, backticks) in cell content
- **FR-T10:** Validate table structure during `sidedoc validate`

## Technical Considerations

### python-docx Table API

Tables are accessed via `doc.tables` and cells via `table.cell(row, col)`:

```python
for table in document.tables:
    for row_idx, row in enumerate(table.rows):
        for col_idx, cell in enumerate(row.cells):
            # Access cell content
            text = cell.text
            # Access cell formatting
            shading = cell._tc.get_or_add_tcPr().get_or_add_shd()
```

### Merged Cell Detection

python-docx doesn't directly expose merge info. Detect via:
- Comparing cell objects (merged cells share same `_tc` element)
- Checking `gridSpan` and `vMerge` in cell XML

### GFM Table Parsing

Use existing markdown parser (marko/mistune) with table extension. Handle:
- Alignment indicators (`:---|`, `:---:|`, `---:|`)
- Escaped pipes in content (`\|`)
- Empty cells

### Structure.json Schema Extension

```json
{
  "id": "block-5",
  "type": "table",
  "docx_table_index": 0,
  "content_start": 200,
  "content_end": 450,
  "rows": 4,
  "cols": 3,
  "header_rows": 1,
  "cells": [
    [
      {"row": 0, "col": 0, "content_hash": "abc123", "docx_cell_paragraphs": [0]},
      {"row": 0, "col": 1, "content_hash": "def456", "docx_cell_paragraphs": [0]},
      {"row": 0, "col": 2, "content_hash": "ghi789", "docx_cell_paragraphs": [0]}
    ]
  ],
  "merged_cells": [
    {"start_row": 2, "start_col": 0, "row_span": 2, "col_span": 1}
  ]
}
```

### Styles.json Schema Extension

```json
{
  "block-5": {
    "table_style": "Grid Table 4 - Accent 1",
    "column_widths": [1.5, 2.0, 1.0],
    "table_alignment": "center",
    "cell_styles": {
      "0,0": {
        "alignment": "center",
        "vertical_alignment": "center",
        "background_color": "D9E2F3",
        "borders": {
          "top": {"style": "single", "width": 4, "color": "4472C4"},
          "bottom": {"style": "single", "width": 4, "color": "4472C4"},
          "left": {"style": "single", "width": 4, "color": "4472C4"},
          "right": {"style": "single", "width": 4, "color": "4472C4"}
        },
        "bold": true
      }
    }
  }
}
```

### Backward Compatibility

- Existing sidedoc archives without tables remain valid
- Sidedoc version in manifest.json indicates table support capability
- Older CLI versions gracefully ignore table metadata they don't understand

## Design Considerations

### Markdown Representation

GFM pipe tables are the standard choice:
- Widely understood by AI models
- Human-readable
- Supported by marko/mistune parsers

Limitations accepted:
- No native merged cell syntax (handled via metadata)
- No native vertical alignment (handled via styles.json)

### Merged Cells in content.md

All cell positions exist in the markdown. Secondary cells of a merge are empty:

```markdown
| Header 1 | Header 2 | Header 3 |
|----------|----------|----------|
| Merged content |  | Value |
|  |  | Value 2 |
```

This keeps content.md parseable while structure.json tracks the actual merges.

### Sync Algorithm Extension

The existing block-level sync extends naturally:
- Table block detected via type="table"
- Cell-level change detection via content hashes
- Row/column count comparison for structural changes
- Smart inheritance for new rows/columns

## Success Metrics

### Fidelity Metrics (Automated)
- **Visual fidelity:** 95%+ match on automated visual diff for test corpus
- **Structure preservation:** 100% row/col count accuracy on roundtrip
- **Formatting preservation:** 100% border/shading accuracy for supported styles

### Capability Metrics (Automated)
- **Acceptance criteria:** 100% of user story acceptance criteria pass
- **Test coverage:** >80% code coverage for table-related code
- **Type safety:** All table code passes mypy type checking

### User Metrics (Manual Testing)
- **Real-world compatibility:** Tables work correctly in 90%+ of sampled enterprise documents
- **AI editing success:** AI can successfully edit cell content in 95%+ of attempts
- **Structural manipulation:** AI can add/remove rows/columns in 90%+ of attempts

## Implementation Phases

### Phase 1: Basic Extraction & Rebuild (US-T01 through US-T05) — Complete
Foundation: extract tables, store structure/formatting, rebuild identical tables. Merged via PR #40.

### Phase 2: Cell Editing + Sync (US-T06 through US-T08) — Complete
Enable AI to edit cell content while preserving formatting. Merged via PR #40.

### Phase 3: Structural Manipulation (US-T09 through US-T12) — Complete
Enable AI to add/remove rows and columns with smart inheritance. Merged via PR #40.

### Phase 4: Full Formatting Fidelity (US-T13 through US-T17) — Complete
Complete formatting: merged cells, all borders, colors, validation. Merged via PR #40, review fixes in PR #42.

### Phase 5: Documentation & Polish (US-T18 through US-T20) — Partial
Test fixtures created (3 of 4). README updated. Roundtrip tests for simple and formatted tables. Remaining: `tables_complex.docx` fixture, CHANGELOG entry, format spec docs, structural/merge roundtrip tests, CI visual diff automation.

## Open Questions

1. **Should we support `mailto:` links in table cells?** Currently deferred with hyperlinks feature.

   **Recommendation:** Follow hyperlinks PRD decision (deferred).
   **Resolution:** Deferred. Hyperlinks in table cells are supported (`[text](url)`), but `mailto:` links remain out of scope.

2. **How should we handle tables with images in cells?** Images in cells are complex.

   **Recommendation:** Extract image reference but flag as "may not roundtrip perfectly."
   **Resolution:** Out of scope per Non-Goals (drawing objects in cells).

3. **Should table formulas be preserved as formula text or computed values?**

   **Recommendation:** Extract as static computed values (formulas are rare and complex).
   **Resolution:** Accepted — formulas extracted as static text per Non-Goals.

4. **How to handle tables that span page breaks?** Word handles this automatically.

   **Recommendation:** No special handling needed; Word manages pagination.
   **Resolution:** Accepted — no special handling implemented. Word manages pagination.

---

## Appendix: Table Extraction Examples

### Example 1: Simple Table

**Input docx table:**
| Name | Role | Start Date |
|------|------|------------|
| Alice | Engineer | 2024-01-15 |
| Bob | Designer | 2024-02-01 |

**Extracted content.md:**
```markdown
| Name | Role | Start Date |
|------|------|------------|
| Alice | Engineer | 2024-01-15 |
| Bob | Designer | 2024-02-01 |
```

**structure.json:**
```json
{
  "id": "block-0",
  "type": "table",
  "docx_table_index": 0,
  "rows": 3,
  "cols": 3,
  "header_rows": 1,
  "cells": [
    [
      {"row": 0, "col": 0, "content_hash": "a1b2c3"},
      {"row": 0, "col": 1, "content_hash": "d4e5f6"},
      {"row": 0, "col": 2, "content_hash": "g7h8i9"}
    ],
    [
      {"row": 1, "col": 0, "content_hash": "j0k1l2"},
      {"row": 1, "col": 1, "content_hash": "m3n4o5"},
      {"row": 1, "col": 2, "content_hash": "p6q7r8"}
    ],
    [
      {"row": 2, "col": 0, "content_hash": "s9t0u1"},
      {"row": 2, "col": 1, "content_hash": "v2w3x4"},
      {"row": 2, "col": 2, "content_hash": "y5z6a7"}
    ]
  ],
  "merged_cells": []
}
```

### Example 2: Table with Merged Cells

**Input docx table (2x3 merge in first column):**
| Category | Q1 | Q2 |
|----------|----|----|
| Revenue | $1M | $1.2M |
| (merged) | $0.8M | $0.9M |

**Extracted content.md:**
```markdown
| Category | Q1 | Q2 |
|----------|----|----|
| Revenue | $1M | $1.2M |
|  | $0.8M | $0.9M |
```

**structure.json merged_cells:**
```json
{
  "merged_cells": [
    {"start_row": 1, "start_col": 0, "row_span": 2, "col_span": 1}
  ]
}
```

### Example 3: AI Adds a Row

**Original content.md:**
```markdown
| Task | Status |
|------|--------|
| Design | Done |
| Build | In Progress |
```

**AI edits to:**
```markdown
| Task | Status |
|------|--------|
| Design | Done |
| Build | In Progress |
| Test | Not Started |
```

**Sync behavior:**
1. Detect row count change (3 → 4)
2. Identify new row at position 3
3. Copy formatting from row 2 (adjacent)
4. Insert row in docx with inherited formatting
5. Update structure.json with new cell metadata
