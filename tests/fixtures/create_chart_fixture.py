"""Script to create a minimal chart docx fixture for testing.

Builds a .docx with a bar chart using raw OOXML (no python-docx chart API).
The chart uses mc:AlternateContent with a PNG fallback image, matching
what Microsoft Word generates for chart-containing documents.

Two fixtures are created:
- charts.docx: Chart with cached PNG fallback (normal case)
- charts_no_fallback.docx: Chart without cached image (edge case)
"""

import io
import zipfile
from pathlib import Path

from PIL import Image

FIXTURES_DIR = Path(__file__).parent

# OOXML namespaces
_NSMAP = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "c": "http://schemas.openxmlformats.org/drawingml/2006/chart",
    "pic": "http://schemas.openxmlformats.org/drawingml/2006/picture",
    "mc": "http://schemas.openxmlformats.org/markup-compatibility/2006",
}


def _create_minimal_png() -> bytes:
    """Create a minimal valid 10x10 PNG image (chart fallback placeholder)."""
    img = Image.new("RGB", (10, 10), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _content_types_xml(*, has_fallback_image: bool = True) -> str:
    parts = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">',
        '  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
        '  <Default Extension="xml" ContentType="application/xml"/>',
        '  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>',
        '  <Override PartName="/word/charts/chart1.xml" ContentType="application/vnd.openxmlformats-officedocument.drawingml.chart+xml"/>',
    ]
    if has_fallback_image:
        parts.append('  <Default Extension="png" ContentType="image/png"/>')
    parts.append("</Types>")
    return "\n".join(parts)


def _rels_xml() -> str:
    return """\
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1"
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"
    Target="word/document.xml"/>
</Relationships>"""


def _document_rels_xml(*, has_fallback_image: bool = True) -> str:
    rels = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">',
        '  <Relationship Id="rId5"'
        ' Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/chart"'
        ' Target="charts/chart1.xml"/>',
    ]
    if has_fallback_image:
        rels.append(
            '  <Relationship Id="rId6"'
            ' Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"'
            ' Target="media/chart1-fallback.png"/>'
        )
    rels.append("</Relationships>")
    return "\n".join(rels)


def _document_xml_with_fallback() -> str:
    """Document with mc:AlternateContent chart + PNG fallback (normal Word output)."""
    return """\
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
            xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
            xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
            xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
            xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart"
            xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"
            xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006"
            mc:Ignorable="c">
  <w:body>
    <w:p>
      <w:r><w:t>Before chart</w:t></w:r>
    </w:p>
    <w:p>
      <w:r>
        <mc:AlternateContent>
          <mc:Choice Requires="c">
            <w:drawing>
              <wp:inline distT="0" distB="0" distL="0" distR="0">
                <wp:extent cx="5486400" cy="3200400"/>
                <wp:docPr id="1" name="Chart 1"/>
                <wp:cNvGraphicFramePr/>
                <a:graphic>
                  <a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/chart">
                    <c:chart r:id="rId5"/>
                  </a:graphicData>
                </a:graphic>
              </wp:inline>
            </w:drawing>
          </mc:Choice>
          <mc:Fallback>
            <w:drawing>
              <wp:inline distT="0" distB="0" distL="0" distR="0">
                <wp:extent cx="5486400" cy="3200400"/>
                <wp:docPr id="2" name="Chart 1 Fallback"/>
                <wp:cNvGraphicFramePr/>
                <a:graphic>
                  <a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">
                    <pic:pic>
                      <pic:nvPicPr>
                        <pic:cNvPr id="0" name="Chart 1"/>
                        <pic:cNvPicPr/>
                      </pic:nvPicPr>
                      <pic:blipFill>
                        <a:blip r:embed="rId6"/>
                        <a:stretch><a:fillRect/></a:stretch>
                      </pic:blipFill>
                      <pic:spPr>
                        <a:xfrm>
                          <a:off x="0" y="0"/>
                          <a:ext cx="5486400" cy="3200400"/>
                        </a:xfrm>
                        <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
                      </pic:spPr>
                    </pic:pic>
                  </a:graphicData>
                </a:graphic>
              </wp:inline>
            </w:drawing>
          </mc:Fallback>
        </mc:AlternateContent>
      </w:r>
    </w:p>
    <w:p>
      <w:r><w:t>After chart</w:t></w:r>
    </w:p>
  </w:body>
</w:document>"""


def _document_xml_no_fallback() -> str:
    """Document with chart drawing but no cached image fallback."""
    return """\
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
            xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
            xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
            xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
            xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart">
  <w:body>
    <w:p>
      <w:r><w:t>Before chart</w:t></w:r>
    </w:p>
    <w:p>
      <w:r>
        <w:drawing>
          <wp:inline distT="0" distB="0" distL="0" distR="0">
            <wp:extent cx="5486400" cy="3200400"/>
            <wp:docPr id="1" name="Chart 1"/>
            <wp:cNvGraphicFramePr/>
            <a:graphic>
              <a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/chart">
                <c:chart r:id="rId5"/>
              </a:graphicData>
            </a:graphic>
          </wp:inline>
        </w:drawing>
      </w:r>
    </w:p>
    <w:p>
      <w:r><w:t>After chart</w:t></w:r>
    </w:p>
  </w:body>
</w:document>"""


def _chart_xml() -> str:
    """Minimal bar chart with inline literal data (no embedded xlsx needed)."""
    return """\
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<c:chartSpace xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart"
              xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
  <c:lang val="en-US"/>
  <c:chart>
    <c:title>
      <c:tx>
        <c:rich>
          <a:bodyPr/>
          <a:lstStyle/>
          <a:p>
            <a:r><a:t>Q4 Revenue</a:t></a:r>
          </a:p>
        </c:rich>
      </c:tx>
      <c:overlay val="0"/>
    </c:title>
    <c:autoTitleDeleted val="0"/>
    <c:plotArea>
      <c:barChart>
        <c:barDir val="col"/>
        <c:grouping val="clustered"/>
        <c:varyColors val="0"/>
        <c:ser>
          <c:idx val="0"/>
          <c:order val="0"/>
          <c:cat>
            <c:strLit>
              <c:ptCount val="3"/>
              <c:pt idx="0"><c:v>Jan</c:v></c:pt>
              <c:pt idx="1"><c:v>Feb</c:v></c:pt>
              <c:pt idx="2"><c:v>Mar</c:v></c:pt>
            </c:strLit>
          </c:cat>
          <c:val>
            <c:numLit>
              <c:ptCount val="3"/>
              <c:pt idx="0"><c:v>100</c:v></c:pt>
              <c:pt idx="1"><c:v>200</c:v></c:pt>
              <c:pt idx="2"><c:v>300</c:v></c:pt>
            </c:numLit>
          </c:val>
        </c:ser>
        <c:axId val="1"/>
        <c:axId val="2"/>
      </c:barChart>
      <c:catAx>
        <c:axId val="1"/>
        <c:scaling><c:orientation val="minMax"/></c:scaling>
        <c:delete val="0"/>
        <c:axPos val="b"/>
        <c:crossAx val="2"/>
      </c:catAx>
      <c:valAx>
        <c:axId val="2"/>
        <c:scaling><c:orientation val="minMax"/></c:scaling>
        <c:delete val="0"/>
        <c:axPos val="l"/>
        <c:crossAx val="1"/>
      </c:valAx>
    </c:plotArea>
    <c:plotVisOnly val="1"/>
  </c:chart>
</c:chartSpace>"""


def create_chart_docx(output_path: Path, *, with_fallback: bool = True) -> None:
    """Create a minimal .docx with a bar chart.

    Args:
        output_path: Path to write the .docx file
        with_fallback: If True, include mc:AlternateContent with PNG fallback image
    """
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", _content_types_xml(has_fallback_image=with_fallback))
        zf.writestr("_rels/.rels", _rels_xml())
        zf.writestr(
            "word/_rels/document.xml.rels",
            _document_rels_xml(has_fallback_image=with_fallback),
        )
        if with_fallback:
            zf.writestr("word/document.xml", _document_xml_with_fallback())
            zf.writestr("word/media/chart1-fallback.png", _create_minimal_png())
        else:
            zf.writestr("word/document.xml", _document_xml_no_fallback())
        zf.writestr("word/charts/chart1.xml", _chart_xml())


if __name__ == "__main__":
    create_chart_docx(FIXTURES_DIR / "charts.docx", with_fallback=True)
    create_chart_docx(FIXTURES_DIR / "charts_no_fallback.docx", with_fallback=False)
    print(f"Created charts.docx and charts_no_fallback.docx in {FIXTURES_DIR}")
