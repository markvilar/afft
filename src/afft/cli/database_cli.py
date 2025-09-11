"""Module for invoking database task from the CLI."""

from pathlib import Path

import click
import polars as pl

import afft.database as db
import afft.utils.env as env

from afft.io import read_config
from afft.tasks.database_tasks import JoinTableConfig, join_database_tables

from afft.utils.log import logger
from afft.utils.result import Ok, Err


@click.group()
@click.pass_context
def database_cli(context: click.Context) -> None:
    """CLI group for invoking database tasks."""
    context.ensure_object(dict)


@database_cli.command()
@click.argument("database", type=str)
@click.argument("host", type=str)
@click.argument("port", type=int)
@click.argument("config", type=click.Path(exists=True))
def table_join(database: str, host: str, port: int, config: click.Path) -> None:
    """Join tables in the database."""

    match read_config(Path(config)):
        case Ok(config):
            task_configs: list[JoinTableConfig] = [
                JoinTableConfig(**task) for task in config.get("tasks")
            ]
        case Err(error):
            logger.error(error)
            return

    assert "PG_USERNAME" in env.env_values(), "missing environment key: PG_USERNAME"
    assert "PG_PASSWORD" in env.env_values(), "missing environment key: PG_PASSWORD"

    engine: db.Engine = create_engine(
        database=database, 
        host=host, 
        port=port,
        username=env.get_env_value("PG_USERNAME"),
        password=env.get_env_value("PG_PASSWORD"),
    )

    assert isinstance(engine, db.Engine), f"error when creating database engine: {engine}"

    results: dict[str, pl.DataFrame] = {
        config.label: join_database_tables(
            endpoint,
            queries=config.queries,
            selections=config.selections,
            base=config.join.get("base"),
            join_on=config.join.get("field"),
        )
        for config in task_configs
    }

    for label, dataframe in results.items():
        logger.info(f"Label: {label}, dataframe: {len(dataframe)}")


# TODO: Add command to upload table
@database_cli.command()
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

    source: Path = Path(source)

    if not name:
        name: str = source.stem

    if overwrite:
        if_table_exists: str = "replace"
    else:
        if_table_exists: str = "fail"

    data_frame: pl.DataFrame = pl.read_csv(source)

    match create_endpoint(database=database, host=host, port=port):
        case Ok(endpoint):
            write_database(
                endpoint,
                table=name,
                data=data_frame,
                if_table_exists=if_table_exists,
            ).unwrap()
        case Err(error):
            logger.error(error)
