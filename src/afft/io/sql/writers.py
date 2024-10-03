"""Module for writing various data types to a SQL database."""

import polars as pl

from ...utils.result import Ok, Err, Result

from .endpoint import Endpoint


def write_database(
    endpoint: Endpoint, table: str, data: pl.DataFrame, **kwargs
) -> Result[int, str]:
    """Writes a data frame to database table."""
    try:
        with endpoint.begin() as connection:
            rows: int = data.write_database(
                table_name=table,
                connection=connection,
                **kwargs,
            )
        return Ok(rows)
    except (IOError, TypeError, ValueError) as error:
        return Err(error)
