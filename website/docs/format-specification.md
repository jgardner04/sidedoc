# Format Specification

A `.sidedoc` file is a ZIP archive containing structured data that enables round-trip document conversion between AI-friendly markdown and human-friendly formatted Word documents.

## Container Structure

```
document.sidedoc (ZIP)
├── content.md              # Clean markdown (AI reads/writes this)
├── structure.json          # Block structure and mappings
├── styles.json             # Formatting information per block
├── manifest.json           # Metadata and version info
└── assets/                 # Images and embedded files
    ├── image1.png
    └── image2.jpg
```

## content.md

Pure markdown that AI agents can read and write efficiently. No metadata, no special markers.

```markdown
# Quarterly Report

We achieved **strong results** in Q3, exceeding targets by 15%.

## Key Highlights

- Revenue grew 23% year-over-year
- Customer retention improved to 94%
- Launched 3 new product features

## Next Steps

1. Expand into European markets
2. Hire 15 additional engineers
3. Complete platform migration

![Sales Chart](assets/image1.png)
```

## structure.json

Maps content to document structure. Enables reconstruction and sync.

```json
{
  "version": "1.0",
  "blocks": [
    {
      "id": "blk_001",
      "type": "heading",
      "level": 1,
      "content_hash": "a1b2c3d4",
      "docx_paragraph_index": 0,
      "content_start": 0,
      "content_end": 18
    },
    {
      "id": "blk_002",
      "type": "paragraph",
      "content_hash": "e5f6g7h8",
      "docx_paragraph_index": 1,
      "content_start": 20,
      "content_end": 85,
      "inline_formatting": [
        {
          "type": "bold",
          "start": 12,
          "end": 26
        },
        {
          "type": "hyperlink",
          "start": 30,
          "end": 45,
          "url": "https://example.com"
        }
      ]
    }
  ]
}
```

## styles.json

Stores formatting that should be preserved but isn't represented in markdown.

```json
{
  "version": "1.0",
  "block_styles": {
    "blk_001": {
      "docx_style": "Heading 1",
      "font_name": null,
      "font_size": null,
      "alignment": "left"
    },
    "blk_002": {
      "docx_style": "Normal",
      "font_name": "Calibri",
      "font_size": 11,
      "alignment": "left",
      "runs": [
        {
          "start": 0,
          "end": 12,
          "bold": false,
          "italic": false,
          "underline": false
        },
        {
          "start": 12,
          "end": 26,
          "bold": true,
          "italic": false,
          "underline": false
        },
        {
          "start": 30,
          "end": 45,
          "bold": false,
          "italic": false,
          "underline": true,
          "color": "0563C1",
          "is_hyperlink": true
        }
      ]
    }
  },
  "document_defaults": {
    "font_name": "Calibri",
    "font_size": 11
  }
}
```

## manifest.json

Metadata about the sidedoc container.

```json
{
  "sidedoc_version": "1.0.0",
  "created_at": "2025-01-08T10:30:00Z",
  "modified_at": "2025-01-08T10:30:00Z",
  "source_file": "quarterly_report.docx",
  "source_hash": "sha256:abc123...",
  "content_hash": "sha256:def456...",
  "generator": "sidedoc-cli/0.1.0"
}
```

## Supported Elements

### Fully Supported

| Element | Markdown | Docx | Notes |
|---------|----------|------|-------|
| Headings H1-H6 | `#` to `######` | Heading 1-6 styles | Map directly |
| Paragraphs | Plain text | Normal style | Preserve paragraph breaks |
| Bold | `**text**` | Bold run | Inline formatting |
| Italic | `*text*` | Italic run | Inline formatting |
| Underline | N/A | Underline run | Preserved in styles.json only |
| Bulleted lists | `- item` | List Bullet style | Single level |
| Numbered lists | `1. item` | List Number style | Single level |
| Images | `![alt](path)` | Inline picture | Copied to assets/ |
| Hyperlinks | `[text](url)` | Hyperlink element | Clickable links preserved |

### Preserved but Not Editable

These elements are preserved but editing them in content.md won't work correctly:

- Nested lists (2+ levels)
- Underlined text (no markdown equivalent)
- Custom named styles
- Font colors
- Highlighting

### Not Supported

- Tables
- Headers/footers
- Footnotes/endnotes
- Track changes
- Comments
- Text boxes
- Shapes
- Charts
