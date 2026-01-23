"""Tests for benchmark README documentation (US-029 to US-030)."""

from pathlib import Path

import pytest


BENCHMARKS_DIR = Path(__file__).parent.parent


class TestBenchmarkReadme:
    """Test the benchmark README (US-029)."""

    def test_readme_exists(self) -> None:
        """Test that README.md exists in benchmarks directory."""
        readme_path = BENCHMARKS_DIR / "README.md"
        assert readme_path.exists(), "benchmarks/README.md does not exist"

    def test_readme_has_overview(self) -> None:
        """Test that README has overview section."""
        readme_path = BENCHMARKS_DIR / "README.md"
        content = readme_path.read_text()

        assert "overview" in content.lower() or "# " in content

    def test_readme_has_prerequisites(self) -> None:
        """Test that README lists prerequisites."""
        readme_path = BENCHMARKS_DIR / "README.md"
        content = readme_path.read_text()

        assert "prerequisite" in content.lower() or "require" in content.lower()

    def test_readme_mentions_python(self) -> None:
        """Test that README mentions Python 3.11+."""
        readme_path = BENCHMARKS_DIR / "README.md"
        content = readme_path.read_text()

        assert "python" in content.lower()

    def test_readme_mentions_pandoc(self) -> None:
        """Test that README mentions Pandoc."""
        readme_path = BENCHMARKS_DIR / "README.md"
        content = readme_path.read_text()

        assert "pandoc" in content.lower()

    def test_readme_mentions_libreoffice(self) -> None:
        """Test that README mentions LibreOffice."""
        readme_path = BENCHMARKS_DIR / "README.md"
        content = readme_path.read_text()

        assert "libreoffice" in content.lower()

    def test_readme_has_installation(self) -> None:
        """Test that README has installation section."""
        readme_path = BENCHMARKS_DIR / "README.md"
        content = readme_path.read_text()

        assert "install" in content.lower()

    def test_readme_has_usage(self) -> None:
        """Test that README has usage section."""
        readme_path = BENCHMARKS_DIR / "README.md"
        content = readme_path.read_text()

        assert "usage" in content.lower()


class TestBenchmarkReadmeTroubleshooting:
    """Test the troubleshooting section (US-030)."""

    def test_readme_has_troubleshooting(self) -> None:
        """Test that README has troubleshooting section."""
        readme_path = BENCHMARKS_DIR / "README.md"
        content = readme_path.read_text()

        assert "troubleshoot" in content.lower()

    def test_readme_has_examples(self) -> None:
        """Test that README has examples."""
        readme_path = BENCHMARKS_DIR / "README.md"
        content = readme_path.read_text()

        assert "example" in content.lower()

    def test_readme_has_environment_variables(self) -> None:
        """Test that README documents environment variables."""
        readme_path = BENCHMARKS_DIR / "README.md"
        content = readme_path.read_text()

        assert "environment" in content.lower() or "ANTHROPIC" in content
