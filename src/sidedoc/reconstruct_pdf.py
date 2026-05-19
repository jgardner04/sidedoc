"""Reconstruct PDF from sidedoc format using WeasyPrint.

Converts sidedoc content.md → HTML → styled PDF via WeasyPrint.
This is the PDF equivalent of reconstruct.py (which builds DOCX).
"""

from importlib import import_module
from pathlib import Path
import tempfile
from typing import Any

import mistune

from sidedoc.store import SidedocStore


def require_weasyprint() -> Any:
    """Return the WeasyPrint module or raise an actionable error."""
    try:
        return import_module("weasyprint")
    except ImportError as e:
        raise ImportError(
            "PDF reconstruction requires weasyprint. Install with: pip install sidedoc[pdf]"
        ) from e


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
    html = mistune.html(content_md)
    if not isinstance(html, str):
        raise TypeError("Expected mistune.html() to return a string")
    return html


def build_pdf_from_sidedoc(sidedoc_path: str, output_path: str) -> None:
    """Build a PDF from a sidedoc directory or archive.

    Args:
        sidedoc_path: Path to .sidedoc directory or .sdoc archive
        output_path: Output path for the PDF file
    """
    store = SidedocStore.open(sidedoc_path)
    with store:
        try:
            content_md = store.read_text("content.md")
        except FileNotFoundError as e:
            raise FileNotFoundError("content.md not found in sidedoc") from e

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

        weasyprint = require_weasyprint()
        if store.is_directory:
            doc = weasyprint.HTML(string=full_html, base_url=str(store.path.resolve()))
            doc.write_pdf(output_path)
            return

        with tempfile.TemporaryDirectory() as render_root:
            render_root_path = Path(render_root)
            for name in store.list_files():
                if not name.startswith("assets/") or name.endswith("/"):
                    continue
                target = (render_root_path / name).resolve()
                if not target.is_relative_to(render_root_path.resolve()):
                    raise ValueError(f"Unsafe path traversal detected: {name}")
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(store.read_bytes(name))

            doc = weasyprint.HTML(string=full_html, base_url=str(render_root_path))
            doc.write_pdf(output_path)
