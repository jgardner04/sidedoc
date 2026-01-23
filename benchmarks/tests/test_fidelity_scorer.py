"""Tests for fidelity scorer utility (US-013 to US-016)."""

import shutil
import tempfile
from pathlib import Path

import pytest
from docx import Document


BENCHMARKS_DIR = Path(__file__).parent.parent
FIXTURES_DIR = BENCHMARKS_DIR / "corpus" / "synthetic"


class TestFidelityStructuralScorer:
    """Test the structural fidelity scorer (US-013)."""

    def test_module_exists(self) -> None:
        """Test that fidelity_scorer.py exists."""
        module_path = BENCHMARKS_DIR / "metrics" / "fidelity_scorer.py"
        assert module_path.exists(), "benchmarks/metrics/fidelity_scorer.py does not exist"

    def test_fidelity_scorer_is_importable(self) -> None:
        """Test that FidelityScorer can be imported."""
        from benchmarks.metrics.fidelity_scorer import FidelityScorer

        assert FidelityScorer is not None

    def test_score_structure_returns_numeric(self) -> None:
        """Test that score_structure returns a 0-100 score."""
        from benchmarks.metrics.fidelity_scorer import FidelityScorer

        scorer = FidelityScorer()
        simple_docx = FIXTURES_DIR / "simple.docx"

        # Comparing a document to itself should return 100
        score = scorer.score_structure(simple_docx, simple_docx)

        assert isinstance(score, (int, float))
        assert 0 <= score <= 100

    def test_identical_documents_score_100(self) -> None:
        """Test that identical documents get a perfect structural score."""
        from benchmarks.metrics.fidelity_scorer import FidelityScorer

        scorer = FidelityScorer()
        simple_docx = FIXTURES_DIR / "simple.docx"

        score = scorer.score_structure(simple_docx, simple_docx)

        assert score == 100

    def test_different_heading_counts_reduce_score(self) -> None:
        """Test that different heading counts reduce the score."""
        from benchmarks.metrics.fidelity_scorer import FidelityScorer

        scorer = FidelityScorer()

        # Create two temporary documents with different heading counts
        with tempfile.TemporaryDirectory() as tmp_dir:
            original_path = Path(tmp_dir) / "original.docx"
            rebuilt_path = Path(tmp_dir) / "rebuilt.docx"

            # Original: 2 headings
            doc1 = Document()
            doc1.add_heading("Heading 1", level=1)
            doc1.add_paragraph("Content 1")
            doc1.add_heading("Heading 2", level=2)
            doc1.add_paragraph("Content 2")
            doc1.save(str(original_path))

            # Rebuilt: 1 heading (missing one)
            doc2 = Document()
            doc2.add_heading("Heading 1", level=1)
            doc2.add_paragraph("Content 1")
            doc2.add_paragraph("Content 2")  # No heading here
            doc2.save(str(rebuilt_path))

            score = scorer.score_structure(original_path, rebuilt_path)

            assert score < 100

    def test_different_paragraph_counts_reduce_score(self) -> None:
        """Test that different paragraph counts reduce the score."""
        from benchmarks.metrics.fidelity_scorer import FidelityScorer

        scorer = FidelityScorer()

        with tempfile.TemporaryDirectory() as tmp_dir:
            original_path = Path(tmp_dir) / "original.docx"
            rebuilt_path = Path(tmp_dir) / "rebuilt.docx"

            # Original: 3 paragraphs
            doc1 = Document()
            doc1.add_paragraph("Paragraph 1")
            doc1.add_paragraph("Paragraph 2")
            doc1.add_paragraph("Paragraph 3")
            doc1.save(str(original_path))

            # Rebuilt: 2 paragraphs
            doc2 = Document()
            doc2.add_paragraph("Paragraph 1")
            doc2.add_paragraph("Paragraph 2")
            doc2.save(str(rebuilt_path))

            score = scorer.score_structure(original_path, rebuilt_path)

            assert score < 100

    def test_different_list_item_counts_reduce_score(self) -> None:
        """Test that different list item counts reduce the score."""
        from benchmarks.metrics.fidelity_scorer import FidelityScorer

        scorer = FidelityScorer()
        lists_docx = FIXTURES_DIR / "lists.docx"

        with tempfile.TemporaryDirectory() as tmp_dir:
            rebuilt_path = Path(tmp_dir) / "rebuilt.docx"

            # Create a document with fewer list items
            doc = Document()
            doc.add_paragraph("Just a paragraph, no lists")
            doc.save(str(rebuilt_path))

            score = scorer.score_structure(lists_docx, rebuilt_path)

            # Should be less than 100 due to missing list items
            assert score < 100

    def test_score_never_negative(self) -> None:
        """Test that the score is never negative."""
        from benchmarks.metrics.fidelity_scorer import FidelityScorer

        scorer = FidelityScorer()

        with tempfile.TemporaryDirectory() as tmp_dir:
            original_path = Path(tmp_dir) / "original.docx"
            rebuilt_path = Path(tmp_dir) / "rebuilt.docx"

            # Original: lots of structure
            doc1 = Document()
            for i in range(10):
                doc1.add_heading(f"Heading {i}", level=1)
                doc1.add_paragraph(f"Paragraph {i}")
            doc1.save(str(original_path))

            # Rebuilt: minimal structure
            doc2 = Document()
            doc2.add_paragraph("Minimal content")
            doc2.save(str(rebuilt_path))

            score = scorer.score_structure(original_path, rebuilt_path)

            assert score >= 0

    def test_accepts_path_strings(self) -> None:
        """Test that score_structure accepts string paths."""
        from benchmarks.metrics.fidelity_scorer import FidelityScorer

        scorer = FidelityScorer()
        simple_docx = str(FIXTURES_DIR / "simple.docx")

        score = scorer.score_structure(simple_docx, simple_docx)

        assert score == 100


class TestFidelityStyleScorer:
    """Test the style fidelity scorer (US-014)."""

    def test_score_styles_method_exists(self) -> None:
        """Test that score_styles method exists on FidelityScorer."""
        from benchmarks.metrics.fidelity_scorer import FidelityScorer

        scorer = FidelityScorer()
        assert hasattr(scorer, "score_styles")
        assert callable(getattr(scorer, "score_styles"))

    def test_score_styles_returns_numeric(self) -> None:
        """Test that score_styles returns a 0-100 score."""
        from benchmarks.metrics.fidelity_scorer import FidelityScorer

        scorer = FidelityScorer()
        formatted_docx = FIXTURES_DIR / "formatted.docx"

        score = scorer.score_styles(formatted_docx, formatted_docx)

        assert isinstance(score, (int, float))
        assert 0 <= score <= 100

    def test_identical_documents_score_100(self) -> None:
        """Test that identical documents get a perfect style score."""
        from benchmarks.metrics.fidelity_scorer import FidelityScorer

        scorer = FidelityScorer()
        formatted_docx = FIXTURES_DIR / "formatted.docx"

        score = scorer.score_styles(formatted_docx, formatted_docx)

        assert score == 100

    def test_different_font_reduces_score(self) -> None:
        """Test that different font names reduce the score."""
        from benchmarks.metrics.fidelity_scorer import FidelityScorer

        scorer = FidelityScorer()

        with tempfile.TemporaryDirectory() as tmp_dir:
            original_path = Path(tmp_dir) / "original.docx"
            rebuilt_path = Path(tmp_dir) / "rebuilt.docx"

            # Original: Arial font
            doc1 = Document()
            para = doc1.add_paragraph()
            run = para.add_run("Test content")
            run.font.name = "Arial"
            doc1.save(str(original_path))

            # Rebuilt: Times New Roman font
            doc2 = Document()
            para = doc2.add_paragraph()
            run = para.add_run("Test content")
            run.font.name = "Times New Roman"
            doc2.save(str(rebuilt_path))

            score = scorer.score_styles(original_path, rebuilt_path)

            assert score < 100

    def test_different_bold_reduces_score(self) -> None:
        """Test that different bold settings reduce the score."""
        from benchmarks.metrics.fidelity_scorer import FidelityScorer

        scorer = FidelityScorer()

        with tempfile.TemporaryDirectory() as tmp_dir:
            original_path = Path(tmp_dir) / "original.docx"
            rebuilt_path = Path(tmp_dir) / "rebuilt.docx"

            # Original: bold text
            doc1 = Document()
            para = doc1.add_paragraph()
            run = para.add_run("Test content")
            run.bold = True
            doc1.save(str(original_path))

            # Rebuilt: no bold
            doc2 = Document()
            para = doc2.add_paragraph()
            run = para.add_run("Test content")
            run.bold = False
            doc2.save(str(rebuilt_path))

            score = scorer.score_styles(original_path, rebuilt_path)

            assert score < 100

    def test_different_italic_reduces_score(self) -> None:
        """Test that different italic settings reduce the score."""
        from benchmarks.metrics.fidelity_scorer import FidelityScorer

        scorer = FidelityScorer()

        with tempfile.TemporaryDirectory() as tmp_dir:
            original_path = Path(tmp_dir) / "original.docx"
            rebuilt_path = Path(tmp_dir) / "rebuilt.docx"

            # Original: italic text
            doc1 = Document()
            para = doc1.add_paragraph()
            run = para.add_run("Test content")
            run.italic = True
            doc1.save(str(original_path))

            # Rebuilt: no italic
            doc2 = Document()
            para = doc2.add_paragraph()
            run = para.add_run("Test content")
            run.italic = False
            doc2.save(str(rebuilt_path))

            score = scorer.score_styles(original_path, rebuilt_path)

            assert score < 100

    def test_different_font_size_reduces_score(self) -> None:
        """Test that different font sizes reduce the score."""
        from benchmarks.metrics.fidelity_scorer import FidelityScorer
        from docx.shared import Pt

        scorer = FidelityScorer()

        with tempfile.TemporaryDirectory() as tmp_dir:
            original_path = Path(tmp_dir) / "original.docx"
            rebuilt_path = Path(tmp_dir) / "rebuilt.docx"

            # Original: 12pt font
            doc1 = Document()
            para = doc1.add_paragraph()
            run = para.add_run("Test content")
            run.font.size = Pt(12)
            doc1.save(str(original_path))

            # Rebuilt: 24pt font
            doc2 = Document()
            para = doc2.add_paragraph()
            run = para.add_run("Test content")
            run.font.size = Pt(24)
            doc2.save(str(rebuilt_path))

            score = scorer.score_styles(original_path, rebuilt_path)

            assert score < 100

    def test_score_styles_samples_up_to_10_paragraphs(self) -> None:
        """Test that score_styles works with documents with more than 10 paragraphs."""
        from benchmarks.metrics.fidelity_scorer import FidelityScorer

        scorer = FidelityScorer()

        with tempfile.TemporaryDirectory() as tmp_dir:
            doc_path = Path(tmp_dir) / "many_paras.docx"

            # Create document with 20 paragraphs
            doc = Document()
            for i in range(20):
                para = doc.add_paragraph()
                run = para.add_run(f"Paragraph {i}")
                run.bold = True
            doc.save(str(doc_path))

            # Should not raise even with many paragraphs
            score = scorer.score_styles(doc_path, doc_path)

            assert score == 100

    def test_score_styles_handles_empty_paragraphs(self) -> None:
        """Test that score_styles handles documents with empty paragraphs."""
        from benchmarks.metrics.fidelity_scorer import FidelityScorer

        scorer = FidelityScorer()

        with tempfile.TemporaryDirectory() as tmp_dir:
            doc_path = Path(tmp_dir) / "empty_paras.docx"

            # Create document with empty paragraphs
            doc = Document()
            doc.add_paragraph()  # Empty
            doc.add_paragraph("Content")
            doc.add_paragraph()  # Empty
            doc.save(str(doc_path))

            # Should not raise with empty paragraphs
            score = scorer.score_styles(doc_path, doc_path)

            assert score >= 0

    def test_score_styles_accepts_path_strings(self) -> None:
        """Test that score_styles accepts string paths."""
        from benchmarks.metrics.fidelity_scorer import FidelityScorer

        scorer = FidelityScorer()
        formatted_docx = str(FIXTURES_DIR / "formatted.docx")

        score = scorer.score_styles(formatted_docx, formatted_docx)

        assert score == 100


def visual_scorer_available() -> bool:
    """Check if visual scoring dependencies (LibreOffice, Poppler) are available."""
    import shutil
    import subprocess

    # Check for LibreOffice
    soffice_paths = [
        "soffice",
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
        "/usr/bin/soffice",
        "/usr/bin/libreoffice",
    ]
    has_libreoffice = False
    for path in soffice_paths:
        if shutil.which(path):
            has_libreoffice = True
            break

    # Check for Poppler (pdfinfo)
    has_poppler = shutil.which("pdfinfo") is not None

    return has_libreoffice and has_poppler


visual_scorer_skip = pytest.mark.skipif(
    not visual_scorer_available(),
    reason="Visual scoring requires LibreOffice and Poppler (pdfinfo)"
)


class TestFidelityVisualScorer:
    """Test the visual fidelity scorer (US-015)."""

    def test_score_visual_method_exists(self) -> None:
        """Test that score_visual method exists on FidelityScorer."""
        from benchmarks.metrics.fidelity_scorer import FidelityScorer

        scorer = FidelityScorer()
        assert hasattr(scorer, "score_visual")
        assert callable(getattr(scorer, "score_visual"))

    @visual_scorer_skip
    def test_score_visual_returns_numeric(self) -> None:
        """Test that score_visual returns a 0-100 score."""
        from benchmarks.metrics.fidelity_scorer import FidelityScorer

        scorer = FidelityScorer()
        simple_docx = FIXTURES_DIR / "simple.docx"

        score = scorer.score_visual(simple_docx, simple_docx)

        assert isinstance(score, (int, float))
        assert 0 <= score <= 100

    @visual_scorer_skip
    def test_identical_documents_score_high(self) -> None:
        """Test that identical documents get a high visual score."""
        from benchmarks.metrics.fidelity_scorer import FidelityScorer

        scorer = FidelityScorer()
        simple_docx = FIXTURES_DIR / "simple.docx"

        score = scorer.score_visual(simple_docx, simple_docx)

        # Identical documents should score 100 or very close
        assert score >= 95

    @visual_scorer_skip
    def test_different_documents_score_lower(self) -> None:
        """Test that visually different documents get a lower score."""
        from benchmarks.metrics.fidelity_scorer import FidelityScorer

        scorer = FidelityScorer()

        with tempfile.TemporaryDirectory() as tmp_dir:
            doc1_path = Path(tmp_dir) / "doc1.docx"
            doc2_path = Path(tmp_dir) / "doc2.docx"

            # Create two documents with very different content
            doc1 = Document()
            doc1.add_heading("Title One", level=1)
            doc1.add_paragraph("This is the first document with specific content.")
            doc1.save(str(doc1_path))

            doc2 = Document()
            doc2.add_heading("Different Title", level=1)
            doc2.add_paragraph("Completely different text that looks nothing alike.")
            doc2.add_paragraph("Even more content that makes them different.")
            doc2.save(str(doc2_path))

            score = scorer.score_visual(doc1_path, doc2_path)

            # Different documents should score lower
            assert score < 100

    @visual_scorer_skip
    def test_score_visual_accepts_path_strings(self) -> None:
        """Test that score_visual accepts string paths."""
        from benchmarks.metrics.fidelity_scorer import FidelityScorer

        scorer = FidelityScorer()
        simple_docx = str(FIXTURES_DIR / "simple.docx")

        score = scorer.score_visual(simple_docx, simple_docx)

        assert score >= 95

    def test_score_visual_handles_missing_dependencies(self) -> None:
        """Test that score_visual raises clear error for missing dependencies."""
        from benchmarks.metrics.fidelity_scorer import FidelityScorer

        scorer = FidelityScorer()
        simple_docx = FIXTURES_DIR / "simple.docx"

        # Either succeeds (dependencies available) or raises clear error
        try:
            score = scorer.score_visual(simple_docx, simple_docx)
            assert 0 <= score <= 100
        except Exception as e:
            error_msg = str(e).lower()
            # Should mention missing dependency
            assert (
                "poppler" in error_msg
                or "libreoffice" in error_msg
                or "soffice" in error_msg
                or "pdfinfo" in error_msg
            )


class TestFidelityCombinedScorer:
    """Test the combined fidelity scorer (US-016)."""

    def test_score_total_method_exists(self) -> None:
        """Test that score_total method exists on FidelityScorer."""
        from benchmarks.metrics.fidelity_scorer import FidelityScorer

        scorer = FidelityScorer()
        assert hasattr(scorer, "score_total")
        assert callable(getattr(scorer, "score_total"))

    def test_score_total_returns_dict(self) -> None:
        """Test that score_total returns a dict with individual scores and total."""
        from benchmarks.metrics.fidelity_scorer import FidelityScorer

        scorer = FidelityScorer()
        simple_docx = FIXTURES_DIR / "simple.docx"

        result = scorer.score_total(simple_docx, simple_docx)

        assert isinstance(result, dict)
        assert "structural" in result
        assert "style" in result
        assert "visual" in result
        assert "total" in result

    def test_score_total_returns_numeric_scores(self) -> None:
        """Test that all scores in the result are numeric 0-100."""
        from benchmarks.metrics.fidelity_scorer import FidelityScorer

        scorer = FidelityScorer()
        simple_docx = FIXTURES_DIR / "simple.docx"

        result = scorer.score_total(simple_docx, simple_docx)

        for key in ["structural", "style", "total"]:
            assert isinstance(result[key], (int, float))
            assert 0 <= result[key] <= 100

        # Visual may be None if dependencies not available
        if result["visual"] is not None:
            assert isinstance(result["visual"], (int, float))
            assert 0 <= result["visual"] <= 100

    def test_score_total_uses_correct_weights(self) -> None:
        """Test that total uses weighted score: 0.3*structural + 0.3*style + 0.4*visual."""
        from benchmarks.metrics.fidelity_scorer import FidelityScorer

        scorer = FidelityScorer()
        simple_docx = FIXTURES_DIR / "simple.docx"

        result = scorer.score_total(simple_docx, simple_docx)

        # Calculate expected total from individual scores
        structural = result["structural"]
        style = result["style"]
        visual = result["visual"]

        if visual is not None:
            expected_total = 0.3 * structural + 0.3 * style + 0.4 * visual
            assert abs(result["total"] - expected_total) < 0.01
        else:
            # Without visual, should use only structural and style (0.5 each)
            expected_total = 0.5 * structural + 0.5 * style
            assert abs(result["total"] - expected_total) < 0.01

    def test_score_total_identical_documents_score_high(self) -> None:
        """Test that identical documents get high combined score."""
        from benchmarks.metrics.fidelity_scorer import FidelityScorer

        scorer = FidelityScorer()
        simple_docx = FIXTURES_DIR / "simple.docx"

        result = scorer.score_total(simple_docx, simple_docx)

        # Structural and style should be 100 for identical docs
        assert result["structural"] == 100
        assert result["style"] == 100
        # Total should be high (may be less than 100 if visual not available)
        assert result["total"] >= 90

    def test_score_total_accepts_path_strings(self) -> None:
        """Test that score_total accepts string paths."""
        from benchmarks.metrics.fidelity_scorer import FidelityScorer

        scorer = FidelityScorer()
        simple_docx = str(FIXTURES_DIR / "simple.docx")

        result = scorer.score_total(simple_docx, simple_docx)

        assert "total" in result
        assert result["total"] >= 90
