"""Concrete `pandas.HDFStore` reader implementing the deployment bundle
read `Protocol` interface defined in `bundle_protocols.py`."""

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import pandas as pd

from .bundle_common import RESERVED_KEYS
from .bundle_hdf_common import (
    read_contents,
    resolve_table_name,
)


@dataclass
class HDFDeploymentBundleReader:
    """Concrete `DeploymentBundleReader` backed by an open `pandas.HDFStore`."""

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


@contextmanager
def open_deployment_bundle_reader(
    path: Path,
) -> Iterator[HDFDeploymentBundleReader]:
    """Open an HDF5 deployment bundle for reading."""
    with pd.HDFStore(str(path), mode="r") as store:
        yield HDFDeploymentBundleReader(store=store)
