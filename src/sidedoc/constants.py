"""Constants used throughout the sidedoc package.

This module centralizes magic numbers and configuration values for better maintainability.
"""

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
