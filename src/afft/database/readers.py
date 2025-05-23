"""Module for reading data from a database."""

import polars as pl

from .engine import Engine


def read_database_table(engine: Engine, query: str, **kwargs) -> pl.DataFrame | str:
    """Read data frame from a database."""
    try:
        with engine.connect() as connection:
            dataframe: pl.DataFrame = pl.read_database(
                connection=connection, query=query, **kwargs
            )
        return dataframe
    except (IOError, TypeError, ValueError) as error:
        return error
