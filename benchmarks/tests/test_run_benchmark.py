"""Tests for benchmark runner CLI (US-021 to US-023)."""

from pathlib import Path

import pytest
from click.testing import CliRunner


BENCHMARKS_DIR = Path(__file__).parent.parent


class TestBenchmarkRunner:
    """Test the benchmark runner CLI (US-021)."""

    def test_module_exists(self) -> None:
        """Test that run_benchmark.py exists."""
        module_path = BENCHMARKS_DIR / "run_benchmark.py"
        assert module_path.exists(), "benchmarks/run_benchmark.py does not exist"

    def test_cli_is_importable(self) -> None:
        """Test that the CLI can be imported."""
        from benchmarks.run_benchmark import cli

        assert cli is not None

    def test_cli_is_click_command(self) -> None:
        """Test that cli is a Click command."""
        import click

        from benchmarks.run_benchmark import cli

        assert isinstance(cli, click.core.Command)

    def test_cli_has_pipeline_option(self) -> None:
        """Test that CLI has --pipeline option."""
        from benchmarks.run_benchmark import cli

        param_names = [p.name for p in cli.params]
        assert "pipeline" in param_names

    def test_cli_has_task_option(self) -> None:
        """Test that CLI has --task option."""
        from benchmarks.run_benchmark import cli

        param_names = [p.name for p in cli.params]
        assert "task" in param_names

    def test_cli_has_corpus_option(self) -> None:
        """Test that CLI has --corpus option."""
        from benchmarks.run_benchmark import cli

        param_names = [p.name for p in cli.params]
        assert "corpus" in param_names

    def test_cli_runs_without_error(self) -> None:
        """Test that CLI runs without error (with --dry-run if available)."""
        from benchmarks.run_benchmark import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "Usage" in result.output

    def test_cli_shows_available_pipelines(self) -> None:
        """Test that CLI help shows available pipelines."""
        from benchmarks.run_benchmark import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])

        # Help should mention pipeline options
        assert "pipeline" in result.output.lower()

    def test_cli_shows_available_tasks(self) -> None:
        """Test that CLI help shows available tasks."""
        from benchmarks.run_benchmark import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])

        # Help should mention task options
        assert "task" in result.output.lower()

    def test_cli_shows_corpus_options(self) -> None:
        """Test that CLI help shows corpus options."""
        from benchmarks.run_benchmark import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])

        # Help should mention corpus
        assert "corpus" in result.output.lower()
