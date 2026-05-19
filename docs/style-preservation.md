# Style Preservation

This document captures implementation details for preserving DOCX paragraph and run formatting across extract, build, and sync.

## Style Dataclass — Paragraph Format Fields

The `Style` dataclass (in `models.py`) carries paragraph-level formatting alongside font and alignment:

- **Indents/spacing** (`left_indent`, `right_indent`, `first_line_indent`, `space_before`, `space_after`): `Optional[int]` in EMUs
- **`line_spacing`**: `Optional[int | float]` — proportional spacing is a float (e.g. `1.5` = 1.5× lines); exact/at-least spacing is an integer EMU value
- **`line_spacing_rule`**: `Optional[str]` — JSON-safe `WD_LINE_SPACING` enum name (e.g. `"EXACTLY"`, `"AT_LEAST"`) needed to interpret integer `line_spacing` values during reconstruction
- **Paragraph flags** (`keep_together`, `keep_with_next`, `page_break_before`): `Optional[bool]`

## Boolean Guard Rule

Always check `is not None` (not truthiness) when applying boolean Style fields. `False` is a meaningful override (e.g. turn off keep_together) and must survive round-trip:

```python
# Correct
if block_style.get("keep_together") is not None:
    pf.keep_together = block_style["keep_together"]

# Wrong — silently drops explicit False
if block_style.get("keep_together"):
    pf.keep_together = block_style["keep_together"]
```

## Per-Run Font Formatting vs. Shared Style Mutation

When applying font overrides during reconstruction, always write to individual runs (`run.font.name`, `run.font.size`), not to `para.style.font`. The `para.style` object is shared across all paragraphs using the same docx style — mutating it changes every paragraph that uses that style, not just the current one:

```python
# Correct — direct run formatting is the override layer above style defaults
for run in para.runs:
    run.font.name = block_style["font_name"]

# Wrong — mutates the shared style object, affecting all paragraphs with that style
para.style.font.name = block_style["font_name"]
```

## `docx_style` Application

`docx_style` is applied first in `_apply_block_formatting()` so style defaults take effect before direct overrides. Three values are intentionally skipped:

- `"Normal"` — default style, no-op assignment can fail on read-only paragraphs
- `"Table"` — table cell paragraphs use a separate `_apply_cell_styles` path
- `"TextBox"` — text box paragraphs have their own reconstruction path

When a custom style name is not found in the target document, a `UserWarning` is emitted and formatting falls back to Normal (no exception raised).
