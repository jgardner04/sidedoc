"""Convert PDF files to DOCX using LibreOffice (US-004).

This script converts PDF files in the corpus to DOCX format for use
in benchmarking Sidedoc against alternatives.
"""

from pathlib import Path
import shutil
import subprocess
from typing import Dict


class LibreOfficeNotFoundError(Exception):
    """Raised when LibreOffice is not installed or not found in PATH."""

    def __init__(self) -> None:
        super().__init__(
            "LibreOffice not found. Please install LibreOffice:\n"
            "  - macOS: brew install --cask libreoffice\n"
            "  - Ubuntu: sudo apt install libreoffice\n"
            "  - Windows: Download from https://www.libreoffice.org/download/"
        )


def check_libreoffice() -> str:
    """Check if LibreOffice is installed and return the path to soffice.

    Returns:
        Path to the soffice executable.

    Raises:
        LibreOfficeNotFoundError: If LibreOffice is not found.
    """
    # Check common locations
    soffice_path = shutil.which("soffice")
    if soffice_path:
        return soffice_path

    # Check macOS application bundle location
    macos_path = "/Applications/LibreOffice.app/Contents/MacOS/soffice"
    if Path(macos_path).exists():
        return macos_path

    raise LibreOfficeNotFoundError()


def convert_pdf_to_docx(pdf_path: Path, output_dir: Path) -> bool:
    """Convert a single PDF file to DOCX.

    Args:
        pdf_path: Path to the PDF file.
        output_dir: Directory to save the DOCX file.

    Returns:
        True if conversion succeeded or file already exists, False on error.
    """
    # Derive output filename
    docx_path = output_dir / f"{pdf_path.stem}.docx"

    # Idempotent: skip if output already exists
    if docx_path.exists():
        return True

    if not pdf_path.exists():
        return False

    try:
        soffice_path = check_libreoffice()

        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)

        # Run LibreOffice conversion
        result = subprocess.run(
            [
                soffice_path,
                "--headless",
                "--convert-to",
                "docx",
                "--outdir",
                str(output_dir),
                str(pdf_path),
            ],
            capture_output=True,
            timeout=120,
        )

        return result.returncode == 0

    except (LibreOfficeNotFoundError, subprocess.TimeoutExpired, subprocess.SubprocessError):
        return False


def convert_corpus(
    input_dir: Path | None = None,
    output_dir: Path | None = None,
) -> Dict[str, bool]:
    """Convert all PDFs in the corpus to DOCX.

    Args:
        input_dir: Directory containing PDFs. Defaults to corpus/real/pdfs/.
        output_dir: Directory to save DOCX files. Defaults to corpus/real/.

    Returns:
        Dict mapping filename to conversion success status.

    Raises:
        LibreOfficeNotFoundError: If LibreOffice is not installed.
    """
    if input_dir is None:
        input_dir = Path(__file__).parent.parent / "corpus" / "real" / "pdfs"
    if output_dir is None:
        output_dir = Path(__file__).parent.parent / "corpus" / "real"

    # Check LibreOffice before starting
    check_libreoffice()

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    results: Dict[str, bool] = {}

    for pdf_path in input_dir.glob("*.pdf"):
        success = convert_pdf_to_docx(pdf_path, output_dir)
        results[pdf_path.name] = success

    return results


def main() -> None:
    """CLI entry point for converting the corpus."""
    import sys

    print("Converting corpus PDFs to DOCX...")

    try:
        results = convert_corpus()
    except LibreOfficeNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    success_count = sum(results.values())
    total_count = len(results)

    if total_count == 0:
        print("No PDF files found in corpus/real/pdfs/")
        print("Run download_corpus.py first to download the PDFs.")
        return

    print(f"\nConverted {success_count}/{total_count} files:")
    for name, success in results.items():
        status = "OK" if success else "FAILED"
        print(f"  {name}: {status}")

    if success_count < total_count:
        sys.exit(1)


if __name__ == "__main__":
    main()
