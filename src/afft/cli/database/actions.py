"""Actions for database CLI commands."""

from pathlib import Path

import polars as pl

import afft.database as db
import afft.io as io
import afft.tasks.database_tasks as dbtasks
import afft.utils.env as env

from afft.utils.log import logger


def dispatch_table_join(
    database: str,
    host: str,
    port: int,
    config_path: str | Path,
) -> None:
    """Load join configs and execute each join against the database."""
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


def dispatch_table_write(
    source: str | Path,
    database: str,
    host: str,
    port: int,
    name: str | None = None,
    overwrite: bool = False,
) -> None:
    """Write a CSV file to a database table."""
    source = Path(source)

    if not name:
        name = source.stem

    if_table_exists = "replace" if overwrite else "fail"

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
