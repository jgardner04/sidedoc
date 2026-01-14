# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Sidedoc is an AI-native document format that separates content from formatting. It enables efficient AI interaction with documents while preserving rich formatting for human consumption. A `.sidedoc` file is a ZIP archive containing markdown content and formatting metadata that can reconstruct the original docx.

**Status:** MVP complete - all 30 user stories implemented and passing

## Specifications

- [Product Requirements Document](docs/slidedoc-prd.md) — Full PRD with format specification, CLI interface, sync algorithm, and implementation phases

## Architecture

Package structure:

```
src/sidedoc/
├── __init__.py
├── cli.py              # CLI entry points (click)
├── extract.py          # docx → sidedoc
├── reconstruct.py      # sidedoc → docx
├── sync.py             # edited content → updated docx
├── validate.py         # verify sidedoc integrity
├── models.py           # data structures
└── utils.py            # shared utilities
```

## Key Concepts

- **Extract:** Convert a .docx file into a Sidedoc container (content.md + formatting metadata)
- **Reconstruct (build):** Rebuild the original .docx from the Sidedoc container with formatting intact
- **Sync:** After editing content.md, update the .docx while preserving original formatting

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
# Run tests
pytest

# Run tests with coverage
pytest --cov=sidedoc

# Type checking
mypy src/

# CLI commands (all implemented)
sidedoc extract document.docx           # Extract docx to sidedoc
sidedoc build document.sidedoc          # Build docx from sidedoc
sidedoc sync document.sidedoc           # Sync edited content.md
sidedoc validate document.sidedoc       # Validate sidedoc integrity
sidedoc info document.sidedoc           # Show metadata
sidedoc unpack document.sidedoc -o dir/ # Extract to directory
sidedoc pack dir/ -o document.sidedoc   # Create from directory
sidedoc diff document.sidedoc           # Show content changes
```

## Tech Stack

- Python 3.11+
- python-docx — Document handling
- mistune or marko — Markdown parsing
- click — CLI framework
- pytest — Testing
