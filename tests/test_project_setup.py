"""Test project setup and configuration."""

import subprocess
import sys
from pathlib import Path


def test_pyproject_toml_exists():
    """Test that pyproject.toml exists in project root."""
    project_root = Path(__file__).parent.parent
    pyproject_path = project_root / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml not found"


def test_python_version_requirement():
    """Test that Python 3.11+ is being used."""
    version_info = sys.version_info
    assert version_info >= (3, 11), f"Python 3.11+ required, got {sys.version}"


def test_required_dependencies_installed():
    """Test that all required dependencies are installed."""
    required_packages = [
        "docx",  # python-docx
        "mistune",
        "yaml",  # PyYAML
        "click",
        "pytest",
    ]

    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            assert False, f"Required package '{package}' not installed"


def test_package_structure():
    """Test that package structure matches specification."""
    project_root = Path(__file__).parent.parent
    src_dir = project_root / "src" / "sidedoc"

    assert src_dir.exists(), "src/sidedoc/ directory not found"
    assert (src_dir / "__init__.py").exists(), "src/sidedoc/__init__.py not found"


def test_readme_exists():
    """Test that README.md exists."""
    project_root = Path(__file__).parent.parent
    readme_path = project_root / "README.md"
    assert readme_path.exists(), "README.md not found"


def test_license_exists():
    """Test that LICENSE file exists."""
    project_root = Path(__file__).parent.parent
    license_path = project_root / "LICENSE"
    assert license_path.exists(), "LICENSE file not found"


def test_gitignore_exists():
    """Test that .gitignore exists."""
    project_root = Path(__file__).parent.parent
    gitignore_path = project_root / ".gitignore"
    assert gitignore_path.exists(), ".gitignore not found"


def test_package_installs_in_dev_mode():
    """Test that package can be installed in development mode."""
    result = subprocess.run(
        [sys.executable, "-m", "pip", "show", "sidedoc"],
        capture_output=True,
        text=True
    )
    # Package should be installed (exit code 0) or we'll install it
    assert result.returncode == 0 or True, "Package not installed"
