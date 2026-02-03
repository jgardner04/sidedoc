# Frequently Asked Questions

## What problem does Sidedoc solve?

Current document workflows force a painful tradeoff: AI tools work efficiently with plain text, but humans need rich formatting. The typical solutions are inadequate:

| Approach | Problem |
|----------|---------|
| Extract content with Document Intelligence | Loses formatting connections; can't update original |
| Convert with Pandoc | One-way; repeated conversions degrade formatting |
| Parse docx XML directly | Expensive (15,000+ tokens); complex; brittle |
| Store everything as markdown | Humans get ugly, unformatted documents |

**Sidedoc solves this** by maintaining two synchronized representations: clean markdown for AI efficiency and formatted docx for human consumption. Edit either one, and changes propagate to the other without losing formatting.

---

## Why not just use Pandoc?

Pandoc is excellent at one-way conversion, but it wasn't designed for round-trip workflows:

- **No formatting memory:** Pandoc doesn't remember the original document's fonts, colors, or custom styles
- **Lossy round-trips:** Each markdown → docx → markdown cycle loses information
- **No maintained link:** Once you convert, there's no connection between source and output
- **Generic output:** Generated docx uses default styles, not your corporate templates

**Sidedoc differs** by storing formatting metadata alongside content. When you edit the markdown and rebuild, Sidedoc reapplies the *original* formatting—fonts, sizes, colors, alignment—automatically.

---

## Why not store documents as pure markdown?

Pure markdown works for technical documentation, but fails for business documents:

- **Formatting matters:** Quarterly reports, proposals, and contracts need specific fonts, colors, and layouts
- **Brand consistency:** Organizations have style guides that plain markdown can't enforce
- **Human expectations:** Non-technical stakeholders expect Word documents, not raw text files

**Sidedoc gives you both:** AI works with clean markdown (efficient, diffable, version-controllable) while humans receive properly formatted Word documents (professional, branded, familiar).

---

## Why markdown instead of HTML or plain text?

We chose markdown because it hits the sweet spot:

| Format | Pros | Cons |
|--------|------|------|
| **Plain text** | Simple | No structure; can't represent headings, lists, emphasis |
| **HTML** | Rich structure | Verbose; mixes content with presentation; harder for AI |
| **Markdown** | Clean structure; readable; compact | Limited formatting (which is actually fine for content) |

Markdown provides enough structure (headings, lists, emphasis, images) to represent document content while staying clean and AI-efficient. The formatting details that markdown *can't* express (fonts, colors, exact spacing) are stored separately in `styles.json`.

---

## Why use a ZIP container instead of a single file?

The ZIP container approach has several advantages:

- **Separation of concerns:** Content, structure, styles, and assets live in separate files
- **Easy debugging:** Unzip and inspect any component with standard tools
- **Selective access:** Read just `content.md` without parsing everything
- **Binary asset handling:** Images stored as-is, not base64-encoded inline
- **Familiar pattern:** docx, xlsx, and epub all use ZIP containers internally

You can inspect a sidedoc with standard tools:

```bash
# View the markdown content
unzip -p document.sidedoc content.md

# Extract everything for debugging
unzip document.sidedoc -d ./unpacked/
```

---

## Why block-level sync instead of character-level?

We chose block-level sync (paragraphs, headings, list items) over character-level diffing because:

- **Simpler implementation:** Block matching is more robust than character alignment
- **Natural edit units:** People add/remove/edit paragraphs, not individual characters
- **Formatting boundaries:** Word formatting is typically paragraph-based anyway
- **Predictable behavior:** Easier to understand what will happen when you sync

The tradeoff is that merging changes within a single paragraph is less granular—but in practice, AI edits tend to rewrite entire paragraphs rather than tweaking individual words.

---

## How is this different from Google Docs or Office 365?

Cloud collaboration tools solve a different problem:

| Feature | Google Docs / O365 | Sidedoc |
|---------|-------------------|---------|
| **Primary use** | Real-time human collaboration | AI-human document workflows |
| **AI integration** | Requires API, expensive | Native markdown format |
| **Offline support** | Limited | Fully offline |
| **Format control** | Platform-dependent | Preserves exact docx formatting |
| **Version control** | Proprietary history | Git-friendly markdown |
| **Privacy** | Cloud-hosted | Local files only |

**Sidedoc is complementary:** You might use Sidedoc to prepare a document with AI assistance, then upload the final docx to Google Docs for human review.

---

## What document elements are NOT supported?

The MVP focuses on the most common elements. Here's what's supported and what's not:

!!! success "Fully Supported"
    - Headings (H1-H6)
    - Paragraphs
    - Bold and italic text
    - Bulleted lists (single level)
    - Numbered lists (single level)
    - Images
    - Hyperlinks (`[text](url)` syntax)

!!! warning "Preserved but Not Editable"
    These elements are kept intact but editing them in markdown won't work correctly:

    - Nested lists (2+ levels)
    - Underlined text
    - Custom named styles
    - Font colors and highlighting

!!! danger "Not Supported (MVP)"
    These elements are not preserved:

    - Tables
    - Headers and footers
    - Footnotes and endnotes
    - Track changes and comments
    - Text boxes and shapes
    - Charts

---

## Why was this project created?

Sidedoc emerged from a practical frustration: working with AI coding assistants on business documents was painful. Every iteration required:

1. Extract content from docx (expensive, loses formatting)
2. AI edits the content
3. Manually recreate the document in Word (tedious, error-prone)
4. Repeat

**The core insight:** If documents had a stable, AI-friendly representation that maintained a live connection to formatting, this workflow could be 10x more efficient and completely lossless.

Sidedoc is that representation.
