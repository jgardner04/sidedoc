"""Utility functions for sidedoc."""

import hashlib
from datetime import datetime, timezone
from pathlib import Path


def compute_file_hash(file_path: str) -> str:
    """Compute SHA256 hash of a file.

    Args:
        file_path: Path to file

    Returns:
        Hex digest of file hash
    """
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
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
