"""Tests for PDF to DOCX conversion script (US-004)."""

from pathlib import Path
from unittest.mock import MagicMock, patch
import tempfile

import pytest


BENCHMARKS_DIR = Path(__file__).parent.parent


class TestConvertCorpusScript:
    """Test that the convert corpus script exists and works correctly."""

    def test_script_file_exists(self) -> None:
        """Test that convert_corpus.py exists."""
        script_path = BENCHMARKS_DIR / "scripts" / "convert_corpus.py"
        assert script_path.exists(), "benchmarks/scripts/convert_corpus.py does not exist"

    def test_script_is_importable(self) -> None:
        """Test that the script module can be imported."""
        from benchmarks.scripts import convert_corpus

        assert hasattr(convert_corpus, "check_libreoffice")
        assert hasattr(convert_corpus, "convert_pdf_to_docx")
        assert hasattr(convert_corpus, "convert_corpus")

    def test_check_libreoffice_returns_path_when_installed(self) -> None:
        """Test that check_libreoffice returns path when LibreOffice is available."""
        from benchmarks.scripts.convert_corpus import check_libreoffice

        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/soffice"
            result = check_libreoffice()
            assert result == "/usr/bin/soffice"

    def test_check_libreoffice_raises_when_not_installed(self) -> None:
        """Test that check_libreoffice raises helpful error when not installed."""
        from benchmarks.scripts.convert_corpus import check_libreoffice, LibreOfficeNotFoundError

        with patch("shutil.which") as mock_which:
            mock_which.return_value = None
            with patch("pathlib.Path.exists") as mock_exists:
                mock_exists.return_value = False
                with pytest.raises(LibreOfficeNotFoundError) as exc_info:
                    check_libreoffice()

                # Error message should be helpful
                assert "LibreOffice" in str(exc_info.value)

    def test_convert_pdf_to_docx_idempotent(self) -> None:
        """Test that convert_pdf_to_docx skips existing files."""
        from benchmarks.scripts.convert_corpus import convert_pdf_to_docx

        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = Path(tmpdir) / "test.pdf"
            pdf_path.write_text("fake pdf")
            docx_path = Path(tmpdir) / "test.docx"
            docx_path.write_text("existing docx")

            with patch("subprocess.run") as mock_run:
                result = convert_pdf_to_docx(pdf_path, Path(tmpdir))
                assert result is True
                mock_run.assert_not_called()

    def test_convert_pdf_to_docx_calls_soffice(self) -> None:
        """Test that convert_pdf_to_docx calls soffice when docx doesn't exist."""
        from benchmarks.scripts.convert_corpus import convert_pdf_to_docx

        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = Path(tmpdir) / "test.pdf"
            pdf_path.write_text("fake pdf")
            output_dir = Path(tmpdir) / "output"
            output_dir.mkdir()

            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)
                # Create the output file to simulate soffice behavior
                with patch("pathlib.Path.exists") as mock_exists:
                    # First call checks if docx exists (False), second checks pdf exists (True)
                    mock_exists.side_effect = [False, True, True]
                    convert_pdf_to_docx(pdf_path, output_dir)

                mock_run.assert_called_once()
                call_args = mock_run.call_args[0][0]
                assert "soffice" in call_args[0] or call_args[0] == "soffice"
                assert "--convert-to" in call_args
                assert "docx" in call_args

    def test_convert_corpus_creates_output_directory(self) -> None:
        """Test that convert_corpus creates the output directory if needed."""
        from benchmarks.scripts.convert_corpus import convert_corpus

        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = Path(tmpdir) / "pdfs"
            input_dir.mkdir()
            output_dir = Path(tmpdir) / "docx"

            with patch("benchmarks.scripts.convert_corpus.check_libreoffice") as mock_check:
                mock_check.return_value = "/usr/bin/soffice"
                with patch("benchmarks.scripts.convert_corpus.convert_pdf_to_docx") as mock_convert:
                    mock_convert.return_value = True
                    convert_corpus(input_dir, output_dir)

            assert output_dir.exists()
