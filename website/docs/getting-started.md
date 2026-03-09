# Getting Started

## Why Use Sidedoc?

Sidedoc makes AI document workflows **dramatically more efficient ([benchmarks](benchmarks.md))** while preserving formatting:

- **Lower AI costs:** Read documents using orders of magnitude fewer tokens than raw XML ([see benchmarks](benchmarks.md))
- **Iterative editing:** Edit content repeatedly without formatting degradation
- **Format preservation:** Original Word styling is maintained automatically through metadata
- **Best of both worlds:** AI works with clean markdown; humans get familiar Word documents

Perfect for teams building AI document automation, content generation pipelines, or iterative AI-human document collaboration.

[Learn more about the motivation](index.md#the-problem){ .md-button }

## Installation

Currently, install from source (PyPI package coming soon):

```bash
git clone https://github.com/jgardner04/sidedoc.git
cd sidedoc
pip install -e ".[dev]"
```

Or install directly from GitHub:

```bash
pip install git+https://github.com/jgardner04/sidedoc.git
```

## Basic Usage

### Extract a Document

Convert a Word document to sidedoc format:

```bash
sidedoc extract document.docx
# Creates: document.sidedoc/ (directory)
```

### View the Content

The sidedoc directory contains clean markdown that AI can efficiently read:

```bash
cat document.sidedoc/content.md
```

### Rebuild the Document

Reconstruct the Word document with formatting intact:

```bash
sidedoc build document.sidedoc
# Creates: document.docx
```

### Edit Content

Edit the markdown directly in the sidedoc directory:

```bash
# Edit content directly in the sidedoc directory
vim document.sidedoc/content.md
```

Note: `unpack` and `pack` commands are for working with `.sdoc` ZIP archives.

### Sync After Editing

After editing content.md, sync the changes:

```bash
sidedoc sync document.sidedoc
```

### View Changes

See what's changed since extraction:

```bash
sidedoc diff document.sidedoc
```

## CLI Commands

All commands are implemented:

| Command | Description |
|---------|-------------|
| `sidedoc extract <docx>` | Create .sidedoc/ directory from docx (or .sdoc ZIP with --pack) |
| `sidedoc build <sidedoc>` | Generate docx from sidedoc (directory or .sdoc) |
| `sidedoc sync <sidedoc>` | Sync edited content back to docx (directory only) |
| `sidedoc diff <sidedoc>` | Show changes since last sync (directory only) |
| `sidedoc validate <sidedoc>` | Check sidedoc integrity |
| `sidedoc info <sidedoc>` | Display sidedoc metadata |
| `sidedoc unpack <sdoc>` | Extract .sdoc ZIP to directory |
| `sidedoc pack <dir>` | Create .sdoc ZIP from directory |

## Example Workflow

```bash
# 1. Extract for AI processing
sidedoc extract quarterly_report.docx
# ✓ Created quarterly_report.sidedoc/

# 2. AI/human edits the markdown content directly
# Edit: quarterly_report.sidedoc/content.md

# 3. View changes (optional)
sidedoc diff quarterly_report.sidedoc/

# 4. Sync the changes
sidedoc sync quarterly_report.sidedoc/
# ✓ Synced: 3 blocks modified, 1 block added

# 5. Rebuild for human consumption
sidedoc build quarterly_report.sidedoc/ -o quarterly_report_updated.docx
# ✓ Built document: quarterly_report_updated.docx

# 6. (Optional) Package for sharing
sidedoc pack quarterly_report.sidedoc/
# ✓ Created quarterly_report.sdoc
```
