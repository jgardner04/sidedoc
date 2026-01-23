"""Tests for report generator CLI (US-024 to US-028)."""

import json
import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner


BENCHMARKS_DIR = Path(__file__).parent.parent


# Sample results data for testing
SAMPLE_RESULTS = {
    "metadata": {
        "timestamp": "2024-01-15T10:30:00",
        "pipelines": ["sidedoc", "pandoc"],
        "tasks": ["summarize"],
        "corpus": "synthetic",
        "documents": ["doc1.docx", "doc2.docx"],
    },
    "results": [
        {
            "pipeline": "sidedoc",
            "task": "summarize",
            "document": "doc1.docx",
            "metrics": {
                "prompt_tokens": 1000,
                "completion_tokens": 200,
                "error": None,
            },
        },
        {
            "pipeline": "pandoc",
            "task": "summarize",
            "document": "doc1.docx",
            "metrics": {
                "prompt_tokens": 2000,
                "completion_tokens": 200,
                "error": None,
            },
        },
    ],
}


class TestReportGenerator:
    """Test the report generator CLI (US-024)."""

    def test_module_exists(self) -> None:
        """Test that generate_report.py exists."""
        module_path = BENCHMARKS_DIR / "generate_report.py"
        assert module_path.exists(), "benchmarks/generate_report.py does not exist"

    def test_cli_is_importable(self) -> None:
        """Test that the CLI can be imported."""
        from benchmarks.generate_report import cli

        assert cli is not None

    def test_cli_is_click_command(self) -> None:
        """Test that cli is a Click command."""
        import click

        from benchmarks.generate_report import cli

        assert isinstance(cli, click.core.Command)

    def test_cli_takes_input_file(self) -> None:
        """Test that CLI takes input file argument."""
        from benchmarks.generate_report import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])

        assert "input" in result.output.lower() or "file" in result.output.lower()

    def test_cli_outputs_markdown(self) -> None:
        """Test that CLI outputs markdown report."""
        from benchmarks.generate_report import cli

        with tempfile.TemporaryDirectory() as tmp_dir:
            input_path = Path(tmp_dir) / "results.json"
            output_path = Path(tmp_dir) / "report.md"

            with open(input_path, "w") as f:
                json.dump(SAMPLE_RESULTS, f)

            runner = CliRunner()
            result = runner.invoke(
                cli, [str(input_path), "--output", str(output_path)]
            )

            assert result.exit_code == 0
            assert output_path.exists()


class TestReportExecutiveSummary:
    """Test the executive summary section (US-025)."""

    def test_report_has_executive_summary(self) -> None:
        """Test that report includes executive summary section."""
        from benchmarks.generate_report import generate_report

        report = generate_report(SAMPLE_RESULTS)

        assert "## Executive Summary" in report

    def test_executive_summary_has_token_reduction(self) -> None:
        """Test that executive summary shows token reduction."""
        from benchmarks.generate_report import generate_report

        report = generate_report(SAMPLE_RESULTS)

        # Should mention tokens or reduction
        assert "token" in report.lower()

    def test_executive_summary_has_fidelity_comparison(self) -> None:
        """Test that executive summary shows fidelity comparison."""
        from benchmarks.generate_report import generate_report

        report = generate_report(SAMPLE_RESULTS)

        # Should mention fidelity
        assert "fidelity" in report.lower() or "format" in report.lower()

    def test_executive_summary_has_cost_savings(self) -> None:
        """Test that executive summary shows cost savings."""
        from benchmarks.generate_report import generate_report

        report = generate_report(SAMPLE_RESULTS)

        # Should mention cost
        assert "cost" in report.lower()


class TestReportMethodology:
    """Test the methodology section (US-026)."""

    def test_report_has_methodology(self) -> None:
        """Test that report includes methodology section."""
        from benchmarks.generate_report import generate_report

        report = generate_report(SAMPLE_RESULTS)

        assert "## Methodology" in report

    def test_methodology_lists_corpus(self) -> None:
        """Test that methodology lists test corpus."""
        from benchmarks.generate_report import generate_report

        report = generate_report(SAMPLE_RESULTS)

        # Should mention corpus or documents
        assert "corpus" in report.lower() or "document" in report.lower()

    def test_methodology_lists_pipelines(self) -> None:
        """Test that methodology lists pipelines compared."""
        from benchmarks.generate_report import generate_report

        report = generate_report(SAMPLE_RESULTS)

        # Should mention pipelines
        assert "sidedoc" in report.lower() or "pipeline" in report.lower()

    def test_methodology_lists_tasks(self) -> None:
        """Test that methodology lists tasks executed."""
        from benchmarks.generate_report import generate_report

        report = generate_report(SAMPLE_RESULTS)

        # Should mention tasks
        assert "task" in report.lower() or "summarize" in report.lower()


class TestReportResultsTables:
    """Test the results tables section (US-027)."""

    def test_report_has_results_section(self) -> None:
        """Test that report includes results section."""
        from benchmarks.generate_report import generate_report

        report = generate_report(SAMPLE_RESULTS)

        assert "## Results" in report

    def test_results_has_token_efficiency_table(self) -> None:
        """Test that results include token efficiency table."""
        from benchmarks.generate_report import generate_report

        report = generate_report(SAMPLE_RESULTS)

        # Should have table with pipeline names
        assert "|" in report  # Markdown table format
        assert "token" in report.lower()

    def test_results_tables_formatted_as_markdown(self) -> None:
        """Test that tables are formatted as Markdown."""
        from benchmarks.generate_report import generate_report

        report = generate_report(SAMPLE_RESULTS)

        # Should have markdown table syntax
        assert "| " in report
        assert " |" in report


class TestReportConclusions:
    """Test the conclusions section (US-028)."""

    def test_report_has_conclusions(self) -> None:
        """Test that report includes conclusions section."""
        from benchmarks.generate_report import generate_report

        report = generate_report(SAMPLE_RESULTS)

        assert "## Conclusions" in report

    def test_conclusions_has_best_pipeline(self) -> None:
        """Test that conclusions summarize best pipeline."""
        from benchmarks.generate_report import generate_report

        report = generate_report(SAMPLE_RESULTS)

        # Should mention best or recommend
        conclusions_section = report.split("## Conclusions")[1] if "## Conclusions" in report else ""
        assert "best" in conclusions_section.lower() or "recommend" in conclusions_section.lower()

    def test_conclusions_has_recommendations(self) -> None:
        """Test that conclusions list recommendations."""
        from benchmarks.generate_report import generate_report

        report = generate_report(SAMPLE_RESULTS)

        # Should have recommendation
        assert "recommend" in report.lower() or "use case" in report.lower()
