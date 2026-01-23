"""Fidelity scorer utility (US-013 to US-016).

This module provides format fidelity scoring for comparing
original and rebuilt documents.
"""

import random
import subprocess
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any, Union

from docx import Document
from docx.oxml.ns import qn

if TYPE_CHECKING:
    from docx.text.paragraph import Paragraph
    from PIL.Image import Image


class FidelityScorer:
    """Scorer for measuring format fidelity between original and rebuilt documents.

    Supports scoring:
    - Structural fidelity (heading, paragraph, list counts)
    - Style fidelity (font name, size, bold, italic)
    - Visual fidelity (perceptual hash comparison)
    - Combined weighted score
    """

    def __init__(self) -> None:
        """Initialize the fidelity scorer."""
        pass

    def score_structure(
        self, original_docx: Union[str, Path], rebuilt_docx: Union[str, Path]
    ) -> float:
        """Score structural fidelity between two documents.

        Compares heading count, paragraph count, and list item count.
        Returns 100 if all counts match, deducts points for differences.

        Args:
            original_docx: Path to the original document.
            rebuilt_docx: Path to the rebuilt document.

        Returns:
            Score from 0 to 100.
        """
        original_path = Path(original_docx)
        rebuilt_path = Path(rebuilt_docx)

        original_counts = self._count_structure(original_path)
        rebuilt_counts = self._count_structure(rebuilt_path)

        # Calculate deductions for each structural element
        score = 100.0

        # Heading difference penalty (up to 40 points)
        heading_diff = abs(original_counts["headings"] - rebuilt_counts["headings"])
        max_headings = max(original_counts["headings"], 1)
        heading_penalty = min(40, (heading_diff / max_headings) * 40)
        score -= heading_penalty

        # Paragraph difference penalty (up to 40 points)
        para_diff = abs(original_counts["paragraphs"] - rebuilt_counts["paragraphs"])
        max_paras = max(original_counts["paragraphs"], 1)
        para_penalty = min(40, (para_diff / max_paras) * 40)
        score -= para_penalty

        # List item difference penalty (up to 20 points)
        list_diff = abs(original_counts["list_items"] - rebuilt_counts["list_items"])
        max_lists = max(original_counts["list_items"], 1)
        list_penalty = min(20, (list_diff / max_lists) * 20)
        score -= list_penalty

        return max(0.0, score)

    def _count_structure(self, docx_path: Path) -> dict[str, int]:
        """Count structural elements in a document.

        Args:
            docx_path: Path to the document.

        Returns:
            Dict with counts for headings, paragraphs, and list_items.
        """
        doc = Document(str(docx_path))

        heading_count = 0
        paragraph_count = 0
        list_item_count = 0

        for para in doc.paragraphs:
            style_name = para.style.name if para.style else ""

            if style_name.startswith("Heading"):
                heading_count += 1
            elif style_name == "List Paragraph" or self._is_list_item(para):
                list_item_count += 1
            else:
                paragraph_count += 1

        return {
            "headings": heading_count,
            "paragraphs": paragraph_count,
            "list_items": list_item_count,
        }

    def _is_list_item(self, para: Any) -> bool:
        """Check if a paragraph is a list item by examining its XML.

        Args:
            para: A python-docx paragraph object.

        Returns:
            True if the paragraph is a list item.
        """
        # Check for numPr (numbering properties) in the paragraph XML
        pPr = para._p.find(qn("w:pPr"))
        if pPr is not None:
            numPr = pPr.find(qn("w:numPr"))
            return numPr is not None
        return False

    def score_styles(
        self, original_docx: Union[str, Path], rebuilt_docx: Union[str, Path]
    ) -> float:
        """Score style fidelity between two documents.

        Samples up to 10 random paragraphs and compares font name, font size,
        bold, and italic settings.

        Args:
            original_docx: Path to the original document.
            rebuilt_docx: Path to the rebuilt document.

        Returns:
            Score from 0 to 100 based on match percentage.
        """
        original_path = Path(original_docx)
        rebuilt_path = Path(rebuilt_docx)

        original_styles = self._extract_paragraph_styles(original_path)
        rebuilt_styles = self._extract_paragraph_styles(rebuilt_path)

        # If no paragraphs with content to compare, return 100
        if not original_styles or not rebuilt_styles:
            return 100.0

        # Sample up to 10 paragraphs by index (matching positions)
        num_to_sample = min(10, len(original_styles), len(rebuilt_styles))
        if num_to_sample == 0:
            return 100.0

        # Get indices to sample (use same indices for both)
        sample_indices = list(range(min(len(original_styles), len(rebuilt_styles))))
        if len(sample_indices) > 10:
            random.seed(42)  # Fixed seed for reproducibility
            sample_indices = random.sample(sample_indices, 10)

        # Compare styles at sampled positions
        total_attributes = 0
        matching_attributes = 0

        for idx in sample_indices:
            orig_style = original_styles[idx]
            rebuilt_style = rebuilt_styles[idx]

            # Compare 4 attributes: font_name, font_size, bold, italic
            total_attributes += 4

            if orig_style["font_name"] == rebuilt_style["font_name"]:
                matching_attributes += 1
            if orig_style["font_size"] == rebuilt_style["font_size"]:
                matching_attributes += 1
            if orig_style["bold"] == rebuilt_style["bold"]:
                matching_attributes += 1
            if orig_style["italic"] == rebuilt_style["italic"]:
                matching_attributes += 1

        if total_attributes == 0:
            return 100.0

        return (matching_attributes / total_attributes) * 100

    def _extract_paragraph_styles(
        self, docx_path: Path
    ) -> list[dict[str, Any]]:
        """Extract style information from non-empty paragraphs.

        Args:
            docx_path: Path to the document.

        Returns:
            List of dicts with font_name, font_size, bold, italic for each paragraph.
        """
        doc = Document(str(docx_path))
        styles = []

        for para in doc.paragraphs:
            # Skip empty paragraphs
            if not para.text.strip():
                continue

            # Get style from first run (most representative)
            font_name = None
            font_size = None
            bold = None
            italic = None

            if para.runs:
                run = para.runs[0]
                font_name = run.font.name
                font_size = run.font.size
                bold = run.bold
                italic = run.italic

            styles.append({
                "font_name": font_name,
                "font_size": font_size,
                "bold": bold,
                "italic": italic,
            })

        return styles

    def score_visual(
        self, original_docx: Union[str, Path], rebuilt_docx: Union[str, Path]
    ) -> float:
        """Score visual fidelity between two documents.

        Renders first page of each docx to PNG and computes perceptual hash
        difference using imagehash.

        Args:
            original_docx: Path to the original document.
            rebuilt_docx: Path to the rebuilt document.

        Returns:
            Score from 0 to 100 (100 = visually identical).

        Raises:
            RuntimeError: If LibreOffice or Poppler are not available.
        """
        import imagehash
        from pdf2image import convert_from_path
        from PIL import Image

        original_path = Path(original_docx)
        rebuilt_path = Path(rebuilt_docx)

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Convert docx to PDF using LibreOffice
            original_pdf = self._convert_docx_to_pdf(original_path, tmp_path)
            rebuilt_pdf = self._convert_docx_to_pdf(rebuilt_path, tmp_path)

            # Convert first page of each PDF to image
            original_images = convert_from_path(str(original_pdf), first_page=1, last_page=1)
            rebuilt_images = convert_from_path(str(rebuilt_pdf), first_page=1, last_page=1)

            if not original_images or not rebuilt_images:
                return 0.0

            original_img = original_images[0]
            rebuilt_img = rebuilt_images[0]

            # Compute perceptual hashes
            original_hash = imagehash.phash(original_img)
            rebuilt_hash = imagehash.phash(rebuilt_img)

            # Hash difference: 0 = identical, higher = more different
            # Max possible difference for 64-bit hash is 64
            hash_diff = original_hash - rebuilt_hash

            # Convert to 0-100 score (0 diff = 100 score)
            score = max(0.0, 100 - (hash_diff / 64) * 100)

            return score

    def _convert_docx_to_pdf(self, docx_path: Path, output_dir: Path) -> Path:
        """Convert a docx file to PDF using LibreOffice.

        Args:
            docx_path: Path to the docx file.
            output_dir: Directory for output PDF.

        Returns:
            Path to the generated PDF.

        Raises:
            RuntimeError: If LibreOffice is not available.
        """
        # Try common LibreOffice paths
        soffice_paths = [
            "soffice",
            "/Applications/LibreOffice.app/Contents/MacOS/soffice",
            "/usr/bin/soffice",
            "/usr/bin/libreoffice",
        ]

        soffice_cmd = None
        for path in soffice_paths:
            try:
                subprocess.run(
                    [path, "--version"],
                    capture_output=True,
                    check=True,
                )
                soffice_cmd = path
                break
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue

        if soffice_cmd is None:
            raise RuntimeError(
                "LibreOffice (soffice) not found. Install LibreOffice for visual comparison."
            )

        # Convert docx to PDF
        subprocess.run(
            [
                soffice_cmd,
                "--headless",
                "--convert-to", "pdf",
                "--outdir", str(output_dir),
                str(docx_path),
            ],
            capture_output=True,
            check=True,
        )

        # Return path to generated PDF
        pdf_path = output_dir / f"{docx_path.stem}.pdf"
        return pdf_path

    def score_total(
        self, original_docx: Union[str, Path], rebuilt_docx: Union[str, Path]
    ) -> dict[str, float | None]:
        """Compute combined fidelity score with weighted components.

        Uses weights: 0.3*structural + 0.3*style + 0.4*visual.
        If visual scoring is unavailable, uses 0.5*structural + 0.5*style.

        Args:
            original_docx: Path to the original document.
            rebuilt_docx: Path to the rebuilt document.

        Returns:
            Dict with individual scores (structural, style, visual) and total.
            Visual may be None if dependencies are not available.
        """
        structural = self.score_structure(original_docx, rebuilt_docx)
        style = self.score_styles(original_docx, rebuilt_docx)

        visual: float | None = None
        try:
            visual = self.score_visual(original_docx, rebuilt_docx)
        except Exception:
            # Visual scoring not available (missing LibreOffice/Poppler)
            pass

        if visual is not None:
            total = 0.3 * structural + 0.3 * style + 0.4 * visual
        else:
            # Fallback: equal weight to structural and style
            total = 0.5 * structural + 0.5 * style

        return {
            "structural": structural,
            "style": style,
            "visual": visual,
            "total": total,
        }
