"""Constants used throughout the sidedoc package.

This module centralizes magic numbers and configuration values for better maintainability.
"""

from docx.enum.text import WD_ALIGN_PARAGRAPH

# =============================================================================
# XML Namespace Constants
# =============================================================================

# Word processing ML namespace (used in extract.py and reconstruct.py)
WORDPROCESSINGML_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

# XML namespace for preserving whitespace (used in reconstruct.py and sync.py)
XML_SPACE_NS = "{http://www.w3.org/XML/1998/namespace}space"

# Hash display length for CLI output
# Used when displaying abbreviated hash values in info command
HASH_DISPLAY_LENGTH = 16

# Content preview length for diff command
# Maximum characters to show when displaying block content in diff output
CONTENT_PREVIEW_LENGTH = 50

# Default image width when reconstructing documents
# Width in inches for images added to Word documents
DEFAULT_IMAGE_WIDTH_INCHES = 3.0

# File read chunk size for hash computation
# Buffer size in bytes for reading files in chunks when computing hashes
FILE_READ_CHUNK_SIZE = 4096

# Maximum image size (10MB)
# Prevents memory issues and potential attacks from extremely large images
MAX_IMAGE_SIZE = 10 * 1024 * 1024

# Maximum individual asset size (50MB)
# Used to prevent ZIP bomb attacks when extracting sidedoc archives
MAX_ASSET_SIZE = 50 * 1024 * 1024

# Similarity threshold for block matching (0.0 to 1.0)
# Blocks at the same position must have at least this similarity to be considered edits
# Below this threshold, they are treated as delete + add operations
SIMILARITY_THRESHOLD = 0.7

# =============================================================================
# Alignment Constants
# =============================================================================

# Default alignment when none specified
DEFAULT_ALIGNMENT = "left"

# Alignment string to WD_ALIGN_PARAGRAPH enum mapping
# Used when applying alignment from styles to paragraphs
ALIGNMENT_STRING_TO_ENUM = {
    "left": WD_ALIGN_PARAGRAPH.LEFT,
    "center": WD_ALIGN_PARAGRAPH.CENTER,
    "right": WD_ALIGN_PARAGRAPH.RIGHT,
    "justify": WD_ALIGN_PARAGRAPH.JUSTIFY,
}

# WD_ALIGN_PARAGRAPH numeric value to string mapping
# Used when extracting alignment from paragraphs (enum value → string for JSON)
ALIGNMENT_NUMERIC_TO_STRING = {
    0: "left",      # WD_ALIGN_PARAGRAPH.LEFT
    1: "center",    # WD_ALIGN_PARAGRAPH.CENTER
    2: "right",     # WD_ALIGN_PARAGRAPH.RIGHT
    3: "justify",   # WD_ALIGN_PARAGRAPH.JUSTIFY
}

# Maximum table dimensions to prevent memory exhaustion from malicious input
MAX_TABLE_ROWS = 1000
MAX_TABLE_COLS = 100
MAX_TABLE_LINES = 2000

# EMU (English Metric Units) conversion constant
# 1 inch = 914400 EMUs in Office Open XML
EMUS_PER_INCH = 914400

# GFM separator indicators for alignment
# Used when converting alignment to GFM table separator row
GFM_ALIGNMENT_TO_SEPARATOR = {
    "left": "---",
    "center": ":---:",
    "right": "---:",
}

# GFM separator patterns for detecting alignment
# (starts_with_colon, ends_with_colon) → alignment
GFM_SEPARATOR_PATTERNS = {
    (False, False): "left",     # ---
    (True, False): "left",      # :--- (explicit left)
    (False, True): "right",     # ---:
    (True, True): "center",     # :---:
}

# =============================================================================
# Cell Formatting Constants
# =============================================================================

# Valid border styles for cell borders (whitelist for security)
VALID_BORDER_STYLES = frozenset({
    'single', 'double', 'dashed', 'dotted', 'thick',
    'hairline', 'dashSmallGap', 'dotDash', 'dotDotDash',
    'triple', 'thinThickSmallGap', 'thickThinSmallGap',
    'thinThickThinSmallGap', 'thinThickMediumGap',
    'thickThinMediumGap', 'thinThickThinMediumGap',
    'thinThickLargeGap', 'thickThinLargeGap',
    'thinThickThinLargeGap', 'wave', 'doubleWave',
    'dashDotStroked', 'threeDEmboss', 'threeDEngrave',
    'outset', 'inset', 'nil', 'none',
})

# Valid pattern fill types from OOXML (w:val on w:shd element)
# 'clear', 'nil', and 'solid' are treated as "no pattern" — not included here
VALID_PATTERN_FILLS = frozenset({
    'horzStripe', 'vertStripe', 'diagStripe', 'reverseDiagStripe',
    'horzCross', 'diagCross',
    'thinHorzStripe', 'thinVertStripe', 'thinDiagStripe', 'thinReverseDiagStripe',
    'thinHorzCross', 'thinDiagCross',
    'pct5', 'pct10', 'pct12', 'pct15', 'pct20', 'pct25',
    'pct30', 'pct35', 'pct37', 'pct40', 'pct45', 'pct50',
    'pct55', 'pct60', 'pct62', 'pct65', 'pct70', 'pct75',
    'pct80', 'pct85', 'pct87', 'pct90', 'pct95',
})

# Regex for validating hex color values
HEX_COLOR_PATTERN = r'^[0-9A-Fa-f]{6}$'

# Maximum border width in eighths of a point (12pt)
MAX_BORDER_WIDTH = 96

# =============================================================================
# OOXML Footnote/Endnote Constants
# =============================================================================

# Relationship types for footnotes and endnotes parts
FOOTNOTES_RT = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/footnotes"
)
ENDNOTES_RT = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/endnotes"
)

# Content types for footnotes and endnotes parts
FOOTNOTES_CT = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.footnotes+xml"
)
ENDNOTES_CT = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.endnotes+xml"
)

# =============================================================================
# CriticMarkup Patterns
# =============================================================================
# These regex patterns parse CriticMarkup syntax for track changes.
# See: http://criticmarkup.com/spec.php
#
# Syntax:
#   - Insertion: {++inserted text++}
#   - Deletion:  {--deleted text--}
#   - Substitution: {~~old text~>new text~~}

# Matches {++text++} - captures the inserted text (group 1)
# Uses non-greedy matching to handle multiple insertions in one line
INSERTION_PATTERN = r"\{\+\+(.+?)\+\+\}"

# Matches {--text--} - captures the deleted text (group 1)
# Uses non-greedy matching to handle multiple deletions in one line
DELETION_PATTERN = r"\{--(.+?)--\}"

# Matches {~~old~>new~~} - captures old text (group 1) and new text (group 2)
# Uses non-greedy matching for both parts
SUBSTITUTION_PATTERN = r"\{~~(.+?)~>(.+?)~~\}"

# =============================================================================
# Sidedoc Format Constants
# =============================================================================

# File extensions
SIDEDOC_DIR_EXTENSION = ".sidedoc"
SIDEDOC_ZIP_EXTENSION = ".sdoc"

# File classification for sidedoc containers
CORE_FILES = ["content.md", "styles.json"]           # Required for build
TRACKING_FILES = ["structure.json", "manifest.json"]  # Required for sync/diff
ALL_FILES = CORE_FILES + TRACKING_FILES               # Required in .sdoc ZIP
