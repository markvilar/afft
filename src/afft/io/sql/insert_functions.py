"""Module for writing various data types to a SQL database."""

import polars as pl

from ...utils.result import Ok, Err, Result

from .endpoint import Endpoint


def insert_data_frame_into(
    endpoint: Endpoint,
    table: str,
    data: pl.DataFrame,
    **kwargs
) -> Result[int, str]:
    """Inserts a data frame into a database."""
    try:
        with endpoint.begin() as connection:
            rows: int = data.write_database(table_name=table, connection=connection, **kwargs,)
        return Ok(rows)
    except (IOError, TypeError, ValueError) as error:
        return Err(error)
