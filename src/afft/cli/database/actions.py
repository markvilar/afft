"""Actions for database CLI commands."""

from pathlib import Path

import pandas as pd
import sqlalchemy as sqla
from rich.progress import Progress

import afft.database as db

from afft.environment import EnvironmentDatabase, load_environment


def invoke_table_export(
    database: str,
    host: str,
    port: int,
    output_dir: str | Path,
    tables: tuple[str, ...] = (),
) -> None:
    """Export database tables to CSV files in output_dir.

    Exports all tables when tables is empty, otherwise only the named ones.
    """
    credentials: EnvironmentDatabase = load_environment().database
    engine: db.Engine | str = db.create_engine(
        database=database,
        host=host,
        port=port,
        username=credentials.username.get_secret_value(),
        password=credentials.password.get_secret_value(),
    )

    assert isinstance(engine, db.Engine), (
        f"error when creating database engine: {engine}"
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
    progress = Progress()
    task = progress.add_task("", total=len(targets))
    progress.start()
    for table in targets:
        progress.update(task, description=table.ljust(width))
        df: pd.DataFrame = pd.read_sql_table(table, con=engine)
        dest = output_dir / f"{table}.csv"
        df.to_csv(dest, index=False)
        progress.advance(task)
    progress.stop()


def invoke_table_write(
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

    if_exists = "replace" if overwrite else "fail"

    data_frame: pd.DataFrame = pd.read_csv(source)

    credentials: EnvironmentDatabase = load_environment().database
    engine: db.Engine | str = db.create_engine(
        database=database,
        host=host,
        port=port,
        username=credentials.username.get_secret_value(),
        password=credentials.password.get_secret_value(),
    )
    assert isinstance(engine, db.Engine), (
        f"error when creating database engine: {engine}"
    )
    db.write_database_table(
        engine,
        table=name,
        data=data_frame,
        if_exists=if_exists,
    )
