# Chart Support

Charts are extracted using their cached PNG/EMF fallback image from the `mc:AlternateContent` OOXML wrapper. The live chart XML is not round-tripped in this phase.

- **Detection:** `extract_chart_from_paragraph()` looks for `mc:AlternateContent` with `mc:Choice Requires="c"` containing `c:chart`, then extracts the blip from `mc:Fallback`. Also handles flat `w:drawing` charts (no `mc:AlternateContent`).
- **Fallback behavior:** Charts with no cached image produce `[Chart: no preview available]` as a `paragraph` block (not a `chart` block).
- **EMF/WMF:** These metafile formats are validated by checking magic bytes first, then skip PIL validation (since PIL cannot open them).
- **Ordering rule:** Chart detection must run before image extraction in `_process_paragraph()`. Chart drawings contain both `c:chart` and an `a:blip` — running image extraction first silently consumes the chart as a regular image.
- **Reconstruction:** Chart blocks reconstruct as embedded images (the cached fallback). Full chart fidelity (JON-108) is not yet implemented.
- **`chart_metadata`:** Currently stores `{"chart_rel_id": ...}` for charts with a resolved relationship ID. Degraded chart paragraphs (no preview / validation error) also preserve `chart_rel_id` in `chart_metadata` when one is available; `None` only when no relationship ID can be resolved. Full chart data (type, series, labels) reserved for JON-107.
