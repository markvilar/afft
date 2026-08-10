"""Concrete `pandas.HDFStore` bundle implementing the deployment bundle
read-write `Protocol` interface defined in `bundle_protocols.py`."""

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Literal

import pandas as pd

from .bundle_common import RESERVED_KEYS, encode_frame_dtypes
from .bundle_hdf_common import (
    coerce_storable_dtypes,
    read_contents,
    resolve_table_name,
    upsert_contents_row,
)


@dataclass
class HDFDeploymentBundleIO:
    """Concrete `DeploymentBundleIO` backed by an open `pandas.HDFStore`."""

    store: pd.HDFStore

    def list_frames(self) -> list[str]:
        return list(self.contents()["identifier"])

    def has_frame(self, key: str) -> bool:
        if key in RESERVED_KEYS:
            return False
        return key in self.list_frames()

    def read_frame(self, key: str) -> pd.DataFrame:
        if key in RESERVED_KEYS:
            raise KeyError(f"{key!r} is reserved; use contents() instead")
        table_name = resolve_table_name(self.store, key)
        return self.store.select(table_name)

    def contents(self) -> pd.DataFrame:
        return read_contents(self.store)

    def write_frame(
        self,
        key: str,
        frame: pd.DataFrame,
        *,
        if_exists: Literal["fail", "replace"] = "fail",
    ) -> None:
        if key in RESERVED_KEYS:
            raise ValueError(f"{key!r} is reserved and managed automatically")

        exists = self.has_frame(key)
        if exists and if_exists == "fail":
            raise ValueError(f"frame already exists at key: {key!r}")

        table_name = key  # HDF: table_name == key verbatim

        # Record the frame's own dtypes, not the ones it is about to be
        # coerced into -- the coercion is a storage limitation, and what it
        # discards is unrecoverable once the frame is written.
        dtypes = encode_frame_dtypes(frame)

        frame = coerce_storable_dtypes(frame)
        if exists:
            self.store.remove(table_name)
        self.store.put(table_name, frame, format="table")

        upsert_contents_row(self.store, key, table_name, dtypes)


@contextmanager
def open_deployment_bundle(path: Path) -> Iterator[HDFDeploymentBundleIO]:
    """Open an HDF5 deployment bundle for reading and writing."""
    with pd.HDFStore(str(path), mode="a") as store:
        yield HDFDeploymentBundleIO(store=store)
