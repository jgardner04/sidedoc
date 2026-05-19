# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Sidedoc is an AI-native document format that separates content from formatting. It enables efficient AI interaction with documents while preserving rich formatting for human consumption. The canonical format is a `.sidedoc/` directory containing markdown content and formatting metadata. A `.sdoc` ZIP archive is used for distribution and sharing.

**Status:** MVP complete with hyperlink, track changes, table, headers/footers, chart, PDF, and paragraph format property support (extraction, reconstruction).

## Development Philosophy

### Test-Driven Development (TDD) — MANDATORY

**All code in this project MUST be developed using Test-Driven Development.**

This is a non-negotiable requirement for all contributions, whether from human developers or AI agents.

#### TDD Workflow

1. **Red** — Write a failing test first
   - Write a test that describes the behavior you want to implement
   - Run the test and verify it fails
   - The test should fail because the feature doesn't exist yet

2. **Green** — Write minimal code to make the test pass
   - Implement only enough code to make the test pass
   - Don't worry about perfection or edge cases yet
   - Run the test and verify it passes

3. **Refactor** — Improve the code while keeping tests green
   - Clean up the implementation
   - Remove duplication
   - Improve naming and structure
   - Run tests after each change to ensure they still pass

#### TDD Rules for This Project

- **Never write production code without a failing test first**
- **Never write more production code than needed to pass the test**
- **Never commit code without passing tests**
- Tests should be:
  - Clear and readable (they serve as documentation)
  - Focused on one behavior per test
  - Independent (can run in any order)
  - Fast (no unnecessary I/O or sleeps)

#### Example TDD Workflow

```bash
# 1. Write a failing test
# Edit tests/test_extract.py to add a test for parsing headings

# 2. Run the test and see it fail
pytest tests/test_extract.py::test_extract_heading -v

# 3. Implement minimal code to pass the test
# Edit src/sidedoc/extract.py

# 4. Run the test and see it pass
pytest tests/test_extract.py::test_extract_heading -v

# 5. Refactor if needed, keeping tests green
pytest tests/test_extract.py::test_extract_heading -v

# 6. Move to next test
```

#### When Working on Features

For any new feature or bug fix:

1. **Start with a test** — Always begin by writing a test that fails
2. **Implement incrementally** — Make the test pass with minimal code
3. **Add more tests** — Cover edge cases and error conditions
4. **Refactor** — Clean up the implementation while keeping all tests passing
5. **Verify coverage** — Run `pytest --cov=sidedoc` to ensure adequate coverage

**If you're an AI agent:** Before writing any implementation code, you must first write the test. If a user asks you to implement something, your first response should be to write the failing test.

## Specifications

- [Track Changes PRD](docs/prd-track-changes.md) — CriticMarkup-based track changes support
- [Tables PRD](docs/tables-prd.md) — Complete table support (all phases implemented)
- [PRD Status](docs/prd.json) — Current feature tracking

## Architecture

Package structure:

```
src/sidedoc/
├── __init__.py
├── cli.py              # CLI entry points (click), includes validate command
├── constants.py        # Shared constants (extensions, limits, patterns)
├── extract.py          # docx → sidedoc (paragraphs, tables, images, charts, headers/footers)
├── extract_pdf.py      # pdf → sidedoc via Docling (optional, requires [pdf] extras)
├── models.py           # Block, Style, Manifest, TrackChange dataclasses
├── package.py          # Archive/directory creation helpers, block serialization
├── reconstruct.py      # sidedoc → docx; owns inline formatting, table creation, block styling, header/footer reconstruction
├── reconstruct_pdf.py  # sidedoc → pdf via WeasyPrint (optional, requires [pdf] extras)
├── store.py            # Read-only abstraction over directory/ZIP
├── sync.py             # edited content → updated docx (imports formatting from reconstruct.py)
└── utils.py            # shared utilities
```

## Key Concepts

- **Extract:** Convert a `.docx` or `.pdf` file into a Sidedoc container (`content.md` + formatting metadata). PDF extraction requires `pip install sidedoc[pdf]`.
- **Reconstruct (build):** Rebuild the original document from the Sidedoc container. Output format (`.docx` or `.pdf`) is determined from `manifest.json`'s `source_format` field.
- **Sync:** Update DOCX output after editing `content.md` while preserving original formatting. Sync is DOCX-only; PDF sync is not supported.

For durable format documentation, see [`docs/sidedoc-format.md`](docs/sidedoc-format.md).

## Feature Documentation

Detailed feature behavior belongs in project docs, not in this agent instruction file:

- [Sidedoc format](docs/sidedoc-format.md) — container files, block types, headers/footers, manifest fields.
- [Tables PRD](docs/tables-prd.md) — GFM table syntax, table metadata, styling, merged cells.
- [Chart support](docs/charts.md) — chart detection, fallback behavior, OOXML archival, reconstruction limits.
- [PDF support](docs/pdf-support.md) — optional Docling/WeasyPrint flow, limitations, dependency pitfalls.
- [Style preservation](docs/style-preservation.md) — paragraph format fields, boolean guard rules, run-level formatting.

## Agent Gotchas

- **TDD is mandatory.** Write a failing test before implementation changes.
- **Chart detection must run before image extraction.** Chart drawings contain both `c:chart` and `a:blip`; image extraction first will consume charts as regular images. See [docs/charts.md](docs/charts.md).
- **PDF dependencies are optional.** Do not import Docling, WeasyPrint, or PyMuPDF eagerly. Use lazy imports/guard helpers so base imports and non-PDF commands work without `sidedoc[pdf]`. See [docs/pdf-support.md](docs/pdf-support.md).
- **Preserve explicit `False` style values.** Use `is not None`, not truthiness, when applying boolean paragraph formatting fields. See [docs/style-preservation.md](docs/style-preservation.md).
- **Do not mutate shared DOCX style objects for per-block font overrides.** Apply font overrides to individual runs. See [docs/style-preservation.md](docs/style-preservation.md).
- **Keep table metadata consistent with GFM content.** Table dimensions, header rows, merged cells, and cell formatting must round-trip together. See [docs/tables-prd.md](docs/tables-prd.md).

## Benchmarks

Benchmarking docs and commands live in [`benchmarks/README.md`](benchmarks/README.md). Published results live in [`website/docs/benchmarks.md`](website/docs/benchmarks.md).

Common commands:

```bash
python -m benchmarks.run_benchmark --pipeline sidedoc --corpus synthetic
python -m benchmarks.run_benchmark --pipeline sidedoc --pipeline pandoc --fidelity
python -m benchmarks.generate_report benchmarks/results/benchmark-latest.json
```

## Development Commands

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=sidedoc

# Run tests excluding PDF (skips tests requiring docling/weasyprint)
pytest -m "not pdf"

# Type checking
mypy src/

# CLI commands (all implemented)
sidedoc extract document.docx                    # Extract to document.sidedoc/ directory
sidedoc extract document.docx --pack             # Extract to document.sdoc ZIP
sidedoc extract document.docx --force            # Overwrite existing output
sidedoc extract document.docx --track-changes    # Force extract track changes
sidedoc extract document.docx --no-track-changes # Accept all changes
sidedoc extract document.pdf                     # Extract PDF (requires pip install sidedoc[pdf])
sidedoc build document.sidedoc                   # Build document; auto-detects .docx or .pdf from manifest
sidedoc sync document.sidedoc                    # Sync edited content.md (directory only, DOCX source only)
sidedoc sync document.sidedoc -o out.docx        # Sync and build updated docx
sidedoc sync document.sidedoc --author "AI"      # Sync with custom author for track changes
sidedoc validate document.sidedoc                # Validate structure, table dimensions, merged cells, styles completeness
sidedoc info document.sidedoc                    # Show metadata (accepts dir or ZIP)
sidedoc diff document.sidedoc                    # Show changes (directory only)
sidedoc pack document.sidedoc/                   # Pack directory → .sdoc ZIP
sidedoc unpack document.sdoc                     # Unpack .sdoc ZIP → .sidedoc/ directory
```

## Tech Stack

- Python 3.11+
- python-docx — Document handling
- mistune — Markdown parsing
- click — CLI framework
- pytest — Testing
- Pillow — Image validation

**Optional (`pip install sidedoc[pdf]`):**
- docling — PDF extraction (IBM; pulls in torch + transformers, ~900 MB)
- weasyprint — PDF reconstruction (markdown → HTML → PDF; requires libpango system library)
- pymupdf — PDF inspection utilities

<!-- rtk-instructions v2 -->
# RTK (Rust Token Killer) - Token-Optimized Commands

## Golden Rule

**Always prefix commands with `rtk`**. If RTK has a dedicated filter, it uses it. If not, it passes through unchanged. This means RTK is always safe to use.

**Important**: Even in command chains with `&&`, use `rtk`:
```bash
# ❌ Wrong
git add . && git commit -m "msg" && git push

# ✅ Correct
rtk git add . && rtk git commit -m "msg" && rtk git push
```

## RTK Commands by Workflow

### Build & Compile (80-90% savings)
```bash
rtk cargo build         # Cargo build output
rtk cargo check         # Cargo check output
rtk cargo clippy        # Clippy warnings grouped by file (80%)
rtk tsc                 # TypeScript errors grouped by file/code (83%)
rtk lint                # ESLint/Biome violations grouped (84%)
rtk prettier --check    # Files needing format only (70%)
rtk next build          # Next.js build with route metrics (87%)
```

### Test (90-99% savings)
```bash
rtk cargo test          # Cargo test failures only (90%)
rtk vitest run          # Vitest failures only (99.5%)
rtk playwright test     # Playwright failures only (94%)
rtk test <cmd>          # Generic test wrapper - failures only
```

### Git (59-80% savings)
```bash
rtk git status          # Compact status
rtk git log             # Compact log (works with all git flags)
rtk git diff            # Compact diff (80%)
rtk git show            # Compact show (80%)
rtk git add             # Ultra-compact confirmations (59%)
rtk git commit          # Ultra-compact confirmations (59%)
rtk git push            # Ultra-compact confirmations
rtk git pull            # Ultra-compact confirmations
rtk git branch          # Compact branch list
rtk git fetch           # Compact fetch
rtk git stash           # Compact stash
rtk git worktree        # Compact worktree
```

Note: Git passthrough works for ALL subcommands, even those not explicitly listed.

### GitHub (26-87% savings)
```bash
rtk gh pr view <num>    # Compact PR view (87%)
rtk gh pr checks        # Compact PR checks (79%)
rtk gh run list         # Compact workflow runs (82%)
rtk gh issue list       # Compact issue list (80%)
rtk gh api              # Compact API responses (26%)
```

### JavaScript/TypeScript Tooling (70-90% savings)
```bash
rtk pnpm list           # Compact dependency tree (70%)
rtk pnpm outdated       # Compact outdated packages (80%)
rtk pnpm install        # Compact install output (90%)
rtk npm run <script>    # Compact npm script output
rtk npx <cmd>           # Compact npx command output
rtk prisma              # Prisma without ASCII art (88%)
```

### Files & Search (60-75% savings)
```bash
rtk ls <path>           # Tree format, compact (65%)
rtk read <file>         # Code reading with filtering (60%)
rtk grep <pattern>      # Search grouped by file (75%)
rtk find <pattern>      # Find grouped by directory (70%)
```

### Analysis & Debug (70-90% savings)
```bash
rtk err <cmd>           # Filter errors only from any command
rtk log <file>          # Deduplicated logs with counts
rtk json <file>         # JSON structure without values
rtk deps                # Dependency overview
rtk env                 # Environment variables compact
rtk summary <cmd>       # Smart summary of command output
rtk diff                # Ultra-compact diffs
```

### Infrastructure (85% savings)
```bash
rtk docker ps           # Compact container list
rtk docker images       # Compact image list
rtk docker logs <c>     # Deduplicated logs
rtk kubectl get         # Compact resource list
rtk kubectl logs        # Deduplicated pod logs
```

### Network (65-70% savings)
```bash
rtk curl <url>          # Compact HTTP responses (70%)
rtk wget <url>          # Compact download output (65%)
```

### Meta Commands
```bash
rtk gain                # View token savings statistics
rtk gain --history      # View command history with savings
rtk discover            # Analyze Claude Code sessions for missed RTK usage
rtk proxy <cmd>         # Run command without filtering (for debugging)
rtk init                # Add RTK instructions to CLAUDE.md
rtk init --global       # Add RTK to ~/.claude/CLAUDE.md
```

## Token Savings Overview

| Category | Commands | Typical Savings |
|----------|----------|-----------------|
| Tests | vitest, playwright, cargo test | 90-99% |
| Build | next, tsc, lint, prettier | 70-87% |
| Git | status, log, diff, add, commit | 59-80% |
| GitHub | gh pr, gh run, gh issue | 26-87% |
| Package Managers | pnpm, npm, npx | 70-90% |
| Files | ls, read, grep, find | 60-75% |
| Infrastructure | docker, kubectl | 85% |
| Network | curl, wget | 65-70% |

Overall average: **60-90% token reduction** on common development operations.
<!-- /rtk-instructions -->