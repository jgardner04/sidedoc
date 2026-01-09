"""Tests for extraction functionality.

Following TDD: Write tests first, then implement.
"""

import pytest
from pathlib import Path
from docx import Document

from sidedoc.extract import extract_paragraphs


class TestExtraction:
    """Tests for extracting .docx to .sidedoc."""

    def test_extract_simple_paragraph(self, tmp_path):
        """Test extracting a single paragraph from a docx file.

        TDD Phase: RED - This test should fail because extract_paragraphs doesn't exist yet.
        """
        # Arrange: Create a simple docx with one paragraph
        docx_path = tmp_path / "test.docx"
        doc = Document()
        doc.add_paragraph("Hello, world!")
        doc.save(str(docx_path))

        # Act: Extract paragraphs from the docx
        paragraphs = extract_paragraphs(str(docx_path))

        # Assert: We should get one paragraph with the correct text
        assert len(paragraphs) == 1
        assert paragraphs[0] == "Hello, world!"

    def test_extract_multiple_paragraphs(self, tmp_path):
        """Test extracting multiple paragraphs from a docx file.

        TDD Phase: RED - This test should fail because extract_paragraphs doesn't exist yet.
        """
        # Arrange: Create a docx with multiple paragraphs
        docx_path = tmp_path / "test.docx"
        doc = Document()
        doc.add_paragraph("First paragraph.")
        doc.add_paragraph("Second paragraph.")
        doc.add_paragraph("Third paragraph.")
        doc.save(str(docx_path))

        # Act: Extract paragraphs
        paragraphs = extract_paragraphs(str(docx_path))

        # Assert: We should get three paragraphs in order
        assert len(paragraphs) == 3
        assert paragraphs[0] == "First paragraph."
        assert paragraphs[1] == "Second paragraph."
        assert paragraphs[2] == "Third paragraph."

    def test_extract_empty_docx(self, tmp_path):
        """Test extracting from an empty docx file.

        TDD Phase: RED - This test should fail because extract_paragraphs doesn't exist yet.
        """
        # Arrange: Create an empty docx
        docx_path = tmp_path / "test.docx"
        doc = Document()
        doc.save(str(docx_path))

        # Act: Extract paragraphs
        paragraphs = extract_paragraphs(str(docx_path))

        # Assert: We should get an empty list
        assert len(paragraphs) == 0
