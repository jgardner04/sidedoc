"""Tests for benchmark requirements.txt (US-002)."""

from pathlib import Path

import pytest


BENCHMARKS_DIR = Path(__file__).parent.parent


class TestBenchmarkRequirements:
    """Test that benchmark requirements.txt is properly configured."""

    def test_requirements_file_exists(self) -> None:
        """Test that requirements.txt exists in benchmarks directory."""
        requirements_path = BENCHMARKS_DIR / "requirements.txt"
        assert requirements_path.exists(), "benchmarks/requirements.txt does not exist"

    def test_required_packages_listed(self) -> None:
        """Test that all required packages are listed."""
        requirements_path = BENCHMARKS_DIR / "requirements.txt"
        content = requirements_path.read_text()

        required_packages = [
            "pytest",
            "click",
            "python-docx",
            "tiktoken",
            "anthropic",
            "azure-ai-formrecognizer",
            "pypandoc",
            "pdf2image",
            "imagehash",
            "Pillow",
        ]

        for package in required_packages:
            # Check for package name (case-insensitive for some packages)
            package_lower = package.lower()
            content_lower = content.lower()
            assert package_lower in content_lower, f"Package {package} not found in requirements.txt"

    def test_versions_are_pinned(self) -> None:
        """Test that package versions are pinned for reproducibility."""
        requirements_path = BENCHMARKS_DIR / "requirements.txt"
        lines = requirements_path.read_text().strip().split("\n")

        for line in lines:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith("#"):
                continue

            # Check that version is pinned with == or >=
            assert "==" in line or ">=" in line, (
                f"Package {line} does not have a pinned version (use == or >=)"
            )
