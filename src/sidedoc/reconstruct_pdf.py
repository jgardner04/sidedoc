"""Reconstruct PDF from sidedoc format using WeasyPrint.

Converts sidedoc content.md → HTML → styled PDF via WeasyPrint.
This is the PDF equivalent of reconstruct.py (which builds DOCX).
"""

import html as html_lib
import logging
from importlib import import_module
from pathlib import Path
import tempfile
from typing import Any

import mistune

from sidedoc.reconstruct import is_table_row, is_table_separator_line, parse_gfm_table
from sidedoc.store import SidedocStore

logger = logging.getLogger(__name__)


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


def _render_table_html(rows: list[list[str]], metadata: dict[str, Any] | None) -> str:
    """Render a parsed GFM table grid to HTML, honoring table_metadata.

    Unlike GFM (which forces row 0 to be a header), this emits ``<thead>`` only
    when ``header_rows > 0`` and expresses merged cells with ``colspan`` /
    ``rowspan`` — neither of which GFM can represent.
    """
    metadata = metadata or {}
    header_rows = int(metadata.get("header_rows") or 0)
    aligns = metadata.get("column_alignments") or []
    merged = metadata.get("merged_cells") or []

    span_at: dict[tuple[int, int], tuple[int, int]] = {}
    covered: set[tuple[int, int]] = set()
    for m in merged:
        r = int(m.get("start_row", 0))
        c = int(m.get("start_col", 0))
        rs = int(m.get("row_span", 1) or 1)
        cs = int(m.get("col_span", 1) or 1)
        span_at[(r, c)] = (rs, cs)
        for dr in range(rs):
            for dc in range(cs):
                if dr or dc:
                    covered.add((r + dr, c + dc))

    def cell_html(r: int, c: int, text: str, tag: str) -> str:
        attrs = ""
        rs, cs = span_at.get((r, c), (1, 1))
        if rs > 1:
            attrs += f' rowspan="{rs}"'
        if cs > 1:
            attrs += f' colspan="{cs}"'
        if c < len(aligns) and aligns[c] in ("center", "right"):
            attrs += f' style="text-align: {aligns[c]}"'
        return f"<{tag}{attrs}>{html_lib.escape(text)}</{tag}>"

    def render_rows(start: int, end: int, tag: str) -> str:
        out = []
        for r in range(start, min(end, len(rows))):
            cells = "".join(
                cell_html(r, c, text, tag)
                for c, text in enumerate(rows[r])
                if (r, c) not in covered
            )
            out.append(f"<tr>{cells}</tr>")
        return "".join(out)

    parts = ["<table>"]
    if header_rows > 0:
        parts.append(f"<thead>{render_rows(0, header_rows, 'th')}</thead>")
    parts.append(f"<tbody>{render_rows(header_rows, len(rows), 'td')}</tbody>")
    parts.append("</table>")
    return "".join(parts)


def _content_md_to_html(
    content_md: str,
    table_metas: list[dict[str, Any]],
    has_structure: bool,
) -> str:
    """Render content.md to HTML, overlaying table structure from metadata.

    content.md is the authoritative source of *text*; ``table_metas`` (from
    structure.json, in document order) supplies header/merge/alignment
    structure that GFM can't express. If structure is missing or the table
    counts disagree (drift), we fall back to plain mistune rendering and warn —
    text is never lost, only the structural overlay is skipped.
    """
    segments: list[tuple[str, list[str]]] = []
    for line in content_md.split("\n"):
        kind = "table" if is_table_row(line) else "text"
        if segments and segments[-1][0] == kind:
            segments[-1][1].append(line)
        else:
            segments.append((kind, [line]))

    # Prepare each segment once. A run of contiguous pipe lines may contain
    # several tables back-to-back (blocks_to_markdown joins blocks with a single
    # "\n"), so split each table run into individual tables by their separator
    # lines — otherwise adjacent tables collapse into one and trip the drift
    # fallback. Text segments are pre-joined. Both results are reused below so
    # _split_gfm_tables is never recomputed.
    prepared: list[tuple[str, Any]] = []  # ("table", list[table-lines]) | ("text", str)
    table_count = 0
    for kind, seg_lines in segments:
        if kind == "table":
            tables = _split_gfm_tables(seg_lines)
            table_count += len(tables)
            prepared.append(("table", tables))
        else:
            prepared.append(("text", "\n".join(seg_lines)))

    if table_count == 0:
        return _markdown_to_html(content_md)

    if not has_structure or table_count != len(table_metas):
        logger.warning(
            "Rendering %d PDF table(s) without structure overlay "
            "(table metadata missing or out of sync with content.md); "
            "header and merged-cell fidelity may be reduced.",
            table_count,
        )
        return _markdown_to_html(content_md)

    out: list[str] = []
    meta_iter = iter(table_metas)
    for kind, payload in prepared:
        if kind == "table":
            for tbl_lines in payload:
                rows, _aligns = parse_gfm_table("\n".join(tbl_lines))
                out.append(_render_table_html(rows, next(meta_iter)))
        elif payload.strip():
            out.append(_markdown_to_html(payload))
    return "\n".join(out)


def _split_gfm_tables(run_lines: list[str]) -> list[list[str]]:
    """Split a contiguous run of GFM pipe lines into individual tables.

    Each GFM table has exactly one separator line (``| --- | --- |``) and the
    row immediately above it is that table's header. A new table therefore
    starts at the line preceding each separator.
    """
    sep_indices = [i for i, line in enumerate(run_lines) if is_table_separator_line(line)]
    if len(sep_indices) <= 1:
        return [run_lines]

    starts = [max(0, sep - 1) for sep in sep_indices]
    tables: list[list[str]] = []
    for k, start in enumerate(starts):
        end = starts[k + 1] if k + 1 < len(starts) else len(run_lines)
        tables.append(run_lines[start:end])
    # Preserve any stray leading rows before the first table's header.
    if starts[0] > 0:
        tables[0] = run_lines[: starts[0]] + tables[0]
    return tables


def _write_pdf_capturing(doc: Any, output_path: str) -> None:
    """Call ``doc.write_pdf`` and surface WeasyPrint asset warnings.

    WeasyPrint logs missing/unloadable assets to the ``weasyprint`` logger at
    WARNING and does not raise; without this the PDF is written with missing
    images/fonts under a success line. We capture those records and re-emit them
    on this module's logger so the CLI (and ``--strict``) can act on them.
    """
    wp_logger = logging.getLogger("weasyprint")
    captured: list[str] = []

    class _Collector(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            if record.levelno >= logging.WARNING:
                captured.append(record.getMessage())

    handler = _Collector()
    wp_logger.addHandler(handler)
    try:
        doc.write_pdf(output_path)
    finally:
        wp_logger.removeHandler(handler)

    for message in captured:
        logger.warning("PDF asset issue: %s", message)


def build_pdf_from_sidedoc(sidedoc_path: str, output_path: str) -> None:
    """Build a PDF from a sidedoc directory or archive.

    Args:
        sidedoc_path: Path to .sidedoc directory or .sdoc archive
        output_path: Output path for the PDF file

    Content that can't be rendered faithfully (table metadata drift, WeasyPrint
    asset-loading failures) is reported via ``logging.WARNING`` on this module's
    logger rather than dropped silently; the CLI surfaces these and ``--strict``
    turns them into a non-zero exit.
    """
    store = SidedocStore.open(sidedoc_path)
    with store:
        try:
            content_md = store.read_text("content.md")
        except FileNotFoundError as e:
            raise FileNotFoundError("content.md not found in sidedoc") from e

        has_structure = store.has_file("structure.json")
        table_metas: list[dict[str, Any]] = []
        if has_structure:
            try:
                structure = store.read_json("structure.json")
            except (ValueError, FileNotFoundError):
                has_structure = False
            else:
                table_metas = [
                    (block.get("table_metadata") or {})
                    for block in structure.get("blocks", [])
                    if block.get("type") == "table"
                ]

        html_content = _content_md_to_html(content_md, table_metas, has_structure)

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
            _write_pdf_capturing(doc, output_path)
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
            _write_pdf_capturing(doc, output_path)
