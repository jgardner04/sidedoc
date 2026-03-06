# Sidedoc Benchmark Report

Generated: 2026-03-05T23:27:28.063316

## Executive Summary

### Key Findings

- **Token Efficiency**: Sidedoc reduces token usage by -56.9% compared to baseline

- **Format Fidelity**: Sidedoc preserves document formatting while alternatives may lose structure

- **Cost Savings**: Lower token usage translates to reduced API costs

## Methodology

### Test Corpus

- Corpus type: synthetic

- Total documents: 15


### Pipelines Compared

- **sidedoc**: AI-native format that separates content from formatting

- **pandoc**: Universal document converter (docx to markdown)

- **raw_docx**: Raw DOCX paragraph extraction (baseline)


### Tasks Executed

- **summarize**: Generate 3-5 bullet point summary

- **edit_single**: Apply single edit instruction

- **edit_multiturn**: Apply 3 sequential edits

## Results

### Token Efficiency

| Pipeline | Prompt Tokens | Completion Tokens | Total Tokens |

|----------|---------------|-------------------|---------------|

| sidedoc | 208 | 171 | 379 |

| pandoc | 240 | 197 | 438 |

| raw_docx | 132 | 109 | 242 |



### Format Fidelity

*Fidelity scores require visual comparison tools (LibreOffice, Poppler)*


### Cost Analysis

| Pipeline | Est. Cost (per doc) |

|----------|---------------------|

| sidedoc | $0.0032 |

| pandoc | $0.0037 |

| raw_docx | $0.0020 |

## Conclusions

### Best Performing Pipeline

**raw_docx** achieved the lowest token usage overall.


### Recommendations

- **Use Sidedoc** for documents where format preservation is important

- **Use Pandoc** for quick conversions where formatting loss is acceptable

- **Avoid Raw DOCX** for LLM tasks due to high token overhead
