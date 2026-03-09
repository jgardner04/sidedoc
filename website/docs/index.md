# Sidedoc

**AI-native document format that separates content from formatting.**

Sidedoc enables efficient AI interaction with documents while preserving rich formatting for human consumption. Sidedoc extracts a `.sidedoc/` directory containing markdown content and formatting metadata that can reconstruct the original docx. A `.sdoc` ZIP archive provides a single-file format for sharing.

!!! info "Project Status: Tables, Track Changes & Hyperlinks"
    **What Works:** Extract, sync, diff, build — including tables, track changes, inline formatting, lists, images, and hyperlinks
    **Coming Next:** Nested lists, headers/footers

## The Problem

Current document workflows force a tradeoff between AI efficiency and human usability:

- **Reading documents:** Extracting content for AI is expensive (raw OOXML runs [325,000+ tokens per document](benchmarks.md)) and loses formatting connections
- **Creating documents:** Tools like Pandoc generate docx from markdown, but it's one-way with no formatting preservation
- **Iterative collaboration:** Repeated extraction and regeneration is lossy and expensive - each cycle costs orders of magnitude more than necessary and degrades formatting

**Cost impact:** AI document workflows using traditional extraction methods pay dramatically more in API costs than necessary and lose formatting with every iteration.

## The Solution

Documents should have two representations that stay in sync:

- **Markdown** - optimized for AI reading and writing
- **Formatted docx** - optimized for human consumption

Changes to either propagate to the other.

!!! success "Key Benefits"
    **Massive Token Savings:** [Measured 1,524x fewer prompt tokens](benchmarks.md) than raw OOXML across 45 LLM task runs

    **Format Preservation:** Original docx formatting is preserved in metadata and automatically reapplied

    **Iterative Editing:** Edit content repeatedly without formatting degradation — each sync maintains fidelity for supported elements

    **Human + AI Friendly:** AI works with clean markdown; humans get familiar Word documents

## Prove It Yourself

Run the [Benchmark Suite](benchmarks.md) to measure token efficiency, format fidelity, and cost savings on your own documents. Compare Sidedoc against Pandoc, raw DOCX extraction, and Azure Document Intelligence.

## Quick Example

```bash
# Extract a Word document to sidedoc format
sidedoc extract quarterly_report.docx

# AI edits the markdown content...

# Sync changes back, preserving formatting
sidedoc sync quarterly_report.sidedoc/

# Rebuild the formatted Word document
sidedoc build quarterly_report.sidedoc/
```

<!-- Keep element lists in sync: index.md, faq.md, format-specification.md -->
!!! example "What's Supported"
    **Fully supported:** Headings, paragraphs, bold/italic, lists, images, hyperlinks, tables (including merged cells and cell styling), and track changes (insertions/deletions with author attribution).

    **Not yet supported:** Nested lists (2+ levels), headers/footers, footnotes, comments, text boxes, shapes, charts.

## What's in a .sidedoc directory?

| File | Purpose |
|------|---------|
| `content.md` | Clean markdown that AI reads/writes |
| `structure.json` | Block structure and mappings to docx paragraphs |
| `styles.json` | Formatting information per block |
| `manifest.json` | Metadata and version info |
| `assets/` | Images and embedded files |

## Get Started

See the [Getting Started](getting-started.md) guide for installation and usage instructions.
