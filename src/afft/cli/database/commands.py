"""
CLI commands for working with databases.
"""

import click

from .actions import dispatch_table_join, dispatch_table_write


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
