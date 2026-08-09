"""Helpers shared by the SQLite deployment bundle reader, writer, and
read-write implementations."""

import sqlite3

from typing import Any

import pandas as pd

from .bundle_common import (
    CONTENTS_KEY,
    decode_frame_dtypes,
    empty_contents,
)


def quote_identifier(name: str) -> str:
    """
    Quote `name` for use as a SQLite table identifier.

    Bundle table names are frame identifiers verbatim, so they contain `/`
    and must be quoted at every reference. Embedded double quotes are
    doubled, as SQLite requires.

    Arguments
    ---------
    name: Identifier to quote.

    Returns
    -------
    The double-quoted identifier.
    """
    escaped: str = name.replace('"', '""')
    return f'"{escaped}"'


def table_exists(connection: sqlite3.Connection, name: str) -> bool:
    """Return whether a table called `name` exists in the database."""
    cursor = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (name,),
    )
    return cursor.fetchone() is not None


def read_contents(connection: sqlite3.Connection) -> pd.DataFrame:
    """Read `bundle_contents`, or an empty frame of the right shape if the
    bundle has no tables yet.

    Rows come back in insertion order: the manifest is ordered by `rowid`,
    and updating a row in place leaves its `rowid` unchanged.
    """
    if not table_exists(connection, CONTENTS_KEY):
        return empty_contents()
    return pd.read_sql(
        f"SELECT identifier, table_name, dtypes FROM "
        f"{quote_identifier(CONTENTS_KEY)} ORDER BY rowid",
        connection,
    )


def resolve_frame_entry(
    connection: sqlite3.Connection, key: str
) -> tuple[str, dict[str, Any]]:
    """
    Look up the table name and recorded dtypes for `key` in `bundle_contents`.

    Arguments
    ---------
    connection: Open connection to the bundle.
    key: The frame's identifier.

    Returns
    -------
    The frame's table name, and its column dtypes decoded back into pandas
    dtypes.

    Raises
    ------
    KeyError: If no frame is registered under `key`.
    """
    if not table_exists(connection, CONTENTS_KEY):
        raise KeyError(key)
    cursor = connection.execute(
        f"SELECT table_name, dtypes FROM {quote_identifier(CONTENTS_KEY)} "
        f"WHERE identifier = ?",
        (key,),
    )
    row = cursor.fetchone()
    if row is None:
        raise KeyError(key)
    table_name, dtypes = row
    return str(table_name), decode_frame_dtypes(dtypes)


def upsert_contents_row(
    connection: sqlite3.Connection, key: str, table_name: str, dtypes: str
) -> None:
    """
    Write the `bundle_contents` row for `key`, creating the manifest table if
    this is the bundle's first frame.

    The row is replaced in place if `key` is already registered, so a frame
    rewritten with a different schema does not leave the manifest describing
    the previous one, and a replacement does not reorder the manifest.

    Arguments
    ---------
    connection: Open connection to write the manifest into.
    key: The frame's identifier.
    table_name: The frame's backend-specific table name.
    dtypes: The frame's dtypes, encoded by `encode_frame_dtypes`.
    """
    quoted: str = quote_identifier(CONTENTS_KEY)
    with connection:
        connection.execute(
            f"CREATE TABLE IF NOT EXISTS {quoted} ("
            f"identifier TEXT PRIMARY KEY, "
            f"table_name TEXT NOT NULL, "
            f"dtypes TEXT NOT NULL)"
        )
        connection.execute(
            f"INSERT INTO {quoted} (identifier, table_name, dtypes) "
            f"VALUES (?, ?, ?) "
            f"ON CONFLICT(identifier) DO UPDATE SET "
            f"table_name = excluded.table_name, dtypes = excluded.dtypes",
            (key, table_name, dtypes),
        )


def write_frame_table(
    connection: sqlite3.Connection, table_name: str, frame: pd.DataFrame
) -> None:
    """
    Write `frame` to `table_name`, replacing any existing table of that name.

    The value encoding is `to_sql`'s: tz-aware timestamps become ISO-8601
    TEXT with an explicit offset, categories their labels, booleans and
    nullable integers INTEGER, and missing values NULL. `read_frame_table`
    reverses it using the dtypes the manifest recorded.

    The index is not stored -- nothing in the codebase reads it, and every
    frame is `RangeIndex`-ed.
    """
    frame.to_sql(table_name, connection, if_exists="replace", index=False)


def read_frame_table(
    connection: sqlite3.Connection,
    table_name: str,
    dtypes: dict[str, Any],
) -> pd.DataFrame:
    """
    Read `table_name` and restore the column dtypes the manifest recorded.

    Arguments
    ---------
    connection: Open connection to the bundle.
    table_name: Table to read.
    dtypes: Column dtypes, as returned by `resolve_frame_entry`.

    Returns
    -------
    The frame, with each recorded column cast back to its original dtype.
    """
    frame: pd.DataFrame = pd.read_sql(
        f"SELECT * FROM {quote_identifier(table_name)}", connection
    )
    for column, dtype in dtypes.items():
        if isinstance(dtype, pd.DatetimeTZDtype):
            # Stored as ISO text with an offset, so parse before casting.
            frame[column] = pd.to_datetime(frame[column], utc=True).astype(
                dtype
            )
        elif pd.api.types.is_datetime64_dtype(dtype):
            frame[column] = pd.to_datetime(frame[column])
        else:
            frame[column] = frame[column].astype(dtype)
    return frame
