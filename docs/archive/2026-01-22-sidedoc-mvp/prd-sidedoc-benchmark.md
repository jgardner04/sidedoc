# PRD: Sidedoc Value Proposition Benchmark

## Introduction

Create a reproducible benchmark suite that proves Sidedoc's value proposition against alternative document-AI workflows. The benchmark measures token efficiency, format fidelity, and end-to-end cost savings across multiple document types and editing tasks. Results are auto-generated into a publishable whitepaper suitable for enterprise architects, investors, and AI decision-makers.

## Goals

- Prove Sidedoc uses fewer tokens than alternatives for AI document interaction
- Demonstrate format preservation superiority through edit cycles
- Calculate concrete cost savings for realistic workflows
- Provide reproducible, open-source benchmark anyone can run
- Auto-generate a professional whitepaper from benchmark results

## User Stories

### US-001: Set up benchmark project structure
**Description:** As a developer, I need the benchmark directory structure created so implementation can proceed in an organized manner.

**Acceptance Criteria:**
- [ ] Create `benchmarks/` directory with subdirectories: `corpus/`, `pipelines/`, `tasks/`, `metrics/`, `results/`
- [ ] Create `benchmarks/requirements.txt` with all dependencies
- [ ] Create `benchmarks/README.md` with project overview
- [ ] Symlink `corpus/synthetic/` to `tests/fixtures/`
- [ ] Typecheck passes

### US-002: Download and convert real-world test corpus
**Description:** As a benchmark user, I need real-world public domain documents so the benchmark reflects realistic enterprise scenarios.

**Acceptance Criteria:**
- [ ] Script downloads 5 PDFs from public sources (SEC, GSA, SSS, BMW, Coca-Cola)
- [ ] Script converts PDFs to DOCX using LibreOffice
- [ ] Script extracts 5-15 page excerpts from large documents
- [ ] Converted documents stored in `corpus/real/`
- [ ] Script is idempotent (re-running doesn't duplicate files)
- [ ] README documents the source URLs and licensing (public domain)

### US-003: Implement Sidedoc pipeline
**Description:** As a benchmark runner, I need the Sidedoc pipeline implemented so it can be compared against alternatives.

**Acceptance Criteria:**
- [ ] `pipelines/sidedoc_pipeline.py` implements `SidedocPipeline` class
- [ ] Pipeline executes: extract → read content.md → (task) → sync → build
- [ ] Pipeline returns metrics: input_tokens, output_tokens, time_elapsed, output_docx_path
- [ ] Pipeline accepts any `.docx` file as input
- [ ] Unit tests verify pipeline works with synthetic fixtures
- [ ] Typecheck passes

### US-004: Implement Document Intelligence pipeline
**Description:** As a benchmark runner, I need the Azure Document Intelligence pipeline so we can compare against enterprise solutions.

**Acceptance Criteria:**
- [ ] `pipelines/docint_pipeline.py` implements `DocIntelPipeline` class
- [ ] Pipeline uses real Azure Document Intelligence API
- [ ] Pipeline executes: analyze document → extract text → (task) → regenerate docx
- [ ] Pipeline returns metrics: input_tokens, output_tokens, api_cost, time_elapsed
- [ ] Requires `AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT` and `AZURE_DOCUMENT_INTELLIGENCE_KEY` env vars
- [ ] Graceful error if Azure credentials not configured
- [ ] Unit tests with mocked Azure responses
- [ ] Typecheck passes

### US-005: Implement Pandoc pipeline
**Description:** As a benchmark runner, I need the Pandoc pipeline so we can compare against open-source alternatives.

**Acceptance Criteria:**
- [ ] `pipelines/pandoc_pipeline.py` implements `PandocPipeline` class
- [ ] Pipeline executes: docx → markdown (via pandoc) → (task) → markdown → docx
- [ ] Pipeline returns metrics: input_tokens, output_tokens, time_elapsed, output_docx_path
- [ ] Requires `pandoc` binary installed (checked at runtime with helpful error)
- [ ] Unit tests verify pipeline works with synthetic fixtures
- [ ] Typecheck passes

### US-006: Implement Raw DOCX pipeline
**Description:** As a benchmark runner, I need the raw docx baseline so we can show why naive approaches fail.

**Acceptance Criteria:**
- [ ] `pipelines/raw_docx_pipeline.py` implements `RawDocxPipeline` class
- [ ] Pipeline executes: extract XML-ish text via python-docx → (task) → attempt to write back
- [ ] Pipeline returns metrics: input_tokens, output_tokens, time_elapsed
- [ ] Pipeline may fail on rebuild (this is expected and documented)
- [ ] Unit tests verify token counting works
- [ ] Typecheck passes

### US-007: Implement summarization task
**Description:** As a benchmark runner, I need the summarization task so we can measure read-only token efficiency.

**Acceptance Criteria:**
- [ ] `tasks/summarize.py` implements `SummarizeTask` class
- [ ] Task sends document content to Claude API with fixed prompt
- [ ] Prompt: "Summarize this document in 3-5 bullet points"
- [ ] Task returns: prompt_tokens, completion_tokens, summary_text
- [ ] Task works with any pipeline's extracted content
- [ ] Unit tests verify token counting accuracy
- [ ] Typecheck passes

### US-008: Implement single-edit task
**Description:** As a benchmark runner, I need the single-edit task so we can measure read-write workflows.

**Acceptance Criteria:**
- [ ] `tasks/edit_single.py` implements `SingleEditTask` class
- [ ] Task sends document + edit instruction to Claude API
- [ ] Edit instruction is deterministic per document (defined in task config)
- [ ] Task returns: prompt_tokens, completion_tokens, edited_content
- [ ] Task works with any pipeline's extracted content
- [ ] Unit tests verify edit is applied correctly
- [ ] Typecheck passes

### US-009: Implement multi-turn edit task
**Description:** As a benchmark runner, I need the multi-turn task so we can show compounding cost advantages.

**Acceptance Criteria:**
- [ ] `tasks/edit_multiturn.py` implements `MultiTurnEditTask` class
- [ ] Task executes 3 rounds of edits with simulated human feedback
- [ ] Each round: send context + edit instruction → receive edit → apply
- [ ] Context grows each round (for non-Sidedoc pipelines)
- [ ] Task returns: total_prompt_tokens, total_completion_tokens, per_round_metrics
- [ ] Unit tests verify all 3 rounds execute
- [ ] Typecheck passes

### US-010: Implement token counter metric
**Description:** As a benchmark runner, I need accurate token counting so cost calculations are reliable.

**Acceptance Criteria:**
- [ ] `metrics/token_counter.py` implements `TokenCounter` class
- [ ] Counts tokens using `tiktoken` (cl100k_base encoding for Claude)
- [ ] Accepts string input, returns integer token count
- [ ] Also captures actual token counts from Claude API responses when available
- [ ] Unit tests verify counts match expected values
- [ ] Typecheck passes

### US-011: Implement format fidelity scorer
**Description:** As a benchmark runner, I need format fidelity scoring so we can quantify formatting preservation.

**Acceptance Criteria:**
- [ ] `metrics/fidelity_scorer.py` implements `FidelityScorer` class
- [ ] Computes structural score: heading/list/paragraph structure match (0-100)
- [ ] Computes style score: font/size/color sampling from 10 random paragraphs (0-100)
- [ ] Computes visual score: render to PNG, compute perceptual hash difference (0-100)
- [ ] Returns weighted total: `0.3×structural + 0.3×style + 0.4×visual`
- [ ] Requires original docx and rebuilt docx as inputs
- [ ] Unit tests with known good/bad document pairs
- [ ] Typecheck passes

### US-012: Implement cost calculator
**Description:** As a benchmark runner, I need cost calculation so we can show dollar savings.

**Acceptance Criteria:**
- [ ] `metrics/cost_calculator.py` implements `CostCalculator` class
- [ ] Calculates LLM cost: `(input_tokens × $0.003/1K) + (output_tokens × $0.015/1K)`
- [ ] Adds Document Intelligence cost when applicable (~$0.01-0.05 per page)
- [ ] Returns itemized breakdown and total cost
- [ ] Configurable pricing (for different models/tiers)
- [ ] Unit tests verify calculations
- [ ] Typecheck passes

### US-013: Implement benchmark runner
**Description:** As a benchmark user, I need a single entry point to run the complete benchmark.

**Acceptance Criteria:**
- [ ] `benchmarks/run_benchmark.py` is the main entry point
- [ ] `python run_benchmark.py` runs all pipelines × all tasks × all documents
- [ ] `--pipeline sidedoc` filters to specific pipeline
- [ ] `--task summarize` filters to specific task
- [ ] `--corpus synthetic` or `--corpus real` filters documents
- [ ] Progress displayed during execution
- [ ] Results saved to `results/benchmark-{timestamp}.json`
- [ ] Exit code 0 on success, non-zero on failure
- [ ] Typecheck passes

### US-014: Implement report generator
**Description:** As a benchmark user, I need auto-generated reports so results are immediately presentable.

**Acceptance Criteria:**
- [ ] `benchmarks/generate_report.py` reads results JSON and generates report
- [ ] Generates `results/report-{timestamp}.md` (Markdown whitepaper)
- [ ] Report includes: executive summary, methodology, results tables, visual comparisons, conclusions
- [ ] Token efficiency table: pipeline × avg read/context/edit tokens
- [ ] Format fidelity table: pipeline × structural/style/visual/total scores
- [ ] Cost analysis table: pipeline × task × per-document and total costs
- [ ] Embeds or links PNG visual comparisons
- [ ] Report is publication-ready (professional formatting)
- [ ] Typecheck passes

### US-015: Create comprehensive documentation
**Description:** As an external user, I need documentation so I can reproduce the benchmark myself.

**Acceptance Criteria:**
- [ ] `benchmarks/README.md` includes: overview, installation, prerequisites, usage, interpreting results
- [ ] Prerequisites section lists: Python 3.11+, Pandoc, LibreOffice, Azure credentials
- [ ] Installation section has copy-paste commands
- [ ] Usage section shows all CLI options with examples
- [ ] Troubleshooting section covers common issues
- [ ] LICENSE file confirms open-source license (MIT)
- [ ] Example output included or linked

## Functional Requirements

- **FR-1:** Benchmark must compare exactly 4 pipelines: Sidedoc, Document Intelligence, Pandoc, Raw docx
- **FR-2:** Benchmark must run exactly 3 task types: summarize, single-edit, multi-turn (3 rounds)
- **FR-3:** Benchmark must use 10 test documents: 5 synthetic fixtures + 5 real-world public domain
- **FR-4:** All Claude API calls must use real API (not mocked) for accurate token counts
- **FR-5:** Document Intelligence must use real Azure API for accurate cost measurement
- **FR-6:** Results JSON must include all raw metrics for each pipeline × task × document combination
- **FR-7:** Report generator must produce Markdown suitable for conversion to PDF
- **FR-8:** Benchmark must be runnable with `pip install -e .` and documented prerequisites
- **FR-9:** Format fidelity scoring must produce visual diff PNGs for human verification
- **FR-10:** Cost calculations must reflect current Claude and Azure pricing (configurable)

## Non-Goals (Out of Scope)

- GUI or web interface for running benchmarks
- Support for document formats other than .docx
- Comparison against other LLMs (GPT-4, etc.) - Claude only for MVP
- Real-time or streaming benchmark execution
- Cloud-hosted benchmark service
- Statistical significance testing (simple averages for MVP)
- Benchmarking Sidedoc's extract/build performance (only AI interaction costs)

## Technical Considerations

### Dependencies
```
# Core
pytest>=7.0
click>=8.0
python-docx>=0.8
tiktoken>=0.5

# Azure
azure-ai-formrecognizer>=3.3

# Pandoc
pypandoc>=1.11

# Visual diff
pdf2image>=1.16
imagehash>=4.3
Pillow>=10.0

# LLM
anthropic>=0.18
```

### External Requirements
- **Pandoc:** Must be installed separately (`brew install pandoc` or equivalent)
- **LibreOffice:** Must be installed for PDF→DOCX conversion (`soffice` command)
- **Azure subscription:** Required for Document Intelligence (costs ~$1-5 per full benchmark run)
- **Claude API key:** Required for all task execution

### Environment Variables
```bash
ANTHROPIC_API_KEY=sk-ant-...
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://....cognitiveservices.azure.com/
AZURE_DOCUMENT_INTELLIGENCE_KEY=...
```

## Success Metrics

- Benchmark completes all 4 pipelines × 3 tasks × 10 documents without errors
- Sidedoc demonstrates ≥50% token reduction vs Document Intelligence
- Sidedoc demonstrates ≥90% format fidelity score
- Report auto-generation produces publication-ready Markdown
- External user can reproduce benchmark following README instructions
- Full benchmark run completes in under 30 minutes

## Open Questions

1. Should we include confidence intervals or just report averages?
2. What Claude model should be used (Sonnet vs Opus)? Affects pricing.
3. Should the report include cost projections at scale (e.g., "1000 docs/month")?
4. Should we version the benchmark results for tracking improvements over time?
