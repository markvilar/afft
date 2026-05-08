"""
CLI commands for working with databases.
"""

import click

from .actions import (
    dispatch_table_export,
    dispatch_table_join,
    dispatch_table_write,
)


@click.group()
@click.pass_context
def database_group(context: click.Context) -> None:
    """CLI group for invoking database tasks."""
    context.ensure_object(dict)


@database_group.command()
@click.argument("database", type=str)
@click.argument("host", type=str)
@click.argument("port", type=int)
@click.argument("config_path", type=click.Path(exists=True))
def table_join(
    database: str, host: str, port: int, config_path: click.Path
) -> None:
    """Join tables in the database."""
    dispatch_table_join(database, host, port, config_path)


@database_group.command()
@click.argument("database", type=str)
@click.argument("host", type=str)
@click.argument("port", type=int)
@click.argument("output_dir", type=click.Path(file_okay=False))
@click.option(
    "--table",
    "tables",
    type=str,
    multiple=True,
    help="table to export (repeatable); omit to export all tables",
)
def table_export(
    database: str,
    host: str,
    port: int,
    output_dir: str,
    tables: tuple[str, ...],
) -> None:
    """Export database tables to CSV files in OUTPUT_DIR."""
    dispatch_table_export(database, host, port, output_dir, tables)


# TODO: Add command to upload table
@database_group.command()
@click.argument("source", type=click.Path(exists=True))
@click.argument("database", type=str)
@click.argument("host", type=str)
@click.argument("port", type=int)
@click.option(
    "--name", type=str, default=None, help="overwrite existing database"
)
@click.option(
    "--overwrite",
    is_flag=True,
    default=False,
    help="overwrite existing database",
)
def table_write(
    source: click.Path,
    database: str,
    host: str,
    port: int,
    name: str | None,
    overwrite: bool,
) -> None:
    """Write a table to a database."""
    dispatch_table_write(source, database, host, port, name, overwrite)
