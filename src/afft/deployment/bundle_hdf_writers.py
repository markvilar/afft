"""Concrete `pandas.HDFStore` writer implementing the deployment bundle
write `Protocol` interface defined in `bundle_protocols.py`."""

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Literal

import pandas as pd

from .bundle_common import RESERVED_KEYS, encode_frame_dtypes
from .bundle_hdf_common import (
    coerce_storable_dtypes,
    read_contents,
    upsert_contents_row,
)


@dataclass
class HDFDeploymentBundleWriter:
    """Concrete `DeploymentBundleWriter` backed by an open `pandas.HDFStore`."""

    store: pd.HDFStore

    def has_frame(self, key: str) -> bool:
        if key in RESERVED_KEYS:
            return False
        return key in read_contents(self.store)["identifier"].values

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
def open_deployment_bundle_writer(
    path: Path,
) -> Iterator[HDFDeploymentBundleWriter]:
    """Open an HDF5 deployment bundle for writing."""
    with pd.HDFStore(str(path), mode="a") as store:
        yield HDFDeploymentBundleWriter(store=store)
