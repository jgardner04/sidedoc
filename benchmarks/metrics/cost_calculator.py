"""Cost calculator utility (US-012).

This module provides cost calculation for LLM API usage and
Azure Document Intelligence API usage.
"""

from typing import TypedDict


class LLMCostBreakdown(TypedDict):
    """Itemized breakdown of LLM API costs."""

    input_cost: float
    output_cost: float
    total: float


class DocIntCostBreakdown(TypedDict):
    """Itemized breakdown of Document Intelligence costs."""

    page_cost: float
    total: float


class CostCalculator:
    """Calculator for API usage costs.

    Supports calculating costs for:
    - Claude/LLM API usage (based on token counts)
    - Azure Document Intelligence API usage (based on page counts)

    Pricing is configurable to support different models and tiers.
    """

    def __init__(
        self,
        input_price_per_1k: float = 0.003,
        output_price_per_1k: float = 0.015,
        docint_price_per_page: float = 0.01,
    ) -> None:
        """Initialize the cost calculator with pricing.

        Args:
            input_price_per_1k: Price per 1000 input tokens (default: $0.003 for Claude Sonnet).
            output_price_per_1k: Price per 1000 output tokens (default: $0.015 for Claude Sonnet).
            docint_price_per_page: Price per page for Document Intelligence (default: $0.01).
        """
        self._input_price_per_1k = input_price_per_1k
        self._output_price_per_1k = output_price_per_1k
        self._docint_price_per_page = docint_price_per_page

    def calculate_llm_cost(
        self, input_tokens: int, output_tokens: int
    ) -> LLMCostBreakdown:
        """Calculate the cost of LLM API usage.

        Args:
            input_tokens: Number of input tokens.
            output_tokens: Number of output tokens.

        Returns:
            Dict with input_cost, output_cost, and total.
        """
        input_cost = (input_tokens / 1000) * self._input_price_per_1k
        output_cost = (output_tokens / 1000) * self._output_price_per_1k
        total = input_cost + output_cost

        return LLMCostBreakdown(
            input_cost=input_cost,
            output_cost=output_cost,
            total=total,
        )

    def calculate_docint_cost(self, pages: int) -> DocIntCostBreakdown:
        """Calculate the cost of Document Intelligence API usage.

        Args:
            pages: Number of pages processed.

        Returns:
            Dict with page_cost and total.
        """
        page_cost = pages * self._docint_price_per_page

        return DocIntCostBreakdown(
            page_cost=page_cost,
            total=page_cost,
        )
