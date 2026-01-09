"""Pytest configuration and shared fixtures."""

import pytest
from pathlib import Path


@pytest.fixture
def fixtures_dir():
    """Return the path to the fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_docx_path(fixtures_dir):
    """Return the path to a sample .docx file for testing."""
    return fixtures_dir / "simple_document.docx"
