"""Tests for benchmark executor (US-022 to US-023)."""

import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ── Shared mock scores for fidelity tests ────────────────────────────

_MOCK_FIDELITY_SCORES = {
    "structure": 100.0,
    "formatting": 95.0,
    "tables": 90.0,
    "hyperlinks": 85.0,
    "track_changes": 80.0,
    "visual": None,
    "total": 90.0,
}


@pytest.fixture()
def fidelity_executor():
    """Yield a BenchmarkExecutor with mocked pipeline and fidelity scorer.

    Patches get_pipeline and FidelityScorer so tests can run without
    real documents or scoring infrastructure.
    """
    from benchmarks.benchmark_executor import BenchmarkExecutor

    with (
        patch("benchmarks.benchmark_executor.get_pipeline") as mock_get_pipeline,
        patch("benchmarks.benchmark_executor.FidelityScorer") as mock_scorer_cls,
    ):
        mock_pipe = MagicMock()
        mock_pipe.extract_content.return_value = "extracted content"
        mock_pipe.rebuild_document.return_value = MagicMock(
            error=None, output_path=Path("/tmp/out.docx")
        )
        mock_get_pipeline.return_value = mock_pipe

        mock_scorer = MagicMock()
        mock_scorer.score_total.return_value = dict(_MOCK_FIDELITY_SCORES)
        mock_scorer_cls.return_value = mock_scorer

        executor = BenchmarkExecutor(
            pipelines=["sidedoc", "pandoc", "raw_docx", "ooxml", "docint"],
            tasks=["summarize"],
            corpus="synthetic",
        )

        yield executor


@pytest.fixture()
def mock_executor():
    """Yield a BenchmarkExecutor with mocked pipeline and task.

    Patches get_pipeline and get_task so tests can run without
    real documents or API calls.
    """
    from benchmarks.benchmark_executor import BenchmarkExecutor

    with (
        patch("benchmarks.benchmark_executor.get_pipeline") as mock_get_pipeline,
        patch("benchmarks.benchmark_executor.get_task") as mock_get_task,
    ):
        mock_pipe = MagicMock()
        mock_pipe.extract_content.return_value = "content"
        mock_get_pipeline.return_value = mock_pipe

        mock_t = MagicMock()
        mock_t.execute.return_value = MagicMock(
            prompt_tokens=100,
            completion_tokens=50,
            error=None,
        )
        mock_get_task.return_value = mock_t

        yield BenchmarkExecutor(
            pipelines=["sidedoc"],
            tasks=["summarize"],
            corpus="synthetic",
        )


class TestBenchmarkExecutor:
    """Test the benchmark executor (US-022)."""

    def test_module_exists(self, benchmarks_dir: Path) -> None:
        """Test that benchmark_executor.py exists."""
        module_path = benchmarks_dir / "benchmark_executor.py"
        assert module_path.exists(), "benchmarks/benchmark_executor.py does not exist"

    def test_executor_is_importable(self) -> None:
        """Test that BenchmarkExecutor can be imported."""
        from benchmarks.benchmark_executor import BenchmarkExecutor

        assert BenchmarkExecutor is not None

    def test_executor_can_be_instantiated(self) -> None:
        """Test that BenchmarkExecutor can be instantiated."""
        from benchmarks.benchmark_executor import BenchmarkExecutor

        executor = BenchmarkExecutor(
            pipelines=["sidedoc"],
            tasks=["summarize"],
            corpus="synthetic",
        )
        assert executor is not None

    def test_executor_has_run_method(self) -> None:
        """Test that BenchmarkExecutor has run method."""
        from benchmarks.benchmark_executor import BenchmarkExecutor

        executor = BenchmarkExecutor(
            pipelines=["sidedoc"],
            tasks=["summarize"],
            corpus="synthetic",
        )
        assert hasattr(executor, "run")
        assert callable(executor.run)

    def test_run_returns_dict(self, mock_executor) -> None:
        """Test that run returns a dict with results."""
        results = mock_executor.run()
        assert isinstance(results, dict)

    def test_results_has_metadata(self, mock_executor) -> None:
        """Test that results include metadata section."""
        results = mock_executor.run()

        assert "metadata" in results
        assert "timestamp" in results["metadata"]
        assert "pipelines" in results["metadata"]
        assert "tasks" in results["metadata"]
        assert "documents" in results["metadata"]

    def test_results_has_results_array(self, mock_executor) -> None:
        """Test that results include results array."""
        results = mock_executor.run()

        assert "results" in results
        assert isinstance(results["results"], list)

    def test_results_entry_has_required_fields(self, mock_executor) -> None:
        """Test that each result entry has required fields."""
        results = mock_executor.run()

        # Check first result entry
        if results["results"]:
            entry = results["results"][0]
            assert "pipeline" in entry
            assert "task" in entry
            assert "document" in entry
            assert "metrics" in entry

    def test_executor_handles_errors_gracefully(self) -> None:
        """Test that executor handles errors without stopping."""
        from benchmarks.benchmark_executor import BenchmarkExecutor

        with (
            patch("benchmarks.benchmark_executor.get_pipeline") as mock_pipeline,
            patch("benchmarks.benchmark_executor.get_task") as mock_task,
        ):
            mock_pipe = MagicMock()
            mock_pipe.extract_content.side_effect = Exception("Pipeline error")
            mock_pipeline.return_value = mock_pipe

            mock_t = MagicMock()
            mock_task.return_value = mock_t

            executor = BenchmarkExecutor(
                pipelines=["sidedoc"],
                tasks=["summarize"],
                corpus="synthetic",
            )

            # Should not raise, even with pipeline errors
            results = executor.run()
            assert isinstance(results, dict)

    def test_task_error_truncated_to_150_chars(self) -> None:
        """Test that task_result.error is truncated to 150 characters."""
        from benchmarks.benchmark_executor import BenchmarkExecutor

        long_error = "x" * 300

        with (
            patch("benchmarks.benchmark_executor.get_pipeline") as mock_pipeline,
            patch("benchmarks.benchmark_executor.get_task") as mock_task,
        ):
            mock_pipe = MagicMock()
            mock_pipe.extract_content.return_value = "content"
            mock_pipeline.return_value = mock_pipe

            mock_t = MagicMock()
            mock_t.execute.return_value = MagicMock(
                prompt_tokens=100,
                completion_tokens=50,
                error=long_error,
            )
            mock_task.return_value = mock_t

            executor = BenchmarkExecutor(
                pipelines=["sidedoc"],
                tasks=["summarize"],
                corpus="synthetic",
            )
            results = executor.run()

            assert results["results"], "Expected non-empty results"
            error = results["results"][0]["metrics"]["error"]
            assert len(error) == 150


class TestResultsJsonOutput:
    """Test the results JSON output (US-023)."""

    def test_results_can_be_serialized_to_json(self, mock_executor) -> None:
        """Test that results can be serialized to JSON."""
        results = mock_executor.run()

        # Should serialize without error
        json_str = json.dumps(results, indent=2)
        assert json_str is not None

    def test_results_can_be_written_to_file(self, mock_executor) -> None:
        """Test that results can be written to a file."""
        results = mock_executor.run()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(results, f, indent=2)
            temp_path = Path(f.name)

        # Verify file was written and can be read back
        with open(temp_path) as f:
            loaded = json.load(f)
            assert loaded == results

        # Cleanup
        temp_path.unlink()

    def test_timestamp_is_valid_format(self, mock_executor) -> None:
        """Test that timestamp in metadata is a valid format."""
        results = mock_executor.run()

        timestamp = results["metadata"]["timestamp"]
        # Should be able to parse as ISO format
        parsed = datetime.fromisoformat(timestamp)
        assert parsed is not None


class TestFidelityExecution:
    """Test fidelity scoring integration in BenchmarkExecutor."""

    def test_run_fidelity_returns_list(self, fidelity_executor) -> None:
        """Test that run_fidelity returns a list of dicts."""
        results = fidelity_executor.run_fidelity()
        assert isinstance(results, list)

    def test_run_fidelity_skips_non_rebuild_pipelines(self, fidelity_executor) -> None:
        """Test that raw_docx and ooxml do not appear in fidelity results."""
        results = fidelity_executor.run_fidelity()

        pipelines_in_results = {r["pipeline"] for r in results}
        assert "raw_docx" not in pipelines_in_results
        assert "ooxml" not in pipelines_in_results
        assert "docint" not in pipelines_in_results

    def test_fidelity_entry_has_correct_structure(self, fidelity_executor) -> None:
        """Test that each fidelity entry has pipeline, document, scores, error keys."""
        results = fidelity_executor.run_fidelity()

        if results:
            entry = results[0]
            assert "pipeline" in entry
            assert "document" in entry
            assert "scores" in entry
            assert "error" in entry

    def test_fidelity_scores_have_dimension_keys(self, fidelity_executor) -> None:
        """Test that scores have structure, formatting, tables, hyperlinks, track_changes, total."""
        results = fidelity_executor.run_fidelity()

        if results:
            scores = results[0]["scores"]
            assert "structure" in scores
            assert "formatting" in scores
            assert "tables" in scores
            assert "hyperlinks" in scores
            assert "track_changes" in scores
            assert "total" in scores

    def test_fidelity_scores_pass_through_values(self, fidelity_executor) -> None:
        """Test that score values from scorer flow through to results correctly."""
        results = fidelity_executor.run_fidelity()

        if results:
            scores = results[0]["scores"]
            assert scores["structure"] == 100.0
            assert scores["formatting"] == 95.0
            assert scores["tables"] == 90.0
            assert scores["hyperlinks"] == 85.0
            assert scores["track_changes"] == 80.0
            assert scores["total"] == 90.0

    def test_run_with_fidelity_includes_fidelity_results(self) -> None:
        """Test that run(include_fidelity=True) includes fidelity_results key."""
        from benchmarks.benchmark_executor import BenchmarkExecutor

        with (
            patch("benchmarks.benchmark_executor.get_pipeline") as mock_get_pipeline,
            patch("benchmarks.benchmark_executor.get_task") as mock_task,
            patch("benchmarks.benchmark_executor.FidelityScorer") as mock_scorer_cls,
        ):
            mock_pipe = MagicMock()
            mock_pipe.extract_content.return_value = "content"
            mock_pipe.rebuild_document.return_value = MagicMock(
                error=None, output_path=Path("/tmp/out.docx")
            )
            mock_get_pipeline.return_value = mock_pipe

            mock_t = MagicMock()
            mock_t.execute.return_value = MagicMock(
                prompt_tokens=100,
                completion_tokens=50,
                error=None,
            )
            mock_task.return_value = mock_t

            mock_scorer = MagicMock()
            mock_scorer.score_total.return_value = dict(_MOCK_FIDELITY_SCORES)
            mock_scorer_cls.return_value = mock_scorer

            executor = BenchmarkExecutor(
                pipelines=["sidedoc"],
                tasks=["summarize"],
                corpus="synthetic",
            )
            results = executor.run(include_fidelity=True)

            assert "fidelity_results" in results

    def test_run_without_fidelity_excludes_fidelity_results(self, mock_executor) -> None:
        """Test that run() default does NOT include fidelity_results key."""
        results = mock_executor.run()
        assert "fidelity_results" not in results
