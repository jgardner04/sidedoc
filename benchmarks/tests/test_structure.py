"""Tests for benchmark project structure (US-001)."""

from pathlib import Path

import pytest


# Get the benchmarks directory path
BENCHMARKS_DIR = Path(__file__).parent.parent


class TestBenchmarkStructure:
    """Test that the benchmark directory structure is correct."""

    def test_benchmarks_directory_exists(self) -> None:
        """Test that benchmarks/ directory exists."""
        assert BENCHMARKS_DIR.exists()
        assert BENCHMARKS_DIR.is_dir()

    def test_required_subdirectories_exist(self) -> None:
        """Test that all required subdirectories exist."""
        required_dirs = ["corpus", "pipelines", "tasks", "metrics", "results", "scripts"]
        for dir_name in required_dirs:
            dir_path = BENCHMARKS_DIR / dir_name
            assert dir_path.exists(), f"Directory {dir_name}/ does not exist"
            assert dir_path.is_dir(), f"{dir_name} is not a directory"

    def test_python_package_init_files_exist(self) -> None:
        """Test that __init__.py files exist for Python package structure."""
        packages = ["", "pipelines", "tasks", "metrics", "scripts", "tests"]
        for pkg in packages:
            init_path = BENCHMARKS_DIR / pkg / "__init__.py" if pkg else BENCHMARKS_DIR / "__init__.py"
            assert init_path.exists(), f"__init__.py missing in {pkg or 'benchmarks'}/"

    def test_corpus_synthetic_symlink(self) -> None:
        """Test that corpus/synthetic/ symlinks to tests/fixtures/."""
        synthetic_path = BENCHMARKS_DIR / "corpus" / "synthetic"
        assert synthetic_path.exists(), "corpus/synthetic/ does not exist"
        assert synthetic_path.is_symlink(), "corpus/synthetic/ is not a symlink"

        # Resolve the symlink and check it points to tests/fixtures/
        resolved = synthetic_path.resolve()
        tests_fixtures = (BENCHMARKS_DIR.parent / "tests" / "fixtures").resolve()
        assert resolved == tests_fixtures, (
            f"corpus/synthetic/ symlink points to {resolved}, expected {tests_fixtures}"
        )

    def test_corpus_real_directory_exists(self) -> None:
        """Test that corpus/real/ directory exists."""
        real_path = BENCHMARKS_DIR / "corpus" / "real"
        assert real_path.exists(), "corpus/real/ does not exist"
        assert real_path.is_dir(), "corpus/real/ is not a directory"

    def test_synthetic_fixtures_accessible(self) -> None:
        """Test that synthetic fixtures are accessible via the symlink."""
        synthetic_path = BENCHMARKS_DIR / "corpus" / "synthetic"
        expected_fixtures = ["simple.docx", "lists.docx", "formatted.docx", "images.docx", "complex.docx"]

        for fixture in expected_fixtures:
            fixture_path = synthetic_path / fixture
            assert fixture_path.exists(), f"Fixture {fixture} not accessible via symlink"
