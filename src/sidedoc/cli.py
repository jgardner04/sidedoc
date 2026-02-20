"""CLI interface for sidedoc."""

import hashlib
import json
import shutil
import sys
import zipfile
from pathlib import Path

import click

from sidedoc import __version__
from sidedoc.constants import (
    ALL_FILES,
    CONTENT_PREVIEW_LENGTH,
    CORE_FILES,
    HASH_DISPLAY_LENGTH,
    SIDEDOC_DIR_EXTENSION,
    SIDEDOC_ZIP_EXTENSION,
    TRACKING_FILES,
)
from sidedoc.extract import extract_blocks, extract_styles, blocks_to_markdown
from sidedoc.models import Block
from sidedoc.package import create_sidedoc_archive, create_sidedoc_directory
from sidedoc.reconstruct import build_docx_from_sidedoc, parse_gfm_table, parse_markdown_to_blocks, validate_gfm_table_dimensions
from sidedoc.store import SidedocStore, detect_sidedoc_format
from sidedoc.sync import (
    generate_updated_docx,
    match_blocks,
    sync_sidedoc_to_docx,
    update_sidedoc_metadata,
)
from sidedoc.utils import ensure_sdoc_extension, ensure_sidedoc_extension, is_safe_path


# Exit codes as per specification
EXIT_SUCCESS = 0
EXIT_ERROR = 1
EXIT_NOT_FOUND = 2
EXIT_INVALID_FORMAT = 3
EXIT_SYNC_CONFLICT = 4


@click.group()
@click.version_option(version=__version__, prog_name="sidedoc")
def main() -> None:
    """Sidedoc - AI-native document format.

    Extract Word documents to markdown, preserve formatting, and sync changes.
    """
    pass


def _read_sidedoc_files(input_path: str) -> tuple[str, dict, dict]:
    """Read content.md, styles.json, and structure.json from a sidedoc container.

    Works with both directory and ZIP formats via SidedocStore.

    Args:
        input_path: Path to .sidedoc directory or ZIP

    Returns:
        Tuple of (content_md, styles_data, old_structure)
    """
    try:
        store = SidedocStore.open(input_path)
    except (FileNotFoundError, ValueError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(EXIT_INVALID_FORMAT)

    with store:
        try:
            content_md = store.read_text("content.md")
        except FileNotFoundError:
            click.echo("Error: content.md not found in sidedoc", err=True)
            sys.exit(EXIT_INVALID_FORMAT)

        try:
            styles_data = store.read_json("styles.json")
        except FileNotFoundError:
            click.echo("Error: styles.json not found in sidedoc", err=True)
            sys.exit(EXIT_INVALID_FORMAT)
        except json.JSONDecodeError as e:
            click.echo(f"Error: Invalid JSON in styles.json: {e}", err=True)
            sys.exit(EXIT_INVALID_FORMAT)

        if store.has_file("structure.json"):
            try:
                old_structure = store.read_json("structure.json")
            except json.JSONDecodeError as e:
                click.echo(f"Error: Invalid JSON in structure.json: {e}", err=True)
                sys.exit(EXIT_INVALID_FORMAT)
        else:
            # structure.json is optional in directory format (first sync or post-clone)
            old_structure = {"blocks": []}

        return content_md, styles_data, old_structure


def _convert_structure_to_blocks(old_structure: dict) -> list[Block]:
    """Convert structure.json dict to list of Block objects."""
    old_blocks = []
    for block_data in old_structure.get("blocks", []):
        old_blocks.append(
            Block(
                id=block_data["id"],
                type=block_data["type"],
                content="",
                docx_paragraph_index=block_data["docx_paragraph_index"],
                content_start=block_data["content_start"],
                content_end=block_data["content_end"],
                content_hash=block_data["content_hash"],
                level=block_data.get("level"),
                image_path=block_data.get("image_path"),
                inline_formatting=block_data.get("inline_formatting"),
                table_metadata=block_data.get("table_metadata"),
            )
        )
    return old_blocks


def _build_output_docx(new_blocks: list[Block], old_structure: dict, styles_data: dict, output: str) -> None:
    """Build output docx file from new blocks with formatting preserved."""
    old_blocks = _convert_structure_to_blocks(old_structure)
    matches = match_blocks(old_blocks, new_blocks)
    generate_updated_docx(new_blocks, matches, styles_data, output)
    click.echo(f"✓ Built updated document: {output}")


@main.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option("-o", "--output", help="Output path")
@click.option("--force", is_flag=True, help="Overwrite existing output directory")
@click.option("--pack", is_flag=True, help="Create .sdoc ZIP archive instead of directory")
@click.option(
    "--track-changes/--no-track-changes",
    default=None,
    help="Force enable/disable track changes extraction. Default: auto-detect",
)
def extract(input_file: str, output: str | None, force: bool, pack: bool, track_changes: bool | None) -> None:
    """Extract a Word document into a sidedoc directory.

    Converts document.docx to document.sidedoc/ directory (or document.sdoc with --pack).

    Track changes behavior:
    - Default: Auto-detect track changes in the document
    - --track-changes: Force extract track changes as CriticMarkup
    - --no-track-changes: Accept all changes (ignore track changes)
    """
    try:
        if pack:
            # Create ZIP archive with .sdoc extension
            if output is None:
                output = str(Path(input_file).with_suffix(SIDEDOC_ZIP_EXTENSION))
            else:
                output = ensure_sdoc_extension(output)

            blocks, image_data = extract_blocks(input_file, track_changes=track_changes)
            styles = extract_styles(input_file, blocks)
            content_md = blocks_to_markdown(blocks)
            create_sidedoc_archive(output, content_md, blocks, styles, input_file, image_data)
        else:
            # Create directory with .sidedoc extension
            if output is None:
                output = str(Path(input_file).with_suffix(SIDEDOC_DIR_EXTENSION))
            else:
                output = ensure_sidedoc_extension(output)

            output_path = Path(output)
            if output_path.is_symlink():
                click.echo("Error: output path is a symlink.", err=True)
                sys.exit(EXIT_ERROR)

            if output_path.exists() and not force:
                click.echo(
                    f"Error: {output} already exists. Use --force to overwrite.",
                    err=True,
                )
                sys.exit(EXIT_ERROR)

            if output_path.exists() and force:
                shutil.rmtree(output_path)

            blocks, image_data = extract_blocks(input_file, track_changes=track_changes)
            styles = extract_styles(input_file, blocks)
            content_md = blocks_to_markdown(blocks)
            create_sidedoc_directory(output, content_md, blocks, styles, input_file, image_data)

        click.echo(f"✓ Extracted to {output}")
        sys.exit(EXIT_SUCCESS)
    except FileNotFoundError:
        click.echo(f"Error: File not found: {input_file}", err=True)
        sys.exit(EXIT_NOT_FOUND)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(EXIT_ERROR)


@main.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option("-o", "--output", help="Output path for .docx file")
def build(input_file: str, output: str | None) -> None:
    """Reconstruct a Word document from a sidedoc directory or archive.

    Accepts both .sidedoc/ directories and .sdoc ZIP archives.
    """
    try:
        if output is None:
            # Place output alongside input (not inside directory)
            input_path = Path(input_file)
            output = str(input_path.parent / (input_path.stem + ".docx"))

        build_docx_from_sidedoc(input_file, output)

        click.echo(f"✓ Built document: {output}")
        sys.exit(EXIT_SUCCESS)
    except FileNotFoundError:
        click.echo(f"Error: File not found: {input_file}", err=True)
        sys.exit(EXIT_NOT_FOUND)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(EXIT_ERROR)


@main.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option("-o", "--output", help="Optional: build updated docx to this path")
@click.option("--author", default="Sidedoc AI", help="Author name for track changes (default: 'Sidedoc AI')")
def sync(input_file: str, output: str | None, author: str) -> None:
    """Sync changes from edited content.md back to the document.

    Updates structure.json, remaps styles.json, and updates manifest.json.
    Only works with .sidedoc/ directories.

    CriticMarkup syntax ({++insert++}, {--delete--}, {~~old~>new~~}) in content.md
    will be converted to track changes in the output docx with the specified author.
    """
    try:
        # Reject ZIP input
        input_path = Path(input_file)
        if input_path.is_file() and zipfile.is_zipfile(input_path):
            click.echo(
                "Error: Cannot sync a ZIP archive. Run `sidedoc unpack` to convert to directory format first.",
                err=True,
            )
            sys.exit(EXIT_INVALID_FORMAT)

        content_md, styles_data, old_structure = _read_sidedoc_files(input_file)
        new_blocks = parse_markdown_to_blocks(content_md)

        # Compute content hashes for new blocks
        for block in new_blocks:
            block.content_hash = hashlib.sha256(block.content.encode()).hexdigest()

        # Match blocks for style remapping
        old_blocks = _convert_structure_to_blocks(old_structure)
        matches = match_blocks(old_blocks, new_blocks)

        update_sidedoc_metadata(input_file, new_blocks, content_md, matches=matches)

        click.echo(f"✓ Synced changes in {input_file}")

        if output:
            # Use sync_sidedoc_to_docx for track changes support
            sync_sidedoc_to_docx(input_file, output, author=author)
            click.echo(f"✓ Built updated document: {output}")

        sys.exit(EXIT_SUCCESS)

    except FileNotFoundError:
        click.echo(f"Error: File not found: {input_file}", err=True)
        sys.exit(EXIT_NOT_FOUND)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(EXIT_ERROR)


def _validate_track_changes(structure: dict, content: str) -> list[str]:
    """Validate track changes in structure.json.

    Checks:
    - Track change positions are within block bounds
    - Track change metadata is complete (author, date)

    Args:
        structure: Parsed structure.json data
        content: Content from content.md

    Returns:
        List of warning messages (empty if no issues)
    """
    warnings = []

    for block in structure.get("blocks", []):
        block_id = block.get("id", "unknown")
        track_changes = block.get("track_changes") or []
        content_start = block.get("content_start", 0)
        content_end = block.get("content_end", 0)
        block_length = content_end - content_start

        for i, tc in enumerate(track_changes):
            tc_start = tc.get("start", 0)
            tc_end = tc.get("end", 0)

            # Check positions are within block bounds
            if tc_end > block_length:
                warnings.append(
                    f"Track change {i+1} in {block_id} has invalid position: "
                    f"end ({tc_end}) exceeds block length ({block_length})"
                )

            # Check start is before end
            if tc_start > tc_end:
                warnings.append(
                    f"Track change {i+1} in {block_id} has invalid positions: "
                    f"start ({tc_start}) is after end ({tc_end})"
                )

            # Check metadata completeness
            if not tc.get("author"):
                warnings.append(
                    f"Track change {i+1} in {block_id} is missing author metadata"
                )
            if not tc.get("date"):
                warnings.append(
                    f"Track change {i+1} in {block_id} is missing date metadata"
                )

    return warnings


def _validate_tables(structure: dict, content: str) -> list[str]:
    """Validate table blocks in structure.json against content.md.

    Checks:
    - Table metadata rows/cols match content dimensions
    - Merged cell regions are within bounds

    Args:
        structure: Parsed structure.json data
        content: Content from content.md

    Returns:
        List of warning messages (empty if no issues)
    """
    warnings = []

    for block in structure.get("blocks", []):
        if block.get("type") != "table":
            continue

        block_id = block.get("id", "unknown")
        metadata = block.get("table_metadata")
        if not metadata:
            continue

        # Extract table content from content.md
        start = block.get("content_start", 0)
        end = block.get("content_end", 0)
        table_content = content[start:end]

        # Parse GFM to get actual dimensions
        try:
            validate_gfm_table_dimensions(table_content)
            rows, _ = parse_gfm_table(table_content)
        except ValueError as e:
            warnings.append(f"Table {block_id}: unable to parse GFM content: {e}")
            continue

        actual_rows = len(rows)
        actual_cols = len(rows[0]) if rows else 0
        expected_rows = metadata.get("rows", 0)
        expected_cols = metadata.get("cols", 0)

        if actual_rows != expected_rows:
            warnings.append(
                f"Table {block_id}: row count mismatch "
                f"(metadata={expected_rows}, content={actual_rows})"
            )
        if actual_cols != expected_cols:
            warnings.append(
                f"Table {block_id}: column count mismatch "
                f"(metadata={expected_cols}, content={actual_cols})"
            )

        # Validate merged cell regions
        for merge in metadata.get("merged_cells", []):
            end_row = merge.get("start_row", 0) + merge.get("row_span", 1) - 1
            end_col = merge.get("start_col", 0) + merge.get("col_span", 1) - 1
            if end_row >= expected_rows:
                warnings.append(
                    f"Table {block_id}: merged cell exceeds row bounds "
                    f"(end_row={end_row}, rows={expected_rows})"
                )
            if end_col >= expected_cols:
                warnings.append(
                    f"Table {block_id}: merged cell exceeds column bounds "
                    f"(end_col={end_col}, cols={expected_cols})"
                )

    return warnings


@main.command()
@click.argument("input_file", type=click.Path(exists=True))
def validate(input_file: str) -> None:
    """Validate a sidedoc directory or archive for correctness.

    For directories: content.md + styles.json required; structure.json + manifest.json optional.
    For ZIP archives (.sdoc): all files required.
    Also checks track change integrity when structure.json is present.
    """
    try:
        fmt = detect_sidedoc_format(input_file)
        with SidedocStore.open(input_file) as store:
            if fmt == "zip":
                click.echo("Tip: Use `sidedoc unpack` to convert to directory format for editing.", err=True)

            files = store.list_files()

            if fmt == "zip":
                # ZIP: all files required
                required = ALL_FILES
            else:
                # Directory: only core files required
                required = CORE_FILES

            missing = [f for f in required if f not in files]
            if missing:
                click.echo(f"✗ Missing required files: {', '.join(missing)}", err=True)
                sys.exit(EXIT_INVALID_FORMAT)

            # Check for optional tracking files in directory format
            if fmt == "directory":
                missing_tracking = [f for f in TRACKING_FILES if f not in files]
                if missing_tracking:
                    click.echo(f"Note: Optional tracking files not present: {', '.join(missing_tracking)}")
                    click.echo("Run `sidedoc sync` to generate them.")

            # Validate JSON files
            json_files_to_check = [f for f in ["structure.json", "styles.json", "manifest.json"]
                                   if store.has_file(f)]
            for json_file in json_files_to_check:
                try:
                    store.read_json(json_file)
                except json.JSONDecodeError as e:
                    click.echo(f"✗ Invalid JSON in {json_file}: {e}", err=True)
                    sys.exit(EXIT_INVALID_FORMAT)

            # Validate track changes and tables if structure.json is present
            if store.has_file("structure.json") and store.has_file("content.md"):
                content = store.read_text("content.md")
                structure = store.read_json("structure.json")

                tc_warnings = _validate_track_changes(structure, content)
                table_warnings = _validate_tables(structure, content)
                all_warnings = tc_warnings + table_warnings

                if all_warnings:
                    for warning in all_warnings:
                        click.echo(f"⚠ Warning: {warning}", err=True)
                    click.echo(f"✗ Sidedoc has {len(all_warnings)} issue(s)")
                    sys.exit(EXIT_INVALID_FORMAT)

            click.echo("✓ Sidedoc is valid")
            sys.exit(EXIT_SUCCESS)
    except ValueError:
        click.echo(f"✗ Not a valid sidedoc: {input_file}", err=True)
        sys.exit(EXIT_INVALID_FORMAT)
    except zipfile.BadZipFile:
        click.echo(f"✗ Invalid ZIP file: {input_file}", err=True)
        sys.exit(EXIT_INVALID_FORMAT)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(EXIT_ERROR)


@main.command()
@click.argument("input_file", type=click.Path(exists=True))
def info(input_file: str) -> None:
    """Display metadata about a sidedoc.

    Shows version, timestamps, source info, and hashes from manifest.json.
    """
    try:
        with SidedocStore.open(input_file) as store:
            if store.is_zip:
                click.echo("Tip: Use `sidedoc unpack` to convert to directory format for editing.", err=True)

            if not store.has_file("manifest.json"):
                click.echo("No manifest found. Run `sidedoc sync` to generate metadata.")
                sys.exit(EXIT_SUCCESS)

            manifest = store.read_json("manifest.json")

            click.echo("Sidedoc Information")
            click.echo("=" * 40)
            click.echo(f"Format:        {'directory' if store.is_directory else 'ZIP archive'}")
            click.echo(f"Version:       {manifest.get('sidedoc_version', 'N/A')}")
            click.echo(f"Created:       {manifest.get('created_at', 'N/A')}")
            click.echo(f"Modified:      {manifest.get('modified_at', 'N/A')}")
            click.echo(f"Source File:   {manifest.get('source_file', 'N/A')}")
            click.echo(f"Source Hash:   {manifest.get('source_hash', 'N/A')[:HASH_DISPLAY_LENGTH]}...")
            click.echo(f"Content Hash:  {manifest.get('content_hash', 'N/A')[:HASH_DISPLAY_LENGTH]}...")
            click.echo(f"Generator:     {manifest.get('generator', 'N/A')}")

            sys.exit(EXIT_SUCCESS)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(EXIT_ERROR)


@main.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option("-o", "--output", help="Output directory for unpacked contents (default: input with .sidedoc extension)")
def unpack(input_file: str, output: str | None) -> None:
    """Unpack a .sdoc ZIP archive to a .sidedoc/ directory.

    Also accepts legacy .sidedoc ZIP files.
    """
    try:
        input_path = Path(input_file)

        if not zipfile.is_zipfile(input_path):
            click.echo(f"Error: {input_file} is not a ZIP archive", err=True)
            sys.exit(EXIT_INVALID_FORMAT)

        if output is None:
            output = str(input_path.with_suffix(SIDEDOC_DIR_EXTENSION))

        output_path = Path(output)

        # Edge case: if input is a .sidedoc ZIP and output would collide
        if input_path.resolve() == output_path.resolve():
            click.echo(
                "Error: Input and output would have the same name. Use `-o` to specify a different output path.",
                err=True,
            )
            sys.exit(EXIT_ERROR)

        output_path.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(input_file, "r") as zip_file:
            for member in zip_file.namelist():
                if not is_safe_path(member, output_path):
                    click.echo(
                        f"Error: Archive contains invalid path that could lead to path traversal: {member}",
                        err=True,
                    )
                    sys.exit(EXIT_INVALID_FORMAT)

            zip_file.extractall(output_path)

        click.echo(f"✓ Unpacked to {output}")
        sys.exit(EXIT_SUCCESS)
    except zipfile.BadZipFile:
        click.echo(f"Error: Invalid sidedoc file: {input_file}", err=True)
        sys.exit(EXIT_INVALID_FORMAT)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(EXIT_ERROR)


@main.command()
@click.argument("input_dir", type=click.Path(exists=True))
@click.option("-o", "--output", help="Output path for .sdoc file (default: alongside input)")
def pack(input_dir: str, output: str | None) -> None:
    """Create a .sdoc ZIP archive from a .sidedoc/ directory.

    All files (content.md, styles.json, structure.json, manifest.json) must be present.
    Run `sidedoc sync` first to generate tracking files if needed.
    """
    try:
        input_path = Path(input_dir)

        # Require all files for ZIP distribution
        required = ALL_FILES
        for req_file in required:
            if not (input_path / req_file).exists():
                if req_file in TRACKING_FILES:
                    click.echo(
                        f"✗ Missing required file: {req_file}. Run `sidedoc sync` first to generate tracking files.",
                        err=True,
                    )
                else:
                    click.echo(f"✗ Missing required file: {req_file}", err=True)
                sys.exit(EXIT_INVALID_FORMAT)

        for json_file in ["structure.json", "styles.json", "manifest.json"]:
            try:
                with open(input_path / json_file) as f:
                    json.load(f)
            except json.JSONDecodeError as e:
                click.echo(f"✗ Invalid JSON in {json_file}: {e}", err=True)
                sys.exit(EXIT_INVALID_FORMAT)

        if output is None:
            output = str(input_path.with_suffix(SIDEDOC_ZIP_EXTENSION))
        else:
            output = ensure_sdoc_extension(output)

        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for file_path in input_path.rglob("*"):
                if file_path.is_file():
                    arcname = str(file_path.relative_to(input_path))
                    zip_file.write(file_path, arcname)

        click.echo(f"✓ Packed to {output}")
        sys.exit(EXIT_SUCCESS)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(EXIT_ERROR)


@main.command()
@click.argument("input_file", type=click.Path(exists=True))
def diff(input_file: str) -> None:
    """Show changes in content.md since last sync.

    Displays added, removed, and modified blocks with +/- markers.
    Only works with .sidedoc/ directories.
    """
    try:
        # Reject ZIP input
        input_path = Path(input_file)
        if input_path.is_file() and zipfile.is_zipfile(input_path):
            click.echo(
                "Error: Cannot diff a ZIP archive. Run `sidedoc unpack` to convert to directory format first.",
                err=True,
            )
            sys.exit(EXIT_INVALID_FORMAT)

        with SidedocStore.open(input_file) as store:
            try:
                content_md = store.read_text("content.md")
            except FileNotFoundError:
                click.echo("Error: content.md not found in sidedoc", err=True)
                sys.exit(EXIT_INVALID_FORMAT)

            if not store.has_file("structure.json"):
                click.echo("No sync history. Run `sidedoc sync` to establish a baseline.")
                sys.exit(EXIT_SUCCESS)

            try:
                old_structure = store.read_json("structure.json")
            except json.JSONDecodeError:
                click.echo("Error: Invalid JSON in structure.json", err=True)
                sys.exit(EXIT_INVALID_FORMAT)

            new_blocks = parse_markdown_to_blocks(content_md)

            # Compute content hashes for new blocks
            for block in new_blocks:
                block.content_hash = hashlib.sha256(block.content.encode()).hexdigest()

            old_blocks = _convert_structure_to_blocks(old_structure)

            # Match blocks to find differences
            matches = match_blocks(old_blocks, new_blocks)

            # Identify changes
            matched_old_ids = set(matches.keys())
            matched_new_block_ids = {b.id for b in matches.values()}

            deleted_blocks = [b for b in old_blocks if b.id not in matched_old_ids]
            added_blocks = [b for b in new_blocks if b.id not in matched_new_block_ids]

            modified_blocks = []
            for old_id, new_block in matches.items():
                old_block = next(b for b in old_blocks if b.id == old_id)
                if old_block.content_hash != new_block.content_hash:
                    modified_blocks.append((old_block, new_block))

            has_changes = deleted_blocks or added_blocks or modified_blocks

            if not has_changes:
                click.echo("No changes detected in content.md")
            else:
                click.echo("Changes in content.md:\n")

                if deleted_blocks:
                    click.echo(click.style("Removed blocks:", fg="red", bold=True))
                    for block in deleted_blocks:
                        block_desc = f"{block.type}"
                        if block.level:
                            block_desc += f" (level {block.level})"
                        click.echo(click.style(f"  - [{block_desc}] ", fg="red"))

                if added_blocks:
                    if deleted_blocks:
                        click.echo()
                    click.echo(click.style("Added blocks:", fg="green", bold=True))
                    for block in added_blocks:
                        block_desc = f"{block.type}"
                        if block.level:
                            block_desc += f" (level {block.level})"
                        content_preview = block.content[:CONTENT_PREVIEW_LENGTH]
                        if len(block.content) > CONTENT_PREVIEW_LENGTH:
                            content_preview += "..."
                        click.echo(click.style(f"  + [{block_desc}] {content_preview}", fg="green"))

                if modified_blocks:
                    if deleted_blocks or added_blocks:
                        click.echo()
                    click.echo(click.style("Modified blocks:", fg="yellow", bold=True))
                    for old_block, new_block in modified_blocks:
                        block_desc = f"{new_block.type}"
                        if new_block.level:
                            block_desc += f" (level {new_block.level})"
                        content_preview = new_block.content[:CONTENT_PREVIEW_LENGTH]
                        if len(new_block.content) > CONTENT_PREVIEW_LENGTH:
                            content_preview += "..."
                        click.echo(click.style(f"  ~ [{block_desc}] {content_preview}", fg="yellow"))

            sys.exit(EXIT_SUCCESS)

    except FileNotFoundError:
        click.echo(f"Error: File not found: {input_file}", err=True)
        sys.exit(EXIT_NOT_FOUND)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(EXIT_ERROR)


if __name__ == "__main__":
    main()
