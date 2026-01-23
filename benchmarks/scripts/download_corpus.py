"""Download public domain PDFs for the benchmark corpus (US-003).

This script downloads 5 public domain PDFs from government and corporate sources
to be used as the real-world test corpus for benchmarking Sidedoc against alternatives.
"""

import hashlib
from pathlib import Path
from typing import Dict, Optional

import requests


# Public domain PDFs for the benchmark corpus
# These are annual reports and financial documents that are publicly available
CORPUS_URLS: Dict[str, str] = {
    "sec_2024_afr": "https://www.sec.gov/files/sec-2024-agency-financial-report.pdf",
    "gsa_2024_annual": "https://www.gsa.gov/system/files/FY2024-GSA-Annual-Report.pdf",
    "sss_fy2024_afr": "https://www.sss.gov/wp-content/uploads/2024/11/FY-2024-AFR-Publication.pdf",
    "bmw_q3_2024": "https://www.bmwgroup.com/content/dam/grpw/websites/bmwgroup_com/ir/downloads/en/2024/Q3/BMW-Group-Report-Q3-2024-EN.pdf",
    "cocacola_earnings_2024": "https://investors.coca-colacompany.com/filings-reports/all-sec-filings/content/0000021344-24-000023/0000021344-24-000023.pdf",
}

# User-Agent header to use for downloads
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# SHA256 checksums for corpus files (None = checksum not yet computed)
# Run download once to get actual checksums, then update these values
CORPUS_CHECKSUMS: Dict[str, Optional[str]] = {
    "sec_2024_afr": None,
    "gsa_2024_annual": None,
    "sss_fy2024_afr": None,
    "bmw_q3_2024": None,
    "cocacola_earnings_2024": None,
}


def compute_sha256(path: Path) -> str:
    """Compute SHA256 hash of a file.

    Args:
        path: Path to the file.

    Returns:
        Hexadecimal SHA256 hash string.
    """
    sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def verify_checksum(path: Path, expected: Optional[str]) -> bool:
    """Verify file integrity via SHA256.

    Args:
        path: Path to the file to verify.
        expected: Expected SHA256 hash, or None to skip verification.

    Returns:
        True if checksum matches or no checksum is configured.
    """
    if expected is None:
        return True
    actual = compute_sha256(path)
    return actual == expected


def download_file(
    url: str, output_path: Path, expected_checksum: Optional[str] = None
) -> bool:
    """Download a file from a URL to the specified path.

    Args:
        url: The URL to download from.
        output_path: The local path to save the file to.
        expected_checksum: Optional SHA256 checksum to verify after download.

    Returns:
        True if the file was downloaded (or already exists with valid checksum),
        False on error or checksum mismatch.
    """
    # Idempotent: skip if file already exists and checksum matches
    if output_path.exists():
        if verify_checksum(output_path, expected_checksum):
            return True
        # Checksum mismatch - re-download
        output_path.unlink()

    try:
        response = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=60,
        )
        response.raise_for_status()

        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write the content
        output_path.write_bytes(response.content)

        # Verify checksum if provided
        if not verify_checksum(output_path, expected_checksum):
            output_path.unlink()
            return False

        return True

    except requests.RequestException:
        return False


def download_corpus(output_dir: Path | None = None) -> Dict[str, bool]:
    """Download all corpus PDFs.

    Args:
        output_dir: Directory to save PDFs to. Defaults to benchmarks/corpus/real/pdfs/.

    Returns:
        Dict mapping filename to download success status.
    """
    if output_dir is None:
        output_dir = Path(__file__).parent.parent / "corpus" / "real" / "pdfs"

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    results: Dict[str, bool] = {}

    for name, url in CORPUS_URLS.items():
        output_path = output_dir / f"{name}.pdf"
        expected_checksum = CORPUS_CHECKSUMS.get(name)
        success = download_file(url, output_path, expected_checksum)
        results[name] = success

    return results


def main() -> None:
    """CLI entry point for downloading the corpus."""
    import sys

    print("Downloading benchmark corpus PDFs...")
    results = download_corpus()

    success_count = sum(results.values())
    total_count = len(results)

    print(f"\nDownloaded {success_count}/{total_count} files:")
    for name, success in results.items():
        status = "OK" if success else "FAILED"
        print(f"  {name}: {status}")

    if success_count < total_count:
        sys.exit(1)


if __name__ == "__main__":
    main()
