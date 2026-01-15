"""Script to create test fixture docx files."""

from pathlib import Path
from docx import Document
from docx.shared import Inches

# Get the directory where this script is located
FIXTURES_DIR = Path(__file__).parent


def create_simple_docx() -> None:
    """Create simple.docx with headings and paragraphs only."""
    doc = Document()

    doc.add_heading("Main Title", level=1)
    doc.add_paragraph("This is a simple paragraph with plain text.")

    doc.add_heading("Section 1", level=2)
    doc.add_paragraph("First paragraph in section 1.")
    doc.add_paragraph("Second paragraph in section 1.")

    doc.add_heading("Section 2", level=2)
    doc.add_paragraph("A paragraph in section 2.")

    doc.save(str(FIXTURES_DIR / "simple.docx"))
    print("✓ Created simple.docx")


def create_lists_docx() -> None:
    """Create lists.docx with bulleted and numbered lists."""
    doc = Document()

    doc.add_heading("Lists Example", level=1)

    doc.add_heading("Bulleted List", level=2)
    doc.add_paragraph("First bullet item", style="List Bullet")
    doc.add_paragraph("Second bullet item", style="List Bullet")
    doc.add_paragraph("Third bullet item", style="List Bullet")

    doc.add_heading("Numbered List", level=2)
    doc.add_paragraph("First numbered item", style="List Number")
    doc.add_paragraph("Second numbered item", style="List Number")
    doc.add_paragraph("Third numbered item", style="List Number")

    doc.add_heading("Mixed Lists", level=2)
    doc.add_paragraph("Bullet one", style="List Bullet")
    doc.add_paragraph("Bullet two", style="List Bullet")
    doc.add_paragraph("Then a numbered item", style="List Number")
    doc.add_paragraph("Another numbered item", style="List Number")

    doc.save(str(FIXTURES_DIR / "lists.docx"))
    print("✓ Created lists.docx")


def create_formatted_docx() -> None:
    """Create formatted.docx with bold, italic, mixed inline formatting."""
    doc = Document()

    doc.add_heading("Formatted Text Example", level=1)

    # Bold text
    p = doc.add_paragraph()
    p.add_run("This text is ").bold = False
    p.add_run("bold").bold = True
    p.add_run(".")

    # Italic text
    p = doc.add_paragraph()
    p.add_run("This text is ").italic = False
    p.add_run("italic").italic = True
    p.add_run(".")

    # Bold and italic
    p = doc.add_paragraph()
    p.add_run("This text is ").bold = False
    run = p.add_run("bold and italic")
    run.bold = True
    run.italic = True
    p.add_run(".")

    # Underline
    p = doc.add_paragraph()
    p.add_run("This text is ").underline = False
    p.add_run("underlined").underline = True
    p.add_run(".")

    # Mixed formatting in a sentence
    p = doc.add_paragraph()
    p.add_run("A sentence with ")
    p.add_run("bold").bold = True
    p.add_run(", ")
    p.add_run("italic").italic = True
    p.add_run(", and ")
    run = p.add_run("both")
    run.bold = True
    run.italic = True
    p.add_run(" mixed together.")

    doc.save(str(FIXTURES_DIR / "formatted.docx"))
    print("✓ Created formatted.docx")


def create_test_images() -> None:
    """Create simple PNG image files for testing."""
    from PIL import Image as PILImage

    # Create a simple red square
    img = PILImage.new('RGB', (100, 100), color='red')
    img.save(str(FIXTURES_DIR / 'test_image1.png'))

    # Create a simple blue square
    img2 = PILImage.new('RGB', (100, 100), color='blue')
    img2.save(str(FIXTURES_DIR / 'test_image2.png'))


def create_images_docx() -> None:
    """Create images.docx with multiple images."""
    # First create the test images
    create_test_images()

    doc = Document()

    doc.add_heading("Document with Images", level=1)

    doc.add_paragraph("First image:")
    doc.add_picture(str(FIXTURES_DIR / 'test_image1.png'), width=Inches(1.5))

    doc.add_paragraph("Second image:")
    doc.add_picture(str(FIXTURES_DIR / 'test_image2.png'), width=Inches(2.0))

    doc.add_paragraph("Text after images.")

    doc.save(str(FIXTURES_DIR / "images.docx"))
    print("✓ Created images.docx")


def create_complex_docx() -> None:
    """Create complex.docx with all supported elements combined."""
    doc = Document()

    doc.add_heading("Complex Document", level=1)

    doc.add_paragraph("This document contains all supported elements.")

    doc.add_heading("Section with Formatting", level=2)
    p = doc.add_paragraph()
    p.add_run("This paragraph has ")
    p.add_run("bold").bold = True
    p.add_run(", ")
    p.add_run("italic").italic = True
    p.add_run(", and ")
    run = p.add_run("both")
    run.bold = True
    run.italic = True
    p.add_run(" formatting.")

    doc.add_heading("Lists Section", level=2)
    doc.add_paragraph("Bullet list:")
    doc.add_paragraph("First item", style="List Bullet")
    doc.add_paragraph("Second item", style="List Bullet")

    doc.add_paragraph("Numbered list:")
    doc.add_paragraph("First", style="List Number")
    doc.add_paragraph("Second", style="List Number")

    doc.add_heading("Image Section", level=2)
    doc.add_paragraph("An embedded image:")
    doc.add_picture(str(FIXTURES_DIR / 'test_image1.png'), width=Inches(1.0))

    doc.add_heading("Final Section", level=2)
    doc.add_paragraph("A concluding paragraph with regular text.")

    doc.save(str(FIXTURES_DIR / "complex.docx"))
    print("✓ Created complex.docx")


if __name__ == "__main__":
    print("Creating test fixtures...")
    create_simple_docx()
    create_lists_docx()
    create_formatted_docx()
    create_images_docx()
    create_complex_docx()
    print("\nAll fixtures created successfully!")
