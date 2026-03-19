# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Sidedoc is an AI-native document format that separates content from formatting. It enables efficient AI interaction with documents while preserving rich formatting for human consumption. The canonical format is a `.sidedoc/` directory containing markdown content and formatting metadata. A `.sdoc` ZIP archive is used for distribution and sharing.

**Status:** MVP complete with hyperlink, track changes, table, and headers/footers support (extraction, reconstruction).

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
├── extract.py          # docx → sidedoc (paragraphs, tables, images, headers/footers)
├── models.py           # Block, Style, Manifest, TrackChange dataclasses
├── package.py          # Archive/directory creation helpers, block serialization
├── reconstruct.py      # sidedoc → docx; owns inline formatting, table creation, block styling, header/footer reconstruction
├── store.py            # Read-only abstraction over directory/ZIP
├── sync.py             # edited content → updated docx (imports formatting from reconstruct.py)
└── utils.py            # shared utilities
```

## Key Concepts

- **Extract:** Convert a .docx file into a Sidedoc container (content.md + formatting metadata)
- **Reconstruct (build):** Rebuild the original .docx from the Sidedoc container with formatting intact
- **Sync:** After editing content.md, update the .docx while preserving original formatting

### Block Types

| Type | Markdown Format | Notes |
|------|-----------------|-------|
| `heading` | `# Title` | Levels 1-6 supported |
| `paragraph` | Plain text | Inline formatting: `**bold**`, `*italic*` |
| `list` | `- bullet` or `1. numbered` | |
| `image` | `![alt](assets/image.png)` | |
| `table` | GFM pipe tables | Merged cells, cell formatting, header rows preserved |
| `hyperlink` | `[text](url)` | Inline within other blocks |

### Headers and Footers

Headers and footers are stored as section metadata in `structure.json` (not as blocks in `content.md`). Each section can have up to six variants: `header_default`, `header_first`, `header_even`, `footer_default`, `footer_first`, `footer_even`.

**Limitation:** Header/footer content is extracted and reconstructed as **plain text only**. Inline formatting (bold, italic, hyperlinks) within header/footer paragraphs is silently dropped. Images in headers/footers are extracted to `assets/` and restored on build.

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
| `manifest.json` | No* | Yes | Metadata and version info |
| `assets/` | No | No | Images and embedded files |

\* `structure.json` is written during `sidedoc extract` and updated by `sidedoc sync`; `manifest.json` is generated by `sidedoc sync`

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

# Type checking
mypy src/

# CLI commands (all implemented)
sidedoc extract document.docx                    # Extract to document.sidedoc/ directory
sidedoc extract document.docx --pack             # Extract to document.sdoc ZIP
sidedoc extract document.docx --force            # Overwrite existing output
sidedoc extract document.docx --track-changes    # Force extract track changes
sidedoc extract document.docx --no-track-changes # Accept all changes
sidedoc build document.sidedoc                   # Build docx (accepts dir or ZIP)
sidedoc sync document.sidedoc                    # Sync edited content.md (directory only)
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
