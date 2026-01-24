# Sidedoc Benchmark Suite

## Overview

This benchmark suite measures and compares document processing pipelines for AI workloads. It evaluates token efficiency, format fidelity, and cost when using different approaches to prepare documents for LLM processing.

### What This Benchmark Measures

- **Token Efficiency**: How many tokens are needed to represent document content
- **Format Fidelity**: How well the original document formatting is preserved after round-trip
- **Cost Analysis**: Estimated API costs based on token usage

### Pipelines Compared

| Pipeline | Description |
|----------|-------------|
| **Sidedoc** | AI-native format that separates content from formatting |
| **Pandoc** | Universal document converter (docx → markdown → docx) |
| **Raw DOCX** | Direct paragraph extraction (baseline) |
| **Document Intelligence** | Azure AI Document Intelligence API |

## Prerequisites

Before running the benchmark, ensure you have:

- **Python 3.11+** - Required for all benchmark code
- **Pandoc** - For the Pandoc pipeline comparison
- **LibreOffice** - For visual fidelity scoring (docx → PDF conversion)
- **Poppler** - For PDF → image conversion (pdfinfo, pdftoppm)

### Installing Prerequisites

**macOS (Homebrew):**
```bash
brew install pandoc libreoffice poppler
```

**Ubuntu/Debian:**
```bash
sudo apt install pandoc libreoffice poppler-utils
```

**Windows:**
- Install Pandoc: https://pandoc.org/installing.html
- Install LibreOffice: https://www.libreoffice.org/download/
- Install Poppler: https://github.com/oschwartz10612/poppler-windows/releases

## Installation

1. Clone the repository and navigate to it:
```bash
git clone https://github.com/jgardner04/sidedoc.git
cd sidedoc
```

2. Install dependencies:
```bash
pip install -r benchmarks/requirements.txt
```

3. Set up environment variables (see Environment Variables section below)

## Usage

### Running the Full Benchmark

Run all pipelines against all tasks and all documents:

```bash
python -m benchmarks.run_benchmark
```

### Filtering by Pipeline

Run only the Sidedoc pipeline:

```bash
python -m benchmarks.run_benchmark --pipeline sidedoc
```

### Filtering by Task

Run only the summarization task:

```bash
python -m benchmarks.run_benchmark --task summarize
```

### Filtering by Corpus

Run only on synthetic test fixtures:

```bash
python -m benchmarks.run_benchmark --corpus synthetic
```

### Combining Filters

```bash
python -m benchmarks.run_benchmark --pipeline sidedoc --task summarize --corpus synthetic
```

### Selecting LLM Model

Use the `--model` flag to specify which LLM to use. The benchmark uses [LiteLLM](https://docs.litellm.ai/) for unified access to multiple providers.

```bash
# Default: Claude Sonnet
python -m benchmarks.run_benchmark --model claude-sonnet-4-20250514

# OpenAI
python -m benchmarks.run_benchmark --model gpt-4o

# Local Ollama model (no API key needed)
python -m benchmarks.run_benchmark --model ollama/llama3
```

#### Supported Providers

| Provider | Model Format | API Key Variable |
|----------|--------------|------------------|
| Anthropic | `claude-sonnet-4-20250514`, `claude-opus-4-20250514` | `ANTHROPIC_API_KEY` |
| OpenAI | `gpt-4o`, `gpt-4-turbo` | `OPENAI_API_KEY` |
| Ollama | `ollama/llama3`, `ollama/mistral` | None (local) |
| Google | `gemini/gemini-pro` | `GEMINI_API_KEY` |

See [LiteLLM's provider list](https://docs.litellm.ai/docs/providers) for all supported models.

#### Using Ollama for Local Development

For fast iteration without API costs:

1. Install Ollama: https://ollama.ai/download
2. Pull a model: `ollama pull llama3`
3. Run benchmark: `python -m benchmarks.run_benchmark --model ollama/llama3`

**Note:** Token counts will differ between providers due to different tokenizers. The relative efficiency comparison (sidedoc vs docx) remains valid across all tokenizers. Use Anthropic models for official published benchmark numbers.

### Generating Reports

After running a benchmark, generate a markdown report:

```bash
python -m benchmarks.generate_report results/benchmark-TIMESTAMP.json
```

## Environment Variables

The following environment variables configure the benchmark:

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Conditional* | API key for Claude models |
| `OPENAI_API_KEY` | Conditional* | API key for OpenAI models |
| `GEMINI_API_KEY` | Conditional* | API key for Google Gemini models |
| `AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT` | No | Azure DI endpoint URL |
| `AZURE_DOCUMENT_INTELLIGENCE_KEY` | No | Azure DI API key |

*Only required for the corresponding provider. Local models (Ollama) require no API key.

### Setting Environment Variables

**Unix/macOS:**
```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

**Windows (PowerShell):**
```powershell
$env:ANTHROPIC_API_KEY = "your-api-key-here"
```

## Examples

### Example 1: Quick Test with Synthetic Documents

```bash
# Run a quick test with synthetic fixtures
python -m benchmarks.run_benchmark --corpus synthetic --pipeline sidedoc --task summarize
```

### Example 2: Full Benchmark Comparison

```bash
# Run full benchmark (requires API keys)
python -m benchmarks.run_benchmark

# Generate report
python -m benchmarks.generate_report results/benchmark-*.json --output results/report.md
```

### Example 3: Token Efficiency Only

```bash
# Compare token counts without running LLM tasks
python -m benchmarks.run_benchmark --pipeline sidedoc --pipeline pandoc --pipeline raw_docx --corpus synthetic
```

## Troubleshooting

### "LibreOffice not found" Error

The visual scoring requires LibreOffice. Install it and ensure `soffice` is in your PATH.

**macOS:** `brew install libreoffice`

**Ubuntu:** `sudo apt install libreoffice`

### "Poppler not found" Error

PDF-to-image conversion requires Poppler's `pdfinfo` and `pdftoppm`.

**macOS:** `brew install poppler`

**Ubuntu:** `sudo apt install poppler-utils`

### "ANTHROPIC_API_KEY not set" Error

Set the API key in your environment:

```bash
export ANTHROPIC_API_KEY="your-key"
```

### "Module not found" Errors

Ensure you've installed all dependencies:

```bash
pip install -r benchmarks/requirements.txt
```

### Visual Scoring Skipped

If visual scoring tests are skipped, the prerequisites (LibreOffice + Poppler) are not available. This is non-fatal; other metrics will still be collected.

## Output Files

Results are saved to the `benchmarks/results/` directory:

- `benchmark-{timestamp}.json` - Raw benchmark data
- `report-{timestamp}.md` - Human-readable markdown report

## Contributing

When adding new pipelines or tasks:

1. Follow TDD - write failing tests first
2. Implement the minimal code to pass
3. Update this README if adding new prerequisites
