# Sidedoc: Product Requirements Document

## Overview

Sidedoc is an AI-native document format that separates content from formatting, enabling efficient AI interaction with documents while preserving rich formatting for human consumption.

**Project Repository:** `sidedoc` (Python package)
**Target Completion:** 4 weeks (MVP/POC)
**Author:** Jonathan Gardner

---

## Problem Statement

Current document workflows force a tradeoff between AI efficiency and human usability:

1. **Reading documents:** Tools like Document Intelligence extract content for AI reasoning, but this is expensive (high token cost for XML parsing) and loses the connection to the original formatting.

2. **Creating documents:** Tools like Pandoc generate docx from markdown, but this is one-way—there's no maintained link between the AI-friendly representation and the formatted output.

3. **Iterative collaboration:** When AI and humans work on the same document over time, the current model requires repeated extraction and regeneration, which is lossy and expensive.

**The core insight:** Documents should have two representations that stay in sync—one optimized for AI (markdown), one optimized for humans (formatted docx). Changes to either should propagate to the other.

---

## Goals

### Primary Goals (MVP)

1. **Extract:** Convert a .docx file into a Sidedoc container that separates content (markdown) from formatting metadata.

2. **Reconstruct:** Rebuild the original .docx from the Sidedoc container with formatting intact.

3. **Sync:** After editing the markdown content layer, update the .docx while preserving original formatting.

4. **Round-trip fidelity:** A document that goes through extract → reconstruct should be visually identical to the original.

### Non-Goals (Out of Scope for MVP)

- Tables
- Track changes
- Comments
- Headers/footers
- Footnotes/endnotes
- Nested lists beyond 2 levels
- Custom styles (preserve opaquely, don't interpret)
- Real-time sync or file watching
- GUI or editor integration
- Cloud storage integration

---

## Target Users

1. **AI developers** building document processing pipelines who want efficient document representation
2. **Enterprise architects** evaluating AI-document integration patterns
3. **Developers using Claude Code / Copilot** who want to work with documents efficiently

---

## Technical Requirements

### Technology Stack

- **Language:** Python 3.11+
- **Document handling:** python-docx
- **Markdown parsing:** mistune or marko
- **Configuration/metadata:** PyYAML
- **CLI framework:** click
- **Testing:** pytest

### Package Structure

```
sidedoc/
├── pyproject.toml
├── README.md
├── LICENSE (MIT)
├── src/
│   └── sidedoc/
│       ├── __init__.py
│       ├── cli.py              # CLI entry points
│       ├── extract.py          # docx → sidedoc
│       ├── reconstruct.py      # sidedoc → docx
│       ├── sync.py             # edited content → updated docx
│       ├── validate.py         # verify sidedoc integrity
│       ├── models.py           # data structures
│       └── utils.py            # shared utilities
├── tests/
│   ├── test_extract.py
│   ├── test_reconstruct.py
│   ├── test_sync.py
│   ├── test_roundtrip.py
│   └── fixtures/               # sample docx files for testing
└── docs/
    └── specification.md        # format specification
```

---

## Sidedoc Format Specification

### Container Structure

A `.sidedoc` file is a ZIP archive containing:

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

### content.md

Pure markdown that AI agents can read and write efficiently. No metadata, no special markers visible to AI.

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

### structure.json

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
        }
      ]
    },
    {
      "id": "blk_003",
      "type": "heading",
      "level": 2,
      "content_hash": "i9j0k1l2",
      "docx_paragraph_index": 2,
      "content_start": 87,
      "content_end": 102
    },
    {
      "id": "blk_004",
      "type": "list",
      "list_type": "bullet",
      "items": [
        {
          "id": "blk_004_001",
          "content_hash": "m3n4o5p6",
          "docx_paragraph_index": 3,
          "content_start": 104,
          "content_end": 135
        },
        {
          "id": "blk_004_002",
          "content_hash": "q7r8s9t0",
          "docx_paragraph_index": 4,
          "content_start": 136,
          "content_end": 170
        },
        {
          "id": "blk_004_003",
          "content_hash": "u1v2w3x4",
          "docx_paragraph_index": 5,
          "content_start": 171,
          "content_end": 203
        }
      ]
    },
    {
      "id": "blk_005",
      "type": "image",
      "alt_text": "Sales Chart",
      "asset_path": "assets/image1.png",
      "docx_paragraph_index": 10
    }
  ]
}
```

### styles.json

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
          "start": 26,
          "end": 65,
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

### manifest.json

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

---

## CLI Interface

### Commands

```bash
# Extract: Create sidedoc from docx
sidedoc extract document.docx
# Output: document.sidedoc

# Extract with custom output path
sidedoc extract document.docx -o /path/to/output.sidedoc

# Reconstruct: Generate docx from sidedoc (without modifying sidedoc)
sidedoc build document.sidedoc
# Output: document.docx

# Reconstruct with custom output path
sidedoc build document.sidedoc -o /path/to/output.docx

# Sync: After editing content.md, update the docx
sidedoc sync document.sidedoc
# Updates the embedded docx reference and can regenerate docx

# Validate: Check sidedoc integrity
sidedoc validate document.sidedoc
# Returns: OK or list of issues

# Diff: Show changes between content.md and last synced state
sidedoc diff document.sidedoc

# Info: Display sidedoc metadata
sidedoc info document.sidedoc

# Unpack: Extract sidedoc contents to a directory (for debugging)
sidedoc unpack document.sidedoc -o ./unpacked/

# Pack: Create sidedoc from unpacked directory
sidedoc pack ./unpacked/ -o document.sidedoc
```

### Exit Codes

- `0`: Success
- `1`: General error
- `2`: File not found
- `3`: Invalid sidedoc format
- `4`: Sync conflict (content changed in incompatible way)

---

## Supported Document Elements

### Fully Supported (MVP)

| Element | Markdown | Docx | Notes |
|---------|----------|------|-------|
| Headings H1-H6 | `# ` to `###### ` | Heading 1-6 styles | Map directly |
| Paragraphs | Plain text | Normal style | Preserve paragraph breaks |
| Bold | `**text**` | Bold run | Inline formatting |
| Italic | `*text*` | Italic run | Inline formatting |
| Underline | N/A in standard MD | Underline run | Preserve in styles.json only |
| Bulleted lists | `- item` | List Bullet style | Single level for MVP |
| Numbered lists | `1. item` | List Number style | Single level for MVP |
| Images | `![alt](path)` | Inline picture | Copy to assets/ |

### Preserved but Not Editable (MVP)

These elements are preserved in the sidedoc but editing them in content.md won't work correctly:

- Nested lists (2+ levels)
- Underlined text (no markdown equivalent)
- Custom named styles
- Font colors
- Highlighting

### Not Supported (MVP)

- Tables
- Headers/footers
- Footnotes/endnotes
- Track changes
- Comments
- Text boxes
- Shapes
- Charts
- Hyperlinks (future: support `[text](url)`)

---

## Sync Algorithm

### Block-Level Sync Strategy

The sync algorithm operates at the block level, not character level. This simplifies implementation while handling most real-world editing scenarios.

#### Step 1: Parse New Content

Parse the edited `content.md` into blocks (headings, paragraphs, list items, images).

#### Step 2: Match Blocks

For each block in the new content:
1. Compute content hash
2. Look for matching hash in structure.json (unchanged block)
3. If no hash match, look for similar blocks by:
   - Same type and position (likely edited in place)
   - Same type and similar content (moved block)
4. Mark unmatched old blocks as deleted
5. Mark unmatched new blocks as inserted

#### Step 3: Generate Updated Docx

1. Create new docx document
2. For each block in new content:
   - If matched to existing block: copy formatting from styles.json
   - If new block: apply default formatting for block type
3. For inline formatting (bold, italic):
   - Parse markdown emphasis markers
   - Apply as runs in the docx paragraph

#### Step 4: Update Sidedoc

1. Regenerate structure.json with new mappings
2. Update content hashes
3. Update manifest.json timestamps
4. Repackage sidedoc

### Conflict Handling

If sync encounters an unresolvable situation:
1. Abort the sync
2. Report the conflict to the user
3. Suggest manual resolution

Conflict examples:
- Markdown syntax error in content.md
- Referenced image missing from assets/

---

## Testing Requirements

### Unit Tests

- `test_extract.py`: Extraction of each supported element type
- `test_reconstruct.py`: Reconstruction produces valid docx
- `test_sync.py`: Various edit scenarios sync correctly
- `test_roundtrip.py`: Extract → reconstruct produces identical output

### Integration Tests

- Round-trip test with sample documents
- CLI command tests
- Error handling tests

### Test Fixtures

Create sample docx files covering:
1. Simple document (headings + paragraphs)
2. Document with lists (bulleted and numbered)
3. Document with inline formatting (bold, italic, mixed)
4. Document with images
5. Complex document (all supported elements)

### Success Criteria

1. **Round-trip fidelity**: A document that goes through `extract` → `build` should be visually identical to the original when opened in Word.

2. **Sync correctness**: After editing content.md (adding/removing/modifying blocks), `sync` should produce a docx that:
   - Reflects all content changes
   - Preserves formatting on unchanged blocks
   - Applies sensible defaults to new blocks

3. **Performance**: Extract and build should complete in under 2 seconds for a 10-page document.

---

## Implementation Phases

### Phase 1: Extraction (Week 1)

**Goal:** `sidedoc extract` works for all supported elements.

Tasks:
1. Set up project structure and dependencies
2. Implement docx parsing (python-docx)
3. Generate content.md from paragraphs and headings
4. Generate structure.json with block mappings
5. Generate styles.json with formatting data
6. Handle images (copy to assets/)
7. Package as ZIP with .sidedoc extension
8. Implement `sidedoc extract` CLI command
9. Write extraction tests

**Deliverable:** Can extract any docx with supported elements into a valid sidedoc.

### Phase 2: Reconstruction (Week 2)

**Goal:** `sidedoc build` produces valid docx from sidedoc.

Tasks:
1. Implement sidedoc unpacking/reading
2. Parse content.md to blocks
3. Create docx document structure
4. Apply styles from styles.json
5. Handle inline formatting (bold, italic)
6. Embed images from assets/
7. Implement `sidedoc build` CLI command
8. Write reconstruction tests
9. Implement round-trip tests

**Deliverable:** Can rebuild docx from sidedoc with formatting intact.

### Phase 3: Sync (Week 3)

**Goal:** `sidedoc sync` handles content edits correctly.

Tasks:
1. Implement block matching algorithm
2. Detect added/removed/modified blocks
3. Generate updated docx preserving formatting
4. Update structure.json and manifest.json
5. Implement `sidedoc sync` CLI command
6. Implement `sidedoc diff` CLI command
7. Write sync tests with various edit scenarios

**Deliverable:** Can edit content.md and sync changes back to docx.

### Phase 4: Polish (Week 4)

**Goal:** Production-ready POC.

Tasks:
1. Implement `sidedoc validate` command
2. Implement `sidedoc info` command
3. Implement `sidedoc unpack` and `sidedoc pack` commands
4. Error handling and edge cases
5. Documentation (README, specification.md)
6. Package for PyPI (optional)
7. Create example documents and usage guide

**Deliverable:** Complete, documented POC ready for public release.

---

## Open Questions

1. **Underline handling**: Markdown has no underline syntax. Options:
   - Ignore underline (loses formatting)
   - Use non-standard syntax like `++underline++`
   - Preserve in styles.json only (not editable via markdown)
   
   **Current decision:** Preserve in styles.json only.

2. **Hyperlinks**: Standard markdown supports `[text](url)`. Should we support this in MVP?
   
   **Current decision:** Defer to post-MVP.

3. **List nesting**: Should we support 2-level nested lists in MVP?
   
   **Current decision:** No, single level only. Nested lists preserved opaquely.

4. **Image positioning**: Docx images can be inline or floating. How to handle?
   
   **Current decision:** Treat all as inline for MVP.

---

## Success Metrics

1. **Functional completeness**: All CLI commands work as specified
2. **Round-trip fidelity**: 100% visual match for supported elements
3. **Test coverage**: >80% code coverage
4. **Documentation**: README with usage examples, format specification

---

## References

- [python-docx documentation](https://python-docx.readthedocs.io/)
- [CommonMark specification](https://commonmark.org/)
- [llms.txt proposal](https://llmstxt.org/) - inspiration for AI-native formats
- [OOXML specification](https://docs.microsoft.com/en-us/openspecs/office_standards/ms-docx/) - docx format reference

---

## Appendix: Sample Workflow

### Scenario: AI edits a quarterly report

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

This workflow enables AI to work with documents efficiently while humans retain their familiar Word experience.
