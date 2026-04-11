"""Generate PDF test fixtures for sidedoc PDF extraction tests.

Run this script to create/update the PDF fixtures:
    python tests/fixtures/create_pdf_fixtures.py

Fixtures:
    simple.pdf   - Heading + two paragraphs
    tables.pdf   - Heading + 3x3 table with header row
    mixed.pdf    - Heading, paragraph, table, embedded image
"""

from pathlib import Path

from fpdf import FPDF

FIXTURES_DIR = Path(__file__).parent


def create_simple_pdf() -> None:
    """Create simple.pdf with a heading and two paragraphs."""
    pdf = FPDF()
    pdf.add_page()

    # Heading
    pdf.set_font("Helvetica", "B", 24)
    pdf.cell(text="Introduction to Sidedoc", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    # Paragraph 1
    pdf.set_font("Helvetica", "", 12)
    pdf.multi_cell(
        w=0,
        text=(
            "Sidedoc is an AI-native document format that separates content "
            "from formatting. It enables efficient AI interaction with documents "
            "while preserving rich formatting for human consumption."
        ),
    )
    pdf.ln(3)

    # Paragraph 2
    pdf.multi_cell(
        w=0,
        text=(
            "The canonical format is a .sidedoc/ directory containing markdown "
            "content and formatting metadata. A .sdoc ZIP archive is used for "
            "distribution and sharing."
        ),
    )

    output = FIXTURES_DIR / "simple.pdf"
    pdf.output(str(output))
    print(f"Created {output} ({output.stat().st_size / 1024:.0f} KB)")


def create_tables_pdf() -> None:
    """Create tables.pdf with a heading and a 3x3 table."""
    pdf = FPDF()
    pdf.add_page()

    # Heading
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(text="Employee Directory", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    # Table
    headers = ["Name", "Role", "Start Date"]
    rows = [
        ["Alice Smith", "Engineer", "2024-01-15"],
        ["Bob Jones", "Designer", "2024-03-01"],
        ["Carol Lee", "Manager", "2023-11-20"],
    ]

    col_widths = [60, 50, 45]

    # Header row
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_fill_color(220, 220, 240)
    for i, header in enumerate(headers):
        pdf.cell(w=col_widths[i], h=8, text=header, border=1, fill=True)
    pdf.ln()

    # Data rows
    pdf.set_font("Helvetica", "", 11)
    for row in rows:
        for i, cell in enumerate(row):
            pdf.cell(w=col_widths[i], h=8, text=cell, border=1)
        pdf.ln()

    output = FIXTURES_DIR / "tables.pdf"
    pdf.output(str(output))
    print(f"Created {output} ({output.stat().st_size / 1024:.0f} KB)")


def create_mixed_pdf() -> None:
    """Create mixed.pdf with heading, paragraph, table, and image placeholder."""
    pdf = FPDF()
    pdf.add_page()

    # Heading
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(text="Quarterly Report", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    # Paragraph
    pdf.set_font("Helvetica", "", 12)
    pdf.multi_cell(
        w=0,
        text=(
            "This report summarizes the key metrics for Q4 2024. "
            "Overall performance exceeded expectations with a 15% increase "
            "in revenue compared to the previous quarter."
        ),
    )
    pdf.ln(3)

    # Subheading
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(text="Revenue by Region", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    # Table
    headers = ["Region", "Revenue ($M)", "Growth (%)"]
    rows = [
        ["North America", "45.2", "+12%"],
        ["Europe", "31.8", "+18%"],
        ["Asia Pacific", "22.4", "+25%"],
    ]

    col_widths = [55, 45, 40]

    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(200, 220, 240)
    for i, header in enumerate(headers):
        pdf.cell(w=col_widths[i], h=7, text=header, border=1, fill=True)
    pdf.ln()

    pdf.set_font("Helvetica", "", 10)
    for row in rows:
        for i, cell in enumerate(row):
            pdf.cell(w=col_widths[i], h=7, text=cell, border=1)
        pdf.ln()

    pdf.ln(5)

    # Image placeholder (a colored rectangle with text)
    pdf.set_font("Helvetica", "I", 10)
    pdf.set_fill_color(240, 240, 240)
    pdf.set_draw_color(180, 180, 180)
    pdf.rect(10, pdf.get_y(), 100, 50, style="DF")
    pdf.set_xy(10, pdf.get_y() + 20)
    pdf.cell(w=100, h=10, text="[Chart Placeholder]", align="C")

    output = FIXTURES_DIR / "mixed.pdf"
    pdf.output(str(output))
    print(f"Created {output} ({output.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    create_simple_pdf()
    create_tables_pdf()
    create_mixed_pdf()
    print("Done.")
