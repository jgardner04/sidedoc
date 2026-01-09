"""CLI entry points for Sidedoc."""

import click


@click.group()
@click.version_option()
def cli():
    """Sidedoc - AI-native document format."""
    pass


@cli.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option("-o", "--output", help="Output path for the .sidedoc file")
def extract(input_file, output):
    """Extract a .docx file into a .sidedoc container."""
    click.echo(f"Extracting {input_file}...")
    # Implementation will come via TDD


@cli.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option("-o", "--output", help="Output path for the .docx file")
def build(input_file, output):
    """Build a .docx file from a .sidedoc container."""
    click.echo(f"Building {input_file}...")
    # Implementation will come via TDD


@cli.command()
@click.argument("input_file", type=click.Path(exists=True))
def sync(input_file):
    """Sync edited content.md back to the .docx."""
    click.echo(f"Syncing {input_file}...")
    # Implementation will come via TDD


@cli.command()
@click.argument("input_file", type=click.Path(exists=True))
def validate(input_file):
    """Validate a .sidedoc container."""
    click.echo(f"Validating {input_file}...")
    # Implementation will come via TDD


if __name__ == "__main__":
    cli()
