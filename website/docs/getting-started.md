# Getting Started

## Why Use Sidedoc?

Sidedoc makes AI document workflows **10x more efficient** while preserving perfect formatting:

- **Lower AI costs:** Read documents using ~1,500 tokens (markdown) instead of 15,000+ tokens (XML)
- **Lossless iteration:** Edit content repeatedly without formatting degradation
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
# Creates: document.sidedoc
```

### View the Content

The sidedoc contains clean markdown that AI can efficiently read:

```bash
unzip -p document.sidedoc content.md
```

### Rebuild the Document

Reconstruct the Word document with formatting intact:

```bash
sidedoc build document.sidedoc
# Creates: document.docx
```

### Unpack for Editing (Current)

Extract the archive to edit the markdown:

```bash
sidedoc unpack document.sidedoc -o unpacked
# Edit unpacked/content.md
sidedoc pack unpacked -o document.sidedoc
```

### Sync After Editing (Coming Soon)

Future versions will support direct sync without unpacking:

```bash
sidedoc sync document.sidedoc
```

## CLI Commands

### ✅ Implemented

| Command | Description |
|---------|-------------|
| `sidedoc extract <docx>` | Create sidedoc from docx |
| `sidedoc build <sidedoc>` | Generate docx from sidedoc |
| `sidedoc validate <sidedoc>` | Check sidedoc integrity |
| `sidedoc info <sidedoc>` | Display sidedoc metadata |
| `sidedoc unpack <sidedoc> -o <dir>` | Extract sidedoc contents to directory |
| `sidedoc pack <dir> -o <sidedoc>` | Create sidedoc from directory |

### 🚧 Coming Soon

| Command | Description |
|---------|-------------|
| `sidedoc sync <sidedoc>` | Sync edited content back to docx |
| `sidedoc diff <sidedoc>` | Show changes since last sync |

## Example Workflow

### Current MVP Workflow

```bash
# 1. Start with a formatted Word document
ls
# quarterly_report.docx

# 2. Extract for AI processing
sidedoc extract quarterly_report.docx
# ✓ Extracted to quarterly_report.sidedoc

# 3. Unpack to edit the markdown
sidedoc unpack quarterly_report.sidedoc -o unpacked
# ✓ Unpacked to unpacked

# 4. AI/human edits the markdown content
# Edit: unpacked/content.md
# ... Add sections, modify text ...

# 5. Pack back into sidedoc
sidedoc pack unpacked -o quarterly_report.sidedoc
# ✓ Packed to quarterly_report.sidedoc

# 6. Rebuild for human consumption
sidedoc build quarterly_report.sidedoc -o quarterly_report_updated.docx
# ✓ Built document: quarterly_report_updated.docx

# 7. Open in Word - formatting preserved, content updated
```

### Future Workflow (with sync)

```bash
# Extract once
sidedoc extract document.docx

# Edit content.md inside the archive
# ... make changes ...

# Sync updates the docx automatically
sidedoc sync document.sidedoc
# ✓ Synced: 3 blocks modified, 1 block added

# Build updated docx
sidedoc build document.sidedoc
```
