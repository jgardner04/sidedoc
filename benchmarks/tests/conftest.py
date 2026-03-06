"""Shared fixtures for benchmark tests."""

from pathlib import Path

import pytest

BENCHMARKS_DIR = Path(__file__).parent.parent
FIXTURES_DIR = BENCHMARKS_DIR.parent / "tests" / "fixtures"


@pytest.fixture
def benchmarks_dir() -> Path:
    return BENCHMARKS_DIR


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES_DIR


@pytest.fixture
def simple_docx() -> Path:
    path = FIXTURES_DIR / "simple.docx"
    if not path.exists():
        pytest.skip("simple.docx fixture not found")
    return path
