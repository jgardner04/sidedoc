"""Extract .docx files into .sidedoc containers.

This module is being developed using TDD.
"""

from docx import Document


def extract_paragraphs(docx_path: str) -> list[str]:
    """Extract paragraph text from a .docx file.

    Args:
        docx_path: Path to the .docx file

    Returns:
        List of paragraph text strings
    """
    doc = Document(docx_path)
    paragraphs = []

    for paragraph in doc.paragraphs:
        text = paragraph.text
        if text:  # Only include non-empty paragraphs
            paragraphs.append(text)

    return paragraphs
