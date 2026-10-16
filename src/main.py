#!/usr/bin/env python3
"""Command-line entry point for Perfmon V3."""

from pathlib import Path

import click


@click.command()
@click.option(
    "-c",
    "--config",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
    help="Path to the configuration file.",
)
@click.option(
    "-l",
    "--log",
    multiple=True,
    default=("_stderr",),
    help="Log destinations: _stdout, _stderr or a file path.",
)
@click.option("--log-level", default="INFO", show_default=True)
def main(config: Path, log: tuple[str, ...], log_level: str) -> None:
    """Start the Perfmon V3 runtime."""
    click.echo(
        f"Perfmon V3 configuration loaded from {config}; "
        "runtime assembly is not implemented yet."
    )


if __name__ == "__main__":
    main()
