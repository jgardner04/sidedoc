---
date: 2026-01-08T18:28:06Z
researcher: Claude Code
git_commit: 19199c226c93bcae6c381ce891a44beb83114079
branch: main
repository: sidedoc
topic: "GitHub Pages Best Practices for Sidedoc Documentation Site"
tags: [research, github-pages, github-actions, mkdocs, documentation]
status: complete
last_updated: 2026-01-08
last_updated_by: Claude Code
---

# Research: GitHub Pages Best Practices for Sidedoc Documentation Site

**Date**: 2026-01-08T18:28:06Z
**Researcher**: Claude Code
**Git Commit**: 19199c226c93bcae6c381ce891a44beb83114079
**Branch**: main
**Repository**: sidedoc

## Research Question

What are the best practices for setting up a GitHub Pages informational site for the Sidedoc project with auto-updating via GitHub Actions workflows?

## Summary

For the Sidedoc Python CLI project, **MkDocs with Material theme** is the recommended static site generator, deployed via **GitHub Actions** to GitHub Pages. This combination provides:

- Native Python tooling (fits the project's Python ecosystem)
- Automatic CLI documentation via `mkdocs-click` plugin
- Beautiful, modern documentation with zero CSS knowledge
- Simple 10-minute setup with GitHub Actions
- Proven track record with similar Python CLI tools (FastAPI, Textual, pipx)

The recommended approach uses GitHub's official deployment actions (`actions/deploy-pages`, `actions/configure-pages`, `actions/upload-pages-artifact`) with proper permissions, concurrency controls, and caching.

---

## Detailed Findings

### 1. Static Site Generator Recommendation

#### Primary Choice: MkDocs with Material Theme

**Why MkDocs Material for Sidedoc:**

| Criteria | Rating | Notes |
|----------|--------|-------|
| Setup Ease | Excellent | 10-minute GitHub Actions config |
| Markdown Support | Native | Pure Markdown, no special markup |
| Python Integration | Excellent | mkdocstrings for autodoc, mkdocs-click for CLI docs |
| Theme Quality | Best-in-class | Used by 50,000+ orgs including FastAPI, Pydantic |
| Build Speed | Fast | Live preview with auto-reload |
| Community | Active | Large plugin ecosystem (200+) |

**Key Plugins for Sidedoc:**

- `mkdocs-material` - Modern, responsive documentation theme
- `mkdocstrings[python]` - Autodoc from Python docstrings
- `mkdocs-click` - Automatic documentation for Click CLI commands (perfect for sidedoc's click-based CLI)

**Future Consideration:** Material for MkDocs is transitioning to **Zensical** (4-5x faster builds). Current `mkdocs.yml` files will be compatible, providing a clear migration path when Zensical matures in mid-2026.

#### Alternative: Sphinx

Choose Sphinx only if you need:
- PDF/ePub output in addition to HTML
- Complex cross-referencing across thousands of pages
- Integration with scientific Python ecosystem

Trade-offs: More complex setup, steeper learning curve (reStructuredText), slower builds.

#### Not Recommended for Sidedoc:

- **Jekyll**: Not Python-focused, declining popularity, slow builds
- **Hugo**: No Python autodoc, Go-based
- **Docusaurus**: Adds Node.js complexity for a Python project

---

### 2. GitHub Pages Configuration

#### Publishing Approach

**Recommended: GitHub Actions workflow** (modern approach with maximum flexibility)

Advantages over branch-based publishing:
- Any static site generator supported
- Build caching
- Custom build steps
- Better security (no committed build artifacts)

#### Directory Structure

```
sidedoc/
├── docs/
│   ├── index.md              # Homepage
│   ├── getting-started.md    # Quick start guide
│   ├── cli-reference.md      # CLI command reference
│   ├── format-specification.md # .sidedoc format details
│   ├── assets/               # Images, diagrams
│   └── stylesheets/          # Custom CSS (optional)
├── mkdocs.yml                # MkDocs configuration
├── .github/
│   └── workflows/
│       └── docs.yml          # GitHub Actions workflow
└── src/sidedoc/              # Python source code
```

#### SEO Best Practices

1. **Install plugins:**
   - `mkdocs-material` includes built-in SEO features
   - Social card generation for sharing

2. **Configure metadata in `mkdocs.yml`:**
   ```yaml
   site_name: Sidedoc
   site_description: AI-native document format that separates content from formatting
   site_author: Jonathan Gardner
   site_url: https://jgardner04.github.io/sidedoc/
   ```

3. **Add Open Graph/social sharing metadata** (automatic with Material theme)

---

### 3. GitHub Actions Workflow

#### Recommended Workflow Configuration

**File: `.github/workflows/docs.yml`**

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
        run: |
          pip install mkdocs-material mkdocstrings[python] mkdocs-click

      - name: Setup Pages
        uses: actions/configure-pages@v5

      - name: Build documentation
        run: mkdocs build --strict

      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: 'site'

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

#### Key Configuration Elements

1. **Permissions** (required):
   - `contents: read` - checkout repository
   - `pages: write` - deploy to Pages
   - `id-token: write` - verify deployment source via OIDC

2. **Concurrency**:
   - `group: "pages"` - ensures only one deployment at a time
   - `cancel-in-progress: false` - allows production deployments to complete

3. **Triggers**:
   - `push: branches: ["main"]` - auto-deploy on main branch updates
   - `workflow_dispatch` - manual deployment option

4. **Caching**:
   - `actions/setup-python@v5` with `cache: 'pip'` - caches pip dependencies
   - Can reduce build times by up to 80%

---

### 4. MkDocs Configuration

**File: `mkdocs.yml`**

```yaml
site_name: Sidedoc
site_description: AI-native document format that separates content from formatting
site_author: Jonathan Gardner
site_url: https://jgardner04.github.io/sidedoc/
repo_url: https://github.com/jgardner04/sidedoc
repo_name: jgardner04/sidedoc

theme:
  name: material
  palette:
    - scheme: default
      primary: indigo
      accent: indigo
      toggle:
        icon: material/brightness-7
        name: Switch to dark mode
    - scheme: slate
      primary: indigo
      accent: indigo
      toggle:
        icon: material/brightness-4
        name: Switch to light mode
  features:
    - navigation.tabs
    - navigation.sections
    - navigation.expand
    - navigation.top
    - search.suggest
    - search.highlight
    - content.tabs.link
    - content.code.annotation
    - content.code.copy
  icon:
    repo: fontawesome/brands/github

plugins:
  - search
  - mkdocstrings:
      handlers:
        python:
          options:
            docstring_style: google
            show_source: true
            show_root_heading: true
  # Uncomment when CLI is implemented:
  # - mkdocs-click:
  #     command: sidedoc.cli:cli

markdown_extensions:
  - pymdownx.highlight:
      anchor_linenums: true
  - pymdownx.inlinehilite
  - pymdownx.snippets
  - pymdownx.superfences
  - admonition
  - pymdownx.details
  - pymdownx.tabbed:
      alternate_style: true
  - tables
  - attr_list
  - md_in_html

nav:
  - Home: index.md
  - Getting Started: getting-started.md
  - User Guide:
    - CLI Reference: cli-reference.md
    - Format Specification: format-specification.md
  - API Reference: api-reference.md
  - Contributing: contributing.md
```

---

### 5. Repository Setup Checklist

#### Enable GitHub Pages with Actions

1. Go to repository Settings > Pages
2. Under "Build and deployment", select "GitHub Actions" as source
3. No branch selection needed (workflow handles this)

#### Initial Documentation Files

Create these files in `docs/`:

1. **`index.md`** - Homepage with project overview
2. **`getting-started.md`** - Installation and quick start
3. **`cli-reference.md`** - CLI command documentation
4. **`format-specification.md`** - .sidedoc format details (from PRD)
5. **`api-reference.md`** - Python API documentation (generated via mkdocstrings)

#### Optional: Custom Domain

If using a custom domain:

1. Create `CNAME` file in `docs/` directory with domain name
2. Configure DNS:
   - For apex domain: A records to GitHub's IPs
   - For subdomain: CNAME to `jgardner04.github.io`
3. Enable "Enforce HTTPS" in repository settings

---

### 6. Performance Optimization

1. **Git LFS for binaries** (if adding images):
   ```gitattributes
   *.png filter=lfs diff=lfs merge=lfs -text
   *.jpg filter=lfs diff=lfs merge=lfs -text
   *.gif filter=lfs diff=lfs merge=lfs -text
   ```

2. **Keep repository under 1GB** for optimal performance

3. **Use cache in GitHub Actions** (already included in recommended workflow)

4. **Strict mode builds**: `mkdocs build --strict` catches errors early

---

## Code References

- `docs/slidedoc-prd.md` - Product requirements document (source for format specification)
- `README.md` - Current project README
- `CLAUDE.md` - Development guidance

---

## Architecture Documentation

**Current State:**
- Repository has basic documentation in `docs/slidedoc-prd.md`
- No existing GitHub Pages setup
- No GitHub Actions workflows

**Proposed Architecture:**
```
GitHub Repository
    │
    ├── Push to main branch
    │       │
    │       ▼
    │   GitHub Actions (docs.yml)
    │       │
    │       ├── Setup Python 3.11
    │       ├── Install MkDocs Material + plugins
    │       ├── Build documentation (mkdocs build)
    │       └── Deploy to GitHub Pages
    │               │
    │               ▼
    └── https://jgardner04.github.io/sidedoc/
```

---

## Related Research

N/A - This is the first research document for the project.

---

## Open Questions

1. **Custom domain**: Should Sidedoc use `sidedoc.io` or similar instead of `jgardner04.github.io/sidedoc`?

2. **Versioned documentation**: When Sidedoc reaches v1.0, should documentation be versioned (requires `mike` plugin)?

3. **API documentation timing**: When should mkdocstrings be configured? (Recommend: when Python package structure is in place)

---

## Implementation Next Steps

1. Create `mkdocs.yml` in repository root
2. Create initial documentation files in `docs/`
3. Create `.github/workflows/docs.yml`
4. Enable GitHub Pages with Actions source in repository settings
5. Push to main branch to trigger first deployment
6. Verify site at `https://jgardner04.github.io/sidedoc/`

---

## Sources

- [GitHub Pages Documentation](https://docs.github.com/en/pages)
- [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)
- [mkdocstrings GitHub Repository](https://github.com/mkdocstrings/mkdocstrings)
- [mkdocs-click Plugin](https://github.com/mkdocs/mkdocs-click)
- [GitHub Actions deploy-pages](https://github.com/actions/deploy-pages)
- [GitHub Actions configure-pages](https://github.com/actions/configure-pages)
- [GitHub Actions cache](https://github.com/actions/cache)
- [Deploying a Static Site with GitHub Pages Best Practices Guide](https://www.theprotec.com/blog/2025/deploying-a-static-site-with-github-pages-best-practices-guide/)
- [Managing a custom domain for GitHub Pages](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site)
- [Securing your GitHub Pages site with HTTPS](https://docs.github.com/en/pages/getting-started-with-github-pages/securing-your-github-pages-site-with-https)
- [Python Documentation: MkDocs vs Sphinx](https://www.pythonsnacks.com/p/python-documentation-generator)
- [Hugo vs Jekyll 2025](https://gethugothemes.com/hugo-vs-jekyll)
