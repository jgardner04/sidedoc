# GitHub Pages Documentation Site Implementation Plan

## Overview

Set up a GitHub Pages documentation site for Sidedoc using MkDocs Material theme with custom styling (Inter font, JetBrains Mono for code, burnt orange #E67E22 accent), deployed automatically via GitHub Actions.

## Current State Analysis

- **Documentation exists:** PRD at `docs/slidedoc-prd.md`, research at `docs/research/`
- **No MkDocs setup:** No `mkdocs.yml` configuration
- **No GitHub Actions:** No `.github/workflows/` directory
- **No Python source code yet:** Project is in planning phase

### Key Discoveries:
- The `docs/` folder contains implementation documentation (PRD, research) - not website content
- Best practice: Use a dedicated `website/` folder for MkDocs to keep concerns separated
- MkDocs Material supports custom color schemes via CSS variables
- Inter and JetBrains Mono are available via Google Fonts

## Desired End State

After implementation:
1. A `website/` folder contains all MkDocs configuration and documentation source files
2. Custom CSS implements the user's style guide (burnt orange accent, Inter/JetBrains Mono fonts)
3. GitHub Actions automatically deploys to GitHub Pages on push to main
4. Documentation site is live at `https://jgardner04.github.io/sidedoc/`

### Verification:
- `mkdocs serve` runs locally without errors
- `mkdocs build --strict` completes successfully
- GitHub Actions workflow deploys successfully
- Site renders with correct fonts and colors

## What We're NOT Doing

- Moving or reorganizing existing `docs/` folder content
- Setting up versioned documentation (can add later with `mike` plugin)
- Configuring `mkdocstrings` or `mkdocs-click` (no Python code exists yet)
- Creating comprehensive API documentation (no code to document)
- Custom domain setup (using default GitHub Pages URL)

## Implementation Approach

Use a dedicated `website/` folder structure:
```
sidedoc/
├── docs/                    # Existing - PRD, research (unchanged)
├── website/                 # NEW - MkDocs project
│   ├── docs/               # MkDocs source files
│   │   ├── index.md
│   │   ├── getting-started.md
│   │   ├── format-specification.md
│   │   └── stylesheets/
│   │       └── extra.css
│   └── mkdocs.yml
├── .github/
│   └── workflows/
│       └── docs.yml
└── ...
```

---

## Phase 1: Project Setup

### Overview
Create the MkDocs project structure with configuration and custom CSS.

### Changes Required:

#### 1. Create MkDocs Configuration
**File**: `website/mkdocs.yml`

```yaml
site_name: Sidedoc
site_description: AI-native document format that separates content from formatting
site_author: Jonathan Gardner
site_url: https://jgardner04.github.io/sidedoc/
repo_url: https://github.com/jgardner04/sidedoc
repo_name: jgardner04/sidedoc

docs_dir: docs
site_dir: site

theme:
  name: material
  palette:
    - scheme: sidedoc
      toggle:
        icon: material/brightness-7
        name: Switch to dark mode
    - scheme: sidedoc-dark
      toggle:
        icon: material/brightness-4
        name: Switch to light mode
  font:
    text: Inter
    code: JetBrains Mono
  features:
    - navigation.sections
    - navigation.top
    - search.suggest
    - search.highlight
    - content.code.copy
  icon:
    repo: fontawesome/brands/github

plugins:
  - search

markdown_extensions:
  - pymdownx.highlight:
      anchor_linenums: true
  - pymdownx.inlinehilite
  - pymdownx.snippets
  - pymdownx.superfences
  - admonition
  - pymdownx.details
  - tables
  - attr_list
  - md_in_html

extra_css:
  - stylesheets/extra.css

nav:
  - Home: index.md
  - Getting Started: getting-started.md
  - Format Specification: format-specification.md
```

#### 2. Create Custom Stylesheet
**File**: `website/docs/stylesheets/extra.css`

```css
/* Sidedoc Light Theme */
[data-md-color-scheme="sidedoc"] {
  /* Primary colors */
  --md-primary-fg-color: #2C3E50;
  --md-primary-fg-color--light: #4A6785;
  --md-primary-fg-color--dark: #1A252F;

  /* Accent color - burnt orange */
  --md-accent-fg-color: #E67E22;
  --md-accent-fg-color--transparent: rgba(230, 126, 34, 0.1);

  /* Background */
  --md-default-bg-color: #F8F9FA;
  --md-default-bg-color--light: #FFFFFF;
  --md-default-bg-color--lighter: #FFFFFF;
  --md-default-bg-color--lightest: #FFFFFF;

  /* Text */
  --md-default-fg-color: #2C3E50;
  --md-default-fg-color--light: #4A6785;
  --md-default-fg-color--lighter: #6C8EAD;
  --md-default-fg-color--lightest: #8EAAC4;

  /* Typeset links */
  --md-typeset-a-color: #E67E22;

  /* Code */
  --md-code-bg-color: #EBEDEF;
  --md-code-fg-color: #2C3E50;
}

/* Sidedoc Dark Theme */
[data-md-color-scheme="sidedoc-dark"] {
  /* Primary colors */
  --md-primary-fg-color: #E8E8E8;
  --md-primary-fg-color--light: #B0B0B0;
  --md-primary-fg-color--dark: #FFFFFF;

  /* Accent color - burnt orange (same in dark mode) */
  --md-accent-fg-color: #E67E22;
  --md-accent-fg-color--transparent: rgba(230, 126, 34, 0.1);

  /* Background */
  --md-default-bg-color: #1A1A1A;
  --md-default-bg-color--light: #242424;
  --md-default-bg-color--lighter: #2E2E2E;
  --md-default-bg-color--lightest: #383838;

  /* Text */
  --md-default-fg-color: #E8E8E8;
  --md-default-fg-color--light: #B0B0B0;
  --md-default-fg-color--lighter: #909090;
  --md-default-fg-color--lightest: #707070;

  /* Typeset links */
  --md-typeset-a-color: #E67E22;

  /* Code */
  --md-code-bg-color: #2E2E2E;
  --md-code-fg-color: #E8E8E8;
}

/* Additional styling */
.md-header {
  background-color: var(--md-primary-fg-color);
}

.md-tabs {
  background-color: var(--md-primary-fg-color);
}
```

#### 3. Create Directory Structure
```bash
mkdir -p website/docs/stylesheets
```

### Success Criteria:

#### Automated Verification:
- [x] Directory structure exists: `ls website/docs/stylesheets`
- [x] MkDocs config is valid YAML: `python -c "import yaml; yaml.safe_load(open('website/mkdocs.yml'))"`

#### Manual Verification:
- [ ] Files are created in correct locations

---

## Phase 2: Create Documentation Content

### Overview
Create the initial documentation pages, incorporating content from the PRD.

### Changes Required:

#### 1. Homepage
**File**: `website/docs/index.md`

```markdown
# Sidedoc

**AI-native document format that separates content from formatting.**

Sidedoc enables efficient AI interaction with documents while preserving rich formatting for human consumption. A `.sidedoc` file is a ZIP archive containing markdown content and formatting metadata that can reconstruct the original docx.

## The Problem

Current document workflows force a tradeoff between AI efficiency and human usability:

- **Reading documents:** Extracting content for AI is expensive and loses formatting connections
- **Creating documents:** Tools like Pandoc generate docx from markdown, but it's one-way
- **Iterative collaboration:** Repeated extraction and regeneration is lossy and expensive

## The Solution

Documents should have two representations that stay in sync:

- **Markdown** - optimized for AI reading and writing
- **Formatted docx** - optimized for human consumption

Changes to either propagate to the other.

## Quick Example

```bash
# Extract a Word document to sidedoc format
sidedoc extract quarterly_report.docx

# AI edits the markdown content...

# Sync changes back, preserving formatting
sidedoc sync quarterly_report.sidedoc

# Rebuild the formatted Word document
sidedoc build quarterly_report.sidedoc
```

## What's in a .sidedoc file?

| File | Purpose |
|------|---------|
| `content.md` | Clean markdown that AI reads/writes |
| `structure.json` | Block structure and mappings to docx paragraphs |
| `styles.json` | Formatting information per block |
| `manifest.json` | Metadata and version info |
| `assets/` | Images and embedded files |

## Get Started

See the [Getting Started](getting-started.md) guide for installation and usage instructions.
```

#### 2. Getting Started Guide
**File**: `website/docs/getting-started.md`

```markdown
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
```

#### 3. Format Specification
**File**: `website/docs/format-specification.md`

```markdown
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
```

### Success Criteria:

#### Automated Verification:
- [x] All markdown files exist: `ls website/docs/*.md`
- [x] No broken internal links: `mkdocs build --strict` (in Phase 4)

#### Manual Verification:
- [ ] Content accurately reflects the PRD
- [ ] Markdown renders correctly

---

## Phase 3: GitHub Actions Workflow

### Overview
Create the GitHub Actions workflow for automatic deployment to GitHub Pages.

### Changes Required:

#### 1. Create Workflow File
**File**: `.github/workflows/docs.yml`

```yaml
name: Deploy Documentation

on:
  push:
    branches: ["main"]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: "pages"
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: pip install mkdocs-material

      - name: Setup Pages
        uses: actions/configure-pages@v5

      - name: Build documentation
        run: mkdocs build --strict --config-file website/mkdocs.yml

      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: 'website/site'

  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    needs: build
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

#### 2. Create Workflow Directory
```bash
mkdir -p .github/workflows
```

### Success Criteria:

#### Automated Verification:
- [x] Workflow file exists: `ls .github/workflows/docs.yml`
- [x] YAML is valid: `python -c "import yaml; yaml.safe_load(open('.github/workflows/docs.yml'))"`

#### Manual Verification:
- [ ] Workflow appears in GitHub Actions tab after push
- [ ] Workflow runs successfully on push to main

---

## Phase 4: Final Verification

### Overview
Test the complete setup locally and prepare for deployment.

### Changes Required:

#### 1. Update .gitignore
**File**: `.gitignore` (create or append)

```
# MkDocs build output
website/site/
```

#### 2. Local Testing Commands
```bash
# Install MkDocs Material locally
pip install mkdocs-material

# Serve locally for preview
cd website && mkdocs serve

# Build with strict mode to catch errors
cd website && mkdocs build --strict
```

### Success Criteria:

#### Automated Verification:
- [x] Local build succeeds: `cd website && mkdocs build --strict`
- [x] No warnings or errors in build output

#### Manual Verification:
- [ ] Local preview at http://127.0.0.1:8000 shows correct styling
- [ ] Light/dark mode toggle works
- [ ] Fonts display correctly (Inter for text, JetBrains Mono for code)
- [ ] Burnt orange accent color (#E67E22) appears on links
- [ ] Navigation works correctly
- [ ] Code blocks have copy button

---

## Post-Deployment: Enable GitHub Pages

After pushing to main, manually enable GitHub Pages:

1. Go to repository Settings > Pages
2. Under "Build and deployment", select **GitHub Actions** as source
3. The workflow will automatically deploy on next push

---

## Testing Strategy

### Local Testing:
1. Run `mkdocs serve` from `website/` directory
2. Verify all pages render correctly
3. Test light/dark mode toggle
4. Check responsive design on different screen sizes

### CI Testing:
- GitHub Actions workflow uses `mkdocs build --strict`
- This catches broken links, missing files, and configuration errors

### Manual Testing After Deployment:
1. Visit `https://jgardner04.github.io/sidedoc/`
2. Verify all pages load
3. Check fonts and colors match style guide
4. Test navigation between pages

---

## References

- Research document: `docs/research/2026-01-08-github-pages-best-practices.md`
- PRD: `docs/slidedoc-prd.md`
- [Material for MkDocs - Custom Colors](https://squidfunk.github.io/mkdocs-material/setup/changing-the-colors/)
- [Material for MkDocs - Custom Fonts](https://squidfunk.github.io/mkdocs-material/setup/changing-the-fonts/)
- [MkDocs Configuration](https://www.mkdocs.org/user-guide/configuration/)
- [GitHub Actions deploy-pages](https://github.com/actions/deploy-pages)
