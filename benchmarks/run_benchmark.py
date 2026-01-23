"""Benchmark runner CLI (US-021 to US-023).

This module provides the CLI entry point for running benchmarks.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import click


# Available pipelines
PIPELINES = ["sidedoc", "pandoc", "raw_docx", "docint"]

# Available tasks
TASKS = ["summarize", "edit_single", "edit_multiturn"]

# Corpus options
CORPUS_OPTIONS = ["synthetic", "real", "all"]


@click.command()
@click.option(
    "--pipeline",
    type=click.Choice(PIPELINES),
    default=None,
    help="Run only this pipeline (default: all)",
)
@click.option(
    "--task",
    type=click.Choice(TASKS),
    default=None,
    help="Run only this task (default: all)",
)
@click.option(
    "--corpus",
    type=click.Choice(CORPUS_OPTIONS),
    default="all",
    help="Which corpus to use: synthetic, real, or all (default: all)",
)
@click.option(
    "--output",
    type=click.Path(),
    default=None,
    help="Output path for results JSON (default: results/benchmark-{timestamp}.json)",
)
def cli(
    pipeline: Optional[str],
    task: Optional[str],
    corpus: str,
    output: Optional[str],
) -> None:
    """Run the Sidedoc benchmark suite.

    Compares document processing pipelines across multiple tasks and documents.
    Results are saved to JSON for later analysis and report generation.

    Available pipelines: sidedoc, pandoc, raw_docx, docint

    Available tasks: summarize, edit_single, edit_multiturn

    Corpus options: synthetic (test fixtures), real (downloaded PDFs), all
    """
    from benchmarks.benchmark_executor import BenchmarkExecutor

    # Determine which pipelines to run
    pipelines_to_run = [pipeline] if pipeline else PIPELINES

    # Determine which tasks to run
    tasks_to_run = [task] if task else TASKS

    # Determine output path
    if output:
        output_path = Path(output)
    else:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        output_path = Path(__file__).parent / "results" / f"benchmark-{timestamp}.json"

    # Ensure results directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    click.echo(f"Running benchmark suite...")
    click.echo(f"  Pipelines: {', '.join(pipelines_to_run)}")
    click.echo(f"  Tasks: {', '.join(tasks_to_run)}")
    click.echo(f"  Corpus: {corpus}")
    click.echo(f"  Output: {output_path}")
    click.echo()

    # Run the benchmark
    executor = BenchmarkExecutor(
        pipelines=pipelines_to_run,
        tasks=tasks_to_run,
        corpus=corpus,
    )

    results = executor.run()

    # Save results
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    click.echo()
    click.echo(f"Results saved to: {output_path}")


if __name__ == "__main__":
    cli()
