# Getting Started

## Installation

```bash
pip install sidedoc
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

### Sync After Editing

After editing `content.md`, sync changes back:

```bash
sidedoc sync document.sidedoc
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `sidedoc extract <docx>` | Create sidedoc from docx |
| `sidedoc build <sidedoc>` | Generate docx from sidedoc |
| `sidedoc sync <sidedoc>` | Sync edited content back to docx |
| `sidedoc validate <sidedoc>` | Check sidedoc integrity |
| `sidedoc diff <sidedoc>` | Show changes since last sync |
| `sidedoc info <sidedoc>` | Display sidedoc metadata |

## Example Workflow

```bash
# 1. Start with a formatted Word document
ls
# quarterly_report.docx

# 2. Extract for AI processing
sidedoc extract quarterly_report.docx
# Created: quarterly_report.sidedoc

# 3. AI reads and edits the markdown content
# ... AI adds sections, modifies text ...

# 4. Sync changes back
sidedoc sync quarterly_report.sidedoc
# Synced: 3 blocks modified, 1 block added

# 5. Rebuild for human consumption
sidedoc build quarterly_report.sidedoc -o quarterly_report_updated.docx
# Created: quarterly_report_updated.docx

# 6. Open in Word - formatting preserved, content updated
```
