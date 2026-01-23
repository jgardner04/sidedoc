# Sidedoc

**AI-native document format that separates content from formatting.**

Sidedoc enables efficient AI interaction with documents while preserving rich formatting for human consumption. A `.sidedoc` file is a ZIP archive containing markdown content and formatting metadata that can reconstruct the original docx.

!!! info "Project Status: MVP Complete"
    **Current Version:** 0.1.0
    **Status:** All MVP features implemented with 156 passing tests (84% coverage)
    **What Works:** Extract, sync, diff, build — including inline formatting, lists, and images
    **Coming Next:** Tables, hyperlinks, nested lists

## The Problem

Current document workflows force a tradeoff between AI efficiency and human usability:

- **Reading documents:** Extracting content for AI is expensive (15,000+ tokens for a 10-page document via XML) and loses formatting connections
- **Creating documents:** Tools like Pandoc generate docx from markdown, but it's one-way with no formatting preservation
- **Iterative collaboration:** Repeated extraction and regeneration is lossy and expensive - each cycle costs 10x more than necessary and degrades formatting

**Cost impact:** AI document workflows using traditional extraction methods pay 10x more in API costs than necessary and lose formatting with every iteration.

## The Solution

Documents should have two representations that stay in sync:

- **Markdown** - optimized for AI reading and writing
- **Formatted docx** - optimized for human consumption

Changes to either propagate to the other.

!!! success "Key Benefits"
    **10x Token Efficiency:** Sidedoc markdown uses ~1,500 tokens vs. 15,000+ tokens for XML-based extraction

    **Perfect Format Preservation:** Original docx formatting is preserved in metadata and automatically reapplied

    **Lossless Iteration:** Edit content infinitely without formatting degradation - each sync maintains perfect fidelity

    **Human + AI Friendly:** AI works with clean markdown; humans get familiar Word documents

## Prove It Yourself

Run the [Benchmark Suite](benchmarks.md) to measure token efficiency, format fidelity, and cost savings on your own documents. Compare Sidedoc against Pandoc, raw DOCX extraction, and Azure Document Intelligence.

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
