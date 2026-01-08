# Sidedoc

An AI-native document format that separates content from formatting, enabling efficient AI interaction with documents while preserving rich formatting for human consumption.

**Status:** MVP in development

---

## The Problem

Current document workflows force a tradeoff between AI efficiency and human usability:

1. **Reading documents:** Tools like Document Intelligence extract content for AI reasoning, but this is expensive (high token cost for XML parsing) and loses the connection to the original formatting.

2. **Creating documents:** Tools like Pandoc generate docx from markdown, but this is one-way—there's no maintained link between the AI-friendly representation and the formatted output.

3. **Iterative collaboration:** When AI and humans work on the same document over time, the current model requires repeated extraction and regeneration, which is lossy and expensive.

## The Solution

Documents should have two representations that stay in sync:

- **Markdown** — optimized for AI (efficient to read/write, low token cost)
- **Formatted docx** — optimized for humans (rich formatting, familiar tools)

Changes to either should propagate to the other. Sidedoc makes this possible.

---

## How It Works

A `.sidedoc` file is a ZIP archive containing:

```
document.sidedoc
├── content.md         # Clean markdown (AI reads/writes this)
├── structure.json     # Block structure and mappings
├── styles.json        # Formatting information per block
├── manifest.json      # Metadata and version info
└── assets/            # Images and embedded files
```

The AI works with `content.md` — pure markdown with no metadata or special markers. The other files preserve formatting information so the original docx can be reconstructed with styling intact.

---

## CLI Commands

```bash
# Extract: Create sidedoc from docx
sidedoc extract document.docx

# Build: Generate docx from sidedoc
sidedoc build document.sidedoc

# Sync: After editing content.md, update the docx
sidedoc sync document.sidedoc

# Validate: Check sidedoc integrity
sidedoc validate document.sidedoc

# Diff: Show changes between content.md and last synced state
sidedoc diff document.sidedoc

# Info: Display sidedoc metadata
sidedoc info document.sidedoc

# Unpack/Pack: Extract or create sidedoc from directory (debugging)
sidedoc unpack document.sidedoc -o ./unpacked/
sidedoc pack ./unpacked/ -o document.sidedoc
```

---

## Example Workflow

```bash
# 1. User has a formatted Word document
$ ls
quarterly_report.docx

# 2. Extract to sidedoc for AI processing
$ sidedoc extract quarterly_report.docx
Created: quarterly_report.sidedoc

# 3. AI reads the markdown content efficiently
$ unzip -p quarterly_report.sidedoc content.md
# Quarterly Report
We achieved **strong results** in Q3...

# 4. AI edits content.md (via Claude Code or similar)
# ... AI adds a new section, modifies text ...

# 5. Sync changes back to docx
$ sidedoc sync quarterly_report.sidedoc
Synced: 3 blocks modified, 1 block added

# 6. Rebuild the docx for human consumption
$ sidedoc build quarterly_report.sidedoc -o quarterly_report_updated.docx
Created: quarterly_report_updated.docx

# 7. Open in Word - formatting preserved, content updated
```

---

## Supported Elements (MVP)

| Element | Markdown | Notes |
|---------|----------|-------|
| Headings H1-H6 | `#` to `######` | Maps to Heading 1-6 styles |
| Paragraphs | Plain text | Preserves paragraph breaks |
| Bold | `**text**` | Inline formatting |
| Italic | `*text*` | Inline formatting |
| Bulleted lists | `- item` | Single level for MVP |
| Numbered lists | `1. item` | Single level for MVP |
| Images | `![alt](path)` | Copied to assets/ |

See the [PRD](docs/slidedoc-prd.md) for full details on supported and unsupported elements.

---

## Installation

```bash
pip install sidedoc
```

*Coming soon — package not yet published.*

---

## Development

```bash
# Clone the repository
git clone https://github.com/jogardn/sidedoc.git
cd sidedoc

# Install in development mode (once pyproject.toml exists)
pip install -e ".[dev]"

# Run tests
pytest
```

---

## Links

- [GitHub](https://github.com/jogardn/sidedoc)
- [Product Requirements Document](docs/slidedoc-prd.md)
- [Author: Jonathan Gardner](https://jonathangardner.io)
