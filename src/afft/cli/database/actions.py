"""Actions for database CLI commands."""

from pathlib import Path

import pandas as pd
import polars as pl
import sqlalchemy as sqla
from tqdm import tqdm

import afft.database as db
import afft.io as io
import afft.tasks.database_tasks as dbtasks
import afft.utils.env as env

from afft.tasks.ingest_tables import IngestTablesCommand, run_ingest_tables
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


def dispatch_table_export(
    database: str,
    host: str,
    port: int,
    output_dir: str | Path,
    tables: tuple[str, ...] = (),
) -> None:
    """Export database tables to CSV files in output_dir.

    Exports all tables when tables is empty, otherwise only the named ones.
    """
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

    output_dir = Path(output_dir)
    if not output_dir.is_dir():
        raise ValueError(f"output directory does not exist: {output_dir}")

    inspector = sqla.inspect(engine)
    available: list[str] = inspector.get_table_names()

    targets = list(tables) if tables else available

    unknown = [t for t in targets if t not in available]
    if unknown:
        raise ValueError(f"tables not found in database: {unknown}")

    width = max(len(t) for t in targets)
    progress = tqdm(targets, unit="table")
    for table in progress:
        progress.set_description(table.ljust(width))
        df: pd.DataFrame = pd.read_sql_table(table, con=engine)
        dest = output_dir / f"{table}.csv"
        df.to_csv(dest, index=False)


def dispatch_table_ingest(
    source_dir: str | Path,
    pattern: str = "*.csv",
    overwrite: bool = False,
    verbose: bool = False,
) -> None:
    """Ingest all files matching pattern in source_dir as database tables."""
    command = IngestTablesCommand(
        source_dir=Path(source_dir),
        pattern=pattern,
        overwrite=overwrite,
        verbose=verbose,
    )
    run_ingest_tables(command)


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
