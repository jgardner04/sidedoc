"""Tests for cost calculator utility (US-012)."""

from pathlib import Path

import pytest


BENCHMARKS_DIR = Path(__file__).parent.parent


class TestCostCalculator:
    """Test that the cost calculator utility works correctly."""

    def test_module_exists(self) -> None:
        """Test that cost_calculator.py exists."""
        module_path = BENCHMARKS_DIR / "metrics" / "cost_calculator.py"
        assert module_path.exists(), "benchmarks/metrics/cost_calculator.py does not exist"

    def test_cost_calculator_is_importable(self) -> None:
        """Test that CostCalculator can be imported."""
        from benchmarks.metrics.cost_calculator import CostCalculator

        assert CostCalculator is not None

    def test_calculate_llm_cost_returns_correct_type(self) -> None:
        """Test that calculate_llm_cost returns a dict with expected keys."""
        from benchmarks.metrics.cost_calculator import CostCalculator

        calculator = CostCalculator()
        result = calculator.calculate_llm_cost(1000, 500)

        assert isinstance(result, dict)
        assert "input_cost" in result
        assert "output_cost" in result
        assert "total" in result

    def test_calculate_llm_cost_computes_correctly(self) -> None:
        """Test that calculate_llm_cost computes Claude API cost correctly."""
        from benchmarks.metrics.cost_calculator import CostCalculator

        calculator = CostCalculator()
        # Default pricing: $0.003/1K input, $0.015/1K output
        result = calculator.calculate_llm_cost(1000, 1000)

        # 1000 tokens at $0.003/1K = $0.003
        # 1000 tokens at $0.015/1K = $0.015
        # Total = $0.018
        assert abs(result["input_cost"] - 0.003) < 0.0001
        assert abs(result["output_cost"] - 0.015) < 0.0001
        assert abs(result["total"] - 0.018) < 0.0001

    def test_calculate_llm_cost_zero_tokens(self) -> None:
        """Test that calculate_llm_cost handles zero tokens."""
        from benchmarks.metrics.cost_calculator import CostCalculator

        calculator = CostCalculator()
        result = calculator.calculate_llm_cost(0, 0)

        assert result["input_cost"] == 0.0
        assert result["output_cost"] == 0.0
        assert result["total"] == 0.0

    def test_calculate_docint_cost_returns_correct_type(self) -> None:
        """Test that calculate_docint_cost returns a dict with expected keys."""
        from benchmarks.metrics.cost_calculator import CostCalculator

        calculator = CostCalculator()
        result = calculator.calculate_docint_cost(10)

        assert isinstance(result, dict)
        assert "page_cost" in result
        assert "total" in result

    def test_calculate_docint_cost_computes_correctly(self) -> None:
        """Test that calculate_docint_cost computes Document Intelligence cost correctly."""
        from benchmarks.metrics.cost_calculator import CostCalculator

        calculator = CostCalculator()
        # Default pricing: ~$0.01/page
        result = calculator.calculate_docint_cost(10)

        # 10 pages at $0.01 = $0.10
        assert abs(result["page_cost"] - 0.10) < 0.0001
        assert abs(result["total"] - 0.10) < 0.0001

    def test_calculate_docint_cost_zero_pages(self) -> None:
        """Test that calculate_docint_cost handles zero pages."""
        from benchmarks.metrics.cost_calculator import CostCalculator

        calculator = CostCalculator()
        result = calculator.calculate_docint_cost(0)

        assert result["page_cost"] == 0.0
        assert result["total"] == 0.0

    def test_configurable_pricing(self) -> None:
        """Test that pricing is configurable."""
        from benchmarks.metrics.cost_calculator import CostCalculator

        # Use custom pricing
        calculator = CostCalculator(
            input_price_per_1k=0.005,
            output_price_per_1k=0.020,
            docint_price_per_page=0.02,
        )

        llm_result = calculator.calculate_llm_cost(1000, 1000)
        assert abs(llm_result["input_cost"] - 0.005) < 0.0001
        assert abs(llm_result["output_cost"] - 0.020) < 0.0001

        docint_result = calculator.calculate_docint_cost(10)
        assert abs(docint_result["total"] - 0.20) < 0.0001

    def test_returns_itemized_breakdown(self) -> None:
        """Test that results include itemized breakdown."""
        from benchmarks.metrics.cost_calculator import CostCalculator

        calculator = CostCalculator()

        llm_result = calculator.calculate_llm_cost(5000, 2000)
        assert "input_cost" in llm_result
        assert "output_cost" in llm_result
        assert "total" in llm_result
        assert llm_result["total"] == llm_result["input_cost"] + llm_result["output_cost"]

        docint_result = calculator.calculate_docint_cost(5)
        assert "page_cost" in docint_result
        assert "total" in docint_result
        assert docint_result["total"] == docint_result["page_cost"]

    def test_large_token_counts(self) -> None:
        """Test with large token counts (100K+ tokens)."""
        from benchmarks.metrics.cost_calculator import CostCalculator

        calculator = CostCalculator()

        # 100K input, 50K output
        result = calculator.calculate_llm_cost(100_000, 50_000)

        # 100K * $0.003/1K = $0.30
        # 50K * $0.015/1K = $0.75
        # Total = $1.05
        assert abs(result["input_cost"] - 0.30) < 0.01
        assert abs(result["output_cost"] - 0.75) < 0.01
        assert abs(result["total"] - 1.05) < 0.01
