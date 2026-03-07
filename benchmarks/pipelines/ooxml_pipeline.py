"""Raw OOXML pipeline implementation.

This pipeline extracts the full XML content from docx files —
all .xml and .rels files inside the ZIP archive. This represents
what you'd need to send to an LLM for a format-preserving round-trip
without a purpose-built intermediate format like Sidedoc.
"""

import os
import re
import zipfile
from pathlib import Path

from benchmarks.metrics.token_counter import TokenCounter
from benchmarks.pipelines.base import BasePipeline, PipelineResult


class OoxmlPipeline(BasePipeline):
    """Pipeline that sends raw OOXML to the LLM.

    Extracts all XML content from the .docx ZIP archive (document.xml,
    styles.xml, numbering.xml, theme, rels, etc.) and concatenates it.
    This is the content an LLM would need to see for a format-preserving
    round-trip edit without an intermediate format.
    """

    def __init__(self) -> None:
        self._current_content: str = ""
        self._token_counter = TokenCounter()

    def extract_content(self, document_path: Path) -> str:
        """Extract all XML content from the .docx archive.

        Args:
            document_path: Path to the .docx file.

        Returns:
            Concatenated XML content from all .xml and .rels files.
        """
        parts: list[str] = []

        with zipfile.ZipFile(document_path) as z:
            for name in sorted(z.namelist()):
                # Reject path traversal attempts (forward and backslash)
                normalized = name.replace("\\", "/")
                if os.path.isabs(normalized) or ".." in normalized.split("/"):
                    continue
                if name.endswith(".xml") or name.endswith(".rels"):
                    content = z.read(name).decode("utf-8", errors="ignore")
                    safe_name = re.sub(r"[^a-zA-Z0-9/._\[\]-]", "_", name)
                    parts.append(f"<!-- {safe_name} -->\n{content}")

        self._current_content = "\n\n".join(parts)
        return self._current_content

    def apply_edit(self, content: str, edit_instruction: str) -> str:
        """No-op — OOXML round-trip editing is not implemented."""
        return content

    def rebuild_document(
        self, content: str, original_path: Path, output_path: Path
    ) -> PipelineResult:
        """Not supported — baseline for token comparison only."""
        # No rebuild work performed
        input_tokens = self._token_counter.count_tokens(content)

        return PipelineResult(
            input_tokens=input_tokens,
            output_tokens=0,
            time_elapsed=0.0,
            output_path=None,
            error="OOXML pipeline cannot rebuild documents (baseline for comparison only)",
        )
