"""Tests for SidedocStore read-only abstraction."""

import json
import tempfile
import zipfile
from pathlib import Path

import pytest

from sidedoc.store import SidedocStore, detect_sidedoc_format


def _create_dir_store(tmp_path: Path, content_md: str = "# Hello", styles: dict | None = None,
                      structure: dict | None = None, manifest: dict | None = None,
                      assets: dict[str, bytes] | None = None) -> Path:
    """Helper to create a directory-format sidedoc for testing."""
    sidedoc_dir = tmp_path / "test.sidedoc"
    sidedoc_dir.mkdir()
    (sidedoc_dir / "content.md").write_text(content_md)
    (sidedoc_dir / "styles.json").write_text(json.dumps(styles or {"block_styles": {}, "document_defaults": {}}))
    if structure is not None:
        (sidedoc_dir / "structure.json").write_text(json.dumps(structure))
    if manifest is not None:
        (sidedoc_dir / "manifest.json").write_text(json.dumps(manifest))
    if assets:
        assets_dir = sidedoc_dir / "assets"
        assets_dir.mkdir()
        for name, data in assets.items():
            (assets_dir / name).write_bytes(data)
    return sidedoc_dir


def _create_zip_store(tmp_path: Path, content_md: str = "# Hello", styles: dict | None = None,
                      structure: dict | None = None, manifest: dict | None = None,
                      assets: dict[str, bytes] | None = None) -> Path:
    """Helper to create a ZIP-format sidedoc for testing."""
    zip_path = tmp_path / "test.sdoc"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("content.md", content_md)
        zf.writestr("styles.json", json.dumps(styles or {"block_styles": {}, "document_defaults": {}}))
        if structure is not None:
            zf.writestr("structure.json", json.dumps(structure))
        if manifest is not None:
            zf.writestr("manifest.json", json.dumps(manifest))
        if assets:
            for name, data in assets.items():
                zf.writestr(f"assets/{name}", data)
    return zip_path


class TestDetectFormat:
    def test_detect_directory(self, tmp_path: Path) -> None:
        sidedoc_dir = _create_dir_store(tmp_path)
        assert detect_sidedoc_format(sidedoc_dir) == "directory"

    def test_detect_zip(self, tmp_path: Path) -> None:
        zip_path = _create_zip_store(tmp_path)
        assert detect_sidedoc_format(zip_path) == "zip"

    def test_detect_legacy_zip_with_sidedoc_extension(self, tmp_path: Path) -> None:
        """Legacy .sidedoc ZIP files should be detected as zip."""
        zip_path = tmp_path / "test.sidedoc"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("content.md", "# Hello")
        assert detect_sidedoc_format(zip_path) == "zip"

    def test_detect_nonexistent_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            detect_sidedoc_format(tmp_path / "nope.sidedoc")

    def test_detect_regular_file_raises(self, tmp_path: Path) -> None:
        f = tmp_path / "plain.txt"
        f.write_text("hello")
        with pytest.raises(ValueError, match="not a valid sidedoc"):
            detect_sidedoc_format(f)


class TestSidedocStoreDirectory:
    def test_open_directory(self, tmp_path: Path) -> None:
        sidedoc_dir = _create_dir_store(tmp_path)
        store = SidedocStore.open(sidedoc_dir)
        assert store.is_directory
        assert not store.is_zip

    def test_read_text(self, tmp_path: Path) -> None:
        sidedoc_dir = _create_dir_store(tmp_path, content_md="# Test Content")
        store = SidedocStore.open(sidedoc_dir)
        assert store.read_text("content.md") == "# Test Content"

    def test_read_json(self, tmp_path: Path) -> None:
        styles = {"block_styles": {"block-0": {"font_name": "Arial"}}, "document_defaults": {}}
        sidedoc_dir = _create_dir_store(tmp_path, styles=styles)
        store = SidedocStore.open(sidedoc_dir)
        assert store.read_json("styles.json") == styles

    def test_read_bytes(self, tmp_path: Path) -> None:
        sidedoc_dir = _create_dir_store(tmp_path, assets={"img.png": b"\x89PNG"})
        store = SidedocStore.open(sidedoc_dir)
        assert store.read_bytes("assets/img.png") == b"\x89PNG"

    def test_has_file_true(self, tmp_path: Path) -> None:
        sidedoc_dir = _create_dir_store(tmp_path, structure={"blocks": []})
        store = SidedocStore.open(sidedoc_dir)
        assert store.has_file("content.md")
        assert store.has_file("structure.json")

    def test_has_file_false(self, tmp_path: Path) -> None:
        sidedoc_dir = _create_dir_store(tmp_path)  # No structure.json
        store = SidedocStore.open(sidedoc_dir)
        assert not store.has_file("structure.json")
        assert not store.has_file("manifest.json")

    def test_list_files(self, tmp_path: Path) -> None:
        sidedoc_dir = _create_dir_store(tmp_path, structure={"blocks": []},
                                         manifest={"sidedoc_version": "1.0"})
        store = SidedocStore.open(sidedoc_dir)
        files = store.list_files()
        assert "content.md" in files
        assert "styles.json" in files
        assert "structure.json" in files
        assert "manifest.json" in files

    def test_list_assets(self, tmp_path: Path) -> None:
        sidedoc_dir = _create_dir_store(tmp_path, assets={"img1.png": b"data1", "img2.jpg": b"data2"})
        store = SidedocStore.open(sidedoc_dir)
        assets = store.list_assets()
        assert "img1.png" in assets
        assert "img2.jpg" in assets

    def test_list_assets_empty(self, tmp_path: Path) -> None:
        sidedoc_dir = _create_dir_store(tmp_path)
        store = SidedocStore.open(sidedoc_dir)
        assert store.list_assets() == []

    def test_assets_dir(self, tmp_path: Path) -> None:
        sidedoc_dir = _create_dir_store(tmp_path, assets={"img.png": b"data"})
        store = SidedocStore.open(sidedoc_dir)
        assert store.assets_dir == sidedoc_dir / "assets"

    def test_path_property(self, tmp_path: Path) -> None:
        sidedoc_dir = _create_dir_store(tmp_path)
        store = SidedocStore.open(sidedoc_dir)
        assert store.path == sidedoc_dir

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        sidedoc_dir = _create_dir_store(tmp_path)
        store = SidedocStore.open(sidedoc_dir)
        with pytest.raises(FileNotFoundError):
            store.read_text("nonexistent.txt")

    def test_context_manager_noop(self, tmp_path: Path) -> None:
        """Directory stores need no cleanup, but context manager works."""
        sidedoc_dir = _create_dir_store(tmp_path)
        with SidedocStore.open(sidedoc_dir) as store:
            assert store.read_text("content.md") == "# Hello"


class TestSidedocStoreZip:
    def test_open_zip(self, tmp_path: Path) -> None:
        zip_path = _create_zip_store(tmp_path)
        store = SidedocStore.open(zip_path)
        assert store.is_zip
        assert not store.is_directory

    def test_read_text(self, tmp_path: Path) -> None:
        zip_path = _create_zip_store(tmp_path, content_md="# Zip Content")
        store = SidedocStore.open(zip_path)
        assert store.read_text("content.md") == "# Zip Content"

    def test_read_json(self, tmp_path: Path) -> None:
        styles = {"block_styles": {"block-0": {"font_name": "Courier"}}, "document_defaults": {}}
        zip_path = _create_zip_store(tmp_path, styles=styles)
        store = SidedocStore.open(zip_path)
        assert store.read_json("styles.json") == styles

    def test_read_bytes(self, tmp_path: Path) -> None:
        zip_path = _create_zip_store(tmp_path, assets={"img.png": b"\x89PNG"})
        store = SidedocStore.open(zip_path)
        assert store.read_bytes("assets/img.png") == b"\x89PNG"

    def test_has_file(self, tmp_path: Path) -> None:
        zip_path = _create_zip_store(tmp_path, structure={"blocks": []})
        store = SidedocStore.open(zip_path)
        assert store.has_file("content.md")
        assert store.has_file("structure.json")
        assert not store.has_file("nonexistent.txt")

    def test_list_files(self, tmp_path: Path) -> None:
        zip_path = _create_zip_store(tmp_path, structure={"blocks": []},
                                      manifest={"sidedoc_version": "1.0"})
        store = SidedocStore.open(zip_path)
        files = store.list_files()
        assert "content.md" in files
        assert "styles.json" in files

    def test_list_assets(self, tmp_path: Path) -> None:
        zip_path = _create_zip_store(tmp_path, assets={"img.png": b"data"})
        store = SidedocStore.open(zip_path)
        assert store.list_assets() == ["img.png"]

    def test_assets_dir_extracts(self, tmp_path: Path) -> None:
        zip_path = _create_zip_store(tmp_path, assets={"img.png": b"\x89PNG"})
        with SidedocStore.open(zip_path) as store:
            adir = store.assets_dir
            assert adir is not None
            assert (adir / "img.png").exists()
            assert (adir / "img.png").read_bytes() == b"\x89PNG"

    def test_context_manager_cleans_up(self, tmp_path: Path) -> None:
        zip_path = _create_zip_store(tmp_path, assets={"img.png": b"data"})
        with SidedocStore.open(zip_path) as store:
            adir = store.assets_dir
            assert adir.exists()
        # After exiting, temp dir should be cleaned up
        assert not adir.exists()

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        zip_path = _create_zip_store(tmp_path)
        store = SidedocStore.open(zip_path)
        with pytest.raises(FileNotFoundError):
            store.read_text("nonexistent.txt")


class TestPathTraversalProtection:
    """Tests for path traversal protection in SidedocStore."""

    def test_read_text_rejects_path_traversal(self, tmp_path: Path) -> None:
        sidedoc_dir = _create_dir_store(tmp_path)
        store = SidedocStore.open(sidedoc_dir)
        with pytest.raises(ValueError, match="path traversal"):
            store.read_text("../../etc/passwd")

    def test_read_bytes_rejects_path_traversal(self, tmp_path: Path) -> None:
        sidedoc_dir = _create_dir_store(tmp_path)
        store = SidedocStore.open(sidedoc_dir)
        with pytest.raises(ValueError, match="path traversal"):
            store.read_bytes("../../etc/passwd")

    def test_has_file_rejects_path_traversal(self, tmp_path: Path) -> None:
        sidedoc_dir = _create_dir_store(tmp_path)
        store = SidedocStore.open(sidedoc_dir)
        with pytest.raises(ValueError, match="path traversal"):
            store.has_file("../../etc/passwd")

    def test_read_text_rejects_absolute_path(self, tmp_path: Path) -> None:
        sidedoc_dir = _create_dir_store(tmp_path)
        store = SidedocStore.open(sidedoc_dir)
        with pytest.raises(ValueError, match="path traversal"):
            store.read_text("/etc/passwd")

    def test_zip_assets_rejects_traversal(self, tmp_path: Path) -> None:
        """ZIP with assets/../../../evil entry should raise on assets_dir access."""
        zip_path = tmp_path / "malicious.sdoc"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("content.md", "# Hello")
            zf.writestr("styles.json", '{"block_styles": {}, "document_defaults": {}}')
            zf.writestr("assets/../../../evil.txt", "malicious content")
        with SidedocStore.open(zip_path) as store:
            with pytest.raises(ValueError, match="path traversal"):
                _ = store.assets_dir
