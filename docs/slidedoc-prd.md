# PRD: Sidedoc - AI-Native Document Format

## Introduction

Sidedoc is an AI-native document format that separates content from formatting, enabling efficient AI interaction with documents while preserving rich formatting for human consumption. A `.sidedoc` file is a ZIP archive containing markdown content and formatting metadata that can reconstruct the original Word document.

Current document workflows force a tradeoff between AI efficiency and human usability. Tools like Document Intelligence extract content for AI reasoning but lose formatting connections. Tools like Pandoc generate docx from markdown but provide no maintained link back. When AI and humans collaborate iteratively on documents, repeated extraction and regeneration is lossy and expensive.

**The core insight:** Documents should have two representations that stay in sync—one optimized for AI (markdown), one optimized for humans (formatted docx). Changes to either should propagate to the other.

**Project Repository:** `sidedoc` (Python package)
**Author:** Jonathan Gardner
**Status:** MVP in development

## Goals

- Enable AI agents to read document content efficiently via clean markdown
- Preserve rich Word formatting (fonts, styles, colors) during AI editing
- Provide round-trip fidelity: extract → reconstruct produces visually identical documents
- Support iterative AI-human collaboration on documents without format loss
- Deliver a command-line tool for document workflows
- Support core document elements: headings, paragraphs, lists, images, inline formatting

## Non-Goals (Out of Scope for MVP)

- Tables, charts, shapes, text boxes
- Track changes and comments
- Headers/footers, footnotes/endnotes
- Nested lists beyond 2 levels
- Custom styles (preserve opaquely, don't interpret)
- Real-time sync or file watching
- GUI or editor integration
- Cloud storage integration
- Hyperlinks (deferred to post-MVP)

## Target Users

1. **AI developers** building document processing pipelines who want efficient document representation
2. **Enterprise architects** evaluating AI-document integration patterns
3. **Developers using Claude Code / Copilot** who want to work with documents efficiently

## User Stories

### US-001: Extract docx to sidedoc format
**Description:** As an AI developer, I want to extract a Word document into a sidedoc archive so that I can access its content as clean markdown while preserving formatting.

**Acceptance Criteria:**
- [ ] `sidedoc extract document.docx` creates `document.sidedoc` ZIP archive
- [ ] Archive contains: content.md, structure.json, styles.json, manifest.json, assets/
- [ ] content.md contains clean markdown with headings (H1-H6), paragraphs, lists, images
- [ ] structure.json maps content blocks to docx paragraph indices with content hashes
- [ ] styles.json stores formatting (fonts, sizes, colors, alignment) per block
- [ ] Images are copied to assets/ directory with proper references
- [ ] manifest.json includes version, timestamps, source file info
- [ ] Typecheck passes
- [ ] Round-trip test: extract → build produces visually identical docx

### US-002: Build docx from sidedoc
**Description:** As a user, I want to reconstruct a Word document from a sidedoc archive so that humans can view and edit the document with formatting intact.

**Acceptance Criteria:**
- [ ] `sidedoc build document.sidedoc` creates `document.docx`
- [ ] All headings (H1-H6) render with correct styles
- [ ] Paragraphs preserve original formatting (fonts, sizes, alignment)
- [ ] Inline formatting (bold, italic, underline) applied correctly
- [ ] Bulleted and numbered lists render properly
- [ ] Images embedded at correct positions
- [ ] Generated docx opens successfully in Microsoft Word
- [ ] Typecheck passes
- [ ] Visual comparison with original confirms formatting fidelity

### US-003: Sync edited markdown to docx
**Description:** As an AI agent, I want to edit content.md and sync changes back to docx so that content updates preserve existing formatting.

**Acceptance Criteria:**
- [ ] `sidedoc sync document.sidedoc` detects changes in content.md
- [ ] Modified blocks update docx while preserving their original formatting
- [ ] New blocks receive sensible default formatting based on type
- [ ] Deleted blocks are removed from docx
- [ ] structure.json and manifest.json updated with new mappings and timestamps
- [ ] Inline formatting (bold, italic) from markdown applied correctly
- [ ] Images added/removed in markdown sync to assets/ and docx
- [ ] Typecheck passes
- [ ] Integration test confirms content changes without format loss

### US-004: Validate sidedoc integrity
**Description:** As a user, I want to validate a sidedoc archive to ensure it's well-formed and complete.

**Acceptance Criteria:**
- [ ] `sidedoc validate document.sidedoc` checks ZIP structure
- [ ] Verifies presence of required files (content.md, structure.json, styles.json, manifest.json)
- [ ] Validates JSON schema compliance
- [ ] Checks content hashes match actual content
- [ ] Verifies all referenced assets exist in assets/
- [ ] Returns exit code 0 for valid sidedoc, non-zero with error messages for invalid
- [ ] Typecheck passes
- [ ] Test with corrupted sidedoc files confirms error detection

### US-005: Display sidedoc metadata
**Description:** As a user, I want to view sidedoc metadata to understand the document version, source, and modification history.

**Acceptance Criteria:**
- [ ] `sidedoc info document.sidedoc` displays manifest.json contents
- [ ] Shows sidedoc version, created/modified timestamps
- [ ] Shows source file name and hash
- [ ] Shows content hash and generator version
- [ ] Output is human-readable and well-formatted
- [ ] Typecheck passes
- [ ] Test with sample sidedoc confirms accurate display

### US-006: Unpack sidedoc for debugging
**Description:** As a developer, I want to extract sidedoc contents to a directory so I can inspect and debug the internal structure.

**Acceptance Criteria:**
- [ ] `sidedoc unpack document.sidedoc -o ./unpacked/` extracts all files
- [ ] Creates output directory if it doesn't exist
- [ ] Preserves directory structure (assets/ subfolder)
- [ ] All files are readable and valid
- [ ] Typecheck passes
- [ ] Test confirms unpacked contents match ZIP contents

### US-007: Pack directory into sidedoc
**Description:** As a developer, I want to create a sidedoc archive from an unpacked directory so I can test manual edits to internal files.

**Acceptance Criteria:**
- [ ] `sidedoc pack ./unpacked/ -o document.sidedoc` creates valid ZIP archive
- [ ] Validates directory structure before packing
- [ ] Includes all required files
- [ ] Resulting sidedoc passes validation
- [ ] Typecheck passes
- [ ] Test confirms pack → unpack roundtrip preserves contents

### US-008: Show changes between versions
**Description:** As a user, I want to see what changed in content.md since the last sync so I can review edits before applying them.

**Acceptance Criteria:**
- [ ] `sidedoc diff document.sidedoc` shows markdown diff
- [ ] Displays added, removed, and modified blocks
- [ ] Uses clear formatting (colors, +/- markers)
- [ ] Works even if content.md was edited externally
- [ ] Typecheck passes
- [ ] Test with various edit scenarios confirms accurate diff

### US-009: Handle extraction of inline formatting
**Description:** As a developer, I need bold, italic, and underline runs extracted correctly so formatting is preserved during round-trip.

**Acceptance Criteria:**
- [ ] Bold text in docx becomes `**bold**` in markdown
- [ ] Italic text becomes `*italic*` in markdown
- [ ] Underline preserved in styles.json (not in markdown)
- [ ] Mixed formatting (bold+italic) handled correctly
- [ ] structure.json records inline formatting positions
- [ ] Typecheck passes
- [ ] Test with various inline formatting combinations

### US-010: Handle images in documents
**Description:** As a user, I want images from my Word document included in sidedoc so they appear in the reconstructed docx.

**Acceptance Criteria:**
- [ ] Images extracted to assets/ directory with unique names
- [ ] content.md includes `![alt text](assets/imagename.png)` references
- [ ] structure.json maps image blocks to docx paragraph indices
- [ ] Build embeds images at correct positions
- [ ] Supports common formats (PNG, JPG, GIF)
- [ ] Typecheck passes
- [ ] Test with documents containing multiple images

### US-011: Set up project structure and dependencies
**Description:** As a developer, I need the Python package properly structured so development can proceed efficiently.

**Acceptance Criteria:**
- [ ] pyproject.toml configured with Python 3.11+ requirement
- [ ] Dependencies: python-docx, mistune (or marko), PyYAML, click, pytest
- [ ] Package structure matches specification (src/sidedoc/ layout)
- [ ] README.md with project overview and installation instructions
- [ ] LICENSE file (MIT)
- [ ] .gitignore configured for Python projects
- [ ] Typecheck passes with mypy configuration
- [ ] `pip install -e .` installs package in development mode

### US-012: Implement CLI framework
**Description:** As a developer, I need a click-based CLI framework so all commands are accessible via the sidedoc command.

**Acceptance Criteria:**
- [ ] cli.py implements click command group
- [ ] `sidedoc --help` shows all available commands
- [ ] `sidedoc --version` shows package version
- [ ] Each command accepts appropriate arguments and options
- [ ] Exit codes follow specification (0=success, 1=error, 2=not found, 3=invalid format, 4=sync conflict)
- [ ] Error messages are clear and actionable
- [ ] Typecheck passes
- [ ] Test confirms all commands are registered

## Functional Requirements

- **FR-1:** Extract .docx files into .sidedoc ZIP archives containing content.md, structure.json, styles.json, manifest.json, and assets/
- **FR-2:** Parse docx paragraphs into markdown with headings (H1-H6), paragraphs, bulleted lists, numbered lists, and images
- **FR-3:** Preserve inline formatting (bold, italic, underline) through markdown and styles.json
- **FR-4:** Extract images to assets/ directory and reference them in markdown as `![alt](assets/image.png)`
- **FR-5:** Generate structure.json mapping content blocks to docx paragraph indices with content hashes
- **FR-6:** Generate styles.json storing fonts, sizes, colors, alignment per block
- **FR-7:** Reconstruct .docx from .sidedoc with visually identical formatting to original
- **FR-8:** Apply stored styles from styles.json when building docx paragraphs
- **FR-9:** Detect content.md changes and sync to updated docx while preserving formatting
- **FR-10:** Match edited blocks to original blocks using content hashes and similarity
- **FR-11:** Apply default formatting to new blocks based on block type (heading, paragraph, list)
- **FR-12:** Validate .sidedoc archives for structural integrity, JSON schema compliance, and content hash consistency
- **FR-13:** Display sidedoc metadata including version, timestamps, source file, and hashes
- **FR-14:** Unpack .sidedoc archives to directories for inspection and debugging
- **FR-15:** Pack directories into .sidedoc archives with validation
- **FR-16:** Show diffs between current content.md and last synced state
- **FR-17:** Provide clear error messages with appropriate exit codes (0=success, 1=error, 2=not found, 3=invalid format, 4=sync conflict)

## Technical Requirements

### Technology Stack

- **Language:** Python 3.11+
- **Document handling:** python-docx
- **Markdown parsing:** mistune or marko
- **Configuration/metadata:** PyYAML
- **CLI framework:** click
- **Testing:** pytest
- **Type checking:** mypy

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

### CLI Interface

```bash
# Extract: Create sidedoc from docx
sidedoc extract document.docx
sidedoc extract document.docx -o /path/to/output.sidedoc

# Build: Generate docx from sidedoc
sidedoc build document.sidedoc
sidedoc build document.sidedoc -o /path/to/output.docx

# Sync: Update docx after editing content.md
sidedoc sync document.sidedoc

# Validate: Check sidedoc integrity
sidedoc validate document.sidedoc

# Diff: Show changes between content.md and last synced state
sidedoc diff document.sidedoc

# Info: Display sidedoc metadata
sidedoc info document.sidedoc

# Unpack: Extract sidedoc contents to directory
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

## Success Metrics

1. **Functional completeness**: All CLI commands work as specified, all user stories pass acceptance criteria
2. **Round-trip fidelity**: A document that goes through `extract` → `build` is visually identical to the original when opened in Word (100% match for supported elements)
3. **Sync correctness**: After editing content.md (adding/removing/modifying blocks), `sync` produces a docx that:
   - Reflects all content changes
   - Preserves formatting on unchanged blocks
   - Applies sensible defaults to new blocks
4. **Performance**: Extract and build complete in under 2 seconds for a 10-page document
5. **Test coverage**: >80% code coverage, all tests passing
6. **Type safety**: All code passes mypy type checking
7. **Documentation**: README with usage examples, format specification document

## Design Considerations

### Architecture Philosophy
- Separation of concerns: extraction, reconstruction, and sync are independent modules
- Immutable data structures where possible for content representation
- Block-level sync algorithm (not character-level) for simplicity and maintainability
- Content hashes for efficient block matching during sync

### User Experience
- Clear, actionable error messages with helpful suggestions
- Predictable command behavior: extract/build are pure functions, sync modifies in place
- Progress indication for operations on large documents
- Verbose mode for debugging (--verbose flag)

### Edge Cases to Handle
- Malformed docx files (partial parsing, graceful degradation)
- Markdown syntax errors in edited content.md (validation before sync)
- Missing images referenced in content.md (clear error message)
- Concurrent modifications (file locking or clear error)
- Very large documents (streaming/chunked processing if needed)

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
