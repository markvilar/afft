"""Module for invoking database task from the CLI."""

from pathlib import Path

import click
import polars as pl

import afft.database as db
import afft.io as io
import afft.tasks.database_tasks as dbtasks
import afft.utils.env as env

from afft.utils.log import logger


@click.group()
@click.pass_context
def database_cli(context: click.Context) -> None:
    """CLI group for invoking database tasks."""
    context.ensure_object(dict)


@database_cli.command()
@click.argument("database", type=str)
@click.argument("host", type=str)
@click.argument("port", type=int)
@click.argument("config_path", type=click.Path(exists=True))
def table_join(
    database: str, host: str, port: int, config_path: click.Path
) -> None:
    """Join tables in the database."""

    config: dict = io.read_config(Path(config_path))
    task_configs: list[dbtasks.JoinTableConfig] = [
        dbtasks.JoinTableConfig(**task) for task in config.get("tasks")
    ]

    assert "PG_USERNAME" in env.env_values(), (
        "missing environment key: PG_USERNAME"
    )
    assert "PG_PASSWORD" in env.env_values(), (
        "missing environment key: PG_PASSWORD"
    )

    engine: db.Engine = db.create_engine(
        database=database,
        host=host,
        port=port,
        username=env.get_env_value("PG_USERNAME"),
        password=env.get_env_value("PG_PASSWORD"),
    )

    assert isinstance(engine, db.Engine), (
        f"error when creating database engine: {engine}"
    )

    results: dict[str, pl.DataFrame] = {
        config.label: dbtasks.join_database_tables(
            engine,
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

    engine: db.Engine = db.create_engine(
        database=database, host=host, port=port
    )
    db.write_database_table(
        engine,
        table=name,
        data=data_frame,
        if_table_exists=if_table_exists,
    )
