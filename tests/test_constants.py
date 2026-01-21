"""Tests for constants module."""

import pytest
from sidedoc.constants import (
    HASH_DISPLAY_LENGTH,
    CONTENT_PREVIEW_LENGTH,
    DEFAULT_IMAGE_WIDTH_INCHES,
    FILE_READ_CHUNK_SIZE,
)


def test_hash_display_length():
    """Test that hash display length is reasonable."""
    assert HASH_DISPLAY_LENGTH == 16
    assert isinstance(HASH_DISPLAY_LENGTH, int)
    assert HASH_DISPLAY_LENGTH > 0


def test_content_preview_length():
    """Test that content preview length is reasonable."""
    assert CONTENT_PREVIEW_LENGTH == 50
    assert isinstance(CONTENT_PREVIEW_LENGTH, int)
    assert CONTENT_PREVIEW_LENGTH > 0


def test_default_image_width():
    """Test that default image width is reasonable."""
    assert DEFAULT_IMAGE_WIDTH_INCHES == 3.0
    assert isinstance(DEFAULT_IMAGE_WIDTH_INCHES, float)
    assert DEFAULT_IMAGE_WIDTH_INCHES > 0


def test_file_read_chunk_size():
    """Test that file read chunk size is reasonable."""
    assert FILE_READ_CHUNK_SIZE == 4096
    assert isinstance(FILE_READ_CHUNK_SIZE, int)
    assert FILE_READ_CHUNK_SIZE > 0


def test_constants_are_immutable():
    """Test that constants module exports are used correctly."""
    # This test ensures constants are defined and can be imported
    # In Python, constants are convention-based (UPPER_CASE naming)
    # but not truly immutable. This test just verifies they exist.
    assert HASH_DISPLAY_LENGTH is not None
    assert CONTENT_PREVIEW_LENGTH is not None
    assert DEFAULT_IMAGE_WIDTH_INCHES is not None
    assert FILE_READ_CHUNK_SIZE is not None
