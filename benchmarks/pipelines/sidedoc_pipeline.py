"""Sidedoc pipeline implementation (US-006).

This pipeline uses the Sidedoc format for document processing.
It extracts content to markdown, applies edits, and rebuilds documents
while preserving original formatting.
"""

import hashlib
import json
import tempfile
import time
import zipfile
from pathlib import Path
from typing import Optional, Self

from benchmarks.metrics.token_counter import TokenCounter
from benchmarks.pipelines.base import BasePipeline, PipelineResult
from sidedoc.extract import extract_blocks, extract_styles, blocks_to_markdown
from sidedoc.package import create_sidedoc_archive
from sidedoc.models import Block
from sidedoc.sync import match_blocks, generate_updated_docx


def _compute_content_hash(content: str) -> str:
    """Compute SHA256 hash of content."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _generate_block_id(index: int) -> str:
    """Generate a unique block ID."""
    return f"block-{index}"


def _parse_markdown_to_blocks(markdown: str) -> list[Block]:
    """Parse markdown content into Block objects.

    Args:
        markdown: Markdown content string.

    Returns:
        List of Block objects.
    """
    lines = markdown.split("\n")
    blocks: list[Block] = []
    content_position = 0

    for i, line in enumerate(lines):
        # Determine block type from content
        if line.startswith("#"):
            block_type = "heading"
            # Count heading level
            level = 0
            for char in line:
                if char == "#":
                    level += 1
                else:
                    break
            level_value: Optional[int] = level
        elif line.startswith("- ") or line.startswith("* "):
            block_type = "list"
            level_value = None
        elif line and line[0].isdigit() and ". " in line[:4]:
            block_type = "list"
            level_value = None
        elif line.startswith("!["):
            block_type = "image"
            level_value = None
        else:
            block_type = "paragraph"
            level_value = None

        content_start = content_position
        content_end = content_position + len(line)

        block = Block(
            id=_generate_block_id(i),
            type=block_type,
            content=line,
            docx_paragraph_index=i,
            content_start=content_start,
            content_end=content_end,
            content_hash=_compute_content_hash(line),
            level=level_value,
            inline_formatting=None,
            image_path=None,
        )

        blocks.append(block)
        content_position = content_end + 1  # +1 for newline

    return blocks


class SidedocPipeline(BasePipeline):
    """Pipeline that uses Sidedoc format for document processing.

    This pipeline:
    1. Extracts content from docx to sidedoc format (markdown + metadata)
    2. Allows editing of the markdown content
    3. Rebuilds the docx using sync to preserve formatting
    """

    def __init__(self) -> None:
        """Initialize the Sidedoc pipeline."""
        self._sidedoc_path: Optional[Path] = None
        self._current_content: str = ""
        self._temp_dir: Optional[tempfile.TemporaryDirectory[str]] = None
        self._token_counter = TokenCounter()

    def __enter__(self) -> Self:
        """Enter context manager."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Exit context manager, ensuring cleanup is called."""
        self.cleanup()

    def extract_content(self, document_path: Path) -> str:
        """Extract text content from a document using sidedoc.

        Args:
            document_path: Path to the document to extract from.

        Returns:
            The extracted text content as markdown.
        """
        # Create a temporary directory for sidedoc file
        self._temp_dir = tempfile.TemporaryDirectory()
        self._sidedoc_path = Path(self._temp_dir.name) / f"{document_path.stem}.sidedoc"

        # Extract blocks and styles from the docx
        blocks, image_data = extract_blocks(str(document_path))
        styles = extract_styles(str(document_path), blocks)

        # Convert blocks to markdown
        markdown_content: str = blocks_to_markdown(blocks)

        # Create the sidedoc archive
        create_sidedoc_archive(
            str(self._sidedoc_path),
            markdown_content,
            blocks,
            styles,
            str(document_path),
            image_data,
        )

        self._current_content = markdown_content
        return markdown_content

    def apply_edit(self, content: str, edit_instruction: str) -> str:
        """Apply an edit to the content.

        For the Sidedoc pipeline, the edit_instruction is simply appended
        to the content (or used as a replacement if it looks like full content).

        Args:
            content: The original text content.
            edit_instruction: The edit to apply (appended to content).

        Returns:
            The edited content as a string.
        """
        # Simple implementation: append the edit instruction
        edited_content = content + edit_instruction

        # Update the sidedoc archive with new content
        if self._sidedoc_path and self._sidedoc_path.exists():
            self._update_sidedoc_content(edited_content)

        self._current_content = edited_content
        return edited_content

    def _update_sidedoc_content(self, new_content: str) -> None:
        """Update the content.md in the sidedoc archive.

        Args:
            new_content: The new markdown content.
        """
        if not self._sidedoc_path:
            return

        # Read existing archive
        with zipfile.ZipFile(self._sidedoc_path, "r") as zip_file:
            structure_json = zip_file.read("structure.json").decode("utf-8")
            styles_json = zip_file.read("styles.json").decode("utf-8")
            manifest_json = zip_file.read("manifest.json").decode("utf-8")

            # Collect assets
            assets: dict[str, bytes] = {}
            for file_info in zip_file.filelist:
                if file_info.filename.startswith("assets/"):
                    assets[file_info.filename] = zip_file.read(file_info.filename)

        # Parse new content into blocks
        new_blocks = _parse_markdown_to_blocks(new_content)

        # Update structure.json
        structure_data = {
            "blocks": [
                {
                    "id": block.id,
                    "type": block.type,
                    "docx_paragraph_index": block.docx_paragraph_index,
                    "content_start": block.content_start,
                    "content_end": block.content_end,
                    "content_hash": block.content_hash,
                    "level": block.level,
                    "image_path": block.image_path,
                    "inline_formatting": block.inline_formatting,
                }
                for block in new_blocks
            ]
        }

        # Update manifest with new content hash
        manifest_data = json.loads(manifest_json)
        manifest_data["content_hash"] = _compute_content_hash(new_content)

        # Rewrite archive
        with zipfile.ZipFile(self._sidedoc_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr("content.md", new_content)
            zip_file.writestr("structure.json", json.dumps(structure_data, indent=2))
            zip_file.writestr("styles.json", styles_json)
            zip_file.writestr("manifest.json", json.dumps(manifest_data, indent=2))

            # Preserve assets
            for asset_path, asset_data in assets.items():
                zip_file.writestr(asset_path, asset_data)

    def rebuild_document(
        self, content: str, original_path: Path, output_path: Path
    ) -> PipelineResult:
        """Rebuild a document from edited content.

        Args:
            content: The edited text content.
            original_path: Path to the original document (for reference).
            output_path: Path where the rebuilt document should be saved.

        Returns:
            PipelineResult with metrics and status.
        """
        start_time = time.time()

        try:
            # Parse new content into blocks
            new_blocks = _parse_markdown_to_blocks(content)

            # Read structure and styles from sidedoc
            if self._sidedoc_path and self._sidedoc_path.exists():
                with zipfile.ZipFile(self._sidedoc_path, "r") as zip_file:
                    structure_data = json.loads(zip_file.read("structure.json").decode("utf-8"))
                    styles_data = json.loads(zip_file.read("styles.json").decode("utf-8"))

                # Reconstruct old blocks from structure
                old_blocks = [
                    Block(
                        id=b["id"],
                        type=b["type"],
                        content="",  # Content not needed for matching
                        docx_paragraph_index=b["docx_paragraph_index"],
                        content_start=b["content_start"],
                        content_end=b["content_end"],
                        content_hash=b["content_hash"],
                        level=b.get("level"),
                        inline_formatting=b.get("inline_formatting"),
                        image_path=b.get("image_path"),
                    )
                    for b in structure_data["blocks"]
                ]

                # Match old blocks to new blocks
                matches = match_blocks(old_blocks, new_blocks)

                # Generate the updated docx
                generate_updated_docx(new_blocks, matches, styles_data, str(output_path))
            else:
                # No sidedoc available, extract fresh
                blocks, _ = extract_blocks(str(original_path))
                matches = match_blocks(blocks, new_blocks)
                styles = extract_styles(str(original_path), blocks)

                styles_data = {
                    "block_styles": {
                        style.block_id: {
                            "docx_style": style.docx_style,
                            "font_name": style.font_name,
                            "font_size": style.font_size,
                            "alignment": style.alignment,
                        }
                        for style in styles
                    }
                }

                generate_updated_docx(new_blocks, matches, styles_data, str(output_path))

            elapsed = time.time() - start_time

            # Calculate token counts using tiktoken
            input_tokens = self._token_counter.count_tokens(content)
            output_tokens = input_tokens  # Output is similar size

            return PipelineResult(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                time_elapsed=elapsed,
                output_path=output_path,
                error=None,
            )

        except Exception as e:
            elapsed = time.time() - start_time
            return PipelineResult(
                input_tokens=0,
                output_tokens=0,
                time_elapsed=elapsed,
                output_path=None,
                error=str(e),
            )

    def cleanup(self) -> None:
        """Clean up temporary files."""
        if self._temp_dir:
            self._temp_dir.cleanup()
            self._temp_dir = None
            self._sidedoc_path = None
