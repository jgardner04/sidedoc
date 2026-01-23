"""Tests for benchmark executor (US-022 to US-023)."""

import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


BENCHMARKS_DIR = Path(__file__).parent.parent


class TestBenchmarkExecutor:
    """Test the benchmark executor (US-022)."""

    def test_module_exists(self) -> None:
        """Test that benchmark_executor.py exists."""
        module_path = BENCHMARKS_DIR / "benchmark_executor.py"
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

    def test_run_returns_dict(self) -> None:
        """Test that run returns a dict with results."""
        from benchmarks.benchmark_executor import BenchmarkExecutor

        # Mock pipelines and tasks to avoid actual API calls
        with patch("benchmarks.benchmark_executor.get_pipeline") as mock_pipeline:
            with patch("benchmarks.benchmark_executor.get_task") as mock_task:
                mock_pipe = MagicMock()
                mock_pipe.extract_content.return_value = "extracted content"
                mock_pipeline.return_value = mock_pipe

                mock_t = MagicMock()
                mock_t.execute.return_value = MagicMock(
                    prompt_tokens=100,
                    completion_tokens=50,
                    result_text="result",
                    error=None,
                )
                mock_task.return_value = mock_t

                executor = BenchmarkExecutor(
                    pipelines=["sidedoc"],
                    tasks=["summarize"],
                    corpus="synthetic",
                )
                results = executor.run()

                assert isinstance(results, dict)

    def test_results_has_metadata(self) -> None:
        """Test that results include metadata section."""
        from benchmarks.benchmark_executor import BenchmarkExecutor

        with patch("benchmarks.benchmark_executor.get_pipeline") as mock_pipeline:
            with patch("benchmarks.benchmark_executor.get_task") as mock_task:
                mock_pipe = MagicMock()
                mock_pipe.extract_content.return_value = "content"
                mock_pipeline.return_value = mock_pipe

                mock_t = MagicMock()
                mock_t.execute.return_value = MagicMock(
                    prompt_tokens=100,
                    completion_tokens=50,
                    result_text="result",
                    error=None,
                )
                mock_task.return_value = mock_t

                executor = BenchmarkExecutor(
                    pipelines=["sidedoc"],
                    tasks=["summarize"],
                    corpus="synthetic",
                )
                results = executor.run()

                assert "metadata" in results
                assert "timestamp" in results["metadata"]
                assert "pipelines" in results["metadata"]
                assert "tasks" in results["metadata"]
                assert "documents" in results["metadata"]

    def test_results_has_results_array(self) -> None:
        """Test that results include results array."""
        from benchmarks.benchmark_executor import BenchmarkExecutor

        with patch("benchmarks.benchmark_executor.get_pipeline") as mock_pipeline:
            with patch("benchmarks.benchmark_executor.get_task") as mock_task:
                mock_pipe = MagicMock()
                mock_pipe.extract_content.return_value = "content"
                mock_pipeline.return_value = mock_pipe

                mock_t = MagicMock()
                mock_t.execute.return_value = MagicMock(
                    prompt_tokens=100,
                    completion_tokens=50,
                    result_text="result",
                    error=None,
                )
                mock_task.return_value = mock_t

                executor = BenchmarkExecutor(
                    pipelines=["sidedoc"],
                    tasks=["summarize"],
                    corpus="synthetic",
                )
                results = executor.run()

                assert "results" in results
                assert isinstance(results["results"], list)

    def test_results_entry_has_required_fields(self) -> None:
        """Test that each result entry has required fields."""
        from benchmarks.benchmark_executor import BenchmarkExecutor

        with patch("benchmarks.benchmark_executor.get_pipeline") as mock_pipeline:
            with patch("benchmarks.benchmark_executor.get_task") as mock_task:
                mock_pipe = MagicMock()
                mock_pipe.extract_content.return_value = "content"
                mock_pipeline.return_value = mock_pipe

                mock_t = MagicMock()
                mock_t.execute.return_value = MagicMock(
                    prompt_tokens=100,
                    completion_tokens=50,
                    result_text="result",
                    error=None,
                )
                mock_task.return_value = mock_t

                executor = BenchmarkExecutor(
                    pipelines=["sidedoc"],
                    tasks=["summarize"],
                    corpus="synthetic",
                )
                results = executor.run()

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

        with patch("benchmarks.benchmark_executor.get_pipeline") as mock_pipeline:
            with patch("benchmarks.benchmark_executor.get_task") as mock_task:
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


class TestResultsJsonOutput:
    """Test the results JSON output (US-023)."""

    def test_results_can_be_serialized_to_json(self) -> None:
        """Test that results can be serialized to JSON."""
        from benchmarks.benchmark_executor import BenchmarkExecutor

        with patch("benchmarks.benchmark_executor.get_pipeline") as mock_pipeline:
            with patch("benchmarks.benchmark_executor.get_task") as mock_task:
                mock_pipe = MagicMock()
                mock_pipe.extract_content.return_value = "content"
                mock_pipeline.return_value = mock_pipe

                mock_t = MagicMock()
                mock_t.execute.return_value = MagicMock(
                    prompt_tokens=100,
                    completion_tokens=50,
                    result_text="result",
                    error=None,
                )
                mock_task.return_value = mock_t

                executor = BenchmarkExecutor(
                    pipelines=["sidedoc"],
                    tasks=["summarize"],
                    corpus="synthetic",
                )
                results = executor.run()

                # Should serialize without error
                json_str = json.dumps(results, indent=2)
                assert json_str is not None

    def test_results_can_be_written_to_file(self) -> None:
        """Test that results can be written to a file."""
        from benchmarks.benchmark_executor import BenchmarkExecutor

        with patch("benchmarks.benchmark_executor.get_pipeline") as mock_pipeline:
            with patch("benchmarks.benchmark_executor.get_task") as mock_task:
                mock_pipe = MagicMock()
                mock_pipe.extract_content.return_value = "content"
                mock_pipeline.return_value = mock_pipe

                mock_t = MagicMock()
                mock_t.execute.return_value = MagicMock(
                    prompt_tokens=100,
                    completion_tokens=50,
                    result_text="result",
                    error=None,
                )
                mock_task.return_value = mock_t

                executor = BenchmarkExecutor(
                    pipelines=["sidedoc"],
                    tasks=["summarize"],
                    corpus="synthetic",
                )
                results = executor.run()

                with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                    json.dump(results, f, indent=2)
                    temp_path = Path(f.name)

                # Verify file was written and can be read back
                with open(temp_path) as f:
                    loaded = json.load(f)
                    assert loaded == results

                # Cleanup
                temp_path.unlink()

    def test_timestamp_is_valid_format(self) -> None:
        """Test that timestamp in metadata is a valid format."""
        from benchmarks.benchmark_executor import BenchmarkExecutor

        with patch("benchmarks.benchmark_executor.get_pipeline") as mock_pipeline:
            with patch("benchmarks.benchmark_executor.get_task") as mock_task:
                mock_pipe = MagicMock()
                mock_pipe.extract_content.return_value = "content"
                mock_pipeline.return_value = mock_pipe

                mock_t = MagicMock()
                mock_t.execute.return_value = MagicMock(
                    prompt_tokens=100,
                    completion_tokens=50,
                    result_text="result",
                    error=None,
                )
                mock_task.return_value = mock_t

                executor = BenchmarkExecutor(
                    pipelines=["sidedoc"],
                    tasks=["summarize"],
                    corpus="synthetic",
                )
                results = executor.run()

                timestamp = results["metadata"]["timestamp"]
                # Should be able to parse as ISO format
                parsed = datetime.fromisoformat(timestamp)
                assert parsed is not None
