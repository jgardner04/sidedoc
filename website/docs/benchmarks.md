# Benchmarks

Measured results comparing document processing pipelines for AI workloads.

## Results Summary

We benchmarked four pipelines across 15 documents and 3 LLM tasks using Gemini 2.5 Flash. All pipelines ran against the same model for an apples-to-apples comparison.

### Key Findings

- **Sidedoc uses 1,524x fewer prompt tokens than raw OOXML** — measured across all successful LLM task runs
- **OOXML is not just expensive, it's unreliable** — 9 of 45 OOXML calls failed (rate limits / errors), while all other pipelines completed 45/45
- **Sidedoc uses 13% fewer prompt tokens than Pandoc** while preserving formatting that Pandoc loses
- **At Claude Sonnet 4 pricing, OOXML costs $2.78/doc vs Sidedoc's $0.07/doc** — a 41x cost difference

### Why This Matters

Every document processing pipeline faces a fundamental tradeoff: token efficiency vs format preservation. Raw text extraction is cheapest but loses all formatting. Raw OOXML preserves everything but is absurdly expensive in tokens. Sidedoc resolves this tradeoff — clean markdown for the LLM, formatting metadata stored separately, and lossless round-trip reconstruction.

## LLM Task Token Usage

Actual API token counts from Gemini 2.5 Flash across 3 tasks and 15 documents. All numbers are measured, not estimated.

### Summarization Task

| Pipeline | Avg Prompt Tokens | Avg Completion Tokens | Avg Total | Successful Runs |
|----------|------------------:|----------------------:|----------:|----------------:|
| **Sidedoc** | **106** | **813** | **919** | 15/15 |
| Pandoc | 122 | 790 | 912 | 15/15 |
| Raw Text | 58 | 605 | 663 | 15/15 |
| Raw OOXML | 359,706 | 1,020 | 360,726 | 12/15 |

### Single Edit Task

| Pipeline | Avg Prompt Tokens | Avg Completion Tokens | Avg Total | Successful Runs |
|----------|------------------:|----------------------:|----------:|----------------:|
| **Sidedoc** | **115** | **1,267** | **1,382** | 15/15 |
| Pandoc | 130 | 1,100 | 1,230 | 15/15 |
| Raw Text | 67 | 940 | 1,007 | 15/15 |
| Raw OOXML | 359,865 | 4,092 | 363,957 | 13/15 |

### Multi-Turn Edit Task (3 rounds)

| Pipeline | Avg Prompt Tokens | Avg Completion Tokens | Avg Total | Successful Runs |
|----------|------------------:|----------------------:|----------:|----------------:|
| **Sidedoc** | **348** | **2,268** | **2,616** | 15/15 |
| Pandoc | 397 | 2,012 | 2,409 | 15/15 |
| Raw Text | 208 | 1,534 | 1,742 | 15/15 |
| Raw OOXML | 363,915 | 10,001 | 373,916 | 11/15 |

### Aggregate Token Usage

| Pipeline | Runs | Total Prompt | Total Completion | Grand Total | vs Sidedoc (prompt) |
|----------|-----:|-------------:|-----------------:|------------:|--------------------:|
| **Sidedoc** | **45/45** | **8,531** | **65,228** | **73,759** | **1.0x** |
| Pandoc | 45/45 | 9,726 | 58,527 | 68,253 | 1.1x |
| Raw Text | 45/45 | 4,994 | 46,194 | 51,188 | 0.6x |
| Raw OOXML | 36/45 | 12,997,779 | 175,449 | 13,173,228 | 1,524x |

## Content Representation

How many tokens does each pipeline need to represent document content? Measured with `cl100k_base` tokenizer before sending to the LLM.

| Pipeline | Avg Tokens/Doc | Total (15 docs) | vs Sidedoc |
|----------|---------------:|----------------:|-----------:|
| **Sidedoc** | **74** | **1,117** | **1.0x** |
| Pandoc | 89 | 1,336 | 1.2x |
| Raw Text | 34 | 505 | 0.5x |
| Raw OOXML | 325,715 | 4,885,730 | 4,374x |

Raw text extraction uses fewer tokens but **cannot reconstruct the document** — all formatting, structure, and metadata are lost.

## Cost Analysis

### Gemini 2.5 Flash ($0.15/M input, $0.60/M output)

| Pipeline | Total Cost | Cost per Document | vs Sidedoc |
|----------|----------:|-----------------:|-----------:|
| **Sidedoc** | **$0.04** | **$0.003** | **1.0x** |
| Pandoc | $0.04 | $0.002 | 0.9x |
| Raw Text | $0.03 | $0.002 | 0.7x |
| Raw OOXML | $2.05 | $0.137 | 51x |

### Claude Sonnet 4 ($3/M input, $15/M output)

| Pipeline | Total Cost | Cost per Document | vs Sidedoc |
|----------|----------:|-----------------:|-----------:|
| **Sidedoc** | **$1.00** | **$0.07** | **1.0x** |
| Pandoc | $0.91 | $0.06 | 0.9x |
| Raw Text | $0.71 | $0.05 | 0.7x |
| Raw OOXML | $41.63 | $2.78 | 41x |

## Pipeline Comparison

| Capability | Sidedoc | Pandoc | Raw Text | Raw OOXML |
|------------|:-------:|:------:|:--------:|:---------:|
| Extract content | Yes | Yes | Yes | Yes |
| Preserve formatting metadata | Yes | No | No | Yes |
| Rebuild document | Yes | Partial | No | Theoretically |
| Lossless round-trip | Yes | No | No | No |
| Token efficient | Yes | Yes | Best | Worst |
| Reliable (0 errors) | Yes | Yes | Yes | No (20% failure rate) |
| Tables preserved | Yes | Partial | No | Yes |
| Track changes support | Yes | No | No | Yes |

## Methodology

### Test Corpus

- **15 synthetic documents** from `tests/fixtures/`, covering: simple text, formatted text, hyperlinks, images, lists, tables (simple, complex, formatted, merged), and track changes (simple, headings, lists, multi-author, paragraph)
- All documents processed through each pipeline identically

### Pipelines

| Pipeline | Description |
|----------|-------------|
| **Sidedoc** | AI-native format — extracts to clean markdown + formatting metadata, enables lossless round-trip |
| **Pandoc** | Universal converter — `docx -> markdown` via pypandoc, loses most formatting on round-trip |
| **Raw Text** | Baseline — extracts paragraph text via python-docx, no formatting, no rebuild capability |
| **Raw OOXML** | Full XML content from the .docx archive (document.xml + styles.xml + numbering.xml + theme + rels) — what an LLM would need for format-preserving round-trip without an intermediate format |

### Tasks

| Task | Description | LLM Calls |
|------|-------------|----------:|
| `summarize` | Generate 3-5 bullet point summary | 1 |
| `edit_single` | Apply a single edit instruction ("Make the text more concise") | 1 |
| `edit_multiturn` | Apply 3 sequential edits (concise, add summary, fix grammar) | 3 |

### Token Counting

- **Content representation**: `cl100k_base` tokenizer via `tiktoken`
- **LLM task tokens**: Actual `prompt_tokens` and `completion_tokens` from API responses
- **Model**: Gemini 2.5 Flash via LiteLLM (all 4 pipelines on the same model for fair comparison)

### Benchmark Date

March 2026. Full results in `benchmarks/results/benchmark-latest.json`.

---

## Run It Yourself

### Prerequisites

- **Python 3.11+**
- **Pandoc** — `brew install pandoc` (macOS) or `sudo apt install pandoc` (Ubuntu)
- **API Key** — `ANTHROPIC_API_KEY` or `GEMINI_API_KEY` depending on model

### Installation

```bash
git clone https://github.com/jgardner04/sidedoc.git
cd sidedoc
pip install -r benchmarks/requirements.txt
```

### Running Benchmarks

```bash
# Run all pipelines against synthetic corpus
for p in sidedoc pandoc raw_docx ooxml; do
  python -m benchmarks.run_benchmark --pipeline $p --corpus synthetic \
    --model gemini/gemini-2.5-flash \
    --output benchmarks/results/benchmark-${p}.json
done

# Generate report
python -m benchmarks.generate_report benchmarks/results/benchmark-latest.json
```

### Filtering

```bash
# Single pipeline
python -m benchmarks.run_benchmark --pipeline sidedoc

# Single task
python -m benchmarks.run_benchmark --task summarize

# Combine filters
python -m benchmarks.run_benchmark --pipeline sidedoc --task summarize --corpus synthetic

# Use a different model
python -m benchmarks.run_benchmark --model claude-sonnet-4-20250514
```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | For Claude | API key for Anthropic models |
| `GEMINI_API_KEY` | For Gemini | API key for Google Gemini models |
| `AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT` | No | Azure DI endpoint (for docint pipeline) |
| `AZURE_DOCUMENT_INTELLIGENCE_KEY` | No | Azure DI API key |
