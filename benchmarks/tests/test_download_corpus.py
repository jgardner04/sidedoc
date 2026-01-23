"""Tests for corpus download script (US-003)."""

from pathlib import Path
from unittest.mock import MagicMock, patch
import tempfile

import pytest


BENCHMARKS_DIR = Path(__file__).parent.parent


class TestDownloadCorpusScript:
    """Test that the download corpus script exists and works correctly."""

    def test_script_file_exists(self) -> None:
        """Test that download_corpus.py exists."""
        script_path = BENCHMARKS_DIR / "scripts" / "download_corpus.py"
        assert script_path.exists(), "benchmarks/scripts/download_corpus.py does not exist"

    def test_script_is_importable(self) -> None:
        """Test that the script module can be imported."""
        from benchmarks.scripts import download_corpus

        assert hasattr(download_corpus, "CORPUS_URLS")
        assert hasattr(download_corpus, "download_file")
        assert hasattr(download_corpus, "download_corpus")

    def test_corpus_urls_defined(self) -> None:
        """Test that the corpus URLs are properly defined."""
        from benchmarks.scripts.download_corpus import CORPUS_URLS

        assert len(CORPUS_URLS) == 5, "Expected 5 corpus URLs"

        # Check that URLs are properly structured
        for name, url in CORPUS_URLS.items():
            assert isinstance(name, str), f"URL key must be string, got {type(name)}"
            assert isinstance(url, str), f"URL value must be string, got {type(url)}"
            assert url.startswith("http"), f"URL must start with http: {url}"

    def test_download_file_idempotent(self) -> None:
        """Test that download_file skips existing files."""
        from benchmarks.scripts.download_corpus import download_file

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.pdf"
            output_path.write_text("existing content")

            # Should return True without downloading (file exists)
            with patch("benchmarks.scripts.download_corpus.requests") as mock_requests:
                result = download_file("http://example.com/test.pdf", output_path)
                assert result is True
                mock_requests.get.assert_not_called()

    def test_download_file_downloads_new_file(self) -> None:
        """Test that download_file downloads when file doesn't exist."""
        from benchmarks.scripts.download_corpus import download_file

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.pdf"

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = b"PDF content"
            mock_response.raise_for_status = MagicMock()

            with patch("benchmarks.scripts.download_corpus.requests.get") as mock_get:
                mock_get.return_value = mock_response

                result = download_file("http://example.com/test.pdf", output_path)
                assert result is True
                assert output_path.exists()
                assert output_path.read_bytes() == b"PDF content"

    def test_download_file_handles_network_error(self) -> None:
        """Test that download_file handles network errors gracefully."""
        from benchmarks.scripts.download_corpus import download_file
        import requests

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.pdf"

            with patch("benchmarks.scripts.download_corpus.requests.get") as mock_get:
                mock_get.side_effect = requests.RequestException("Network error")

                result = download_file("http://example.com/test.pdf", output_path)
                assert result is False
                assert not output_path.exists()

    def test_download_corpus_creates_output_directory(self) -> None:
        """Test that download_corpus creates the output directory if needed."""
        from benchmarks.scripts.download_corpus import download_corpus

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "pdfs"

            with patch("benchmarks.scripts.download_corpus.download_file") as mock_download:
                mock_download.return_value = True
                download_corpus(output_dir)
                assert output_dir.exists()
