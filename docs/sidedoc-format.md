# Sidedoc Format

A `.sidedoc/` directory (or `.sdoc` ZIP for distribution) contains markdown content plus formatting and structure metadata.

## Container Files

| File | Required (dir) | Required (ZIP) | Purpose |
|------|:-:|:-:|---------|
| `content.md` | Yes | Yes | Clean markdown that AI reads/writes |
| `styles.json` | Yes | Yes | Formatting information per block |
| `structure.json` | No* | Yes | Block structure, docx paragraph mappings, and section metadata (headers, footers, page setup) |
| `manifest.json` | No* | Yes | Metadata and version info; includes `source_format` (`"docx"` or `"pdf"`) |
| `assets/` | No | No | Images and embedded files |

\* `structure.json` is written during `sidedoc extract` and updated by `sidedoc sync`; `manifest.json` is written during `sidedoc extract` (for PDF sources) or `sidedoc sync` (for DOCX sources).

## Key Concepts

- **Extract:** Convert a `.docx` or `.pdf` file into a Sidedoc container (`content.md` + formatting metadata). PDF extraction requires `pip install sidedoc[pdf]`.
- **Reconstruct (build):** Rebuild the original document from the Sidedoc container. Output format (`.docx` or `.pdf`) is determined automatically from `manifest.json`'s `source_format` field.
- **Sync:** After editing `content.md`, update the `.docx` while preserving original formatting. Non-block metadata (headers/footers, footnotes, columns, page setup) is carried forward from the existing `structure.json` — only the `blocks` array is rebuilt from content. Sync is DOCX-only; PDF sync is not supported.

## Block Types

| Type | Markdown Format | Notes |
|------|-----------------|-------|
| `heading` | `# Title` | Levels 1-6 supported |
| `paragraph` | Plain text | Inline formatting: `**bold**`, `*italic*` |
| `list` | `- bullet` or `1. numbered` | |
| `image` | `![alt](assets/image.png)` | |
| `table` | GFM pipe tables | Merged cells, cell formatting, header rows preserved |
| `hyperlink` | `[text](url)` | Inline within other blocks |
| `chart` | `![Chart](assets/chart1.png)` | Alt text must start with `"Chart"` — this is how reconstruction distinguishes charts from images |

## Headers and Footers

Headers and footers are stored as section metadata in `structure.json` (not as blocks in `content.md`). Each section can have up to six variants: `header_default`, `header_first`, `header_even`, `footer_default`, `footer_first`, `footer_even`.

**Limitation:** Header/footer content is extracted and reconstructed as plain text only. Inline formatting (bold, italic, hyperlinks) within header/footer paragraphs is silently dropped. Images in headers/footers are extracted to `assets/` and restored on build.
