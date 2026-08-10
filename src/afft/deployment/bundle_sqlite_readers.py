"""Concrete SQLite reader implementing the deployment bundle read
`Protocol` interface defined in `bundle_protocols.py`."""

import sqlite3

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import pandas as pd

from .bundle_common import RESERVED_KEYS
from .bundle_sqlite_common import (
    read_contents,
    read_frame_table,
    resolve_frame_entry,
)


@dataclass
class SQLiteDeploymentBundleReader:
    """Concrete `DeploymentBundleReader` backed by an open `sqlite3` connection."""

    connection: sqlite3.Connection

    def list_frames(self) -> list[str]:
        return list(self.contents()["identifier"])

    def has_frame(self, key: str) -> bool:
        if key in RESERVED_KEYS:
            return False
        return key in self.list_frames()

    def read_frame(self, key: str) -> pd.DataFrame:
        if key in RESERVED_KEYS:
            raise KeyError(f"{key!r} is reserved; use contents() instead")
        table_name, dtypes = resolve_frame_entry(self.connection, key)
        return read_frame_table(self.connection, table_name, dtypes)

    def contents(self) -> pd.DataFrame:
        return read_contents(self.connection)


@contextmanager
def open_deployment_bundle_reader(
    path: Path,
) -> Iterator[SQLiteDeploymentBundleReader]:
    """
    Open a SQLite deployment bundle for reading.

    Raises
    ------
    FileNotFoundError: If `path` does not exist. The check is explicit
        because SQLite would otherwise create an empty database, turning a
        mistyped path into a bundle with no frames rather than an error.
    """
    if not path.exists():
        raise FileNotFoundError(f"no deployment bundle at: {path}")
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        yield SQLiteDeploymentBundleReader(connection=connection)
    finally:
        connection.close()
