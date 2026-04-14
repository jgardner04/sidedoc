"""Tests for chart and SmartArt extraction and reconstruction."""

import json
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest
from sidedoc.extract import extract_blocks
from sidedoc.models import Block
from sidedoc.reconstruct import build_docx_from_sidedoc
from tests.helpers import create_sidedoc_dir


@pytest.fixture
def fixtures_dir():
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def chart_bar_path(fixtures_dir):
    return fixtures_dir / "chart_bar.docx"


@pytest.fixture
def chart_pie_path(fixtures_dir):
    return fixtures_dir / "chart_pie.docx"


@pytest.fixture
def smartart_orgchart_path(fixtures_dir):
    return fixtures_dir / "smartart_orgchart.docx"


# ── Chart Detection ──────────────────────────────────────────────


class TestChartDetection:
    """Charts are detected during extraction and produce 'chart' blocks."""

    def test_bar_chart_detected(self, chart_bar_path):
        blocks, _ = extract_blocks(str(chart_bar_path))
        chart_blocks = [b for b in blocks if b.type == "chart"]
        assert len(chart_blocks) == 1

    def test_pie_chart_detected(self, chart_pie_path):
        blocks, _ = extract_blocks(str(chart_pie_path))
        chart_blocks = [b for b in blocks if b.type == "chart"]
        assert len(chart_blocks) == 1

    def test_chart_block_has_image_reference(self, chart_bar_path):
        """Chart blocks with cached images include an image reference in content."""
        blocks, image_data = extract_blocks(str(chart_bar_path))
        chart_block = next(b for b in blocks if b.type == "chart")
        assert "![Chart:" in chart_block.content
        assert "assets/" in chart_block.content

    def test_chart_block_no_cached_image(self, chart_pie_path):
        """Charts without cached images get a placeholder."""
        blocks, _ = extract_blocks(str(chart_pie_path))
        chart_block = next(b for b in blocks if b.type == "chart")
        assert "[Chart:" in chart_block.content


# ── Chart Cached Image Extraction ────────────────────────────────


class TestChartImageExtraction:
    """Chart cached images are extracted to assets/."""

    def test_chart_image_extracted(self, chart_bar_path):
        _, image_data = extract_blocks(str(chart_bar_path))
        chart_images = [k for k in image_data if "chart" in k]
        assert len(chart_images) >= 1

    def test_chart_image_is_png(self, chart_bar_path):
        _, image_data = extract_blocks(str(chart_bar_path))
        chart_images = [k for k in image_data if "chart" in k]
        assert any(k.endswith(".png") for k in chart_images)


# ── Chart Data Extraction ────────────────────────────────────────


class TestChartDataExtraction:
    """Chart data (type, series, labels) extracted to metadata."""

    def test_chart_metadata_present(self, chart_bar_path):
        blocks, _ = extract_blocks(str(chart_bar_path))
        chart_block = next(b for b in blocks if b.type == "chart")
        assert chart_block.chart_metadata is not None

    def test_chart_type_detected(self, chart_bar_path):
        blocks, _ = extract_blocks(str(chart_bar_path))
        chart_block = next(b for b in blocks if b.type == "chart")
        assert chart_block.chart_metadata is not None
        assert chart_block.chart_metadata.chart_type == "bar"

    def test_pie_chart_type(self, chart_pie_path):
        blocks, _ = extract_blocks(str(chart_pie_path))
        chart_block = next(b for b in blocks if b.type == "chart")
        assert chart_block.chart_metadata is not None
        assert chart_block.chart_metadata.chart_type == "pie"

    def test_chart_title(self, chart_bar_path):
        blocks, _ = extract_blocks(str(chart_bar_path))
        chart_block = next(b for b in blocks if b.type == "chart")
        assert chart_block.chart_metadata is not None
        assert chart_block.chart_metadata.title == "Q4 Revenue"

    def test_chart_series_names(self, chart_bar_path):
        blocks, _ = extract_blocks(str(chart_bar_path))
        chart_block = next(b for b in blocks if b.type == "chart")
        assert chart_block.chart_metadata is not None
        assert len(chart_block.chart_metadata.series) >= 1
        assert chart_block.chart_metadata.series[0]["name"] == "Revenue"

    def test_chart_categories(self, chart_bar_path):
        blocks, _ = extract_blocks(str(chart_bar_path))
        chart_block = next(b for b in blocks if b.type == "chart")
        assert chart_block.chart_metadata is not None
        assert chart_block.chart_metadata.categories == ["Oct", "Nov", "Dec"]

    def test_chart_values(self, chart_bar_path):
        blocks, _ = extract_blocks(str(chart_bar_path))
        chart_block = next(b for b in blocks if b.type == "chart")
        assert chart_block.chart_metadata is not None
        assert chart_block.chart_metadata.series[0]["values"] == ["1200000", "1350000", "1500000"]


# ── SmartArt Detection ───────────────────────────────────────────


class TestSmartArtDetection:
    """SmartArt diagrams are detected and produce 'smartart' blocks."""

    def test_smartart_detected(self, smartart_orgchart_path):
        blocks, _ = extract_blocks(str(smartart_orgchart_path))
        smartart_blocks = [b for b in blocks if b.type == "smartart"]
        assert len(smartart_blocks) == 1

    def test_smartart_cached_image_extracted(self, smartart_orgchart_path):
        _, image_data = extract_blocks(str(smartart_orgchart_path))
        smartart_images = [k for k in image_data if "smartart" in k]
        assert len(smartart_images) >= 1

    def test_smartart_block_has_image_reference(self, smartart_orgchart_path):
        blocks, _ = extract_blocks(str(smartart_orgchart_path))
        smartart_block = next(b for b in blocks if b.type == "smartart")
        assert "![SmartArt:" in smartart_block.content
        assert "assets/" in smartart_block.content

    def test_smartart_metadata_present(self, smartart_orgchart_path):
        blocks, _ = extract_blocks(str(smartart_orgchart_path))
        smartart_block = next(b for b in blocks if b.type == "smartart")
        assert smartart_block.smartart_metadata is not None

    def test_smartart_nodes(self, smartart_orgchart_path):
        blocks, _ = extract_blocks(str(smartart_orgchart_path))
        smartart_block = next(b for b in blocks if b.type == "smartart")
        assert smartart_block.smartart_metadata is not None
        nodes = smartart_block.smartart_metadata.nodes
        assert len(nodes) == 3
        node_texts = [n["text"] for n in nodes]
        assert "CEO" in node_texts
        assert "VP Engineering" in node_texts


# ── Content.md Integration ───────────────────────────────────────


class TestContentMarkdown:
    """content.md includes image reference with chart/SmartArt notation."""

    def test_chart_in_content_md(self, chart_bar_path):
        blocks, _ = extract_blocks(str(chart_bar_path))
        chart_block = next(b for b in blocks if b.type == "chart")
        # Should look like: ![Chart: Q4 Revenue](assets/chart1.png)
        assert "Chart:" in chart_block.content

    def test_smartart_in_content_md(self, smartart_orgchart_path):
        blocks, _ = extract_blocks(str(smartart_orgchart_path))
        smartart_block = next(b for b in blocks if b.type == "smartart")
        assert "SmartArt:" in smartart_block.content


# ── Round-trip ───────────────────────────────────────────────────


class TestChartPartsArchival:
    """Chart XML parts are archived during extraction for full-fidelity reconstruction."""

    def test_chart_parts_manifest_present(self, chart_bar_path):
        blocks, _ = extract_blocks(str(chart_bar_path))
        chart_block = next(b for b in blocks if b.type == "chart")
        assert chart_block.chart_parts_manifest is not None

    def test_chart_parts_stored_as_files(self, chart_bar_path, tmp_path):
        """Chart XML parts are stored as separate files in assets/chart_parts/."""
        from sidedoc.extract import extract_styles
        from sidedoc.package import create_sidedoc_directory

        blocks, image_data = extract_blocks(str(chart_bar_path))
        styles = extract_styles(str(chart_bar_path), blocks)
        content_md = "\n".join(b.content for b in blocks)

        sidedoc_dir = tmp_path / "test.sidedoc"
        create_sidedoc_directory(
            str(sidedoc_dir), content_md, blocks, styles,
            str(chart_bar_path), image_data,
        )

        chart_parts_dir = sidedoc_dir / "assets" / "chart_parts"
        assert chart_parts_dir.exists()
        chart_files = list(chart_parts_dir.rglob("*"))
        assert len([f for f in chart_files if f.is_file()]) >= 2  # drawing.xml + chart XML

    def test_drawing_xml_archived(self, chart_bar_path):
        blocks, image_data = extract_blocks(str(chart_bar_path))
        chart_block = next(b for b in blocks if b.type == "chart")
        manifest = chart_block.chart_parts_manifest
        assert manifest.drawing_xml_path in image_data
        drawing_xml = image_data[manifest.drawing_xml_path]
        assert b"drawing" in drawing_xml.lower() or b"chart" in drawing_xml.lower()

    def test_chart_xml_archived(self, chart_bar_path):
        blocks, image_data = extract_blocks(str(chart_bar_path))
        chart_block = next(b for b in blocks if b.type == "chart")
        manifest = chart_block.chart_parts_manifest
        # At least one OOXML part should be the chart XML
        chart_parts = [p for p in manifest.parts if "chart" in p]
        assert len(chart_parts) >= 1
        # Verify the chart XML bytes are in image_data
        for ooxml_path, asset_path in manifest.parts.items():
            assert asset_path in image_data

    def test_part_relationships_recorded(self, chart_bar_path):
        blocks, _ = extract_blocks(str(chart_bar_path))
        chart_block = next(b for b in blocks if b.type == "chart")
        manifest = chart_block.chart_parts_manifest
        assert len(manifest.rels) >= 1
        chart_rel = next(r for r in manifest.rels if "chart" in r["type"])
        assert "id" in chart_rel
        assert "type" in chart_rel
        assert "target" in chart_rel

    def test_content_types_recorded(self, chart_bar_path):
        blocks, _ = extract_blocks(str(chart_bar_path))
        chart_block = next(b for b in blocks if b.type == "chart")
        manifest = chart_block.chart_parts_manifest
        assert len(manifest.content_types) >= 1
        assert any("chart" in ct["content_type"] for ct in manifest.content_types)

    def test_manifest_serialized_in_structure_json(self, chart_bar_path, tmp_path):
        from sidedoc.extract import extract_styles
        from sidedoc.package import create_sidedoc_directory

        blocks, image_data = extract_blocks(str(chart_bar_path))
        styles = extract_styles(str(chart_bar_path), blocks)
        content_md = "\n".join(b.content for b in blocks)

        sidedoc_dir = tmp_path / "test.sidedoc"
        create_sidedoc_directory(
            str(sidedoc_dir), content_md, blocks, styles,
            str(chart_bar_path), image_data,
        )

        structure = json.loads((sidedoc_dir / "structure.json").read_text())
        chart_struct = next(b for b in structure["blocks"] if b["type"] == "chart")
        assert "chart_parts_manifest" in chart_struct
        assert "drawing_xml_path" in chart_struct["chart_parts_manifest"]
        assert "parts" in chart_struct["chart_parts_manifest"]
        assert "rels" in chart_struct["chart_parts_manifest"]

    def test_chart_parts_not_in_structure_json_inline(self, chart_bar_path, tmp_path):
        """Chart XML bytes must NOT be inlined in structure.json."""
        from sidedoc.extract import extract_styles
        from sidedoc.package import create_sidedoc_directory

        blocks, image_data = extract_blocks(str(chart_bar_path))
        styles = extract_styles(str(chart_bar_path), blocks)
        content_md = "\n".join(b.content for b in blocks)

        sidedoc_dir = tmp_path / "test.sidedoc"
        create_sidedoc_directory(
            str(sidedoc_dir), content_md, blocks, styles,
            str(chart_bar_path), image_data,
        )

        structure_text = (sidedoc_dir / "structure.json").read_text()
        # structure.json should contain paths, not base64 or raw XML
        assert "chartSpace" not in structure_text


class TestChartRoundTrip:
    """Build can reconstruct from archived XML parts."""

    def _extract_and_build(self, docx_path, tmp_path):
        from sidedoc.extract import extract_blocks, extract_styles
        from sidedoc.package import create_sidedoc_directory

        blocks, image_data = extract_blocks(str(docx_path))
        styles = extract_styles(str(docx_path), blocks)
        content_md = "\n".join(b.content for b in blocks)

        sidedoc_dir = tmp_path / "test.sidedoc"
        create_sidedoc_directory(
            str(sidedoc_dir), content_md, blocks, styles,
            str(docx_path), image_data,
        )

        output_docx = tmp_path / "rebuilt.docx"
        build_docx_from_sidedoc(str(sidedoc_dir), str(output_docx))
        return output_docx

    def test_chart_roundtrip_preserves_content(self, chart_bar_path, tmp_path):
        """Extract a chart doc, build from sidedoc, verify chart block survives."""
        output_docx = self._extract_and_build(chart_bar_path, tmp_path)
        assert output_docx.exists()

    def test_roundtrip_produces_functional_chart(self, chart_bar_path, tmp_path):
        """Rebuilt docx contains a functional chart XML part, not just a raster image."""
        output_docx = self._extract_and_build(chart_bar_path, tmp_path)

        with zipfile.ZipFile(str(output_docx), "r") as zf:
            names = zf.namelist()
            chart_parts = [n for n in names if "charts/" in n and n.endswith(".xml")]
            assert len(chart_parts) >= 1, f"No chart XML parts found in rebuilt docx: {names}"

            # Verify the chart XML is valid and contains chart data
            chart_xml = zf.read(chart_parts[0])
            root = ET.fromstring(chart_xml)
            chart_ns = "http://schemas.openxmlformats.org/drawingml/2006/chart"
            assert root.find(f".//{{{chart_ns}}}barChart") is not None or \
                   root.find(f".//{{{chart_ns}}}chart") is not None

    def test_roundtrip_has_chart_relationship(self, chart_bar_path, tmp_path):
        """Rebuilt docx has proper chart relationship in document.xml.rels."""
        output_docx = self._extract_and_build(chart_bar_path, tmp_path)

        with zipfile.ZipFile(str(output_docx), "r") as zf:
            rels_xml = zf.read("word/_rels/document.xml.rels")
            root = ET.fromstring(rels_xml)
            chart_rels = [
                r for r in root
                if "chart" in r.get("Type", "")
            ]
            assert len(chart_rels) >= 1

    def test_roundtrip_has_chart_content_type(self, chart_bar_path, tmp_path):
        """Rebuilt docx has chart content type override."""
        output_docx = self._extract_and_build(chart_bar_path, tmp_path)

        with zipfile.ZipFile(str(output_docx), "r") as zf:
            ct_xml = zf.read("[Content_Types].xml")
            root = ET.fromstring(ct_xml)
            ct_ns = "http://schemas.openxmlformats.org/package/2006/content-types"
            chart_overrides = [
                o for o in root.findall(f"{{{ct_ns}}}Override")
                if "chart" in o.get("ContentType", "")
            ]
            assert len(chart_overrides) >= 1

    def test_roundtrip_drawing_references_chart(self, chart_bar_path, tmp_path):
        """Rebuilt docx has a w:drawing element referencing the chart."""
        output_docx = self._extract_and_build(chart_bar_path, tmp_path)

        with zipfile.ZipFile(str(output_docx), "r") as zf:
            doc_xml = zf.read("word/document.xml")
            W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
            C = "http://schemas.openxmlformats.org/drawingml/2006/chart"
            root = ET.fromstring(doc_xml)
            chart_refs = root.findall(f".//{{{C}}}chart")
            assert len(chart_refs) >= 1

    def test_pie_chart_roundtrip(self, chart_pie_path, tmp_path):
        """Pie chart (no fallback image) also round-trips with chart XML."""
        output_docx = self._extract_and_build(chart_pie_path, tmp_path)

        with zipfile.ZipFile(str(output_docx), "r") as zf:
            names = zf.namelist()
            chart_parts = [n for n in names if "charts/" in n and n.endswith(".xml")]
            assert len(chart_parts) >= 1


# ── No Regression ────────────────────────────────────────────────


class TestNoRegression:
    """Chart/SmartArt changes don't break standard image extraction."""

    def test_standard_images_still_work(self, fixtures_dir):
        images_path = fixtures_dir / "images.docx"
        if not images_path.exists():
            pytest.skip("images.docx fixture not found")
        blocks, image_data = extract_blocks(str(images_path))
        image_blocks = [b for b in blocks if b.type == "image"]
        assert len(image_blocks) >= 1
        assert len(image_data) >= 1

    def test_simple_doc_no_charts(self, fixtures_dir):
        simple_path = fixtures_dir / "simple.docx"
        blocks, _ = extract_blocks(str(simple_path))
        chart_blocks = [b for b in blocks if b.type in ("chart", "smartart")]
        assert len(chart_blocks) == 0


# ── Regression coverage for behaviors the JON-108 rewrite left uncovered ──


class TestAlternateContentChartDetection:
    """Charts wrapped in mc:AlternateContent (the dominant Word 2010+ format)
    must be detected. The legacy charts.docx fixture uses this wrapping;
    chart_bar.docx uses flat w:drawing and does not exercise this path."""

    def test_alternate_content_wrapped_chart_detected(self, fixtures_dir):
        charts_path = fixtures_dir / "charts.docx"
        if not charts_path.exists():
            pytest.skip("charts.docx fixture not found")
        # Sanity: fixture actually uses mc:AlternateContent
        with zipfile.ZipFile(str(charts_path), "r") as zf:
            doc_xml = zf.read("word/document.xml").decode("utf-8")
        assert "mc:AlternateContent" in doc_xml, \
            "charts.docx is expected to use mc:AlternateContent wrappers"
        blocks, _ = extract_blocks(str(charts_path))
        chart_blocks = [b for b in blocks if b.type == "chart"]
        assert len(chart_blocks) >= 1, (
            "Chart inside mc:AlternateContent was not detected — "
            "fell through to paragraph placeholder"
        )


class TestValidateImageMetafiles:
    """EMF and WMF cached-fallback images bypass PIL (which can't open them)
    but must still be checked via magic bytes."""

    def test_validate_image_emf_passes_without_pil(self):
        from sidedoc.extract import validate_image
        # Minimal EMF header — 4-byte magic + padding
        emf_bytes = b"\x01\x00\x00\x00" + b"\x00" * 60
        is_valid, err = validate_image(emf_bytes, "emf")
        assert is_valid, f"EMF with correct magic rejected: {err}"
        assert err == ""

    def test_validate_image_emf_rejects_wrong_magic(self):
        from sidedoc.extract import validate_image
        is_valid, err = validate_image(b"\xFF\xFF\xFF\xFF" + b"\x00" * 60, "emf")
        assert not is_valid
        assert "EMF" in err

    def test_validate_image_wmf_passes_without_pil(self):
        from sidedoc.extract import validate_image
        # Aldus placeable WMF header
        wmf_bytes = b"\xD7\xCD\xC6\x9A" + b"\x00" * 60
        is_valid, err = validate_image(wmf_bytes, "wmf")
        assert is_valid, f"WMF with correct magic rejected: {err}"
        assert err == ""


class TestExternalRelationshipBlipSkip:
    """_extract_blip_image must skip blips whose embed relationship is external,
    to prevent SSRF-ish resolution of remote URLs during extraction."""

    def test_external_relationship_blip_returns_none(self):
        from unittest.mock import MagicMock
        from sidedoc.extract import _extract_blip_image, RELATIONSHIPS_NS

        blip = MagicMock()
        blip.get.return_value = "rId99"

        rel = MagicMock()
        rel.is_external = True

        doc_part = MagicMock()
        doc_part.rels = {"rId99": rel}

        result = _extract_blip_image(blip, doc_part, "image", 0)
        assert result is None, "External-relationship blip should be skipped"
        blip.get.assert_called_with(f"{{{RELATIONSHIPS_NS}}}embed")


class TestNamespacePreservation:
    """Round-tripped docx must preserve the `w:` namespace prefix in
    document.xml. Using stdlib ElementTree to serialize re-emits as `ns0:`,
    which python-docx and other OOXML tools cannot parse."""

    def _build(self, docx_path, tmp_path):
        from sidedoc.extract import extract_styles
        from sidedoc.package import create_sidedoc_directory
        blocks, image_data = extract_blocks(str(docx_path))
        styles = extract_styles(str(docx_path), blocks)
        content_md = "\n".join(b.content for b in blocks)
        sdoc_dir = tmp_path / "test.sidedoc"
        create_sidedoc_directory(
            str(sdoc_dir), content_md, blocks, styles,
            str(docx_path), image_data,
        )
        output_docx = tmp_path / "rebuilt.docx"
        build_docx_from_sidedoc(str(sdoc_dir), str(output_docx))
        return output_docx

    def test_rebuilt_document_xml_uses_w_prefix(self, chart_bar_path, tmp_path):
        output_docx = self._build(chart_bar_path, tmp_path)

        with zipfile.ZipFile(str(output_docx), "r") as zf:
            doc_xml = zf.read("word/document.xml").decode("utf-8")

        assert "ns0:" not in doc_xml, (
            "document.xml uses stdlib ET default prefix (ns0:) instead of w:; "
            "this will break python-docx round-tripping"
        )
        assert "<w:body" in doc_xml or "w:body " in doc_xml, \
            "expected w:body element in rebuilt document.xml"

    def test_rebuilt_docx_has_no_invalid_rsidR_marker(self, chart_bar_path, tmp_path):
        output_docx = self._build(chart_bar_path, tmp_path)

        with zipfile.ZipFile(str(output_docx), "r") as zf:
            doc_xml = zf.read("word/document.xml").decode("utf-8")

        # block-N is the internal sidedoc ID; it must not appear as a w:rsidR
        # attribute in the rebuilt docx (w:rsidR is spec'd as 8-digit hex).
        assert 'w:rsidR="block-' not in doc_xml, \
            "internal block-N IDs leaked into w:rsidR — invalid OOXML"
        assert 'rsidR="block-' not in doc_xml, \
            "internal block-N IDs leaked into rsidR — invalid OOXML"
