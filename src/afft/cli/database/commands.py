"""
CLI commands for working with databases.
"""

import click

from .actions import (
    dispatch_table_export,
    dispatch_table_ingest,
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


@database_group.command()
@click.argument("source_dir", type=click.Path(exists=True, file_okay=False))
@click.option(
    "--pattern",
    type=str,
    default="*.csv",
    show_default=True,
    help="glob pattern to select files in source_dir",
)
@click.option(
    "--overwrite",
    is_flag=True,
    default=False,
    help="replace existing tables instead of failing",
)
@click.option(
    "--verbose",
    is_flag=True,
    default=False,
    help="log a summary of ingested files and row counts after completion",
)
def table_ingest(
    source_dir: str,
    pattern: str,
    overwrite: bool,
    verbose: bool,
) -> None:
    """Ingest files from SOURCE_DIR as database tables (reads DATABASE_URL from env)."""
    dispatch_table_ingest(source_dir, pattern, overwrite, verbose)


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
