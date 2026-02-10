"""Constants used throughout the sidedoc package.

This module centralizes magic numbers and configuration values for better maintainability.
"""

from docx.enum.text import WD_ALIGN_PARAGRAPH

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
    "center": (True, True),   # :---: starts and ends with :
    "right": (False, True),   # ---: ends with : only
    "left": (False, False),   # --- (default)
}

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
