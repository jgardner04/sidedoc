# PRD: Track Changes Support for Sidedoc

## Introduction

Add bidirectional track changes support to Sidedoc, enabling round-trip preservation of Word revision tracking. Track changes are essential for collaborative document workflows in enterprise environments, allowing reviewers to see exactly what changed and accept/reject modifications. This feature enables AI agents to work with tracked documents and produce output where AI edits appear as reviewable changes.

**Project Repository:** `sidedoc` (Python package)
**Author:** Jonathan Gardner
**Status:** Post-MVP Phase 2 (following Hyperlinks)

## Goals

- Extract track changes (insertions/deletions) from docx and represent them using CriticMarkup syntax
- Preserve track change metadata (author, date) during round-trip
- Support AI agents viewing and understanding pending changes in documents
- Enable AI edits to appear as tracked changes in output docx (reviewable in Word)
- Smart behavior: inherit track changes mode from source document
- Configurable author attribution for AI-generated changes
- Maintain backward compatibility with existing sidedoc archives

## Non-Goals (Out of Scope for Phase 1)

- Formatting changes (bold/italic/underline revisions) - Phase 2
- Comments attached to track changes - Phase 3
- Move tracking (text relocated within document) - Phase 4
- Accept/reject operations within sidedoc (use Word for this)
- Real-time collaborative editing
- Merge conflict resolution for concurrent edits
- Track changes in tables (tables not yet supported)

## Success Metrics

### Primary Metric: Round-Trip Fidelity

**Definition:** 100% of track changes survive the extract → build cycle with content, author, and date preserved.

| Attribute | Requirement |
|-----------|-------------|
| Inserted/deleted text | Exact match |
| Author name | Exact match |
| Date/timestamp | Exact match (ISO 8601) |
| Revision ID | May be regenerated (not user-visible) |

### Validation Method: Automated Test Suite

All validation is performed via automated tests that:
1. Create Word documents with known track changes
2. Extract to sidedoc format
3. Rebuild to docx
4. Programmatically compare track change metadata before/after

### Acceptance Threshold

**Zero failures.** All test cases must pass. Any failure blocks release.

### Definition of Done (Phase 1)

- [ ] All automated tests pass (100% pass rate)
- [ ] Type checking passes (`mypy src/`)
- [ ] User-facing documentation updated
- [ ] No regressions in existing functionality

## User Stories

### US-001: Extract track changes from docx to CriticMarkup
**Description:** As an AI developer, I want track changes extracted as CriticMarkup syntax so that AI can see and understand what changes are pending review.

**Acceptance Criteria:**
- [ ] Insertions in docx are extracted as `{++inserted text++}` in content.md
- [ ] Deletions in docx are extracted as `{--deleted text--}` in content.md
- [ ] Multiple track changes in a single paragraph are all extracted correctly
- [ ] Track changes spanning multiple runs are handled correctly
- [ ] structure.json records track change positions, authors, and dates
- [ ] Typecheck passes
- [ ] Unit tests cover various track change scenarios

### US-002: Store track change metadata
**Description:** As a developer, I need track change metadata stored in structure.json so that author and date information survives round-trip.

**Acceptance Criteria:**
- [ ] structure.json stores `track_changes` array per block
- [ ] Each track change includes: type, start, end, author, date, revision_id
- [ ] Deletions include the deleted text content
- [ ] manifest.json indicates whether source had track changes enabled
- [ ] Typecheck passes
- [ ] Unit tests verify metadata storage

### US-003: Reconstruct track changes in docx from sidedoc
**Description:** As a user, I want track changes in the rebuilt docx to appear exactly as in the original so that I can continue the review workflow in Word.

**Acceptance Criteria:**
- [ ] CriticMarkup `{++text++}` converts to `w:ins` elements in docx
- [ ] CriticMarkup `{--text--}` converts to `w:del` elements in docx
- [ ] Author and date attributes are preserved on reconstructed elements
- [ ] Track changes are visible and functional in Microsoft Word
- [ ] Typecheck passes
- [ ] Integration test confirms round-trip produces identical track changes

### US-004: AI edits appear as tracked changes
**Description:** As a document owner, I want AI edits to appear as tracked changes so that I can review and accept/reject them in Word.

**Acceptance Criteria:**
- [ ] When source doc had track changes, AI modifications create new tracked changes
- [ ] New insertions get `w:ins` elements with configured author name
- [ ] Removed content gets `w:del` elements with configured author name
- [ ] Timestamps reflect when sync was performed
- [ ] Default author is "Sidedoc AI" (configurable via CLI)
- [ ] Typecheck passes
- [ ] Integration test confirms AI edits are reviewable in Word

### US-005: Smart track changes detection
**Description:** As a user, I want sidedoc to automatically detect whether to use track changes based on my source document.

**Acceptance Criteria:**
- [ ] If source docx contains `w:ins` or `w:del` elements, enable track changes mode
- [ ] If source docx has no revisions, output docx has no track changes
- [ ] CLI flag `--track-changes` overrides auto-detection
- [ ] CLI flag `--no-track-changes` disables even if source had changes
- [ ] manifest.json records `track_changes.source_had_revisions` boolean
- [ ] Typecheck passes
- [ ] Unit tests verify detection logic

### US-006: Handle track changes in all block types
**Description:** As a user, I want track changes to work in headings and lists, not just paragraphs.

**Acceptance Criteria:**
- [ ] Track changes in headings (H1-H6) extract and reconstruct correctly
- [ ] Track changes in bulleted list items work correctly
- [ ] Track changes in numbered list items work correctly
- [ ] Multiple track changes in a single list item are handled
- [ ] Typecheck passes
- [ ] Unit tests verify all block type scenarios

### US-007: Parse CriticMarkup during sync
**Description:** As an AI agent, I want to use CriticMarkup syntax in content.md to explicitly mark insertions and deletions.

**Acceptance Criteria:**
- [ ] `{++new text++}` in edited content.md creates insertion in docx
- [ ] `{--removed text--}` in edited content.md creates deletion in docx
- [ ] `{~~old~>new~~}` substitution syntax creates deletion + insertion
- [ ] CriticMarkup with nested markdown formatting works (`{++**bold**++}`)
- [ ] Invalid CriticMarkup syntax produces clear error message
- [ ] Typecheck passes
- [ ] Unit tests cover CriticMarkup parsing edge cases

### US-008: Configurable author attribution
**Description:** As an enterprise user, I want to configure the author name for AI-generated changes to match our naming conventions.

**Acceptance Criteria:**
- [ ] Default author is "Sidedoc AI"
- [ ] `--author "Name"` CLI option overrides default
- [ ] Author name appears correctly in Word's track changes pane
- [ ] Configuration can be set in sidedoc config file (future)
- [ ] Typecheck passes
- [ ] Unit tests verify author attribution

### US-009: Validate sidedoc with track changes
**Description:** As a user, I want validation to check track change integrity.

**Acceptance Criteria:**
- [ ] `sidedoc validate` checks track change positions are within block bounds
- [ ] Validation verifies track change metadata is complete (author, date)
- [ ] Clear error messages for track change validation failures
- [ ] Validation passes for documents with valid track changes
- [ ] Typecheck passes
- [ ] Unit tests cover validation scenarios

### US-010: Update test fixtures
**Description:** As a developer, I need test fixtures that include track changes.

**Acceptance Criteria:**
- [ ] Create `tests/fixtures/track_changes_simple.docx` with basic insertions/deletions
- [ ] Create `tests/fixtures/track_changes_complex.docx` with multiple authors, nested changes
- [ ] Fixtures include track changes in headings and lists
- [ ] Document fixture contents in test file comments
- [ ] Typecheck passes

## Functional Requirements

- **FR-1:** Extract `w:ins` elements from docx as CriticMarkup `{++text++}` syntax
- **FR-2:** Extract `w:del` elements from docx as CriticMarkup `{--text--}` syntax
- **FR-3:** Store track change metadata (author, date, positions) in structure.json
- **FR-4:** Store track changes mode in manifest.json (`track_changes.enabled`)
- **FR-5:** Reconstruct `w:ins` XML elements from CriticMarkup during build
- **FR-6:** Reconstruct `w:del` XML elements from CriticMarkup during build
- **FR-7:** Preserve author and date attributes on reconstructed track changes
- **FR-8:** Auto-detect track changes mode from source document
- **FR-9:** Generate track changes for AI edits during sync (when enabled)
- **FR-10:** Apply configurable author name to AI-generated track changes
- **FR-11:** Parse CriticMarkup substitution syntax `{~~old~>new~~}`
- **FR-12:** Validate track change integrity during `sidedoc validate`
- **FR-13:** Handle track changes in paragraphs, headings, and list items
- **FR-14:** Provide clear error messages for track change parsing failures

## Technical Considerations

### Word Track Changes XML Structure

Track changes use specific XML elements in the `w:` namespace:

```xml
<!-- Insertion -->
<w:ins w:id="1" w:author="John Doe" w:date="2026-01-15T10:30:00Z">
  <w:r><w:t>inserted text</w:t></w:r>
</w:ins>

<!-- Deletion -->
<w:del w:id="2" w:author="Jane Smith" w:date="2026-01-15T11:00:00Z">
  <w:r><w:delText>deleted text</w:delText></w:r>
</w:del>
```

### CriticMarkup Syntax

Standard CriticMarkup syntax for document revision:

| Syntax | Meaning | Example |
|--------|---------|---------|
| `{++text++}` | Insertion | `{++new content++}` |
| `{--text--}` | Deletion | `{--removed content--}` |
| `{~~old~>new~~}` | Substitution | `{~~typo~>fixed~~}` |

### structure.json Schema Extension

```json
{
  "blocks": [{
    "id": "block-0",
    "type": "paragraph",
    "track_changes": [
      {
        "type": "insertion",
        "start": 12,
        "end": 26,
        "author": "John Doe",
        "date": "2026-01-15T10:30:00Z",
        "revision_id": "1"
      },
      {
        "type": "deletion",
        "start": 30,
        "end": 45,
        "deleted_text": "removed text",
        "author": "Jane Smith",
        "date": "2026-01-15T11:00:00Z",
        "revision_id": "2"
      }
    ]
  }]
}
```

### manifest.json Extension

```json
{
  "track_changes": {
    "enabled": true,
    "source_had_revisions": true,
    "default_author": "Sidedoc AI"
  }
}
```

### Backward Compatibility

- Existing sidedoc archives without `track_changes` fields remain valid
- Older CLI versions should ignore unknown `track_changes` metadata
- No breaking changes to existing structure.json or manifest.json schemas

## Phased Delivery

| Phase | Scope | Dependencies |
|-------|-------|--------------|
| **Phase 1** | Text insertions/deletions | None |
| Phase 2 | Formatting changes (`w:rPrChange`) | Phase 1 |
| Phase 3 | Comments (`w:comment`, `w:commentRangeStart`) | Phase 1 |
| Phase 4 | Move tracking (`w:moveFrom`, `w:moveTo`) | Phase 1 |

## Testing Strategy

### Test Categories

1. **Unit Tests** - Individual functions in isolation
   - CriticMarkup parsing
   - XML element creation
   - Metadata extraction

2. **Integration Tests** - Full round-trip workflows
   - Extract → Build fidelity
   - Sync with track changes generation
   - CLI option handling

3. **Edge Case Tests** - Boundary conditions
   - Empty insertions/deletions
   - Track changes at block boundaries
   - Nested markdown within track changes
   - Multiple authors in same paragraph

### Required Test Fixtures

| Fixture | Contents |
|---------|----------|
| `track_changes_simple.docx` | Single insertion, single deletion |
| `track_changes_paragraph.docx` | Multiple changes in one paragraph |
| `track_changes_multiauthor.docx` | Changes from different authors |
| `track_changes_lists.docx` | Changes within list items |
| `track_changes_headings.docx` | Changes within headings |

### Verification Commands

```bash
# Run all track changes tests
pytest tests/test_track_changes.py -v

# Run with coverage
pytest tests/test_track_changes.py --cov=sidedoc --cov-report=term-missing

# Type checking
mypy src/sidedoc/

# Manual verification
sidedoc extract tests/fixtures/track_changes_simple.docx -o test.sidedoc
sidedoc unpack test.sidedoc -o unpacked/
cat unpacked/content.md  # Should show CriticMarkup
sidedoc build test.sidedoc -o rebuilt.docx
# Open rebuilt.docx in Word - track changes should be visible
```

## CLI Interface

### Updated Commands

```bash
# Extract with track changes auto-detection (default)
sidedoc extract document.docx

# Force track changes mode
sidedoc extract document.docx --track-changes

# Disable track changes (accept all in output)
sidedoc extract document.docx --no-track-changes

# Sync with custom author
sidedoc sync document.sidedoc --author "Review Bot"

# Build with track changes preserved
sidedoc build document.sidedoc -o output.docx
```

### New CLI Options

| Command | Option | Description |
|---------|--------|-------------|
| `extract` | `--track-changes` | Force enable track changes mode |
| `extract` | `--no-track-changes` | Force disable (accept all) |
| `sync` | `--author NAME` | Set author for AI changes |
| `sync` | `--accept-all` | Accept existing changes before sync |

## Open Questions

1. **Nested track changes:** Word allows changes within changes (edit an insertion). Should we support this in Phase 1?
   **Decision:** No - flatten to simplest representation. Document as limitation.

2. **Track changes in images:** Should image add/remove be tracked?
   **Decision:** Yes, but as block-level change, not inline.

3. **Date timezone handling:** Should we normalize to UTC or preserve original?
   **Decision:** Preserve original timezone from source; use UTC for new changes.

## References

- [CriticMarkup Specification](http://criticmarkup.com/spec.php)
- [Office Open XML Track Changes](https://docs.microsoft.com/en-us/openspecs/office_standards/ms-docx/)
- [python-docx Documentation](https://python-docx.readthedocs.io/)
- [Sidedoc Hyperlinks PRD](docs/prd-hyperlinks.md) - Pattern reference

---

## Appendix: Implementation Files

### Files to Create

| File | Purpose |
|------|---------|
| `src/sidedoc/track_changes.py` | Core track changes module |
| `tests/test_track_changes.py` | Track changes test suite |
| `tests/fixtures/track_changes_*.docx` | Test fixtures |

### Files to Modify

| File | Changes |
|------|---------|
| `src/sidedoc/extract.py` | Add track change extraction |
| `src/sidedoc/reconstruct.py` | Add track change reconstruction |
| `src/sidedoc/sync.py` | Add CriticMarkup parsing, track change generation |
| `src/sidedoc/models.py` | Add `track_changes` field to Block |
| `src/sidedoc/cli.py` | Add CLI options |
| `src/sidedoc/constants.py` | Add CriticMarkup patterns |
