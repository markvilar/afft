"""Module for reading data from a database."""

from typing import Any

import pandas as pd

from .engine import Engine


def read_database_table(
    engine: Engine, query: str, **kwargs: Any
) -> pd.DataFrame:
    """Read data frame from a database."""
    try:
        with engine.connect() as connection:
            dataframe: pd.DataFrame = pd.read_sql(
                sql=query, con=connection, **kwargs
            )
        return dataframe
    except (IOError, TypeError, ValueError) as exception:
        raise exception
