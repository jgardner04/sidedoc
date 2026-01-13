# Sidedoc

**AI-native document format that separates content from formatting.**

Sidedoc enables efficient AI interaction with documents while preserving rich formatting for human consumption. A `.sidedoc` file is a ZIP archive containing markdown content and formatting metadata that can reconstruct the original docx.

!!! info "Project Status: MVP Released"
    **Current Version:** 0.1.0
    **Status:** Core extract/build workflow functional with 55 passing tests
    **What Works:** Extract docx → edit markdown → rebuild docx with formatting preserved
    **Coming Soon:** Inline formatting (bold/italic), lists, images, sync command

## The Problem

Current document workflows force a tradeoff between AI efficiency and human usability:

- **Reading documents:** Extracting content for AI is expensive and loses formatting connections
- **Creating documents:** Tools like Pandoc generate docx from markdown, but it's one-way
- **Iterative collaboration:** Repeated extraction and regeneration is lossy and expensive

## The Solution

Documents should have two representations that stay in sync:

- **Markdown** - optimized for AI reading and writing
- **Formatted docx** - optimized for human consumption

Changes to either propagate to the other.

## Quick Example

```bash
# Extract a Word document to sidedoc format
sidedoc extract quarterly_report.docx

# AI edits the markdown content...

# Sync changes back, preserving formatting
sidedoc sync quarterly_report.sidedoc

# Rebuild the formatted Word document
sidedoc build quarterly_report.sidedoc
```

## What's in a .sidedoc file?

| File | Purpose |
|------|---------|
| `content.md` | Clean markdown that AI reads/writes |
| `structure.json` | Block structure and mappings to docx paragraphs |
| `styles.json` | Formatting information per block |
| `manifest.json` | Metadata and version info |
| `assets/` | Images and embedded files |

## Get Started

See the [Getting Started](getting-started.md) guide for installation and usage instructions.
