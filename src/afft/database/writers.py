"""Module for writing various data types to a SQL database."""

from typing import Any

import pandas as pd

from .engine import Engine


def write_database_table(
    engine: Engine, table: str, data: pd.DataFrame, **overrides: Any
) -> int | Exception:
    """Writes a data frame to database table."""
    try:
        with engine.begin() as connection:
            rows: int | None = data.to_sql(
                name=table,
                con=connection,
                index=False,
                **overrides,
            )
        return rows if rows is not None else 0
    except (IOError, TypeError, ValueError) as error:
        return error
