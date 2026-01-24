# PRD: Hyperlink Support for Sidedoc

## Introduction

Add hyperlink support to Sidedoc, enabling round-trip preservation of clickable links in Word documents. Hyperlinks are ubiquitous in enterprise documents (references, citations, external resources) and were explicitly deferred from MVP. This feature enables AI agents to read, modify, and create hyperlinks using standard markdown syntax while preserving link formatting and behavior in the reconstructed docx.

**Project Repository:** `sidedoc` (Python package)
**Author:** Jonathan Gardner
**Status:** Post-MVP Phase 1

## Goals

- Extract hyperlinks from docx and represent them as markdown `[text](url)` syntax
- Preserve hyperlink formatting (color, underline) during round-trip
- Support AI agents adding new hyperlinks via markdown syntax
- Enable AI agents to modify existing hyperlink text and URLs
- Maintain backward compatibility with existing sidedoc archives
- Update documentation site with hyperlink feature documentation

## Non-Goals (Out of Scope)

- Bookmark/anchor links within the document (internal references)
- Email links (`mailto:`) - may add in future iteration
- Link tooltips/screentips
- Link target attributes (open in new window)
- Validating that URLs are reachable
- Automatic URL detection in plain text

## User Stories

### US-001: Extract hyperlinks from docx to markdown
**Description:** As an AI developer, I want hyperlinks extracted as markdown syntax so that I can read and process linked content efficiently.

**Acceptance Criteria:**
- [ ] Hyperlinks in docx paragraphs are extracted as `[visible text](url)` in content.md
- [ ] Multiple hyperlinks in a single paragraph are all extracted correctly
- [ ] Hyperlinks spanning multiple runs are handled correctly
- [ ] Hyperlinks with special characters in URL are properly escaped
- [ ] structure.json records hyperlink positions within blocks
- [ ] Typecheck passes
- [ ] Unit tests cover various hyperlink scenarios

### US-002: Store hyperlink formatting metadata
**Description:** As a developer, I need hyperlink formatting stored in styles.json so that links maintain their appearance after round-trip.

**Acceptance Criteria:**
- [ ] styles.json stores hyperlink-specific formatting (color, underline style)
- [ ] Default hyperlink style (blue, underlined) is recorded
- [ ] Custom hyperlink colors are preserved
- [ ] Visited link colors are not tracked (not applicable to static docs)
- [ ] Typecheck passes
- [ ] Unit tests verify formatting storage

### US-003: Reconstruct hyperlinks in docx from sidedoc
**Description:** As a user, I want hyperlinks in the rebuilt docx to be clickable and properly formatted so that the document functions as expected.

**Acceptance Criteria:**
- [ ] Markdown `[text](url)` syntax converts to clickable docx hyperlinks
- [ ] Hyperlink text displays correctly in Word
- [ ] Clicking the link opens the URL in default browser
- [ ] Hyperlink formatting (color, underline) matches original or uses Word defaults
- [ ] Hyperlinks work in Microsoft Word, Google Docs, and LibreOffice
- [ ] Typecheck passes
- [ ] Integration test confirms round-trip produces working links

### US-004: Sync edited hyperlinks back to docx
**Description:** As an AI agent, I want to modify hyperlink text or URLs and have those changes reflected in the synced docx so that I can update references programmatically.

**Acceptance Criteria:**
- [ ] Changing link text in markdown updates the visible text in docx
- [ ] Changing URL in markdown updates the hyperlink target
- [ ] Adding new `[text](url)` creates new hyperlink in docx
- [ ] Removing markdown link syntax removes hyperlink (text remains as plain text)
- [ ] Formatting of modified links uses sensible defaults (blue, underlined)
- [ ] Typecheck passes
- [ ] Integration test confirms sync preserves existing formatting where possible

### US-005: Handle edge cases in hyperlink extraction
**Description:** As a developer, I need edge cases handled gracefully so that extraction doesn't fail on complex documents.

**Acceptance Criteria:**
- [ ] Empty hyperlinks (no visible text) are handled gracefully
- [ ] Hyperlinks with no URL are treated as plain text
- [ ] Very long URLs (>2000 chars) are preserved correctly
- [ ] URLs with unicode characters are encoded properly
- [ ] Nested formatting within hyperlinks (bold link text) is preserved
- [ ] Typecheck passes
- [ ] Unit tests cover all edge cases

### US-006: Handle hyperlinks in lists
**Description:** As a user, I want hyperlinks within list items to work correctly so that bulleted/numbered lists with references are supported.

**Acceptance Criteria:**
- [ ] Hyperlinks in bulleted list items extract correctly
- [ ] Hyperlinks in numbered list items extract correctly
- [ ] Multiple hyperlinks in a single list item are handled
- [ ] Hyperlinks rebuild correctly within list context
- [ ] Typecheck passes
- [ ] Unit tests verify list hyperlink handling

### US-007: Validate sidedoc with hyperlinks
**Description:** As a user, I want validation to check hyperlink integrity so that I catch issues before building.

**Acceptance Criteria:**
- [ ] `sidedoc validate` checks that hyperlink positions in structure.json are valid
- [ ] Validation warns if URL format is malformed (optional, non-blocking)
- [ ] Validation passes for documents with valid hyperlinks
- [ ] Clear error messages for hyperlink-related validation failures
- [ ] Typecheck passes
- [ ] Unit tests cover validation scenarios

### US-008: Update test fixtures with hyperlink examples
**Description:** As a developer, I need test fixtures that include hyperlinks so that automated tests verify the feature.

**Acceptance Criteria:**
- [ ] Create `tests/fixtures/hyperlinks.docx` with various hyperlink scenarios
- [ ] Fixture includes: simple links, multiple links per paragraph, formatted link text
- [ ] Fixture includes: links in headings, links in lists
- [ ] Fixture includes: long URLs, URLs with special characters
- [ ] Document fixture contents in test file comments
- [ ] Typecheck passes

### US-009: Update CLI help and documentation
**Description:** As a user, I want documentation updated so that I understand hyperlink support is available.

**Acceptance Criteria:**
- [ ] README.md updated with hyperlink support in "Supported Elements" section
- [ ] CLI `--help` output reflects any new options (if applicable)
- [ ] CHANGELOG.md entry for hyperlink feature
- [ ] Typecheck passes

### US-010: Update documentation website with hyperlink feature
**Description:** As a potential user, I want the docs site updated so that I know Sidedoc supports hyperlinks.

**Acceptance Criteria:**
- [ ] Docs site "Features" page lists hyperlink support
- [ ] Docs site "Format Specification" page documents hyperlink handling
- [ ] Example showing hyperlink extraction and reconstruction
- [ ] Migration notes for existing sidedoc archives (backward compatible)
- [ ] Docs site builds without errors

## Functional Requirements

- **FR-1:** Extract docx hyperlinks as markdown `[text](url)` syntax in content.md
- **FR-2:** Store hyperlink positions in structure.json `inline_formatting` array with type "hyperlink"
- **FR-3:** Store hyperlink formatting (color, underline) in styles.json runs
- **FR-4:** Reconstruct clickable hyperlinks from markdown syntax during `sidedoc build`
- **FR-5:** Sync hyperlink changes (text, URL, add, remove) during `sidedoc sync`
- **FR-6:** Apply default hyperlink formatting (blue #0563C1, underline) to new links
- **FR-7:** Preserve original hyperlink formatting for unchanged links
- **FR-8:** Validate hyperlink structure during `sidedoc validate`
- **FR-9:** Handle hyperlinks within all supported block types (paragraphs, headings, lists)
- **FR-10:** URL-encode special characters in hyperlink URLs for markdown compatibility

## Technical Considerations

### python-docx Hyperlink Handling

python-docx provides access to hyperlinks through the `paragraph._element` XML. Hyperlinks are represented as `<w:hyperlink>` elements containing runs. Key considerations:

```python
# Accessing hyperlinks requires working with the underlying XML
from docx.oxml.ns import qn

for paragraph in document.paragraphs:
    for hyperlink in paragraph._element.findall(qn('w:hyperlink')):
        # Get the relationship ID
        r_id = hyperlink.get(qn('r:id'))
        # Look up the actual URL from relationships
        url = document.part.rels[r_id].target_ref
        # Get the visible text from runs within the hyperlink
        text = ''.join(run.text for run in hyperlink.findall(qn('w:r')))
```

### Markdown Escaping

URLs in markdown links need proper escaping:
- Parentheses in URLs: `[text](url%28with%29parens)`
- Spaces in URLs: `[text](url%20with%20spaces)`
- Special markdown characters in text: `[text with \[brackets\]](url)`

### Structure.json Schema Update

Add hyperlink tracking to `inline_formatting`:

```json
{
  "inline_formatting": [
    {
      "type": "hyperlink",
      "start": 10,
      "end": 25,
      "url": "https://example.com"
    }
  ]
}
```

### Styles.json Schema Update

Hyperlink runs should include link-specific formatting:

```json
{
  "runs": [
    {
      "start": 10,
      "end": 25,
      "bold": false,
      "italic": false,
      "underline": true,
      "color": "0563C1",
      "is_hyperlink": true
    }
  ]
}
```

### Backward Compatibility

- Existing sidedoc archives without hyperlinks remain valid
- Sidedoc version in manifest.json should indicate hyperlink support capability
- Older CLI versions should gracefully ignore hyperlink metadata they don't understand

## Design Considerations

### Hyperlink Detection in Markdown

During sync, the markdown parser must detect `[text](url)` patterns and map them back to hyperlinks. The marko/mistune parser provides this natively.

### Conflict with Images

Image syntax `![alt](path)` is similar to link syntax `[text](url)`. The `!` prefix distinguishes them. Parser must handle both correctly, including edge cases like `[![alt](img)](url)` (clickable image).

### Multiple Links Same Text

If the same visible text links to different URLs in different locations, each instance must be tracked separately in structure.json by position.

## Success Metrics

- Round-trip test: extract → build produces identical hyperlinks (100% fidelity for supported scenarios)
- All hyperlinks in test fixtures are clickable in rebuilt docx
- No regression in existing extract/build/sync functionality
- Benchmark shows minimal token overhead for hyperlink metadata
- Documentation site reflects new capability within this release

## Open Questions

1. **Should we support `mailto:` links?** These are common in business documents but have different behavior. Recommendation: Defer to future iteration.

2. **Should relative URLs be supported?** Relative URLs don't make sense outside the original document context. Recommendation: Convert to absolute or warn.

3. **How should we handle hyperlinks to local files?** `file:///` URLs are platform-specific. Recommendation: Preserve as-is, document limitation.

4. **Should we validate URL reachability?** This would require network access and slow down validation. Recommendation: No, just validate URL format optionally.

---

## Appendix: Hyperlink Extraction Examples

### Example 1: Simple Paragraph with Link

**Input docx paragraph:**
> Visit our website at Example.com for more information.
> (where "Example.com" is hyperlinked to https://example.com)

**Extracted content.md:**
```markdown
Visit our website at [Example.com](https://example.com) for more information.
```

**structure.json:**
```json
{
  "id": "block-0",
  "type": "paragraph",
  "inline_formatting": [
    {
      "type": "hyperlink",
      "start": 21,
      "end": 32,
      "url": "https://example.com"
    }
  ]
}
```

### Example 2: Multiple Links in Paragraph

**Input docx paragraph:**
> Contact us via email or visit our help center.
> ("email" links to mailto:support@example.com, "help center" links to https://help.example.com)

**Extracted content.md:**
```markdown
Contact us via [email](mailto:support@example.com) or visit our [help center](https://help.example.com).
```

### Example 3: Formatted Link Text

**Input docx paragraph:**
> Read the **important announcement** for details.
> ("important announcement" is bold AND hyperlinked)

**Extracted content.md:**
```markdown
Read the [**important announcement**](https://example.com/announcement) for details.
```

### Example 4: Link in List

**Input docx:**
> - See the documentation
> - Contact support
> (both are hyperlinked)

**Extracted content.md:**
```markdown
- [See the documentation](https://docs.example.com)
- [Contact support](https://support.example.com)
```
