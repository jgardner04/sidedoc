# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Sidedoc is an AI-native document format that separates content from formatting. It enables efficient AI interaction with documents while preserving rich formatting for human consumption. A `.sidedoc` file is a ZIP archive containing markdown content and formatting metadata that can reconstruct the original docx.

**Status:** MVP complete with hyperlink, track changes, and table support (extraction, reconstruction, sync).

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

- [Product Requirements Document](docs/slidedoc-prd.md) — Full PRD with format specification, CLI interface, sync algorithm
- [Track Changes PRD](docs/prd-track-changes.md) — CriticMarkup-based track changes support
- [Tables PRD](docs/tables-prd.md) — Phase 2 table support requirements
- [PRD Status](docs/prd.json) — Current feature tracking

## Architecture

Package structure:

```
src/sidedoc/
├── __init__.py
├── cli.py              # CLI entry points (click), includes validate command
├── constants.py        # Shared constants (image limits, etc.)
├── extract.py          # docx → sidedoc (paragraphs, tables, images)
├── models.py           # Block, Style, Manifest dataclasses
├── package.py          # ZIP archive handling
├── reconstruct.py      # sidedoc → docx
├── sync.py             # edited content → updated docx
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
| `table` | GFM pipe tables | |
| `hyperlink` | `[text](url)` | Inline within other blocks |

### Table Support (Phase 2)

Tables are extracted as GFM (GitHub Flavored Markdown) pipe table syntax:

```markdown
| Name | Role | Start Date |
| --- | --- | --- |
| Alice | Engineer | 2024-01-15 |
```

- **Alignment:** `---` (default left), `:---|` (explicit left), `:---:|` (center), `---:|` (right)
- **Escaping:** Pipe characters in content escaped as `\|`
- **Metadata:** `table_metadata` in Block stores rows, cols, cells, column_alignments, docx_table_index
- **Styling:** `table_formatting` in Style stores column_widths, table_alignment

## Sidedoc Format

A `.sidedoc` file is a ZIP archive containing:

| File | Purpose |
|------|---------|
| `content.md` | Clean markdown that AI reads/writes |
| `structure.json` | Block structure and mappings to docx paragraphs |
| `styles.json` | Formatting information per block |
| `manifest.json` | Metadata and version info |
| `assets/` | Images and embedded files |

## Development Commands

```bash
# Run tests (use uv run prefix)
uv run pytest

# Run tests with coverage (>80% required)
uv run pytest --cov=sidedoc

# Type checking
uv run mypy src/

# CLI commands (all implemented)
sidedoc extract document.docx                    # Extract docx to sidedoc
sidedoc extract document.docx --track-changes    # Force extract track changes
sidedoc extract document.docx --no-track-changes # Accept all changes
sidedoc build document.sidedoc                   # Build docx from sidedoc
sidedoc sync document.sidedoc -o out.docx        # Sync edited content.md
sidedoc sync document.sidedoc --author "AI"      # Sync with custom author
sidedoc validate document.sidedoc                # Validate sidedoc integrity
sidedoc info document.sidedoc                    # Show metadata
sidedoc unpack document.sidedoc -o dir/          # Extract to directory
sidedoc pack dir/ -o document.sidedoc            # Create from directory
sidedoc diff document.sidedoc                    # Show content changes
```

## Tech Stack

- Python 3.11+
- python-docx — Document handling
- mistune — Markdown parsing
- click — CLI framework
- pytest — Testing
