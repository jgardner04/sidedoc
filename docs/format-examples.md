# Sidedoc Format Examples

This document provides comprehensive, annotated examples of the sidedoc format to help contributors understand the structure and implement the specification correctly.

## Table of Contents

1. [Example 1: Minimal Document](#example-1-minimal-document)
2. [Example 2: Document with Inline Formatting](#example-2-document-with-inline-formatting)
3. [Example 3: Document with Lists](#example-3-document-with-lists)
4. [Example 4: Document with Images](#example-4-document-with-images)
5. [Example 5: Complex Document](#example-5-complex-document)
6. [Sync Transformation Examples](#sync-transformation-examples)

---

## Example 1: Minimal Document

### Source Document Description

**File:** `minimal_doc.docx`

**Content:**
- Heading 1: "Welcome" (Calibri 16pt, Bold, default black color)
- Paragraph: "This is a simple document." (Calibri 11pt, regular weight)

### Extracted Archive Contents

#### content.md

```markdown
# Welcome

This is a simple document.
```

**Explanation:**
- Single heading becomes `# Welcome` (one hash for H1)
- Single paragraph rendered as plain text
- Clean markdown with no metadata or markers

#### structure.json

```json
{
  "version": "1.0",
  "blocks": [
    {
      "id": "block-0",
      "type": "heading",
      "level": 1,
      "content_hash": "4f7b3a1d2e8c9f5a6b0d3e7c8a1f2b4d",
      "docx_paragraph_index": 0,
      "content_start": 0,
      "content_end": 9
    },
    {
      "id": "block-1",
      "type": "paragraph",
      "content_hash": "8c2f5d9a1b3e6c7d0f4a8b2e5c9d1a6f",
      "docx_paragraph_index": 1,
      "content_start": 11,
      "content_end": 37
    }
  ]
}
```

**Explanation:**
- `blocks` array contains two blocks (heading and paragraph)
- `id`: Unique identifier, sequential starting from block-0
- `type`: Either "heading" or "paragraph" (or "list"/"image" in other examples)
- `level`: For headings only, indicates H1-H6 (1-6)
- `content_hash`: SHA256 hash of the block content (used for sync matching)
- `docx_paragraph_index`: Maps to paragraph index in original .docx (0-indexed)
- `content_start`/`content_end`: Character positions in content.md (0-indexed, inclusive/exclusive)

**Position Mapping:**
```
# Welcome\n\nThis is a simple document.
^         ^  ^                         ^
0         9  11                        37

Block 0: "# Welcome" spans positions 0-9
Block 1: "This is a simple document." spans positions 11-37
(Position 10 is the blank line separator)
```

#### styles.json

```json
{
  "version": "1.0",
  "block_styles": {
    "block-0": {
      "docx_style": "Heading 1",
      "font_name": "Calibri",
      "font_size": 16,
      "alignment": "left"
    },
    "block-1": {
      "docx_style": "Normal",
      "font_name": "Calibri",
      "font_size": 11,
      "alignment": "left"
    }
  },
  "document_defaults": {
    "font_name": "Calibri",
    "font_size": 11
  }
}
```

**Explanation:**
- Each block_id from structure.json has corresponding style entry
- `docx_style`: The Word style name applied (e.g., "Heading 1", "Normal")
- `font_name`: Font family name
- `font_size`: Font size in points
- `alignment`: Text alignment ("left", "center", "right", "justify")
- `document_defaults`: Fallback values for blocks without explicit settings

#### manifest.json

```json
{
  "sidedoc_version": "1.0.0",
  "created_at": "2025-01-14T10:00:00Z",
  "modified_at": "2025-01-14T10:00:00Z",
  "source_file": "minimal_doc.docx",
  "source_hash": "sha256:a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6...",
  "content_hash": "sha256:f6e5d4c3b2a1f0e9d8c7b6a5f4e3d2c1...",
  "generator": "sidedoc-cli/0.1.0"
}
```

**Explanation:**
- `sidedoc_version`: Format version (for compatibility checks)
- `created_at`/`modified_at`: ISO 8601 timestamps
- `source_file`: Original .docx filename
- `source_hash`: SHA256 of original .docx (for change detection)
- `content_hash`: SHA256 of content.md (for sync validation)
- `generator`: Tool and version that created the sidedoc

---

## Example 2: Document with Inline Formatting

### Source Document Description

**File:** `formatted_doc.docx`

**Content:**
- Paragraph: "We achieved **strong results** in _Q3_ with **_outstanding_** performance."
  - "strong results" is bold
  - "Q3" is italic
  - "outstanding" is both bold and italic
  - Base font: Calibri 11pt

### Extracted Archive Contents

#### content.md

```markdown
We achieved **strong results** in *Q3* with **_outstanding_** performance.
```

**Explanation:**
- Bold text uses `**double asterisks**`
- Italic text uses `*single asterisks*`
- Bold+italic uses `**_combination_**` (order can vary)

#### structure.json

```json
{
  "version": "1.0",
  "blocks": [
    {
      "id": "block-0",
      "type": "paragraph",
      "content_hash": "9d8e7f6a5b4c3d2e1f0a9b8c7d6e5f4a",
      "docx_paragraph_index": 0,
      "content_start": 0,
      "content_end": 74,
      "inline_formatting": [
        {
          "type": "bold",
          "start": 12,
          "end": 26
        },
        {
          "type": "italic",
          "start": 31,
          "end": 33
        },
        {
          "type": "bold",
          "start": 40,
          "end": 54
        },
        {
          "type": "italic",
          "start": 40,
          "end": 54
        }
      ]
    }
  ]
}
```

**Explanation:**
- `inline_formatting`: Array of emphasis regions
- Each entry specifies `type` (bold/italic/underline) and character range
- Overlapping ranges indicate combined formatting (e.g., bold+italic)
- Positions are relative to the plain text content (ignoring markdown markers)

**Position Analysis:**
```
We achieved **strong results** in *Q3* with **_outstanding_** performance.
            ^^^^^^^^^^^^^^^^      ^^^^       ^^^^^^^^^^^^^^^
            bold (12-26)          italic     bold+italic (40-54)
                                  (31-33)
```

#### styles.json

```json
{
  "version": "1.0",
  "block_styles": {
    "block-0": {
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
          "start": 26,
          "end": 31,
          "bold": false,
          "italic": false,
          "underline": false
        },
        {
          "start": 31,
          "end": 33,
          "bold": false,
          "italic": true,
          "underline": false
        },
        {
          "start": 33,
          "end": 40,
          "bold": false,
          "italic": false,
          "underline": false
        },
        {
          "start": 40,
          "end": 54,
          "bold": true,
          "italic": true,
          "underline": false
        },
        {
          "start": 54,
          "end": 67,
          "bold": false,
          "italic": false,
          "underline": false
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

**Explanation:**
- `runs`: Array of text runs with explicit formatting for each segment
- Each run specifies exact character range and formatting flags
- Runs are used during reconstruction to apply exact formatting from original docx
- This preserves formatting even if markdown parsing differs

---

## Example 3: Document with Lists

### Source Document Description

**File:** `list_doc.docx`

**Content:**
- Heading 1: "Project Goals"
- Bulleted list:
  - "Complete MVP development"
  - "Launch beta program"
  - "Gather user feedback"
- Heading 2: "Timeline"
- Numbered list:
  1. "Q1: Development phase"
  2. "Q2: Beta testing"
  3. "Q3: General release"

### Extracted Archive Contents

#### content.md

```markdown
# Project Goals

- Complete MVP development
- Launch beta program
- Gather user feedback

## Timeline

1. Q1: Development phase
2. Q2: Beta testing
3. Q3: General release
```

#### structure.json

```json
{
  "version": "1.0",
  "blocks": [
    {
      "id": "block-0",
      "type": "heading",
      "level": 1,
      "content_hash": "1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d",
      "docx_paragraph_index": 0,
      "content_start": 0,
      "content_end": 16
    },
    {
      "id": "block-1",
      "type": "list",
      "list_type": "bullet",
      "items": [
        {
          "id": "block-1-0",
          "content_hash": "2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e",
          "docx_paragraph_index": 1,
          "content_start": 18,
          "content_end": 43
        },
        {
          "id": "block-1-1",
          "content_hash": "3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f",
          "docx_paragraph_index": 2,
          "content_start": 44,
          "content_end": 64
        },
        {
          "id": "block-1-2",
          "content_hash": "4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a",
          "docx_paragraph_index": 3,
          "content_start": 65,
          "content_end": 86
        }
      ]
    },
    {
      "id": "block-2",
      "type": "heading",
      "level": 2,
      "content_hash": "5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b",
      "docx_paragraph_index": 4,
      "content_start": 88,
      "content_end": 99
    },
    {
      "id": "block-3",
      "type": "list",
      "list_type": "numbered",
      "items": [
        {
          "id": "block-3-0",
          "content_hash": "6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c",
          "docx_paragraph_index": 5,
          "content_start": 101,
          "content_end": 125
        },
        {
          "id": "block-3-1",
          "content_hash": "7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d",
          "docx_paragraph_index": 6,
          "content_start": 126,
          "content_end": 143
        },
        {
          "id": "block-3-2",
          "content_hash": "8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e",
          "docx_paragraph_index": 7,
          "content_start": 144,
          "content_end": 165
        }
      ]
    }
  ]
}
```

**Explanation:**
- List blocks have `type: "list"` with `list_type: "bullet"` or `"numbered"`
- `items` array contains individual list items
- Each item has a hierarchical ID: `block-1-0`, `block-1-1`, etc.
- Each item maps to a separate docx paragraph
- List items have their own content hashes for granular sync tracking

#### styles.json

```json
{
  "version": "1.0",
  "block_styles": {
    "block-0": {
      "docx_style": "Heading 1",
      "font_name": "Calibri",
      "font_size": 16,
      "alignment": "left"
    },
    "block-1-0": {
      "docx_style": "List Bullet",
      "font_name": "Calibri",
      "font_size": 11,
      "alignment": "left",
      "indent_left": 0.5,
      "indent_hanging": 0.25
    },
    "block-1-1": {
      "docx_style": "List Bullet",
      "font_name": "Calibri",
      "font_size": 11,
      "alignment": "left",
      "indent_left": 0.5,
      "indent_hanging": 0.25
    },
    "block-1-2": {
      "docx_style": "List Bullet",
      "font_name": "Calibri",
      "font_size": 11,
      "alignment": "left",
      "indent_left": 0.5,
      "indent_hanging": 0.25
    },
    "block-2": {
      "docx_style": "Heading 2",
      "font_name": "Calibri",
      "font_size": 13,
      "alignment": "left"
    },
    "block-3-0": {
      "docx_style": "List Number",
      "font_name": "Calibri",
      "font_size": 11,
      "alignment": "left",
      "indent_left": 0.5,
      "indent_hanging": 0.25
    },
    "block-3-1": {
      "docx_style": "List Number",
      "font_name": "Calibri",
      "font_size": 11,
      "alignment": "left",
      "indent_left": 0.5,
      "indent_hanging": 0.25
    },
    "block-3-2": {
      "docx_style": "List Number",
      "font_name": "Calibri",
      "font_size": 11,
      "alignment": "left",
      "indent_left": 0.5,
      "indent_hanging": 0.25
    }
  },
  "document_defaults": {
    "font_name": "Calibri",
    "font_size": 11
  }
}
```

**Explanation:**
- Each list item gets its own style entry
- `indent_left`: Left indent in inches
- `indent_hanging`: Hanging indent for bullet/number (in inches)
- List items can have individual formatting (different fonts, sizes per item)

---

## Example 4: Document with Images

### Source Document Description

**File:** `image_doc.docx`

**Content:**
- Heading 1: "Sales Report"
- Paragraph: "Our sales exceeded expectations this quarter."
- Image: sales_chart.png (embedded in document)
- Paragraph: "Key metrics are shown above."

### Extracted Archive Contents

#### content.md

```markdown
# Sales Report

Our sales exceeded expectations this quarter.

![Sales Chart](assets/sales_chart.png)

Key metrics are shown above.
```

#### structure.json

```json
{
  "version": "1.0",
  "blocks": [
    {
      "id": "block-0",
      "type": "heading",
      "level": 1,
      "content_hash": "9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d",
      "docx_paragraph_index": 0,
      "content_start": 0,
      "content_end": 14
    },
    {
      "id": "block-1",
      "type": "paragraph",
      "content_hash": "0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e",
      "docx_paragraph_index": 1,
      "content_start": 16,
      "content_end": 59
    },
    {
      "id": "block-2",
      "type": "image",
      "alt_text": "Sales Chart",
      "asset_path": "assets/sales_chart.png",
      "docx_paragraph_index": 2,
      "content_start": 61,
      "content_end": 96
    },
    {
      "id": "block-3",
      "type": "paragraph",
      "content_hash": "1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f",
      "docx_paragraph_index": 3,
      "content_start": 98,
      "content_end": 127
    }
  ]
}
```

**Explanation:**
- Image blocks have `type: "image"`
- `alt_text`: Alternative text from markdown
- `asset_path`: Relative path to image in sidedoc archive
- Image blocks don't have `content_hash` (not text content)
- Images are extracted from docx and saved to `assets/` directory

#### Archive Structure

```
image_doc.sidedoc (ZIP)
├── content.md
├── structure.json
├── styles.json
├── manifest.json
└── assets/
    └── sales_chart.png
```

#### styles.json

```json
{
  "version": "1.0",
  "block_styles": {
    "block-0": {
      "docx_style": "Heading 1",
      "font_name": "Calibri",
      "font_size": 16,
      "alignment": "left"
    },
    "block-1": {
      "docx_style": "Normal",
      "font_name": "Calibri",
      "font_size": 11,
      "alignment": "left"
    },
    "block-2": {
      "image_width": 400,
      "image_height": 300,
      "alignment": "center"
    },
    "block-3": {
      "docx_style": "Normal",
      "font_name": "Calibri",
      "font_size": 11,
      "alignment": "left"
    }
  },
  "document_defaults": {
    "font_name": "Calibri",
    "font_size": 11
  }
}
```

**Explanation:**
- Image blocks store dimensions (width/height in pixels)
- Image alignment can be left/center/right
- No font properties for image blocks

---

## Example 5: Complex Document

### Source Document Description

**File:** `complex_doc.docx`

**Content:**
- Heading 1: "Annual Report 2024" (Calibri 18pt, Bold, Blue #0000FF)
- Paragraph: "Overview of our achievements in **2024**." (Calibri 11pt)
- Heading 2: "Key Accomplishments" (Calibri 14pt, Bold)
- Bulleted list:
  - "Revenue growth of 25%"
  - "_Customer satisfaction_ improved"
  - "**Expanded** to new markets"
- Image: growth_chart.png
- Heading 2: "Future Plans" (Calibri 14pt, Bold)
- Numbered list:
  1. "Launch new product line"
  2. "Open 3 new offices"
  3. "Hire 50 more employees"

### Extracted Archive Contents

#### content.md

```markdown
# Annual Report 2024

Overview of our achievements in **2024**.

## Key Accomplishments

- Revenue growth of 25%
- *Customer satisfaction* improved
- **Expanded** to new markets

![Growth Chart](assets/growth_chart.png)

## Future Plans

1. Launch new product line
2. Open 3 new offices
3. Hire 50 more employees
```

#### structure.json

```json
{
  "version": "1.0",
  "blocks": [
    {
      "id": "block-0",
      "type": "heading",
      "level": 1,
      "content_hash": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6",
      "docx_paragraph_index": 0,
      "content_start": 0,
      "content_end": 21
    },
    {
      "id": "block-1",
      "type": "paragraph",
      "content_hash": "b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7",
      "docx_paragraph_index": 1,
      "content_start": 23,
      "content_end": 63,
      "inline_formatting": [
        {
          "type": "bold",
          "start": 30,
          "end": 34
        }
      ]
    },
    {
      "id": "block-2",
      "type": "heading",
      "level": 2,
      "content_hash": "c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8",
      "docx_paragraph_index": 2,
      "content_start": 65,
      "content_end": 88
    },
    {
      "id": "block-3",
      "type": "list",
      "list_type": "bullet",
      "items": [
        {
          "id": "block-3-0",
          "content_hash": "d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9",
          "docx_paragraph_index": 3,
          "content_start": 90,
          "content_end": 113
        },
        {
          "id": "block-3-1",
          "content_hash": "e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0",
          "docx_paragraph_index": 4,
          "content_start": 114,
          "content_end": 148,
          "inline_formatting": [
            {
              "type": "italic",
              "start": 0,
              "end": 23
            }
          ]
        },
        {
          "id": "block-3-2",
          "content_hash": "f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1",
          "docx_paragraph_index": 5,
          "content_start": 149,
          "content_end": 177,
          "inline_formatting": [
            {
              "type": "bold",
              "start": 0,
              "end": 8
            }
          ]
        }
      ]
    },
    {
      "id": "block-4",
      "type": "image",
      "alt_text": "Growth Chart",
      "asset_path": "assets/growth_chart.png",
      "docx_paragraph_index": 6,
      "content_start": 179,
      "content_end": 218
    },
    {
      "id": "block-5",
      "type": "heading",
      "level": 2,
      "content_hash": "a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5",
      "docx_paragraph_index": 7,
      "content_start": 220,
      "content_end": 235
    },
    {
      "id": "block-6",
      "type": "list",
      "list_type": "numbered",
      "items": [
        {
          "id": "block-6-0",
          "content_hash": "b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6",
          "docx_paragraph_index": 8,
          "content_start": 237,
          "content_end": 262
        },
        {
          "id": "block-6-1",
          "content_hash": "c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7",
          "docx_paragraph_index": 9,
          "content_start": 263,
          "content_end": 283
        },
        {
          "id": "block-6-2",
          "content_hash": "d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8",
          "docx_paragraph_index": 10,
          "content_start": 284,
          "content_end": 309
        }
      ]
    }
  ]
}
```

**Key Observations:**
- Mixed content types: headings, paragraphs, lists (bulleted and numbered), images
- Inline formatting within both paragraphs and list items
- Sequential block IDs across all types
- Each element type preserves its specific metadata

---

## Sync Transformation Examples

### Scenario 1: Simple Text Edit

**Original content.md:**
```markdown
# Product Overview

We offer innovative solutions.
```

**User edits to:**
```markdown
# Product Overview

We offer innovative cloud-based solutions.
```

**Sync Actions:**
1. Block 0 (heading): Hash matches → No change
2. Block 1 (paragraph): Hash mismatch at same position → Text edited in place
   - Action: Update paragraph content
   - Formatting: Preserve original font, size, alignment

**Result:** Updated docx with modified paragraph text, all formatting intact.

---

### Scenario 2: Adding Inline Formatting

**Original content.md:**
```markdown
# Quarterly Results

Revenue increased significantly this quarter.
```

**User edits to:**
```markdown
# Quarterly Results

Revenue increased **significantly** this quarter.
```

**Sync Actions:**
1. Block 0: Hash matches → No change
2. Block 1: Hash mismatch → Inline formatting added
   - Detect new `**significantly**` emphasis
   - Parse as bold run from position 17-30
   - Update structure.json inline_formatting array
   - Update styles.json runs to add bold run

**Result:** Word document with "significantly" in bold, rest of formatting preserved.

---

### Scenario 3: Reordering Content

**Original content.md:**
```markdown
# Features

## Performance

Fast and efficient.

## Security

Secure by design.
```

**User edits to:**
```markdown
# Features

## Security

Secure by design.

## Performance

Fast and efficient.
```

**Sync Actions:**
1. Block 0 (heading "Features"): Hash matches → No change
2. Block 1 (heading "Performance"): Hash matches but different position → Reordered
3. Block 2 (paragraph under Performance): Moved with heading
4. Block 3 (heading "Security"): Hash matches but different position → Reordered
5. Block 4 (paragraph under Security): Moved with heading

**Result:** Docx paragraphs reordered to match new sequence, all formatting preserved.

---

### Scenario 4: Adding New Content

**Original content.md:**
```markdown
# Introduction

Welcome to our platform.

## Features

Core capabilities.
```

**User edits to:**
```markdown
# Introduction

Welcome to our platform.

## Benefits

Key advantages for users.

## Features

Core capabilities.
```

**Sync Actions:**
1. Block 0: Hash matches → No change
2. Block 1: Hash matches → No change
3. New block detected: "## Benefits" heading
   - No hash match, new content
   - Action: Insert new heading paragraph at position 2
   - Formatting: Apply Heading 2 style from document template
4. New block detected: "Key advantages for users."
   - Action: Insert new paragraph at position 3
   - Formatting: Apply Normal style with document defaults
5. Block 2 (original): Now at position 4 → Update indices

**Result:** Docx with new section inserted, using template styles for new content.

---

### Scenario 5: Deleting Content

**Original content.md:**
```markdown
# Overview

## Section A

Content for A.

## Section B

Content for B.

## Section C

Content for C.
```

**User edits to:**
```markdown
# Overview

## Section A

Content for A.

## Section C

Content for C.
```

**Sync Actions:**
1. Block 0: Hash matches → No change
2. Block 1-2 (Section A): Hash matches → No change
3. Block 3-4 (Section B): No matches in new content → Deleted
   - Action: Remove these paragraphs from docx
4. Block 5-6 (Section C): Hash matches → No change (indices updated)

**Result:** Docx with Section B removed, other sections intact with original formatting.

---

### Scenario 6: Complex Multi-Change Edit

**Original content.md:**
```markdown
# Report

## Summary

Good results achieved.

## Details

- Point one
- Point two
```

**User edits to:**
```markdown
# Annual Report

## Executive Summary

**Excellent** results achieved in *2024*.

## Details

- Point one
- Point two
- Point three

![Chart](assets/chart.png)
```

**Sync Actions:**
1. Block 0 (heading): Text changed "Report" → "Annual Report"
   - Hash mismatch, same position, same level
   - Action: Update text, preserve Heading 1 style
2. Block 1 (heading): Text changed "Summary" → "Executive Summary"
   - Hash mismatch, same position, same level
   - Action: Update text, preserve Heading 2 style
3. Block 2 (paragraph): Text changed + inline formatting added
   - Detect `**Excellent**` and `*2024*`
   - Action: Update text, add bold and italic runs
   - Preserve base paragraph formatting
4. Block 3 (heading "Details"): Hash matches → No change
5. Block 4 (list): Items expanded
   - Items 0-1: Hash matches → No change
   - Item 2: New item "Point three"
     - Action: Insert new list paragraph
     - Formatting: Apply List Bullet style
6. New block: Image added
   - Action: Insert image paragraph
   - Asset: Ensure chart.png exists in assets/
   - Formatting: Apply default image alignment (center)

**Result:** Comprehensive update with text changes, formatting additions, content expansion, and new image - all integrated seamlessly.

---

## Validation Checklist

When implementing or verifying sidedoc format, check:

- [ ] All block IDs are unique and sequential
- [ ] Content positions don't overlap and cover full content.md
- [ ] Content hashes match actual content (recompute to verify)
- [ ] Docx paragraph indices are sequential and valid
- [ ] Every block in structure.json has corresponding style in styles.json
- [ ] List items use hierarchical IDs (block-N-M format)
- [ ] Image asset_path references exist in archive
- [ ] Inline formatting positions are within block content range
- [ ] Style runs cover entire paragraph with no gaps or overlaps
- [ ] Manifest hashes are valid SHA256
- [ ] All JSON validates against schema
- [ ] Markdown in content.md is valid and parseable

---

## Common Pitfalls

### Pitfall 1: Off-by-One Errors in Positions

**Problem:** Content positions are 0-indexed and exclusive for end position.

**Wrong:**
```json
{
  "content_start": 0,
  "content_end": 10
}
// For content "0123456789" (10 characters)
// This would actually be positions 0-9, which is correct
// But if you think "10 characters" → end=10, you might accidentally use end=11
```

**Correct:** End position is the index AFTER the last character (exclusive).

### Pitfall 2: Not Accounting for Markdown Markers in Inline Formatting

**Problem:** Inline formatting positions in structure.json refer to plain text positions, not markdown positions.

**Wrong:**
```markdown
Content: "We achieved **strong** results"
Inline formatting position for "strong": start=12, end=20
```

**Correct:**
```markdown
Content: "We achieved **strong** results"
Plain text: "We achieved strong results"
Inline formatting position for "strong": start=12, end=18
```

### Pitfall 3: Forgetting to Update Content Hashes

**Problem:** After sync, content hashes must be recomputed for changed blocks.

**Wrong:** Keep old hash even though content changed.

**Correct:** Recompute SHA256 hash of new content and update structure.json.

---

## Additional Resources

- [PRD: Full specification](slidedoc-prd.md)
- [Sync Algorithm Details](slidedoc-prd.md#sync-algorithm)
- [Error Handling](slidedoc-prd.md#error-handling-specification)
- [python-docx Documentation](https://python-docx.readthedocs.io/)
- [CommonMark Spec](https://commonmark.org/)
