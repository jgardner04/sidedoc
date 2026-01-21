"""Utility functions for sidedoc."""

import hashlib
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from sidedoc.constants import FILE_READ_CHUNK_SIZE


def compute_file_hash(file_path: str) -> str:
    """Compute SHA256 hash of a file.

    Args:
        file_path: Path to file

    Returns:
        Hex digest of file hash
    """
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read file in chunks rather than loading entire file into memory
        # Why chunks: Large docx files (potentially hundreds of MB) would cause
        # memory issues if loaded all at once. Chunked reading keeps memory usage
        # constant regardless of file size.
        # Why iter with lambda: This is a Python idiom for reading until EOF. The
        # lambda returns empty bytes (b"") when EOF is reached, which terminates
        # the iterator.
        for chunk in iter(lambda: f.read(FILE_READ_CHUNK_SIZE), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def get_iso_timestamp() -> str:
    """Get current timestamp in ISO 8601 format.

    Returns:
        ISO 8601 formatted timestamp string
    """
    return datetime.now(timezone.utc).isoformat()


def ensure_sidedoc_extension(path: str) -> str:
    """Ensure path has .sidedoc extension.

    Args:
        path: Input path

    Returns:
        Path with .sidedoc extension
    """
    p = Path(path)
    if p.suffix != ".sidedoc":
        return str(p.with_suffix(".sidedoc"))
    return path


def is_safe_path(path: str, base_dir: Path) -> bool:
    """Check if a path is safe for extraction (no path traversal).

    Args:
        path: Path to check (from ZIP archive)
        base_dir: Base directory for extraction

    Returns:
        True if path is safe, False otherwise
    """
    # Reject absolute paths first (e.g., /etc/passwd)
    # Why reject: Absolute paths could write anywhere on the filesystem, which is
    # a serious security vulnerability when extracting untrusted ZIP archives.
    if Path(path).is_absolute():
        return False

    # Resolve the path relative to base_dir and check if it's actually within base_dir
    # Why resolve: This handles path traversal attacks like "../../etc/passwd" by
    # converting to absolute paths and checking containment.
    try:
        target_path = (base_dir / path).resolve()
        base_dir_resolved = base_dir.resolve()

        # Check if target is within base directory
        # Why is_relative_to: This is the security check. If someone includes
        # "../../../etc/passwd" in a ZIP, resolve() will convert it to the real
        # path, and is_relative_to() will detect it's outside base_dir and reject it.
        # This prevents "Zip Slip" vulnerabilities.
        return target_path.is_relative_to(base_dir_resolved)
    except (ValueError, RuntimeError):
        # Path resolution failed - not safe
        # Why catch exceptions: Some paths (symlink loops, permission errors) can't
        # be resolved. Better to reject than risk a security issue.
        return False


def compute_similarity(text1: str, text2: str) -> float:
    """Compute similarity ratio between two strings.

    Uses Python's difflib.SequenceMatcher to calculate a similarity ratio
    between 0.0 (completely different) and 1.0 (identical).

    Args:
        text1: First string to compare
        text2: Second string to compare

    Returns:
        Similarity ratio as a float between 0.0 and 1.0
    """
    return SequenceMatcher(None, text1, text2).ratio()
