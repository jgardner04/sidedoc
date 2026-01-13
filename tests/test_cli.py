"""Test CLI framework."""

import subprocess
import sys
from click.testing import CliRunner
from sidedoc.cli import main, extract, build, sync, validate, info, unpack, pack, diff


def test_cli_main_exists():
    """Test that main CLI group exists."""
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "sidedoc" in result.output.lower() or "usage" in result.output.lower()


def test_cli_version_flag():
    """Test that --version flag works."""
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_cli_help_shows_commands():
    """Test that --help shows all available commands."""
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    output = result.output.lower()

    # Check that all commands are listed
    assert "extract" in output
    assert "build" in output
    assert "sync" in output
    assert "validate" in output
    assert "info" in output
    assert "unpack" in output
    assert "pack" in output
    assert "diff" in output


def test_extract_command_exists():
    """Test that extract command exists."""
    runner = CliRunner()
    result = runner.invoke(main, ["extract", "--help"])
    assert result.exit_code == 0
    assert "extract" in result.output.lower()


def test_build_command_exists():
    """Test that build command exists."""
    runner = CliRunner()
    result = runner.invoke(main, ["build", "--help"])
    assert result.exit_code == 0
    assert "build" in result.output.lower()


def test_sync_command_exists():
    """Test that sync command exists."""
    runner = CliRunner()
    result = runner.invoke(main, ["sync", "--help"])
    assert result.exit_code == 0
    assert "sync" in result.output.lower()


def test_validate_command_exists():
    """Test that validate command exists."""
    runner = CliRunner()
    result = runner.invoke(main, ["validate", "--help"])
    assert result.exit_code == 0
    assert "validate" in result.output.lower()


def test_info_command_exists():
    """Test that info command exists."""
    runner = CliRunner()
    result = runner.invoke(main, ["info", "--help"])
    assert result.exit_code == 0
    assert "info" in result.output.lower()


def test_unpack_command_exists():
    """Test that unpack command exists."""
    runner = CliRunner()
    result = runner.invoke(main, ["unpack", "--help"])
    assert result.exit_code == 0
    assert "unpack" in result.output.lower()


def test_pack_command_exists():
    """Test that pack command exists."""
    runner = CliRunner()
    result = runner.invoke(main, ["pack", "--help"])
    assert result.exit_code == 0
    assert "pack" in result.output.lower()


def test_diff_command_exists():
    """Test that diff command exists."""
    runner = CliRunner()
    result = runner.invoke(main, ["diff", "--help"])
    assert result.exit_code == 0
    assert "diff" in result.output.lower()


def test_cli_executable_installed():
    """Test that sidedoc command is installed and executable."""
    result = subprocess.run(
        ["sidedoc", "--version"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "0.1.0" in result.stdout or "0.1.0" in result.stderr
