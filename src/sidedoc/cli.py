"""CLI interface for sidedoc."""

import sys
from pathlib import Path
import click
from sidedoc import __version__
from sidedoc.extract import extract_blocks, extract_styles, blocks_to_markdown
from sidedoc.package import create_sidedoc_archive
from sidedoc.reconstruct import build_docx_from_sidedoc, parse_markdown_to_blocks
from sidedoc.sync import update_sidedoc_metadata, generate_updated_docx, match_blocks
from sidedoc.utils import ensure_sidedoc_extension, is_safe_path
from sidedoc.models import Block
from sidedoc.constants import HASH_DISPLAY_LENGTH, CONTENT_PREVIEW_LENGTH


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


@main.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option("-o", "--output", help="Output path for .sidedoc file")
@click.option(
    "--track-changes/--no-track-changes",
    default=None,
    help="Force enable/disable track changes extraction. Default: auto-detect",
)
def extract(input_file: str, output: str | None, track_changes: bool | None) -> None:
    """Extract a Word document into a sidedoc archive.

    Converts document.docx to document.sidedoc (or custom output path).

    Track changes behavior:
    - Default: Auto-detect track changes in the document
    - --track-changes: Force extract track changes as CriticMarkup
    - --no-track-changes: Accept all changes (ignore track changes)
    """
    try:
        if output is None:
            output = str(Path(input_file).with_suffix(".sidedoc"))
        else:
            output = ensure_sidedoc_extension(output)

        blocks, image_data = extract_blocks(input_file, track_changes=track_changes)
        styles = extract_styles(input_file, blocks)
        content_md = blocks_to_markdown(blocks)
        create_sidedoc_archive(output, content_md, blocks, styles, input_file, image_data)

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
    """Reconstruct a Word document from a sidedoc archive.

    Converts document.sidedoc to document.docx (or custom output path).
    """
    try:
        if output is None:
            output = str(Path(input_file).with_suffix(".docx"))

        build_docx_from_sidedoc(input_file, output)

        click.echo(f"✓ Built document: {output}")
        sys.exit(EXIT_SUCCESS)
    except FileNotFoundError:
        click.echo(f"Error: File not found: {input_file}", err=True)
        sys.exit(EXIT_NOT_FOUND)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(EXIT_ERROR)


def _read_sidedoc_files(input_file: str) -> tuple[str, dict, dict]:
    """Read content.md, styles.json, and structure.json from sidedoc archive.

    Args:
        input_file: Path to .sidedoc file

    Returns:
        Tuple of (content_md, styles_data, old_structure)

    Raises:
        KeyError: If required files are missing
        json.JSONDecodeError: If JSON files are invalid
    """
    import zipfile
    import json

    with zipfile.ZipFile(input_file, "r") as zip_file:
        try:
            content_md = zip_file.read("content.md").decode("utf-8")
        except KeyError:
            click.echo("Error: content.md not found in archive", err=True)
            sys.exit(EXIT_INVALID_FORMAT)

        try:
            styles_data = json.loads(zip_file.read("styles.json").decode("utf-8"))
        except KeyError:
            click.echo("Error: styles.json not found in archive", err=True)
            sys.exit(EXIT_INVALID_FORMAT)
        except json.JSONDecodeError as e:
            click.echo(f"Error: Invalid JSON in styles.json: {e}", err=True)
            sys.exit(EXIT_INVALID_FORMAT)

        try:
            old_structure = json.loads(zip_file.read("structure.json").decode("utf-8"))
        except KeyError:
            click.echo("Error: structure.json not found in archive", err=True)
            sys.exit(EXIT_INVALID_FORMAT)
        except json.JSONDecodeError as e:
            click.echo(f"Error: Invalid JSON in structure.json: {e}", err=True)
            sys.exit(EXIT_INVALID_FORMAT)

    return content_md, styles_data, old_structure


def _convert_structure_to_blocks(old_structure: dict) -> list:
    """Convert structure.json dict to list of Block objects.

    Args:
        old_structure: Dictionary containing blocks from structure.json

    Returns:
        List of Block objects
    """
    from sidedoc.models import Block

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
            )
        )
    return old_blocks


def _build_output_docx(new_blocks: list, old_structure: dict, styles_data: dict, output: str) -> None:
    """Build output docx file from new blocks with formatting preserved.

    Args:
        new_blocks: List of new Block objects
        old_structure: Dictionary containing blocks from structure.json
        styles_data: Style information dictionary
        output: Path to save output docx file
    """
    from sidedoc.sync import match_blocks

    old_blocks = _convert_structure_to_blocks(old_structure)
    matches = match_blocks(old_blocks, new_blocks)
    generate_updated_docx(new_blocks, matches, styles_data, output)
    click.echo(f"✓ Built updated document: {output}")


@main.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option("-o", "--output", help="Optional: build updated docx to this path")
@click.option("--author", default="Sidedoc AI", help="Author name for track changes (default: 'Sidedoc AI')")
def sync(input_file: str, output: str | None, author: str) -> None:
    """Sync changes from edited content.md back to the document.

    Updates the internal docx representation in the sidedoc archive.
    Optionally builds the updated docx to a specified path.

    CriticMarkup syntax ({++insert++}, {--delete--}, {~~old~>new~~}) in content.md
    will be converted to track changes in the output docx with the specified author.
    """
    import zipfile
    from sidedoc.sync import sync_sidedoc_to_docx

    try:
        content_md, styles_data, old_structure = _read_sidedoc_files(input_file)
        new_blocks = parse_markdown_to_blocks(content_md)
        update_sidedoc_metadata(input_file, new_blocks, content_md)

        click.echo(f"✓ Synced changes in {input_file}")

        if output:
            # Use sync_sidedoc_to_docx for track changes support
            sync_sidedoc_to_docx(input_file, output, author=author)
            click.echo(f"✓ Built updated document: {output}")

        sys.exit(EXIT_SUCCESS)

    except FileNotFoundError:
        click.echo(f"Error: File not found: {input_file}", err=True)
        sys.exit(EXIT_NOT_FOUND)
    except zipfile.BadZipFile:
        click.echo(f"Error: Invalid sidedoc file: {input_file}", err=True)
        sys.exit(EXIT_INVALID_FORMAT)
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
    content_lines = content.split('\n')

    for block in structure.get("blocks", []):
        block_id = block.get("id", "unknown")
        track_changes = block.get("track_changes") or []
        content_start = block.get("content_start", 0)
        content_end = block.get("content_end", 0)
        block_length = content_end - content_start

        for i, tc in enumerate(track_changes):
            tc_type = tc.get("type", "unknown")
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


@main.command()
@click.argument("input_file", type=click.Path(exists=True))
def validate(input_file: str) -> None:
    """Validate a sidedoc archive for correctness.

    Checks structure, JSON schemas, content hashes, asset references,
    and track change integrity.
    """
    import zipfile
    import json

    try:
        with zipfile.ZipFile(input_file, "r") as zip_file:
            names = zip_file.namelist()

            required = ["content.md", "structure.json", "styles.json", "manifest.json"]
            missing = [f for f in required if f not in names]

            if missing:
                click.echo(f"✗ Missing files: {', '.join(missing)}", err=True)
                sys.exit(EXIT_INVALID_FORMAT)

            for json_file in ["structure.json", "styles.json", "manifest.json"]:
                try:
                    json.loads(zip_file.read(json_file))
                except json.JSONDecodeError as e:
                    click.echo(f"✗ Invalid JSON in {json_file}: {e}", err=True)
                    sys.exit(EXIT_INVALID_FORMAT)

            # Validate track changes
            content = zip_file.read("content.md").decode("utf-8")
            structure = json.loads(zip_file.read("structure.json").decode("utf-8"))
            tc_warnings = _validate_track_changes(structure, content)

            if tc_warnings:
                for warning in tc_warnings:
                    click.echo(f"⚠ Warning: {warning}", err=True)
                click.echo(f"✗ Sidedoc archive has {len(tc_warnings)} track change issue(s)")
                sys.exit(EXIT_INVALID_FORMAT)

        click.echo("✓ Sidedoc archive is valid")
        sys.exit(EXIT_SUCCESS)
    except zipfile.BadZipFile:
        click.echo(f"✗ Invalid ZIP file: {input_file}", err=True)
        sys.exit(EXIT_INVALID_FORMAT)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(EXIT_ERROR)


@main.command()
@click.argument("input_file", type=click.Path(exists=True))
def info(input_file: str) -> None:
    """Display metadata about a sidedoc archive.

    Shows version, timestamps, source info, and hashes from manifest.json.
    """
    import zipfile
    import json

    try:
        with zipfile.ZipFile(input_file, "r") as zip_file:
            manifest = json.loads(zip_file.read("manifest.json"))

            click.echo("Sidedoc Archive Information")
            click.echo("=" * 40)
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
@click.option("-o", "--output", required=True, help="Output directory for unpacked contents")
def unpack(input_file: str, output: str) -> None:
    """Extract sidedoc contents to a directory.

    Unpacks the ZIP archive for inspection and debugging.
    """
    import zipfile
    from pathlib import Path

    try:
        output_path = Path(output)
        output_path.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(input_file, "r") as zip_file:
            for member in zip_file.namelist():
                if not is_safe_path(member, output_path):
                    click.echo(
                        f"Error: Archive contains invalid path that could lead to path traversal: {member}",
                        err=True
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
@click.option("-o", "--output", required=True, help="Output path for .sidedoc file")
def pack(input_dir: str, output: str) -> None:
    """Create a sidedoc archive from an unpacked directory.

    Packages directory contents into a .sidedoc ZIP archive.
    """
    import zipfile
    import json
    from pathlib import Path

    try:
        input_path = Path(input_dir)

        required = ["content.md", "structure.json", "styles.json", "manifest.json"]
        for req_file in required:
            if not (input_path / req_file).exists():
                click.echo(f"✗ Missing required file: {req_file}", err=True)
                sys.exit(EXIT_INVALID_FORMAT)

        for json_file in ["structure.json", "styles.json", "manifest.json"]:
            try:
                with open(input_path / json_file) as f:
                    json.load(f)
            except json.JSONDecodeError as e:
                click.echo(f"✗ Invalid JSON in {json_file}: {e}", err=True)
                sys.exit(EXIT_INVALID_FORMAT)

        output = ensure_sidedoc_extension(output)
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
    """
    import zipfile
    import json

    try:
        with zipfile.ZipFile(input_file, "r") as zip_file:
            try:
                content_md = zip_file.read("content.md").decode("utf-8")
            except KeyError:
                click.echo("Error: content.md not found in archive", err=True)
                sys.exit(EXIT_INVALID_FORMAT)

            try:
                old_structure = json.loads(zip_file.read("structure.json").decode("utf-8"))
            except KeyError:
                click.echo("Error: structure.json not found in archive", err=True)
                sys.exit(EXIT_INVALID_FORMAT)

        import hashlib
        new_blocks = parse_markdown_to_blocks(content_md)

        # Compute content hashes for new blocks (parse_markdown_to_blocks doesn't compute them)
        for block in new_blocks:
            block.content_hash = hashlib.sha256(block.content.encode()).hexdigest()

        old_blocks = []
        for block_data in old_structure.get("blocks", []):
            old_blocks.append(
                Block(
                    id=block_data["id"],
                    type=block_data["type"],
                    content="",  # We don't have old content
                    docx_paragraph_index=block_data["docx_paragraph_index"],
                    content_start=block_data["content_start"],
                    content_end=block_data["content_end"],
                    content_hash=block_data["content_hash"],
                    level=block_data.get("level"),
                    image_path=block_data.get("image_path"),
                    inline_formatting=block_data.get("inline_formatting"),
                )
            )

        # Match blocks to find differences
        matches = match_blocks(old_blocks, new_blocks)

        # Identify changes
        matched_old_ids = set(matches.keys())
        matched_new_block_ids = {b.id for b in matches.values()}

        # Find deleted blocks (in old but not matched)
        deleted_blocks = [b for b in old_blocks if b.id not in matched_old_ids]

        # Find added blocks (in new but not matched)
        added_blocks = [b for b in new_blocks if b.id not in matched_new_block_ids]

        # Find modified blocks (matched but content hash differs)
        modified_blocks = []
        for old_id, new_block in matches.items():
            old_block = next(b for b in old_blocks if b.id == old_id)
            if old_block.content_hash != new_block.content_hash:
                modified_blocks.append((old_block, new_block))

        # Display diff
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
                    # Show first N chars of content
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
    except zipfile.BadZipFile:
        click.echo(f"Error: Invalid sidedoc file: {input_file}", err=True)
        sys.exit(EXIT_INVALID_FORMAT)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(EXIT_ERROR)


if __name__ == "__main__":
    main()
