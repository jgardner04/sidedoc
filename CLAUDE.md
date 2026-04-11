# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Sidedoc is an AI-native document format that separates content from formatting. It enables efficient AI interaction with documents while preserving rich formatting for human consumption. The canonical format is a `.sidedoc/` directory containing markdown content and formatting metadata. A `.sdoc` ZIP archive is used for distribution and sharing.

**Status:** MVP complete with hyperlink, track changes, table, headers/footers, chart, and PDF support (extraction, reconstruction).

## Development Philosophy

### Test-Driven Development (TDD) — MANDATORY

**All code in this project MUST be developed using Test-Driven Development.**

This is a non-negotiable requirement for all contributions, whether from human developers or AI agents.

#### TDD Workflow

1. **Red** — Write a failing test first
   - Write a test that describes the behavior you want to implement
   - Run the test and verify it fails
   - The test should fail because the feature doesn't exist yet

2. **Green** — Write minimal code to make the test pass
   - Implement only enough code to make the test pass
   - Don't worry about perfection or edge cases yet
   - Run the test and verify it passes

3. **Refactor** — Improve the code while keeping tests green
   - Clean up the implementation
   - Remove duplication
   - Improve naming and structure
   - Run tests after each change to ensure they still pass

#### TDD Rules for This Project

- **Never write production code without a failing test first**
- **Never write more production code than needed to pass the test**
- **Never commit code without passing tests**
- Tests should be:
  - Clear and readable (they serve as documentation)
  - Focused on one behavior per test
  - Independent (can run in any order)
  - Fast (no unnecessary I/O or sleeps)

#### Example TDD Workflow

```bash
# 1. Write a failing test
# Edit tests/test_extract.py to add a test for parsing headings

# 2. Run the test and see it fail
pytest tests/test_extract.py::test_extract_heading -v

# 3. Implement minimal code to pass the test
# Edit src/sidedoc/extract.py

# 4. Run the test and see it pass
pytest tests/test_extract.py::test_extract_heading -v

# 5. Refactor if needed, keeping tests green
pytest tests/test_extract.py::test_extract_heading -v

# 6. Move to next test
```

#### When Working on Features

For any new feature or bug fix:

1. **Start with a test** — Always begin by writing a test that fails
2. **Implement incrementally** — Make the test pass with minimal code
3. **Add more tests** — Cover edge cases and error conditions
4. **Refactor** — Clean up the implementation while keeping all tests passing
5. **Verify coverage** — Run `pytest --cov=sidedoc` to ensure adequate coverage

**If you're an AI agent:** Before writing any implementation code, you must first write the test. If a user asks you to implement something, your first response should be to write the failing test.

## Specifications

- [Track Changes PRD](docs/prd-track-changes.md) — CriticMarkup-based track changes support
- [Tables PRD](docs/tables-prd.md) — Complete table support (all phases implemented)
- [PRD Status](docs/prd.json) — Current feature tracking

## Architecture

Package structure:

```
src/sidedoc/
├── __init__.py
├── cli.py              # CLI entry points (click), includes validate command
├── constants.py        # Shared constants (extensions, limits, patterns)
├── extract.py          # docx → sidedoc (paragraphs, tables, images, charts, headers/footers)
├── extract_pdf.py      # pdf → sidedoc via Docling (optional, requires [pdf] extras)
├── models.py           # Block, Style, Manifest, TrackChange dataclasses
├── package.py          # Archive/directory creation helpers, block serialization
├── reconstruct.py      # sidedoc → docx; owns inline formatting, table creation, block styling, header/footer reconstruction
├── reconstruct_pdf.py  # sidedoc → pdf via WeasyPrint (optional, requires [pdf] extras)
├── store.py            # Read-only abstraction over directory/ZIP
├── sync.py             # edited content → updated docx (imports formatting from reconstruct.py)
└── utils.py            # shared utilities
```

## Key Concepts

- **Extract:** Convert a `.docx` or `.pdf` file into a Sidedoc container (content.md + formatting metadata). PDF extraction requires `pip install sidedoc[pdf]`.
- **Reconstruct (build):** Rebuild the original document from the Sidedoc container. Output format (`.docx` or `.pdf`) is determined automatically from `manifest.json`'s `source_format` field.
- **Sync:** After editing content.md, update the .docx while preserving original formatting. Non-block metadata (headers/footers, footnotes, columns, page setup) is carried forward from the existing `structure.json` — only the `blocks` array is rebuilt from content. (DOCX only — PDF sync not yet supported.)

### Block Types

| Type | Markdown Format | Notes |
|------|-----------------|-------|
| `heading` | `# Title` | Levels 1-6 supported |
| `paragraph` | Plain text | Inline formatting: `**bold**`, `*italic*` |
| `list` | `- bullet` or `1. numbered` | |
| `image` | `![alt](assets/image.png)` | |
| `table` | GFM pipe tables | Merged cells, cell formatting, header rows preserved |
| `hyperlink` | `[text](url)` | Inline within other blocks |
| `chart` | `![Chart](assets/chart1.png)` | Alt text **must** start with `"Chart"` — this is how reconstruction distinguishes charts from images |

### Headers and Footers

Headers and footers are stored as section metadata in `structure.json` (not as blocks in `content.md`). Each section can have up to six variants: `header_default`, `header_first`, `header_even`, `footer_default`, `footer_first`, `footer_even`.

**Limitation:** Header/footer content is extracted and reconstructed as **plain text only**. Inline formatting (bold, italic, hyperlinks) within header/footer paragraphs is silently dropped. Images in headers/footers are extracted to `assets/` and restored on build.

### Chart Support

Charts are extracted using their cached PNG/EMF fallback image from the `mc:AlternateContent` OOXML wrapper. The live chart XML is not round-tripped in this phase.

- **Detection:** `extract_chart_from_paragraph()` looks for `mc:AlternateContent` with `mc:Choice Requires="c"` containing `c:chart`, then extracts the blip from `mc:Fallback`. Also handles flat `w:drawing` charts (no `mc:AlternateContent`).
- **Fallback behavior:** Charts with no cached image produce `[Chart: no preview available]` as a `paragraph` block (not a `chart` block).
- **EMF/WMF:** These metafile formats are validated by checking magic bytes first, then skip PIL validation (since PIL cannot open them).
- **Ordering rule:** Chart detection must run before image extraction in `_process_paragraph()`. Chart drawings contain both `c:chart` and an `a:blip` — running image extraction first silently consumes the chart as a regular image.
- **Reconstruction:** Chart blocks reconstruct as embedded images (the cached fallback). Full chart fidelity (JON-108) is not yet implemented.
- **`chart_metadata`:** Currently stores `{"chart_rel_id": ...}` for charts with a resolved relationship ID. Degraded chart paragraphs (no preview / validation error) also preserve `chart_rel_id` in `chart_metadata` when one is available; `None` only when no relationship ID can be resolved. Full chart data (type, series, labels) reserved for JON-107.

### PDF Support

PDF extraction uses Docling (`extract_pdf.py`) and reconstruction uses WeasyPrint (`reconstruct_pdf.py`). Both require `pip install sidedoc[pdf]`.

**Pitfalls to avoid:**

- **`mistune.html()` is the correct API.** Use `mistune.html(content_md)` directly — do not wrap it in a custom class or use `mistune.create_markdown()`. The function returns a plain `str` and is the simplest correct approach.
- **GFM separator double-insertion.** `_table_to_gfm()` has two code paths: one that appends a separator after a detected header row, and a fallback that inserts one after row 0 when no headers are detected. These must be `if/else` — never two independent `if` checks — or headerless tables will get two separator rows.
- **Do not coerce `header_rows` to `max(1, ...)`** — Docling tables without any `column_header=True` cells legitimately have `header_rows=0`. Forcing it to 1 creates incorrect GFM (treats a data row as a header) and corrupts `table_metadata`.
- **Guard optional heavy deps at module level.** `fitz` (PyMuPDF), `weasyprint`, and `docling` are all optional. Each module that needs them must use a top-level `try/except ImportError` block and set a `HAS_*` flag. Tests skip via `pytest.mark.skipif(not HAS_PYMUPDF, ...)`.
- **Skip `PictureItem` blocks when image extraction is unimplemented.** Do not emit a block with a broken asset reference. Use `continue` to skip the item entirely; the block list stays clean and no dangling `![alt](assets/...)` references appear in `content.md`.
- **WeasyPrint requires `base_url`.** `weasyprint.HTML(string=full_html)` cannot resolve relative paths to assets. Always pass `base_url=str(Path(sidedoc_path).resolve())` so embedded images in `assets/` resolve correctly.

### Table Support (Phase 2)

Tables are extracted as GFM (GitHub Flavored Markdown) pipe table syntax:

```markdown
| Name | Role | Start Date |
| --- | --- | --- |
| Alice | Engineer | 2024-01-15 |
```

- **Alignment:** `---` (default left), `:---` (explicit left), `:---:` (center), `---:` (right)
- **Escaping:** Pipe characters in content escaped as `\|`
- **Metadata:** `table_metadata` in Block stores rows, cols, cells, column_alignments, docx_table_index, header_rows, merged_cells
- **Styling:** `table_formatting` in Style stores column_widths, table_alignment, table_style, cell_styles (including background colors and pattern fills like `diagStripe`, `horzStripe`)

## Sidedoc Format

A `.sidedoc/` directory (or `.sdoc` ZIP for distribution) contains:

| File | Required (dir) | Required (ZIP) | Purpose |
|------|:-:|:-:|---------|
| `content.md` | Yes | Yes | Clean markdown that AI reads/writes |
| `styles.json` | Yes | Yes | Formatting information per block |
| `structure.json` | No* | Yes | Block structure, docx paragraph mappings, and section metadata (headers, footers, page setup) |
| `manifest.json` | No* | Yes | Metadata and version info; includes `source_format` ("docx" or "pdf") |
| `assets/` | No | No | Images and embedded files |

\* `structure.json` is written during `sidedoc extract` and updated by `sidedoc sync`; `manifest.json` is written during `sidedoc extract` (for PDF sources) or `sidedoc sync` (for DOCX sources)

## Benchmarks

Benchmarking suite compares Sidedoc against alternative document processing pipelines (sidedoc, pandoc, raw_docx, ooxml, docint) across LLM tasks.

```bash
# Run benchmarks
python -m benchmarks.run_benchmark --pipeline sidedoc --corpus synthetic

# Run with format fidelity scoring (round-trip preservation)
python -m benchmarks.run_benchmark --pipeline sidedoc --pipeline pandoc --fidelity

# Generate report
python -m benchmarks.generate_report benchmarks/results/benchmark-latest.json
```

**Format Fidelity**: Measures what each pipeline preserves on extract→rebuild round-trip across 5 dimensions: structure (heading levels, counts), formatting (bold/italic/font per run), tables (structure, merged cells, styles), hyperlinks (text+URL pairs), and track changes (insertions/deletions/authors). Only sidedoc and pandoc support rebuild.

Full documentation: [`benchmarks/README.md`](benchmarks/README.md) | Published results: [`website/docs/benchmarks.md`](website/docs/benchmarks.md)

## Development Commands

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=sidedoc

# Run tests excluding PDF (skips tests requiring docling/weasyprint)
pytest -m "not pdf"

# Type checking
mypy src/

# CLI commands (all implemented)
sidedoc extract document.docx                    # Extract to document.sidedoc/ directory
sidedoc extract document.docx --pack             # Extract to document.sdoc ZIP
sidedoc extract document.docx --force            # Overwrite existing output
sidedoc extract document.docx --track-changes    # Force extract track changes
sidedoc extract document.docx --no-track-changes # Accept all changes
sidedoc extract document.pdf                     # Extract PDF (requires pip install sidedoc[pdf])
sidedoc build document.sidedoc                   # Build document; auto-detects .docx or .pdf from manifest
sidedoc sync document.sidedoc                    # Sync edited content.md (directory only, DOCX source only)
sidedoc sync document.sidedoc -o out.docx        # Sync and build updated docx
sidedoc sync document.sidedoc --author "AI"      # Sync with custom author for track changes
sidedoc validate document.sidedoc                # Validate structure, table dimensions, merged cells, styles completeness
sidedoc info document.sidedoc                    # Show metadata (accepts dir or ZIP)
sidedoc diff document.sidedoc                    # Show changes (directory only)
sidedoc pack document.sidedoc/                   # Pack directory → .sdoc ZIP
sidedoc unpack document.sdoc                     # Unpack .sdoc ZIP → .sidedoc/ directory
```

## Tech Stack

- Python 3.11+
- python-docx — Document handling
- mistune — Markdown parsing
- click — CLI framework
- pytest — Testing
- Pillow — Image validation

**Optional (`pip install sidedoc[pdf]`):**
- docling — PDF extraction (IBM; pulls in torch + transformers, ~900 MB)
- weasyprint — PDF reconstruction (markdown → HTML → PDF; requires libpango system library)
- pymupdf — PDF inspection utilities

<!-- rtk-instructions v2 -->
# RTK (Rust Token Killer) - Token-Optimized Commands

## Golden Rule

**Always prefix commands with `rtk`**. If RTK has a dedicated filter, it uses it. If not, it passes through unchanged. This means RTK is always safe to use.

**Important**: Even in command chains with `&&`, use `rtk`:
```bash
# ❌ Wrong
git add . && git commit -m "msg" && git push

# ✅ Correct
rtk git add . && rtk git commit -m "msg" && rtk git push
```

## RTK Commands by Workflow

### Build & Compile (80-90% savings)
```bash
rtk cargo build         # Cargo build output
rtk cargo check         # Cargo check output
rtk cargo clippy        # Clippy warnings grouped by file (80%)
rtk tsc                 # TypeScript errors grouped by file/code (83%)
rtk lint                # ESLint/Biome violations grouped (84%)
rtk prettier --check    # Files needing format only (70%)
rtk next build          # Next.js build with route metrics (87%)
```

### Test (90-99% savings)
```bash
rtk cargo test          # Cargo test failures only (90%)
rtk vitest run          # Vitest failures only (99.5%)
rtk playwright test     # Playwright failures only (94%)
rtk test <cmd>          # Generic test wrapper - failures only
```

### Git (59-80% savings)
```bash
rtk git status          # Compact status
rtk git log             # Compact log (works with all git flags)
rtk git diff            # Compact diff (80%)
rtk git show            # Compact show (80%)
rtk git add             # Ultra-compact confirmations (59%)
rtk git commit          # Ultra-compact confirmations (59%)
rtk git push            # Ultra-compact confirmations
rtk git pull            # Ultra-compact confirmations
rtk git branch          # Compact branch list
rtk git fetch           # Compact fetch
rtk git stash           # Compact stash
rtk git worktree        # Compact worktree
```

Note: Git passthrough works for ALL subcommands, even those not explicitly listed.

### GitHub (26-87% savings)
```bash
rtk gh pr view <num>    # Compact PR view (87%)
rtk gh pr checks        # Compact PR checks (79%)
rtk gh run list         # Compact workflow runs (82%)
rtk gh issue list       # Compact issue list (80%)
rtk gh api              # Compact API responses (26%)
```

### JavaScript/TypeScript Tooling (70-90% savings)
```bash
rtk pnpm list           # Compact dependency tree (70%)
rtk pnpm outdated       # Compact outdated packages (80%)
rtk pnpm install        # Compact install output (90%)
rtk npm run <script>    # Compact npm script output
rtk npx <cmd>           # Compact npx command output
rtk prisma              # Prisma without ASCII art (88%)
```

### Files & Search (60-75% savings)
```bash
rtk ls <path>           # Tree format, compact (65%)
rtk read <file>         # Code reading with filtering (60%)
rtk grep <pattern>      # Search grouped by file (75%)
rtk find <pattern>      # Find grouped by directory (70%)
```

### Analysis & Debug (70-90% savings)
```bash
rtk err <cmd>           # Filter errors only from any command
rtk log <file>          # Deduplicated logs with counts
rtk json <file>         # JSON structure without values
rtk deps                # Dependency overview
rtk env                 # Environment variables compact
rtk summary <cmd>       # Smart summary of command output
rtk diff                # Ultra-compact diffs
```

### Infrastructure (85% savings)
```bash
rtk docker ps           # Compact container list
rtk docker images       # Compact image list
rtk docker logs <c>     # Deduplicated logs
rtk kubectl get         # Compact resource list
rtk kubectl logs        # Deduplicated pod logs
```

### Network (65-70% savings)
```bash
rtk curl <url>          # Compact HTTP responses (70%)
rtk wget <url>          # Compact download output (65%)
```

### Meta Commands
```bash
rtk gain                # View token savings statistics
rtk gain --history      # View command history with savings
rtk discover            # Analyze Claude Code sessions for missed RTK usage
rtk proxy <cmd>         # Run command without filtering (for debugging)
rtk init                # Add RTK instructions to CLAUDE.md
rtk init --global       # Add RTK to ~/.claude/CLAUDE.md
```

## Token Savings Overview

| Category | Commands | Typical Savings |
|----------|----------|-----------------|
| Tests | vitest, playwright, cargo test | 90-99% |
| Build | next, tsc, lint, prettier | 70-87% |
| Git | status, log, diff, add, commit | 59-80% |
| GitHub | gh pr, gh run, gh issue | 26-87% |
| Package Managers | pnpm, npm, npx | 70-90% |
| Files | ls, read, grep, find | 60-75% |
| Infrastructure | docker, kubectl | 85% |
| Network | curl, wget | 65-70% |

Overall average: **60-90% token reduction** on common development operations.
<!-- /rtk-instructions -->