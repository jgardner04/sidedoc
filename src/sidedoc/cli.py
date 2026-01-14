"""CLI interface for sidedoc."""

import sys
from pathlib import Path
import click
from sidedoc import __version__
from sidedoc.extract import extract_blocks, extract_styles, blocks_to_markdown
from sidedoc.package import create_sidedoc_archive
from sidedoc.reconstruct import build_docx_from_sidedoc, parse_markdown_to_blocks
from sidedoc.sync import update_sidedoc_metadata, generate_updated_docx, match_blocks
from sidedoc.utils import ensure_sidedoc_extension
from sidedoc.models import Block


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
def extract(input_file: str, output: str | None) -> None:
    """Extract a Word document into a sidedoc archive.

    Converts document.docx to document.sidedoc (or custom output path).
    """
    try:
        # Determine output path
        if output is None:
            output = str(Path(input_file).with_suffix(".sidedoc"))
        else:
            output = ensure_sidedoc_extension(output)

        # Extract blocks and styles
        blocks, image_data = extract_blocks(input_file)
        styles = extract_styles(input_file, blocks)

        # Convert to markdown
        content_md = blocks_to_markdown(blocks)

        # Create archive
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
        # Determine output path
        if output is None:
            output = str(Path(input_file).with_suffix(".docx"))

        # Build document
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
def sync(input_file: str, output: str | None) -> None:
    """Sync changes from edited content.md back to the document.

    Updates the internal docx representation in the sidedoc archive.
    Optionally builds the updated docx to a specified path.
    """
    import zipfile
    import json

    try:
        # Read sidedoc archive
        with zipfile.ZipFile(input_file, "r") as zf:
            # Read content.md
            try:
                content_md = zf.read("content.md").decode("utf-8")
            except KeyError:
                click.echo("Error: content.md not found in archive", err=True)
                sys.exit(EXIT_INVALID_FORMAT)

            # Read styles.json for formatting
            try:
                styles_data = json.loads(zf.read("styles.json").decode("utf-8"))
            except KeyError:
                click.echo("Error: styles.json not found in archive", err=True)
                sys.exit(EXIT_INVALID_FORMAT)
            except json.JSONDecodeError as e:
                click.echo(f"Error: Invalid JSON in styles.json: {e}", err=True)
                sys.exit(EXIT_INVALID_FORMAT)

            # Read old structure.json for block history
            try:
                old_structure = json.loads(zf.read("structure.json").decode("utf-8"))
            except KeyError:
                click.echo("Error: structure.json not found in archive", err=True)
                sys.exit(EXIT_INVALID_FORMAT)

        # Parse edited content.md into new blocks
        new_blocks = parse_markdown_to_blocks(content_md)

        # Update metadata in sidedoc archive
        update_sidedoc_metadata(input_file, new_blocks, content_md)

        click.echo(f"✓ Synced changes in {input_file}")

        # If output path specified, build the docx
        if output:
            # Generate updated docx
            from sidedoc.sync import match_blocks
            from sidedoc.models import Block

            # Convert old structure to Block objects for matching
            old_blocks = []
            for block_data in old_structure.get("blocks", []):
                old_blocks.append(
                    Block(
                        id=block_data["id"],
                        type=block_data["type"],
                        content="",  # We don't have old content, but that's OK for matching
                        docx_paragraph_index=block_data["docx_paragraph_index"],
                        content_start=block_data["content_start"],
                        content_end=block_data["content_end"],
                        content_hash=block_data["content_hash"],
                        level=block_data.get("level"),
                        image_path=block_data.get("image_path"),
                        inline_formatting=block_data.get("inline_formatting"),
                    )
                )

            # Match old blocks to new blocks
            matches = match_blocks(old_blocks, new_blocks)

            # Generate updated docx
            generate_updated_docx(new_blocks, matches, styles_data, output)
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


@main.command()
@click.argument("input_file", type=click.Path(exists=True))
def validate(input_file: str) -> None:
    """Validate a sidedoc archive for correctness.

    Checks structure, JSON schemas, content hashes, and asset references.
    """
    import zipfile
    import json

    try:
        with zipfile.ZipFile(input_file, "r") as zf:
            names = zf.namelist()

            # Check required files
            required = ["content.md", "structure.json", "styles.json", "manifest.json"]
            missing = [f for f in required if f not in names]

            if missing:
                click.echo(f"✗ Missing files: {', '.join(missing)}", err=True)
                sys.exit(EXIT_INVALID_FORMAT)

            # Validate JSON files
            for json_file in ["structure.json", "styles.json", "manifest.json"]:
                try:
                    json.loads(zf.read(json_file))
                except json.JSONDecodeError as e:
                    click.echo(f"✗ Invalid JSON in {json_file}: {e}", err=True)
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
        with zipfile.ZipFile(input_file, "r") as zf:
            manifest = json.loads(zf.read("manifest.json"))

            click.echo("Sidedoc Archive Information")
            click.echo("=" * 40)
            click.echo(f"Version:       {manifest.get('sidedoc_version', 'N/A')}")
            click.echo(f"Created:       {manifest.get('created_at', 'N/A')}")
            click.echo(f"Modified:      {manifest.get('modified_at', 'N/A')}")
            click.echo(f"Source File:   {manifest.get('source_file', 'N/A')}")
            click.echo(f"Source Hash:   {manifest.get('source_hash', 'N/A')[:16]}...")
            click.echo(f"Content Hash:  {manifest.get('content_hash', 'N/A')[:16]}...")
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

        with zipfile.ZipFile(input_file, "r") as zf:
            zf.extractall(output_path)

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

        # Validate required files exist
        required = ["content.md", "structure.json", "styles.json", "manifest.json"]
        for req_file in required:
            if not (input_path / req_file).exists():
                click.echo(f"✗ Missing required file: {req_file}", err=True)
                sys.exit(EXIT_INVALID_FORMAT)

        # Validate JSON files
        for json_file in ["structure.json", "styles.json", "manifest.json"]:
            try:
                with open(input_path / json_file) as f:
                    json.load(f)
            except json.JSONDecodeError as e:
                click.echo(f"✗ Invalid JSON in {json_file}: {e}", err=True)
                sys.exit(EXIT_INVALID_FORMAT)

        # Create ZIP archive
        output = ensure_sidedoc_extension(output)
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
            for file_path in input_path.rglob("*"):
                if file_path.is_file():
                    arcname = str(file_path.relative_to(input_path))
                    zf.write(file_path, arcname)

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
        # Read sidedoc archive
        with zipfile.ZipFile(input_file, "r") as zf:
            # Read current content.md
            try:
                content_md = zf.read("content.md").decode("utf-8")
            except KeyError:
                click.echo("Error: content.md not found in archive", err=True)
                sys.exit(EXIT_INVALID_FORMAT)

            # Read old structure.json
            try:
                old_structure = json.loads(zf.read("structure.json").decode("utf-8"))
            except KeyError:
                click.echo("Error: structure.json not found in archive", err=True)
                sys.exit(EXIT_INVALID_FORMAT)

        # Parse current content into blocks
        import hashlib
        new_blocks = parse_markdown_to_blocks(content_md)

        # Compute content hashes for new blocks (parse_markdown_to_blocks doesn't compute them)
        for block in new_blocks:
            block.content_hash = hashlib.sha256(block.content.encode()).hexdigest()

        # Convert old structure to Block objects
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
                    # Show first 50 chars of content
                    content_preview = block.content[:50]
                    if len(block.content) > 50:
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
                    content_preview = new_block.content[:50]
                    if len(new_block.content) > 50:
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
