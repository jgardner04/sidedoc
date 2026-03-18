# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-03-15

### Added

- **Core format:** `.sidedoc/` directory with `content.md`, `styles.json`, `structure.json`, and `manifest.json`
- **Extract:** Convert `.docx` to sidedoc with paragraph, heading, list, image, table, and hyperlink support
- **Build:** Reconstruct `.docx` from sidedoc with full formatting preservation
- **Sync:** Update `.docx` after editing `content.md` while preserving original formatting
- **Validate:** Check sidedoc integrity including table dimensions, merged cells, and styles completeness
- **Diff:** Show changes between `content.md` and last synced state
- **Pack/Unpack:** Convert between `.sidedoc/` directories and `.sdoc` ZIP archives
- **Info:** Display sidedoc metadata
- **Table support:** GFM pipe tables with merged cells, column alignment, cell formatting, and background colors
- **Track changes:** Bidirectional CriticMarkup support (`{++insert++}`, `{--delete--}`, `{~~old~>new~~}`)
- **Hyperlink support:** Inline hyperlinks preserved through extract/build/sync round-trips
- **Directory-first architecture:** `.sidedoc/` directories as canonical format, `.sdoc` ZIPs for distribution
- **SidedocStore:** Read-only abstraction over directory and ZIP formats with auto-detection
- **Benchmarking suite:** Compare sidedoc against pandoc, raw_docx, ooxml, and docint pipelines
- **Format fidelity scoring:** Measure round-trip preservation across structure, formatting, tables, hyperlinks, and track changes
- **CI/CD:** GitHub Actions for tests, mypy, and PyPI publishing via Trusted Publishers
- **Security:** Path traversal protection, input validation, and content sanitization

### Fixed

- Table metadata preservation when loading from `structure.json`
- Style remapping after sync to fix stale block IDs
- Column normalization for tables with inconsistent row widths
