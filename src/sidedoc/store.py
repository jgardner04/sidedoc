"""Read-only storage abstraction for sidedoc containers (directory or ZIP)."""

import json
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Literal


def detect_sidedoc_format(path: str | Path) -> Literal["directory", "zip"]:
    """Detect whether a sidedoc path is a directory or ZIP archive.

    Args:
        path: Path to sidedoc file or directory

    Returns:
        "directory" or "zip"

    Raises:
        FileNotFoundError: If path does not exist
        ValueError: If path is neither a directory nor a valid ZIP
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"No such file or directory: {p}")
    if p.is_dir():
        return "directory"
    if zipfile.is_zipfile(p):
        return "zip"
    raise ValueError(f"{p} is not a valid sidedoc (not a directory or ZIP archive)")


class SidedocStore:
    """Read-only interface for sidedoc containers (directory or ZIP)."""

    def __init__(self, path: Path, fmt: Literal["directory", "zip"]) -> None:
        self._path = path
        self._fmt = fmt
        self._temp_dir: str | None = None  # For ZIP asset extraction

    @staticmethod
    def open(path: str | Path) -> "SidedocStore":
        """Auto-detect directory vs ZIP and return appropriate store."""
        p = Path(path)
        fmt = detect_sidedoc_format(p)
        return SidedocStore(p, fmt)

    def _validate_name(self, name: str) -> None:
        """Validate that a file name doesn't escape the container.

        Raises:
            ValueError: If name contains path traversal or is absolute
        """
        if Path(name).is_absolute():
            raise ValueError(f"Unsafe path traversal detected: {name}")
        try:
            target = (self._path / name).resolve()
            if not target.is_relative_to(self._path.resolve()):
                raise ValueError(f"Unsafe path traversal detected: {name}")
        except (ValueError, RuntimeError):
            raise ValueError(f"Unsafe path traversal detected: {name}")

    def read_text(self, name: str) -> str:
        """Read a text file from the container."""
        self._validate_name(name)
        if self._fmt == "directory":
            file_path = self._path / name
            if not file_path.exists():
                raise FileNotFoundError(f"{name} not found in {self._path}")
            return file_path.read_text(encoding="utf-8")
        else:
            try:
                with zipfile.ZipFile(self._path, "r") as zf:
                    return zf.read(name).decode("utf-8")
            except KeyError:
                raise FileNotFoundError(f"{name} not found in {self._path}")

    def read_json(self, name: str) -> dict:
        """Read and parse a JSON file from the container."""
        result: dict = json.loads(self.read_text(name))
        return result

    def read_bytes(self, name: str) -> bytes:
        """Read raw bytes from a file in the container."""
        self._validate_name(name)
        if self._fmt == "directory":
            file_path = self._path / name
            if not file_path.exists():
                raise FileNotFoundError(f"{name} not found in {self._path}")
            return file_path.read_bytes()
        else:
            try:
                with zipfile.ZipFile(self._path, "r") as zf:
                    return zf.read(name)
            except KeyError:
                raise FileNotFoundError(f"{name} not found in {self._path}")

    def has_file(self, name: str) -> bool:
        """Check if a file exists in the container."""
        self._validate_name(name)
        if self._fmt == "directory":
            return (self._path / name).exists()
        else:
            with zipfile.ZipFile(self._path, "r") as zf:
                return name in zf.namelist()

    def list_files(self) -> list[str]:
        """List all files in the container."""
        if self._fmt == "directory":
            files = []
            for p in self._path.rglob("*"):
                if p.is_file():
                    files.append(str(p.relative_to(self._path)))
            return sorted(files)
        else:
            with zipfile.ZipFile(self._path, "r") as zf:
                return sorted(zf.namelist())

    def list_assets(self) -> list[str]:
        """List asset filenames (without the assets/ prefix)."""
        if self._fmt == "directory":
            assets_dir = self._path / "assets"
            if not assets_dir.exists():
                return []
            return sorted(p.name for p in assets_dir.iterdir() if p.is_file())
        else:
            with zipfile.ZipFile(self._path, "r") as zf:
                return sorted(
                    name.removeprefix("assets/")
                    for name in zf.namelist()
                    if name.startswith("assets/") and name != "assets/"
                )

    @property
    def assets_dir(self) -> Path:
        """Get path to assets directory.

        For directories: returns path/assets/ directly.
        For ZIPs: extracts assets to a temp directory (cleaned up on __exit__).
        """
        if self._fmt == "directory":
            return self._path / "assets"
        else:
            if self._temp_dir is None:
                self._temp_dir = tempfile.mkdtemp()
                assets_path = Path(self._temp_dir)
                with zipfile.ZipFile(self._path, "r") as zf:
                    for file_info in zf.filelist:
                        if file_info.filename.startswith("assets/") and file_info.filename != "assets/":
                            filename = file_info.filename.removeprefix("assets/")
                            target = (assets_path / filename).resolve()
                            if not target.is_relative_to(assets_path.resolve()):
                                raise ValueError(
                                    f"Unsafe path traversal detected: {file_info.filename}"
                                )
                            target.parent.mkdir(parents=True, exist_ok=True)
                            target.write_bytes(zf.read(file_info.filename))
            return Path(self._temp_dir)

    @property
    def is_directory(self) -> bool:
        return self._fmt == "directory"

    @property
    def is_zip(self) -> bool:
        return self._fmt == "zip"

    @property
    def path(self) -> Path:
        return self._path

    def __enter__(self) -> "SidedocStore":
        return self

    def __exit__(self, *args: object) -> None:
        if self._temp_dir is not None:
            shutil.rmtree(self._temp_dir, ignore_errors=True)
            self._temp_dir = None
