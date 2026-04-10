# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Chart support:** Detect charts during extraction, extract cached images to `assets/`, and parse chart data (type, series, labels, categories) into structured metadata
- **SmartArt support:** Detect SmartArt diagrams, extract cached images, and parse node text into metadata
- **Chart/SmartArt in content.md:** `![Chart: title](assets/chart1.png)` and `![SmartArt: type](assets/smartart1.png)` notation
- **Full-fidelity chart round-trip:** Archive chart XML parts, embedded spreadsheets, relationship IDs, and drawing XML to `assets/chart_parts/` during extraction; reconstruct functional charts (not just raster images) during `sidedoc build` ([JON-108](https://linear.app/jonathangardner/issue/JON-108/chart-full-fidelity-round-trip-archive-reconstruct))

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
