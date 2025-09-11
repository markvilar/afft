"""Module for writing various data types to a SQL database."""

import polars as pl

from .engine import Engine


def write_database_table(engine: Engine, table: str, data: pl.DataFrame, **overrides) -> int | str:
    """Writes a data frame to database table."""
    try:
        with engine.begin() as connection:
            rows: int = data.write_database(
                table_name=table,
                connection=connection,
                **overrides,
            )
        return rows
    except (IOError, TypeError, ValueError) as error:
        return error
