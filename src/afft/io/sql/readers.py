"""Module for reading data from a database."""

import polars as pl

from ...utils.result import Ok, Err, Result

from .endpoint import Endpoint


def read_database(
    endpoint: Endpoint, query: str, **kwargs
) -> Result[pl.DataFrame, str]:
    """Read data frame from a database."""

    try:
        with endpoint.connect() as connection:
            dataframe: pl.DataFrame = pl.read_database(
                connection=connection, query=query, **kwargs
            )
        return Ok(dataframe)
    except (IOError, TypeError, ValueError) as error:
        return Err(error)
