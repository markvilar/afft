"""Concrete SQLite writer implementing the deployment bundle write
`Protocol` interface defined in `bundle_protocols.py`."""

import sqlite3

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Literal

import pandas as pd

from .bundle_common import RESERVED_KEYS, encode_frame_dtypes
from .bundle_sqlite_common import (
    read_contents,
    upsert_contents_row,
    write_frame_table,
)


@dataclass
class SQLiteDeploymentBundleWriter:
    """Concrete `DeploymentBundleWriter` backed by an open `sqlite3` connection."""

    connection: sqlite3.Connection

    def has_frame(self, key: str) -> bool:
        if key in RESERVED_KEYS:
            return False
        return key in read_contents(self.connection)["identifier"].values

    def write_frame(
        self,
        key: str,
        frame: pd.DataFrame,
        *,
        if_exists: Literal["fail", "replace"] = "fail",
    ) -> None:
        if key in RESERVED_KEYS:
            raise ValueError(f"{key!r} is reserved and managed automatically")

        if self.has_frame(key) and if_exists == "fail":
            raise ValueError(f"frame already exists at key: {key!r}")

        table_name = key  # SQLite: table_name == key verbatim

        # The table is written before its manifest row, so an interrupted
        # write leaves an unreferenced table rather than a manifest entry
        # pointing at a table that is not there.
        write_frame_table(self.connection, table_name, frame)
        upsert_contents_row(
            self.connection, key, table_name, encode_frame_dtypes(frame)
        )


@contextmanager
def open_deployment_bundle_writer(
    path: Path,
) -> Iterator[SQLiteDeploymentBundleWriter]:
    """Open a SQLite deployment bundle for writing, creating it if absent."""
    connection = sqlite3.connect(path)
    try:
        yield SQLiteDeploymentBundleWriter(connection=connection)
    finally:
        connection.close()
