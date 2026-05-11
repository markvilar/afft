"""
CLI commands for processing AUV messages, including parsing from the native AUV format.
"""

import click

from .actions import dispatch_parse_messages


@click.group()
@click.pass_context
def message_group(context: click.Context) -> None:
    """CLI group for invoking message processing tasks."""
    context.ensure_object(dict)


@message_group.command()
@click.argument("source", type=click.Path(exists=True))
@click.argument("config", type=click.Path(exists=True))
@click.option("--database", type=str, help="destination database")
@click.option("--host", type=str, help="destination host")
@click.option("--port", type=int, help="destination port")
@click.option(
    "--prefix", type=str, help="common prefix for exported message groups"
)
@click.option(
    "--output-dir",
    type=click.Path(file_okay=False),
    default=None,
    help="export parsed tables as CSV files to this directory",
)
def parse_messages(
    source: str,
    config: str,
    database: str | None = None,
    host: str | None = None,
    port: int | None = None,
    prefix: str | None = None,
    output_dir: str | None = None,
) -> None:
    """CLI action for ingesting messages into a destination."""
    dispatch_parse_messages(
        source, config, database, host, port, prefix, output_dir
    )
