"""Reconstruct PDF from sidedoc format using WeasyPrint.

Converts sidedoc content.md → HTML → styled PDF via WeasyPrint.
This is the PDF equivalent of reconstruct.py (which builds DOCX).
"""

from pathlib import Path
from typing import cast

import mistune

try:
    import weasyprint
except ImportError as e:
    raise ImportError(
        "PDF reconstruction requires weasyprint. Install with: pip install sidedoc[pdf]"
    ) from e

from sidedoc.store import SidedocStore


_CSS = """\
@page {
    size: A4;
    margin: 2.54cm;
}
body {
    font-family: Helvetica, Arial, sans-serif;
    font-size: 11pt;
    line-height: 1.4;
    color: #000;
}
h1 { font-size: 24pt; margin-top: 0; margin-bottom: 12pt; }
h2 { font-size: 18pt; margin-top: 18pt; margin-bottom: 10pt; }
h3 { font-size: 14pt; margin-top: 14pt; margin-bottom: 8pt; }
h4 { font-size: 12pt; margin-top: 12pt; margin-bottom: 6pt; }
h5 { font-size: 11pt; margin-top: 10pt; margin-bottom: 6pt; }
h6 { font-size: 10pt; margin-top: 10pt; margin-bottom: 6pt; }
p { margin-top: 0; margin-bottom: 8pt; }
ul, ol { margin-top: 0; margin-bottom: 8pt; padding-left: 24pt; }
li { margin-bottom: 4pt; }
table {
    border-collapse: collapse;
    width: 100%;
    margin-top: 8pt;
    margin-bottom: 12pt;
    font-size: 10pt;
}
th, td {
    border: 1px solid #999;
    padding: 4pt 8pt;
    text-align: left;
}
th {
    background-color: #e8e8f0;
    font-weight: bold;
}
img {
    max-width: 100%;
    margin: 8pt 0;
}
"""


def _markdown_to_html(content_md: str) -> str:
    """Convert sidedoc markdown content to HTML using mistune."""
    return cast(str, mistune.html(content_md))


def build_pdf_from_sidedoc(sidedoc_path: str, output_path: str) -> None:
    """Build a PDF from a sidedoc directory or archive.

    Args:
        sidedoc_path: Path to .sidedoc directory or .sdoc archive
        output_path: Output path for the PDF file
    """
    store = SidedocStore.open(sidedoc_path)
    with store:
        content_md = store.read_text("content.md")

    html_content = _markdown_to_html(content_md)

    full_html = f"""\
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>{_CSS}</style>
</head>
<body>
{html_content}
</body>
</html>
"""

    doc = weasyprint.HTML(string=full_html, base_url=str(Path(sidedoc_path).resolve()))
    doc.write_pdf(output_path)
