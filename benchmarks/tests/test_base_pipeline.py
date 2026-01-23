"""Tests for base pipeline interface (US-005)."""

from pathlib import Path
from abc import ABC
import pytest


BENCHMARKS_DIR = Path(__file__).parent.parent


class TestBasePipeline:
    """Test that the base pipeline interface is properly defined."""

    def test_base_module_exists(self) -> None:
        """Test that base.py exists in pipelines directory."""
        base_path = BENCHMARKS_DIR / "pipelines" / "base.py"
        assert base_path.exists(), "benchmarks/pipelines/base.py does not exist"

    def test_base_pipeline_is_importable(self) -> None:
        """Test that BasePipeline can be imported."""
        from benchmarks.pipelines.base import BasePipeline

        assert BasePipeline is not None

    def test_base_pipeline_is_abstract(self) -> None:
        """Test that BasePipeline is an abstract base class."""
        from benchmarks.pipelines.base import BasePipeline

        assert issubclass(BasePipeline, ABC)

        # Should not be instantiable
        with pytest.raises(TypeError):
            BasePipeline()  # type: ignore[abstract]

    def test_base_pipeline_has_required_abstract_methods(self) -> None:
        """Test that BasePipeline defines required abstract methods."""
        from benchmarks.pipelines.base import BasePipeline

        # Check abstract methods are defined
        abstract_methods: set[str] = getattr(BasePipeline, "__abstractmethods__", set())
        assert "extract_content" in abstract_methods
        assert "apply_edit" in abstract_methods
        assert "rebuild_document" in abstract_methods

    def test_pipeline_result_is_importable(self) -> None:
        """Test that PipelineResult can be imported."""
        from benchmarks.pipelines.base import PipelineResult

        assert PipelineResult is not None

    def test_pipeline_result_is_dataclass(self) -> None:
        """Test that PipelineResult is a dataclass with correct fields."""
        from dataclasses import fields
        from benchmarks.pipelines.base import PipelineResult

        field_names = {f.name for f in fields(PipelineResult)}

        assert "input_tokens" in field_names
        assert "output_tokens" in field_names
        assert "time_elapsed" in field_names
        assert "output_path" in field_names
        assert "error" in field_names

    def test_pipeline_result_can_be_instantiated(self) -> None:
        """Test that PipelineResult can be created with values."""
        from benchmarks.pipelines.base import PipelineResult

        result = PipelineResult(
            input_tokens=100,
            output_tokens=50,
            time_elapsed=1.5,
            output_path=Path("/tmp/test.docx"),
            error=None,
        )

        assert result.input_tokens == 100
        assert result.output_tokens == 50
        assert result.time_elapsed == 1.5
        assert result.output_path == Path("/tmp/test.docx")
        assert result.error is None

    def test_pipeline_result_can_have_error(self) -> None:
        """Test that PipelineResult can store an error."""
        from benchmarks.pipelines.base import PipelineResult

        result = PipelineResult(
            input_tokens=0,
            output_tokens=0,
            time_elapsed=0.1,
            output_path=None,
            error="Something went wrong",
        )

        assert result.error == "Something went wrong"
        assert result.output_path is None
