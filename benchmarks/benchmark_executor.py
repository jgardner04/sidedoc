"""Benchmark executor (US-022 to US-023).

This module provides the BenchmarkExecutor which runs benchmarks
across pipelines, tasks, and documents.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import click


BENCHMARKS_DIR = Path(__file__).parent
SYNTHETIC_DIR = BENCHMARKS_DIR / "corpus" / "synthetic"
REAL_DIR = BENCHMARKS_DIR / "corpus" / "real"


def get_pipeline(pipeline_name: str) -> Any:
    """Get a pipeline instance by name.

    Args:
        pipeline_name: Name of the pipeline (sidedoc, pandoc, raw_docx, docint).

    Returns:
        Pipeline instance.
    """
    if pipeline_name == "sidedoc":
        from benchmarks.pipelines.sidedoc_pipeline import SidedocPipeline

        return SidedocPipeline()
    elif pipeline_name == "pandoc":
        from benchmarks.pipelines.pandoc_pipeline import PandocPipeline

        return PandocPipeline()
    elif pipeline_name == "raw_docx":
        from benchmarks.pipelines.raw_docx_pipeline import RawDocxPipeline

        return RawDocxPipeline()
    elif pipeline_name == "docint":
        from benchmarks.pipelines.docint_pipeline import DocIntelPipeline

        return DocIntelPipeline()
    else:
        raise ValueError(f"Unknown pipeline: {pipeline_name}")


def get_task(task_name: str) -> Any:
    """Get a task instance by name.

    Args:
        task_name: Name of the task (summarize, edit_single, edit_multiturn).

    Returns:
        Task instance.
    """
    if task_name == "summarize":
        from benchmarks.tasks.summarize import SummarizeTask

        return SummarizeTask()
    elif task_name == "edit_single":
        from benchmarks.tasks.edit_single import SingleEditTask

        return SingleEditTask(edit_instruction="Make the text more concise")
    elif task_name == "edit_multiturn":
        from benchmarks.tasks.edit_multiturn import MultiTurnEditTask

        return MultiTurnEditTask(
            edit_instructions=[
                "Make the text more concise",
                "Add a summary at the end",
                "Fix any grammar issues",
            ]
        )
    else:
        raise ValueError(f"Unknown task: {task_name}")


def get_documents(corpus: str) -> list[Path]:
    """Get document paths for the given corpus.

    Args:
        corpus: Corpus type (synthetic, real, all).

    Returns:
        List of document paths.
    """
    documents: list[Path] = []

    if corpus in ("synthetic", "all"):
        if SYNTHETIC_DIR.exists():
            documents.extend(SYNTHETIC_DIR.glob("*.docx"))

    if corpus in ("real", "all"):
        if REAL_DIR.exists():
            documents.extend(REAL_DIR.glob("*.docx"))

    return sorted(documents)


class BenchmarkExecutor:
    """Executor that runs benchmarks across pipelines, tasks, and documents.

    Collects results and returns them as a dict suitable for JSON serialization.
    """

    def __init__(
        self,
        pipelines: list[str],
        tasks: list[str],
        corpus: str,
    ) -> None:
        """Initialize the benchmark executor.

        Args:
            pipelines: List of pipeline names to run.
            tasks: List of task names to run.
            corpus: Corpus type (synthetic, real, all).
        """
        self.pipelines = pipelines
        self.tasks = tasks
        self.corpus = corpus

    def run(self) -> dict[str, Any]:
        """Run the benchmark suite.

        Returns:
            Dict with metadata and results array.
        """
        documents = get_documents(self.corpus)
        results: list[dict[str, Any]] = []

        click.echo(f"Found {len(documents)} documents")

        for doc_path in documents:
            click.echo(f"\nProcessing: {doc_path.name}")

            for pipeline_name in self.pipelines:
                for task_name in self.tasks:
                    click.echo(f"  Pipeline: {pipeline_name}, Task: {task_name}...", nl=False)

                    result_entry = self._run_single(
                        pipeline_name=pipeline_name,
                        task_name=task_name,
                        doc_path=doc_path,
                    )
                    results.append(result_entry)

                    if result_entry["metrics"].get("error"):
                        click.echo(" ERROR")
                    else:
                        click.echo(" OK")

        return {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "pipelines": self.pipelines,
                "tasks": self.tasks,
                "corpus": self.corpus,
                "documents": [str(d) for d in documents],
            },
            "results": results,
        }

    def _run_single(
        self,
        pipeline_name: str,
        task_name: str,
        doc_path: Path,
    ) -> dict[str, Any]:
        """Run a single pipeline/task/document combination.

        Args:
            pipeline_name: Name of the pipeline.
            task_name: Name of the task.
            doc_path: Path to the document.

        Returns:
            Result entry with pipeline, task, document, and metrics.
        """
        metrics: dict[str, Any] = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "error": None,
        }

        try:
            # Get pipeline and extract content
            pipeline = get_pipeline(pipeline_name)
            content = pipeline.extract_content(doc_path)

            # Get task and execute
            task = get_task(task_name)
            task_result = task.execute(content)

            metrics["prompt_tokens"] = task_result.prompt_tokens
            metrics["completion_tokens"] = task_result.completion_tokens
            metrics["error"] = task_result.error

        except Exception as e:
            metrics["error"] = str(e)

        return {
            "pipeline": pipeline_name,
            "task": task_name,
            "document": str(doc_path),
            "metrics": metrics,
        }
