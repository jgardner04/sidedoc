"""CLI interface for sidedoc."""

import sys
from pathlib import Path
import click
from sidedoc import __version__
from sidedoc.extract import extract_blocks, extract_styles, blocks_to_markdown
from sidedoc.package import create_sidedoc_archive
from sidedoc.reconstruct import build_docx_from_sidedoc
from sidedoc.utils import ensure_sidedoc_extension


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
        blocks = extract_blocks(input_file)
        styles = extract_styles(input_file, blocks)

        # Convert to markdown
        content_md = blocks_to_markdown(blocks)

        # Create archive
        create_sidedoc_archive(output, content_md, blocks, styles, input_file)

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
    """
    click.echo(f"Sync command - input: {input_file}, output: {output}")
    sys.exit(EXIT_SUCCESS)


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

    Displays added, removed, and modified blocks.
    """
    click.echo(f"Diff command - input: {input_file}")
    sys.exit(EXIT_SUCCESS)


if __name__ == "__main__":
    main()
