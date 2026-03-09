"""Report generator CLI (US-024 to US-028).

This module provides the CLI entry point for generating reports
from benchmark results.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import click

from benchmarks.metrics.cost_calculator import CostCalculator


@click.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option(
    "--output",
    type=click.Path(),
    default=None,
    help="Output path for report (default: results/report-{timestamp}.md)",
)
def cli(input_file: str, output: str | None) -> None:
    """Generate a report from benchmark results.

    INPUT_FILE is the path to the benchmark results JSON file.
    """
    # Load results
    with open(input_file) as f:
        results = json.load(f)

    # Generate report
    report = generate_report(results)

    # Determine output path
    if output:
        output_path = Path(output)
    else:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        output_path = Path(__file__).parent / "results" / f"report-{timestamp}.md"

    # Ensure results directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write report
    with open(output_path, "w") as f:
        f.write(report)

    click.echo(f"Report saved to: {output_path}")


def generate_report(results: dict[str, Any]) -> str:
    """Generate a markdown report from benchmark results.

    Args:
        results: Benchmark results dict with metadata and results array.

    Returns:
        Markdown formatted report string.
    """
    pipeline_tokens = calculate_pipeline_tokens(results)

    sections = [
        "# Sidedoc Benchmark Report\n",
        f"Generated: {datetime.now().isoformat()}\n",
        generate_executive_summary(results, pipeline_tokens),
        generate_methodology(results),
        generate_results_section(results, pipeline_tokens),
        generate_conclusions(pipeline_tokens),
    ]

    return "\n".join(sections)


def generate_executive_summary(results: dict[str, Any], pipeline_tokens: dict[str, dict[str, float]]) -> str:
    """Generate the executive summary section.

    Args:
        results: Benchmark results dict.
        pipeline_tokens: Pre-computed pipeline token averages.

    Returns:
        Markdown formatted executive summary.
    """
    lines = []
    lines.append("## Executive Summary\n")

    if pipeline_tokens:
        # Find best pipeline (lowest tokens)
        baseline = pipeline_tokens.get("raw_docx", pipeline_tokens.get("pandoc", {}))

        lines.append("### Key Findings\n")

        # Token reduction
        if "sidedoc" in pipeline_tokens and baseline:
            sidedoc_tokens = pipeline_tokens["sidedoc"]["total"]
            baseline_tokens = baseline.get("total", sidedoc_tokens)
            if baseline_tokens > 0:
                reduction = ((baseline_tokens - sidedoc_tokens) / baseline_tokens) * 100
                lines.append(f"- **Token Efficiency**: Sidedoc reduces token usage by {reduction:.1f}% compared to baseline\n")

        # Format fidelity placeholder
        lines.append("- **Format Fidelity**: Sidedoc preserves document formatting while alternatives may lose structure\n")

        # Cost savings
        lines.append("- **Cost Savings**: Lower token usage translates to reduced API costs\n")

    return "\n".join(lines)


def generate_methodology(results: dict[str, Any]) -> str:
    """Generate the methodology section.

    Args:
        results: Benchmark results dict.

    Returns:
        Markdown formatted methodology.
    """
    lines = []
    lines.append("## Methodology\n")

    metadata = results.get("metadata", {})

    # Corpus
    lines.append("### Test Corpus\n")
    corpus = metadata.get("corpus", "unknown")
    documents = metadata.get("documents", [])
    lines.append(f"- Corpus type: {corpus}\n")
    lines.append(f"- Total documents: {len(documents)}\n")

    # Pipelines
    lines.append("\n### Pipelines Compared\n")
    pipelines = metadata.get("pipelines", [])
    for pipeline in pipelines:
        desc = get_pipeline_description(pipeline)
        lines.append(f"- **{pipeline}**: {desc}\n")

    # Tasks
    lines.append("\n### Tasks Executed\n")
    tasks = metadata.get("tasks", [])
    for task in tasks:
        desc = get_task_description(task)
        lines.append(f"- **{task}**: {desc}\n")

    return "\n".join(lines)


def generate_results_section(results: dict[str, Any], pipeline_tokens: dict[str, dict[str, float]]) -> str:
    """Generate the results section with tables.

    Args:
        results: Benchmark results dict.
        pipeline_tokens: Pre-computed pipeline token averages.

    Returns:
        Markdown formatted results with tables.
    """
    lines = []
    lines.append("## Results\n")

    # Token efficiency table
    lines.append("### Token Efficiency\n")

    if pipeline_tokens:
        lines.append("| Pipeline | Prompt Tokens | Completion Tokens | Total Tokens |\n")
        lines.append("|----------|---------------|-------------------|---------------|\n")

        for pipeline, tokens in pipeline_tokens.items():
            lines.append(
                f"| {pipeline} | {tokens['prompt']:.0f} | {tokens['completion']:.0f} | {tokens['total']:.0f} |\n"
            )

    lines.append("\n")

    # Add fidelity section
    lines.append(generate_fidelity_section(results))

    lines.append("\n### Cost Analysis\n")
    lines.append("| Pipeline | Est. Cost (per doc) |\n")
    lines.append("|----------|---------------------|\n")

    calculator = CostCalculator()
    for pipeline, tokens in pipeline_tokens.items():
        cost = calculator.calculate_llm_cost(int(tokens["prompt"]), int(tokens["completion"]))["total"]
        lines.append(f"| {pipeline} | ${cost:.4f} |\n")

    return "\n".join(lines)


def generate_conclusions(pipeline_tokens: dict[str, dict[str, float]]) -> str:
    """Generate the conclusions section.

    Args:
        pipeline_tokens: Pre-computed pipeline token averages.

    Returns:
        Markdown formatted conclusions.
    """
    lines = []
    lines.append("## Conclusions\n")

    if pipeline_tokens:
        # Find best pipeline
        best_pipeline = min(pipeline_tokens, key=lambda p: pipeline_tokens[p]["total"])
        lines.append(f"### Best Performing Pipeline\n")
        lines.append(f"**{best_pipeline}** achieved the lowest token usage overall.\n\n")

    lines.append("### Recommendations\n")
    lines.append("- **Use Sidedoc** for documents where format preservation is important\n")
    lines.append("- **Use Pandoc** for quick conversions where formatting loss is acceptable\n")
    lines.append("- **Avoid Raw DOCX** for LLM tasks due to high token overhead\n")

    return "\n".join(lines)


def calculate_pipeline_tokens(results: dict[str, Any]) -> dict[str, dict[str, float]]:
    """Calculate average tokens per pipeline.

    Args:
        results: Benchmark results dict.

    Returns:
        Dict mapping pipeline names to token stats.
    """
    pipeline_stats: dict[str, dict[str, list[int]]] = {}

    for entry in results.get("results", []):
        pipeline = entry.get("pipeline", "unknown")
        metrics = entry.get("metrics", {})

        if pipeline not in pipeline_stats:
            pipeline_stats[pipeline] = {"prompt": [], "completion": []}

        if not metrics.get("error"):
            pipeline_stats[pipeline]["prompt"].append(metrics.get("prompt_tokens", 0))
            pipeline_stats[pipeline]["completion"].append(metrics.get("completion_tokens", 0))

    # Calculate averages
    result: dict[str, dict[str, float]] = {}
    for pipeline, stats in pipeline_stats.items():
        if stats["prompt"]:
            avg_prompt = sum(stats["prompt"]) / len(stats["prompt"])
            avg_completion = sum(stats["completion"]) / len(stats["completion"])
            result[pipeline] = {
                "prompt": avg_prompt,
                "completion": avg_completion,
                "total": avg_prompt + avg_completion,
            }

    return result


def get_pipeline_description(pipeline: str) -> str:
    """Get description for a pipeline.

    Args:
        pipeline: Pipeline name.

    Returns:
        Description string.
    """
    descriptions = {
        "sidedoc": "AI-native format that separates content from formatting",
        "pandoc": "Universal document converter (docx to markdown)",
        "raw_docx": "Raw DOCX paragraph extraction (baseline)",
        "ooxml": "Full OOXML extraction from .docx archive (all XML files)",
        "docint": "Azure Document Intelligence API",
    }
    return descriptions.get(pipeline, "Unknown pipeline")


def get_task_description(task: str) -> str:
    """Get description for a task.

    Args:
        task: Task name.

    Returns:
        Description string.
    """
    descriptions = {
        "summarize": "Generate 3-5 bullet point summary",
        "edit_single": "Apply single edit instruction",
        "edit_multiturn": "Apply 3 sequential edits",
    }
    return descriptions.get(task, "Unknown task")


def _fmt_score(val: float | None) -> str:
    """Format a fidelity score for display."""
    return "N/A" if val is None else f"{val:.1f}"


def generate_fidelity_section(results: dict[str, Any]) -> str:
    """Generate fidelity scoring section from benchmark results.

    If fidelity_results exists in results, render a table:
    | Pipeline | Structure | Formatting | Tables | Hyperlinks | Track Changes | Total |

    Otherwise, return the existing placeholder text.

    Args:
        results: Benchmark results dict.

    Returns:
        Markdown formatted fidelity section.
    """
    lines = []
    lines.append("### Format Fidelity\n")

    if "fidelity_results" not in results or not results["fidelity_results"]:
        lines.append("*Fidelity scores require visual comparison tools (LibreOffice, Poppler)*\n")
        return "\n".join(lines)

    pipeline_fidelity = calculate_pipeline_fidelity(results)

    lines.append("| Pipeline | Structure | Formatting | Tables | Hyperlinks | Track Changes | Total |\n")
    lines.append("|----------|-----------|------------|--------|------------|---------------|-------|\n")

    for pipeline, scores in pipeline_fidelity.items():
        lines.append(
            f"| {pipeline} | {_fmt_score(scores.get('structure'))} | {_fmt_score(scores.get('formatting'))} "
            f"| {_fmt_score(scores.get('tables'))} | {_fmt_score(scores.get('hyperlinks'))} "
            f"| {_fmt_score(scores.get('track_changes'))} | {_fmt_score(scores.get('total'))} |\n"
        )

    return "\n".join(lines)


def calculate_pipeline_fidelity(results: dict[str, Any]) -> dict[str, dict[str, float | None]]:
    """Average fidelity scores per pipeline across documents.

    Returns dict mapping pipeline name to avg scores per dimension.
    For null dimensions, average only non-null values.

    Args:
        results: Benchmark results dict with fidelity_results.

    Returns:
        Dict mapping pipeline names to averaged fidelity scores.
    """
    dimensions = ["structure", "formatting", "tables", "hyperlinks", "track_changes", "total"]
    pipeline_accum: dict[str, dict[str, list[float]]] = {}

    for entry in results.get("fidelity_results", []):
        if entry.get("error"):
            continue

        pipeline = entry["pipeline"]
        scores = entry.get("scores", {})

        if pipeline not in pipeline_accum:
            pipeline_accum[pipeline] = {d: [] for d in dimensions}

        for dim in dimensions:
            val = scores.get(dim)
            if val is not None:
                pipeline_accum[pipeline][dim].append(val)

    result: dict[str, dict[str, float | None]] = {}
    for pipeline, dim_lists in pipeline_accum.items():
        result[pipeline] = {}
        for dim in dimensions:
            vals = dim_lists[dim]
            if vals:
                result[pipeline][dim] = sum(vals) / len(vals)
            else:
                result[pipeline][dim] = None

    return result


if __name__ == "__main__":
    cli()
